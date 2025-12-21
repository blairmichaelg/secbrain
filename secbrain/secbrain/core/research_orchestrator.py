"""Centralized research orchestrator for strategic knowledge gathering."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from typing import Any

from secbrain.core.context import RunContext


@dataclass
class ResearchQuery:
    """Structured research query with context."""

    question: str
    context: str
    priority: int = 5  # 1-10, higher = more important
    phase: str = ""
    tags: list[str] = field(default_factory=list)
    cache_key: str = field(init=False)

    def __post_init__(self) -> None:
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

    async def queue_research(self, query: ResearchQuery) -> None:
        """Queue a research query for later execution."""
        # Check cache first
        if query.cache_key in self._cache:
            return

        # Check if already queued
        if any(q.cache_key == query.cache_key for q in self._pending_queries):
            return

        self._pending_queries.append(query)

    async def execute_batch(self, max_queries: int = 5) -> list[ResearchResult]:
        """Execute top priority queries in batch."""
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

        # Filter out exceptions
        return [r for r in results if isinstance(r, ResearchResult)]

    async def _execute_single(self, query: ResearchQuery) -> ResearchResult:
        """Execute a single research query."""
        # Check cache again (race condition)
        if query.cache_key in self._cache:
            return self._cache[query.cache_key]

        async with self._semaphore:
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
        """Research a specific vulnerability pattern."""
        query = ResearchQuery(
            question=f"What are the key indicators and exploitation techniques for {vuln_type} vulnerabilities in smart contracts? Include recent (2023-2024) attack patterns.",
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
        """Research common vulnerabilities for a protocol type."""
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
        """Research whether a revert indicates a near-miss exploit."""
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
        """Research historical exploits of similar type."""
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
