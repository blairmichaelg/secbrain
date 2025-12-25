# Threshold Network Run - Optimization Checklist

This checklist ensures optimal performance and cost-efficiency when running SecBrain against the Threshold Network bug bounty program.

## Pre-Run Checklist

### 1. Dependencies ✓
- [x] eth-hash[pycryptodome]>=0.7.0 installed
- [x] All requirements from requirements.in installed
- [x] Python 3.11+ running

**Verify:**
```bash
python -c "import eth_hash; print('eth-hash OK')"
python -c "import eth_utils; print('eth-utils OK')"
```

### 2. API Keys Configuration

- [ ] PERPLEXITY_API_KEY set (for research integration)
- [ ] GOOGLE_API_KEY set (for Gemini advisor model)
- [ ] TOGETHER_API_KEY or OPENROUTER_API_KEY or OPENAI_API_KEY set (for worker model)

**Verify:**
```bash
echo "Perplexity: ${PERPLEXITY_API_KEY:0:10}..."
echo "Google: ${GOOGLE_API_KEY:0:10}..."
echo "Together: ${TOGETHER_API_KEY:0:10}..."
```

**Recommended Setup (from OPTIMIZATION-GUIDE.md):**
- **Worker Model**: DeepSeek-Chat via Together AI (fast, cost-effective)
- **Advisor Model**: Gemini 2.0 Flash Exp (quick reviews)
- **Research Model**: Perplexity Sonar (real-time exploit data)

### 3. Configuration Files ✓

- [x] program.json exists and is valid
- [x] scope.yaml exists and is valid
- [x] All 39 contracts configured in scope.yaml
- [x] RPC URLs configured (3 endpoints)
- [x] Profit tokens configured (TBTC, T, WETH, USDC)
- [x] Foundry root path correct

**Verify:**
```bash
python targets/thresholdnetwork/validate_config.py
```

### 4. Foundry Setup

- [ ] Foundry installed (`forge --version`)
- [ ] Contracts can be compiled

**Verify:**
```bash
cd targets/thresholdnetwork/instascope
# Test compile one contract
FOUNDRY_PROFILE=contract_TBTC_1808 forge build
# Or build all
./build.sh
```

### 5. Network Access

- [ ] RPC endpoints accessible
- [ ] No firewall blocking Ethereum RPC calls

**Verify:**
```bash
curl -X POST https://ethereum.publicnode.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

## Optimization Settings

### Model Selection (from OPTIMIZATION-GUIDE.md)

#### Worker Model
```python
# DeepSeek-Chat (via Together AI) - Recommended
- Performance: ~2-3x faster than Qwen 2.5 72B
- Cost: ~50% reduction
- Quality: High for security analysis
```

#### Advisor Model
```python
# Gemini 2.0 Flash Exp - Recommended
- Performance: ~3-5x faster than Gemini Pro
- Cost: ~70% reduction
- Quality: Comparable for security reviews
```

#### Research Model
```python
# Perplexity Sonar - Recommended
- Performance: ~2x faster than Sonar Medium Online
- Cost: ~40% reduction
- Quality: Sufficient for security research
```

### Caching Strategy

Research caching TTLs (from OPTIMIZATION-GUIDE.md):
- **Severity Context**: 168h (7 days) - Severity standards change slowly
- **Attack Vectors**: 48h (2 days) - Attack patterns evolve moderately
- **Market Conditions**: 1h - Market data must be current
- **Technology Research**: 24h (1 day) - Balanced refresh rate

### Rate Limiting

- **Research calls**: 10 req/min (configured)
- **RPC calls**: 10 req/sec (configured in scope.yaml)
- **Connection pooling**: Enabled (HTTP clients use keep-alive)

### HTTP Connection Pooling

Already configured in SecBrain:
- Perplexity: max_keepalive=5, max_connections=10
- Worker Model: max_keepalive=10, max_connections=20

**Benefits:**
- 60-80% reduction in connection overhead
- Improved throughput via connection reuse
- Reduced latency for consecutive calls

## Run Configuration

### Recommended First Run (Dry-Run)

```bash
secbrain run \
  --scope targets/thresholdnetwork/scope.yaml \
  --program targets/thresholdnetwork/program.json \
  --workspace targets/thresholdnetwork/workspace \
  --dry-run
```

**Why dry-run first:**
- Validates configuration without making actual network calls
- Tests hypothesis generation
- Verifies contract compilation
- No API costs
- Fast feedback loop

### Full Production Run

```bash
secbrain run \
  --scope targets/thresholdnetwork/scope.yaml \
  --program targets/thresholdnetwork/program.json \
  --workspace targets/thresholdnetwork/workspace
```

**Expected behavior:**
1. **Recon Phase**: Compile 39 contracts, extract ABIs
2. **Hypothesis Phase**: Generate vulnerability hypotheses (expect 10-20)
3. **Exploit Phase**: Test hypotheses on local forks
4. **Triage Phase**: Validate findings
5. **Report Phase**: Generate PoCs and reports

### Targeted Run (Focus on High-Value Contracts)

To optimize for specific contracts:

1. Create a focused scope file:
```yaml
# targets/thresholdnetwork/scope-critical.yaml
contracts:
  - name: TBTC
    address: "0x18084fbA666a33d37592fA2633fD49a74DD93a88"
    chain_id: 1
    foundry_profile: "contract_TBTC_1808"
  - name: TBTCVault
    address: "0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD"
    chain_id: 1
    foundry_profile: "contract_TBTCVault_9c07"
  - name: Bridge
    address: "0x8d014903bf7867260584d714e11809fea5293234"
    chain_id: 1
    foundry_profile: "contract_Bridge_8d01"
  # ... add other critical contracts
```

2. Run with focused scope:
```bash
secbrain run \
  --scope targets/thresholdnetwork/scope-critical.yaml \
  --program targets/thresholdnetwork/program.json \
  --workspace targets/thresholdnetwork/workspace-critical
```

## Performance Optimization Tips

### 1. Parallel Contract Compilation

Build contracts in parallel:
```bash
cd targets/thresholdnetwork/instascope
# Parallel build (adjust -j based on CPU cores)
ls -d src/*/ | xargs -P 4 -I {} bash -c 'FOUNDRY_PROFILE=$(basename {}) forge build'
```

### 2. RPC Endpoint Selection

Prioritize RPC endpoints by performance:
1. **Fastest**: Your own node (if available)
2. **Fast**: Paid services (Alchemy, Infura)
3. **Moderate**: Public endpoints (configured in scope.yaml)

Add custom endpoint in scope.yaml:
```yaml
rpc_urls:
  - "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"  # Add first for priority
  - "https://ethereum.publicnode.com"
  - "https://eth.llamarpc.com"
```

### 3. Workspace Management

Keep workspace clean between runs:
```bash
# Archive old workspace
tar -czf workspace-$(date +%Y%m%d-%H%M%S).tar.gz targets/thresholdnetwork/workspace

# Start fresh
rm -rf targets/thresholdnetwork/workspace
```

### 4. Focus on High-Severity Patterns

Prioritize patterns that match critical severity criteria:
- Direct theft of user funds
- Permanent freezing of funds
- Protocol insolvency
- Bridge vulnerabilities (tBTC specific)

### 5. Incremental Analysis

Run analysis in phases:
1. **Phase 1**: Core tBTC contracts (TBTC, TBTCVault, Bridge)
2. **Phase 2**: Staking and governance (TokenStaking, Governors)
3. **Phase 3**: Cross-chain bridges (Starknet, Wormhole)
4. **Phase 4**: Supporting contracts (Proxies, Validators)

## Cost Optimization

### Expected API Costs (per full run)

Based on OPTIMIZATION-GUIDE.md optimizations:

**Worker Model (DeepSeek-Chat):**
- ~50% cost reduction vs baseline
- Estimated: $5-15 per full run (39 contracts)

**Advisor Model (Gemini 2.0 Flash Exp):**
- ~70% cost reduction vs baseline
- Estimated: $2-5 per full run

**Research Model (Perplexity Sonar):**
- ~40% cost reduction vs baseline
- With caching: ~60% total reduction
- Estimated: $3-8 per full run

**Total estimated cost per full run: $10-30**

### Cost Reduction Strategies

1. **Use dry-run extensively** - No API costs
2. **Enable caching** - Already configured, 30-40% reduction
3. **Focus on high-value contracts first** - Test with smaller scope
4. **Batch similar analyses** - Share research cache across runs
5. **Monitor usage** - Check API dashboards regularly

## Monitoring and Debugging

### Log Locations

```bash
# Run logs
targets/thresholdnetwork/workspace/logs/

# Phase outputs
targets/thresholdnetwork/workspace/phases/

# Hypotheses
targets/thresholdnetwork/workspace/hypotheses/

# Findings
targets/thresholdnetwork/workspace/findings/
```

### Key Metrics to Monitor

Check `meta_metrics.jsonl`:
```bash
cat targets/thresholdnetwork/workspace/meta_metrics.jsonl | jq '.'
```

**Important metrics:**
- `hypotheses_generated` - Should be 10-20 for 39 contracts
- `hypotheses_with_targets` - Should be 85%+ coverage
- `exploit_attempts` - Varies based on hypotheses
- `profitable_attempts` - Check for profit detection
- `findings_count` - Validated findings

### Common Issues

1. **Missing eth-hash backend**
```bash
pip install "eth-hash[pycryptodome]"
```

2. **Compilation errors**
```bash
cd targets/thresholdnetwork/instascope
FOUNDRY_PROFILE=contract_<name>_<addr> forge build --force
```

3. **RPC rate limiting**
```bash
# Add delays or use multiple endpoints
# Already configured in scope.yaml with 3 endpoints
```

4. **Memory issues**
```bash
# Reduce concurrent analysis, focus on fewer contracts
# Use targeted scope files
```

## Post-Run Analysis

### Generate Insights Report

```bash
secbrain insights \
  --workspace targets/thresholdnetwork/workspace \
  --format html \
  --open
```

### Review Findings

1. Check findings directory
2. Validate PoCs
3. Assess severity
4. Calculate impact
5. Prepare Immunefi submission

### Iteration

Based on results:
1. Review hypotheses that had no targets
2. Adjust focus areas if needed
3. Re-run with improved configuration
4. Focus on specific patterns that showed promise

## Security Reminders

- ✅ **ALWAYS** use local forks for testing
- ❌ **NEVER** test on mainnet or public testnets
- ✅ **ALWAYS** include PoC in submissions
- ✅ **ALWAYS** follow Immunefi safe harbor rules
- ❌ **NEVER** exploit vulnerabilities for personal gain
- ✅ **ALWAYS** report responsibly to Immunefi

## Success Criteria

A successful run should have:
- [ ] All 39 contracts compiled successfully
- [ ] 10-20 hypotheses generated
- [ ] 85%+ hypotheses with concrete targets
- [ ] Multiple exploit attempts executed
- [ ] At least 1-3 validated findings (if vulnerabilities exist)
- [ ] Complete PoCs for any findings
- [ ] Detailed impact assessment

## Next Steps After Successful Run

1. **Review all findings carefully**
2. **Validate PoCs locally**
3. **Assess severity accurately**
4. **Calculate funds at risk**
5. **Prepare detailed write-up**
6. **Submit to Immunefi**
7. **Follow up on questions**

---

**Last Updated**: 2025-12-25
**Target**: Threshold Network (39 contracts)
**Expected Run Time**: 2-4 hours (full run)
**Expected Cost**: $10-30 (with optimizations)
