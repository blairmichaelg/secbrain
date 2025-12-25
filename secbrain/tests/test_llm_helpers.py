"""Tests for LLM helper utilities."""

import json

import pytest

from secbrain.utils.llm_helpers import build_retry_prompt, extract_json_from_response


class TestExtractJsonFromResponse:
    """Test JSON extraction from LLM responses."""

    def test_extract_simple_dict(self) -> None:
        """Test extracting a simple JSON dict."""
        response = '{"key": "value", "number": 42}'
        result = extract_json_from_response(response)
        assert result == {"key": "value", "number": 42}

    def test_extract_simple_list(self) -> None:
        """Test extracting a simple JSON list."""
        response = '[1, 2, 3, "test"]'
        result = extract_json_from_response(response, expected_type=list)
        assert result == [1, 2, 3, "test"]

    def test_extract_from_markdown_code_block(self) -> None:
        """Test extracting JSON from markdown code block."""
        response = """```json
{"name": "test", "value": 123}
```"""
        result = extract_json_from_response(response)
        assert result == {"name": "test", "value": 123}

    def test_extract_from_markdown_without_json_prefix(self) -> None:
        """Test extracting JSON from markdown code block without json prefix."""
        response = """```
{"name": "test", "value": 123}
```"""
        result = extract_json_from_response(response)
        assert result == {"name": "test", "value": 123}

    def test_extract_with_extra_whitespace(self) -> None:
        """Test extracting JSON with extra whitespace."""
        response = """

        {"key": "value"}

        """
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_with_prefix_text(self) -> None:
        """Test extracting JSON with prefix text."""
        response = 'Here is the result: {"status": "success"}'
        result = extract_json_from_response(response)
        assert result == {"status": "success"}

    def test_extract_with_suffix_text(self) -> None:
        """Test extracting JSON with suffix text."""
        response = '{"status": "success"} - this is the response'
        result = extract_json_from_response(response)
        assert result == {"status": "success"}

    def test_extract_list_with_surrounding_text(self) -> None:
        """Test extracting list with surrounding text."""
        response = 'The items are: [1, 2, 3] in order'
        result = extract_json_from_response(response, expected_type=list)
        assert result == [1, 2, 3]

    def test_extract_nested_dict(self) -> None:
        """Test extracting nested JSON dict."""
        response = '{"outer": {"inner": {"value": 42}}}'
        result = extract_json_from_response(response)
        assert result == {"outer": {"inner": {"value": 42}}}

    def test_extract_complex_structure(self) -> None:
        """Test extracting complex JSON structure."""
        response = """```json
{
    "items": [
        {"id": 1, "name": "first"},
        {"id": 2, "name": "second"}
    ],
    "count": 2,
    "metadata": {
        "version": "1.0"
    }
}
```"""
        result = extract_json_from_response(response)
        assert result["items"] == [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
        ]
        assert result["count"] == 2
        assert result["metadata"]["version"] == "1.0"

    def test_empty_response_raises_error(self) -> None:
        """Test empty response raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError, match="empty response"):
            extract_json_from_response("")

    def test_invalid_json_raises_error(self) -> None:
        """Test invalid JSON raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response("{invalid json}")

    def test_type_mismatch_raises_error(self) -> None:
        """Test type mismatch raises TypeError."""
        with pytest.raises(TypeError, match="Expected list, got dict"):
            extract_json_from_response('{"key": "value"}', expected_type=list)

    def test_dict_expected_got_list_raises_error(self) -> None:
        """Test expecting dict but getting list raises TypeError."""
        with pytest.raises(TypeError, match="Expected dict, got list"):
            extract_json_from_response('[1, 2, 3]', expected_type=dict)

    def test_no_json_boundaries_found(self) -> None:
        """Test when no JSON boundaries are found."""
        # This should fail to parse
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response("just plain text with no json")

    def test_multiple_markdown_blocks(self) -> None:
        """Test with multiple markdown blocks - takes the first."""
        response = """```
{"first": 1}
```
Some text
```
{"second": 2}
```"""
        result = extract_json_from_response(response)
        assert result == {"first": 1}

    def test_extract_with_unicode(self) -> None:
        """Test extracting JSON with unicode characters."""
        response = '{"message": "Hello 世界", "emoji": "🔒"}'
        result = extract_json_from_response(response)
        assert result["message"] == "Hello 世界"
        assert result["emoji"] == "🔒"

    def test_extract_with_escaped_characters(self) -> None:
        """Test extracting JSON with escaped characters."""
        response = r'{"path": "C:\\Users\\test", "quote": "He said \"hello\""}'
        result = extract_json_from_response(response)
        assert result["path"] == "C:\\Users\\test"
        assert result["quote"] == 'He said "hello"'

    def test_extract_list_of_dicts(self) -> None:
        """Test extracting a list of dictionaries."""
        response = '[{"id": 1}, {"id": 2}, {"id": 3}]'
        result = extract_json_from_response(response, expected_type=list)
        assert len(result) == 3
        assert result[0]["id"] == 1

    def test_extract_with_numbers(self) -> None:
        """Test extracting JSON with various number types."""
        response = '{"int": 42, "float": 3.14, "negative": -10, "scientific": 1.23e-4}'
        result = extract_json_from_response(response)
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["negative"] == -10
        assert abs(result["scientific"] - 0.000123) < 1e-10

    def test_extract_with_booleans_and_null(self) -> None:
        """Test extracting JSON with boolean and null values."""
        response = '{"active": true, "deleted": false, "data": null}'
        result = extract_json_from_response(response)
        assert result["active"] is True
        assert result["deleted"] is False
        assert result["data"] is None


class TestBuildRetryPrompt:
    """Test retry prompt building."""

    def test_build_basic_retry_prompt(self) -> None:
        """Test building a basic retry prompt."""
        original = "Generate a JSON response"
        error = ValueError("Invalid JSON")
        previous = '{"incomplete": '

        result = build_retry_prompt(original, error, previous)

        assert "Invalid JSON" in result
        assert "Generate a JSON response" in result
        assert '{"incomplete": ' in result

    def test_truncates_long_response(self) -> None:
        """Test that long previous responses are truncated."""
        original = "Test prompt"
        error = Exception("Error")
        previous = "x" * 500  # 500 character response

        result = build_retry_prompt(original, error, previous)

        # Should only include first 300 chars
        assert "x" * 300 in result
        assert "x" * 301 not in result

    def test_includes_all_components(self) -> None:
        """Test that retry prompt includes all expected components."""
        original = "Original instructions"
        error = json.JSONDecodeError("msg", "doc", 0)
        previous = "Bad response"

        result = build_retry_prompt(original, error, previous)

        # Check for key components
        assert "previous response had an error" in result.lower()
        assert "Original instructions" in result
        assert "valid JSON" in result
        assert "markdown" in result.lower()

    def test_with_different_error_types(self) -> None:
        """Test with different exception types."""
        original = "Test"
        previous = "response"

        errors = [
            ValueError("test error"),
            TypeError("wrong type"),
            RuntimeError("runtime issue"),
        ]

        for error in errors:
            result = build_retry_prompt(original, error, previous)
            assert str(error) in result

    def test_short_previous_response(self) -> None:
        """Test with short previous response (less than 300 chars)."""
        original = "Test prompt"
        error = Exception("Error")
        previous = "Short response"

        result = build_retry_prompt(original, error, previous)

        # Should include full previous response
        assert "Short response" in result

    def test_empty_previous_response(self) -> None:
        """Test with empty previous response."""
        original = "Test prompt"
        error = Exception("Error")
        previous = ""

        result = build_retry_prompt(original, error, previous)

        # Should still work, just empty previous response section
        assert "Test prompt" in result
        assert "Error" in result

    def test_multiline_original_prompt(self) -> None:
        """Test with multiline original prompt."""
        original = """Line 1
Line 2
Line 3"""
        error = Exception("Error")
        previous = "response"

        result = build_retry_prompt(original, error, previous)

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_special_characters_in_error_message(self) -> None:
        """Test with special characters in error message."""
        original = "Test"
        error = Exception("Error: {key} at line [5]")
        previous = "response"

        result = build_retry_prompt(original, error, previous)

        assert "Error: {key} at line [5]" in result

    def test_unicode_in_responses(self) -> None:
        """Test with unicode characters."""
        original = "Generate response for 世界"
        error = Exception("Error with emoji 🔒")
        previous = "Response: 你好"

        result = build_retry_prompt(original, error, previous)

        assert "世界" in result
        assert "🔒" in result
        assert "你好" in result
