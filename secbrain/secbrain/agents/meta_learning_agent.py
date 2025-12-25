"""Meta-learning agent - tracks performance and updates strategies."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class MetaLearningAgent(BaseAgent):
    """
    Meta-learning agent.

    Responsibilities:
    - Tracks which hypotheses/techniques worked
    - Uses research to compare to external writeups
    - Informs future runs
    """

    name = "meta_learning"
    phase = "meta"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Execute meta-learning phase."""
        self._log("starting_meta_learning")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        # Collect data from all phases
        ingest_data = kwargs.get("ingest_data", {})
        recon_data = kwargs.get("recon_data", {})
        hypothesis_data = kwargs.get("hypothesis_data", {})
        exploit_data = kwargs.get("exploit_data", {})
        triage_data = kwargs.get("triage_data", {})

        # Analyze run performance
        metrics = self._calculate_metrics(
            recon_data,
            hypothesis_data,
            exploit_data,
            triage_data,
        )

        # Analyze what worked and what didn't
        analysis = await self._analyze_effectiveness(
            hypothesis_data,
            exploit_data,
            triage_data,
        )

        # Research: compare to known patterns
        if self.research_client:
            insights = await self._research_patterns(
                ingest_data.get("program_name", ""),
                triage_data.get("findings", []),
            )
            analysis["external_insights"] = insights

        # Generate recommendations for future runs
        recommendations = await self._generate_recommendations(
            metrics,
            analysis,
        )

        # Store learnings
        learnings = {
            "run_id": self.run_context.run_id,
            "program": ingest_data.get("program_name", ""),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "recommendations": recommendations,
        }

        await self._store_learnings(learnings)

        return self._success(
            message="Meta-learning complete",
            data=learnings,
        )

    def _calculate_metrics(
        self,
        recon_data: dict[str, Any],
        hypothesis_data: dict[str, Any],
        exploit_data: dict[str, Any],
        triage_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate run metrics."""
        # Recon metrics
        assets_found = len(recon_data.get("assets", []))
        live_hosts = recon_data.get("live_hosts_count", 0)

        # Hypothesis metrics
        hypotheses_generated = len(hypothesis_data.get("hypotheses", []))
        hypotheses_by_type = hypothesis_data.get("by_vuln_type", {})

        # Exploit metrics
        tested = exploit_data.get("tested_count", 0)
        confirmed = exploit_data.get("confirmed_count", 0)
        confirmation_rate = confirmed / tested if tested > 0 else 0

        # Triage metrics
        findings = triage_data.get("findings", [])
        by_severity = triage_data.get("by_severity", {})

        return {
            "recon": {
                "assets_discovered": assets_found,
                "live_hosts": live_hosts,
            },
            "hypotheses": {
                "total_generated": hypotheses_generated,
                "by_type": hypotheses_by_type,
            },
            "exploitation": {
                "tested": tested,
                "confirmed": confirmed,
                "confirmation_rate": round(confirmation_rate, 3),
            },
            "findings": {
                "total": len(findings),
                "by_severity": by_severity,
            },
        }

    async def _analyze_effectiveness(
        self,
        hypothesis_data: dict[str, Any],
        exploit_data: dict[str, Any],
        triage_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze what techniques were effective."""
        hypotheses = hypothesis_data.get("hypotheses", [])
        findings = triage_data.get("findings", [])

        # Track which hypothesis types led to findings
        effective_types: dict[str, int] = {}
        ineffective_types: dict[str, int] = {}

        finding_hyp_ids = {f.get("hypothesis_id") for f in findings}

        for hyp in hypotheses:
            vtype = hyp.get("vuln_type", "unknown")
            if hyp.get("id") in finding_hyp_ids:
                effective_types[vtype] = effective_types.get(vtype, 0) + 1
            else:
                ineffective_types[vtype] = ineffective_types.get(vtype, 0) + 1

        # Calculate success rates by type
        success_rates: dict[str, float] = {}
        for vtype in set(effective_types.keys()) | set(ineffective_types.keys()):
            successful = effective_types.get(vtype, 0)
            total = successful + ineffective_types.get(vtype, 0)
            success_rates[vtype] = round(successful / total, 3) if total > 0 else 0

        # Calculate hypothesis effectiveness with detailed breakdown
        hypothesis_effectiveness = self._calculate_hypothesis_effectiveness(
            hypotheses, findings
        )

        return {
            "effective_types": effective_types,
            "ineffective_types": ineffective_types,
            "success_rates": success_rates,
            "top_performing": sorted(
                success_rates.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            "hypothesis_effectiveness": hypothesis_effectiveness,
        }

    def _calculate_hypothesis_effectiveness(
        self,
        hypotheses: list[dict[str, Any]],
        findings: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Track which hypothesis types yield confirmed findings.

        This method provides detailed statistics on hypothesis generation
        effectiveness, helping identify which vulnerability types have the
        highest success rates and should be prioritized in future runs.

        Args:
            hypotheses: All generated hypotheses
            findings: Confirmed findings from exploitation

        Returns:
            Dictionary mapping vuln_type to stats including generated count,
            confirmed count, and success rate.
        """
        by_type: dict[str, dict[str, Any]] = {}

        # Initialize counts for all hypothesis types
        for hyp in hypotheses:
            vtype = hyp.get("vuln_type", "unknown")
            if vtype not in by_type:
                by_type[vtype] = {
                    "generated": 0,
                    "confirmed": 0,
                    "success_rate": 0.0,
                    "avg_confidence": 0.0,
                    "confidence_sum": 0.0,
                    "hypothesis_ids": [],
                    "finding_ids": [],
                }
            by_type[vtype]["generated"] += 1
            by_type[vtype]["hypothesis_ids"].append(hyp.get("id"))
            by_type[vtype]["confidence_sum"] += float(hyp.get("confidence", 0) or 0)

        # Track which hypotheses led to findings
        for finding in findings:
            hyp_id = finding.get("hypothesis_id")
            if not hyp_id:
                continue

            # Find the matching hypothesis
            matching_hyp = next(
                (h for h in hypotheses if h.get("id") == hyp_id),
                None
            )
            if matching_hyp:
                vtype = matching_hyp.get("vuln_type", "unknown")
                if vtype in by_type:
                    by_type[vtype]["confirmed"] += 1
                    by_type[vtype]["finding_ids"].append(finding.get("id"))

        # Calculate success rates and average confidence
        for vtype, stats in by_type.items():
            if stats["generated"] > 0:
                stats["success_rate"] = round(
                    stats["confirmed"] / stats["generated"], 3
                )
                stats["avg_confidence"] = round(
                    stats["confidence_sum"] / stats["generated"], 3
                )
            # Clean up temporary field
            del stats["confidence_sum"]

        return by_type

    async def _research_patterns(
        self,
        program_name: str,
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Research external patterns and writeups."""
        if not findings:
            return {}

        # Get the most common finding types
        vuln_types = [f.get("vuln_type", "") for f in findings]
        if not vuln_types:
            return {}

        # Research patterns for this type of target
        result = await self._research(
            question=f"What vulnerability patterns are commonly reported in bug bounty programs similar to {program_name}?",
            context=f"Found vulnerabilities: {', '.join(set(vuln_types))}",
        )

        return {
            "patterns": result.get("answer", "")[:500],
            "sources": result.get("sources", []),
        }

    async def _generate_recommendations(
        self,
        metrics: dict[str, Any],
        analysis: dict[str, Any],
    ) -> list[str]:
        """Generate recommendations for future runs."""
        recommendations: list[str] = []

        # Based on confirmation rate
        conf_rate = metrics.get("exploitation", {}).get("confirmation_rate", 0)
        if conf_rate < 0.1:
            recommendations.append(
                "Low confirmation rate - consider improving hypothesis quality or testing methodology"
            )
        elif conf_rate > 0.3:
            recommendations.append(
                "High confirmation rate - current approach is effective, consider expanding scope"
            )

        # Based on effective types
        top_types = analysis.get("top_performing", [])
        if top_types:
            best_type = top_types[0][0]
            recommendations.append(
                f"Focus on {best_type} vulnerabilities - highest success rate"
            )

        # Based on findings count
        finding_count = metrics.get("findings", {}).get("total", 0)
        if finding_count == 0:
            recommendations.append(
                "No findings - consider expanding attack surface or trying new techniques"
            )

        # Use worker model for additional insights
        if self.worker_model:
            prompt = f"""Based on this security testing run analysis, provide 2-3 specific recommendations.

Metrics:
{json.dumps(metrics, indent=2)}

Analysis:
{json.dumps(analysis, indent=2)}

Provide actionable recommendations for improving future runs."""

            response = await self._call_worker(prompt)
            recommendations.append(f"AI Insights: {response[:300]}")

        return recommendations

    async def _store_learnings(self, learnings: dict[str, Any]) -> None:
        """Store learnings for future reference."""
        # Store in database if available
        if self.storage:
            await self.storage.save_asset({
                "id": f"learning-{self.run_context.run_id}",
                "type": "meta_learning",
                "value": json.dumps(learnings),
                "metadata": {
                    "program": learnings.get("program"),
                    "timestamp": learnings.get("timestamp"),
                },
            })

        # Also save to file for easy access
        learnings_dir = self.run_context.workspace_path / "learnings"
        learnings_dir.mkdir(parents=True, exist_ok=True)

        file_path = learnings_dir / f"{self.run_context.run_id}.json"
        file_path.write_text(json.dumps(learnings, indent=2))

        self._log("learnings_stored", path=str(file_path))
