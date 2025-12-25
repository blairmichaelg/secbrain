"""Structured error taxonomy for SecBrain.

This module provides a comprehensive error handling system with:
- Categorized exceptions for different error types
- Severity levels for error prioritization
- Structured error details for debugging and logging
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCategory(Enum):
    """Categories of errors in SecBrain."""

    CONFIGURATION = "configuration"
    NETWORK = "network"
    TOOL_EXECUTION = "tool_execution"
    VALIDATION = "validation"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    PROTOCOL = "protocol"


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    LOW = "low"  # Non-critical, can continue
    MEDIUM = "medium"  # May affect results but not critical
    HIGH = "high"  # Critical, may stop execution
    CRITICAL = "critical"  # Must stop immediately


class SecBrainError(Exception):
    """Base error class for SecBrain."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.cause = cause

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"category={self.category.value}, "
            f"severity={self.severity.value})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
        }


class ConfigurationError(SecBrainError):
    """Error in configuration loading or validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            details=details,
        )


class ToolExecutionError(SecBrainError):
    """Error during tool execution."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        exit_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        all_details = {
            "tool_name": tool_name,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            **(details or {}),
        }
        super().__init__(
            message=message,
            category=ErrorCategory.TOOL_EXECUTION,
            severity=ErrorSeverity.MEDIUM,
            details=all_details,
        )


class ValidationError(SecBrainError):
    """Error in data validation."""

    def __init__(self, message: str, field: str | None = None, value: Any | None = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
        )


class NetworkError(SecBrainError):
    """Error in network operations."""

    def __init__(self, message: str, url: str | None = None, status_code: int | None = None):
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            details=details,
        )


class TimeoutError(SecBrainError):
    """Error due to timeout."""

    def __init__(self, message: str, timeout_seconds: float | None = None):
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds

        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.HIGH,
            details=details,
        )


class PermissionError(SecBrainError):
    """Error due to insufficient permissions."""

    def __init__(self, message: str, resource: str | None = None):
        details = {}
        if resource:
            details["resource"] = resource

        super().__init__(
            message=message,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            details=details,
        )


class ResourceError(SecBrainError):
    """Error due to resource constraints."""

    def __init__(self, message: str, resource_type: str | None = None, usage: str | None = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if usage:
            details["usage"] = usage

        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            details=details,
        )
