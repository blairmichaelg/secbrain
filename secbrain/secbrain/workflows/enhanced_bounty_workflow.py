"""Enhanced bug bounty workflow integrating advanced research and Immunefi intelligence.

This workflow provides an improved bug hunting experience with:
- Immunefi platform integration for target selection
- Advanced vulnerability research and pattern discovery
- Success metrics tracking and continuous learning
- Optimized analysis based on historical performance
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.core.context import RunContext

logger = logging.getLogger(__name__)


class EnhancedBountyWorkflow:
    """
    Enhanced workflow for bug bounty hunting with cutting-edge research.
    
    Workflow stages:
    1. Target Selection - Use Immunefi data to prioritize high-value programs
    2. Intelligence Gathering - Collect platform and research intelligence
    3. Advanced Research - Apply cutting-edge vulnerability patterns
    4. Targeted Analysis - Focus on high-probability vulnerabilities
    5. Validation - Verify findings with historical success data
    6. Submission Optimization - Use metrics to optimize submission quality
    """

    def __init__(self, run_context: RunContext):
        self.run_context = run_context

    async def select_targets_from_immunefi(
        self,
        min_bounty: int = 500_000,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Select high-value targets from Immunefi platform.
        
        Args:
            min_bounty: Minimum bounty amount to consider
            limit: Max number of targets to return
            
        Returns:
            List of prioritized targets with intelligence
        """
        from secbrain.tools.immunefi_client import ImmunefiClient

        logger.info(f"Selecting Immunefi targets with min bounty ${min_bounty:,}")

        client = ImmunefiClient()
        try:
            # Get high-value programs
            programs = await client.get_high_value_programs(
                min_bounty=min_bounty,
                limit=limit,
            )

            # Enrich with intelligence
            targets = []
            for program in programs:
                intelligence = await client.get_program_intelligence(program.id)

                targets.append({
                    "program_id": program.id,
                    "name": program.name,
                    "max_bounty": program.max_bounty,
                    "priority_score": program.get_priority_score(),
                    "blockchain": program.blockchain,
                    "intelligence": intelligence,
                })

            logger.info(f"Selected {len(targets)} high-priority targets")
            return targets

        finally:
            await client.close()

    async def gather_intelligence(
        self,
        target_program: str,
    ) -> dict[str, Any]:
        """
        Gather comprehensive intelligence for a target program.
        
        Args:
            target_program: Program ID or name
            
        Returns:
            Intelligence package with all relevant data
        """
        from secbrain.tools.immunefi_client import ImmunefiClient

        logger.info(f"Gathering intelligence for {target_program}")

        intelligence = {
            "program_details": None,
            "trending_vulnerabilities": [],
            "recommended_focus": [],
            "similar_programs": [],
        }

        client = ImmunefiClient()
        try:
            # Get program-specific intelligence
            program_intel = await client.get_program_intelligence(target_program)
            intelligence["program_details"] = program_intel.get("program", {})
            intelligence["recommended_focus"] = program_intel.get("recommended_focus_areas", [])
            intelligence["similar_programs"] = program_intel.get("similar_programs", [])

            # Get trending vulnerabilities
            trends = await client.get_trending_vulnerabilities(days=90)
            intelligence["trending_vulnerabilities"] = [
                {
                    "type": t.vulnerability_type,
                    "severity": t.severity,
                    "avg_bounty": t.avg_bounty,
                    "occurrences": t.occurrences,
                }
                for t in trends[:10]
            ]

            logger.info(f"Gathered intelligence: {len(trends)} trends, "
                       f"{len(intelligence['recommended_focus'])} focus areas")

            return intelligence

        finally:
            await client.close()

    async def conduct_advanced_research(
        self,
        target_contracts: list[str],
        protocol_name: str = "",
    ) -> dict[str, Any]:
        """
        Conduct advanced vulnerability research.
        
        Args:
            target_contracts: List of contracts to analyze
            protocol_name: Protocol name for context
            
        Returns:
            Research findings and novel hypotheses
        """
        from secbrain.agents.advanced_research_agent import AdvancedResearchAgent

        logger.info(f"Conducting advanced research on {len(target_contracts)} contracts")

        # Get research client if available
        research_client = getattr(self.run_context, 'research_client', None)

        agent = AdvancedResearchAgent(
            run_context=self.run_context,
            research_client=research_client,
        )

        # Research emerging patterns
        emerging_patterns = await agent.research_emerging_patterns(timeframe_days=90)

        # Protocol-specific research if name provided
        protocol_findings = []
        if protocol_name:
            # Default to Ethereum, could be extended to read from program config
            blockchain = "Ethereum"
            protocol_findings = await agent.analyze_protocol_specific(
                protocol_name=protocol_name,
                blockchain=blockchain,
            )

        # Generate novel hypotheses
        novel_hypotheses = await agent.generate_novel_hypotheses(
            target_contracts=target_contracts,
            context=f"Analyzing {protocol_name}" if protocol_name else "",
        )

        return {
            "emerging_patterns": [
                {
                    "title": f.title,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "attack_vectors": f.attack_vectors,
                }
                for f in emerging_patterns
            ],
            "protocol_findings": [
                {
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                }
                for f in protocol_findings
            ],
            "novel_hypotheses": novel_hypotheses,
        }

    async def optimize_analysis_with_metrics(
        self,
        hypotheses: list[dict[str, Any]],
        metrics_dir: Path | str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Optimize hypotheses using historical success metrics.
        
        Args:
            hypotheses: List of vulnerability hypotheses
            metrics_dir: Directory with metrics data
            
        Returns:
            Optimized and prioritized hypotheses
        """
        from pathlib import Path

        from secbrain.tools.bounty_metrics import BountyMetricsTracker

        if not metrics_dir:
            # Use workspace metrics directory
            workspace = Path(self.run_context.workspace_path)
            metrics_dir = workspace / "metrics"

        tracker = BountyMetricsTracker(metrics_dir)

        # Get learning insights
        insights = tracker.get_learning_insights()
        high_value_patterns = {p["pattern"] for p in insights["high_value_patterns"]}
        low_confidence_patterns = {p["pattern"] for p in insights["low_confidence_patterns"]}

        # Optimize hypotheses
        optimized = []
        for hypothesis in hypotheses:
            vuln_type = hypothesis.get("vulnerability_type", hypothesis.get("title", "unknown"))
            confidence = hypothesis.get("confidence", 0.5)

            # Check if should submit based on historical data
            decision = tracker.should_submit(
                vulnerability_type=vuln_type,
                confidence=confidence,
            )

            # Adjust priority based on historical performance
            priority_boost = 0.0
            if vuln_type in high_value_patterns:
                priority_boost = 0.3
                hypothesis["high_value_pattern"] = True
            elif vuln_type in low_confidence_patterns:
                priority_boost = -0.2
                hypothesis["low_confidence_pattern"] = True

            # Add submission recommendation
            hypothesis["submission_recommendation"] = decision
            hypothesis["priority_score"] = confidence + priority_boost

            optimized.append(hypothesis)

        # Sort by priority
        optimized.sort(key=lambda h: h.get("priority_score", 0), reverse=True)

        logger.info(f"Optimized {len(optimized)} hypotheses using historical metrics")
        return optimized

    async def run_enhanced_workflow(
        self,
        target_program: str | None = None,
        min_bounty: int = 500_000,
    ) -> dict[str, Any]:
        """
        Run complete enhanced bounty workflow.
        
        Args:
            target_program: Specific program to analyze (optional)
            min_bounty: Minimum bounty for auto-target selection
            
        Returns:
            Complete analysis results
        """
        logger.info("Starting enhanced bug bounty workflow")

        results = {
            "targets": [],
            "intelligence": {},
            "research": {},
            "optimized_hypotheses": [],
            "recommendations": [],
        }

        # Stage 1: Target Selection
        if not target_program:
            targets = await self.select_targets_from_immunefi(
                min_bounty=min_bounty,
                limit=5,
            )
            results["targets"] = targets

            if targets:
                # Use highest priority target
                target_program = targets[0]["program_id"]
                logger.info(f"Selected target: {targets[0]['name']} "
                           f"(priority: {targets[0]['priority_score']:.1f})")

        # Stage 2: Intelligence Gathering
        if target_program:
            intelligence = await self.gather_intelligence(target_program)
            results["intelligence"] = intelligence

            # Stage 3: Advanced Research
            # Extract contract names from intelligence
            program_details = intelligence.get("program_details", {})
            contracts = program_details.get("assets_in_scope", [])
            program_name = program_details.get("name", target_program)

            if contracts:
                research = await self.conduct_advanced_research(
                    target_contracts=contracts,
                    protocol_name=program_name,
                )
                results["research"] = research

                # Stage 4: Optimization with Metrics
                all_hypotheses = research.get("novel_hypotheses", [])
                if all_hypotheses:
                    optimized = await self.optimize_analysis_with_metrics(all_hypotheses)
                    results["optimized_hypotheses"] = optimized

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        logger.info("Enhanced workflow complete")
        return results

    def _generate_recommendations(self, results: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations from workflow results."""
        recommendations = []

        # Target recommendations
        if results["targets"]:
            top_target = results["targets"][0]
            recommendations.append(
                f"Focus on {top_target['name']} - "
                f"${top_target['max_bounty']:,} max bounty, "
                f"priority score {top_target['priority_score']:.1f}/100"
            )

        # Research-based recommendations
        research = results.get("research", {})
        if research.get("emerging_patterns"):
            top_patterns = research["emerging_patterns"][:3]
            recommendations.append(
                f"Prioritize {len(top_patterns)} emerging vulnerability patterns with "
                f"high severity ratings"
            )

        # Intelligence-based recommendations
        intelligence = results.get("intelligence", {})
        if intelligence.get("recommended_focus"):
            focus_areas = intelligence["recommended_focus"][:3]
            recommendations.append(
                f"Concentrate analysis on: {', '.join(focus_areas)}"
            )

        # Hypothesis recommendations
        if results.get("optimized_hypotheses"):
            high_priority = [
                h for h in results["optimized_hypotheses"]
                if h.get("priority_score", 0) > 0.7
            ]
            if high_priority:
                recommendations.append(
                    f"Investigate {len(high_priority)} high-priority hypotheses "
                    f"with historical success patterns"
                )

        return recommendations


async def run_enhanced_bounty_hunt(
    run_context: RunContext,
    target_program: str | None = None,
    min_bounty: int = 500_000,
) -> dict[str, Any]:
    """
    Convenience function to run enhanced bounty workflow.
    
    Args:
        run_context: Run context with configuration
        target_program: Specific program to analyze (optional)
        min_bounty: Minimum bounty for target selection
        
    Returns:
        Complete analysis results
    """
    workflow = EnhancedBountyWorkflow(run_context)
    return await workflow.run_enhanced_workflow(
        target_program=target_program,
        min_bounty=min_bounty,
    )
