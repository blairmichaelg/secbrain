"""Tests for HypothesisEnhancer."""

from __future__ import annotations

import pytest

from secbrain.agents.hypothesis_enhancer import HypothesisEnhancer
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
    # Test backward compatibility
    assert enhancer.research == orch


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

    # Should return hypotheses with Immunefi intelligence enhancements even when no research available
    assert len(enhanced) == 1
    # Confidence is boosted by Immunefi intelligence (withdraw function gets priority 9, +20% boost)
    assert enhanced[0]["confidence"] == 0.72
    assert enhanced[0].get("detection_priority") == 9
    assert "confidence_boost_reasons" in enhanced[0]


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


@pytest.mark.asyncio
async def test_enhance_contract_hypotheses_threshold_network():
    """Test enhancing hypotheses for Threshold Network contracts."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    static_hyps = [
        {
            "vuln_type": "bridge_attack",
            "confidence": 0.5,
            "contract_address": "0x123",
        }
    ]

    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={
            "protocol_type": "threshold_network",
            "name": "tBTC Bridge",
            "functions": ["deposit", "withdraw", "relay"],
        },
        static_hypotheses=static_hyps,
    )

    # Threshold Network patterns should enhance hypotheses
    assert len(enhanced) == 1


@pytest.mark.asyncio
async def test_enhance_with_immunefi_intelligence():
    """Test Immunefi intelligence enhancement."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    hypotheses = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.6,
            "function_signature": "withdraw(uint256)",
        }
    ]

    enhanced = enhancer._enhance_with_immunefi_intelligence(
        protocol_type="defi_vault",
        contract_name="TestVault",
        functions=["withdraw"],
        hypotheses=hypotheses,
    )

    assert len(enhanced) == 1
    assert enhanced[0]["confidence"] > 0.6
    assert "detection_priority" in enhanced[0]


@pytest.mark.asyncio
async def test_extract_vulnerability_types():
    """Test extracting vulnerability types from research text."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    research_text = "This contract is vulnerable to reentrancy attacks and oracle manipulation"
    vuln_types = enhancer._extract_vulnerability_types(research_text)

    assert "reentrancy" in vuln_types
    assert "oracle" in vuln_types


@pytest.mark.asyncio
async def test_extract_patterns_from_research():
    """Test extracting patterns from research text."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    research_text = "The contract should validate user inputs. Common attack: flash loan manipulation."
    patterns = enhancer._extract_patterns_from_research(research_text)

    assert isinstance(patterns, list)
    assert len(patterns) > 0


@pytest.mark.asyncio
async def test_categorize_failure():
    """Test failure categorization."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    # Test revert categorization
    revert_failure = {"error": "Transaction reverted"}
    category = enhancer._categorize_failure(revert_failure)
    assert category == "revert"

    # Test access control categorization
    access_failure = {"error": "Not authorized"}
    category = enhancer._categorize_failure(access_failure)
    assert category == "access_control"

    # Test balance categorization
    balance_failure = {"error": "Insufficient balance"}
    category = enhancer._categorize_failure(balance_failure)
    assert category == "insufficient_balance"

    # Test timing constraint
    timing_failure = {"error": "Deadline exceeded"}
    category = enhancer._categorize_failure(timing_failure)
    assert category == "timing_constraint"

    # Test arithmetic
    overflow_failure = {"error": "Arithmetic overflow"}
    category = enhancer._categorize_failure(overflow_failure)
    assert category == "arithmetic"


@pytest.mark.asyncio
async def test_refine_from_failures_multiple_types():
    """Test refining from failures with multiple error types."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    failed_attempts = [
        {"error": "Transaction reverted"},
        {"error": "Insufficient balance"},
    ]

    refined = await enhancer.refine_from_failures(
        failed_attempts=failed_attempts,
        original_hypothesis={
            "id": "hyp-multi",
            "vuln_type": "flash_loan",
            "confidence": 0.7,
        },
    )

    # Should generate refinements for both error types
    assert len(refined) > 0


@pytest.mark.asyncio
async def test_refine_from_failures_missing_keys():
    """Test refining from failures with missing required keys."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    failed_attempts = [{"error": "Transaction reverted"}]

    # Missing 'id' key
    refined = await enhancer.refine_from_failures(
        failed_attempts=failed_attempts,
        original_hypothesis={"vuln_type": "reentrancy"},
    )

    assert len(refined) == 0


@pytest.mark.asyncio
async def test_enhance_contract_hypotheses_with_high_confidence():
    """Test that high-confidence hypotheses get exploitation guidance."""
    run_context = MockRunContext()
    research_client = MockResearchClient(
        research_response={
            "answer": "Reentrancy can be exploited by calling back before state updates",
            "confidence": 0.9,
            "sources": ["research1", "research2", "research3"],
        }
    )
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    static_hyps = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.75,  # Above HIGH_CONFIDENCE_THRESHOLD (0.7)
            "contract_address": "0x123",
        }
    ]

    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={"protocol_type": "defi_vault", "functions": ["withdraw"]},
        static_hypotheses=static_hyps,
    )

    assert len(enhanced) == 1
    # High-confidence hypotheses should get exploitation guidance
    assert "exploitation_guidance" in enhanced[0] or enhanced[0]["confidence"] > 0.75


@pytest.mark.asyncio
async def test_enhance_contract_hypotheses_generic_protocol():
    """Test enhancing hypotheses for generic protocol type."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    static_hyps = [
        {
            "vuln_type": "access_control",
            "confidence": 0.5,
        }
    ]

    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={
            "name": "GenericContract",
            "functions": ["transfer", "approve"],
        },
        static_hypotheses=static_hyps,
    )

    # Should still enhance even for generic protocol
    assert len(enhanced) == 1
    assert "detection_priority" in enhanced[0]
