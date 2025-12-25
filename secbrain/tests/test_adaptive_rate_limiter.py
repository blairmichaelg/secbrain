"""Tests for AdaptiveRateLimiter concurrency and thread-safety."""

from __future__ import annotations

import asyncio

import pytest

from secbrain.agents.exploit_agent import ExploitAgent


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_basic_functionality():
    """Test basic acquire/release functionality."""
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=2, max_limit=5)

    assert limiter.current_limit == 2
    assert limiter.success_count == 0
    assert limiter.error_count == 0

    # Test basic context manager usage
    async with limiter:
        pass

    assert limiter.success_count == 1


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_increases_on_success():
    """Test that the limiter increases capacity after repeated successes."""
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=2, max_limit=5)

    # Trigger 8 successes to increase limit
    for _ in range(8):
        async with limiter:
            pass

    assert limiter.success_count == 8
    assert limiter.current_limit == 3  # Should have increased from 2 to 3


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_decreases_on_error():
    """Test that the limiter decreases capacity after repeated errors."""
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=3, max_limit=5)

    # Trigger 3 errors to decrease limit
    for _ in range(3):
        try:
            async with limiter:
                raise ValueError("Simulated error")
        except ValueError:
            pass

    assert limiter.error_count == 3
    assert limiter.current_limit == 2  # Should have decreased from 3 to 2


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_respects_max_limit():
    """Test that the limiter doesn't exceed max_limit."""
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=2, max_limit=3)

    # Trigger many successes (way more than needed to hit max)
    for _ in range(32):  # 4 increments * 8 successes each
        async with limiter:
            pass

    # Should cap at max_limit
    assert limiter.current_limit == 3
    assert limiter.current_limit <= limiter.max_limit


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_respects_min_limit():
    """Test that the limiter doesn't go below 1."""
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=2, max_limit=5)

    # Trigger many errors (way more than needed to hit minimum)
    for _ in range(9):  # 3 errors * 3 decrements
        try:
            async with limiter:
                raise ValueError("Simulated error")
        except ValueError:
            pass

    # Should not go below 1
    assert limiter.current_limit >= 1


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_concurrency_limit():
    """Test that the limiter properly limits concurrent operations."""
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=2, max_limit=5)

    max_concurrent = 0
    current_concurrent = 0
    lock = asyncio.Lock()

    async def task():
        nonlocal max_concurrent, current_concurrent

        async with limiter:
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)

            # Simulate some work
            await asyncio.sleep(0.01)

            async with lock:
                current_concurrent -= 1

    # Run 10 tasks concurrently
    await asyncio.gather(*[task() for _ in range(10)])

    # Max concurrent should not exceed initial_limit
    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_no_race_condition_on_resize():
    """
    Test that semaphore resizing doesn't cause race conditions.

    This is a regression test for the critical bug where swapping out
    the semaphore was unsynchronized, potentially allowing concurrency
    limits to be exceeded.
    """
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=2, max_limit=8)

    max_concurrent = 0
    current_concurrent = 0
    lock = asyncio.Lock()
    errors_triggered = 0

    async def task(should_error: bool):
        nonlocal max_concurrent, current_concurrent, errors_triggered

        async with limiter:
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)

            # Simulate work
            await asyncio.sleep(0.001)

            async with lock:
                current_concurrent -= 1

            # Trigger error to cause resize
            if should_error:
                errors_triggered += 1
                raise ValueError("Intentional error for resize test")

    # Create a mix of successful and failing tasks
    tasks = []
    for i in range(100):
        # Every 8th task succeeds (triggers upsize)
        # Every 3rd failing task decreases (triggers downsize)
        should_error = (i % 3 == 0)
        tasks.append(task(should_error))

    # Run all tasks, catching errors
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count errors
    error_count = sum(1 for r in results if isinstance(r, ValueError))
    assert error_count == errors_triggered

    # Critical assertion: max concurrent should NEVER exceed max_limit
    # even during resize operations
    assert max_concurrent <= limiter.max_limit

    # Also verify it never exceeded the limits during resize
    # This catches the race condition where old semaphore releases
    # would not be reflected in the new semaphore
    assert max_concurrent <= 8  # max_limit


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_hammer_test():
    """
    Hammer test: stress test with many concurrent operations.

    This test runs many tasks concurrently and frequently triggers
    resize operations to ensure the lock-based synchronization
    prevents any race conditions.
    """
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=3, max_limit=10)

    max_concurrent = 0
    current_concurrent = 0
    lock = asyncio.Lock()
    completed = 0

    async def hammer_task(task_id: int):
        nonlocal max_concurrent, current_concurrent, completed

        # Alternate between success and error to trigger many resizes
        should_error = (task_id % 5 == 0)

        async with limiter:
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)

                # Verify we're not exceeding the limit
                assert current_concurrent <= limiter.max_limit, (
                    f"Concurrency violation: {current_concurrent} > {limiter.max_limit}"
                )

            # Very short sleep to maximize contention
            await asyncio.sleep(0.0001)

            async with lock:
                current_concurrent -= 1
                completed += 1

            if should_error:
                raise ValueError("Intentional error")

    # Run 500 tasks with high concurrency
    tasks = [hammer_task(i) for i in range(500)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify all tasks completed
    assert completed == 500

    # Critical: no concurrency violations
    assert max_concurrent <= limiter.max_limit

    # Count errors
    error_count = sum(1 for r in results if isinstance(r, ValueError))
    assert error_count == 100  # Every 5th task errors


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_resize_during_acquire():
    """
    Test that resize operations don't interfere with pending acquires.

    This specifically tests the scenario where:
    1. Task A acquires the semaphore
    2. Task B is waiting to acquire
    3. Task A triggers a resize on exit
    4. Task B should still successfully acquire
    """
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=1, max_limit=5)

    # First, build up success count to be near resize threshold
    # Run 7 operations so that task A's operation will be the 8th, triggering resize
    # This needs to happen before tasks A and B start to avoid deadlock
    for _ in range(7):
        async with limiter:
            pass

    task_a_acquired = asyncio.Event()
    task_b_waiting = asyncio.Event()
    task_a_can_exit = asyncio.Event()
    results = []

    async def task_a():
        # This will be the 8th success, triggering resize on exit
        async with limiter:
            results.append("A acquired")
            task_a_acquired.set()

            # Wait for task B to start waiting
            await task_b_waiting.wait()

            # Now we can exit (and trigger resize)
            await task_a_can_exit.wait()

        results.append("A released")

    async def task_b():
        # Wait for task A to acquire first
        await task_a_acquired.wait()

        # Signal that we're about to wait
        task_b_waiting.set()

        # This acquire should succeed even if task A triggers resize
        async with limiter:
            results.append("B acquired")

        results.append("B released")

    # Start both tasks
    task_a_future = asyncio.create_task(task_a())
    task_b_future = asyncio.create_task(task_b())

    # Wait a bit for setup
    await asyncio.sleep(0.01)

    # Now let task A exit (which will trigger resize in __aexit__ since it's the 8th success)
    task_a_can_exit.set()

    # Wait for both to complete
    await asyncio.gather(task_a_future, task_b_future)

    # Verify order
    assert results == ["A acquired", "A released", "B acquired", "B released"]


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_concurrent_resizes():
    """
    Test that multiple concurrent resize operations are safe.

    This tests the scenario where multiple tasks exit at the same time,
    each potentially triggering a resize operation.
    """
    limiter = ExploitAgent.AdaptiveRateLimiter(initial_limit=5, max_limit=10)

    initial_limit = limiter.current_limit

    # Set up to trigger resize on 8th success
    # Run exactly 8 tasks simultaneously
    async def task():
        async with limiter:
            await asyncio.sleep(0.001)

    # First batch to approach resize threshold
    await asyncio.gather(*[task() for _ in range(7)])

    # Limit should not have changed yet (need 8 for resize)
    assert limiter.current_limit == initial_limit

    # Now run multiple tasks that all complete at similar times
    # to try to trigger concurrent resizes
    await asyncio.gather(*[task() for _ in range(10)])

    # Multiple resizes should have happened (8th and 16th operations trigger resizes)
    assert limiter.current_limit > initial_limit

    # The limiter should still be in a valid state
    assert limiter.current_limit <= limiter.max_limit
    assert limiter.current_limit >= 1
