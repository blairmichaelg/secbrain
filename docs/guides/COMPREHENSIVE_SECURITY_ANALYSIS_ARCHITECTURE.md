# Comprehensive Security Analysis Workflow Architecture

## Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER INPUT (workflow_dispatch)                   │
│  • target_repo: Repository URL                                      │
│  • target_type: python | smart-contract | mixed                     │
│  • analysis_depth: quick | standard | deep                          │
│  • enable_ai_analysis: true | false                                 │
│  • enable_fuzzing: true | false                                     │
│  • immunefi_program: Optional program name                          │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: Setup & Reconnaissance                   │
│                         (setup-and-recon)                            │
│                                                                      │
│  1. Clone target repository                                         │
│  2. Detect project characteristics:                                 │
│     • Solidity files (.sol)                                         │
│     • Python files (.py)                                            │
│     • Foundry (foundry.toml)                                        │
│     • Hardhat (hardhat.config.*)                                    │
│  3. Estimate complexity (low/medium/high)                           │
│  4. Upload repository as artifact                                   │
│                                                                      │
│  Outputs: has_solidity, has_python, has_foundry, complexity         │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
        ┌───────────────────────────┴───────────────────────────┐
        │                                                        │
┌───────▼────────┐  ┌────────────────┐  ┌────────────────────┐ │
│ PHASE 2: STATIC ANALYSIS (Parallel)                          │ │
└──────────────────────────────────────────────────────────────┘ │
        │                        │                      │         │
┌───────▼────────┐  ┌────────────▼────┐  ┌────────────▼───────┐│
│ Python Static  │  │ Solidity Static │  │ Mythril (Deep)     ││
│   Analysis     │  │    Analysis     │  │ Symbolic Execution ││
│                │  │                 │  │                    ││
│ • Bandit       │  │ • Solhint       │  │ • Deep mode only   ││
│ • Safety       │  │ • Slither       │  │ • Contract-level   ││
│ • pip-audit    │  │ • Build checks  │  │ • 10 files max     ││
│ • Semgrep      │  │                 │  │                    ││
│                │  │                 │  │                    ││
│ If: has_python │  │ If: has_solidity│  │ If: depth=deep     ││
└────────┬───────┘  └────────┬────────┘  └─────────┬──────────┘│
         │                   │                      │           │
         └───────────────────┴──────────────────────┘           │
                             ↓                                  │
        ┌────────────────────────────────────────────┐          │
        │ PHASE 3: DYNAMIC ANALYSIS (Parallel)       │          │
        └────────────────────────────────────────────┘          │
                             │                                  │
          ┌──────────────────┴──────────────────┐              │
          │                                     │              │
  ┌───────▼────────┐              ┌─────────────▼────────┐    │
  │ Foundry        │              │ Echidna              │    │
  │ Fuzzing        │              │ Property Fuzzing     │    │
  │                │              │                      │    │
  │ • 256 (quick)  │              │ • Deep mode only     │    │
  │ • 10K (std)    │              │ • Property tests     │    │
  │ • 50K (deep)   │              │ • 10K test limit     │    │
  │                │              │                      │    │
  │ If: fuzzing +  │              │ If: fuzzing +        │    │
  │   has_foundry  │              │   depth=deep +       │    │
  │                │              │   has_solidity       │    │
  └───────┬────────┘              └─────────┬────────────┘    │
          │                                 │                 │
          └─────────────────┬───────────────┘                 │
                            ↓                                 │
        ┌─────────────────────────────────────────┐           │
        │ PHASE 4: AI ANALYSIS (Parallel)         │           │
        └─────────────────────────────────────────┘           │
                            │                                 │
      ┌─────────────────────┼─────────────────────┐          │
      │                     │                     │          │
┌─────▼──────┐  ┌───────────▼────────┐  ┌────────▼────────┐ │
│ AI Engineer│  │ Security           │  │ SecBrain        │ │
│ Analysis   │  │ Intelligence       │  │ Multi-Agent     │ │
│            │  │                    │  │                 │ │
│ • Codebase │  │ • CVE gathering    │  │ • Recon agent   │ │
│   patterns │  │ • Advisory intel   │  │ • Hypothesis    │ │
│ • Metrics  │  │ • DeFi exploits    │  │ • Triage        │ │
│            │  │                    │  │                 │ │
│ If: ai=true│  │ If: ai=true        │  │ If: ai=true +   │ │
│            │  │                    │  │   depth≥std     │ │
└─────┬──────┘  └───────────┬────────┘  └────────┬────────┘ │
      │                     │                     │          │
      └─────────────────────┴─────────────────────┘          │
                            ↓                                │
              ┌─────────────────────────┐                    │
              │ Generate Recommendations│                    │
              │                         │                    │
              │ • Context-aware         │                    │
              │ • Priority-based        │                    │
              │ • Actionable steps      │                    │
              └─────────────┬───────────┘                    │
                            ↓                                │
        ┌─────────────────────────────────────────┐          │
        │ PHASE 5: AGGREGATION & REPORTING        │          │
        └─────────────────────────────────────────┘          │
                            │                                │
              ┌─────────────▼───────────┐                    │
              │ Aggregate All Findings  │                    │
              │                         │                    │
              │ • Download artifacts    │                    │
              │ • Parse JSON results    │                    │
              │ • Count findings        │                    │
              │ • Generate summary      │                    │
              │ • Create markdown report│                    │
              └─────────────┬───────────┘                    │
                            ↓                                │
              ┌─────────────▼───────────┐                    │
              │ Create GitHub Issue     │                    │
              │                         │                    │
              │ • Auto-create issue     │                    │
              │ • Link artifacts        │                    │
              │ • Add recommendations   │                    │
              │ • Apply labels          │                    │
              └─────────────────────────┘                    │
                                                             │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           OUTPUTS                                    │
│                                                                      │
│  📦 Artifacts (Download from Actions):                              │
│  • comprehensive-analysis-report (90 days)                          │
│  • python-static-analysis (30 days)                                 │
│  • solidity-static-analysis (30 days)                               │
│  • mythril-analysis (30 days, deep only)                            │
│  • foundry-fuzzing (30 days)                                        │
│  • echidna-fuzzing (30 days, deep only)                             │
│  • ai-engineer-analysis (30 days)                                   │
│  • security-intelligence (30 days)                                  │
│  • recommendations (30 days)                                        │
│  • secbrain-agents (90 days)                                        │
│                                                                      │
│  📋 GitHub Issue:                                                   │
│  • Executive summary with all findings                              │
│  • Links to artifacts                                               │
│  • Prioritized recommendations                                      │
│  • Labels: security-analysis, automated                             │
└─────────────────────────────────────────────────────────────────────┘
```

## Job Dependency Graph

```
setup-and-recon
    ↓
    ├──→ python-static-analysis ────┐
    ├──→ solidity-static-analysis ──┼──→ aggregate-findings ──→ create-issue-report
    ├──→ mythril-analysis ──────────┤
    ├──→ foundry-fuzzing ───────────┤
    ├──→ echidna-fuzzing ───────────┤
    ├──→ ai-engineer-analysis ──────┼──→ generate-recommendations ──→ (feeds into aggregation)
    ├──→ security-intelligence ─────┘
    └──→ secbrain-agents ───────────┘
```

## Conditional Execution Matrix

| Job | Quick | Standard | Deep | Python | Smart Contract | Mixed |
|-----|-------|----------|------|--------|----------------|-------|
| setup-and-recon | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| python-static-analysis | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| solidity-static-analysis | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| mythril-analysis | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| foundry-fuzzing | 256 | 10K | 50K | ❌ | ✅¹ | ✅¹ |
| echidna-fuzzing | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| ai-engineer-analysis | ❌² | ✅ | ✅ | ✅ | ✅ | ✅ |
| security-intelligence | ❌² | ✅ | ✅ | ✅ | ✅ | ✅ |
| generate-recommendations | ❌² | ✅ | ✅ | ✅ | ✅ | ✅ |
| secbrain-agents | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| aggregate-findings | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| create-issue-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ Requires `has_foundry=true`  
² Unless `enable_ai_analysis=true`

## Timeline Estimates

### Quick Mode (5-15 minutes)
```
0:00 - Setup & Recon (2-3 min)
0:03 - Static Analysis (parallel, 3-5 min)
0:08 - Aggregation (1-2 min)
0:10 - Reporting (1 min)
Total: ~10 minutes
```

### Standard Mode (30-60 minutes)
```
0:00 - Setup & Recon (3-5 min)
0:05 - Static Analysis (parallel, 5-10 min)
0:15 - Fuzzing (parallel, 15-20 min)
0:35 - AI Analysis (parallel, 10-15 min)
0:50 - Aggregation (2-3 min)
0:53 - Reporting (2 min)
Total: ~55 minutes
```

### Deep Mode (2-4 hours)
```
0:00 - Setup & Recon (5 min)
0:05 - Static Analysis (parallel, 10-15 min)
0:20 - Mythril (parallel, 45-60 min)
1:20 - Foundry Fuzzing (50K runs, 30-45 min)
2:05 - Echidna (parallel, 60-90 min)
3:35 - AI Analysis (parallel, 15-20 min)
3:55 - Aggregation (3-5 min)
4:00 - Reporting (2 min)
Total: ~4 hours
```

## Resource Usage

### Compute
- **Quick:** 1 runner × 15 min = 15 runner-minutes
- **Standard:** 5 runners × 15 min avg = 75 runner-minutes
- **Deep:** 8 runners × 30 min avg = 240 runner-minutes

### Storage
- **Artifacts:** 50-500 MB per run
- **Retention:** 30-90 days
- **Monthly:** ~5-50 GB (depends on frequency)

### API Calls
- **Perplexity:** 5-20 requests (if AI enabled)
- **Google:** 10-30 requests (if AI enabled)
- **GitHub:** 50-100 API calls

## Security Considerations

1. **Secrets Management:**
   - API keys stored in GitHub Secrets
   - Never logged or exposed in artifacts
   - Scoped to minimum required permissions

2. **Target Isolation:**
   - Cloned to temporary directory
   - No write access to SecBrain repo
   - Cleaned up after analysis

3. **Artifact Security:**
   - Read-only access via artifacts
   - Time-limited retention
   - No sensitive data included

4. **Rate Limiting:**
   - Built into tools (Semgrep, Slither)
   - API clients respect limits
   - Parallel jobs don't exceed quotas

## Extensibility Points

### Adding New Static Analysis Tools

```yaml
custom-static-analysis:
  name: 🔧 Custom Static Tool
  runs-on: ubuntu-latest
  needs: setup-and-recon
  if: conditions
  timeout-minutes: 20
  steps:
    - uses: actions/checkout@v6
    - uses: actions/download-artifact@v6
      with:
        name: target-repository
    - name: Run tool
      run: |
        custom-tool analyze
    - uses: actions/upload-artifact@v6
      with:
        name: custom-results
```

### Adding New AI Agents

Integrate with `secbrain-agents` job or create parallel job following the same pattern.

### Custom Reporting

Extend `aggregate-findings` or add post-processing job that depends on it.

## Performance Optimization Tips

1. **Parallel Execution:**
   - Independent jobs run simultaneously
   - Reduces total wall-clock time by 60-80%

2. **Conditional Skipping:**
   - Jobs skip based on project type
   - Saves 30-50% compute time

3. **Artifact Caching:**
   - Target repo cached for downstream jobs
   - Reduces clone time for parallel jobs

4. **Timeout Protection:**
   - Each job has timeout limit
   - Prevents runaway processes
   - Ensures predictable runtime

5. **Smart Depth Selection:**
   - Quick for rapid iteration
   - Standard for CI/CD
   - Deep for critical audits
