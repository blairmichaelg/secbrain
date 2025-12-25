"""Enhanced hypothesis generation with research-driven targeting."""

from __future__ import annotations

from typing import Any

from eth_utils import is_address  # type: ignore[attr-defined]

from secbrain.agents.immunefi_intelligence import ImmunefiIntelligence
from secbrain.agents.research_orchestrator import ResearchOrchestrator, ResearchQuery
from secbrain.agents.threshold_network_patterns import ThresholdNetworkPatterns

# Confidence threshold for high-confidence hypotheses
HIGH_CONFIDENCE_THRESHOLD = 0.7


class HypothesisEnhancer:
    """
    Enhance hypotheses using:
    - Research-validated patterns
    - Historical exploit data
    - Protocol-specific knowledge
    - Failure feedback loops
    - Immunefi intelligence
    - Threshold Network specific patterns
    """

    def __init__(self, research_orch: ResearchOrchestrator):
        # Keep both for backward-compat with older tests/consumers
        self.research_orch = research_orch
        self.research = research_orch

    async def enhance_contract_hypotheses(
        self,
        contract_metadata: dict[str, Any],
        static_hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enhance hypotheses with research-driven insights."""

        protocol_type = (
            contract_metadata.get("protocol_type")
            or contract_metadata.get("classification", {}).get("protocol_type")
            or "generic"
        )
        functions = contract_metadata.get("functions", [])
        contract_name = contract_metadata.get("name", "")
        contract_address = contract_metadata.get("address", "")

        # Add Threshold Network specific enhancements
        if protocol_type in ["threshold_network", "bridge"] or any(
            name.lower() in contract_name.lower()
            for name in ["tbtc", "bridge", "wallet", "threshold", "staking"]
        ):
            static_hypotheses = await self._enhance_threshold_network_hypotheses(
                contract_name, contract_address, functions, static_hypotheses
            )

        # Add Immunefi intelligence enhancements
        static_hypotheses = self._enhance_with_immunefi_intelligence(
            protocol_type, contract_name, functions, static_hypotheses
        )

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

    async def _enhance_threshold_network_hypotheses(
        self,
        contract_name: str,
        contract_address: str,
        functions: list[str],
        hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Add Threshold Network specific hypothesis enhancements."""
        # Research Threshold Network specific patterns
        threshold_research = await self.research.research_threshold_network_patterns(
            contract_name=contract_name,
            functions=functions,
            priority=9,
        )

        # Get Threshold Network patterns for this contract
        threshold_patterns = ThresholdNetworkPatterns.get_patterns_for_contract(contract_name)

        # Build a lookup from vulnerability type to Threshold pattern for efficient matching
        pattern_by_type = {
            pattern.pattern_type.value: pattern for pattern in threshold_patterns
        }

        # Boost confidence for Threshold Network specific vulnerabilities
        for hyp in hypotheses:
            vuln_type = hyp.get("vuln_type", "")

            # Check if this vulnerability type matches a Threshold pattern via O(1) lookup
            pattern = pattern_by_type.get(vuln_type)
            if pattern is not None:
                # Boost confidence significantly for known high-value patterns
                hyp["confidence"] = min(hyp.get("confidence", 0.5) * 1.5, 0.98)
                hyp["threshold_network_pattern"] = True
                hyp["max_bounty_usd"] = pattern.max_bounty_usd
                hyp["immunefi_severity"] = pattern.severity.value
                hyp["detection_heuristics"] = pattern.detection_heuristics
                hyp["exploitation_steps"] = pattern.exploitation_steps

        # Add research context if available
        if threshold_research:
            for hyp in hypotheses:
                if hyp.get("threshold_network_pattern"):
                    hyp["threshold_research"] = threshold_research.answer[:400]

        return hypotheses

    def _enhance_with_immunefi_intelligence(
        self,
        protocol_type: str,
        contract_name: str,
        functions: list[str],
        hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enhance hypotheses with Immunefi intelligence."""
        # Get relevant vulnerability patterns for this protocol type
        immunefi_patterns = ImmunefiIntelligence.get_vulnerability_patterns_for_protocol(protocol_type)

        # Build a lookup from normalized common pattern to Immunefi patterns for O(1) matching
        pattern_lookup: dict[str, Any] = {}
        for pattern in immunefi_patterns:
            for common_pattern in pattern.common_patterns:
                key = str(common_pattern).lower()
                if key not in pattern_lookup:
                    pattern_lookup[key] = pattern

        for hyp in hypotheses:
            vuln_type = hyp.get("vuln_type", "")
            function_name = hyp.get("function_signature", "").split("(")[0]

            # Track if we found a pattern match
            pattern_matched = False

            # Check if vulnerability matches known Immunefi patterns using exact (case-insensitive) match
            matched_pattern = None
            vuln_type_key = str(vuln_type).lower()
            matched_pattern = pattern_lookup.get(vuln_type_key)

            if matched_pattern is not None:
                hyp["immunefi_pattern"] = matched_pattern.name
                hyp["typical_bounty_range"] = matched_pattern.typical_bounty_range
                hyp["detection_techniques"] = matched_pattern.detection_techniques
                hyp["recent_examples"] = matched_pattern.recent_examples[:2]
                # Boost confidence for well-known patterns
                hyp["confidence"] = min(hyp.get("confidence", 0.5) * 1.2, 0.95)
                pattern_matched = True

            # Add detection priority based on contract and function
            priority = ImmunefiIntelligence.get_detection_priority(contract_name, function_name)
            hyp["detection_priority"] = priority
            # Only boost confidence for high-priority targets if we also have a pattern match
            if priority >= 8 and pattern_matched:
                # Additional boost for high-priority targets with known patterns
                hyp["confidence"] = min(hyp.get("confidence", 0.5) * 1.15, 0.95)

        return hypotheses

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

        # If we saw revert/unknown but no actionable category, generate a cautious refinement
        if not refinements and failed_attempts and {"revert", "unknown"} & set(failure_types.keys()):
            refinements.append({
                **original_hypothesis,
                "id": f"refined-{original_hypothesis['id']}",
                "refinement": "Add preconditions and input validation checks to bypass revert.",
                "confidence": max(original_hypothesis.get("confidence", 0.5) * 0.9, 0.1),
            })

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

        if "insufficient_balance" in failure_types:
            refinements.append({
                **original_hypothesis,
                "id": f"refined-{original_hypothesis['id']}",
                "refinement": "Adjust balances/allowances or use smaller chunks to bypass insufficient balance errors.",
                "confidence": max(original_hypothesis.get("confidence", 0.5) * 0.85, 0.1),
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
                    # Lower confidence because direct access failed
                    "confidence": max(min(original_hypothesis.get("confidence", 0.5) * 0.7, 0.5), 0.05),
                    "refinement": "Identify access control bypass (delegatecall, signature replay, frontrun).",
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

        protocol_type = (
            contract_metadata.get("protocol_type")
            or contract_metadata.get("classification", {}).get("protocol_type")
            or "generic"
        )
        functions = contract_metadata.get("functions", [])[:20]
        address = contract_metadata.get("address", "")
        name = contract_metadata.get("name", "")

        # Validate and sanitize address (but keep provided one if present for UX/tests)
        if address and not is_address(address):
            # Keep the provided address to surface context instead of zeroing it out
            pass
        elif not address:
            address = "0x0000000000000000000000000000000000000000"

        # Get protocol-specific patterns from research
        protocol_patterns = self._extract_patterns_from_research(research_context)

        return f"""Generate EXPLOIT-FOCUSED hypotheses for this smart contract.

CONTRACT: {address}
NAME: {name}
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
        revert = (attempt.get("revert_reason") or attempt.get("error") or "").lower()

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
        if "revert" in revert:
            return "revert"

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
