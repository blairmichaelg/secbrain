"""Centralized research orchestrator for strategic knowledge gathering."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from secbrain.core.context import RunContext

logger = logging.getLogger(__name__)


@dataclass
class ResearchQuery:
    """Structured research query with context."""

    question: str
    context: str
    priority: int = 5  # 1-10, higher = more important
    phase: str = ""
    tags: list[str] = field(default_factory=list)
    cache_key: str = field(init=False)

    # Priority validation constants
    MIN_PRIORITY = 1
    MAX_PRIORITY = 10

    def __post_init__(self) -> None:
        # Validate priority range
        if not self.MIN_PRIORITY <= self.priority <= self.MAX_PRIORITY:
            raise ValueError(
                f"priority must be between {self.MIN_PRIORITY} and {self.MAX_PRIORITY}, got {self.priority}"
            )
        raw = f"{self.question}|||{self.context}"
        self.cache_key = hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class ResearchResult:
    """Research result with metadata."""

    query: ResearchQuery
    answer: str
    sources: list[str]
    confidence: float = 0.5
    cached: bool = False

    def __post_init__(self) -> None:
        # Validate confidence range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


class ResearchOrchestrator:
    """
    Centralized research orchestration with:
    - Query deduplication
    - Priority-based scheduling
    - Result caching
    - Strategic timing
    """

    def __init__(self, run_context: RunContext, research_client: Any) -> None:
        self.run_context = run_context
        self.research_client = research_client
        self._cache: dict[str, ResearchResult] = {}
        self._pending_queries: list[ResearchQuery] = []
        self._semaphore = asyncio.Semaphore(3)  # Max concurrent research
        self._queue_lock = asyncio.Lock()  # Protect pending_queries list

    async def queue_research(self, query: ResearchQuery) -> None:
        """Queue a research query for later execution."""
        # Check cache first
        if query.cache_key in self._cache:
            return

        async with self._queue_lock:
            # Check if already queued
            if any(q.cache_key == query.cache_key for q in self._pending_queries):
                return

            self._pending_queries.append(query)

    async def execute_batch(self, max_queries: int = 5) -> list[ResearchResult]:
        """Execute top priority queries in batch."""
        async with self._queue_lock:
            if not self._pending_queries:
                return []

            # Sort by priority
            self._pending_queries.sort(key=lambda q: q.priority, reverse=True)

            # Take top N
            batch = self._pending_queries[:max_queries]
            self._pending_queries = self._pending_queries[max_queries:]

        # Execute in parallel
        tasks = [self._execute_single(q) for q in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, ResearchResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(
                    f"Research query failed: {batch[i].question[:100]}",
                    exc_info=result,
                )

        return valid_results

    async def _execute_single(self, query: ResearchQuery) -> ResearchResult:
        """Execute a single research query."""
        async with self._semaphore:
            # Check cache inside semaphore to prevent race conditions
            cached_result = self._cache.get(query.cache_key)
            if cached_result is not None:
                # Mark as cached and return
                cached_result.cached = True
                return cached_result

            result = await self.research_client.ask_research(
                question=query.question,
                context=query.context,
                run_context=self.run_context,
            )

            research_result = ResearchResult(
                query=query,
                answer=result.get("answer", ""),
                sources=result.get("sources", []),
                cached=False,
            )

            # Cache result
            self._cache[query.cache_key] = research_result

            return research_result

    async def research_vulnerability_pattern(
        self,
        vuln_type: str,
        contract_context: str = "",
        priority: int = 7,
    ) -> ResearchResult | None:
        """Research a specific vulnerability pattern.

        Note: This method executes immediately, bypassing the normal priority queue.
        If you need priority-based scheduling, use queue_research() and execute_batch().
        """
        # Calculate recent years dynamically
        current_year = datetime.now(UTC).year
        recent_years = f"{current_year - 1}-{current_year}"

        query = ResearchQuery(
            question=f"What are the key indicators and exploitation techniques for {vuln_type} vulnerabilities in smart contracts? Include recent ({recent_years}) attack patterns.",
            context=f"Analyzing potential {vuln_type} vulnerability. {contract_context}",
            priority=priority,
            phase="hypothesis",
            tags=[vuln_type, "pattern"],
        )

        await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)

        return results[0] if results else None

    async def research_protocol_type(
        self,
        protocol_type: str,
        functions: list[str],
        priority: int = 8,
    ) -> ResearchResult | None:
        """Research common vulnerabilities for a protocol type.

        Note: This method executes immediately, bypassing the normal priority queue.
        If you need priority-based scheduling, use queue_research() and execute_batch().
        """
        query = ResearchQuery(
            question=f"What are the top 5 vulnerability classes in {protocol_type} protocols? Focus on high-severity issues from recent audits.",
            context=f"Contract has functions: {', '.join(functions[:10])}",
            priority=priority,
            phase="hypothesis",
            tags=[protocol_type, "vulnerabilities"],
        )

        await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)

        return results[0] if results else None

    async def research_exploit_validation(
        self,
        vuln_type: str,
        revert_reason: str,
        priority: int = 6,
    ) -> ResearchResult | None:
        """Research whether a revert indicates a near-miss exploit.

        Note: This method executes immediately, bypassing the normal priority queue.
        If you need priority-based scheduling, use queue_research() and execute_batch().
        """
        query = ResearchQuery(
            question=f"For {vuln_type} exploits, what do reverts like '{revert_reason[:100]}' typically indicate? Is this a near-miss that could succeed with parameter adjustment?",
            context=f"Exploit attempt reverted with: {revert_reason}",
            priority=priority,
            phase="exploit",
            tags=[vuln_type, "validation"],
        )

        await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)

        return results[0] if results else None

    async def research_similar_exploits(
        self,
        vuln_type: str,
        target_protocol: str,
        priority: int = 8,
    ) -> ResearchResult | None:
        """Research historical exploits of similar type.

        Note: This method executes immediately, bypassing the normal priority queue.
        If you need priority-based scheduling, use queue_research() and execute_batch().
        """
        query = ResearchQuery(
            question=f"What are documented {vuln_type} exploits in {target_protocol} or similar protocols? Include root causes and profit mechanisms.",
            context="Looking for exploit patterns to validate hypothesis",
            priority=priority,
            phase="hypothesis",
            tags=[vuln_type, target_protocol, "historical"],
        )

        await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)

        return results[0] if results else None

    def get_cached_result(self, question: str, context: str) -> ResearchResult | None:
        """Get cached research result."""
        raw = f"{question}|||{context}"
        cache_key = hashlib.sha256(raw.encode()).hexdigest()
        return self._cache.get(cache_key)

    def get_research_summary(self) -> dict[str, Any]:
        """Get summary of research activity."""
        return {
            "total_queries": len(self._cache) + len(self._pending_queries),
            "cached": len(self._cache),
            "pending": len(self._pending_queries),
            "by_phase": self._group_by_phase(),
            "by_tag": self._group_by_tag(),
        }

    def _group_by_phase(self) -> dict[str, int]:
        """Group queries by phase."""
        counts: dict[str, int] = {}
        for result in self._cache.values():
            phase = result.query.phase or "unknown"
            counts[phase] = counts.get(phase, 0) + 1
        return counts

    def _group_by_tag(self) -> dict[str, int]:
        """Group queries by tag."""
        counts: dict[str, int] = {}
        for result in self._cache.values():
            for tag in result.query.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts
