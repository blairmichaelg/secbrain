"""CLI wrappers for recon tools (subfinder, amass, httpx, ffuf, etc.)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.core.context import RunContext


@dataclass
class ToolResult:
    """Result from a CLI tool execution."""

    tool: str
    success: bool
    output: str
    parsed_data: list[dict[str, Any]]
    duration_ms: float
    error: str | None = None


class ReconToolRunner:
    """
    Runner for recon CLI tools with safety controls.

    Supports:
    - subfinder: Subdomain discovery
    - amass: Attack surface mapping
    - httpx: HTTP probing
    - ffuf: Fuzzing
    """

    def __init__(self, run_context: RunContext):
        self.run_context = run_context
        self._tool_paths: dict[str, str] = {}

    def _find_tool(self, tool_name: str) -> str | None:
        """Find the path to a tool executable."""
        if tool_name in self._tool_paths:
            return self._tool_paths[tool_name]

        path = shutil.which(tool_name)
        if path:
            self._tool_paths[tool_name] = path
        return path

    def _check_preconditions(self, tool_name: str) -> str | None:
        """Check preconditions for running a tool."""
        if self.run_context.is_killed():
            return "Kill-switch activated"

        if not self.run_context.check_tool_acl(tool_name):
            return f"Tool not allowed: {tool_name}"

        if self.run_context.dry_run:
            return None

        if not self._find_tool(tool_name):
            return f"Tool not found: {tool_name}"

        return None

    async def _run_command(
        self,
        tool_name: str,
        args: list[str],
        timeout: int = 300,
    ) -> ToolResult:
        """Run a CLI command with safety checks."""
        import time

        start_time = time.time()

        # Check preconditions
        error = self._check_preconditions(tool_name)
        if error:
            return ToolResult(
                tool=tool_name,
                success=False,
                output="",
                parsed_data=[],
                duration_ms=0,
                error=error,
            )

        # Dry-run mode
        if self.run_context.dry_run:
            parsed_data: list[dict[str, Any]] = []
            if tool_name == "subfinder":
                try:
                    domain_idx = args.index("-d") + 1
                    domain = args[domain_idx]
                except Exception:
                    domain = "example.com"
                parsed_data = [
                    {"subdomain": f"www.{domain}", "source": "dry_run"},
                    {"subdomain": f"api.{domain}", "source": "dry_run"},
                ]
            elif tool_name == "httpx":
                parsed_data = [
                    {
                        "url": "https://example.com",
                        "status_code": 200,
                        "title": "Example Domain",
                        "tech": [],
                        "content_length": 0,
                        "webserver": "",
                    }
                ]
            return ToolResult(
                tool=tool_name,
                success=True,
                output=f"[DRY-RUN] Would run: {tool_name} {' '.join(args)}",
                parsed_data=parsed_data,
                duration_ms=0,
            )

        if self.run_context.requires_approval(tool_name) and not self.run_context.auto_approve:
            from secbrain.core.approval import ApprovalRequest, new_request_id

            approval = await self.run_context.approval_manager.request_approval(
                ApprovalRequest(
                    request_id=new_request_id(),
                    tool_name=tool_name,
                    operation=f"{tool_name} {' '.join(args)}",
                    risk_level="high",
                    timestamp=datetime.now(UTC),
                )
            )
            if not approval.approved:
                return ToolResult(
                    tool=tool_name,
                    success=False,
                    output="",
                    parsed_data=[],
                    duration_ms=0,
                    error=f"Approval denied: {tool_name} ({approval.reason})",
                )

        # Acquire rate limit
        await self.run_context.acquire_rate_limit(tool_name)

        try:
            tool_path = self._find_tool(tool_name)
            process = await asyncio.create_subprocess_exec(
                tool_path,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            duration_ms = (time.time() - start_time) * 1000
            self.run_context.record_tool_call(tool_name)

            output = stdout.decode("utf-8", errors="replace")
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                return ToolResult(
                    tool=tool_name,
                    success=False,
                    output=output,
                    parsed_data=[],
                    duration_ms=duration_ms,
                    error=error_msg,
                )

            return ToolResult(
                tool=tool_name,
                success=True,
                output=output,
                parsed_data=[],
                duration_ms=duration_ms,
            )

        except TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool=tool_name,
                success=False,
                output="",
                parsed_data=[],
                duration_ms=duration_ms,
                error=f"Timeout after {timeout}s",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool=tool_name,
                success=False,
                output="",
                parsed_data=[],
                duration_ms=duration_ms,
                error=str(e),
            )

    async def run_subfinder(
        self,
        domain: str,
        output_file: Path | None = None,
        timeout: int = 300,
    ) -> ToolResult:
        """Run subfinder for subdomain enumeration."""
        args = ["-d", domain, "-silent"]

        if output_file:
            args.extend(["-o", str(output_file)])

        result = await self._run_command("subfinder", args, timeout)

        # Parse output into structured data
        if result.success and result.output:
            subdomains = [
                {"subdomain": line.strip(), "source": "subfinder"}
                for line in result.output.strip().split("\n")
                if line.strip()
            ]
            result.parsed_data = subdomains

        return result

    async def run_amass(
        self,
        domain: str,
        passive_only: bool = True,
        timeout: int = 600,
    ) -> ToolResult:
        """Run amass for attack surface mapping."""
        args = ["enum", "-d", domain]

        if passive_only:
            args.append("-passive")

        result = await self._run_command("amass", args, timeout)

        # Parse output
        if result.success and result.output:
            assets = [
                {"asset": line.strip(), "source": "amass"}
                for line in result.output.strip().split("\n")
                if line.strip()
            ]
            result.parsed_data = assets

        return result

    async def run_httpx(
        self,
        targets: list[str],
        timeout: int = 300,
    ) -> ToolResult:
        """Run httpx for HTTP probing."""
        # Create a temp file with targets

        targets_file: str | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("\n".join(targets))
                targets_file = f.name

            args = ["-l", targets_file, "-silent", "-json"]

            result = await self._run_command("httpx", args, timeout)

            # Parse JSON output
            if result.success and result.output:
                parsed = []
                for line in result.output.strip().split("\n"):
                    if line.strip():
                        with contextlib.suppress(json.JSONDecodeError):
                            parsed.append(json.loads(line))
                result.parsed_data = parsed

            return result
        finally:
            if targets_file:
                Path(targets_file).unlink(missing_ok=True)

    async def run_ffuf(
        self,
        url: str,
        wordlist: str,
        timeout: int = 600,
        rate: int = 100,
    ) -> ToolResult:
        """Run ffuf for fuzzing."""
        args = [
            "-u", url,
            "-w", wordlist,
            "-rate", str(rate),
            "-o", "-",
            "-of", "json",
            "-s",
        ]

        result = await self._run_command("ffuf", args, timeout)

        # Parse JSON output
        if result.success and result.output:
            try:
                data = json.loads(result.output)
                result.parsed_data = data.get("results", [])
            except json.JSONDecodeError:
                pass

        return result

    async def run_nmap(
        self,
        target: str,
        ports: str = "1-1000",
        timeout: int = 600,
    ) -> ToolResult:
        """Run nmap for port scanning."""
        args = ["-p", ports, "-sV", "--open", "-oG", "-", target]

        result = await self._run_command("nmap", args, timeout)

        # Parse greppable output
        if result.success and result.output:
            parsed = []
            for line in result.output.split("\n"):
                if "Ports:" in line:
                    # Parse nmap greppable format
                    parsed.append({"raw": line, "source": "nmap"})
            result.parsed_data = parsed

        return result


async def create_recon_runner(run_context: RunContext) -> ReconToolRunner:
    """Create a recon tool runner for the given context."""
    return ReconToolRunner(run_context)
