from pathlib import Path

import hypothesis.strategies as st
import pytest
from hypothesis import given

from secbrain.agents.exploit_agent import validate_function_signature
from secbrain.core.validation import (
    ValidationError,
    validate_environment,
    validate_program_file,
    validate_scope_file,
    validate_tools_on_path,
)


def test_scope_requires_targets(tmp_path: Path) -> None:
    scope_file = tmp_path / "scope.yaml"
    scope_file.write_text("domains: []\nurls: []\nips: []\ncontracts: []\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_scope_file(scope_file)


def test_program_requires_name(tmp_path: Path) -> None:
    program_file = tmp_path / "program.json"
    program_file.write_text("{}", encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_program_file(program_file)


def test_validate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_KEY", raising=False)
    with pytest.raises(ValidationError):
        validate_environment(["MISSING_KEY"])

    monkeypatch.setenv("PRESENT_KEY", "1")
    assert validate_environment(["PRESENT_KEY"]) == ["PRESENT_KEY"]


def test_validate_tools_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    # Use a tool that should exist on CI (python) and one that likely doesn't.
    validate_tools_on_path(["python"])

    with pytest.raises(ValidationError):
        validate_tools_on_path(["definitely-not-a-real-tool-name-xyz"])


# ---------------------------------------------------------------------------
# Property-based tests for function signature validation
# ---------------------------------------------------------------------------

valid_names = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122),
    min_size=1,
    max_size=50,
).filter(lambda s: s and (s[0].isalpha() or s[0] == "_"))

valid_types = st.sampled_from(
    [
        "address",
        "uint256",
        "uint8",
        "bytes",
        "bytes32",
        "bool",
        "string",
        "address[]",
        "uint256[]",
        "bytes[]",
    ]
)


@given(name=valid_names, types=st.lists(valid_types, max_size=10))
def test_validate_function_signature_accepts_valid(name: str, types: list[str]) -> None:
    """Property test: valid signatures should pass validation and normalize whitespace."""
    sig = f"{name}({','.join(types)})"
    result = validate_function_signature(sig)
    assert result == sig.replace(" ", "")


@given(sig=st.text())
def test_validate_function_signature_safe(sig: str) -> None:
    """Property test: validation should never allow injection patterns."""
    try:
        result = validate_function_signature(sig)
        assert ";" not in result
        assert "&&" not in result
        assert "|" not in result
        assert "$(" not in result
        assert "`" not in result
    except ValueError:
        # Invalid inputs are expected to raise
        pass
