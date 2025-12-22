"""Tests for ResearchOrchestrator."""

from __future__ import annotations

import pytest

from secbrain.agents.research_orchestrator import (
    ResearchOrchestrator,
    ResearchQuery,
    ResearchResult,
)


class MockRunContext:
    """Mock RunContext for testing."""

    def is_killed(self):
        return False


class MockResearchClient:
    """Mock research client for testing."""

    async def research(self, question: str, context: str = "") -> dict:
        """Mock research method."""
        return {
            "answer": f"Answer to: {question}",
            "confidence": 0.8,
            "sources": ["source1", "source2"],
        }


@pytest.mark.asyncio
async def test_research_orchestrator_initialization():
    """Test ResearchOrchestrator initialization."""
    run_context = MockRunContext()
    research_client = MockResearchClient()

    orch = ResearchOrchestrator(
        run_context=run_context,
        research_client=research_client,
    )

    assert orch.run_context == run_context
    assert orch.research_client == research_client
    assert orch.max_concurrent == 3
    assert orch.priority_threshold == 5


@pytest.mark.asyncio
async def test_queue_research():
    """Test queuing research queries."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)

    query = ResearchQuery(
        question="What are common vulnerabilities?",
        context="Smart contract",
        priority=7,
    )

    query_hash = await orch.queue_research(query)

    assert query_hash is not None
    assert len(orch._pending_queries) == 1
    assert orch._stats["total_queries"] == 1


@pytest.mark.asyncio
async def test_deduplication():
    """Test that identical queries are deduplicated."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)

    # Queue same query twice
    q1 = ResearchQuery(question="test", context="ctx", priority=5)
    q2 = ResearchQuery(question="test", context="ctx", priority=5)

    hash1 = await orch.queue_research(q1)
    hash2 = await orch.queue_research(q2)

    # Should have same hash and only 1 pending
    assert hash1 == hash2
    assert len(orch._pending_queries) == 1


@pytest.mark.asyncio
async def test_priority_ordering():
    """Test that queries are executed in priority order."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)

    # Queue low priority then high priority
    q_low = ResearchQuery(question="low", context="ctx", priority=3)
    q_high = ResearchQuery(question="high", context="ctx", priority=9)

    await orch.queue_research(q_low)
    await orch.queue_research(q_high)

    # Execute batch with limit of 1
    results = await orch.execute_batch(max_queries=1)

    # High priority should execute first
    assert len(results) == 1
    assert results[0].query.question == "high"


@pytest.mark.asyncio
async def test_execute_batch():
    """Test executing a batch of queries."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)

    # Queue multiple queries
    q1 = ResearchQuery(question="q1", context="ctx", priority=5)
    q2 = ResearchQuery(question="q2", context="ctx", priority=6)

    await orch.queue_research(q1)
    await orch.queue_research(q2)

    # Execute batch
    results = await orch.execute_batch()

    assert len(results) == 2
    assert all(isinstance(r, ResearchResult) for r in results)
    assert orch._stats["executed_queries"] == 2


@pytest.mark.asyncio
async def test_caching():
    """Test that results are cached."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)

    # Execute a query
    query = ResearchQuery(question="test", context="ctx", priority=5)
    query_hash = await orch.queue_research(query)
    results = await orch.execute_batch()

    assert len(results) == 1
    assert query_hash in orch._cache

    # Queue same query again
    hash2 = await orch.queue_research(query)
    
    # Should be same hash and already cached
    assert hash2 == query_hash
    assert orch._stats["cached_hits"] == 1
    
    # Get cached result directly
    cached_result = orch.get_cached_result(query_hash)
    assert cached_result is not None
    assert cached_result.query.question == "test"


@pytest.mark.asyncio
async def test_research_protocol_type():
    """Test researching a specific protocol type."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client, priority_threshold=0)

    result = await orch.research_protocol_type(
        protocol_type="defi_vault",
        functions=["deposit", "withdraw"],
        priority=8,
    )

    assert result is not None
    assert isinstance(result, ResearchResult)
    assert "defi_vault" in result.query.question.lower()


def test_get_research_summary():
    """Test getting research summary."""
    run_context = MockRunContext()
    research_client = MockResearchClient()
    orch = ResearchOrchestrator(run_context, research_client)

    summary = orch.get_research_summary()

    assert "stats" in summary
    assert "pending_count" in summary
    assert "cache_size" in summary
    assert summary["stats"]["total_queries"] == 0
