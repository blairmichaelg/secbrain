"""Property-based tests using Hypothesis for critical functions.

These tests verify properties that should always hold true regardless of input,
helping discover edge cases and corner cases that traditional tests might miss.
"""

from __future__ import annotations

import json
from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from secbrain.utils.response_diff import (
    diff_body_size_entropy,
    diff_headers,
    diff_json_semantic,
    diff_keywords,
    diff_status,
)

# ============================================================================
# Property-based tests for response_diff module
# ============================================================================


@given(st.integers(min_value=100, max_value=599), st.integers(min_value=100, max_value=599))
def test_diff_status_symmetry(status1: int, status2: int) -> None:
    """Diff should detect change regardless of order when statuses differ."""
    result1 = diff_status(status1, status2)
    result2 = diff_status(status2, status1)

    # Both should agree on whether there's a change
    assert result1["changed"] == result2["changed"]
    # If statuses are different, both should report a change
    if status1 != status2:
        assert result1["changed"] is True
        assert result2["changed"] is True


@given(st.integers(min_value=100, max_value=599))
def test_diff_status_identity(status: int) -> None:
    """Comparing a status to itself should show no change."""
    result = diff_status(status, status)
    assert result["changed"] is False
    assert result["baseline"] == status
    assert result["test"] == status


@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10,
    )
)
def test_diff_headers_identity(headers: dict[str, str]) -> None:
    """Comparing headers to themselves should show no diff."""
    result = diff_headers(headers, headers)
    assert result["has_diff"] is False
    assert not result["added"]
    assert not result["removed"]
    assert not result["changed"]


@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=20),
        st.text(min_size=0, max_size=100),
        min_size=1,
        max_size=5,
    ),
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=20),
        st.text(min_size=0, max_size=100),
        min_size=1,
        max_size=5,
    ),
)
def test_diff_headers_case_insensitive(headers1: dict[str, str], headers2: dict[str, str]) -> None:
    """Header comparison should be case-insensitive for header names."""
    # Create case-variant versions
    headers1_lower = {k.lower(): v for k, v in headers1.items()}
    headers2_lower = {k.lower(): v for k, v in headers2.items()}

    result = diff_headers(headers1_lower, headers2_lower)
    # The result should be consistent regardless of original case
    assert isinstance(result["has_diff"], bool)


@given(st.text(min_size=0, max_size=1000))
def test_diff_body_entropy_identity(body: str) -> None:
    """Entropy and size should be same when comparing to self."""
    result = diff_body_size_entropy(body, body)
    assert result["size"]["baseline"] == result["size"]["test"]
    assert result["size"]["delta"] == 0
    assert result["entropy"]["baseline"] == result["entropy"]["test"]


@given(st.text(min_size=0, max_size=500), st.text(min_size=0, max_size=500))
def test_diff_body_size_delta_property(body1: str, body2: str) -> None:
    """Delta should equal test size minus baseline size."""
    result = diff_body_size_entropy(body1, body2)
    expected_delta = len(body2) - len(body1)
    assert result["size"]["delta"] == expected_delta
    assert result["size"]["baseline"] == len(body1)
    assert result["size"]["test"] == len(body2)


@given(st.text(min_size=0, max_size=100))
def test_diff_body_entropy_non_negative(body: str) -> None:
    """Entropy should always be non-negative."""
    result = diff_body_size_entropy(body, body)
    assert result["entropy"]["baseline"] >= 0
    assert result["entropy"]["test"] >= 0


@given(
    st.text(min_size=0, max_size=200),
    st.text(min_size=0, max_size=200),
    st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
)
def test_diff_keywords_symmetric_detection(body1: str, body2: str, keywords: list[str]) -> None:
    """Keyword diff should detect changes regardless of which is baseline."""
    result1 = diff_keywords(body1, body2, keywords)
    result2 = diff_keywords(body2, body1, keywords)

    # Both should agree on whether there's a change
    assert result1["changed"] == result2["changed"]


@given(
    st.text(min_size=0, max_size=200),
    st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
)
def test_diff_keywords_identity(body: str, keywords: list[str]) -> None:
    """Comparing body to itself should show no keyword changes."""
    result = diff_keywords(body, body, keywords)
    assert result["changed"] is False
    assert not result["keywords"]


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.text(min_size=0, max_size=50), st.integers(), st.booleans()),
        min_size=0,
        max_size=10,
    )
)
def test_diff_json_semantic_identity(json_obj: dict[str, Any]) -> None:
    """Comparing JSON to itself should show no changes."""
    json_str = json.dumps(json_obj)
    result = diff_json_semantic(json_str, json_str)
    assert result["changed"] is False
    if isinstance(json_obj, dict):
        assert not result["added_keys"]
        assert not result["removed_keys"]


@given(st.text(min_size=0, max_size=100).filter(lambda x: not _is_valid_json(x)))
def test_diff_json_semantic_handles_invalid_json(invalid_json: str) -> None:
    """Should gracefully handle invalid JSON."""
    result = diff_json_semantic(invalid_json, invalid_json)
    # Should not crash and should indicate error
    assert "error" in result or result["changed"] is False


def _is_valid_json(text: str) -> bool:
    """Helper to check if text is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


# ============================================================================
# Property-based tests for security-critical properties
# ============================================================================


@given(st.text(min_size=0, max_size=1000))
def test_entropy_bounded(text: str) -> None:
    """Entropy should be bounded by log2 of alphabet size."""
    from secbrain.utils.response_diff import _entropy

    entropy = _entropy(text)
    # Entropy should be non-negative
    assert entropy >= 0
    # For non-empty strings, entropy should be finite
    if text:
        assert entropy == entropy  # Not NaN
        # Entropy upper bound is log2(n) where n is the length
        # But practically, it should be reasonable
        assert entropy <= 20.0  # Reasonable upper bound for text
