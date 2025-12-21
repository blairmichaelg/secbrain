"""Enhanced hypothesis generation with research-driven targeting."""

from __future__ import annotations

from typing import Any

from eth_utils import is_address  # type: ignore[attr-defined]

from secbrain.agents.research_orchestrator import ResearchOrchestrator, ResearchQuery

# Confidence threshold for high-confidence hypotheses
HIGH_CONFIDENCE_THRESHOLD = 0.7


class HypothesisEnhancer:
    """
    Enhance hypotheses using:
    - Research-validated patterns
    - Historical exploit data
    - Protocol-specific knowledge
    - Failure feedback loops
    """

    def __init__(self, research_orch: ResearchOrchestrator):
        self.research = research_orch

    async def enhance_contract_hypotheses(
        self,
        contract_metadata: dict[str, Any],
        static_hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enhance hypotheses with research-driven insights."""

        protocol_type = contract_metadata.get("classification", {}).get("protocol_type", "generic")
        functions = contract_metadata.get("functions", [])

        # Research protocol-specific vulnerabilities
        protocol_research = await self.research.research_protocol_type(
            protocol_type=protocol_type,
            functions=functions,
            priority=9,
        )

        if protocol_research:
            # Extract vulnerability types from research
            research_vulns = self._extract_vulnerability_types(protocol_research.answer)

            # Boost confidence for hypotheses matching research
            for hyp in static_hypotheses:
                vuln_type = hyp.get("vuln_type", "")
                if vuln_type in research_vulns:
                    hyp["confidence"] = min(hyp.get("confidence", 0.5) * 1.3, 0.95)
                    hyp["research_validated"] = True
                    hyp["research_context"] = protocol_research.answer[:300]

        # Research each high-confidence hypothesis
        for hyp in static_hypotheses:
            vuln_type = hyp.get("vuln_type", "")
            confidence = hyp.get("confidence", 0)
            if confidence >= HIGH_CONFIDENCE_THRESHOLD and vuln_type:
                pattern_research = await self.research.research_vulnerability_pattern(
                    vuln_type=vuln_type,
                    contract_context=f"{protocol_type} with {len(functions)} functions",
                    priority=7,
                )

                if pattern_research:
                    hyp["exploitation_guidance"] = pattern_research.answer[:500]
                    hyp["research_sources"] = pattern_research.sources[:3]

        return static_hypotheses

    async def refine_from_failures(
        self,
        failed_attempts: list[dict[str, Any]],
        original_hypothesis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate refined hypotheses from failed exploit attempts."""

        # Validate required keys in original_hypothesis
        required_keys = ["vuln_type", "id"]
        for key in required_keys:
            if key not in original_hypothesis:
                # Return empty list if required keys are missing
                return []

        refinements = []

        # Group failures by type
        failure_types: dict[str, list[dict[str, Any]]] = {}
        for attempt in failed_attempts:
            category = self._categorize_failure(attempt)
            if category not in failure_types:
                failure_types[category] = []
            failure_types[category].append(attempt)

        # Research validation for near-misses
        if "insufficient_profit" in failure_types:
            # This was close - research profit amplification
            query = ResearchQuery(
                question=f"What techniques amplify profit in {original_hypothesis['vuln_type']} exploits? Consider flash loans, leverage, and multi-step attacks.",
                context="Exploit succeeded but profit below threshold",
                priority=8,
                phase="exploit",
                tags=[original_hypothesis['vuln_type'], "amplification"],
            )
            await self.research.queue_research(query)
            results = await self.research.execute_batch(max_queries=1)

            if results:
                refinements.append({
                    **original_hypothesis,
                    "id": f"refined-{original_hypothesis['id']}",
                    "confidence": min(original_hypothesis.get("confidence", 0.5) * 1.2, 0.95),
                    "exploit_notes": [
                        *original_hypothesis.get("exploit_notes", []),
                        "Add flash loan leverage",
                        "Consider multi-hop arbitrage",
                        results[0].answer[:200],
                    ],
                    "expected_profit_hint_eth": original_hypothesis.get("expected_profit_hint_eth", 0) * 3,
                })

        if "access_control" in failure_types:
            # Research privilege escalation
            query = ResearchQuery(
                question=f"What are common access control bypasses in {original_hypothesis['vuln_type']} scenarios? Include delegate calls, signature replay, and front-running.",
                context="Direct call failed due to permissions",
                priority=8,
                phase="exploit",
                tags=[original_hypothesis['vuln_type'], "access_control"],
            )
            await self.research.queue_research(query)
            results = await self.research.execute_batch(max_queries=1)

            if results:
                refinements.append({
                    **original_hypothesis,
                    "id": f"refined-{original_hypothesis['id']}",
                    "vuln_type": "access_control_bypass",
                    "confidence": 0.7,
                    "exploit_notes": [
                        "Try delegate call path",
                        "Check for signature reuse",
                        results[0].answer[:200],
                    ],
                })

        return refinements

    async def generate_targeted_llm_prompt(
        self,
        contract_metadata: dict[str, Any],
        research_context: str = "",
    ) -> str:
        """Generate a highly targeted LLM prompt using research context."""

        protocol_type = contract_metadata.get("classification", {}).get("protocol_type", "generic")
        functions = contract_metadata.get("functions", [])[:20]
        address = contract_metadata.get("address", "")

        # Validate and sanitize address
        if address and not is_address(address):
            # If address is invalid, use placeholder
            address = "0x0000000000000000000000000000000000000000"

        # Get protocol-specific patterns from research
        protocol_patterns = self._extract_patterns_from_research(research_context)

        return f"""Generate EXPLOIT-FOCUSED hypotheses for this smart contract.

CONTRACT: {address}
PROTOCOL: {protocol_type}
KEY FUNCTIONS: {', '.join(functions[:10])}

RESEARCH CONTEXT:
{research_context[:800]}

FOCUS AREAS (from research):
{chr(10).join(f'- {p}' for p in protocol_patterns[:5])}

For each hypothesis, provide a JSON object with:
{{
  "vuln_type": "specific_vulnerability_class",
  "confidence": 0.0-1.0,
  "rationale": "why this specific contract is vulnerable",
  "contract_address": "{address}",
  "function_signature": "exactFunction(type1,type2)",
  "exploit_notes": ["step1", "step2", "step3"],
  "expected_profit_hint_eth": estimated_eth_profit
}}

CONSTRAINTS:
1. Only include vulnerabilities with clear exploitation path
2. Confidence >= 0.6 (we filter lower quality)
3. Must cite specific functions from the provided list
4. Focus on {protocol_type}-specific issues first

Return ONLY a JSON array of 3-5 hypotheses. No markdown, no prose."""

    def _extract_vulnerability_types(self, research_text: str) -> set[str]:
        """Extract vulnerability type keywords from research."""
        # Simple keyword extraction
        vuln_keywords = {
            "reentrancy", "oracle", "flash_loan", "access_control",
            "precision", "rounding", "sandwich", "mev", "front_running",
            "delegation", "signature", "replay", "inflation", "manipulation",
        }

        text_lower = research_text.lower()
        found = set()

        for keyword in vuln_keywords:
            if keyword in text_lower:
                found.add(keyword)

        return found

    def _extract_patterns_from_research(self, research_text: str) -> list[str]:
        """Extract actionable patterns from research text."""
        # Split into sentences and find pattern indicators
        sentences = research_text.split(". ")
        patterns = []

        pattern_indicators = ["attack", "exploit", "vulnerability", "bypass", "manipulate"]

        for sentence in sentences[:10]:
            if any(indicator in sentence.lower() for indicator in pattern_indicators):
                patterns.append(sentence.strip())

        return patterns[:5]

    def _categorize_failure(self, attempt: dict[str, Any]) -> str:
        """Categorize failure type for targeted refinement."""
        revert = (attempt.get("revert_reason") or "").lower()

        # Check balance/liquidity before insufficient to avoid false positives
        if "balance" in revert or "liquidity" in revert:
            return "insufficient_balance"
        if "slippage" in revert or "deadline" in revert:
            return "timing_constraint"
        if "overflow" in revert or "underflow" in revert:
            return "arithmetic"
        if "insufficient" in revert or "profit" in revert:
            return "insufficient_profit"
        if "permission" in revert or "authorized" in revert or "owner" in revert:
            return "access_control"

        return "unknown"

    def calibrate_confidence(
        self,
        hypothesis: dict[str, Any],
        research_validated: bool,
        similar_exploits_found: bool,
        failure_feedback: dict[str, Any] | None = None,
    ) -> float:
        """Calibrate hypothesis confidence using multiple signals."""

        # Safely extract and validate confidence value
        raw_confidence = hypothesis.get("confidence", 0.5)
        try:
            base_confidence = float(raw_confidence)
        except (TypeError, ValueError):
            base_confidence = 0.5

        # Boost for research validation
        if research_validated:
            base_confidence *= 1.25

        # Boost for similar historical exploits
        if similar_exploits_found:
            base_confidence *= 1.15

        # Adjust based on failure feedback
        if failure_feedback:
            failure_count = int(failure_feedback.get("attempt_count", 0) or 0)
            if failure_count > 0:
                # Penalize if many attempts failed
                base_confidence *= (0.95 ** failure_count)

            near_misses = int(failure_feedback.get("near_miss_count", 0) or 0)
            if near_misses > 0:
                # Boost if we had near-misses, with diminishing effect as failures grow
                near_miss_boost = 1.0 + 0.1 / (1 + failure_count)
                base_confidence *= near_miss_boost

        # Cap at 0.95
        return min(base_confidence, 0.95)
