# SecBrain Codemap Analysis Index

This index provides quick navigation to the comprehensive codemap analysis of the SecBrain repository.

## Quick Navigation

### Main Analysis Documents
1. **[CODEMAP_ANALYSIS.md](../CODEMAP_ANALYSIS.md)** - Comprehensive text-based analysis
   - Module breakdown and statistics
   - Dependency analysis
   - Code metrics
   - Recommendations

2. **[CODEMAP_VISUAL.md](CODEMAP_VISUAL.md)** - Visual diagrams and charts
   - Mermaid diagrams
   - Architecture visualizations
   - Data flow diagrams

### Related Documentation
- [Architecture](../secbrain/docs/architecture-updated.md) - Original architecture document
- [Workflows](../secbrain/docs/workflows.md) - Workflow details
- [Operations Guide](../secbrain/docs/ops.md) - How to use SecBrain

---

## What is This Codemap?

This codemap provides a comprehensive analysis of the SecBrain codebase, including:

✅ **Complete module inventory** - All 80 Python files catalogued  
✅ **Dependency mapping** - Internal and external dependencies  
✅ **Code metrics** - LOC, complexity, async/sync ratios  
✅ **Architecture visualization** - Mermaid diagrams of structure  
✅ **Recommendations** - Actionable improvement suggestions  

---

## Key Findings

### Codebase Statistics
- **Total LOC:** 23,923 lines
- **Total Files:** 80 Python modules
- **Total Classes:** 192
- **Total Functions:** 431 (55% async)

### Module Distribution
| Module | LOC | % of Total |
|--------|-----|-----------|
| Agents | 11,604 | 48.5% |
| Tools | 3,696 | 15.5% |
| Core | 3,192 | 13.3% |
| Others | 8,431 | 35.2% |

### Architecture Pattern
**Layered Architecture** with clear separation:
```
CLI → Workflows → Agents → Core/Tools/Models
```

---

## Quick Reference: Module Purposes

| Module | Purpose | Key Files |
|--------|---------|-----------|
| **agents/** | Security intelligence and testing | supervisor.py, exploit_agent.py, vuln_hypothesis_agent.py |
| **tools/** | External integrations | perplexity_research.py, immunefi_client.py, storage.py |
| **core/** | Foundational types and logic | context.py, types.py, validation.py |
| **workflows/** | Process orchestration | bug_bounty_run.py, enhanced_bounty_workflow.py |
| **cli/** | User interface | secbrain_cli.py, approval_ui.py |
| **models/** | LLM abstractions | base.py, gemini_advisor.py |
| **utils/** | Shared utilities | circuit_breaker.py, llm_helpers.py |
| **insights/** | Analytics and reporting | aggregator.py, analyzer.py, reporter.py |
| **config/** | Configuration | constants.py |

---

## Navigation Guide

### For New Contributors
Start with:
1. [CODEMAP_VISUAL.md](CODEMAP_VISUAL.md) - Visual overview
2. [Architecture](../secbrain/docs/architecture-updated.md) - System design
3. [CODEMAP_ANALYSIS.md](../CODEMAP_ANALYSIS.md) - Detailed breakdown

### For Maintainers
Focus on:
1. [Recommendations Section](../CODEMAP_ANALYSIS.md#recommendations) - Improvement suggestions
2. [Dependency Graph](../CODEMAP_ANALYSIS.md#dependency-graph) - Coupling analysis
3. [Code Metrics](../CODEMAP_ANALYSIS.md#code-metrics) - Complexity indicators

### For Security Researchers
Check out:
1. [Key Components](../CODEMAP_ANALYSIS.md#key-components) - Critical files
2. [Data Flow](../CODEMAP_ANALYSIS.md#data-flow) - Execution paths
3. [Security Considerations](../CODEMAP_ANALYSIS.md#security-considerations) - Security analysis

---

## How to Use This Codemap

### Understanding the Codebase
The codemap helps you quickly understand:
- Where specific functionality lives
- How modules depend on each other
- Which files are most critical
- Where to add new features

### Making Changes
Before modifying code:
1. Check the dependency graph to understand impact
2. Review the module's purpose and key files
3. Consider the recommendations for that area
4. Verify changes don't create circular dependencies

### Code Review
When reviewing PRs:
1. Check if changes align with module responsibilities
2. Verify dependencies aren't increasing unnecessarily
3. Ensure file size stays reasonable
4. Confirm async patterns are followed correctly

---

## Visualizations Included

### Dependency Diagrams
- Module dependency graph
- Agent ecosystem map
- Tool integration map

### Flow Diagrams
- Workflow state machine
- Data flow architecture
- Security control flow
- Component interaction sequence

### Metrics Charts
- Module size distribution (pie chart)
- Async vs sync functions
- File size distribution
- Agent specialization tree

---

## Maintenance

This codemap should be updated when:
- New modules are added
- Major refactoring occurs
- Architecture patterns change
- Significant new features are introduced

**Regeneration Command:**
```bash
# Run the analysis scripts from the codemap generation
python /tmp/analyze_modules.py > module_analysis.json
python /tmp/complexity_analysis.py > complexity_report.txt
```

---

## Questions?

- 🐛 **Found an issue?** Open an issue on GitHub
- 💡 **Have a suggestion?** Submit a PR with updates
- 📖 **Need more details?** Check the full [CODEMAP_ANALYSIS.md](../CODEMAP_ANALYSIS.md)

---

*Generated: 2025-12-25*  
*Version: 1.0*  
*Repository: blairmichaelg/secbrain*
