"""Tests for HypothesisEnhancer."""

from __future__ import annotations

import pytest

from secbrain.agents.hypothesis_enhancement import HypothesisEnhancer
from secbrain.agents.research_orchestrator import ResearchOrchestrator


class MockRunContext:
    """Mock RunContext for testing."""

    def is_killed(self):
        return False


class MockResearchClient:
    """Mock research client for testing."""

    def __init__(self, research_response: dict | None = None):
        self.research_response = research_response or {
            "answer": "Common vulnerabilities include reentrancy, oracle manipulation, and flash loan attacks",
            "confidence": 0.8,
            "sources": ["source1"],
        }

    async def research(self, question: str, context: str = "") -> dict:
        """Mock research method."""
        return self.research_response


@pytest.mark.asyncio
async def test_hypothesis_enhancer_initialization():
    """Test HypothesisEnhancer initialization."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    assert enhancer.research_orch == orch


@pytest.mark.asyncio
async def test_enhance_contract_hypotheses_no_research():
    """Test enhancing hypotheses when no research is available."""
    run_context = MockRunContext()
    research_client = MockResearchClient(research_response={"answer": "", "confidence": 0.0})
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    static_hyps = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.6,
            "contract_address": "0x123",
            "function_signature": "withdraw(uint256)",
        }
    ]

    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={"protocol_type": "defi_vault"},
        static_hypotheses=static_hyps,
    )

    # Should return hypotheses as-is when no research available
    assert len(enhanced) == 1
    assert enhanced[0]["confidence"] == 0.6


@pytest.mark.asyncio
async def test_enhance_contract_hypotheses_with_research():
    """Test enhancing hypotheses with research validation."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    static_hyps = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.6,
            "contract_address": "0x123",
            "function_signature": "withdraw(uint256)",
        },
        {
            "vuln_type": "access_control",
            "confidence": 0.5,
            "contract_address": "0x123",
            "function_signature": "setOwner(address)",
        },
    ]

    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={
            "protocol_type": "defi_vault",
            "functions": ["deposit", "withdraw"],
        },
        static_hypotheses=static_hyps,
    )

    # Reentrancy should be boosted (mentioned in research)
    assert len(enhanced) == 2
    reentrancy_hyp = next(h for h in enhanced if h["vuln_type"] == "reentrancy")
    assert reentrancy_hyp["confidence"] > 0.6
    assert reentrancy_hyp.get("research_validated") is True


@pytest.mark.asyncio
async def test_generate_targeted_llm_prompt():
    """Test generating a targeted LLM prompt."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    prompt = await enhancer.generate_targeted_llm_prompt(
        contract_metadata={
            "name": "TestVault",
            "address": "0x123",
            "chain_id": 1,
            "protocol_type": "defi_vault",
            "functions": ["deposit", "withdraw", "claim", "stake"],
        },
        research_context="Research shows that vaults are vulnerable to share inflation attacks",
    )

    assert "TestVault" in prompt
    assert "0x123" in prompt
    assert "defi_vault" in prompt
    assert "deposit" in prompt
    assert "Research" in prompt or "research" in prompt


@pytest.mark.asyncio
async def test_refine_from_failures_empty():
    """Test refining from failures with no failures."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    refined = await enhancer.refine_from_failures(
        failed_attempts=[],
        original_hypothesis={"vuln_type": "reentrancy", "confidence": 0.7},
    )

    assert len(refined) == 0


@pytest.mark.asyncio
async def test_refine_from_failures_revert():
    """Test refining from failures with revert errors."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    failed_attempts = [
        {"error": "Transaction reverted without a reason"},
    ]

    refined = await enhancer.refine_from_failures(
        failed_attempts=failed_attempts,
        original_hypothesis={
            "id": "hyp-123",
            "vuln_type": "reentrancy",
            "confidence": 0.7,
            "rationale": "Potential reentrancy in withdraw",
        },
    )

    assert len(refined) > 0
    # Check that at least one refinement contains "precondition" in its refinement field
    assert any("precondition" in r.get("refinement", "").lower() for r in refined)


@pytest.mark.asyncio
async def test_refine_from_failures_balance():
    """Test refining from failures with balance errors."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    failed_attempts = [
        {"error": "Insufficient balance for transfer"},
    ]

    refined = await enhancer.refine_from_failures(
        failed_attempts=failed_attempts,
        original_hypothesis={
            "id": "hyp-456",
            "vuln_type": "flash_loan",
            "confidence": 0.8,
        },
    )

    assert len(refined) > 0
    assert any("balance" in r.get("refinement", "") for r in refined)


@pytest.mark.asyncio
async def test_refine_from_failures_access():
    """Test refining from failures with access control errors."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    failed_attempts = [
        {"error": "Access denied: unauthorized caller"},
    ]

    refined = await enhancer.refine_from_failures(
        failed_attempts=failed_attempts,
        original_hypothesis={
            "id": "hyp-789",
            "vuln_type": "access_control",
            "confidence": 0.6,
        },
    )

    assert len(refined) > 0
    access_refined = next((r for r in refined if "access" in r.get("refinement", "")), None)
    assert access_refined is not None
    # Confidence should be significantly lowered
    assert access_refined["confidence"] < 0.6
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

