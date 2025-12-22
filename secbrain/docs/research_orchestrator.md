# ResearchOrchestrator

The `ResearchOrchestrator` is a centralized research management system for SecBrain that addresses critical issues with research integration.

## Problem Statement

Previously, research calls in SecBrain were:
- Scatter-shot and not strategically placed
- Not deduplicated (same queries could be made multiple times)
- Not cached properly
- Missing strategic timing and prioritization
- Results weren't fed back into hypothesis refinement

## Solution

The `ResearchOrchestrator` provides:

### Core Features

1. **Query Deduplication**: Automatically prevents duplicate research queries
2. **Priority-based Scheduling**: Execute most important queries first
3. **Result Caching**: Cache results to avoid redundant API calls
4. **Batch Execution**: Execute multiple queries efficiently in parallel
5. **Concurrency Control**: Limit concurrent research requests (default: 3)
6. **Strategic Timing**: Queue queries and execute at optimal times

### Specialized Research Methods

The orchestrator provides domain-specific research methods:

- `research_vulnerability_pattern()`: Research specific vulnerability patterns with recent attack examples
- `research_protocol_type()`: Research common vulnerabilities for protocol types (lending, AMM, etc.)
- `research_exploit_validation()`: Validate if reverts indicate near-miss exploits
- `research_similar_exploits()`: Find historical exploits of similar types

### Analytics

- `get_research_summary()`: Get metrics on research activity (total, cached, pending, by phase, by tag)
- `get_cached_result()`: Retrieve cached results directly

## Usage

### Basic Usage

```python
from secbrain.core import ResearchOrchestrator, ResearchQuery, RunContext
from secbrain.tools.perplexity_research import PerplexityResearch

# Initialize
orchestrator = ResearchOrchestrator(run_context, research_client)

# Queue queries
query = ResearchQuery(
    question="What are common reentrancy patterns?",
    context="Analyzing lending protocol",
    priority=8,  # 1-10, higher = more important
    phase="hypothesis",
    tags=["reentrancy", "defi"],
)
await orchestrator.queue_research(query)

# Execute top priority queries
results = await orchestrator.execute_batch(max_queries=5)
```

### Using Specialized Methods

```python
# Research vulnerability patterns
result = await orchestrator.research_vulnerability_pattern(
    vuln_type="reentrancy",
    contract_context="ERC4626 vault with external calls",
    priority=8,
)

# Research protocol-specific vulnerabilities
result = await orchestrator.research_protocol_type(
    protocol_type="lending",
    functions=["deposit", "withdraw", "borrow"],
    priority=7,
)

# Validate exploit attempts
result = await orchestrator.research_exploit_validation(
    vuln_type="flash_loan",
    revert_reason="Insufficient collateral ratio",
    priority=6,
)

# Find historical exploits
result = await orchestrator.research_similar_exploits(
    vuln_type="oracle_manipulation",
    target_protocol="Aave",
    priority=8,
)
```

### Analytics

```python
# Get summary of research activity
summary = orchestrator.get_research_summary()
print(f"Total queries: {summary['total_queries']}")
print(f"Cached: {summary['cached']}")
print(f"Pending: {summary['pending']}")
print(f"By phase: {summary['by_phase']}")
print(f"By tag: {summary['by_tag']}")

# Get cached result directly
cached = orchestrator.get_cached_result(
    question="What are reentrancy patterns?",
    context="Lending protocol"
)
```

## Architecture

### ResearchQuery

Structured query with metadata:
- `question`: The research question
- `context`: Additional context for the query
- `priority`: 1-10, higher = more important
- `phase`: Current analysis phase (hypothesis, exploit, etc.)
- `tags`: List of tags for categorization
- `cache_key`: Auto-generated hash for deduplication

### ResearchResult

Result with metadata:
- `query`: The original ResearchQuery
- `answer`: The research answer
- `sources`: List of source URLs
- `confidence`: Confidence score (0.0-1.0)
- `cached`: Whether result was retrieved from cache

### ResearchOrchestrator

Main orchestrator class:
- `queue_research()`: Add query to pending queue
- `execute_batch()`: Execute top N priority queries
- `_execute_single()`: Execute single query with caching
- Specialized methods for common research patterns
- Analytics and summary methods

## Integration with Existing Code

The `ResearchOrchestrator` integrates seamlessly with:

- **RunContext**: Uses existing context for state management
- **PerplexityResearch**: Delegates actual research calls to existing client
- **Session caching**: Leverages RunContext's research cache

## Example

See `examples/research_orchestrator_example.py` for complete usage examples.

## Testing

Comprehensive test suite in `tests/test_research_orchestrator.py` covers:
- Query deduplication
- Priority-based scheduling
- Result caching
- Batch execution
- Specialized methods
- Concurrent execution limits
- Race condition handling

Run tests with:
```bash
pytest tests/test_research_orchestrator.py -v
```

## Future Enhancements

Potential improvements:
1. TTL-based cache expiration (integrate with PerplexityResearch TTL)
2. Query cost estimation and budgeting
3. Research result quality scoring
4. Adaptive priority adjustment based on results
5. Research dependency tracking (queries that depend on other results)
