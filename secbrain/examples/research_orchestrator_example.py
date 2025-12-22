"""Example usage of ResearchOrchestrator for strategic research management.

This example demonstrates how to use the ResearchOrchestrator to:
1. Queue research queries with priorities
2. Execute batches efficiently
3. Use specialized research methods
4. Get research analytics
"""

import asyncio
from pathlib import Path

from secbrain.core.context import RunContext
from secbrain.core.research_orchestrator import (
    ResearchOrchestrator,
    ResearchQuery,
)
from secbrain.tools.perplexity_research import PerplexityResearch


async def example_basic_usage():
    """Example: Basic queue and execute pattern."""
    # Setup (in real usage, these would come from your orchestrator)
    workspace = Path("/tmp/research_example")
    workspace.mkdir(parents=True, exist_ok=True)

    scope_file = workspace / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")

    program_file = workspace / "program.yaml"
    program_file.write_text("name: 'example-program'\n")

    run_context = RunContext(
        workspace_path=workspace,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,  # Use dry-run for this example
    )

    research_client = PerplexityResearch()
    orchestrator = ResearchOrchestrator(run_context, research_client)

    # Queue multiple research queries with different priorities
    queries = [
        ResearchQuery(
            question="What are common reentrancy patterns in DeFi?",
            context="Analyzing lending protocol",
            priority=8,  # High priority
            phase="hypothesis",
            tags=["reentrancy", "defi"],
        ),
        ResearchQuery(
            question="How to detect price oracle manipulation?",
            context="Analyzing AMM protocol",
            priority=5,  # Medium priority
            phase="hypothesis",
            tags=["oracle", "manipulation"],
        ),
        ResearchQuery(
            question="What are flash loan attack vectors?",
            context="Protocol with flash loan support",
            priority=9,  # Highest priority
            phase="hypothesis",
            tags=["flash_loan", "attack"],
        ),
    ]

    # Queue all queries
    for query in queries:
        await orchestrator.queue_research(query)

    # Execute top 2 priority queries
    results = await orchestrator.execute_batch(max_queries=2)

    print(f"Executed {len(results)} queries")
    for result in results:
        print(f"  - {result.query.question[:60]}...")
        print(f"    Priority: {result.query.priority}")
        print(f"    Answer: {result.answer[:100]}...")
        print()

    # Get summary
    summary = orchestrator.get_research_summary()
    print("Research Summary:")
    print(f"  Total queries: {summary['total_queries']}")
    print(f"  Cached: {summary['cached']}")
    print(f"  Pending: {summary['pending']}")
    print(f"  By phase: {summary['by_phase']}")
    print(f"  By tag: {summary['by_tag']}")


async def example_specialized_methods():
    """Example: Using specialized research methods."""
    workspace = Path("/tmp/research_example2")
    workspace.mkdir(parents=True, exist_ok=True)

    scope_file = workspace / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")

    program_file = workspace / "program.yaml"
    program_file.write_text("name: 'example-program'\n")

    run_context = RunContext(
        workspace_path=workspace,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,
    )

    research_client = PerplexityResearch()
    orchestrator = ResearchOrchestrator(run_context, research_client)

    # Research vulnerability patterns
    result = await orchestrator.research_vulnerability_pattern(
        vuln_type="reentrancy",
        contract_context="ERC4626 vault with external calls",
        priority=8,
    )
    if result:
        print("Vulnerability Pattern Research:")
        print(f"  Question: {result.query.question}")
        print(f"  Answer: {result.answer[:150]}...")
        print()

    # Research protocol-specific vulnerabilities
    result = await orchestrator.research_protocol_type(
        protocol_type="lending",
        functions=["deposit", "withdraw", "borrow", "liquidate"],
        priority=7,
    )
    if result:
        print("Protocol Type Research:")
        print(f"  Question: {result.query.question}")
        print(f"  Answer: {result.answer[:150]}...")
        print()

    # Research exploit validation
    result = await orchestrator.research_exploit_validation(
        vuln_type="flash_loan",
        revert_reason="Insufficient collateral ratio",
        priority=6,
    )
    if result:
        print("Exploit Validation Research:")
        print(f"  Question: {result.query.question}")
        print(f"  Answer: {result.answer[:150]}...")
        print()

    # Research similar historical exploits
    result = await orchestrator.research_similar_exploits(
        vuln_type="oracle_manipulation",
        target_protocol="Aave",
        priority=8,
    )
    if result:
        print("Historical Exploits Research:")
        print(f"  Question: {result.query.question}")
        print(f"  Answer: {result.answer[:150]}...")
        print()


async def example_caching():
    """Example: Demonstrating query deduplication and caching."""
    workspace = Path("/tmp/research_example3")
    workspace.mkdir(parents=True, exist_ok=True)

    scope_file = workspace / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")

    program_file = workspace / "program.yaml"
    program_file.write_text("name: 'example-program'\n")

    run_context = RunContext(
        workspace_path=workspace,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,
    )

    research_client = PerplexityResearch()
    orchestrator = ResearchOrchestrator(run_context, research_client)

    # Queue the same query twice (should be deduplicated)
    query = ResearchQuery(
        question="What are ERC20 approve() vulnerabilities?",
        context="Token contract analysis",
        priority=5,
    )

    await orchestrator.queue_research(query)
    await orchestrator.queue_research(query)

    print(f"Queued same query twice, pending: {len(orchestrator._pending_queries)}")
    # Should only have 1 pending query

    # Execute it
    results = await orchestrator.execute_batch(max_queries=1)
    print(f"Executed {len(results)} queries")

    # Try to queue again (should be in cache now)
    await orchestrator.queue_research(query)
    print(f"Queued again after execution, pending: {len(orchestrator._pending_queries)}")
    # Should have 0 pending (already cached)

    # Get cached result directly
    cached = orchestrator.get_cached_result(
        "What are ERC20 approve() vulnerabilities?",
        "Token contract analysis"
    )
    print(f"Retrieved from cache: {cached is not None}")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("Example 1: Basic Usage")
    print("=" * 70)
    await example_basic_usage()

    print("\n" + "=" * 70)
    print("Example 2: Specialized Methods")
    print("=" * 70)
    await example_specialized_methods()

    print("\n" + "=" * 70)
    print("Example 3: Caching and Deduplication")
    print("=" * 70)
    await example_caching()


if __name__ == "__main__":
    asyncio.run(main())
