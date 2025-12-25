"""Circuit breaker for external service calls.

This module implements the circuit breaker pattern to prevent cascading failures:
- Automatic failure detection and fast-fail behavior
- State management (CLOSED, OPEN, HALF_OPEN)
- Configurable thresholds and timeouts
- Service health monitoring and recovery
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls.

    Prevents cascading failures by failing fast when service is down.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_duration: timedelta = timedelta(seconds=60),
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.success_threshold = success_threshold

        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result from the function call
            
        Raises:
            CircuitBreakerOpenError: If circuit is open and not ready to retry
            Exception: Any exception raised by the wrapped function
        """
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                else:
                    retry_after = self._get_retry_after()
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker open, retry after {retry_after:.1f} seconds",
                        retry_after=retry_after
                    )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return datetime.now(UTC) - self._last_failure_time > self.timeout_duration

    def _get_retry_after(self) -> float:
        """Get seconds until retry is allowed."""
        if self._last_failure_time is None:
            return 0.0
        elapsed = datetime.now(UTC) - self._last_failure_time
        remaining = self.timeout_duration - elapsed
        return max(0.0, remaining.total_seconds())

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(UTC)

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open.
    
    This exception indicates that the circuit breaker has detected too many
    failures and is temporarily blocking requests to prevent cascading failures.
    """
    
    def __init__(self, message: str, retry_after: float = 0.0):
        """Initialize the error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message)
        self.retry_after = retry_after

