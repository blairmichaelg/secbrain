"""Utilities for LLM interaction."""

import json
from typing import Any, TypeVar

T = TypeVar("T")


def extract_json_from_response(
    response: str,
    *,
    expected_type: type[T] = dict,
) -> T:
    """Extract and parse JSON from LLM response.

    Handles common patterns:
    - Markdown code blocks
    - "json" prefix
    - Extra whitespace

    Args:
        response: Raw LLM response string
        expected_type: Expected Python type (dict or list)

    Returns:
        Parsed JSON object

    Raises:
        json.JSONDecodeError: If parsing fails
        ValueError: If type doesn't match expected_type
    """
    if not response:
        raise json.JSONDecodeError("empty response", response, 0)

    text = response.strip()

    # Remove markdown code blocks
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            # Remove "json" prefix
            if text.startswith("json"):
                text = text[4:].strip()

    # Try to find JSON array/object boundaries
    if expected_type == list:
        start = text.find("[")
        end = text.rfind("]")
    else:  # dict
        start = text.find("{")
        end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    # Parse and validate
    data: Any = json.loads(text)

    if not isinstance(data, expected_type):
        raise ValueError(f"Expected {expected_type.__name__}, got {type(data).__name__}")

    return data


def build_retry_prompt(
    original_prompt: str,
    error: Exception,
    previous_response: str,
) -> str:
    """Build a retry prompt after LLM failure.

    Args:
        original_prompt: The original prompt that failed
        error: The exception that occurred
        previous_response: The response that failed to parse

    Returns:
        New prompt for retry attempt
    """
    return f"""Your previous response had an error: {error}

Previous response (first 300 chars):
{previous_response[:300]}

Please provide a corrected response following the original instructions:

{original_prompt}

Remember to:
1. Return ONLY valid JSON
2. No markdown formatting
3. No explanatory text outside JSON
"""
