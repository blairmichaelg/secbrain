# 🔒 Comprehensive Security Analysis Workflow

## Overview

The Comprehensive Security Analysis workflow is a production-ready, enterprise-grade security testing pipeline that orchestrates 12+ security tools with AI-powered analysis to provide deep insights into target repositories.

## Features

### ✅ Multi-Tool Coverage

**Python Security:**
- Bandit (SAST)
- Safety (Dependency vulnerabilities)
- pip-audit (Package vulnerabilities)
- Semgrep (Custom security rules)

**Solidity Security:**
- Slither (Static analysis)
- Solhint (Linting & best practices)
- Mythril (Symbolic execution - deep mode only)

**Fuzzing:**
- Foundry (Property-based fuzzing)
- Echidna (Advanced fuzzing - deep mode only)

**AI-Powered:**
- SecBrain multi-agent analysis
- AI engineer codebase analysis
- Security intelligence gathering
- Intelligent recommendations

### ⚡ Performance Optimizations

- **Parallel Execution:** Independent analysis jobs run simultaneously
- **Adaptive Depth:** Three analysis modes (quick/standard/deep)
- **Smart Detection:** Automatic project type detection
- **Timeout Protection:** Per-job timeouts prevent runaway processes
- **Artifact Retention:** 30-90 day retention based on artifact type

### 🎯 Smart Analysis Modes

| Mode | Duration | Tools | Use Case |
|------|----------|-------|----------|
| **Quick** | 5-15 min | Static analysis only, 256 fuzz runs | Pre-commit checks, rapid iteration |
| **Standard** | 30-60 min | Full static analysis, 10K fuzz runs, AI analysis | Pull requests, weekly scans |
| **Deep** | 2-4 hours | All tools, 50K fuzz runs, Mythril, Echidna | Release candidates, critical audits |

## Usage

### Prerequisites

1. **Repository Secrets** (Settings → Secrets and variables → Actions):
   ```bash
   PERPLEXITY_API_KEY    # For research capabilities
   GOOGLE_API_KEY        # For Gemini advisor model
   TOGETHER_API_KEY      # For worker models (optional)
   ```

2. **Permissions:** The workflow needs `issues: write` to create summary reports

### Running the Workflow

#### Method 1: GitHub UI

1. Navigate to **Actions** tab
2. Select **"🔒 Comprehensive Security Analysis"**
3. Click **"Run workflow"**
4. Fill in parameters:
   - **target_repo:** `https://github.com/owner/repo` (required)
   - **target_type:** `smart-contract`, `python`, or `mixed`
   - **analysis_depth:** `quick`, `standard`, or `deep`
   - **enable_ai_analysis:** Check for AI-powered insights
   - **enable_fuzzing:** Check to enable fuzzing tests
   - **immunefi_program:** Optional program name for context

#### Method 2: GitHub CLI

```bash
# Standard analysis of a smart contract project
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/aave/aave-v3-core \
  -f target_type=smart-contract \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true

# Quick Python security scan
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/psf/requests \
  -f target_type=python \
  -f analysis_depth=quick \
  -f enable_ai_analysis=false \
  -f enable_fuzzing=false

# Deep audit with Immunefi context
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/Uniswap/v4-core \
  -f target_type=smart-contract \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true \
  -f immunefi_program=uniswap
```

#### Method 3: API Call

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/blairmichaelg/secbrain/actions/workflows/comprehensive-security-analysis.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "target_repo": "https://github.com/example/target",
      "target_type": "mixed",
      "analysis_depth": "standard",
      "enable_ai_analysis": "true",
      "enable_fuzzing": "true"
    }
  }'
```

## Workflow Architecture

### Phase 1: Setup & Reconnaissance
```
setup-and-recon
├── Clone target repository
├── Detect project type (Solidity/Python/Mixed)
├── Identify frameworks (Foundry/Hardhat)
├── Estimate complexity
└── Upload target as artifact
```

### Phase 2: Static Analysis (Parallel)
```
python-static-analysis          solidity-static-analysis       mythril-analysis
├── Bandit                      ├── Solhint                    └── Symbolic execution
├── Safety                      ├── Slither                       (deep mode only)
├── pip-audit                   └── Build contracts
└── Semgrep
```

### Phase 3: Dynamic Analysis (Parallel)
```
foundry-fuzzing                 echidna-fuzzing
├── Build contracts             └── Property-based fuzzing
└── Fuzz tests                     (deep mode only)
   └── 256/10K/50K runs
      (quick/standard/deep)
```

### Phase 4: AI Analysis (Parallel)
```
ai-engineer-analysis    security-intelligence    secbrain-agents
├── Codebase analysis   ├── CVE gathering        ├── Recon agent
└── Context generation  └── Advisory intel       ├── Hypothesis agent
                                                 └── Multi-agent flow
         └────────────────┬──────────────────┘
                generate-recommendations
```

### Phase 5: Reporting
```
aggregate-findings
├── Collect all artifacts
├── Parse JSON results
├── Generate summary
└── Create markdown report
         │
         v
   create-issue-report
   └── Auto-create GitHub issue
```

## Outputs

### Artifacts (Download from Actions tab)

1. **target-repository** (7 days)
   - Cloned target for reference

2. **python-static-analysis** (30 days)
   - `bandit-results.json` - Security issues
   - `safety-results.json` - Dependency vulnerabilities
   - `pip-audit-results.json` - Package audit
   - `semgrep-results.json` - Pattern-based findings

3. **solidity-static-analysis** (30 days)
   - `slither-results.json` - Contract vulnerabilities
   - `solhint-results.json` - Code quality issues

4. **foundry-fuzzing** (30 days)
   - `foundry-fuzz-output.txt` - Fuzz test results

5. **mythril-analysis** (30 days, deep only)
   - `mythril-*.json` - Symbolic execution findings

6. **echidna-fuzzing** (30 days, deep only)
   - `echidna-output.txt` - Property test results

7. **ai-engineer-analysis** (30 days)
   - `ai-analysis.json` - AI-powered insights

8. **security-intelligence** (30 days)
   - `security-intel.json` - Threat intelligence

9. **recommendations** (30 days)
   - `recommendations.json` - Actionable suggestions

10. **secbrain-agents** (90 days)
    - SecBrain multi-agent analysis logs

11. **comprehensive-analysis-report** (90 days)
    - `REPORT.md` - Executive summary
    - `findings.json` - Aggregated JSON
    - `summary.json` - Quick stats

### GitHub Issue

A new issue is automatically created with:
- Executive summary
- Project characteristics
- Analysis coverage
- Links to all artifacts
- Prioritized recommendations
- Next steps

## Customization

### Adding Custom Tools

Add a new job to the workflow:

```yaml
custom-tool-analysis:
  name: 🔧 Custom Security Tool
  runs-on: ubuntu-latest
  needs: setup-and-recon
  timeout-minutes: 20
  
  steps:
    - name: Checkout SecBrain
      uses: actions/checkout@v6
    
    - name: Download target repository
      uses: actions/download-artifact@v6
      with:
        name: target-repository
        path: ${{ env.ANALYSIS_DIR }}/target
    
    - name: Install custom tool
      run: |
        # Installation commands
    
    - name: Run analysis
      run: |
        mkdir -p ${{ env.RESULTS_DIR }}
        cd ${{ env.ANALYSIS_DIR }}/target
        # Run your tool
        custom-tool analyze . > ${{ env.RESULTS_DIR }}/custom-results.json
    
    - name: Upload results
      uses: actions/upload-artifact@v6
      with:
        name: custom-tool-analysis
        path: ${{ env.RESULTS_DIR }}
        retention-days: 30
```

### Adjusting Timeouts

Modify the `timeout-minutes` for any job:

```yaml
solidity-static-analysis:
  timeout-minutes: 45  # Increase for large codebases
```

### Conditional Execution

Use `if` conditions to control job execution:

```yaml
expensive-analysis:
  if: |
    inputs.analysis_depth == 'deep' && 
    needs.setup-and-recon.outputs.project_complexity == 'high'
```

## Interpreting Results

### Severity Levels

**Critical/High:**
- Immediate attention required
- Potential security vulnerabilities
- May lead to loss of funds or data

**Medium:**
- Should be addressed soon
- Code quality or best practice violations
- May create attack surface

**Low/Informational:**
- Nice-to-have improvements
- Documentation suggestions
- Minor optimizations

### Common Findings

**Bandit:**
- `B101` - Assert used (not for production)
- `B201` - Flask debug mode
- `B301-B323` - Pickle, subprocess, crypto issues

**Slither:**
- Reentrancy vulnerabilities
- Unprotected selfdestruct
- Timestamp dependence
- Integer overflow/underflow (pre-0.8.0)

**Semgrep:**
- SQL injection patterns
- XSS vulnerabilities
- Insecure deserialization
- Hardcoded secrets

## Troubleshooting

### Common Issues

**"Failed to clone target repository"**
- Verify the URL is correct
- Ensure repository is public or add authentication
- Check network connectivity

**"No Solidity/Python files found"**
- Verify target_type matches repository contents
- Check if files are in subdirectories
- May need to adjust detection logic

**AI Analysis Failed**
- Verify API keys are set correctly
- Check API rate limits
- May need to reduce parallel requests

**Fuzzing Timeout**
- Reduce fuzz runs for large test suites
- Increase timeout-minutes
- Consider breaking into multiple jobs

### Debug Mode

Enable debug logging by adding to workflow:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

## Performance Tips

### For Large Repositories

1. Use `quick` mode initially to validate setup
2. Increase timeouts for analysis jobs
3. Consider analyzing specific directories
4. Use incremental analysis when possible

### For CI/CD Integration

1. Use `quick` mode for PR checks
2. Schedule `standard` mode daily
3. Run `deep` mode weekly or before releases
4. Cache dependencies where possible

### Cost Optimization

1. Disable AI analysis for non-critical scans
2. Use `quick` mode for frequent runs
3. Adjust artifact retention periods
4. Run full analysis only on main branch

## Best Practices

1. **Start Small:** Test with `quick` mode on a small repo first
2. **Iterate:** Review findings and adjust depth/tools as needed
3. **Automate:** Schedule regular scans (weekly/monthly)
4. **Triage:** Create a process for reviewing and addressing findings
5. **Document:** Keep notes on false positives and exceptions
6. **Update:** Regularly update tool versions for latest checks
7. **Combine:** Use with other security practices (code review, audits)

## Examples

### Example 1: Quick Python Library Scan

```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/pallets/flask \
  -f target_type=python \
  -f analysis_depth=quick \
  -f enable_ai_analysis=false \
  -f enable_fuzzing=false
```

**Expected Duration:** 5-10 minutes  
**Tools Used:** Bandit, Safety, pip-audit, Semgrep  
**Artifacts:** Python static analysis results

### Example 2: Standard DeFi Protocol Analysis

```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/compound-finance/compound-protocol \
  -f target_type=smart-contract \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true \
  -f immunefi_program=compound
```

**Expected Duration:** 45-60 minutes  
**Tools Used:** All static analysis, Foundry fuzzing, AI analysis  
**Artifacts:** Full suite of analysis results

### Example 3: Deep Audit for Critical Release

```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/makerdao/dss \
  -f target_type=smart-contract \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true \
  -f immunefi_program=makerdao
```

**Expected Duration:** 2-4 hours  
**Tools Used:** Everything including Mythril and Echidna  
**Artifacts:** Comprehensive analysis with all tools

## Integration Examples

### Scheduled Weekly Scans

Add to your repository's workflow:

```yaml
name: Weekly Security Audit

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM
  workflow_dispatch:

jobs:
  trigger-analysis:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger comprehensive analysis
        uses: actions/github-script@v8
        with:
          github-token: ${{ secrets.PAT_TOKEN }}
          script: |
            await github.rest.actions.createWorkflowDispatch({
              owner: 'blairmichaelg',
              repo: 'secbrain',
              workflow_id: 'comprehensive-security-analysis.yml',
              ref: 'main',
              inputs: {
                target_repo: context.payload.repository.html_url,
                target_type: 'mixed',
                analysis_depth: 'standard',
                enable_ai_analysis: 'true',
                enable_fuzzing: 'true'
              }
            });
```

### PR Comment Integration

Use GitHub Actions to comment on PRs with analysis results:

```yaml
- name: Comment on PR
  uses: actions/github-script@v8
  with:
    script: |
      const fs = require('fs');
      const report = fs.readFileSync('report/REPORT.md', 'utf8');
      
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: report
      });
```

## Version History

**v1.0** (2025-12-25)
- Initial release
- 12+ security tools
- 3 analysis modes
- AI integration
- Parallel execution
- Automated reporting

## Support

For issues or questions:
1. Check troubleshooting section
2. Review workflow logs in Actions tab
3. Open an issue in the SecBrain repository
4. Consult SecBrain documentation

## License

This workflow is part of the SecBrain project and follows the same license.
