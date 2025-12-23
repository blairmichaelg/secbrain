"""Tests for error taxonomy and custom error classes."""

import pytest

from secbrain.core.errors import (
    ConfigurationError,
    ErrorCategory,
    ErrorSeverity,
    NetworkError,
    PermissionError,
    ResourceError,
    SecBrainError,
    TimeoutError,
    ToolExecutionError,
    ValidationError,
)


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_error_category_values(self) -> None:
        """Test that all error categories have expected values."""
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.TOOL_EXECUTION.value == "tool_execution"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.PERMISSION.value == "permission"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.PROTOCOL.value == "protocol"


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self) -> None:
        """Test that all severity levels have expected values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestSecBrainError:
    """Test base SecBrainError class."""

    def test_basic_initialization(self) -> None:
        """Test basic error initialization."""
        error = SecBrainError(
            message="Test error",
            category=ErrorCategory.CONFIGURATION,
        )
        assert error.message == "Test error"
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.MEDIUM  # default
        assert error.details == {}
        assert error.cause is None

    def test_full_initialization(self) -> None:
        """Test error initialization with all parameters."""
        cause = ValueError("Original error")
        details = {"key": "value", "number": 42}
        error = SecBrainError(
            message="Complex error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            details=details,
            cause=cause,
        )
        assert error.message == "Complex error"
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == details
        assert error.cause == cause

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        error = SecBrainError(
            message="Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details={"field": "test"},
        )
        result = error.to_dict()
        assert result["error_type"] == "SecBrainError"
        assert result["message"] == "Test error"
        assert result["category"] == "validation"
        assert result["severity"] == "low"
        assert result["details"] == {"field": "test"}
        assert result["cause"] is None

    def test_to_dict_with_cause(self) -> None:
        """Test to_dict includes cause information."""
        cause = ValueError("Original error")
        error = SecBrainError(
            message="Test error",
            category=ErrorCategory.CONFIGURATION,
            cause=cause,
        )
        result = error.to_dict()
        assert result["cause"] == "Original error"

    def test_exception_behavior(self) -> None:
        """Test that SecBrainError behaves as an exception."""
        with pytest.raises(SecBrainError) as exc_info:
            raise SecBrainError("Test", ErrorCategory.CONFIGURATION)
        assert str(exc_info.value) == "Test"


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_initialization(self) -> None:
        """Test ConfigurationError initialization."""
        error = ConfigurationError(message="Config missing")
        assert error.message == "Config missing"
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {}

    def test_with_details(self) -> None:
        """Test ConfigurationError with details."""
        details = {"config_file": "/path/to/config.yaml", "missing_keys": ["api_key"]}
        error = ConfigurationError(message="Invalid config", details=details)
        assert error.details == details

    def test_to_dict(self) -> None:
        """Test ConfigurationError dictionary conversion."""
        error = ConfigurationError(message="Config error", details={"key": "value"})
        result = error.to_dict()
        assert result["error_type"] == "ConfigurationError"
        assert result["category"] == "configuration"
        assert result["severity"] == "high"


class TestToolExecutionError:
    """Test ToolExecutionError class."""

    def test_initialization(self) -> None:
        """Test ToolExecutionError initialization."""
        error = ToolExecutionError(
            message="Tool failed",
            tool_name="pytest",
        )
        assert error.message == "Tool failed"
        assert error.category == ErrorCategory.TOOL_EXECUTION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["tool_name"] == "pytest"
        assert error.details["exit_code"] is None
        assert error.details["stdout"] is None
        assert error.details["stderr"] is None

    def test_with_full_details(self) -> None:
        """Test ToolExecutionError with all details."""
        error = ToolExecutionError(
            message="Command failed",
            tool_name="forge",
            exit_code=1,
            stdout="Some output",
            stderr="Error message",
            details={"command": "forge build"},
        )
        assert error.details["tool_name"] == "forge"
        assert error.details["exit_code"] == 1
        assert error.details["stdout"] == "Some output"
        assert error.details["stderr"] == "Error message"
        assert error.details["command"] == "forge build"

    def test_to_dict(self) -> None:
        """Test ToolExecutionError dictionary conversion."""
        error = ToolExecutionError(
            message="Tool error",
            tool_name="slither",
            exit_code=2,
        )
        result = error.to_dict()
        assert result["error_type"] == "ToolExecutionError"
        assert result["category"] == "tool_execution"
        assert result["details"]["tool_name"] == "slither"
        assert result["details"]["exit_code"] == 2


class TestValidationError:
    """Test ValidationError class."""

    def test_basic_initialization(self) -> None:
        """Test ValidationError basic initialization."""
        error = ValidationError(message="Invalid input")
        assert error.message == "Invalid input"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details == {}

    def test_with_field(self) -> None:
        """Test ValidationError with field."""
        error = ValidationError(message="Invalid value", field="address")
        assert error.details["field"] == "address"

    def test_with_value(self) -> None:
        """Test ValidationError with value."""
        error = ValidationError(message="Invalid value", value=42)
        assert error.details["value"] == "42"

    def test_with_field_and_value(self) -> None:
        """Test ValidationError with both field and value."""
        error = ValidationError(message="Invalid", field="amount", value="abc")
        assert error.details["field"] == "amount"
        assert error.details["value"] == "abc"

    def test_to_dict(self) -> None:
        """Test ValidationError dictionary conversion."""
        error = ValidationError(message="Validation failed", field="email", value="invalid")
        result = error.to_dict()
        assert result["error_type"] == "ValidationError"
        assert result["category"] == "validation"


class TestNetworkError:
    """Test NetworkError class."""

    def test_basic_initialization(self) -> None:
        """Test NetworkError basic initialization."""
        error = NetworkError(message="Connection failed")
        assert error.message == "Connection failed"
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details == {}

    def test_with_url(self) -> None:
        """Test NetworkError with URL."""
        error = NetworkError(message="Request failed", url="https://example.com")
        assert error.details["url"] == "https://example.com"

    def test_with_status_code(self) -> None:
        """Test NetworkError with status code."""
        error = NetworkError(message="HTTP error", status_code=404)
        assert error.details["status_code"] == 404

    def test_with_url_and_status(self) -> None:
        """Test NetworkError with URL and status code."""
        error = NetworkError(
            message="Request failed",
            url="https://api.example.com/v1",
            status_code=500,
        )
        assert error.details["url"] == "https://api.example.com/v1"
        assert error.details["status_code"] == 500

    def test_to_dict(self) -> None:
        """Test NetworkError dictionary conversion."""
        error = NetworkError(message="Network issue", url="https://test.com", status_code=503)
        result = error.to_dict()
        assert result["error_type"] == "NetworkError"
        assert result["category"] == "network"


class TestTimeoutError:
    """Test TimeoutError class."""

    def test_basic_initialization(self) -> None:
        """Test TimeoutError basic initialization."""
        error = TimeoutError(message="Operation timed out")
        assert error.message == "Operation timed out"
        assert error.category == ErrorCategory.TIMEOUT
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {}

    def test_with_timeout_seconds(self) -> None:
        """Test TimeoutError with timeout value."""
        error = TimeoutError(message="Timed out", timeout_seconds=30.5)
        assert error.details["timeout_seconds"] == 30.5

    def test_to_dict(self) -> None:
        """Test TimeoutError dictionary conversion."""
        error = TimeoutError(message="Timeout", timeout_seconds=60.0)
        result = error.to_dict()
        assert result["error_type"] == "TimeoutError"
        assert result["category"] == "timeout"
        assert result["severity"] == "high"


class TestPermissionError:
    """Test PermissionError class."""

    def test_basic_initialization(self) -> None:
        """Test PermissionError basic initialization."""
        error = PermissionError(message="Access denied")
        assert error.message == "Access denied"
        assert error.category == ErrorCategory.PERMISSION
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {}

    def test_with_resource(self) -> None:
        """Test PermissionError with resource."""
        error = PermissionError(message="Cannot access", resource="/etc/secret")
        assert error.details["resource"] == "/etc/secret"

    def test_to_dict(self) -> None:
        """Test PermissionError dictionary conversion."""
        error = PermissionError(message="Forbidden", resource="admin_panel")
        result = error.to_dict()
        assert result["error_type"] == "PermissionError"
        assert result["category"] == "permission"
        assert result["severity"] == "high"


class TestResourceError:
    """Test ResourceError class."""

    def test_basic_initialization(self) -> None:
        """Test ResourceError basic initialization."""
        error = ResourceError(message="Resource exhausted")
        assert error.message == "Resource exhausted"
        assert error.category == ErrorCategory.RESOURCE
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {}

    def test_with_resource_type(self) -> None:
        """Test ResourceError with resource type."""
        error = ResourceError(message="Out of memory", resource_type="memory")
        assert error.details["resource_type"] == "memory"

    def test_with_usage(self) -> None:
        """Test ResourceError with usage information."""
        error = ResourceError(message="Limit exceeded", usage="95%")
        assert error.details["usage"] == "95%"

    def test_with_full_details(self) -> None:
        """Test ResourceError with all details."""
        error = ResourceError(
            message="Resource limit",
            resource_type="disk_space",
            usage="99%",
        )
        assert error.details["resource_type"] == "disk_space"
        assert error.details["usage"] == "99%"

    def test_to_dict(self) -> None:
        """Test ResourceError dictionary conversion."""
        error = ResourceError(message="Resource error", resource_type="cpu", usage="100%")
        result = error.to_dict()
        assert result["error_type"] == "ResourceError"
        assert result["category"] == "resource"
        assert result["severity"] == "high"
