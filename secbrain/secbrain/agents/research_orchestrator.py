"""Research orchestrator for queuing and executing research queries."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from secbrain.core.context import RunContext
    from secbrain.tools.perplexity_research import PerplexityResearch

logger = logging.getLogger(__name__)


@dataclass
class ResearchQuery:
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
    sources: list[str]
    cached: bool = False
    error: bool = False


class ResearchOrchestrator:
    """
    Orchestrates research queries with priority-based execution.

    Features:
    - Priority queue for research queries
    - Batch execution with rate limiting
    - Protocol-specific research methods
    - Integration with PerplexityResearch
    """

    def __init__(self, research_client: PerplexityResearch, run_context: RunContext):
        self.research_client = research_client
        self.run_context = run_context
        self._query_queue: list[ResearchQuery] = []
        self._results: list[ResearchResult] = []

    async def queue_research(self, query: ResearchQuery) -> None:
        """Add a research query to the priority queue."""
        self._query_queue.append(query)
        # Sort by priority (higher priority first)
        self._query_queue.sort(key=lambda q: q.priority, reverse=True)

    async def execute_batch(self, max_queries: int = 10) -> list[ResearchResult]:
        """Execute a batch of queued research queries."""
        if not self._query_queue:
            return []

        # Get the top priority queries
        queries_to_execute = self._query_queue[:max_queries]
        self._query_queue = self._query_queue[max_queries:]

        results = []
        for query in queries_to_execute:
            try:
                # Use the research client to execute the query
                response = await self.research_client.ask_research(
                    question=query.question,
                    context=query.context,
                    run_context=self.run_context,
                    ttl_hours=query.ttl_hours,
                )

                result = ResearchResult(
                    query=query,
                    answer=response.get("answer", ""),
                    sources=response.get("sources", []),
                    cached=response.get("cached", False),
                    error=response.get("error", False),
                )
                results.append(result)
                self._results.append(result)

            except Exception as e:
                # Log the exception with context
                logger.error(
                    "Research query failed",
                    exc_info=True,
                    extra={
                        "question": query.question[:100],
                        "context": query.context,
                        "priority": query.priority,
                        "phase": query.phase,
                        "exception_type": type(e).__name__,
                    },
                )
                # Create an error result
                error_result = ResearchResult(
                    query=query,
                    answer=f"Error: {e!s}",
                    sources=[],
                    cached=False,
                    error=True,
                )
                results.append(error_result)
                self._results.append(error_result)

        return results

    async def research_protocol_type(
        self,
        protocol_type: str,
        functions: list[str],
        priority: int = 7,
    ) -> ResearchResult | None:
        """Research protocol-specific vulnerabilities."""
        query = ResearchQuery(
            question=f"What are the most common vulnerabilities in {protocol_type} protocols with functions like {', '.join(functions[:5])}? Include recent exploits and attack patterns.",
            context=f"Protocol type research for {protocol_type}",
            priority=priority,
            phase="hypothesis",
            tags=[protocol_type, "vulnerability_patterns"],
            ttl_hours=48,
        )

        await self.queue_research(query)
        results = await self.execute_batch(max_queries=1)
        return results[0] if results else None

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
