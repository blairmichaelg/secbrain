"""Scanner integrations (nuclei, semgrep) for SecBrain."""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.core.context import RunContext


@dataclass
class ScanResult:
    """Result from a scanner execution."""

    scanner: str
    success: bool
    findings: list[dict[str, Any]]
    duration_ms: float
    error: str | None = None
    raw_output: str = ""


class NucleiScanner:
    """
    Nuclei vulnerability scanner integration.

    Features:
    - Template-based scanning
    - Severity filtering
    - Tag-based filtering
    - Rate limiting
    """

    def __init__(
        self,
        run_context: RunContext,
        templates_path: str | None = None,
    ):
        self.run_context = run_context
        self.templates_path = templates_path or "~/nuclei-templates"

    def _find_nuclei(self) -> str | None:
        """Find nuclei executable."""
        return shutil.which("nuclei")

    def _check_preconditions(self) -> str | None:
        """Check preconditions for running nuclei."""
        if self.run_context.is_killed():
            return "Kill-switch activated"

        if not self.run_context.check_tool_acl("nuclei"):
            return "Nuclei not allowed in current phase"

        if (
            self.run_context.requires_approval("nuclei")
            and not (self.run_context.dry_run or self.run_context.auto_approve)
        ):
            return "Approval required: nuclei"

        if not self._find_nuclei():
            return "Nuclei not found"

        return None

    async def scan(
        self,
        targets: list[str],
        templates: list[str] | None = None,
        tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        severity: list[str] | None = None,
        rate_limit: int = 100,
        timeout: int = 600,
    ) -> ScanResult:
        """Run a nuclei scan."""
        import tempfile
        import time

        start_time = time.time()

        # Check preconditions
        error = self._check_preconditions()
        if error:
            return ScanResult(
                scanner="nuclei",
                success=False,
                findings=[],
                duration_ms=0,
                error=error,
            )

        # Dry-run mode
        if self.run_context.dry_run:
            return ScanResult(
                scanner="nuclei",
                success=True,
                findings=[],
                duration_ms=0,
                raw_output=f"[DRY-RUN] Would scan {len(targets)} targets",
            )

        # Create targets file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("\n".join(targets))
            targets_file = f.name

        # Build command
        args = [
            "-l", targets_file,
            "-j",  # JSON output
            "-silent",
            "-rate-limit", str(rate_limit),
        ]

        if templates:
            for t in templates:
                args.extend(["-t", t])

        if tags:
            args.extend(["-tags", ",".join(tags)])

        if exclude_tags:
            args.extend(["-etags", ",".join(exclude_tags)])

        if severity:
            args.extend(["-severity", ",".join(severity)])

        # Acquire rate limit
        await self.run_context.acquire_rate_limit("nuclei")

        try:
            nuclei_path = self._find_nuclei()
            process = await asyncio.create_subprocess_exec(
                nuclei_path,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            duration_ms = (time.time() - start_time) * 1000
            self.run_context.record_tool_call("nuclei")

            output = stdout.decode("utf-8", errors="replace")

            # Parse JSON lines output
            findings = []
            for line in output.strip().split("\n"):
                if line.strip():
                    try:
                        finding = json.loads(line)
                        findings.append(finding)
                    except json.JSONDecodeError:
                        pass

            return ScanResult(
                scanner="nuclei",
                success=True,
                findings=findings,
                duration_ms=duration_ms,
                raw_output=output,
            )

        except TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ScanResult(
                scanner="nuclei",
                success=False,
                findings=[],
                duration_ms=duration_ms,
                error=f"Timeout after {timeout}s",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ScanResult(
                scanner="nuclei",
                success=False,
                findings=[],
                duration_ms=duration_ms,
                error=str(e),
            )
        finally:
            Path(targets_file).unlink(missing_ok=True)


class SemgrepScanner:
    """
    Semgrep static analysis scanner integration.

    Used for source code analysis when available.
    """

    def __init__(self, run_context: RunContext):
        self.run_context = run_context

    def _find_semgrep(self) -> str | None:
        """Find semgrep executable."""
        return shutil.which("semgrep")

    def _check_preconditions(self) -> str | None:
        """Check preconditions."""
        if self.run_context.is_killed():
            return "Kill-switch activated"

        if not self.run_context.check_tool_acl("semgrep"):
            return "Semgrep not allowed"

        if (
            self.run_context.requires_approval("semgrep")
            and not (self.run_context.dry_run or self.run_context.auto_approve)
        ):
            return "Approval required: semgrep"

        if not self._find_semgrep():
            return "Semgrep not found"

        return None

    async def scan(
        self,
        path: Path,
        config: str = "auto",
        severity: list[str] | None = None,
        timeout: int = 600,
    ) -> ScanResult:
        """Run semgrep scan on source code."""
        import time

        start_time = time.time()

        error = self._check_preconditions()
        if error:
            return ScanResult(
                scanner="semgrep",
                success=False,
                findings=[],
                duration_ms=0,
                error=error,
            )

        if self.run_context.dry_run:
            return ScanResult(
                scanner="semgrep",
                success=True,
                findings=[],
                duration_ms=0,
                raw_output=f"[DRY-RUN] Would scan {path}",
            )

        args = [
            "--config", config,
            "--json",
            "--quiet",
            str(path),
        ]

        if severity:
            args.extend(["--severity", ",".join(severity)])

        await self.run_context.acquire_rate_limit("semgrep")

        try:
            semgrep_path = self._find_semgrep()
            process = await asyncio.create_subprocess_exec(
                semgrep_path,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            duration_ms = (time.time() - start_time) * 1000
            self.run_context.record_tool_call("semgrep")

            output = stdout.decode("utf-8", errors="replace")

            try:
                data = json.loads(output)
                findings = data.get("results", [])
            except json.JSONDecodeError:
                findings = []

            return ScanResult(
                scanner="semgrep",
                success=True,
                findings=findings,
                duration_ms=duration_ms,
                raw_output=output,
            )

        except TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ScanResult(
                scanner="semgrep",
                success=False,
                findings=[],
                duration_ms=duration_ms,
                error=f"Timeout after {timeout}s",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ScanResult(
                scanner="semgrep",
                success=False,
                findings=[],
                duration_ms=duration_ms,
                error=str(e),
            )


async def create_nuclei_scanner(run_context: RunContext) -> NucleiScanner:
    """Create a Nuclei scanner."""
    return NucleiScanner(run_context)


async def create_semgrep_scanner(run_context: RunContext) -> SemgrepScanner:
    """Create a Semgrep scanner."""
    return SemgrepScanner(run_context)
