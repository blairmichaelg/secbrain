"""Triage agent - clusters and prioritizes findings."""

from __future__ import annotations

import json
from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class TriageAgent(BaseAgent):
    """
    Triage agent.

    Responsibilities:
    - Clusters anomalies
    - Correlates dynamic + static findings
    - Uses advisor for high/medium/low classification
    """

    name = "triage"
    phase = "triage"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Execute triage phase."""
        self._log("starting_triage")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        exploit_data = kwargs.get("exploit_data", {})
        static_data = kwargs.get("static_data", {})

        # Economic filter from exploit attempts
        attempts = exploit_data.get("attempts", [])
        econ_summary = self._economic_decision(attempts)

        # Collect all findings
        dynamic_findings = exploit_data.get("findings", [])
        static_findings = static_data.get("findings", [])
        all_findings = dynamic_findings + static_findings

        if not all_findings:
            return self._success(
                message="No findings to triage",
                data={
                    "findings": [],
                    "triaged": 0,
                    "economic": econ_summary,
                },
                next_actions=["report"],
            )

        # Deduplicate findings
        unique_findings = self._deduplicate(all_findings)

        # Cluster by vulnerability type
        clusters = self._cluster_findings(unique_findings)

        # Get advisor review for severity classification
        reviewed_findings = await self._advisor_review(unique_findings)

        # Prioritize findings
        prioritized = self._prioritize(reviewed_findings)

        ready_for_report = []
        if econ_summary.get("decision") == "PURSUE":
            ready_for_report = [f for f in prioritized if f.get("severity") in ["critical", "high"]]

        # Update storage
        if self.storage:
            for finding in prioritized:
                await self.storage.save_finding(finding)

        return self._success(
            message=f"Triaged {len(prioritized)} findings",
            data={
                "findings": prioritized,
                "clusters": clusters,
                "by_severity": self._group_by_severity(prioritized),
                "ready_for_report": ready_for_report,
                "economic": econ_summary,
            },
            next_actions=["report"],
        )

    def _deduplicate(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Remove duplicate findings."""
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []

        for finding in findings:
            # Create a key based on target and vuln type
            key = f"{finding.get('target', '')}:{finding.get('vuln_type', '')}"

            if key not in seen:
                seen.add(key)
                unique.append(finding)
            else:
                # Mark as duplicate
                finding["status"] = "duplicate"

        return unique

    def _cluster_findings(
        self,
        findings: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Cluster findings by vulnerability type."""
        clusters: dict[str, list[str]] = {}

        for finding in findings:
            vuln_type = finding.get("vuln_type", "unknown")
            finding_id = finding.get("id", "")

            if vuln_type not in clusters:
                clusters[vuln_type] = []
            clusters[vuln_type].append(finding_id)

        return clusters

    async def _advisor_review(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Get advisor review for severity classification."""
        if not self.advisor_model or not findings:
            return findings

        # Review top findings for accurate severity
        top_findings = findings[:10]

        prompt = f"""Review these security findings and validate severity classifications.

Findings:
{json.dumps(top_findings, indent=2)}

For each finding, assess:
1. Is the severity classification accurate?
2. Is this a real vulnerability or false positive?
3. What is the potential business impact?

Respond with JSON:
{{
  "assessments": [
    {{
      "id": "finding-id",
      "validated_severity": "critical|high|medium|low|info",
      "confidence": 0.0-1.0,
      "is_false_positive": false,
      "impact": "description"
    }}
  ]
}}"""

        response = await self._call_advisor(prompt)

        try:
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                review_data = json.loads(json_str.strip())
            else:
                review_data = json.loads(response)

            # Apply assessments to findings
            assessments = {a["id"]: a for a in review_data.get("assessments", [])}

            for finding in findings:
                fid = finding.get("id")
                if fid in assessments:
                    assessment = assessments[fid]
                    finding["validated_severity"] = assessment.get("validated_severity")
                    finding["advisor_confidence"] = assessment.get("confidence")
                    finding["impact"] = assessment.get("impact")

                    if assessment.get("is_false_positive"):
                        finding["status"] = "false_positive"

        except json.JSONDecodeError:
            pass

        return findings

    def _prioritize(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Prioritize findings by severity and confidence."""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

        def sort_key(f: dict[str, Any]) -> tuple[int, float]:
            sev = f.get("validated_severity") or f.get("severity", "info")
            conf = f.get("advisor_confidence", 0.5)
            return (severity_order.get(sev, 5), -conf)

        # Filter out false positives and duplicates
        active = [
            f for f in findings
            if f.get("status") not in ["false_positive", "duplicate"]
        ]

        return sorted(active, key=sort_key)

    def _group_by_severity(
        self,
        findings: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Group findings by severity."""
        counts: dict[str, int] = {}
        for f in findings:
            sev = f.get("validated_severity") or f.get("severity", "info")
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    def _economic_decision(self, attempts: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute a profitability gate from exploit attempts (ETH + tokens)."""
        if not attempts:
            return {"decision": "SKIP", "reason": "no_attempts", "max_profit_eth": 0.0}

        eth_price = 3000.0  # fallback; prefer attempt-provided estimates
        max_profit_eth = 0.0
        max_profit_usd = 0.0
        gas_used = None
        gas_price_wei = None

        for att in attempts:
            try:
                p_eth = float(att.get("profit_eth") or 0.0)
                p_usd = float(att.get("profit_usd_estimate") or 0.0)
            except (TypeError, ValueError):
                continue

            # Use any ETH price hint attached to attempt
            try:
                eth_price = float(att.get("eth_price_usd") or eth_price)
            except Exception:
                pass

            # Derive USD from ETH if not provided
            if not p_usd and eth_price:
                p_usd = p_eth * eth_price

            # Include token breakdown if present (already USD or normalized values)
            breakdown = att.get("profit_breakdown") or {}
            if isinstance(breakdown, dict):
                try:
                    token_sum = sum(float(v or 0.0) for v in breakdown.values())
                    p_usd = max(p_usd, token_sum) if token_sum else p_usd
                except Exception:
                    pass

            if p_eth > max_profit_eth:
                max_profit_eth = p_eth
                gas_used = att.get("gas_used")
                gas_price_wei = att.get("gas_price_wei") or att.get("gas_price")
            max_profit_usd = max(max_profit_usd, p_usd)

        # Estimate gas cost with EIP-1559-style baseline + priority fee if available
        base_gas_price_wei = 50e9  # 50 gwei fallback
        try:
            if gas_price_wei:
                base_gas_price_wei = float(gas_price_wei)
        except Exception:
            pass
        gas_cost_eth = (float(gas_used or 0) * base_gas_price_wei) / 1e18
        gas_cost = gas_cost_eth * eth_price if eth_price else 0.0
        net_usd = max_profit_usd - gas_cost

        gas_ratio = (gas_cost / max_profit_usd) if max_profit_usd > 0 else float("inf")
        min_profit_threshold = 300
        if gas_ratio > 0.5:
            decision = "SKIP"
            reason = "Gas cost too high relative to profit"
        elif net_usd >= min_profit_threshold:
            decision = "PURSUE"
            reason = f"Net profit ${net_usd:.0f} exceeds threshold"
        elif net_usd > 0:
            decision = "CONSIDER"
            reason = f"Marginal profit ${net_usd:.0f}"
        else:
            decision = "SKIP"
            reason = "Negative or zero profit"

        return {
            "decision": decision,
            "reason": reason,
            "max_profit_eth": max_profit_eth,
            "max_profit_usd": round(max_profit_usd, 2),
            "gas_used": gas_used,
            "gas_cost_usd_est": round(gas_cost, 2) if gas_used else 0,
            "net_usd_est": round(net_usd, 2),
            "threshold_eth": 0.1,
            "threshold_usd": min_profit_threshold,
            "gas_price_wei": base_gas_price_wei,
        }
