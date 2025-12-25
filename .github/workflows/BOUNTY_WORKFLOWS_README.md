# Bounty Hunting Workflows

This directory contains GitHub Actions workflows designed to help find security vulnerabilities and bounties in smart contract projects, with a focus on the Threshold Network and other bug bounty programs.

## Available Workflows

### 1. Threshold Network Bounty Hunt (`threshold-bounty-hunt.yml`)

**Purpose:** Automated weekly bounty hunting specifically for Threshold Network using SecBrain's multi-agent system.

**Triggers:**
- 🕐 **Scheduled:** Every Monday at 6 AM UTC
- 🖱️ **Manual:** Via workflow_dispatch

**Features:**
- Full SecBrain workflow execution (ingest → plan → recon → hypothesis → exploit → static → triage → report → meta)
- Foundry contract compilation and testing
- Automated insights report generation
- High-value finding detection and GitHub issue creation
- Workspace archiving for historical analysis

**Configuration Options:**
- `run_mode`: Choose between `dry-run` (no API costs) or `full` (complete analysis)
- `scope_type`: Target `full` scope (all 39 contracts) or `critical` scope (high-value contracts only)

**Usage:**
```bash
# Trigger manually via GitHub UI
Go to Actions → Threshold Network Bounty Hunt → Run workflow

# Or use GitHub CLI
gh workflow run threshold-bounty-hunt.yml -f run_mode=full -f scope_type=critical
```

**Outputs:**
- Workspace artifacts with findings and reports
- GitHub issues for high-value vulnerabilities
- Automated commits to repository with results

**Best For:**
- Regular scheduled bounty hunting
- Comprehensive multi-phase security analysis
- Research-backed vulnerability discovery

---

### 2. Foundry Bounty Hunt (`foundry-bounty-hunt.yml`)

**Purpose:** Intensive Foundry-based testing with fuzzing, invariant testing, and multiple static analysis tools.

**Triggers:**
- 🕐 **Scheduled:** Every Wednesday at 3 AM UTC
- 🖱️ **Manual:** Via workflow_dispatch

**Features:**
- Intensive fuzz testing (default: 50,000 runs per test)
- Deep invariant testing (default: 5,000 runs with depth 50)
- Slither static analysis
- Mythril symbolic execution
- Echidna advanced fuzzing
- Gas usage analysis and optimization
- Automated vulnerability reporting

**Configuration Options:**
- `target`: Which target to analyze (default: `thresholdnetwork`)
- `fuzz_runs`: Number of fuzz iterations (default: `50000`)
- `invariant_runs`: Number of invariant test runs (default: `5000`)

**Usage:**
```bash
# Trigger manually
gh workflow run foundry-bounty-hunt.yml -f target=thresholdnetwork -f fuzz_runs=100000

# For quick testing
gh workflow run foundry-bounty-hunt.yml -f target=thresholdnetwork -f fuzz_runs=10000
```

**Tools Used:**
- **Foundry:** Property-based fuzzing and invariant testing
- **Slither:** Static analysis for common vulnerabilities
- **Mythril:** Symbolic execution for deep analysis
- **Echidna:** Coverage-guided fuzzing

**Outputs:**
- Detailed test results and logs
- Vulnerability reports with severity rankings
- GitHub issues for detected vulnerabilities
- Gas snapshots and optimization suggestions

**Best For:**
- Deep contract testing
- Finding edge cases and invariant violations
- Gas optimization opportunities
- Comprehensive security auditing

---

### 3. SecBrain Auto PR (`secbrain-auto-pr.yml`)

**Purpose:** Run SecBrain analysis and automatically create a pull request with results.

**Triggers:**
- 🖱️ **Manual only:** Via workflow_dispatch

**Features:**
- On-demand SecBrain runs
- Automatic PR creation with results
- Customizable branch names
- Detailed run summaries in PR description

**Configuration Options:**
- `target`: Choose from `thresholdnetwork` or `originprotocol`
- `run_mode`: `dry-run` or `full`
- `branch_name`: Custom branch name (optional)

**Usage:**
```bash
gh workflow run secbrain-auto-pr.yml \
  -f target=thresholdnetwork \
  -f run_mode=full \
  -f branch_name=threshold-analysis-$(date +%Y%m%d)
```

**Best For:**
- Ad-hoc analysis runs
- Testing new configurations
- Collaborative review via PRs

---

## Workflow Comparison

| Feature | Threshold Bounty Hunt | Foundry Bounty Hunt | SecBrain Auto PR |
|---------|----------------------|---------------------|------------------|
| **Automation** | Scheduled + Manual | Scheduled + Manual | Manual Only |
| **Analysis Type** | Multi-agent AI | Fuzzing + Static | Multi-agent AI |
| **Tools** | SecBrain, Foundry | Foundry, Slither, Mythril, Echidna | SecBrain |
| **Intensity** | High | Very High | Configurable |
| **Duration** | 60-120 min | 60-180 min | 30-90 min |
| **Best For** | Vulnerability discovery | Edge case finding | On-demand analysis |
| **Outputs** | Findings + Reports | Test results + Vulnerabilities | PR with results |

---

## Getting Started

### Prerequisites

1. **API Keys** (for full runs):
   - `PERPLEXITY_API_KEY` - Required for research
   - `GOOGLE_API_KEY` - Required for advisor model
   - `TOGETHER_API_KEY` or `OPENROUTER_API_KEY` - Required for worker models

2. **Repository Access**:
   - GitHub Actions enabled
   - Proper permissions for workflows

### Setup Steps

1. **Add Secrets** (for full analysis):
   ```bash
   # Go to repository Settings → Secrets and variables → Actions
   # Add the following secrets:
   - PERPLEXITY_API_KEY
   - GOOGLE_API_KEY
   - TOGETHER_API_KEY
   ```

2. **Enable Workflows**:
   - Go to Actions tab in GitHub
   - Enable workflows if not already enabled

3. **Run Your First Workflow**:
   ```bash
   # Start with a dry-run
   gh workflow run threshold-bounty-hunt.yml -f run_mode=dry-run
   
   # Review results, then run full analysis
   gh workflow run threshold-bounty-hunt.yml -f run_mode=full -f scope_type=critical
   ```

---

## Understanding Results

### Threshold Bounty Hunt Results

Located in: `targets/thresholdnetwork/workspace/`

**Key Files:**
- `run_summary.json` - High-level metrics
- `findings/*.json` - Individual vulnerability findings
- `reports/*.md` - Detailed vulnerability reports
- `insights/` - Analysis insights and trends
- `logs/*.jsonl` - Detailed execution logs

**Finding Severity:**
- **CRITICAL** → Up to $1,000,000 (direct theft, protocol insolvency)
- **HIGH** → Up to $50,000 (theft/freezing of unclaimed yield)
- **MEDIUM** → Up to $10,000 (contract inoperability, griefing)
- **LOW** → Up to $1,000 (informational issues)

### Foundry Bounty Hunt Results

Located in: `targets/thresholdnetwork/foundry-results-{timestamp}/`

**Key Files:**
- `fuzz-results.log` - Fuzz testing output
- `invariant-results.log` - Invariant test results
- `slither-results.json` - Static analysis findings
- `mythril-results.log` - Symbolic execution results
- `vulnerability-report.md` - Consolidated report
- `gas-snapshot.txt` - Gas usage data

**Interpreting Results:**
- Test **FAILURES** → Potential vulnerabilities
- **Slither HIGH/CRITICAL** → Review immediately
- **Invariant violations** → Logic bugs
- **Gas spikes** → Optimization opportunities

---

## Next Steps After Finding Vulnerabilities

### 1. Validate the Finding
- [ ] Reproduce the issue manually
- [ ] Create a minimal PoC
- [ ] Test on local fork (never on mainnet!)
- [ ] Verify severity and impact

### 2. Document the Vulnerability
- [ ] Write clear description
- [ ] Document affected contracts/functions
- [ ] Explain attack scenario
- [ ] Calculate potential impact
- [ ] Prepare PoC code

### 3. Submit to Bug Bounty Program

**For Threshold Network:**
1. Go to https://immunefi.com/bug-bounty/thresholdnetwork/
2. Click "Submit a bug"
3. Provide detailed information:
   - Clear title
   - Severity assessment
   - Impact description
   - Proof of Concept
   - Remediation suggestion
4. Follow up with the program team

**Submission Checklist:**
- [ ] Clear vulnerability description
- [ ] Working PoC on local fork
- [ ] Impact assessment
- [ ] Remediation suggestion
- [ ] No public disclosure

### 4. Follow Responsible Disclosure
- ⚠️ **NEVER** test on mainnet
- ⚠️ **NEVER** disclose publicly before fix
- ⚠️ **NEVER** exploit for personal gain
- ✅ **ALWAYS** follow Immunefi safe harbor
- ✅ **ALWAYS** give team time to fix

---

## Optimization Tips

### Reduce Costs
1. Use `dry-run` mode for testing
2. Target `critical` scope instead of `full`
3. Run locally first with `./targets/thresholdnetwork/run-threshold.sh`

### Increase Effectiveness
1. **Schedule strategically:**
   - Run after major contract updates
   - Run before audit deadlines
   - Coordinate with bug bounty program updates

2. **Combine workflows:**
   - Run Threshold Bounty Hunt for comprehensive analysis
   - Follow up with Foundry Bounty Hunt for deep testing
   - Use SecBrain Auto PR for specific hypothesis testing

3. **Monitor results:**
   - Review artifacts regularly
   - Track finding trends
   - Update hypotheses based on learnings

### Performance Tuning

**For Faster Runs:**
```bash
# Reduce scope
scope_type: critical

# Lower fuzz runs
fuzz_runs: 10000
invariant_runs: 1000
```

**For Deeper Analysis:**
```bash
# Full scope
scope_type: full

# Intensive fuzzing
fuzz_runs: 100000
invariant_runs: 10000
```

---

## Troubleshooting

### Common Issues

**1. Workflow Fails with "API key not set"**
- **Solution:** Add required API keys to repository secrets
- For dry-run: API keys not required

**2. Foundry Build Fails**
- **Solution:** Check Solidity versions in contracts
- Some contracts may require specific compiler versions
- Build errors don't block analysis

**3. No Findings Generated**
- **Possible causes:**
  - Contracts are secure (good!)
  - Scope too narrow
  - Quality filter too strict
- **Solution:** Review logs, adjust parameters

**4. Out of Memory**
- **Solution:** Use critical scope, reduce concurrent analysis
- Consider running locally with more resources

**5. Workflow Times Out**
- **Solution:** Reduce scope or test iterations
- Split analysis into multiple runs

### Getting Help

1. **Check Documentation:**
   - [BOUNTY_WORKFLOW_ANALYSIS.md](../BOUNTY_WORKFLOW_ANALYSIS.md)
   - [RUN_ANALYSIS_GUIDANCE.md](../RUN_ANALYSIS_GUIDANCE.md)
   - [Threshold Network README](../targets/thresholdnetwork/README.md)

2. **Review Logs:**
   - Workflow run logs in GitHub Actions
   - Workspace logs: `workspace/logs/*.jsonl`

3. **Community Resources:**
   - GitHub Issues for bug reports
   - Threshold Discord for program questions
   - Immunefi docs for submission guidance

---

## Security Considerations

### Workflow Security
- ✅ Workflows run in isolated environments
- ✅ API keys stored as encrypted secrets
- ✅ No mainnet interactions
- ✅ Results reviewed before public disclosure

### Data Privacy
- Findings stored in private repository
- No sensitive data in public logs
- Workspace artifacts expire after 90 days

### Responsible Disclosure
- All findings kept confidential
- Follow Immunefi safe harbor rules
- No exploitation for personal gain
- Coordinate fixes with project team

---

## Contributing

### Adding New Targets

1. Create target directory: `targets/{project_name}/`
2. Add configuration files:
   - `scope.yaml` - Contract scope
   - `program.json` - Bounty program details
   - `instascope/` - Source code
3. Update workflows to include new target
4. Test with dry-run first

### Improving Workflows

1. Fork repository
2. Make changes to workflow files
3. Test thoroughly with dry-runs
4. Submit PR with description

---

## Resources

### Documentation
- [SecBrain Documentation](../README.md)
- [Foundry Book](https://book.getfoundry.sh/)
- [Immunefi Guidelines](https://immunefi.com/learn/)

### Tools
- [Foundry](https://github.com/foundry-rs/foundry)
- [Slither](https://github.com/crytic/slither)
- [Mythril](https://github.com/ConsenSys/mythril)
- [Echidna](https://github.com/crytic/echidna)

### Bug Bounty Platforms
- [Immunefi](https://immunefi.com/)
- [Code4rena](https://code4rena.com/)
- [HackerOne](https://hackerone.com/)

---

## License

These workflows are part of the SecBrain project. See main [LICENSE](../LICENSE) for details.

---

**Last Updated:** 2025-12-25  
**Maintained by:** SecBrain Team  
**Questions?** Open an issue or reach out on Discord
