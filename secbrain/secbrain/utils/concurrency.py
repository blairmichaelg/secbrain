"""Controlled concurrency harness for race testing and bounded execution.

This module provides utilities for managing concurrent task execution with:
- Semaphore-based concurrency limiting
- Idempotency checking and deduplication
- Structured result collection
- Type-safe async task management
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


class ConcurrencyHarness:
    """Run async callables with bounded parallelism and optional idempotency checks."""

    def __init__(self, max_concurrency: int = 5) -> None:
        self._sem = asyncio.Semaphore(max_concurrency)

    async def run(
        self,
        tasks: Iterable[Callable[[], Awaitable[T]]],
        *,
        idempotency_key: Callable[[T], str] | None = None,
    ) -> list[T]:
        """Execute tasks with bounded parallelism. Optionally dedupe by idempotency_key."""

        results: list[T] = []
        seen_keys: set[str] = set()

        async def _wrap(fn: Callable[[], Awaitable[T]]) -> None:
            async with self._sem:
                res = await fn()
                if idempotency_key:
                    key = idempotency_key(res)
                    if key in seen_keys:
                        return
                    seen_keys.add(key)
                results.append(res)

        await asyncio.gather(*[_wrap(fn) for fn in tasks])
        return results
