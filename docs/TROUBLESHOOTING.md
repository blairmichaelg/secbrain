# SecBrain Troubleshooting Guide

Comprehensive guide for debugging and resolving common issues in the SecBrain bounty workflow.

---

## Quick Diagnostics

### Check Tool Availability

```bash
# SecBrain automatically checks tools on startup
secbrain run --scope ... --program ... --workspace ...

# Manual checks:
forge --version      # Foundry (required for contracts)
nuclei -version      # Nuclei (recommended for scanning)
semgrep --version    # Semgrep (recommended for static analysis)
subfinder -version   # Subfinder (recommended for recon)
```

### Check Logs

```bash
# View latest run logs
tail -f workspace/logs/*.jsonl

# Search for errors
grep '"level":"error"' workspace/logs/*.jsonl

# Search for warnings
grep '"level":"warning"' workspace/logs/*.jsonl
```

### Check Phase Outputs

```bash
# View phase results
cat workspace/phases/recon.json | jq .
cat workspace/phases/hypothesis.json | jq .
cat workspace/phases/exploit.json | jq .

# Check run summary
cat workspace/run_summary.json | jq .
```

---

## Common Issues

### Issue: "Required tools are missing"

**Symptom:**
```
⚠️  REQUIRED TOOLS MISSING:
  ❌ foundry
Cannot proceed: required tools are not installed
```

**Solution:**
Install the required tools:

```bash
# Foundry (required for smart contracts)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Verify
forge --version
```

---

### Issue: Zero findings despite running all phases

**Symptom:**
- All phases complete successfully
- 0 hypotheses generated OR
- Hypotheses generated but 0 exploit attempts OR
- Exploit attempts made but 0 profitable

**Root Causes & Solutions:**

#### 1. Missing Dependencies (eth-hash)

**Check:**
```bash
python3 -c "from eth_utils import to_checksum_address; print('OK')"
```

**Fix:**
```bash
pip install "eth-hash[pycryptodome]"
```

**Reference:** See [RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md)

#### 2. Hypothesis Quality Filtering Too Strict

**Check:**
```bash
cat workspace/phases/hypothesis.json | jq '.hypotheses_filtered_out | length'
```

**Fix:**
Lower quality thresholds in workflow initialization:

```python
from secbrain.workflows.bug_bounty_run import BugBountyWorkflow
from secbrain.workflows.hypothesis_quality_filter import HypothesisQualityFilter

custom_filter = HypothesisQualityFilter(
    min_confidence=0.3,  # Lower from default 0.45
    min_overall_score=0.4,  # Lower from default 0.5
)

# Pass to workflow...
```

#### 3. Source Code Not Found

**Check:**
```bash
cat workspace/phases/static.json | jq '.skipped'
# If true, static analysis was skipped
```

**Fix:**
Either:
- Use `--source` parameter: `secbrain run --source targets/myprotocol/instascope ...`
- Or ensure source code is in auto-detected location:
  - `workspace/instascope/src/`
  - `workspace/src/`
  - `workspace/contracts/`

#### 4. RPC/Forking Issues

**Check logs:**
```bash
grep "rpc" workspace/logs/*.jsonl
grep "fork" workspace/logs/*.jsonl
```

**Fix:**
- Use valid RPC URL with sufficient credits
- Pin to specific block number
- Check chain ID matches network

```bash
secbrain run \
  --rpc-url https://mainnet.infura.io/v3/YOUR_KEY \
  --block-number 18000000 \
  --chain-id 1 \
  ...
```

---

### Issue: "Tool not found" errors during recon

**Symptom:**
```
tool_unavailable: subfinder
tool_unavailable: amass
```

**Solutions:**

#### Quick Fix (Recommended Tools)
```bash
# Install Go tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Or via Homebrew (macOS)
brew install subfinder amass httpx nuclei
```

#### Alternative: Skip Tool-Dependent Phases
```bash
# Run only contract-based recon (no web tools needed)
secbrain run --phases ingest,plan,recon,hypothesis,exploit,triage,report ...
```

---

### Issue: Workflow takes too long

**Symptom:**
- Workflow runs for >10 minutes
- No progress updates
- Phases seem to hang

**Diagnostics:**

```bash
# Check current phase
tail -1 workspace/logs/*.jsonl | jq .phase

# Check performance metrics
cat workspace/performance_metrics.json | jq .
```

**Solutions:**

#### 1. Enable Checkpoints (Resume)
Checkpoints are enabled by default. If workflow is interrupted, re-run:

```bash
# Will resume from last checkpoint
secbrain run --scope ... --program ... --workspace ...
```

#### 2. Reduce Scope
```bash
# Test critical contracts only
# Edit scope.yaml to include fewer contracts/domains

# Or run specific phases
secbrain run --phases recon,hypothesis,exploit ...
```

#### 3. Tune Exploit Iterations
```bash
# Reduce iterations per hypothesis
secbrain run --exploit-iterations 1 ...  # Default is 3
```

#### 4. Set Profit Threshold
```bash
# Stop early when profit found
secbrain run --profit-threshold 0.05 ...  # 0.05 ETH
```

---

### Issue: Nuclei scanner not finding vulnerabilities

**Symptom:**
```
nuclei_scanner_unavailable: not_installed
```

or

```
nuclei_scan_complete: findings_count=0
```

**Solutions:**

#### Install Nuclei
```bash
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Update templates
nuclei -update-templates

# Verify
nuclei -version
```

#### Check Scan Configuration
Nuclei only scans live HTTP hosts. Verify you have live hosts:

```bash
cat workspace/phases/recon.json | jq '.live_hosts_count'
```

If 0, check:
- Domains are in scope
- Domains are reachable
- HTTP probing is working

---

### Issue: Semgrep not running

**Symptom:**
```
static_analysis skipped: no_source
```

**Solutions:**

#### 1. Auto-Detection (New in v2.0)
Place source code in standard locations:
```
workspace/instascope/src/
workspace/src/
workspace/contracts/
```

SecBrain will auto-detect and analyze.

#### 2. Manual Source Path
```bash
secbrain run --source ./instascope ...
```

#### 3. Install Semgrep
```bash
pip install semgrep

# Verify
semgrep --version
```

---

### Issue: "Permission denied" or "ACL violation"

**Symptom:**
```
ACL violation: tool 'nuclei' not allowed in phase 'recon'
```

**Solution:**

Check RunContext configuration:

```python
# In custom workflow code:
run_context.check_tool_acl("nuclei")  # Returns bool

# Update ACL if needed (advanced)
# See secbrain/core/context.py
```

Default ACLs are permissive. This is rare.

---

### Issue: API rate limits exceeded

**Symptom:**
```
rate_limit_exceeded: perplexity
rate_limit_exceeded: gemini
```

**Solutions:**

#### 1. Check API Keys
```bash
echo $PERPLEXITY_API_KEY
echo $GOOGLE_API_KEY
echo $TOGETHER_API_KEY
```

#### 2. Use Free Tier Limits
- Perplexity PRO: Unlimited (free)
- Google Gemini: High limits (free)
- Together AI: Generous free tier

See [FREE_TIER_MODELS.md](FREE_TIER_MODELS.md)

#### 3. Reduce Research Calls
Lower max_calls_per_run:

```python
from secbrain.tools.perplexity_research import PerplexityResearch

research = PerplexityResearch(max_calls_per_run=20)  # Default is 50
```

---

## Debugging Workflows

### Enable Debug Logging

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Run workflow
secbrain run ...

# Check debug logs
grep '"level":"debug"' workspace/logs/*.jsonl
```

### Dry Run Mode

Test workflow without actual tool execution:

```bash
secbrain run --dry-run --scope ... --program ... --workspace ...
```

### Run Specific Phases

```bash
# Test hypothesis generation only
secbrain run --phases ingest,plan,recon,hypothesis ...

# Test exploit without hypothesis (requires existing workspace)
secbrain run --phases exploit ...
```

### Inspect Checkpoints

```bash
# List checkpoints
ls -la workspace/.checkpoints/

# View checkpoint
cat workspace/.checkpoints/run-xxx_latest.json | jq .
```

---

## Performance Issues

### Slow Hypothesis Generation

**Check:**
```bash
cat workspace/performance_metrics.json | jq '.phases.hypothesis'
```

**Potential Causes:**
- Too many contracts (>20)
- Large ABIs with many functions
- Research queries timing out

**Solutions:**
- Focus on critical contracts
- Reduce hypothesis budget per contract
- Cache research results

### Slow Exploit Phase

**Check:**
```bash
cat workspace/performance_metrics.json | jq '.phases.exploit'
```

**Solutions:**
- Reduce `--exploit-iterations`
- Set `--profit-threshold` for early exit
- Enable parallel execution (future feature)

### High Memory Usage

**Check:**
```bash
# Monitor during run
ps aux | grep secbrain
```

**Solutions:**
- Reduce batch sizes
- Clear old workspace data
- Process fewer contracts per run

---

## Error Messages Reference

### "Kill-switch activated"

**Cause:** Kill-switch file was created or signal received

**Check:**
```bash
ls -la /path/to/kill-switch-file
```

**Solution:** Remove file and re-run

### "Approval required: [tool]"

**Cause:** Tool requires human approval

**Solutions:**
- Use `--auto-approve` flag (not recommended for production)
- Use `--approval-mode auto`
- Approve manually when prompted

### "Scope violation: [target]"

**Cause:** Target is outside defined scope

**Solution:**
- Verify scope.yaml includes target
- Check domain/contract address format
- Ensure wildcards are correct (e.g., `*.example.com`)

---

## Getting Help

### Check Existing Documentation

1. [BOUNTY_WORKFLOW_ANALYSIS.md](BOUNTY_WORKFLOW_ANALYSIS.md) - Complete workflow analysis
2. [WORKFLOW_OPTIMIZATION_GUIDE.md](WORKFLOW_OPTIMIZATION_GUIDE.md) - Optimization features
3. [RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md) - Zero-finding debugging
4. [README.md](README.md) - General documentation

### Collect Diagnostic Information

Before reporting issues, collect:

```bash
# Version
secbrain version

# Tool versions
forge --version
nuclei -version
semgrep --version

# Logs
tar -czf debug-logs.tar.gz workspace/logs/ workspace/*.json

# Configuration (redact sensitive data)
cat workspace/scope.yaml
cat workspace/program.json
```

### File an Issue

Include:
- SecBrain version
- Command run
- Expected vs actual behavior
- Relevant log snippets
- Configuration files (redacted)

---

## Quick Reference

### Workflow Phases

| Phase | Purpose | Common Issues |
|-------|---------|---------------|
| Ingest | Load program/scope | Invalid YAML/JSON |
| Plan | Generate test plan | API key missing |
| Recon | Discover assets | Tools not installed |
| Hypothesis | Generate vuln ideas | eth-hash missing |
| Exploit | Test hypotheses | RPC issues |
| Static | Code analysis | Source not found |
| Triage | Prioritize findings | N/A |
| Report | Generate reports | N/A |
| Meta | Learn from run | N/A |

### Essential Commands

```bash
# Check tools
forge --version && nuclei -version && semgrep --version

# Run with all optimizations
secbrain run --scope ... --program ... --workspace ...

# Resume from checkpoint
secbrain run --scope ... --program ... --workspace ...  # Same workspace

# Debug mode
LOG_LEVEL=DEBUG secbrain run ...

# Dry run
secbrain run --dry-run ...

# Specific phases
secbrain run --phases recon,hypothesis,exploit ...
```

---

**Last Updated:** 2025-12-25  
**Version:** 2.0.0
