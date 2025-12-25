"""Parallel execution utilities for workflow optimization."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog


@dataclass
class TaskResult:
    """Result from a parallel task execution."""

    task_id: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    error: str | None = None


class ParallelExecutor:
    """
    Execute independent tasks in parallel with proper error handling.

    Features:
    - Concurrent task execution with configurable limits
    - Individual task timeout support
    - Error isolation (one task failure doesn't stop others)
    - Result aggregation
    - Progress tracking
    """

    def __init__(
        self,
        max_concurrent: int = 3,
        logger: structlog.stdlib.BoundLogger | None = None,
    ):
        self.max_concurrent = max_concurrent
        self.logger = logger
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_tasks(
        self,
        tasks: dict[str, Callable[[], Coroutine[Any, Any, dict[str, Any]]]],
        timeout_seconds: float | None = None,
    ) -> dict[str, TaskResult]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: Dictionary mapping task_id to async callable
            timeout_seconds: Optional timeout per task

        Returns:
            Dictionary mapping task_id to TaskResult
        """
        if not tasks:
            return {}

        self._log("parallel_execution_started", task_count=len(tasks))

        # Create task coroutines
        task_coroutines = {
            task_id: self._execute_single_task(task_id, task_func, timeout_seconds)
            for task_id, task_func in tasks.items()
        }

        # Execute all tasks concurrently
        results = await asyncio.gather(
            *task_coroutines.values(),
            return_exceptions=True,
        )

        # Map results back to task IDs
        task_results = {}
        for task_id, result in zip(task_coroutines.keys(), results, strict=False):
            if isinstance(result, Exception):
                task_results[task_id] = TaskResult(
                    task_id=task_id,
                    success=False,
                    error=str(result),
                )
            elif isinstance(result, TaskResult):
                task_results[task_id] = result
            else:
                # Unexpected result type
                task_results[task_id] = TaskResult(
                    task_id=task_id,
                    success=False,
                    error=f"Unexpected result type: {type(result)}",
                )

        # Log summary
        successful = sum(1 for r in task_results.values() if r.success)
        failed = len(task_results) - successful
        self._log(
            "parallel_execution_completed",
            total=len(task_results),
            successful=successful,
            failed=failed,
        )

        return task_results

    async def _execute_single_task(
        self,
        task_id: str,
        task_func: Callable[[], Coroutine[Any, Any, dict[str, Any]]],
        timeout_seconds: float | None,
    ) -> TaskResult:
        """Execute a single task with semaphore and timeout."""
        start_time = datetime.now(UTC)

        async with self._semaphore:
            try:
                self._log("task_started", task_id=task_id)

                if timeout_seconds:
                    data = await asyncio.wait_for(
                        task_func(),
                        timeout=timeout_seconds,
                    )
                else:
                    data = await task_func()

                duration = (datetime.now(UTC) - start_time).total_seconds()
                self._log("task_completed", task_id=task_id, duration=duration)

                return TaskResult(
                    task_id=task_id,
                    success=True,
                    data=data,
                    duration_seconds=duration,
                )

            except TimeoutError:
                duration = (datetime.now(UTC) - start_time).total_seconds()
                self._log("task_timeout", task_id=task_id, timeout=timeout_seconds)
                return TaskResult(
                    task_id=task_id,
                    success=False,
                    duration_seconds=duration,
                    error=f"Timeout after {timeout_seconds}s",
                )

            except Exception as e:
                duration = (datetime.now(UTC) - start_time).total_seconds()
                self._log("task_failed", task_id=task_id, error=str(e))
                return TaskResult(
                    task_id=task_id,
                    success=False,
                    duration_seconds=duration,
                    error=str(e),
                )

    def _log(self, event: str, **kwargs: Any) -> None:
        """Log an event if logger is available."""
        if self.logger:
            self.logger.info(event, **kwargs)


async def execute_parallel_if_independent(
    tasks: dict[str, Callable[[], Coroutine[Any, Any, dict[str, Any]]]],
    max_concurrent: int = 3,
    timeout_seconds: float | None = None,
    logger: Any = None,
) -> dict[str, TaskResult]:
    """
    Convenience function to execute tasks in parallel.

    Args:
        tasks: Dictionary mapping task_id to async callable
        max_concurrent: Maximum number of concurrent tasks
        timeout_seconds: Optional timeout per task
        logger: Optional logger instance

    Returns:
        Dictionary mapping task_id to TaskResult
    """
    executor = ParallelExecutor(max_concurrent=max_concurrent, logger=logger)
    return await executor.execute_tasks(tasks, timeout_seconds)
