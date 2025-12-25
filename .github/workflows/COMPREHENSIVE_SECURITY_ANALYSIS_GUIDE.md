# 🔒 Comprehensive Security Analysis Workflow Guide

## Overview

The **Comprehensive Security Analysis** workflow is SecBrain's flagship automated security testing framework that orchestrates 13+ industry-standard security tools along with AI-powered analysis to provide complete security coverage for any repository.

## 🎯 Key Features

### ✅ Comprehensive Coverage
- **13+ security tools** orchestrated in parallel
- **Multi-phase analysis**: Static → Dynamic → Symbolic → AI
- **Smart detection** of project type and complexity
- **Adaptive execution** based on analysis depth
- **Secret detection** with detect-secrets

### ⚡ Optimized Performance
- **Parallel job execution** for faster results
- **Conditional execution** based on project type
- **Timeout protection** for long-running tasks
- **Artifact caching** for faster reruns

### 🤖 AI-Powered Insights
- **Multi-agent analysis** with SecBrain
- **Research integration** for emerging vulnerabilities
- **Intelligent recommendations** based on findings
- **Immunefi platform intelligence** (optional)

### 📊 Actionable Reporting
- **Aggregated JSON** with all findings
- **Markdown report** with executive summary
- **GitHub Issue** auto-created with results
- **90-day artifact** retention

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have the required GitHub secrets configured:

```bash
# Go to: Repository → Settings → Secrets and variables → Actions

# Add these secrets:
PERPLEXITY_API_KEY   # For research capabilities (optional, for AI analysis)
GOOGLE_API_KEY       # For advisor model (optional, for AI analysis)
TOGETHER_API_KEY     # For worker model (optional, for AI analysis)
```

**Note:** The workflow works without API keys but AI-powered analysis will be limited.

### 2. Run via GitHub UI

1. Go to **Actions** tab in your repository
2. Select **"🔒 Comprehensive Security Analysis"**
3. Click **"Run workflow"**
4. Fill in the parameters:

| Parameter | Description | Options |
|-----------|-------------|---------|
| **target_repo** | Repository URL to analyze | Any GitHub repo URL |
| **target_type** | Type of project | `smart-contract`, `python`, `mixed` |
| **analysis_depth** | How thorough to analyze | `quick`, `standard`, `deep` |
| **enable_ai_analysis** | Enable AI-powered insights | `true` / `false` |
| **enable_fuzzing** | Enable fuzzing tests | `true` / `false` |
| **immunefi_program** | Immunefi program name | Optional |

5. Click **"Run workflow"**

### 3. Run via GitHub CLI

```bash
# Quick analysis
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/example/target \
  -f target_type=smart-contract \
  -f analysis_depth=quick \
  -f enable_ai_analysis=false \
  -f enable_fuzzing=false

# Standard analysis (recommended)
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/example/defi-protocol \
  -f target_type=smart-contract \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true

# Deep analysis with Immunefi intelligence
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/wormhole-foundation/wormhole \
  -f target_type=mixed \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true \
  -f immunefi_program=wormhole
```

## 📊 Analysis Depth Comparison

### Quick (5-15 minutes)
- ✅ Basic static analysis
- ✅ Linting and formatting checks
- ⏭️ No fuzzing
- ⏭️ No symbolic execution
- ⏭️ Limited AI analysis
- **Use case:** Rapid feedback, PR checks

**Fuzz runs:** 256

### Standard (30-60 minutes) ⭐ Recommended
- ✅ Full static analysis
- ✅ Standard fuzzing (1,000 runs)
- ✅ Complete AI analysis
- ⏭️ No Echidna
- ⏭️ No Mythril
- **Use case:** Regular security audits, bounty prep

**Fuzz runs:** 1,000

### Deep (2-4 hours)
- ✅ All tools enabled
- ✅ Extended fuzzing (10,000 runs)
- ✅ Echidna property testing
- ✅ Mythril symbolic execution
- ✅ Maximum AI insights
- **Use case:** Pre-deployment audits, critical systems

**Fuzz runs:** 10,000

## 🔧 Workflow Architecture

### Phase 1: Setup & Reconnaissance
```
🔍 Setup & Recon
├── Clone target repository
├── Detect project characteristics
│   ├── Solidity contracts?
│   ├── Python code?
│   ├── Foundry/Hardhat?
│   └── Calculate complexity
└── Cache repository for other jobs
```

### Phase 2: Static Analysis (Parallel)
```
🔐 Solidity Static Analysis    🐍 Python Static Analysis
├── Slither                     ├── Bandit
├── Solhint                     ├── Safety
└── Format checks               ├── pip-audit
                                └── Semgrep
```

### Phase 3: Dynamic Analysis (Conditional)
```
⚡ Foundry Fuzzing              🦇 Echidna (Deep mode only)
├── Property-based testing      └── Advanced invariant testing
├── Gas reporting               
└── Coverage analysis           
```

### Phase 4: Symbolic Execution (Deep mode)
```
🔮 Mythril
└── Symbolic execution on main contracts
```

### Phase 5: AI-Powered Analysis
```
🤖 SecBrain AI
├── Codebase analysis
├── Security intelligence gathering
├── AI-generated recommendations
└── Immunefi intelligence (optional)
```

### Phase 6: Aggregation & Reporting
```
📊 Aggregate & Report
├── Combine all findings
├── Generate unified JSON
├── Create markdown report
├── Auto-create GitHub issue
└── Upload artifacts
```

## 📦 Output Artifacts

After workflow completion, you'll get:

### 1. GitHub Issue
- Executive summary
- Key findings by severity
- Recommended actions
- Links to detailed artifacts

### 2. Workflow Artifacts (90-day retention)

| Artifact | Contents |
|----------|----------|
| `comprehensive-analysis-results` | Aggregated JSON + Markdown report |
| `static-analysis-solidity` | Slither, Solhint outputs |
| `static-analysis-python` | Bandit, Safety, Semgrep outputs |
| `dynamic-analysis-foundry` | Fuzzing results, gas reports |
| `dynamic-analysis-echidna` | Property testing results |
| `symbolic-execution-mythril` | Symbolic execution findings |
| `ai-analysis-secbrain` | AI insights and recommendations |

### 3. Aggregated JSON Structure
```json
{
  "analysis_metadata": {
    "target_repo": "...",
    "analysis_depth": "...",
    "timestamp": "...",
    "project_characteristics": {...}
  },
  "findings": {
    "static_analysis": {...},
    "dynamic_analysis": {...},
    "symbolic_execution": {...},
    "ai_insights": {...}
  },
  "summary": {
    "total_issues": 0,
    "critical_issues": 0,
    "high_issues": 0,
    "medium_issues": 0,
    "low_issues": 0
  }
}
```

## 🎨 Customization

### Add Custom Tools

To add a new security tool to the workflow:

1. Create a new job in the appropriate phase
2. Add tool installation steps
3. Run the tool and save results
4. Upload as artifact

**Example:**

```yaml
custom-tool-analysis:
  name: 🔧 Custom Tool
  runs-on: ubuntu-latest
  needs: setup-and-recon
  timeout-minutes: 20
  steps:
    - name: Restore target repository
      uses: actions/cache@v4
      with:
        path: ${{ env.TARGET_DIR }}
        key: target-repo-${{ github.run_id }}-${{ github.run_attempt }}

    - name: Install custom tool
      run: |
        pip install my-custom-security-tool

    - name: Run analysis
      run: |
        mkdir -p ${{ env.RESULTS_DIR }}/custom-tool
        cd ${{ env.TARGET_DIR }}
        my-tool analyze --output ${{ env.RESULTS_DIR }}/custom-tool/results.json

    - name: Upload results
      uses: actions/upload-artifact@v6
      with:
        name: custom-tool-results
        path: ${{ env.RESULTS_DIR }}/custom-tool/**/*
        retention-days: 90
```

### Adjust Timeouts

Modify timeout values based on your needs:

```yaml
timeout-minutes: ${{ inputs.analysis_depth == 'quick' && 15 || inputs.analysis_depth == 'standard' && 45 || 120 }}
```

### Custom Fuzz Runs

Adjust fuzzing intensity in the Foundry job:

```yaml
FUZZ_RUNS=256      # Quick
FUZZ_RUNS=1000     # Standard
FUZZ_RUNS=10000    # Deep
FUZZ_RUNS=50000    # Ultra-deep (custom)
```

## 🔒 Security Considerations

### API Keys
- Store all API keys in GitHub Secrets
- Never hardcode credentials in workflow files
- Use `env` context to pass secrets to jobs

### Target Repository Access
- Workflow clones the target repository
- Ensure you have permission to analyze the target
- Consider using personal access tokens for private repos

### Resource Limits
- Deep analysis can take 2-4 hours
- Be mindful of GitHub Actions minute quotas
- Use `quick` or `standard` for regular checks

## 🐛 Troubleshooting

### Common Issues

#### 1. Job Timeout
**Problem:** Job exceeds timeout limit

**Solution:**
- Use `quick` or `standard` depth
- Disable fuzzing for initial run
- Increase timeout in workflow file

#### 2. Tool Installation Fails
**Problem:** Security tool fails to install

**Solution:**
- Check tool compatibility with Ubuntu runner
- Update tool version in workflow
- Use Docker container for problematic tools

#### 3. No Artifacts Generated
**Problem:** Expected artifacts are missing

**Solution:**
- Check job logs for errors
- Ensure `continue-on-error: true` is set
- Verify artifact upload paths

#### 4. AI Analysis Fails
**Problem:** SecBrain AI analysis doesn't run

**Solution:**
- Verify API keys are set correctly
- Check API key permissions and quotas
- Review SecBrain installation logs

## 📊 Metrics & Tracking

### Workflow Metrics

Track these metrics over time:

- **Analysis Duration** - How long each depth takes
- **Issues Found** - Trending by severity
- **Tool Coverage** - Which tools find the most issues
- **False Positive Rate** - Quality of findings

### Integration with Metrics Dashboard

```bash
# After analysis, log to metrics
secbrain metrics log \
  --type analysis \
  --target ${{ inputs.target_repo }} \
  --depth ${{ inputs.analysis_depth }} \
  --issues-found $TOTAL_ISSUES
```

## 🔄 Best Practices

### 1. Regular Analysis
- Run `standard` analysis weekly on active projects
- Run `deep` analysis before major releases
- Run `quick` analysis on every PR

### 2. Incremental Improvement
- Track findings over time
- Set goals for reducing issue counts
- Focus on high-severity issues first

### 3. Integration with Development
- Add to CI/CD pipeline
- Gate deployments on analysis results
- Use findings to improve code quality

### 4. Team Collaboration
- Review generated issues as a team
- Assign remediation tasks
- Share learnings across projects

## 📚 Additional Resources

- [SecBrain Documentation](../../README.md)
- [Workflow Optimization Guide](../../WORKFLOW_OPTIMIZATION_GUIDE.md)
- [Bounty Workflows](./BOUNTY_WORKFLOWS_README.md)
- [Security Best Practices](../../docs/)

## 🤝 Contributing

Improvements to this workflow are welcome! Consider:

- Adding new security tools
- Improving result aggregation
- Enhancing AI analysis integration
- Better error handling
- Performance optimizations

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## 📝 Changelog

### v1.0 (2024)
- Initial release
- 12+ tool integration
- AI-powered analysis
- Multi-phase execution
- Adaptive depth configuration

---

*Built with ❤️ by the SecBrain team*
