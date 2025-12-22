"""Research orchestrator for coordinating research queries across agents."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.core.context import RunContext
    from secbrain.tools.perplexity_research import PerplexityResearch

logger = logging.getLogger(__name__)


@dataclass
class ResearchQuery:
    """Represents a research query."""

    question: str
    context: str = ""
    priority: int = 5
    phase: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def hash_key(self) -> str:
        """Generate a unique hash for deduplication."""
        content = f"{self.question.lower().strip()}||{self.context[:200]}"
        return hashlib.sha256(content.encode()).hexdigest()
    """A research query with priority and context."""

    question: str
    context: str
    priority: int = 5  # 1-10, higher is more important
    phase: str = ""
    tags: list[str] = field(default_factory=list)
    ttl_hours: int = 24


@dataclass
class ResearchResult:
    """Result from a research query."""

    query: ResearchQuery
    answer: str
    confidence: float
    sources: list[str] = field(default_factory=list)
    cached: bool = False
    error: str | None = None
    sources: list[str]
    cached: bool = False
    error: bool = False


class ResearchOrchestrator:
    """
    Orchestrates research queries across agents.

    Features:
    - Deduplication of identical queries
    - Priority-based execution
    - Result caching
    - Rate limiting
    - Batch processing
    """

    def __init__(
        self,
        run_context: RunContext,
        research_client: PerplexityResearch | None = None,
        max_concurrent: int = 3,
        priority_threshold: int = 5,
    ):
        self.run_context = run_context
        self.research_client = research_client
        self.max_concurrent = max_concurrent
        self.priority_threshold = priority_threshold

        # Query management
        self._pending_queries: dict[str, ResearchQuery] = {}
        self._cache: dict[str, ResearchResult] = {}
        self._results: list[ResearchResult] = []

        # Rate limiting
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate_limiter = asyncio.Semaphore(10)  # Additional concurrency limit
        self._last_query_time = 0.0
        self._min_query_interval = 6.0  # 6 seconds between queries
        self._time_lock = asyncio.Lock()  # Lock for thread-safe timestamp updates

        # Statistics
        self._stats = {
            "total_queries": 0,
            "cached_hits": 0,
            "executed_queries": 0,
            "failed_queries": 0,
        }

    async def queue_research(self, query: ResearchQuery) -> str:
        """Queue a research query for execution. Returns the query hash."""
        query_hash = query.hash_key()

        # Check if already in cache
        if query_hash in self._cache:
            self._stats["cached_hits"] += 1
            return query_hash

        # Check if already pending (deduplicate)
        if query_hash in self._pending_queries:
            # Update priority if higher
            existing = self._pending_queries[query_hash]
            if query.priority > existing.priority:
                existing.priority = query.priority
            return query_hash

        # Add to pending queue
        self._pending_queries[query_hash] = query
        self._stats["total_queries"] += 1
        return query_hash

    async def execute_batch(self, max_queries: int | None = None) -> list[ResearchResult]:
        """Execute pending queries in priority order."""
        if not self.research_client:
            return []

        # Sort by priority (descending)
        sorted_queries = sorted(
            self._pending_queries.values(),
            key=lambda q: q.priority,
            reverse=True,
        )

        # Filter by priority threshold
        queries_to_execute = [q for q in sorted_queries if q.priority >= self.priority_threshold]

        if max_queries is not None:
            queries_to_execute = queries_to_execute[:max_queries]

        # Execute queries
        results = []
        for query in queries_to_execute:
            query_hash = query.hash_key()

            # Check cache first
            if query_hash in self._cache:
                cached_result = self._cache[query_hash]
                # Create a copy to avoid mutating the cached object
                result_copy = ResearchResult(
                    query=cached_result.query,
                    answer=cached_result.answer,
                    confidence=cached_result.confidence,
                    sources=cached_result.sources,
                    cached=True,
                    error=cached_result.error,
                )
                results.append(result_copy)
                self._pending_queries.pop(query_hash, None)
                continue

            # Execute query
            result = await self._execute_query(query)
            results.append(result)

            # Cache result
            self._cache[query_hash] = result
            self._results.append(result)

            # Remove from pending
            self._pending_queries.pop(query_hash, None)

        return results

    async def _execute_query(self, query: ResearchQuery) -> ResearchResult:
        """Execute a single research query with rate limiting."""
        async with self._semaphore, self._rate_limiter:
            # Rate limiting with lock to prevent race conditions
            async with self._time_lock:
                current_time = asyncio.get_event_loop().time()
                time_since_last = current_time - self._last_query_time
                
                if time_since_last < self._min_query_interval:
                    sleep_time = self._min_query_interval - time_since_last
                    # Update timestamp before releasing the lock
                    self._last_query_time = current_time + sleep_time
                else:
                    self._last_query_time = current_time
            
            # Sleep outside the lock to allow other queries to check timing
            if time_since_last < self._min_query_interval:
                await asyncio.sleep(sleep_time)

            try:
                if not self.research_client:
                    return ResearchResult(
                        query=query,
                        answer="",
                        confidence=0.0,
                        error="No research client available",
                    )

                # Execute research query
                response = await self.research_client.research(
                    question=query.question,
                    context=query.context,
                )

                self._stats["executed_queries"] += 1

                return ResearchResult(
                    query=query,
                    answer=response.get("answer", ""),
                    confidence=response.get("confidence", 0.5),
                    sources=response.get("sources", []),
                )

            except Exception as e:
                self._stats["failed_queries"] += 1
                return ResearchResult(
                    query=query,
                    answer="",
                    confidence=0.0,
                    error=str(e),
                )

    async def research_protocol_type(
        self,
        protocol_type: str,
        functions: list[str] | None = None,
        priority: int = 7,
    ) -> ResearchResult | None:
        """Research vulnerabilities specific to a protocol type."""
        question = f"What are the most common vulnerabilities in {protocol_type} protocols?"

        context_parts = [f"Protocol type: {protocol_type}"]
        if functions:
            context_parts.append(f"Available functions: {', '.join(functions[:10])}")

        context = " | ".join(context_parts)

        query = ResearchQuery(
            question=question,
            context=context,
            priority=priority,
            phase="hypothesis",
            metadata={"protocol_type": protocol_type},
        )

        query_hash = await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)

        # Find the result for this query
        for result in results:
            if result.query.hash_key() == query_hash:
                return result

        # Check cache
        if query_hash in self._cache:
            return self._cache[query_hash]

        # If we reach here, the query was queued but no result was produced or cached.
        # This can happen if the query was filtered out by a priority threshold.
        return ResearchResult(
            query=query,
            answer="",
            confidence=0.0,
            sources=[],
            cached=False,
            error=(
                "No research result was produced for this protocol type query. "
                "The query may have been filtered out by a priority threshold or "
                "failed to execute."
            ),
        )

    def get_research_summary(self) -> dict[str, Any]:
        """Get summary of research activity."""
        return {
            "stats": dict(self._stats),
            "pending_count": len(self._pending_queries),
            "cache_size": len(self._cache),
            "results_count": len(self._results),
        }

    def get_cached_result(self, query_hash: str) -> ResearchResult | None:
        """Get a cached result by query hash."""
        return self._cache.get(query_hash)

    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._cache.clear()

    def save_cache(self, filepath: str) -> None:
        """Save cache to a JSON file."""
        cache_data = {}
        for query_hash, result in self._cache.items():
            cache_data[query_hash] = {
                "question": result.query.question,
                "context": result.query.context,
                "answer": result.answer,
                "confidence": result.confidence,
                "sources": result.sources,
            }

        with open(filepath, "w") as f:
            json.dump(cache_data, f, indent=2)

    def load_cache(self, filepath: str) -> None:
        """Load cache from a JSON file."""
        try:
            with open(filepath) as f:
                cache_data = json.load(f)

            for query_hash, data in cache_data.items():
                query = ResearchQuery(
                    question=data["question"],
                    context=data.get("context", ""),
                )
                result = ResearchResult(
                    query=query,
                    answer=data["answer"],
                    confidence=data.get("confidence", 0.5),
                    sources=data.get("sources", []),
                    cached=True,
                )
                self._cache[query_hash] = result
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Expected errors when cache doesn't exist or is corrupted - silently continue
            pass
        except Exception as e:
            # Unexpected errors - log but don't fail
            logger.warning("Unexpected error loading research cache: %s", str(e), exc_info=True)

    async def research_vulnerability_pattern(
        self,
        vuln_type: str,
        contract_context: str,
        priority: int = 7,
    ) -> ResearchResult | None:
        """Research specific vulnerability exploitation patterns."""
        query = ResearchQuery(
            question=f"What are the exploitation techniques for {vuln_type} vulnerabilities in {contract_context}? Include step-by-step attack methods and success indicators.",
            context=f"Vulnerability pattern research for {vuln_type}",
            priority=priority,
            phase="hypothesis",
            tags=[vuln_type, "exploitation"],
            ttl_hours=48,
        )

        await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)
        return results[0] if results else None

    def get_results(self) -> list[ResearchResult]:
        """Get all research results collected so far."""
        return self._results.copy()

    def clear_queue(self) -> None:
        """Clear the research queue."""
        self._query_queue.clear()

    def clear_results(self) -> None:
        """Clear stored results."""
        self._results.clear()
