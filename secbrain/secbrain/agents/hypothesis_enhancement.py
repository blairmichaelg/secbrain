"""Hypothesis enhancement using research."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.agents.research_orchestrator import ResearchOrchestrator, ResearchQuery


class HypothesisEnhancer:
    """
    Enhances vulnerability hypotheses using research.

    Features:
    - Boosts confidence based on research validation
    - Generates targeted LLM prompts with research context
    - Refines hypotheses from failed exploit attempts
    """

    def __init__(self, research_orch: ResearchOrchestrator):
        self.research_orch = research_orch

    async def enhance_contract_hypotheses(
        self,
        contract_metadata: dict[str, Any],
        static_hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Enhance static hypotheses with research validation.

        Args:
            contract_metadata: Contract metadata including protocol type, functions, etc.
            static_hypotheses: List of hypotheses generated from static analysis

        Returns:
            Enhanced hypotheses with boosted confidence and research validation flags
        """
        protocol_type = contract_metadata.get("protocol_type", "generic")

        # Research protocol-specific vulnerabilities
        research_result = await self.research_orch.research_protocol_type(
            protocol_type=protocol_type,
            functions=contract_metadata.get("functions", []),
            priority=8,
        )

        if not research_result or not research_result.answer:
            # No research available, return hypotheses as-is
            return static_hypotheses

        # Extract vulnerability types mentioned in research
        research_answer_lower = research_result.answer.lower()
        research_vuln_types = set()

        # Common vulnerability keywords to look for
        vuln_keywords = {
            "reentrancy": ["reentrancy", "re-entrancy", "reentrant"],
            "oracle_manipulation": ["oracle", "price manipulation", "oracle attack"],
            "flash_loan": ["flash loan", "flash-loan", "flashloan"],
            "access_control": ["access control", "unauthorized", "permission"],
            "integer_overflow": ["overflow", "underflow", "arithmetic"],
            "mev_sandwich": ["mev", "sandwich", "frontrun", "front-run"],
        }

        for vuln_type, keywords in vuln_keywords.items():
            if any(keyword in research_answer_lower for keyword in keywords):
                research_vuln_types.add(vuln_type)

        # Enhance hypotheses
        enhanced_hypotheses = []
        for hyp in static_hypotheses:
            enhanced_hyp = dict(hyp)
            vuln_type = hyp.get("vuln_type", "")

            # Boost confidence if vulnerability type is validated by research
            if vuln_type in research_vuln_types:
                current_confidence = hyp.get("confidence", 0.5)
                boost_amount = 0.15  # Boost by 15%
                enhanced_hyp["confidence"] = min(1.0, current_confidence + boost_amount)
                enhanced_hyp["research_validated"] = True
                enhanced_hyp["research_source"] = "protocol_research"
            else:
                enhanced_hyp["research_validated"] = False

            enhanced_hypotheses.append(enhanced_hyp)

        return enhanced_hypotheses

    async def generate_targeted_llm_prompt(
        self,
        contract_metadata: dict[str, Any],
        research_context: str,
    ) -> str:
        """
        Generate a targeted LLM prompt using research context.

        Args:
            contract_metadata: Contract metadata
            research_context: Research context from protocol-specific research

        Returns:
            Concise prompt for LLM hypothesis generation
        """
        name = contract_metadata.get("name", "Unknown")
        address = contract_metadata.get("address", "")
        chain_id = contract_metadata.get("chain_id", 1)
        protocol_type = contract_metadata.get("protocol_type", "generic")
        functions = contract_metadata.get("functions", [])

        # Limit functions to most relevant ones
        functions_preview = functions[:8]

        # Truncate research context
        research_snippet = research_context[:400] if research_context else "No research available"

        prompt = f"""Contract: {name} ({address})
Chain: {chain_id}
Protocol: {protocol_type}
Functions (sample): {', '.join(functions_preview)}

Research Context:
{research_snippet}

Generate 3-5 exploit hypotheses as JSON array. Format:
{{"vuln_type":"","confidence":0.8,"rationale":"","function_signature":"","exploit_notes":[]}}

Focus on {protocol_type}-specific high-severity issues."""

        return prompt

    async def refine_from_failures(
        self,
        failed_attempts: list[dict[str, Any]],
        original_hypothesis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Refine hypotheses based on failed exploit attempts.

        Args:
            failed_attempts: List of failed exploit attempts with error details
            original_hypothesis: The original hypothesis that led to failures

        Returns:
            List of refined hypotheses
        """
        if not failed_attempts:
            return []

        # Extract common failure patterns
        failure_reasons = []
        for attempt in failed_attempts:
            error = attempt.get("error", "")
            if error:
                failure_reasons.append(error.lower())

        # Generate refined hypotheses based on failure patterns
        refined_hypotheses = []

        # Check for common failure patterns
        has_revert = any("revert" in reason for reason in failure_reasons)
        has_insufficient_balance = any("insufficient" in reason or "balance" in reason for reason in failure_reasons)
        has_access_denied = any("access" in reason or "unauthorized" in reason or "forbidden" in reason for reason in failure_reasons)

        if has_revert:
            # Add a hypothesis about missing preconditions
            refined_hypotheses.append({
                **original_hypothesis,
                "id": f"{original_hypothesis.get('id', 'hyp')}-refined-revert",
                "confidence": original_hypothesis.get("confidence", 0.5) * 0.8,  # Lower confidence
                "rationale": f"Original hypothesis refined: {original_hypothesis.get('rationale', '')} - Failed due to revert, may need different preconditions",
                "refinement": "check_preconditions",
            })

        if has_insufficient_balance:
            # Add a hypothesis about balance requirements
            refined_hypotheses.append({
                **original_hypothesis,
                "id": f"{original_hypothesis.get('id', 'hyp')}-refined-balance",
                "confidence": original_hypothesis.get("confidence", 0.5) * 0.9,
                "rationale": f"Original hypothesis refined: {original_hypothesis.get('rationale', '')} - May require initial balance or tokens",
                "refinement": "balance_requirements",
            })

        if has_access_denied:
            # Reduce confidence for access control issues
            refined_hypotheses.append({
                **original_hypothesis,
                "id": f"{original_hypothesis.get('id', 'hyp')}-refined-access",
                "confidence": original_hypothesis.get("confidence", 0.5) * 0.5,  # Significantly lower
                "rationale": f"Original hypothesis refined: {original_hypothesis.get('rationale', '')} - Access control restrictions detected",
                "refinement": "access_control_blocked",
            })

        return refined_hypotheses
