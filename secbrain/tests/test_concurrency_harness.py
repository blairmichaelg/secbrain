"""Tests for concurrency utilities."""

import asyncio

import pytest

from secbrain.utils.concurrency import ConcurrencyHarness


class TestConcurrencyHarness:
    """Test ConcurrencyHarness for bounded parallel execution."""

    @pytest.mark.asyncio
    async def test_init_default(self):
        """Test harness initialization with default concurrency."""
        harness = ConcurrencyHarness()
        # Default max_concurrency is 5
        assert harness._sem._value == 5

    @pytest.mark.asyncio
    async def test_init_custom_concurrency(self):
        """Test harness initialization with custom concurrency."""
        harness = ConcurrencyHarness(max_concurrency=10)
        assert harness._sem._value == 10

    @pytest.mark.asyncio
    async def test_run_empty_tasks(self):
        """Test running with no tasks."""
        harness = ConcurrencyHarness()
        results = await harness.run([])
        assert results == []

    @pytest.mark.asyncio
    async def test_run_single_task(self):
        """Test running a single task."""
        harness = ConcurrencyHarness()

        async def task():
            return 42

        results = await harness.run([task])
        assert results == [42]

    @pytest.mark.asyncio
    async def test_run_multiple_tasks(self):
        """Test running multiple tasks."""
        harness = ConcurrencyHarness()

        async def task(value):
            await asyncio.sleep(0.01)
            return value

        tasks = [lambda v=i: task(v) for i in range(5)]
        results = await harness.run(tasks)
        assert len(results) == 5
        assert sorted(results) == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_run_respects_max_concurrency(self):
        """Test that max_concurrency limit is respected."""
        max_concurrent = 2
        harness = ConcurrencyHarness(max_concurrency=max_concurrent)
        concurrent_count = 0
        max_observed = 0

        async def task():
            nonlocal concurrent_count, max_observed
            concurrent_count += 1
            max_observed = max(max_observed, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return "done"

        tasks = [task for _ in range(10)]
        await harness.run(tasks)

        # Should never exceed max_concurrency
        assert max_observed <= max_concurrent

    @pytest.mark.asyncio
    async def test_run_with_idempotency_key(self):
        """Test running with idempotency key to dedupe results."""
        harness = ConcurrencyHarness()

        async def task(value):
            return {"id": value, "data": f"result_{value}"}

        # Create tasks with duplicate IDs
        tasks = [
            lambda: task(1),
            lambda: task(2),
            lambda: task(1),  # Duplicate
            lambda: task(3),
            lambda: task(2),  # Duplicate
        ]

        results = await harness.run(
            tasks,
            idempotency_key=lambda r: str(r["id"]),
        )

        # Should only have unique IDs
        assert len(results) == 3
        result_ids = {r["id"] for r in results}
        assert result_ids == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_run_without_idempotency_key(self):
        """Test running without idempotency key (no deduplication)."""
        harness = ConcurrencyHarness()

        async def task(value):
            return value

        # Create tasks with duplicates
        tasks = [
            lambda: task(1),
            lambda: task(2),
            lambda: task(1),  # Duplicate
        ]

        results = await harness.run(tasks)

        # Should have all results including duplicates
        assert len(results) == 3
        assert sorted(results) == [1, 1, 2]

    @pytest.mark.asyncio
    async def test_run_handles_task_errors(self):
        """Test that task errors are propagated."""
        harness = ConcurrencyHarness()

        async def failing_task():
            raise ValueError("Task failed")

        async def success_task():
            return "success"

        tasks = [success_task, failing_task]

        with pytest.raises(ValueError, match="Task failed"):
            await harness.run(tasks)

    @pytest.mark.asyncio
    async def test_run_preserves_order(self):
        """Test that results preserve execution order."""
        harness = ConcurrencyHarness(max_concurrency=1)  # Sequential execution

        results_order = []

        async def task(value):
            results_order.append(value)
            return value

        tasks = [lambda v=i: task(v) for i in range(5)]
        await harness.run(tasks)

        # Results should be in order when run sequentially
        assert results_order == [0, 1, 2, 3, 4]
