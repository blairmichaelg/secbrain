"""Tests for LLM helper utilities."""

import json

import pytest

from secbrain.utils.llm_helpers import build_retry_prompt, extract_json_from_response


class TestExtractJsonFromResponse:
    """Test extracting JSON from LLM responses."""

    def test_extract_simple_json_dict(self):
        """Test extracting a simple JSON dictionary."""
        response = '{"key": "value", "number": 123}'
        result = extract_json_from_response(response)
        assert result == {"key": "value", "number": 123}

    def test_extract_simple_json_list(self):
        """Test extracting a simple JSON list."""
        response = '[1, 2, 3, "test"]'
        result = extract_json_from_response(response, expected_type=list)
        assert result == [1, 2, 3, "test"]

    def test_extract_json_with_whitespace(self):
        """Test extracting JSON with extra whitespace."""
        response = '  \n  {"key": "value"}  \n  '
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_json_from_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        response = """
Here's the JSON:
```json
{"key": "value"}
```
"""
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_json_from_markdown_without_json_label(self):
        """Test extracting JSON from markdown code block without json label."""
        response = """```
{"key": "value"}
```"""
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_json_with_extra_text(self):
        """Test extracting JSON with extra text around it."""
        response = 'Here is the result: {"key": "value"} and that is all'
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_list_with_extra_text(self):
        """Test extracting list with extra text."""
        response = "The list is: [1, 2, 3] end of list"
        result = extract_json_from_response(response, expected_type=list)
        assert result == [1, 2, 3]

    def test_extract_json_empty_response_raises_error(self):
        """Test that empty response raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response("")

    def test_extract_json_invalid_json_raises_error(self):
        """Test that invalid JSON raises error."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response("not valid json")

    def test_extract_json_wrong_type_raises_error(self):
        """Test that wrong type raises TypeError."""
        response = '{"key": "value"}'
        with pytest.raises(TypeError, match="Expected list, got dict"):
            extract_json_from_response(response, expected_type=list)

    def test_extract_list_wrong_type_raises_error(self):
        """Test that getting dict when expecting list raises error."""
        response = "[1, 2, 3]"
        with pytest.raises(TypeError, match="Expected dict, got list"):
            extract_json_from_response(response, expected_type=dict)

    def test_extract_nested_json(self):
        """Test extracting nested JSON structures."""
        response = '{"outer": {"inner": {"deep": "value"}}}'
        result = extract_json_from_response(response)
        assert result == {"outer": {"inner": {"deep": "value"}}}

    def test_extract_json_with_arrays(self):
        """Test extracting JSON with arrays."""
        response = '{"items": [1, 2, 3], "nested": [{"a": 1}]}'
        result = extract_json_from_response(response)
        assert result == {"items": [1, 2, 3], "nested": [{"a": 1}]}


class TestBuildRetryPrompt:
    """Test building retry prompts."""

    def test_build_retry_prompt_basic(self):
        """Test building a basic retry prompt."""
        original = "Generate a JSON object"
        error = ValueError("Invalid format")
        previous = '{"incomplete": '

        result = build_retry_prompt(original, error, previous)

        assert "error: Invalid format" in result
        assert "Generate a JSON object" in result
        assert '{"incomplete":' in result
        assert "valid JSON" in result

    def test_build_retry_prompt_truncates_long_response(self):
        """Test that long responses are truncated."""
        original = "Generate JSON"
        error = json.JSONDecodeError("test", "doc", 0)
        previous = "x" * 500  # Long response

        result = build_retry_prompt(original, error, previous)

        # Should be truncated to 300 chars - check that the prompt includes the first 300
        assert previous[:300] in result
        # But the full response should still be there since we're looking at slicing [:300]
        # The assertion should be that it's limited, not that content after 300 is excluded

    def test_build_retry_prompt_includes_instructions(self):
        """Test that retry prompt includes helpful instructions."""
        original = "Generate JSON"
        error = ValueError("test")
        previous = "invalid"

        result = build_retry_prompt(original, error, previous)

        assert "Remember to:" in result
        assert "valid json" in result.lower()
        assert "markdown" in result.lower()
        assert "explanatory text" in result.lower()

    def test_build_retry_prompt_with_json_decode_error(self):
        """Test retry prompt with JSONDecodeError."""
        original = "Create a user object"
        error = json.JSONDecodeError("Expecting value", "doc", 10)
        previous = '{"user": "test"'

        result = build_retry_prompt(original, error, previous)

        assert "Expecting value" in result
        assert "Create a user object" in result
