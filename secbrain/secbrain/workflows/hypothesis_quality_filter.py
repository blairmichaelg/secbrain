"""Hypothesis quality filtering to optimize exploit testing efficiency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Quality scoring thresholds
RATIONALE_LENGTH_SHORT = 100
RATIONALE_LENGTH_LONG = 200
MIN_RATIONALE_SCORE = 0.5


@dataclass
class QualityScore:
    """Quality score for a hypothesis."""

    overall_score: float  # 0.0 to 1.0
    confidence_score: float
    completeness_score: float
    specificity_score: float
    rationale_score: float
    reasons: list[str]
    pass_threshold: bool


class HypothesisQualityFilter:
    """
    Filter and prioritize hypotheses based on quality metrics.

    This reduces waste by skipping low-quality hypotheses that are unlikely
    to yield successful exploits, improving overall efficiency.

    Quality factors:
    - Confidence level (from LLM)
    - Completeness (has required fields)
    - Specificity (has concrete target details)
    - Rationale quality (detailed explanation)
    """

    def __init__(
        self,
        min_confidence: float = 0.45,
        min_overall_score: float = 0.5,
        require_contract_address: bool = False,
        require_function_signature: bool = False,
    ):
        self.min_confidence = min_confidence
        self.min_overall_score = min_overall_score
        self.require_contract_address = require_contract_address
        self.require_function_signature = require_function_signature

    def evaluate_hypothesis(self, hypothesis: dict[str, Any]) -> QualityScore:
        """
        Evaluate the quality of a hypothesis.

        Args:
            hypothesis: Hypothesis dictionary with fields like confidence, contract_address, etc.

        Returns:
            QualityScore with detailed scoring
        """
        reasons = []

        # 1. Confidence score (0.0 - 1.0)
        confidence = float(hypothesis.get("confidence", 0.0))
        confidence_score = min(confidence, 1.0)
        if confidence < self.min_confidence:
            reasons.append(f"Low confidence: {confidence:.2f} < {self.min_confidence:.2f}")

        # 2. Completeness score (has required fields)
        required_fields = ["vuln_type", "rationale"]
        present_fields = sum(1 for field in required_fields if hypothesis.get(field))
        completeness_score = present_fields / len(required_fields)
        if completeness_score < 1.0:
            missing = [f for f in required_fields if not hypothesis.get(f)]
            reasons.append(f"Missing fields: {', '.join(missing)}")

        # 3. Specificity score (has concrete target details)
        specificity_factors = []

        has_contract = bool(hypothesis.get("contract_address"))
        specificity_factors.append(has_contract)
        if self.require_contract_address and not has_contract:
            reasons.append("No contract address specified")

        has_function = bool(hypothesis.get("function_signature"))
        specificity_factors.append(has_function)
        if self.require_function_signature and not has_function:
            reasons.append("No function signature specified")

        has_params = bool(hypothesis.get("function_params"))
        specificity_factors.append(has_params)

        has_exploit_steps = bool(hypothesis.get("exploit_steps"))
        specificity_factors.append(has_exploit_steps)

        specificity_score = sum(specificity_factors) / len(specificity_factors)

        # 4. Rationale quality (detailed explanation)
        rationale = str(hypothesis.get("rationale", ""))
        rationale_score = 0.0

        if len(rationale) > RATIONALE_LENGTH_SHORT:
            rationale_score += 0.3
        if len(rationale) > RATIONALE_LENGTH_LONG:
            rationale_score += 0.2

        # Check for technical terms
        technical_terms = ["reentrancy", "overflow", "oracle", "manipulation", "bypass", "exploit"]
        if any(term in rationale.lower() for term in technical_terms):
            rationale_score += 0.3

        # Check for code references
        if "0x" in rationale or "function" in rationale.lower():
            rationale_score += 0.2

        rationale_score = min(rationale_score, 1.0)

        if rationale_score < MIN_RATIONALE_SCORE:
            reasons.append("Weak rationale (too short or vague)")

        # Calculate overall score (weighted average)
        weights = {
            "confidence": 0.4,
            "completeness": 0.2,
            "specificity": 0.25,
            "rationale": 0.15,
        }

        overall_score = (
            confidence_score * weights["confidence"]
            + completeness_score * weights["completeness"]
            + specificity_score * weights["specificity"]
            + rationale_score * weights["rationale"]
        )

        pass_threshold = overall_score >= self.min_overall_score

        return QualityScore(
            overall_score=overall_score,
            confidence_score=confidence_score,
            completeness_score=completeness_score,
            specificity_score=specificity_score,
            rationale_score=rationale_score,
            reasons=reasons,
            pass_threshold=pass_threshold,
        )

    def filter_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Filter hypotheses into high-quality and low-quality groups.

        Args:
            hypotheses: List of hypothesis dictionaries

        Returns:
            Tuple of (high_quality, low_quality) hypothesis lists
        """
        high_quality = []
        low_quality = []

        for hyp in hypotheses:
            score = self.evaluate_hypothesis(hyp)

            # Attach score to hypothesis for logging/debugging
            hyp["quality_score"] = {
                "overall": score.overall_score,
                "confidence": score.confidence_score,
                "completeness": score.completeness_score,
                "specificity": score.specificity_score,
                "rationale": score.rationale_score,
                "reasons": score.reasons,
            }

            if score.pass_threshold:
                high_quality.append(hyp)
            else:
                low_quality.append(hyp)

        return high_quality, low_quality

    def prioritize_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Sort hypotheses by quality score (highest first).

        Args:
            hypotheses: List of hypothesis dictionaries

        Returns:
            Sorted list of hypotheses
        """
        # Evaluate all hypotheses
        scored = []
        for hyp in hypotheses:
            score = self.evaluate_hypothesis(hyp)
            hyp["quality_score"] = {
                "overall": score.overall_score,
                "confidence": score.confidence_score,
                "completeness": score.completeness_score,
                "specificity": score.specificity_score,
                "rationale": score.rationale_score,
                "reasons": score.reasons,
            }
            scored.append((score.overall_score, hyp))

        # Sort by score (descending)
        return [hyp for _, hyp in sorted(scored, key=lambda x: x[0], reverse=True)]
