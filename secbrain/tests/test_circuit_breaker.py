"""Tests for circuit breaker functionality."""

import asyncio
from datetime import timedelta

import pytest

from secbrain.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreaker:
    """Test circuit breaker behavior."""

    async def test_init_defaults(self):
        """Test circuit breaker initialization with defaults."""
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.timeout_duration == timedelta(seconds=60)
        assert cb.success_threshold == 2
        assert cb._state == CircuitState.CLOSED
        assert cb._failure_count == 0
        assert cb._success_count == 0

    async def test_init_custom_params(self):
        """Test circuit breaker initialization with custom parameters."""
        cb = CircuitBreaker(
            failure_threshold=3,
            timeout_duration=timedelta(seconds=30),
            success_threshold=1,
        )
        assert cb.failure_threshold == 3
        assert cb.timeout_duration == timedelta(seconds=30)
        assert cb.success_threshold == 1

    async def test_successful_call(self):
        """Test successful function call through circuit breaker."""
        cb = CircuitBreaker()

        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb._state == CircuitState.CLOSED
        assert cb._failure_count == 0

    async def test_failed_call(self):
        """Test failed function call through circuit breaker."""
        cb = CircuitBreaker(failure_threshold=2)

        async def failing_func():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            await cb.call(failing_func)
        assert cb._failure_count == 1
        assert cb._state == CircuitState.CLOSED

        # Second failure should open circuit
        with pytest.raises(ValueError):
            await cb.call(failing_func)
        assert cb._failure_count == 2
        assert cb._state == CircuitState.OPEN

    async def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold is reached."""
        cb = CircuitBreaker(failure_threshold=3)

        async def failing_func():
            raise RuntimeError("Simulated failure")

        # Fail 3 times to reach threshold
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(failing_func)

        assert cb._state == CircuitState.OPEN

    async def test_circuit_rejects_when_open(self):
        """Test that circuit breaker rejects calls when open."""
        cb = CircuitBreaker(failure_threshold=1, timeout_duration=timedelta(seconds=10))

        async def failing_func():
            raise RuntimeError("Failure")

        # Open the circuit
        with pytest.raises(RuntimeError):
            await cb.call(failing_func)

        assert cb._state == CircuitState.OPEN

        # Should reject next call
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await cb.call(failing_func)
        assert "Circuit breaker open" in str(exc_info.value)

    async def test_half_open_state_transition(self):
        """Test transition to half-open state after timeout."""
        cb = CircuitBreaker(
            failure_threshold=1,
            timeout_duration=timedelta(milliseconds=100),
            success_threshold=2,
        )

        async def failing_func():
            raise RuntimeError("Failure")

        async def success_func():
            return "success"

        # Open the circuit
        with pytest.raises(RuntimeError):
            await cb.call(failing_func)
        assert cb._state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Should transition to half-open and allow test
        result = await cb.call(success_func)
        assert result == "success"
        assert cb._state == CircuitState.HALF_OPEN
        assert cb._success_count == 1

    async def test_half_open_to_closed_transition(self):
        """Test transition from half-open to closed after success threshold."""
        cb = CircuitBreaker(
            failure_threshold=1,
            timeout_duration=timedelta(milliseconds=100),
            success_threshold=2,
        )

        async def failing_func():
            raise RuntimeError("Failure")

        async def success_func():
            return "success"

        # Open the circuit
        with pytest.raises(RuntimeError):
            await cb.call(failing_func)
        assert cb._state == CircuitState.OPEN

        # Wait and transition to half-open
        await asyncio.sleep(0.15)
        await cb.call(success_func)
        assert cb._state == CircuitState.HALF_OPEN

        # Second success should close circuit
        await cb.call(success_func)
        assert cb._state == CircuitState.CLOSED
        assert cb._success_count == 0

    async def test_success_resets_failure_count(self):
        """Test that successful calls reset the failure count."""
        cb = CircuitBreaker(failure_threshold=3)

        async def failing_func():
            raise RuntimeError("Failure")

        async def success_func():
            return "success"

        # Fail twice
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing_func)
        assert cb._failure_count == 2

        # Success should reset counter
        await cb.call(success_func)
        assert cb._failure_count == 0

    async def test_get_retry_after(self):
        """Test retry_after calculation."""
        cb = CircuitBreaker(
            failure_threshold=1, timeout_duration=timedelta(seconds=5)
        )

        async def failing_func():
            raise RuntimeError("Failure")

        # Open the circuit
        with pytest.raises(RuntimeError):
            await cb.call(failing_func)

        # Check retry after
        retry_after = cb._get_retry_after()
        assert 0 < retry_after <= 5

        # Wait a bit
        await asyncio.sleep(0.1)
        new_retry_after = cb._get_retry_after()
        assert new_retry_after < retry_after

    async def test_should_attempt_reset(self):
        """Test should_attempt_reset logic."""
        cb = CircuitBreaker(
            failure_threshold=1, timeout_duration=timedelta(milliseconds=100)
        )

        # No failures yet
        assert cb._should_attempt_reset()

        async def failing_func():
            raise RuntimeError("Failure")

        # Open the circuit
        with pytest.raises(RuntimeError):
            await cb.call(failing_func)

        # Should not attempt reset immediately
        assert not cb._should_attempt_reset()

        # Wait for timeout
        await asyncio.sleep(0.15)
        assert cb._should_attempt_reset()
