# Example Comprehensive Security Analysis Configurations

This file contains example configurations for various use cases of the Comprehensive Security Analysis workflow.

## Example 1: Python Library Security Scan

**Use Case:** Regular security scanning of a Python library  
**Target:** Flask web framework  
**Duration:** ~10 minutes

```yaml
inputs:
  target_repo: https://github.com/pallets/flask
  target_type: python
  analysis_depth: standard
  enable_ai_analysis: true
  enable_fuzzing: false
  immunefi_program: ''
```

**Expected Results:**
- Python dependency vulnerabilities
- Code security issues (Bandit)
- Pattern-based vulnerabilities (Semgrep)
- AI-generated security recommendations

---

## Example 2: DeFi Protocol Analysis

**Use Case:** Security analysis of a DeFi protocol for bug bounty  
**Target:** Compound Finance  
**Duration:** ~60 minutes

```yaml
inputs:
  target_repo: https://github.com/compound-finance/compound-protocol
  target_type: smart-contract
  analysis_depth: standard
  enable_ai_analysis: true
  enable_fuzzing: true
  immunefi_program: compound
```

**Expected Results:**
- Slither static analysis findings
- Solhint code quality issues
- Foundry fuzz test results (10K runs)
- SecBrain multi-agent analysis
- Immunefi context integration

---

## Example 3: Pre-Release Deep Audit

**Use Case:** Comprehensive audit before major release  
**Target:** MakerDAO DSS  
**Duration:** ~3 hours

```yaml
inputs:
  target_repo: https://github.com/makerdao/dss
  target_type: smart-contract
  analysis_depth: deep
  enable_ai_analysis: true
  enable_fuzzing: true
  immunefi_program: makerdao
```

**Expected Results:**
- All static analysis tools
- Mythril symbolic execution
- Echidna property-based fuzzing (10K runs)
- Foundry fuzzing (50K runs)
- Full SecBrain agent analysis
- Comprehensive recommendations

---

## Example 4: Mixed Python/Solidity Project

**Use Case:** Full-stack DApp security analysis  
**Target:** Brownie framework  
**Duration:** ~45 minutes

```yaml
inputs:
  target_repo: https://github.com/eth-brownie/brownie
  target_type: mixed
  analysis_depth: standard
  enable_ai_analysis: true
  enable_fuzzing: true
  immunefi_program: ''
```

**Expected Results:**
- Python security analysis
- Solidity analysis (if contracts present)
- Both dependency and code security checks
- Integrated findings report

---

## Example 5: Quick CI/CD Integration

**Use Case:** Fast pre-commit security check  
**Target:** Your own repository  
**Duration:** ~5 minutes

```yaml
inputs:
  target_repo: https://github.com/you/your-repo
  target_type: mixed
  analysis_depth: quick
  enable_ai_analysis: false
  enable_fuzzing: false
  immunefi_program: ''
```

**Expected Results:**
- Basic static analysis
- Critical vulnerability detection
- Fast feedback for development

---

## Example 6: Uniswap V4 Core Analysis

**Use Case:** Advanced DEX protocol security analysis  
**Target:** Uniswap V4  
**Duration:** ~90 minutes

```yaml
inputs:
  target_repo: https://github.com/Uniswap/v4-core
  target_type: smart-contract
  analysis_depth: deep
  enable_ai_analysis: true
  enable_fuzzing: true
  immunefi_program: uniswap
```

**Expected Results:**
- Comprehensive static analysis
- Extensive fuzzing
- MEV vulnerability detection
- Oracle manipulation analysis
- SecBrain multi-agent insights

---

## Example 7: Aave V3 Security Review

**Use Case:** Lending protocol security analysis  
**Target:** Aave V3 Core  
**Duration:** ~75 minutes

```yaml
inputs:
  target_repo: https://github.com/aave/aave-v3-core
  target_type: smart-contract
  analysis_depth: deep
  enable_ai_analysis: true
  enable_fuzzing: true
  immunefi_program: aave
```

**Expected Results:**
- Flash loan vulnerability analysis
- Oracle security checks
- Access control review
- Economic attack vectors
- AI-powered insights

---

## Example 8: Chainlink Contracts Analysis

**Use Case:** Oracle infrastructure security  
**Target:** Chainlink contracts  
**Duration:** ~60 minutes

```yaml
inputs:
  target_repo: https://github.com/smartcontractkit/chainlink
  target_type: mixed
  analysis_depth: standard
  enable_ai_analysis: true
  enable_fuzzing: true
  immunefi_program: chainlink
```

**Expected Results:**
- Smart contract analysis
- Off-chain code analysis
- Integration security checks
- Oracle manipulation vectors

---

## Scheduled Analysis Examples

### Weekly Security Audit

```yaml
# .github/workflows/weekly-security.yml
name: Weekly Security Audit

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM UTC
  workflow_dispatch:

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger comprehensive analysis
        run: |
          gh workflow run comprehensive-security-analysis.yml \
            -f target_repo=${{ github.server_url }}/${{ github.repository }} \
            -f target_type=mixed \
            -f analysis_depth=standard \
            -f enable_ai_analysis=true \
            -f enable_fuzzing=true
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Pre-Release Security Gate

```yaml
# .github/workflows/pre-release-audit.yml
name: Pre-Release Security Audit

on:
  push:
    tags:
      - 'v*'

jobs:
  security-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Deep security analysis
        run: |
          gh workflow run comprehensive-security-analysis.yml \
            -f target_repo=${{ github.server_url }}/${{ github.repository }} \
            -f target_type=smart-contract \
            -f analysis_depth=deep \
            -f enable_ai_analysis=true \
            -f enable_fuzzing=true
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Custom Analysis Profiles

### Profile: Quick Development Check

```yaml
analysis_depth: quick
enable_ai_analysis: false
enable_fuzzing: false
# Best for: Rapid iteration, pre-commit hooks
# Duration: 5-15 minutes
```

### Profile: Standard CI/CD

```yaml
analysis_depth: standard
enable_ai_analysis: true
enable_fuzzing: true
# Best for: Pull requests, daily builds
# Duration: 30-60 minutes
```

### Profile: Comprehensive Audit

```yaml
analysis_depth: deep
enable_ai_analysis: true
enable_fuzzing: true
# Best for: Releases, security audits, bug bounties
# Duration: 2-4 hours
```

### Profile: Bug Bounty Research

```yaml
analysis_depth: deep
enable_ai_analysis: true
enable_fuzzing: true
immunefi_program: [program-name]
# Best for: Bug bounty hunting, vulnerability research
# Duration: 2-4 hours
# Includes: Immunefi intelligence integration
```

---

## Tips for Configuration

1. **Start Small:** Begin with `quick` mode to validate setup
2. **Iterate:** Move to `standard` once comfortable
3. **Deep Dive:** Use `deep` mode for critical analysis
4. **Context Matters:** Always specify `immunefi_program` when applicable
5. **Type Selection:** Use `mixed` when unsure about project type
6. **AI Toggle:** Disable AI for faster scans when not needed
7. **Fuzzing Toggle:** Disable for projects without tests

---

## Command Line Templates

### Basic Analysis
```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=REPO_URL \
  -f target_type=TYPE \
  -f analysis_depth=DEPTH
```

### Full Analysis
```bash
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=REPO_URL \
  -f target_type=TYPE \
  -f analysis_depth=DEPTH \
  -f enable_ai_analysis=BOOL \
  -f enable_fuzzing=BOOL \
  -f immunefi_program=PROGRAM
```

### API Call Template
```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/blairmichaelg/secbrain/actions/workflows/comprehensive-security-analysis.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "target_repo": "REPO_URL",
      "target_type": "TYPE",
      "analysis_depth": "DEPTH",
      "enable_ai_analysis": "BOOL",
      "enable_fuzzing": "BOOL",
      "immunefi_program": "PROGRAM"
    }
  }'
```

Replace placeholders:
- `REPO_URL` - Target repository URL
- `TYPE` - `python`, `smart-contract`, or `mixed`
- `DEPTH` - `quick`, `standard`, or `deep`
- `BOOL` - `true` or `false`
- `PROGRAM` - Immunefi program name (or empty string)

---

## Additional Resources

- [Full Documentation](.github/workflows/COMPREHENSIVE_SECURITY_ANALYSIS_README.md)
- [Quick Reference](COMPREHENSIVE_SECURITY_ANALYSIS_QUICKREF.md)
- [Main README](README.md)
