"""Tests for VulnHypothesisAgent schema changes."""

from __future__ import annotations

import pytest
from jsonschema import validate

from secbrain.agents.vuln_hypothesis_agent import VulnHypothesisAgent


def test_hypothesis_schema_optional_fields():
    """Test that contract_address and function_signature are optional in schema."""
    schema = VulnHypothesisAgent.HYPOTHESIS_SCHEMA

    # Test with minimal required fields only
    minimal_hypothesis = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.8,
        }
    ]

    # Should not raise ValidationError
    validate(instance=minimal_hypothesis, schema=schema)


def test_hypothesis_schema_with_all_fields():
    """Test that schema accepts hypotheses with all fields."""
    schema = VulnHypothesisAgent.HYPOTHESIS_SCHEMA

    full_hypothesis = [
        {
            "vuln_type": "reentrancy",
            "confidence": 0.8,
            "contract_address": "0x1234567890123456789012345678901234567890",
            "function_signature": "withdraw(uint256)",
            "rationale": "Potential reentrancy vulnerability",
            "attack_description": "Attacker can drain funds",
            "expected_profit_hint_eth": 10.5,
            "exploit_notes": ["Step 1", "Step 2"],
        }
    ]

    # Should not raise ValidationError
    validate(instance=full_hypothesis, schema=schema)


def test_hypothesis_schema_accepts_any_string_address():
    """Test that schema accepts any string for contract_address (no pattern restriction)."""
    schema = VulnHypothesisAgent.HYPOTHESIS_SCHEMA

    # Test with various address formats
    hypotheses = [
        {"vuln_type": "reentrancy", "confidence": 0.8, "contract_address": "0x123"},
        {"vuln_type": "reentrancy", "confidence": 0.8, "contract_address": "short"},
        {"vuln_type": "reentrancy", "confidence": 0.8, "contract_address": ""},
    ]

    # All should be valid since we removed pattern restriction
    for hyp in hypotheses:
        validate(instance=[hyp], schema=schema)


def test_hypothesis_schema_accepts_any_function_signature():
    """Test that schema accepts any string for function_signature (no pattern restriction)."""
    schema = VulnHypothesisAgent.HYPOTHESIS_SCHEMA

    # Test with various function signature formats
    hypotheses = [
        {"vuln_type": "reentrancy", "confidence": 0.8, "function_signature": "withdraw(uint256)"},
        {"vuln_type": "reentrancy", "confidence": 0.8, "function_signature": "invalid"},
        {"vuln_type": "reentrancy", "confidence": 0.8, "function_signature": ""},
    ]

    # All should be valid since we removed pattern restriction
    for hyp in hypotheses:
        validate(instance=[hyp], schema=schema)


def test_hypothesis_schema_rejects_invalid_confidence():
    """Test that schema rejects invalid confidence values."""
    schema = VulnHypothesisAgent.HYPOTHESIS_SCHEMA

    # Confidence must be between 0 and 1
    invalid_hypotheses = [
        {"vuln_type": "reentrancy", "confidence": 1.5},  # Too high
        {"vuln_type": "reentrancy", "confidence": -0.1},  # Too low
    ]

    for hyp in invalid_hypotheses:
        with pytest.raises(Exception):  # ValidationError
            validate(instance=[hyp], schema=schema)


def test_hypothesis_schema_rejects_missing_required_fields():
    """Test that schema rejects hypotheses missing required fields."""
    schema = VulnHypothesisAgent.HYPOTHESIS_SCHEMA

    # Missing vuln_type
    invalid_hypothesis1 = [{"confidence": 0.8}]

    with pytest.raises(Exception):  # ValidationError
        validate(instance=invalid_hypothesis1, schema=schema)

    # Missing confidence
    invalid_hypothesis2 = [{"vuln_type": "reentrancy"}]

    with pytest.raises(Exception):  # ValidationError
        validate(instance=invalid_hypothesis2, schema=schema)


def test_checksum_address_lenient():
    """Test that _checksum_address handles various inputs gracefully."""
    from secbrain.agents.vuln_hypothesis_agent import VulnHypothesisAgent

    # Create a minimal instance just to test the method
    class MinimalContext:
        worker_model = None
        advisor_model = None

        def is_killed(self):
            return False

        def get_cached_llm(self, key):
            return None

        def cache_llm(self, key, value):
            pass

    class MinimalModel:
        async def generate(self, prompt, system=None, **kwargs):
            class Response:
                content = "test"

            return Response()

    agent = VulnHypothesisAgent(
        run_context=MinimalContext(),
        worker_model=MinimalModel(),
    )

    # Test None - should return placeholder
    result = agent._checksum_address(None)
    assert result == "0x0000000000000000000000000000000000000000"

    # Test empty string - should return placeholder
    result = agent._checksum_address("")
    assert result == "0x0000000000000000000000000000000000000000"

    # Test short address - should pad
    result = agent._checksum_address("0x123")
    assert len(result) == 42
    assert result.startswith("0x")

    # Test address without 0x - should add it
    result = agent._checksum_address("1234567890123456789012345678901234567890")
    assert result.startswith("0x")

    # Test too long address - should truncate
    result = agent._checksum_address("0x" + "1" * 50)
    assert len(result) == 42

    # Test valid address - should return checksum
    valid_addr = "0x1234567890123456789012345678901234567890"
    result = agent._checksum_address(valid_addr)
    assert len(result) == 42
    assert result.startswith("0x")
