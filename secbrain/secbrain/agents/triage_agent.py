"""Triage agent - clusters and prioritizes findings."""

from __future__ import annotations

import json
from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class EconomicAnalyzer:
    """Analyze exploit profitability with gas cost estimation."""

    def __init__(
        self,
        min_profit_usd: float = 300.0,
        gas_ratio_threshold: float = 0.5,
        default_eth_price: float = 3000.0,
        default_gas_price_gwei: float = 50.0,
    ) -> None:
        self.min_profit_usd = min_profit_usd
        self.gas_ratio_threshold = gas_ratio_threshold
        self.default_eth_price = default_eth_price
        self.default_gas_price_gwei = default_gas_price_gwei

    def analyze_attempts(
        self,
        attempts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze exploit attempts for profitability."""
        if not attempts:
            return {
                "decision": "SKIP",
                "reason": "no_attempts",
                "max_profit_eth": 0.0,
                "max_profit_usd": 0.0,
                "gas_cost_usd_est": 0.0,
                "net_usd_est": 0.0,
            }

        eth_price = self.default_eth_price
        max_profit_eth = 0.0
        max_profit_usd = 0.0
        gas_info: dict[str, Any] | None = None

        for attempt in attempts:
            profit_eth, profit_usd = self._extract_profit(attempt, eth_price)

            if profit_eth > max_profit_eth:
                max_profit_eth = profit_eth
                gas_info = self._extract_gas_info(attempt)
            if profit_usd > max_profit_usd:
                max_profit_usd = profit_usd

            if attempt.get("eth_price_usd"):
                try:
                    eth_price = float(attempt["eth_price_usd"])
                except (TypeError, ValueError):
                    pass

        gas_cost_usd = self._estimate_gas_cost(gas_info, eth_price)
        net_usd = max_profit_usd - gas_cost_usd

        decision = self._make_decision(max_profit_usd, gas_cost_usd, net_usd)

        return {
            "decision": decision["decision"],
            "reason": decision["reason"],
            "max_profit_eth": round(max_profit_eth, 4),
            "max_profit_usd": round(max_profit_usd, 2),
            "gas_used": gas_info["gas_used"] if gas_info else None,
            "gas_cost_usd_est": round(gas_cost_usd, 2),
            "net_usd_est": round(net_usd, 2),
            "threshold_usd": self.min_profit_usd,
            "gas_price_gwei": gas_info["gas_price_gwei"] if gas_info else self.default_gas_price_gwei,
        }

    def _extract_profit(
        self,
        attempt: dict[str, Any],
        eth_price: float,
    ) -> tuple[float, float]:
        """Extract profit values from attempt."""
        try:
            profit_eth = float(attempt.get("profit_eth", 0) or 0)
            profit_usd = float(attempt.get("profit_usd_estimate", 0) or 0)
        except (TypeError, ValueError):
            return (0.0, 0.0)

        if not profit_usd and eth_price:
            profit_usd = profit_eth * eth_price

        breakdown = attempt.get("profit_breakdown") or {}
        if isinstance(breakdown, dict):
            try:
                token_sum = sum(float(value or 0) for value in breakdown.values())
                if token_sum:
                    profit_usd = max(profit_usd, token_sum)
            except (TypeError, ValueError):
                pass

        return (profit_eth, profit_usd)

    def _extract_gas_info(self, attempt: dict[str, Any]) -> dict[str, Any] | None:
        """Extract gas usage information."""
        gas_used = attempt.get("gas_used")
        if not gas_used:
            return None

        try:
            gas_used_int = int(gas_used)
        except (TypeError, ValueError):
            return None

        gas_price_wei = attempt.get("gas_price_wei") or attempt.get("gas_price")
        if gas_price_wei:
            try:
                gas_price_wei = float(gas_price_wei)
            except (TypeError, ValueError):
                gas_price_wei = self.default_gas_price_gwei * 1e9
        else:
            gas_price_wei = self.default_gas_price_gwei * 1e9

        return {
            "gas_used": gas_used_int,
            "gas_price_wei": gas_price_wei,
            "gas_price_gwei": gas_price_wei / 1e9,
        }

    def _estimate_gas_cost(
        self,
        gas_info: dict[str, Any] | None,
        eth_price: float,
    ) -> float:
        """Estimate gas cost in USD."""
        if not gas_info:
            return 0.0

        gas_eth = (gas_info["gas_used"] * gas_info["gas_price_wei"]) / 1e18
        return gas_eth * eth_price

    def _make_decision(
        self,
        max_profit_usd: float,
        gas_cost_usd: float,
        net_usd: float,
    ) -> dict[str, str]:
        """Make economic decision."""
        if max_profit_usd == 0:
            return {
                "decision": "SKIP",
                "reason": "No profit detected",
            }

        gas_ratio = gas_cost_usd / max_profit_usd if max_profit_usd > 0 else float("inf")
        if gas_ratio > self.gas_ratio_threshold:
            return {
                "decision": "SKIP",
                "reason": f"Gas cost too high ({gas_ratio:.1%} of profit)",
            }

        if net_usd >= self.min_profit_usd:
            return {
                "decision": "PURSUE",
                "reason": f"Net profit ${net_usd:.0f} exceeds threshold ${self.min_profit_usd:.0f}",
            }
        if net_usd > 0:
            return {
                "decision": "CONSIDER",
                "reason": f"Marginal profit ${net_usd:.0f} (below threshold ${self.min_profit_usd:.0f})",
            }
        return {
            "decision": "SKIP",
            "reason": "Negative or zero net profit",
        }


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

        # Use research_severity_context for real-world severity data
        research_context = ""
        if self.research_client and top_findings:
            # Get unique vulnerability types from findings
            vuln_types = {f.get("vuln_type", "") for f in top_findings if f.get("vuln_type")}
            if vuln_types:
                # Select vulnerability type deterministically (most frequent, then alphabetically)
                from collections import Counter
                vuln_type_counts = Counter(f.get("vuln_type", "") for f in top_findings if f.get("vuln_type"))
                # Get most common, break ties alphabetically
                primary_vuln = max(vuln_type_counts.items(), key=lambda x: (x[1], -ord(x[0][0]) if x[0] else 0))[0]
                try:
                    research_result = await self.research_client.research_severity_context(
                        vuln_type=primary_vuln,
                        run_context=self.run_context,
                        details=f"Found in {len(findings)} total findings across {len(vuln_types)} vulnerability types",
                    )
                    if not research_result.get("error") and not research_result.get("limited"):
                        research_context = f"\n\nReal-world severity context for {primary_vuln}:\n{research_result.get('answer', '')[:500]}"
                except Exception as e:
                    self._log_error("research_severity_failed", error=str(e))

        prompt = f"""Review these security findings and validate severity classifications.

Findings:
{json.dumps(top_findings, indent=2)}{research_context}

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
            f
            for f in findings
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
        """Compute a profitability gate from exploit attempts."""
        analyzer = EconomicAnalyzer(min_profit_usd=300.0, gas_ratio_threshold=0.5)
        return analyzer.analyze_attempts(attempts)
