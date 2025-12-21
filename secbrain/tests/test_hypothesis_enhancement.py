"""Tests for research orchestrator and hypothesis enhancer."""

import pytest

from secbrain.agents.hypothesis_enhancer import HypothesisEnhancer
from secbrain.agents.research_orchestrator import (
    ResearchOrchestrator,
    ResearchQuery,
)


class MockPerplexityResearch:
    """Mock research client for testing."""

    def __init__(self):
        self.calls = []

    async def ask_research(self, question, context, run_context, ttl_hours=24):
        """Mock research call."""
        self.calls.append({
            "question": question,
            "context": context,
            "ttl_hours": ttl_hours,
        })
        return {
            "answer": f"Mock answer for: {question[:50]}",
            "sources": ["mock-source-1", "mock-source-2"],
            "cached": False,
            "error": False,
        }


class MockRunContext:
    """Mock run context for testing."""

    def __init__(self):
        self.dry_run = False
        self.cache = {}

    def get_cached_research(self, key):
        return self.cache.get(key)

    def cache_research(self, key, value):
        self.cache[key] = value


@pytest.mark.asyncio
async def test_research_orchestrator_queue():
    """Test queueing research queries."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)

    # Queue some queries with different priorities
    await orchestrator.queue_research(
        ResearchQuery(
            question="Low priority question",
            context="test",
            priority=3,
        )
    )
    await orchestrator.queue_research(
        ResearchQuery(
            question="High priority question",
            context="test",
            priority=9,
        )
    )
    await orchestrator.queue_research(
        ResearchQuery(
            question="Medium priority question",
            context="test",
            priority=5,
        )
    )

    # Execute batch
    results = await orchestrator.execute_batch(max_queries=3)

    # Check that results are in priority order (highest first)
    assert len(results) == 3

    # Validate that the underlying research client was called in priority order
    called_questions = [call["question"] for call in mock_client.calls]
    assert called_questions == [
        "High priority question",
        "Medium priority question",
        "Low priority question",
    ]


@pytest.mark.asyncio
async def test_research_orchestrator_batch_limit():
    """Test batch execution with max query limit."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)

    # Queue 5 queries
    for i in range(5):
        await orchestrator.queue_research(
            ResearchQuery(
                question=f"Question {i}",
                context="test",
                priority=i,
            )
        )

    # Execute only 2 at a time
    results = await orchestrator.execute_batch(max_queries=2)
    assert len(results) == 2

    # Execute remaining
    results = await orchestrator.execute_batch(max_queries=10)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_research_orchestrator_protocol_type():
    """Test protocol type research."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)

    result = await orchestrator.research_protocol_type(
        protocol_type="defi_vault",
        functions=["deposit", "withdraw", "mint"],
        priority=8,
    )

    assert result is not None
    assert "Mock answer" in result.answer
    assert len(result.sources) == 2
    assert result.error is False


@pytest.mark.asyncio
async def test_hypothesis_enhancer_extract_vulnerability_types():
    """Test vulnerability type extraction."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    research_text = """
    This contract is vulnerable to reentrancy attacks and oracle manipulation.
    Additionally, there are precision errors in the rounding logic.
    Flash_loan attacks could be used to manipulate the price.
    """

    vulns = enhancer._extract_vulnerability_types(research_text)

    assert "reentrancy" in vulns
    assert "oracle" in vulns
    assert "precision" in vulns
    assert "rounding" in vulns
    assert "flash_loan" in vulns
    assert "manipulation" in vulns


@pytest.mark.asyncio
async def test_hypothesis_enhancer_categorize_failure():
    """Test failure categorization."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    # Test different failure types
    assert enhancer._categorize_failure(
        {"revert_reason": "Insufficient profit"}
    ) == "insufficient_profit"

    assert enhancer._categorize_failure(
        {"revert_reason": "Not authorized"}
    ) == "access_control"

    assert enhancer._categorize_failure(
        {"revert_reason": "Insufficient balance"}
    ) == "insufficient_balance"

    assert enhancer._categorize_failure(
        {"revert_reason": "Deadline exceeded"}
    ) == "timing_constraint"

    assert enhancer._categorize_failure(
        {"revert_reason": "Arithmetic overflow"}
    ) == "arithmetic"

    assert enhancer._categorize_failure(
        {"revert_reason": "Unknown error"}
    ) == "unknown"


@pytest.mark.asyncio
async def test_hypothesis_enhancer_calibrate_confidence():
    """Test confidence calibration."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    # Base hypothesis
    hyp = {"confidence": 0.5}

    # Test with research validation
    conf = enhancer.calibrate_confidence(hyp, research_validated=True, similar_exploits_found=False)
    assert conf == 0.5 * 1.25

    # Test with similar exploits
    conf = enhancer.calibrate_confidence(hyp, research_validated=False, similar_exploits_found=True)
    assert conf == 0.5 * 1.15

    # Test with both
    conf = enhancer.calibrate_confidence(hyp, research_validated=True, similar_exploits_found=True)
    assert conf == 0.5 * 1.25 * 1.15

    # Test with failure feedback - new diminishing near-miss logic
    conf = enhancer.calibrate_confidence(
        hypothesis=hyp,
        research_validated=False,
        similar_exploits_found=False,
        failure_feedback={"attempt_count": 2, "near_miss_count": 1},
    )
    # New formula: 0.5 * (0.95^2) * (1.0 + 0.1/(1+2))
    expected = 0.5 * (0.95 ** 2) * (1.0 + 0.1 / 3)
    assert abs(conf - expected) < 0.001

    # Test with invalid confidence value (should default to 0.5)
    hyp_invalid = {"confidence": "invalid"}
    conf = enhancer.calibrate_confidence(
        hypothesis=hyp_invalid,
        research_validated=False,
        similar_exploits_found=False,
    )
    assert conf == 0.5

    # Test capping at 0.95
    hyp_high = {"confidence": 0.9}
    conf = enhancer.calibrate_confidence(
        hypothesis=hyp_high,
        research_validated=True,
        similar_exploits_found=True,
    )
    assert conf == 0.95


@pytest.mark.asyncio
async def test_hypothesis_enhancer_enhance_contract_hypotheses():
    """Test contract hypothesis enhancement."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    contract_metadata = {
        "classification": {"protocol_type": "defi_vault"},
        "functions": ["deposit", "withdraw", "mint", "redeem"],
    }

    static_hypotheses = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.6,
        },
        {
            "vuln_type": "oracle",
            "confidence": 0.7,
        },
    ]

    # Mock research to return content with "reentrancy" and "oracle"
    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata,
        static_hypotheses,
    )

    # Should have 2 hypotheses
    assert len(enhanced) == 2

    # Check that confidence was boosted for research-validated hypotheses
    # Both should be boosted since mock returns both keywords
    for hyp in enhanced:
        if hyp.get("research_validated"):
            # Confidence should be boosted (original * 1.3, capped at 0.95)
            assert hyp["confidence"] > 0.6  # Original was 0.6 or 0.7
            assert "research_context" in hyp

    # Check that research context was added to high-confidence hypothesis
    oracle_hyp = next(h for h in enhanced if h["vuln_type"] == "oracle")
    assert "exploitation_guidance" in oracle_hyp
    assert "research_sources" in oracle_hyp


@pytest.mark.asyncio
async def test_hypothesis_enhancer_generate_targeted_prompt():
    """Test targeted LLM prompt generation."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    contract_metadata = {
        "classification": {"protocol_type": "amm"},
        "functions": ["swap", "addLiquidity", "removeLiquidity"],
        "address": "0x1234567890123456789012345678901234567890",
    }

    research_context = """
    Recent attacks on AMM protocols have exploited sandwich attacks and price manipulation.
    Flash loan attacks can be used to manipulate pool reserves.
    """

    prompt = await enhancer.generate_targeted_llm_prompt(
        contract_metadata,
        research_context,
    )

    # Check that prompt contains key elements
    assert "0x1234567890123456789012345678901234567890" in prompt
    assert "amm" in prompt.lower()
    assert "swap" in prompt
    assert "sandwich" in prompt.lower() or "attack" in prompt.lower()
    assert "JSON" in prompt
    assert "vuln_type" in prompt
    assert "confidence" in prompt


@pytest.mark.asyncio
async def test_hypothesis_enhancer_refine_from_failures():
    """Test hypothesis refinement from failures."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    original_hypothesis = {
        "id": "hyp-123",
        "vuln_type": "oracle_manipulation",
        "confidence": 0.7,
        "exploit_notes": ["Step 1", "Step 2"],
        "expected_profit_hint_eth": 1.0,
    }

    failed_attempts = [
        {"revert_reason": "Insufficient profit"},
        {"revert_reason": "Not authorized"},
    ]

    refinements = await enhancer.refine_from_failures(
        failed_attempts,
        original_hypothesis,
    )

    # Should have refinements for both failure types (insufficient_profit and access_control)
    assert len(refinements) == 2

    # Check that refinements have updated properties
    refinement_types = set()
    for refinement in refinements:
        assert "refined-" in refinement["id"]
        assert refinement["confidence"] > 0

        # Track refinement type to verify both were created
        if "access_control_bypass" in refinement.get("vuln_type", ""):
            refinement_types.add("access_control")
        else:
            refinement_types.add("insufficient_profit")

    # Verify both refinement types were created
    assert "access_control" in refinement_types
    assert "insufficient_profit" in refinement_types


@pytest.mark.asyncio
async def test_hypothesis_enhancer_refine_from_failures_missing_keys():
    """Test refine_from_failures with missing required keys."""
    mock_client = MockPerplexityResearch()
    mock_context = MockRunContext()
    orchestrator = ResearchOrchestrator(mock_client, mock_context)
    enhancer = HypothesisEnhancer(orchestrator)

    # Hypothesis missing required keys
    incomplete_hypothesis = {
        "confidence": 0.7,
        # Missing 'id' and 'vuln_type'
    }

    failed_attempts = [
        {"revert_reason": "Insufficient profit"},
    ]

    refinements = await enhancer.refine_from_failures(
        failed_attempts,
        incomplete_hypothesis,
    )

    # Should return empty list when required keys are missing
    assert len(refinements) == 0

