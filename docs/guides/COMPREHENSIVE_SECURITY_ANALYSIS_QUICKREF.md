# 🔒 Comprehensive Security Analysis - Quick Reference

## One-Line Commands

### Quick Scan (5-15 min)
```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/owner/repo \
  -f analysis_depth=quick \
  -f enable_ai_analysis=false \
  -f enable_fuzzing=false
```

### Standard Analysis (30-60 min) - RECOMMENDED
```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/owner/repo \
  -f target_type=mixed \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true
```

### Deep Audit (2-4 hours)
```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/owner/repo \
  -f target_type=smart-contract \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true \
  -f immunefi_program=protocol-name
```

## Target Types

| Type | Use When |
|------|----------|
| `python` | Python-only projects |
| `smart-contract` | Solidity/smart contract projects |
| `mixed` | Projects with both Python and Solidity |

## Analysis Depth

| Depth | Time | Tools | Fuzz Runs |
|-------|------|-------|-----------|
| `quick` | 5-15m | Static only | 256 |
| `standard` | 30-60m | Static + AI + Fuzzing | 10,000 |
| `deep` | 2-4h | All tools + Mythril + Echidna | 50,000 |

## Tools Included

### Python Security
- ✅ Bandit (SAST)
- ✅ Safety (Dependencies)
- ✅ pip-audit (Packages)
- ✅ Semgrep (Patterns)

### Solidity Security
- ✅ Slither (Static analysis)
- ✅ Solhint (Linting)
- ✅ Mythril (Symbolic - deep only)

### Fuzzing
- ✅ Foundry (Property-based)
- ✅ Echidna (Advanced - deep only)

### AI Analysis
- ✅ SecBrain agents
- ✅ AI engineer analysis
- ✅ Security intelligence
- ✅ Recommendations

## Output Artifacts

Download from Actions tab after completion:

1. `comprehensive-analysis-report` - Main report (90 days)
2. `python-static-analysis` - Python findings (30 days)
3. `solidity-static-analysis` - Solidity findings (30 days)
4. `foundry-fuzzing` - Fuzz results (30 days)
5. `ai-engineer-analysis` - AI insights (30 days)
6. `recommendations` - Actionable suggestions (30 days)
7. `secbrain-agents` - Multi-agent analysis (90 days)

Plus: GitHub issue auto-created with summary

## Required Secrets

Set in: Settings → Secrets and variables → Actions

```
PERPLEXITY_API_KEY    # For research (required for AI)
GOOGLE_API_KEY        # For Gemini (required for AI)
TOGETHER_API_KEY      # For workers (optional)
```

## Common Use Cases

### Pre-commit Check
```bash
# Quick scan before committing
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/you/your-repo \
  -f analysis_depth=quick
```

### PR Review
```bash
# Standard analysis for pull requests
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/you/your-repo \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true
```

### Weekly Audit
```bash
# Comprehensive weekly security check
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/you/your-repo \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true
```

### Pre-release Audit
```bash
# Deep analysis before major release
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/you/your-repo \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true
```

### Bug Bounty Research
```bash
# Analyze target with Immunefi context
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/protocol/contracts \
  -f target_type=smart-contract \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true \
  -f immunefi_program=protocol-name
```

## Tips

### 🚀 Performance
- Use `quick` for rapid iteration
- Use `standard` for CI/CD
- Use `deep` for releases/audits

### 💰 Cost Optimization
- Disable AI for non-critical scans
- Reduce fuzz runs for large test suites
- Use quick mode for frequent checks

### 🐛 Troubleshooting
- Check workflow logs in Actions tab
- Verify repository is public
- Confirm API keys are set
- Increase timeouts for large repos

## Example Workflow

```bash
# 1. Quick validation
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/target/repo \
  -f analysis_depth=quick

# 2. Review results in Actions tab
# 3. If clean, run standard analysis
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/target/repo \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true

# 4. Review findings in auto-created issue
# 5. Download artifacts for detailed analysis
# 6. Address findings and re-run
```

## Next Steps

- 📖 [Full Documentation](.github/workflows/COMPREHENSIVE_SECURITY_ANALYSIS_README.md)
- 🔧 [Customization Guide](.github/workflows/COMPREHENSIVE_SECURITY_ANALYSIS_README.md#customization)
- 🐛 [Troubleshooting](.github/workflows/COMPREHENSIVE_SECURITY_ANALYSIS_README.md#troubleshooting)
- 💡 [Best Practices](.github/workflows/COMPREHENSIVE_SECURITY_ANALYSIS_README.md#best-practices)
