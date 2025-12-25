"""Reporting agent - creates bug bounty reports.

This module generates professional bug bounty reports including:
- Templated markdown reports with proof-of-concept code
- CWE and impact reference integration via research
- Platform-specific formatting for submission
- Evidence collection and documentation
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class ReportingAgent(BaseAgent):
    """
    Reporting agent.

    Responsibilities:
    - Creates templated reports (markdown with PoC)
    - Uses research for CWE/impact references
    - Formats for platform submission
    """

    name = "reporting"
    phase = "report"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Execute reporting phase."""
        self._log("starting_reporting")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        triage_data = kwargs.get("triage_data", {})
        findings = triage_data.get("findings", [])

        if not findings:
            return self._success(
                message="No findings to report",
                data={"reports": []},
            )

        # Filter to reportable findings
        reportable = [
            f for f in findings
            if f.get("severity") in ["critical", "high", "medium"]
            and f.get("status") not in ["false_positive", "duplicate"]
        ]

        reports: list[dict[str, Any]] = []

        for finding in reportable:
            report = await self._generate_report(finding)
            reports.append(report)

            # Save report to workspace
            await self._save_report(report)

        # Generate summary
        summary = self._generate_summary(reports)

        return self._success(
            message=f"Generated {len(reports)} reports",
            data={
                "reports": reports,
                "summary": summary,
                "report_path": str(self._get_reports_dir()),
            },
        )

    async def _generate_report(
        self,
        finding: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a full report for a finding."""
        vuln_type = finding.get("vuln_type", "Unknown")
        target = finding.get("target", "")

        # Research CWE and impact
        cwe_info = {}
        if self.research_client:
            cwe_info = await self._research_cwe(vuln_type)

        # Generate report content using worker model
        content = await self._generate_report_content(finding, cwe_info)

        # Generate PoC if applicable
        poc = await self._generate_poc(finding)

        return {
            "id": finding.get("id"),
            "title": self._format_title(finding),
            "severity": finding.get("severity", "medium"),
            "vuln_type": vuln_type,
            "target": target,
            "cwe": cwe_info.get("cwe_id", ""),
            "cvss": cwe_info.get("cvss", ""),
            "content": content,
            "poc": poc,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def _format_title(self, finding: dict[str, Any]) -> str:
        """Format a professional report title."""
        vuln_type = finding.get("vuln_type", "Vulnerability")
        target = finding.get("target", "")

        # Extract domain from URL
        if target.startswith("http"):
            from urllib.parse import urlparse
            parsed = urlparse(target)
            domain = parsed.netloc
        else:
            domain = target

        return f"{vuln_type.upper()} vulnerability in {domain}"

    async def _research_cwe(self, vuln_type: str) -> dict[str, Any]:
        """Research CWE classification for vulnerability type."""
        result = await self._research(
            question=f"What is the CWE ID and CVSS score range for {vuln_type} vulnerabilities?",
            context="Need CWE classification for bug bounty report",
        )

        # Parse response for CWE ID
        answer = result.get("answer", "")

        cwe_id = ""
        if "CWE-" in answer:
            import re
            match = re.search(r"CWE-\d+", answer)
            if match:
                cwe_id = match.group()

        return {
            "cwe_id": cwe_id,
            "cvss": "",  # Would need more parsing
            "description": answer[:200] if answer else "",
        }

    async def _generate_report_content(
        self,
        finding: dict[str, Any],
        cwe_info: dict[str, Any],
    ) -> str:
        """Generate the main report content."""
        prompt = f"""Write a professional bug bounty report for this vulnerability.

Vulnerability Type: {finding.get('vuln_type')}
Target: {finding.get('target')}
Severity: {finding.get('severity')}
Description: {finding.get('description', '')}
Evidence: {json.dumps(finding.get('evidence', []))}
CWE: {cwe_info.get('cwe_id', 'TBD')}

Use this format:

## Summary
[Brief description of the vulnerability]

## Impact
[What an attacker could achieve]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
...

## Recommendation
[How to fix the vulnerability]

## References
[CWE/OWASP references]

Be concise but thorough. Focus on clarity for the security team."""

        return await self._call_worker(prompt)

    async def _generate_poc(self, finding: dict[str, Any]) -> str:
        """Generate proof-of-concept code."""
        vuln_type = finding.get("vuln_type", "").lower()
        target = finding.get("target", "")
        evidence = finding.get("evidence", [])

        if not evidence:
            return ""

        prompt = f"""Generate a minimal proof-of-concept for this vulnerability.

Type: {vuln_type}
Target: {target}
Evidence: {json.dumps(evidence)}

Requirements:
- Safe, non-destructive PoC
- Can be run from command line (curl, python, etc.)
- Clearly demonstrates the issue

Output code only, with comments."""

        return await self._call_worker(prompt)

    async def _save_report(self, report: dict[str, Any]) -> None:
        """Save report to workspace."""
        reports_dir = self._get_reports_dir()
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_file = reports_dir / f"{report['id']}.md"

        content = f"""# {report['title']}

**Severity:** {report['severity']}
**CWE:** {report.get('cwe', 'TBD')}
**Target:** {report['target']}
**Generated:** {report['generated_at']}

{report['content']}

## Proof of Concept

```
{report.get('poc', 'N/A')}
```
"""

        report_file.write_text(content)
        self._log("report_saved", path=str(report_file))

    def _get_reports_dir(self) -> Path:
        """Get reports directory path."""
        return self.run_context.workspace_path / "reports"

    def _generate_summary(self, reports: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a summary of all reports."""
        by_severity: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for report in reports:
            sev = report.get("severity", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1

            vtype = report.get("vuln_type", "unknown")
            by_type[vtype] = by_type.get(vtype, 0) + 1

        return {
            "total_reports": len(reports),
            "by_severity": by_severity,
            "by_type": by_type,
            "generated_at": datetime.now(UTC).isoformat(),
        }
