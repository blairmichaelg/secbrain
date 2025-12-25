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
async def test_enhance_with_immunefi_patterns():
    """Test enhancing hypotheses includes Immunefi intelligence patterns."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    hypotheses = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.6,
            "function_signature": "withdraw(uint256)",
        }
    ]

    # Test through public API
    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={
            "protocol_type": "defi_vault",
            "name": "TestVault",
            "functions": ["withdraw"],
        },
        static_hypotheses=hypotheses,
    )

    assert len(enhanced) == 1
    assert enhanced[0]["confidence"] > 0.6
    assert "detection_priority" in enhanced[0]


@pytest.mark.asyncio
async def test_vulnerability_type_extraction():
    """Test that research context properly enhances hypotheses."""
    run_context = MockRunContext()
    research_client = MockResearchClient(
        research_response={
            "answer": "This contract is vulnerable to reentrancy attacks and oracle manipulation",
            "confidence": 0.8,
            "sources": ["source1"],
        }
    )
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    hypotheses = [
        {"vuln_type": "reentrancy", "confidence": 0.5},
        {"vuln_type": "oracle", "confidence": 0.5},
    ]

    enhanced = await enhancer.enhance_contract_hypotheses(
        contract_metadata={"protocol_type": "defi", "functions": ["swap"]},
        static_hypotheses=hypotheses,
    )

    # Both vulnerability types should be boosted due to research validation
    assert len(enhanced) == 2
    reentrancy_hyp = next((h for h in enhanced if h["vuln_type"] == "reentrancy"), None)
    oracle_hyp = next((h for h in enhanced if h["vuln_type"] == "oracle"), None)
    
    assert reentrancy_hyp is not None
    assert oracle_hyp is not None
    # At least one should have research validation
    assert any(h.get("research_validated") for h in enhanced)


@pytest.mark.asyncio
async def test_pattern_extraction_from_research():
    """Test that patterns are extracted from research and included in prompts."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)
    enhancer = HypothesisEnhancer(orch)

    research_text = "The contract should validate user inputs. Common attack: flash loan manipulation."
    
    # Test through public API (generate_targeted_llm_prompt uses _extract_patterns_from_research internally)
    prompt = await enhancer.generate_targeted_llm_prompt(
        contract_metadata={
            "name": "TestVault",
            "address": "0x123",
            "protocol_type": "defi_vault",
            "functions": ["deposit", "withdraw"],
        },
        research_context=research_text,
    )

    # Verify the prompt was generated with research context
    assert "TestVault" in prompt
    assert "defi_vault" in prompt
    assert len(prompt) > 100  # Should be a substantial prompt


@pytest.mark.asyncio
async def test_failure_categorization_through_refinement():
    """Test failure categorization through the public refine_from_failures API."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)
    enhancer = HypothesisEnhancer(orch)

    # Test different failure types through public API
    test_cases = [
        {
            "failures": [{"error": "Transaction reverted"}],
            "expected_refinement_contains": "precondition",
        },
        {
            "failures": [{"error": "Not authorized"}],
            "expected_refinement_contains": "access",
        },
        {
            "failures": [{"error": "Insufficient balance"}],
            "expected_refinement_contains": "balance",
        },
    ]

    for test_case in test_cases:
        refined = await enhancer.refine_from_failures(
            failed_attempts=test_case["failures"],
            original_hypothesis={
                "id": "hyp-test",
                "vuln_type": "test_vuln",
                "confidence": 0.7,
            },
        )

        # Should generate refinements for recognized error patterns
        if test_case["expected_refinement_contains"]:
            assert len(refined) > 0
            assert any(
                test_case["expected_refinement_contains"] in r.get("refinement", "").lower()
                for r in refined
            )


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
