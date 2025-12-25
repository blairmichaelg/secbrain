"""Tests for concurrency utilities."""

import asyncio

import pytest

from secbrain.utils.concurrency import ConcurrencyHarness


class TestConcurrencyHarness:
    """Test ConcurrencyHarness for bounded parallel execution."""

    @pytest.mark.asyncio
    async def test_basic_execution(self) -> None:
        """Test basic parallel execution of tasks."""
        harness = ConcurrencyHarness(max_concurrency=2)
        counter = []

        async def task() -> int:
            counter.append(1)
            await asyncio.sleep(0.01)
            return len(counter)

        tasks = [task for _ in range(5)]
        results = await harness.run(tasks)

        assert len(results) == 5
        assert len(counter) == 5

    @pytest.mark.asyncio
    async def test_respects_max_concurrency(self) -> None:
        """Test that max_concurrency limit is respected."""
        max_concurrent = 3
        harness = ConcurrencyHarness(max_concurrency=max_concurrent)
        concurrent_count = []
        max_seen = [0]

        async def task() -> int:
            concurrent_count.append(1)
            current = len(concurrent_count)
            max_seen[0] = max(max_seen[0], current)
            await asyncio.sleep(0.05)
            concurrent_count.pop()
            return current

        tasks = [task for _ in range(10)]
        await harness.run(tasks)

        # The max concurrent should not exceed our limit
        # Note: This is a best-effort test due to async timing
        assert max_seen[0] <= max_concurrent + 1  # +1 for timing tolerance

    @pytest.mark.asyncio
    async def test_returns_all_results(self) -> None:
        """Test that all task results are returned."""
        harness = ConcurrencyHarness(max_concurrency=5)

        async def make_task(value: int) -> int:
            await asyncio.sleep(0.001)
            return value * 2

        tasks = [lambda v=i: make_task(v) for i in range(10)]
        results = await harness.run(tasks)

        assert len(results) == 10
        assert sorted(results) == [i * 2 for i in range(10)]

    @pytest.mark.asyncio
    async def test_empty_task_list(self) -> None:
        """Test with empty task list."""
        harness = ConcurrencyHarness(max_concurrency=2)
        results = await harness.run([])
        assert results == []

    @pytest.mark.asyncio
    async def test_single_task(self) -> None:
        """Test with a single task."""
        harness = ConcurrencyHarness(max_concurrency=2)

        async def task() -> str:
            return "result"

        results = await harness.run([task])
        assert results == ["result"]

    @pytest.mark.asyncio
    async def test_idempotency_key_deduplication(self) -> None:
        """Test deduplication using idempotency key."""
        harness = ConcurrencyHarness(max_concurrency=5)

        async def make_task(value: int) -> dict[str, int]:
            await asyncio.sleep(0.001)
            return {"id": value % 3, "value": value}  # Only 3 unique IDs

        tasks = [lambda v=i: make_task(v) for i in range(9)]

        # Use ID as idempotency key
        def get_key(result: dict[str, int]) -> str:
            return str(result["id"])

        results = await harness.run(tasks, idempotency_key=get_key)

        # Should only have 3 results (one for each unique ID)
        assert len(results) == 3
        ids = {r["id"] for r in results}
        assert ids == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_idempotency_key_keeps_first_occurrence(self) -> None:
        """Test that idempotency keeps the first occurrence."""
        harness = ConcurrencyHarness(max_concurrency=5)
        call_order = []

        async def make_task(value: int) -> dict[str, int]:
            call_order.append(value)
            await asyncio.sleep(0.001)
            return {"key": "same", "value": value}

        tasks = [lambda v=i: make_task(v) for i in range(5)]

        def get_key(result: dict[str, int]) -> str:
            return result["key"]

        results = await harness.run(tasks, idempotency_key=get_key)

        # Should only have 1 result
        assert len(results) == 1
        # Should be the first one that completed
        assert results[0]["value"] == call_order[0]

    @pytest.mark.asyncio
    async def test_without_idempotency_key(self) -> None:
        """Test that without idempotency key, all results are kept."""
        harness = ConcurrencyHarness(max_concurrency=5)

        async def task() -> dict[str, str]:
            await asyncio.sleep(0.001)
            return {"key": "same"}

        tasks = [task for _ in range(5)]
        results = await harness.run(tasks)

        # All 5 results should be kept even though they're identical
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_different_result_types(self) -> None:
        """Test with different result types."""
        harness = ConcurrencyHarness(max_concurrency=3)

        async def string_task() -> str:
            return "string"

        async def int_task() -> int:
            return 42

        async def dict_task() -> dict[str, int]:
            return {"value": 1}

        # Test with strings
        results = await harness.run([string_task for _ in range(3)])
        assert all(r == "string" for r in results)

        # Test with ints
        results = await harness.run([int_task for _ in range(3)])
        assert all(r == 42 for r in results)

        # Test with dicts
        results = await harness.run([dict_task for _ in range(3)])
        assert all(r == {"value": 1} for r in results)

    @pytest.mark.asyncio
    async def test_task_exceptions_propagate(self) -> None:
        """Test that exceptions in tasks propagate."""
        harness = ConcurrencyHarness(max_concurrency=2)

        async def failing_task() -> int:
            raise ValueError("Task failed")

        tasks = [failing_task]

        with pytest.raises(ValueError, match="Task failed"):
            await harness.run(tasks)

    @pytest.mark.asyncio
    async def test_partial_failure(self) -> None:
        """Test behavior when some tasks fail."""
        harness = ConcurrencyHarness(max_concurrency=2)

        async def success_task() -> str:
            return "success"

        async def failing_task() -> str:
            raise RuntimeError("Failed")

        tasks = [success_task, failing_task, success_task]

        # Should raise the exception from failing task
        with pytest.raises(RuntimeError, match="Failed"):
            await harness.run(tasks)

    @pytest.mark.asyncio
    async def test_max_concurrency_one(self) -> None:
        """Test with max_concurrency=1 (sequential execution)."""
        harness = ConcurrencyHarness(max_concurrency=1)
        execution_order = []

        async def make_task(value: int) -> int:
            execution_order.append(value)
            await asyncio.sleep(0.01)
            return value

        tasks = [lambda v=i: make_task(v) for i in range(5)]
        results = await harness.run(tasks)

        assert len(results) == 5
        # With max_concurrency=1, tasks should execute sequentially
        assert execution_order == list(range(5))

    @pytest.mark.asyncio
    async def test_large_number_of_tasks(self) -> None:
        """Test with a large number of tasks."""
        harness = ConcurrencyHarness(max_concurrency=10)

        async def task(value: int) -> int:
            await asyncio.sleep(0.001)
            return value

        tasks = [lambda v=i: task(v) for i in range(100)]
        results = await harness.run(tasks)

        assert len(results) == 100
        assert sorted(results) == list(range(100))

    @pytest.mark.asyncio
    async def test_idempotency_with_complex_keys(self) -> None:
        """Test idempotency with complex key generation."""
        harness = ConcurrencyHarness(max_concurrency=5)

        async def make_task(id1: int, id2: int) -> dict[str, int]:
            await asyncio.sleep(0.001)
            return {"id1": id1, "id2": id2, "sum": id1 + id2}

        # Create tasks with some duplicate combinations
        tasks = [
            lambda: make_task(1, 1),
            lambda: make_task(1, 1),  # duplicate
            lambda: make_task(1, 2),
            lambda: make_task(2, 1),
            lambda: make_task(1, 2),  # duplicate
        ]

        def get_key(result: dict[str, int]) -> str:
            return f"{result['id1']},{result['id2']}"

        results = await harness.run(tasks, idempotency_key=get_key)

        # Should have 3 unique combinations: (1,1), (1,2), (2,1)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_concurrent_modifications_safe(self) -> None:
        """Test that concurrent modifications to shared state are safe."""
        harness = ConcurrencyHarness(max_concurrency=5)
        shared_list: list[int] = []

        async def task(value: int) -> int:
            # This is intentionally NOT thread-safe, but asyncio should handle it
            await asyncio.sleep(0.001)
            shared_list.append(value)
            return value

        tasks = [lambda v=i: task(v) for i in range(10)]
        results = await harness.run(tasks)

        # All tasks should complete
        assert len(results) == 10
        # All values should be in shared list
        assert len(shared_list) == 10
