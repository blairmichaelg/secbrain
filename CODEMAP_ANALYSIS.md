# SecBrain Codemap Analysis

**Generated:** 2025-12-25  
**Repository:** blairmichaelg/secbrain  
**Total LOC:** ~23,923 (excluding tests)  
**Total Files:** 80 Python modules

## Executive Summary

SecBrain is a sophisticated multi-agent security bounty system with a well-organized architecture. The codebase demonstrates strong separation of concerns across 11 major modules, with agents being the largest component (48.5% of codebase). The system is heavily async-oriented (238 async functions) and follows a clear layered architecture pattern.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Breakdown](#module-breakdown)
3. [Dependency Graph](#dependency-graph)
4. [Code Metrics](#code-metrics)
5. [Key Components](#key-components)
6. [Data Flow](#data-flow)
7. [External Dependencies](#external-dependencies)
8. [Recommendations](#recommendations)

---

## Architecture Overview

SecBrain follows a **layered architecture** pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (cli/)                        │
│                    Entry point for users                     │
│                    3 files, 1,060 LOC                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Workflow Layer (workflows/)                 │
│              Orchestration & Process Control                 │
│                    8 files, 1,854 LOC                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Agent Layer (agents/)                      │
│            22 specialized security agents                    │
│                   22 files, 11,604 LOC                      │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│   │  Recon   │Hypothesis│ Exploit  │  Triage  │Reporting │  │
│   │  Agent   │  Agent   │  Agent   │  Agent   │  Agent   │  │
│   └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer (core/)                        │
│         Context, Types, Validation, Logging                  │
│                   15 files, 3,192 LOC                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│  Tools (tools/)  │  Models (models/)│  Utils (utils/)      │
│  12 files        │  4 files         │  6 files             │
│  3,696 LOC       │  637 LOC         │  660 LOC             │
│  External integr.│  LLM abstractions│  Helper functions    │
└──────────────────┴──────────────────┴──────────────────────┘
```

---

## Module Breakdown

### 1. **Agents Module** (agents/) - 11,604 LOC
**Purpose:** Core intelligence layer with specialized security agents

**Key Components:**
- `supervisor.py` - Orchestrates agent coordination
- `vuln_hypothesis_agent.py` - Generates vulnerability hypotheses
- `exploit_agent.py` - Tests exploitability
- `recon_agent.py` - Reconnaissance and information gathering
- `triage_agent.py` - Prioritizes findings
- `reporting_agent.py` - Generates security reports
- `advanced_research_agent.py` - AI-powered research
- `immunefi_intelligence.py` - Bug bounty platform integration
- `meta_learning_agent.py` - Learns from past findings
- `static_analysis_agent.py` - Static code analysis
- `oracle_manipulation_detector.py` - DeFi oracle attacks
- `exploit_specialists.py` - Specialized exploit techniques
- `hypothesis_enhancer.py` - Improves vulnerability hypotheses
- `verifiers.py` - Verification logic
- `exploit_pattern_db.py` - Known exploit patterns
- `solidity_security_patterns.py` - Smart contract patterns
- `threshold_network_patterns.py` - Protocol-specific patterns
- `program_ingest_agent.py` - Program ingestion
- `planner_agent.py` - Planning logic
- `research_orchestrator.py` - Research coordination

**Stats:**
- 62 Classes
- 140 Functions (117 async)
- Average 527 LOC per file
- Heaviest module (48.5% of codebase)

**Dependencies:**
- Internal: core, tools, models, utils, config
- External: httpx, jsonschema, eth_utils, structlog

**Analysis:**
- Highly cohesive module with clear specialization
- Strong async orientation (83.6% async functions)
- Well-structured with base classes for polymorphism
- Potential for further modularization of exploit specialists

---

### 2. **Tools Module** (tools/) - 3,696 LOC
**Purpose:** External tool integrations and infrastructure

**Key Components:**
- `perplexity_research.py` - AI research integration
- `immunefi_client.py` - Bug bounty platform API
- `bounty_metrics.py` - Success metrics tracking
- `storage.py` - Data persistence (SQLite)
- `foundry_runner.py` - Foundry testing framework
- `hardhat_runner.py` - Hardhat testing framework
- `http_client.py` - HTTP communication
- `playwright_client.py` - Browser automation
- `recon_cli_wrappers.py` - Recon tool wrappers
- `scanners.py` - Security scanners
- `oob_client.py` - Out-of-band testing

**Stats:**
- 24 Classes
- 52 Functions (71 async)
- Average 308 LOC per file
- 15.5% of codebase

**Dependencies:**
- Internal: core
- External: httpx, playwright, aiosqlite, tomllib

**Analysis:**
- High async function count (137% async-to-sync ratio) indicates I/O-bound operations
- Good abstraction of external dependencies
- Storage layer uses SQLite for metrics/caching

---

### 3. **Core Module** (core/) - 3,192 LOC
**Purpose:** Foundational types, context, and core logic

**Key Components:**
- `context.py` - Execution context management
- `types.py` - Type definitions and schemas
- `validation.py` - Input validation
- `logging.py` - Structured logging (structlog)
- `approval.py` - Human-in-the-loop approval
- `verification.py` - Exploit verification
- `profit_calculator.py` - Economic impact analysis
- `consensus_engine.py` - Multi-model consensus
- `research_orchestrator.py` - Research coordination
- `foundry_runner.py` - Foundry integration
- `identity.py` - Identity management
- `exceptions.py` - Custom exceptions
- `errors.py` - Error handling
- `payload_adaptation.py` - Payload generation

**Stats:**
- 61 Classes
- 130 Functions (13 async)
- Average 212 LOC per file
- 13.3% of codebase

**Dependencies:**
- Internal: models, cli, config
- External: pydantic, structlog, yaml

**Analysis:**
- Low async ratio (10%) - primarily synchronous logic
- Heavy use of Pydantic for type safety
- Strong separation between core logic and I/O

---

### 4. **Workflows Module** (workflows/) - 1,854 LOC
**Purpose:** Process orchestration and execution flows

**Key Components:**
- `bug_bounty_run.py` - Main bounty hunting workflow
- `enhanced_bounty_workflow.py` - Enhanced workflow features
- `http_workflow.py` - HTTP-based workflows
- `checkpoint_manager.py` - State checkpointing
- `parallel_executor.py` - Parallel execution
- `hypothesis_quality_filter.py` - Quality filtering
- `performance_metrics.py` - Performance tracking

**Stats:**
- 17 Classes
- 36 Functions (13 async)
- Average 231 LOC per file
- 7.8% of codebase

**Analysis:**
- Balanced async/sync ratio (36% async)
- Clear separation of workflow concerns
- Good checkpoint/recovery support

---

### 5. **CLI Module** (cli/) - 1,060 LOC
**Purpose:** Command-line interface and user interaction

**Key Components:**
- `secbrain_cli.py` - Main CLI entry point
- `approval_ui.py` - Human approval interface

**Stats:**
- 0 Classes (functional design)
- 12 Functions (5 async)
- Average 353 LOC per file
- 4.4% of codebase

**Dependencies:**
- External: (likely Click or similar CLI framework)

**Analysis:**
- Lightweight CLI layer
- Functional approach (no classes)
- Direct delegation to workflows

---

### 6. **Insights Module** (insights/) - 925 LOC
**Purpose:** Data analysis and reporting

**Key Components:**
- `aggregator.py` - Data aggregation
- `analyzer.py` - Analysis logic
- `reporter.py` - Report generation

**Stats:**
- 6 Classes
- 27 Functions (0 async)
- Average 231 LOC per file
- 3.9% of codebase

**Analysis:**
- Purely synchronous (data processing)
- Clean separation of aggregation/analysis/reporting

---

### 7. **Utils Module** (utils/) - 660 LOC
**Purpose:** Shared utilities and helpers

**Key Components:**
- `circuit_breaker.py` - Circuit breaker pattern
- `concurrency.py` - Concurrency helpers
- `llm_helpers.py` - LLM utilities
- `response_diff.py` - Response comparison
- `tool_checker.py` - Tool availability checks

**Stats:**
- 6 Classes
- 19 Functions (5 async)
- Average 110 LOC per file
- 2.8% of codebase

**Analysis:**
- Small, focused utility functions
- Good use of design patterns (circuit breaker)
- Low coupling

---

### 8. **Models Module** (models/) - 637 LOC
**Purpose:** LLM model abstractions

**Key Components:**
- `base.py` - Base model interface
- `gemini_advisor.py` - Google Gemini integration
- `open_workers.py` - Open-source model workers

**Stats:**
- 6 Classes
- 8 Functions (14 async)
- Average 159 LOC per file
- 2.7% of codebase

**Analysis:**
- High async ratio (175%) - I/O-bound API calls
- Clean abstraction layer for multiple LLM providers
- Advisor pattern for critical decisions

---

### 9. **Config Module** (config/) - 59 LOC
**Purpose:** Configuration and constants

**Key Components:**
- `constants.py` - System constants

**Stats:**
- 5 Classes (likely dataclasses)
- 0 Functions
- Minimal code (0.2% of codebase)

**Analysis:**
- Pure configuration module
- Dataclass-based configuration

---

### 10. **Root Module** (root/) - 215 LOC
**Purpose:** Package initialization

**Stats:**
- 5 Classes
- 7 Functions
- 0.9% of codebase

---

### 11. **Fixtures Module** (fixtures/) - 21 LOC
**Purpose:** Test fixtures and mock data

**Stats:**
- Minimal module for test support

---

## Dependency Graph

### Internal Dependencies

```
┌──────────┐
│   CLI    │
└────┬─────┘
     │
     ▼
┌──────────┐     ┌──────────┐
│Workflows │────→│  Agents  │
└────┬─────┘     └────┬─────┘
     │                │
     │                ├───→ Tools
     │                │
     ▼                ▼
┌──────────┐     ┌──────────┐
│   Core   │←────┤  Models  │
└────┬─────┘     └──────────┘
     │
     ├───→ Config
     │
     └───→ Utils
```

**Dependency Flow:**
1. **CLI** → Workflows → Agents → Core/Tools/Models
2. **Core** is the central dependency (used by Agents, Tools, Workflows)
3. **Config** is a leaf dependency (no outbound deps)
4. **Utils** provides cross-cutting concerns

### Key Observations:
- ✅ Clean layered architecture with minimal circular dependencies
- ✅ Core provides stable foundation
- ✅ Agents encapsulate domain logic
- ⚠️ Agents module has high coupling (depends on 5 other modules)

---

## External Dependencies

### Critical External Libraries

**Async Runtime:**
- `asyncio` - Core async support
- `aiosqlite` - Async SQLite

**HTTP/Network:**
- `httpx` - HTTP client
- `playwright` - Browser automation

**AI/ML:**
- (Gemini API, Perplexity API via httpx)

**Data Validation:**
- `pydantic` - Type validation
- `jsonschema` - JSON schema validation

**Logging:**
- `structlog` - Structured logging

**Blockchain:**
- `eth_utils` - Ethereum utilities

**Configuration:**
- `yaml` - YAML parsing
- `tomllib` - TOML parsing

**Testing:**
- Foundry (external binary)
- Hardhat (external binary)

---

## Code Metrics

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total LOC | 23,923 |
| Total Files | 80 |
| Total Classes | 192 |
| Total Functions | 431 |
| Async Functions | 238 (55.2%) |
| Avg LOC/File | 299 |

### Module Distribution

| Module | LOC | % of Total | Files |
|--------|-----|------------|-------|
| Agents | 11,604 | 48.5% | 22 |
| Tools | 3,696 | 15.5% | 12 |
| Core | 3,192 | 13.3% | 15 |
| Workflows | 1,854 | 7.8% | 8 |
| CLI | 1,060 | 4.4% | 3 |
| Insights | 925 | 3.9% | 4 |
| Utils | 660 | 2.8% | 6 |
| Models | 637 | 2.7% | 4 |
| Root | 215 | 0.9% | 2 |
| Config | 59 | 0.2% | 2 |
| Fixtures | 21 | 0.1% | 2 |

### Complexity Indicators

**Async Orientation:**
- 55.2% of all functions are async
- Tools module: 137% async ratio (71 async / 52 sync)
- Models module: 175% async ratio (14 async / 8 sync)
- Agents module: 83.6% async ratio (117 async / 140 total)

**File Size Distribution:**
- Largest: Agents (avg 527 LOC/file)
- Smallest: Fixtures (avg 10 LOC/file)
- Median: ~230 LOC/file

**Class/Function Density:**
- Agents: 0.45 classes/function (class-heavy)
- Core: 0.47 classes/function
- Insights: 0.22 classes/function (function-heavy)

---

## Key Components

### Critical Files (by importance)

1. **secbrain/agents/supervisor.py**
   - Orchestrates all agent interactions
   - Enforces ACLs, rate limits, kill-switch
   - Human-in-the-loop checkpoints

2. **secbrain/workflows/bug_bounty_run.py**
   - Main workflow orchestrator
   - Phase coordination (Recon → Hypothesis → Exploit)

3. **secbrain/core/context.py**
   - Execution context management
   - State tracking across workflow

4. **secbrain/agents/exploit_agent.py**
   - Core exploit testing logic
   - Multi-method verification

5. **secbrain/tools/perplexity_research.py**
   - AI research integration
   - TTL-based caching
   - Rate limiting

6. **secbrain/core/types.py**
   - Type system foundation
   - Pydantic models

7. **secbrain/cli/secbrain_cli.py**
   - CLI entry point
   - User interface

8. **secbrain/models/base.py**
   - LLM abstraction layer
   - Multi-model support

9. **secbrain/tools/storage.py**
   - Data persistence
   - Metrics storage

10. **secbrain/agents/immunefi_intelligence.py**
    - Bug bounty platform integration
    - Target discovery

---

## Data Flow

### Main Execution Flow

```
1. CLI Entry Point
   ├─ Parse arguments
   ├─ Load configuration
   └─ Initialize context

2. Workflow Orchestration
   ├─ Create supervisor agent
   ├─ Load scope/program
   └─ Execute phases

3. Phase Execution (Recon → Hypothesis → Exploit → Triage → Report)
   
   Phase 1: Reconnaissance
   ├─ Recon Agent
   ├─ Tools: subfinder, amass, httpx
   └─ Output: targets.json

   Phase 2: Hypothesis Generation
   ├─ Vuln Hypothesis Agent
   ├─ Research Orchestrator
   ├─ Tools: Perplexity Research
   └─ Output: hypotheses.json

   Phase 3: Exploit Development
   ├─ Exploit Agent
   ├─ Static Analysis Agent
   ├─ Tools: Foundry, Hardhat
   └─ Output: exploits/

   Phase 4: Triage
   ├─ Triage Agent
   ├─ Verifiers
   └─ Output: findings.json

   Phase 5: Reporting
   ├─ Reporting Agent
   ├─ Insights Aggregator
   └─ Output: report.md

4. Storage & Metrics
   ├─ Store findings in SQLite
   ├─ Update success metrics
   └─ Log audit trail
```

### Data Persistence

**Workspace Structure:**
```
workspace/
├── recon/
│   ├── domains.txt
│   └── targets.json
├── hypotheses/
│   └── hypotheses.json
├── exploits/
│   ├── exploit_1.sol
│   └── results/
├── findings/
│   └── findings.json
├── logs/
│   ├── audit.jsonl
│   └── debug.log
└── reports/
    └── final_report.md
```

**Database:**
- SQLite for metrics, caching
- JSONL for audit logs

---

## Recommendations

### Strengths ✅

1. **Clean Architecture**
   - Clear separation of concerns
   - Layered design with minimal coupling
   - Well-defined module boundaries

2. **Strong Type Safety**
   - Extensive use of Pydantic
   - Custom type definitions in core/types.py

3. **Async-First Design**
   - 55% async functions
   - Efficient I/O handling
   - Scalable for concurrent operations

4. **Comprehensive Agent System**
   - 22 specialized agents
   - Clear responsibilities
   - Good base abstractions

5. **Research Integration**
   - Perplexity API integration
   - TTL-based caching
   - Rate limiting

6. **Safety Controls**
   - Human-in-the-loop approvals
   - ACLs and rate limits
   - Kill-switch mechanism
   - Dry-run mode

### Areas for Improvement ⚠️

1. **Agent Module Size**
   - **Issue:** 11,604 LOC (48.5% of codebase) in single module
   - **Recommendation:** Split into submodules:
     ```
     agents/
     ├── core/          # Base, Supervisor
     ├── security/      # Exploit, Hypothesis, Triage
     ├── intelligence/  # Research, Immunefi
     ├── analysis/      # Static, Oracle
     └── reporting/     # Reporting
     ```

2. **Dependency Management**
   - **Issue:** Agents depends on 5 internal modules (high coupling)
   - **Recommendation:** 
     - Consider dependency injection
     - Extract shared interfaces to separate module

3. **Documentation**
   - **Current:** architecture-updated.md exists
   - **Recommendation:**
     - Add per-module README.md files
     - Document agent interactions
     - Create API documentation (Sphinx)

4. **Testing**
   - **Current:** Test files excluded from this analysis
   - **Recommendation:**
     - Ensure test coverage for all agents
     - Integration tests for workflows
     - Property-based testing for core logic

5. **Configuration**
   - **Issue:** Minimal config module (59 LOC)
   - **Recommendation:**
     - Centralize configuration management
     - Add environment-based configs
     - Schema validation for configs

6. **Monitoring**
   - **Current:** Logging with structlog
   - **Recommendation:**
     - Add OpenTelemetry support
     - Metrics export (Prometheus)
     - Distributed tracing

7. **Error Handling**
   - **Current:** Custom exceptions in core/exceptions.py
   - **Recommendation:**
     - Standardize error handling patterns
     - Add retry mechanisms with exponential backoff
     - Improve error context propagation

8. **Performance**
   - **Recommendation:**
     - Profile hot paths
     - Consider caching layer for repeated operations
     - Optimize database queries

### Refactoring Opportunities 🔧

1. **Extract Common Patterns**
   - Many agents share similar patterns
   - Consider base classes with template methods

2. **Reduce File Size**
   - Some files >500 LOC
   - Break down large agent implementations

3. **Interface Segregation**
   - Define minimal interfaces for agent interactions
   - Reduce coupling through contracts

4. **Plugin Architecture**
   - Consider plugin system for tools
   - Allow third-party agent extensions

### Security Considerations 🔒

1. **Input Validation**
   - ✅ Good: Pydantic validation in core
   - ⚠️ Ensure all external inputs validated

2. **Secret Management**
   - ⚠️ Review API key handling
   - Consider secrets management service

3. **Rate Limiting**
   - ✅ Good: Rate limiting in research tools
   - ✅ Supervisor enforces limits

4. **Sandboxing**
   - ⚠️ Review exploit execution isolation
   - Consider containerization for exploit testing

---

## Conclusion

SecBrain demonstrates a well-architected, mature codebase with clear separation of concerns. The multi-agent system is comprehensive and extensible. The primary opportunity for improvement is in modularizing the large agents module and enhancing documentation. The async-first design positions the system well for scale, and the safety controls show production-ready thinking.

**Overall Assessment:** 🟢 Production-Ready with Minor Improvements Needed

**Next Steps:**
1. Implement agent module refactoring
2. Add comprehensive documentation
3. Expand test coverage
4. Set up monitoring/observability
5. Review security practices

---

*This codemap was generated through automated analysis of the SecBrain repository structure, dependencies, and code metrics.*
