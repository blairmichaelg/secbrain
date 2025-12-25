"""Static analysis agent - integrates scanners for source code analysis."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class StaticAnalysisAgent(BaseAgent):
    """
    Static analysis agent.

    Responsibilities:
    - Integrates scanners/semgrep when source is available
    - Analyzes code patterns for vulnerabilities
    - Correlates with dynamic findings
    """

    name = "static_analysis"
    phase = "static"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Execute static analysis phase."""
        self._log("starting_static_analysis")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        source_path = kwargs.get("source_path")
        exploit_data = kwargs.get("exploit_data", {})

        # Try to auto-detect source code if not provided
        if not source_path:
            source_path = self._auto_detect_source_code()
            if source_path:
                self._log(
                    "source_code_auto_detected",
                    path=str(source_path),
                )

        # Static analysis requires source code
        if not source_path:
            return self._success(
                message="No source code available for static analysis",
                data={"skipped": True, "reason": "no_source"},
                next_actions=["triage"],
            )

        source_path = Path(source_path)
        if not source_path.exists():
            return self._success(
                message="Source path does not exist",
                data={"skipped": True, "reason": "path_not_found"},
                next_actions=["triage"],
            )

        findings: list[dict[str, Any]] = []

        # Run semgrep if available
        semgrep_findings = await self._run_semgrep(source_path)
        findings.extend(semgrep_findings)

        # Correlate with dynamic findings
        dynamic_findings = exploit_data.get("findings", [])
        correlations = self._correlate_findings(findings, dynamic_findings)

        # Store findings
        if self.storage:
            for finding in findings:
                await self.storage.save_finding(finding)

        return self._success(
            message=f"Static analysis complete: {len(findings)} issues found",
            data={
                "findings": findings,
                "correlations": correlations,
                "scanner": "semgrep",
                "source_path": str(source_path),
                "auto_detected": not kwargs.get("source_path"),
            },
            next_actions=["triage"],
        )

    def _auto_detect_source_code(self) -> Path | None:
        """
        Auto-detect source code in common locations.

        Checks for:
        1. {workspace}/instascope/src
        2. {workspace}/instascope
        3. {workspace}/src
        4. {workspace}/contracts

        Returns:
            Path to source code directory or None
        """
        workspace = self.run_context.workspace_path

        # Check common source locations
        candidates = [
            workspace / "instascope" / "src",
            workspace / "instascope",
            workspace / "src",
            workspace / "contracts",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                # Check if it contains Solidity files (efficiently)
                # Use next() to avoid creating full list for large directories
                has_sol_files = next(candidate.glob("**/*.sol"), None) is not None
                if has_sol_files:
                    # Get count for logging
                    sol_files_count = sum(1 for _ in candidate.glob("**/*.sol"))
                    self._log(
                        "source_code_found",
                        path=str(candidate),
                        sol_files_count=sol_files_count,
                    )
                    return candidate

        return None

    async def _run_semgrep(self, source_path: Path) -> list[dict[str, Any]]:
        """Run semgrep scanner on source code."""
        from secbrain.tools.scanners import SemgrepScanner

        scanner = SemgrepScanner(self.run_context)
        result = await scanner.scan(
            path=source_path,
            severity=["ERROR", "WARNING"],
        )

        findings: list[dict[str, Any]] = []

        if result.success:
            for item in result.findings:
                findings.append({
                    "id": f"static-{uuid.uuid4().hex[:8]}",
                    "title": item.get("check_id", "Unknown"),
                    "severity": self._map_severity(item.get("extra", {}).get("severity", "INFO")),
                    "status": "potential",
                    "vuln_type": item.get("check_id", "").split(".")[-1],
                    "target": str(source_path),
                    "description": item.get("extra", {}).get("message", ""),
                    "evidence": [{
                        "file": item.get("path"),
                        "line": item.get("start", {}).get("line"),
                        "code": item.get("extra", {}).get("lines", ""),
                    }],
                    "source": "semgrep",
                })

        return findings

    def _map_severity(self, semgrep_severity: str) -> str:
        """Map semgrep severity to standard levels."""
        mapping = {
            "ERROR": "high",
            "WARNING": "medium",
            "INFO": "low",
        }
        return mapping.get(semgrep_severity.upper(), "info")

    def _correlate_findings(
        self,
        static_findings: list[dict[str, Any]],
        dynamic_findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Correlate static and dynamic findings."""
        correlations: list[dict[str, Any]] = []

        for static in static_findings:
            static_type = static.get("vuln_type", "").lower()

            for dynamic in dynamic_findings:
                dynamic_type = dynamic.get("vuln_type", "").lower()

                # Check if vulnerability types are related
                if static_type in dynamic_type or dynamic_type in static_type:
                    correlations.append({
                        "static_id": static.get("id"),
                        "dynamic_id": dynamic.get("id"),
                        "vuln_type": static_type,
                        "confidence": "high",
                        "message": f"Static finding correlates with dynamic finding for {static_type}",
                    })

        return correlations
