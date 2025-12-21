# Hypothesis Enhancement System

This module implements targeted hypothesis generation with research-driven insights for the SecBrain vulnerability detection system.

## Components

### ResearchOrchestrator (`research_orchestrator.py`)

Manages research queries with priority-based execution and batch processing.

**Features:**
- Priority queue for research queries (1-10, higher = more important)
- Batch execution with rate limiting integration
- Protocol-specific research methods
- Integration with PerplexityResearch API

**Usage:**
```python
from secbrain.agents.research_orchestrator import ResearchOrchestrator, ResearchQuery

# Initialize orchestrator
orchestrator = ResearchOrchestrator(research_client, run_context)

# Queue research queries
await orchestrator.queue_research(
    ResearchQuery(
        question="What are common vulnerabilities in DeFi vaults?",
        context="Protocol type research",
        priority=9,
        phase="hypothesis",
        tags=["defi_vault", "vulnerability_patterns"],
        ttl_hours=48,
    )
)

# Execute batch
results = await orchestrator.execute_batch(max_queries=5)

# Use convenience methods
protocol_research = await orchestrator.research_protocol_type(
    protocol_type="defi_vault",
    functions=["deposit", "withdraw"],
    priority=8,
)
```

### HypothesisEnhancer (`hypothesis_enhancer.py`)

Enhances vulnerability hypotheses using research-validated patterns and failure feedback loops.

**Features:**
- Research-validated pattern matching
- Protocol-specific vulnerability boosting
- Failure analysis and refinement
- Targeted LLM prompt generation
- Confidence calibration based on multiple signals

**Usage:**
```python
from secbrain.agents.hypothesis_enhancer import HypothesisEnhancer

# Initialize enhancer
enhancer = HypothesisEnhancer(orchestrator)

# Enhance contract hypotheses
contract_metadata = {
    "classification": {"protocol_type": "amm"},
    "functions": ["swap", "addLiquidity", "removeLiquidity"],
    "address": "0x1234...",
}

static_hypotheses = [
    {"vuln_type": "reentrancy", "confidence": 0.6, ...},
    {"vuln_type": "oracle", "confidence": 0.7, ...},
]

enhanced = await enhancer.enhance_contract_hypotheses(
    contract_metadata,
    static_hypotheses,
)

# Refine from failures
failed_attempts = [
    {"revert_reason": "Insufficient profit"},
    {"revert_reason": "Not authorized"},
]

refinements = await enhancer.refine_from_failures(
    failed_attempts,
    original_hypothesis,
)

# Generate targeted LLM prompt
prompt = await enhancer.generate_targeted_llm_prompt(
    contract_metadata,
    research_context="Recent AMM exploits...",
)

# Calibrate confidence
confidence = enhancer.calibrate_confidence(
    hypothesis=hypothesis,
    research_validated=True,
    similar_exploits_found=True,
    failure_feedback={"attempt_count": 2, "near_miss_count": 1},
)
```

## Key Improvements

1. **Research-Driven Targeting**: Hypotheses are validated against real-world exploit data
2. **Failure Feedback Loops**: Failed exploits inform refined hypotheses
3. **Protocol-Specific Knowledge**: Vulnerabilities are boosted based on protocol type
4. **Confidence Calibration**: Multiple signals (research, exploits, failures) adjust confidence
5. **Targeted Prompts**: LLM prompts include research context for better results

## Architecture

```
┌─────────────────────┐
│ PerplexityResearch  │
│  (API Client)       │
└──────────┬──────────┘
           │
           │ uses
           ▼
┌─────────────────────┐
│ ResearchOrchestrator│
│  - Priority Queue   │
│  - Batch Execution  │
│  - Protocol Methods │
└──────────┬──────────┘
           │
           │ powers
           ▼
┌─────────────────────┐
│ HypothesisEnhancer  │
│  - Enhancement      │
│  - Refinement       │
│  - Calibration      │
└─────────────────────┘
```

## Testing

Run tests with:
```bash
pytest tests/test_hypothesis_enhancement.py -v
```

All 9 tests cover:
- Research query queueing and priority ordering
- Batch execution limits
- Protocol-specific research
- Vulnerability type extraction
- Failure categorization
- Confidence calibration
- Hypothesis enhancement
- Targeted prompt generation
- Failure-based refinement

## Integration

This system integrates with:
- `VulnHypothesisAgent`: Enhances generated hypotheses
- `ExploitAgent`: Refines hypotheses based on exploit failures
- `PerplexityResearch`: Provides research data with TTL caching
- `RunContext`: Manages execution state and caching
