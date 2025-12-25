"""Tests for custom exceptions."""

import pytest

from secbrain.core.exceptions import (
    CompilationError,
    InsufficientProfitError,
    RateLimitError,
    SecBrainError,
    ValidationError,
)


class TestSecBrainError:
    """Test base SecBrain exception."""

    def test_base_exception(self) -> None:
        """Test base exception can be raised and caught."""
        with pytest.raises(SecBrainError, match="test error"):
            raise SecBrainError("test error")

    def test_inheritance(self) -> None:
        """Test base exception inherits from Exception."""
        assert issubclass(SecBrainError, Exception)


class TestValidationError:
    """Test validation exception."""

    def test_validation_error(self) -> None:
        """Test validation error can be raised."""
        with pytest.raises(ValidationError, match="invalid input"):
            raise ValidationError("invalid input")

    def test_inheritance(self) -> None:
        """Test ValidationError inherits from SecBrainError."""
        assert issubclass(ValidationError, SecBrainError)

    def test_can_catch_as_secbrain_error(self) -> None:
        """Test ValidationError can be caught as SecBrainError."""
        with pytest.raises(SecBrainError):
            raise ValidationError("test")


class TestCompilationError:
    """Test compilation exception."""

    def test_basic_compilation_error(self) -> None:
        """Test basic compilation error."""
        with pytest.raises(CompilationError, match="compilation failed"):
            raise CompilationError("compilation failed")

    def test_compilation_error_with_contract(self) -> None:
        """Test compilation error with contract name."""
        err = CompilationError("failed", contract="MyContract")
        assert err.contract == "MyContract"
        assert str(err) == "failed"

    def test_compilation_error_with_outputs(self) -> None:
        """Test compilation error with stdout and stderr."""
        err = CompilationError(
            "build failed",
            contract="Token",
            stdout="Compiling...",
            stderr="Error: syntax error",
        )
        assert err.contract == "Token"
        assert err.stdout == "Compiling..."
        assert err.stderr == "Error: syntax error"

    def test_compilation_error_defaults(self) -> None:
        """Test compilation error has empty string defaults."""
        err = CompilationError("error")
        assert err.contract == ""
        assert err.stdout == ""
        assert err.stderr == ""

    def test_inheritance(self) -> None:
        """Test CompilationError inherits from SecBrainError."""
        assert issubclass(CompilationError, SecBrainError)


class TestRateLimitError:
    """Test rate limit exception."""

    def test_basic_rate_limit_error(self) -> None:
        """Test basic rate limit error."""
        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            raise RateLimitError("rate limit exceeded")

    def test_rate_limit_error_with_retry_after(self) -> None:
        """Test rate limit error with retry_after."""
        err = RateLimitError("too many requests", retry_after=60.5)
        assert err.retry_after == 60.5
        assert str(err) == "too many requests"

    def test_rate_limit_error_default(self) -> None:
        """Test rate limit error has default retry_after of 0."""
        err = RateLimitError("error")
        assert err.retry_after == 0.0

    def test_inheritance(self) -> None:
        """Test RateLimitError inherits from SecBrainError."""
        assert issubclass(RateLimitError, SecBrainError)


class TestInsufficientProfitError:
    """Test insufficient profit exception."""

    def test_basic_insufficient_profit_error(self) -> None:
        """Test basic insufficient profit error."""
        with pytest.raises(InsufficientProfitError, match="profit too low"):
            raise InsufficientProfitError("profit too low")

    def test_insufficient_profit_error_with_values(self) -> None:
        """Test insufficient profit error with actual and threshold."""
        err = InsufficientProfitError(
            "insufficient profit",
            actual_profit=100.0,
            threshold=500.0,
        )
        assert err.actual_profit == 100.0
        assert err.threshold == 500.0
        assert str(err) == "insufficient profit"

    def test_insufficient_profit_error_defaults(self) -> None:
        """Test insufficient profit error has default values of 0."""
        err = InsufficientProfitError("error")
        assert err.actual_profit == 0.0
        assert err.threshold == 0.0

    def test_inheritance(self) -> None:
        """Test InsufficientProfitError inherits from SecBrainError."""
        assert issubclass(InsufficientProfitError, SecBrainError)


class TestExceptionHierarchy:
    """Test the exception hierarchy."""

    def test_all_custom_exceptions_inherit_from_base(self) -> None:
        """Test all custom exceptions can be caught with base exception."""
        exceptions = [
            ValidationError("test"),
            CompilationError("test"),
            RateLimitError("test"),
            InsufficientProfitError("test"),
        ]

        for exc in exceptions:
            with pytest.raises(SecBrainError):
                raise exc

    def test_can_differentiate_exceptions(self) -> None:
        """Test different exception types can be caught separately."""
        # ValidationError
        with pytest.raises(ValidationError):
            raise ValidationError("test")

        # CompilationError
        with pytest.raises(CompilationError):
            raise CompilationError("test")

        # RateLimitError
        with pytest.raises(RateLimitError):
            raise RateLimitError("test")

        # InsufficientProfitError
        with pytest.raises(InsufficientProfitError):
            raise InsufficientProfitError("test")
