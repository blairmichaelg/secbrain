"""Tests for the ResearchOrchestrator class."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from secbrain.core.context import RunContext
from secbrain.core.research_orchestrator import (
    ResearchOrchestrator,
    ResearchQuery,
    ResearchResult,
)


class MockResearchClient:
    """Mock research client for testing."""

    def __init__(self):
        self.call_count = 0
        self.calls: list[dict[str, Any]] = []

    async def ask_research(
        self,
        question: str,
        context: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Mock research call."""
        self.call_count += 1
        self.calls.append({
            "question": question,
            "context": context,
        })

        return {
            "answer": f"Mock answer for: {question[:50]}",
            "sources": ["mock-source-1", "mock-source-2"],
            "cached": False,
        }


@pytest.fixture
def mock_run_context(tmp_path: Path) -> RunContext:
    """Create a mock run context for testing."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Create minimal scope and program files
    scope_file = tmp_path / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n", encoding="utf-8")

    program_file = tmp_path / "program.yaml"
    program_file.write_text("name: 'test-program'\n", encoding="utf-8")

    return RunContext(
        workspace_path=workspace,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,
    )


@pytest.fixture
def mock_research_client() -> MockResearchClient:
    """Create a mock research client."""
    return MockResearchClient()


@pytest.fixture
def orchestrator(mock_run_context: RunContext, mock_research_client: MockResearchClient) -> ResearchOrchestrator:
    """Create a ResearchOrchestrator instance."""
    return ResearchOrchestrator(mock_run_context, mock_research_client)


class TestResearchQuery:
    """Tests for ResearchQuery dataclass."""

    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        query1 = ResearchQuery(
            question="What is reentrancy?",
            context="Smart contract analysis",
            priority=5,
        )
        query2 = ResearchQuery(
            question="What is reentrancy?",
            context="Smart contract analysis",
            priority=8,  # Different priority
        )

        # Same question and context should generate same cache key
        assert query1.cache_key == query2.cache_key

    def test_cache_key_uniqueness(self):
        """Test that different queries generate different cache keys."""
        query1 = ResearchQuery(
            question="What is reentrancy?",
            context="Smart contract analysis",
        )
        query2 = ResearchQuery(
            question="What is flash loan?",
            context="Smart contract analysis",
        )

        assert query1.cache_key != query2.cache_key


class TestResearchOrchestrator:
    """Tests for ResearchOrchestrator class."""

    async def test_queue_research(self, orchestrator: ResearchOrchestrator):
        """Test queueing research queries."""
        query = ResearchQuery(
            question="What is reentrancy?",
            context="Analysis",
            priority=5,
        )

        await orchestrator.queue_research(query)

        assert len(orchestrator._pending_queries) == 1
        assert orchestrator._pending_queries[0].cache_key == query.cache_key

    async def test_queue_deduplication(self, orchestrator: ResearchOrchestrator):
        """Test that duplicate queries are not queued."""
        query1 = ResearchQuery(
            question="What is reentrancy?",
            context="Analysis",
            priority=5,
        )
        query2 = ResearchQuery(
            question="What is reentrancy?",
            context="Analysis",
            priority=8,  # Different priority but same question/context
        )

        await orchestrator.queue_research(query1)
        await orchestrator.queue_research(query2)

        # Should only have one query
        assert len(orchestrator._pending_queries) == 1

    async def test_priority_based_scheduling(self, orchestrator: ResearchOrchestrator):
        """Test that queries are executed in priority order."""
        low_priority = ResearchQuery(
            question="Low priority",
            context="Context",
            priority=3,
        )
        high_priority = ResearchQuery(
            question="High priority",
            context="Context",
            priority=9,
        )
        medium_priority = ResearchQuery(
            question="Medium priority",
            context="Context",
            priority=6,
        )

        # Queue in random order
        await orchestrator.queue_research(low_priority)
        await orchestrator.queue_research(high_priority)
        await orchestrator.queue_research(medium_priority)

        # Execute batch should prioritize high priority first
        results = await orchestrator.execute_batch(max_queries=2)

        # Should get high and medium priority (top 2)
        assert len(results) == 2
        assert "High priority" in results[0].answer
        assert "Medium priority" in results[1].answer

        # Low priority should still be pending
        assert len(orchestrator._pending_queries) == 1

    async def test_execute_batch(self, orchestrator: ResearchOrchestrator, mock_research_client: MockResearchClient):
        """Test batch execution of queries."""
        queries = [
            ResearchQuery(question=f"Question {i}", context="Context", priority=i+1)
            for i in range(5)
        ]

        for query in queries:
            await orchestrator.queue_research(query)

        results = await orchestrator.execute_batch(max_queries=3)

        # Should execute 3 queries
        assert len(results) == 3
        assert mock_research_client.call_count == 3

        # Should have 2 pending
        assert len(orchestrator._pending_queries) == 2

    async def test_result_caching(self, orchestrator: ResearchOrchestrator, mock_research_client: MockResearchClient):
        """Test that results are cached."""
        query = ResearchQuery(
            question="Cacheable query",
            context="Context",
            priority=5,
        )

        await orchestrator.queue_research(query)
        results1 = await orchestrator.execute_batch(max_queries=1)

        # Cache should now contain the result
        assert len(orchestrator._cache) == 1
        assert len(results1) == 1

        # Queue same query again
        await orchestrator.queue_research(query)

        # Should not be queued because it's cached
        assert len(orchestrator._pending_queries) == 0

        # Should only have made one API call
        assert mock_research_client.call_count == 1

    async def test_get_cached_result(self, orchestrator: ResearchOrchestrator):
        """Test retrieving cached results."""
        query = ResearchQuery(
            question="Test query",
            context="Test context",
            priority=5,
        )

        await orchestrator.queue_research(query)
        await orchestrator.execute_batch(max_queries=1)

        # Should be able to retrieve cached result
        cached = orchestrator.get_cached_result("Test query", "Test context")

        assert cached is not None
        assert cached.query.question == "Test query"

    async def test_concurrent_execution_limit(self, orchestrator: ResearchOrchestrator, mock_research_client: MockResearchClient):
        """Test that concurrent execution is limited by semaphore."""
        # Create many queries
        queries = [
            ResearchQuery(question=f"Query {i}", context="Context", priority=(i % 10) + 1)
            for i in range(10)
        ]

        for query in queries:
            await orchestrator.queue_research(query)

        # Execute all at once
        results = await orchestrator.execute_batch(max_queries=10)

        # All should succeed
        assert len(results) == 10
        assert mock_research_client.call_count == 10

    async def test_research_vulnerability_pattern(self, orchestrator: ResearchOrchestrator):
        """Test specialized vulnerability pattern research."""
        result = await orchestrator.research_vulnerability_pattern(
            vuln_type="reentrancy",
            contract_context="ERC4626 vault",
            priority=7,
        )

        assert result is not None
        assert isinstance(result, ResearchResult)
        assert "reentrancy" in result.query.question.lower()
        assert result.query.priority == 7
        assert "pattern" in result.query.tags

    async def test_research_protocol_type(self, orchestrator: ResearchOrchestrator):
        """Test protocol type vulnerability research."""
        result = await orchestrator.research_protocol_type(
            protocol_type="lending",
            functions=["borrow", "repay", "liquidate"],
            priority=8,
        )

        assert result is not None
        assert "lending" in result.query.question.lower()
        assert "borrow" in result.query.context
        assert result.query.priority == 8

    async def test_research_exploit_validation(self, orchestrator: ResearchOrchestrator):
        """Test exploit validation research."""
        result = await orchestrator.research_exploit_validation(
            vuln_type="flash_loan",
            revert_reason="Insufficient collateral",
            priority=6,
        )

        assert result is not None
        assert "flash_loan" in result.query.question.lower()
        assert "Insufficient collateral" in result.query.question
        assert result.query.priority == 6

    async def test_research_similar_exploits(self, orchestrator: ResearchOrchestrator):
        """Test historical exploit research."""
        result = await orchestrator.research_similar_exploits(
            vuln_type="oracle_manipulation",
            target_protocol="Aave",
            priority=8,
        )

        assert result is not None
        assert "oracle_manipulation" in result.query.question.lower()
        assert "Aave" in result.query.question
        assert "historical" in result.query.tags

    async def test_get_research_summary(self, orchestrator: ResearchOrchestrator):
        """Test research activity summary."""
        # Queue and execute some queries
        queries = [
            ResearchQuery(question="Q1", context="C1", priority=5, phase="hypothesis", tags=["tag1"]),
            ResearchQuery(question="Q2", context="C2", priority=6, phase="hypothesis", tags=["tag2"]),
            ResearchQuery(question="Q3", context="C3", priority=7, phase="exploit", tags=["tag1", "tag2"]),
        ]

        for query in queries:
            await orchestrator.queue_research(query)

        # Execute 2, leave 1 pending (will execute Q3 and Q2 based on priority)
        await orchestrator.execute_batch(max_queries=2)

        summary = orchestrator.get_research_summary()

        assert summary["total_queries"] == 3
        assert summary["cached"] == 2
        assert summary["pending"] == 1
        # Q3 (exploit) and Q2 (hypothesis) were executed
        assert summary["by_phase"]["hypothesis"] == 1
        assert summary["by_phase"]["exploit"] == 1
        # Q3 has both tags, Q2 has tag2
        assert summary["by_tag"]["tag1"] == 1
        assert summary["by_tag"]["tag2"] == 2

    async def test_empty_batch_execution(self, orchestrator: ResearchOrchestrator):
        """Test executing batch with no pending queries."""
        results = await orchestrator.execute_batch(max_queries=5)

        assert results == []

    async def test_race_condition_handling(self, orchestrator: ResearchOrchestrator, mock_research_client: MockResearchClient):
        """Test that race conditions in caching are handled correctly during execution."""
        query = ResearchQuery(
            question="Race condition test",
            context="Context",
            priority=5,
        )

        # Queue the query
        await orchestrator.queue_research(query)

        # Execute the same query concurrently multiple times to test cache check inside semaphore
        tasks = [
            orchestrator._execute_single(query),
            orchestrator._execute_single(query),
            orchestrator._execute_single(query),
        ]
        results = await asyncio.gather(*tasks)

        # All should return results (from cache after first execution)
        assert len(results) == 3
        for result in results:
            assert isinstance(result, ResearchResult)

        # Should only make one API call (others hit cache)
        assert mock_research_client.call_count == 1

        # All results should be marked as cached (except potentially the first)
        # At least 2 should be cached
        cached_count = sum(1 for r in results if r.cached)
        assert cached_count >= 2


class TestValidation:
    """Tests for input validation."""

    def test_priority_out_of_range_low(self):
        """Test that priority below 1 raises ValueError."""
        with pytest.raises(ValueError, match="priority must be between 1 and 10"):
            ResearchQuery(
                question="Test",
                context="Context",
                priority=0,
            )

    def test_priority_out_of_range_high(self):
        """Test that priority above 10 raises ValueError."""
        with pytest.raises(ValueError, match="priority must be between 1 and 10"):
            ResearchQuery(
                question="Test",
                context="Context",
                priority=11,
            )

    def test_confidence_out_of_range_low(self):
        """Test that confidence below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match=r"confidence must be between 0\.0 and 1\.0"):
            ResearchResult(
                query=ResearchQuery(question="Test", context="Context", priority=5),
                answer="Answer",
                sources=[],
                confidence=-0.1,
            )

    def test_confidence_out_of_range_high(self):
        """Test that confidence above 1.0 raises ValueError."""
        with pytest.raises(ValueError, match=r"confidence must be between 0\.0 and 1\.0"):
            ResearchResult(
                query=ResearchQuery(question="Test", context="Context", priority=5),
                answer="Answer",
                sources=[],
                confidence=1.5,
            )

    def test_priority_valid_range(self):
        """Test that priority within 1-10 works correctly."""
        for priority in [1, 5, 10]:
            query = ResearchQuery(
                question="Test",
                context="Context",
                priority=priority,
            )
            assert query.priority == priority

    def test_confidence_valid_range(self):
        """Test that confidence within 0.0-1.0 works correctly."""
        for confidence in [0.0, 0.5, 1.0]:
            result = ResearchResult(
                query=ResearchQuery(question="Test", context="Context", priority=5),
                answer="Answer",
                sources=[],
                confidence=confidence,
            )
            assert result.confidence == confidence
