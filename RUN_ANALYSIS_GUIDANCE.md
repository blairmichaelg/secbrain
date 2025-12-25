# Origin Protocol Run Analysis & Guidance

**Date:** 2025-12-25  
**Target:** Origin Protocol  
**Analysis Type:** Post-Run Diagnostic

---

## Executive Summary

This document provides guidance on investigating SecBrain runs that complete successfully but produce zero findings, specifically analyzing patterns observed in the Origin Protocol target runs.

### Key Observations

Based on the meta_metrics.jsonl analysis of multiple Origin Protocol runs:

- **Consistent Pattern:** 7 hypotheses generated across successful runs
- **Target Coverage:** 6 out of 7 hypotheses had concrete targets (85.7% coverage)
- **Missing Targets:** 1 hypothesis consistently lacked contract/function mapping
- **Exploit Attempts:** Varied from 0-15 attempts per run
- **Profitability:** 0 attempts with detected profit across all runs
- **Economic Decision:** SKIP in all cases (no profit detected)

---

## Root Cause Analysis

### 1. **Dependency Issue: Missing eth-hash Backend** ❌ CRITICAL

**Problem:**  
The most recent run (3883eaeb) failed during hypothesis generation with:
```
None of these hashing backends are installed: ['pycryptodome', 'pysha3'].
Install with `python -m pip install "eth-hash[pycryptodome]"`.
```

**Impact:**
- Prevents address validation in hypothesis generation
- Causes hypothesis phase to fail completely
- Results in 0 hypotheses → 0 exploit attempts → 0 findings

**Resolution:**
✅ Added `eth-hash[pycryptodome]>=0.7.0` to:
- `requirements.in`
- `pyproject.toml`

**Action Required:**
```bash
# Regenerate requirements with hashes
cd secbrain
pip-compile --generate-hashes --output-file=requirements-hashed.txt requirements.in

# Or install directly for testing
pip install "eth-hash[pycryptodome]"
```

---

### 2. **Hypothesis Quality: Missing Contract/Function Targets** ⚠️ HIGH

**Pattern Observed:**
- 7 hypotheses generated consistently
- 1 hypothesis always lacks concrete target mapping
- Only 6/7 hypotheses can be tested

**Potential Causes:**
1. **ABI Parsing Issues:** Contracts may have complex or non-standard ABIs
2. **Function Signature Matching:** Generated hypothesis references function that doesn't exist
3. **Proxy Pattern Complexity:** Origin Protocol uses multiple proxy contracts which may confuse target resolution
4. **Incomplete Static Analysis:** Recon phase may not fully resolve proxy implementation addresses

**Investigation Steps:**
```bash
# Check which contracts were compiled
cat targets/originprotocol/phases/recon.json | jq '.contracts'

# Review hypothesis targets
cat targets/originprotocol/phases/hypothesis.json | jq '.hypotheses[] | {pattern: .pattern, contract: .target_contract, function: .target_function}'

# Check for proxy resolution
grep -r "proxy" targets/originprotocol/instascope/
```

---

### 3. **Zero Profitability: No Profitable Exploit Paths** ⚠️ HIGH

**Pattern Observed:**
- 0-15 attempts generated across runs
- 0 attempts detected any profit
- All economic decisions: SKIP

**Possible Explanations:**

#### A. **Profit Calculation Conservative**
The profit calculator may be too conservative or missing edge cases:
- Gas cost estimates too high
- Profit threshold too strict
- Not accounting for flash loan profits
- Missing MEV opportunities

#### B. **Test Environment Limitations**
Exploit attempts may fail in simulation:
- Missing mainnet state (price oracles, liquidity pools)
- Incorrect fork block height
- Test accounts lack necessary token balances
- Missing approval/setup steps

#### C. **Hypothesis Patterns Don't Match Real Vulnerabilities**
Generated hypotheses may be:
- Too generic (e.g., standard reentrancy checks on hardened contracts)
- Missing protocol-specific attack vectors
- Not leveraging Origin Protocol's unique mechanisms (rebasing, AMO, vault strategies)

#### D. **Origin Protocol Is Secure**
The protocol may simply not have exploitable vulnerabilities in the tested contracts:
- Origin Protocol has been audited multiple times
- Contracts are mature and battle-tested
- Bug bounty program has filtered out obvious issues

---

## Recommendations

### Immediate Actions (Required)

1. **✅ Fix eth-hash dependency** (COMPLETED)
   - Added to requirements.in and pyproject.toml
   - Regenerate requirements-hashed.txt
   - Test hypothesis generation works

2. **🔍 Debug Missing Target Mapping**
   ```bash
   # Enable debug logging for hypothesis agent
   export LOG_LEVEL=DEBUG
   secbrain run --scope targets/originprotocol/scope.yaml \
                --program targets/originprotocol/program.json \
                --workspace targets/originprotocol/debug-run
   
   # Check logs for target resolution
   cat targets/originprotocol/debug-run/logs/*.jsonl | grep "target"
   ```

3. **📊 Analyze Hypothesis Quality**
   - Review what vulnerability patterns are being generated
   - Check if they align with Origin Protocol's architecture
   - Verify contract addresses are correctly checksummed

### Short-term Improvements

4. **🎯 Protocol-Specific Hypothesis Enhancement**
   
   Origin Protocol specific attack surfaces to consider:
   - **Rebasing token mechanics** (OETH/OUSD)
   - **AMO strategy contracts** (Curve integration)
   - **Vault share price manipulation**
   - **Oracle manipulation** (Chainlink, Curve pools)
   - **Governance parameter changes**
   - **Strategy yield extraction**
   
   Update `ProtocolProfile` in `vuln_hypothesis_agent.py` to add Origin-specific patterns.

5. **💰 Profit Calculation Review**
   
   Examine `secbrain/core/profit_calculator.py`:
   - Lower profit threshold for testing
   - Add verbose logging
   - Verify gas estimates are reasonable
   - Check flash loan profit calculations

6. **🔬 Exploit Attempt Debugging**
   
   For runs that generate attempts but 0 profit:
   ```bash
   # Check exploit attempt details
   ls -la targets/originprotocol/exploit_attempts/
   
   # Review attempt outputs
   cat targets/originprotocol/exploit_attempts/*/attempt_*.json
   
   # Check for Foundry test outputs
   find targets/originprotocol/instascope -name "*.t.sol"
   ```

### Long-term Enhancements

7. **📚 Learning from Historical Data**
   - Analyze `targets/originprotocol/learnings/*.json`
   - Identify recurring failure patterns
   - Build corpus of known-good exploit patterns
   - Implement feedback loop for hypothesis refinement

8. **🧪 Enhanced Testing Strategies**
   - Fork from recent mainnet state
   - Pre-populate test accounts with realistic balances
   - Enable Foundry fuzzing for generated test cases
   - Add invariant testing for protocol properties

9. **🎯 Targeted Vulnerability Research**
   
   Use Perplexity research integration to:
   - Find recent Origin Protocol vulnerabilities
   - Study similar DeFi protocol exploits (Rari, Beanstalk, Harvest)
   - Research rebasing token attack vectors
   - Investigate Curve AMO manipulation techniques

10. **📈 Success Metrics & Monitoring**
    - Track hypothesis-to-attempt conversion rate
    - Monitor attempt-to-profitable-attempt ratio
    - Measure hypothesis diversity (pattern coverage)
    - Set up alerting for dependency failures

---

## Run Metrics Interpretation

### Normal vs. Concerning Patterns

| Metric | Normal Range | Concerning | Observed |
|--------|--------------|------------|----------|
| Hypotheses Generated | 5-15 | 0-2 | 7 ✅ (when deps work) |
| Target Coverage | 80-100% | <60% | 85.7% ⚠️ |
| Attempts per Hypothesis | 1-3 | 0 or >5 | 0-2.14 ⚠️ |
| Profitable Attempts | >0 | 0 | 0 ❌ |
| Duration (sec) | 60-300 | >600 | 11-794 ⚠️ |

### What the Metrics Tell Us

**Good Signs:**
- ✅ All phases complete successfully (when deps are installed)
- ✅ 7 contracts compiled from scope
- ✅ Hypothesis generation works (when eth-hash is available)
- ✅ 6/7 hypotheses have concrete targets

**Concerning Signs:**
- ❌ Dependency failure blocking recent runs
- ❌ 1 hypothesis consistently missing targets (14.3% gap)
- ❌ Zero profitable attempts across all runs
- ❌ High variation in attempt count (0-15)
- ❌ Long durations with no findings (up to 13 minutes)

---

## Testing the Fixes

### Validation Steps

1. **Verify Dependency Fix**
   ```bash
   python3 -c "from eth_utils import is_address, to_checksum_address; print(to_checksum_address('0x85b78aca6deae198fbf201c82daf6ca21942acc6'))"
   # Should print: 0x85b78ACA6DaaE198fBF201c82DAf6cA21942ACC6
   ```

2. **Run Hypothesis Generation Test**
   ```bash
   secbrain run --scope targets/originprotocol/scope.yaml \
                --program targets/originprotocol/program.json \
                --workspace targets/originprotocol/test-fix \
                --phases ingest,plan,recon,hypothesis
   
   # Check results
   cat targets/originprotocol/test-fix/phases/hypothesis.json | jq '.success'
   # Should be: true
   ```

3. **Full Run Test**
   ```bash
   secbrain run --scope targets/originprotocol/scope.yaml \
                --program targets/originprotocol/program.json \
                --workspace targets/originprotocol/full-test
   
   # Review results
   cat targets/originprotocol/full-test/run_summary.json | jq '.'
   ```

4. **Compare Metrics**
   ```bash
   # Before fix (from meta_metrics.jsonl line 23):
   # {"hypotheses_count": 0, "attempts_count": 0, ...}
   
   # After fix should show:
   tail -1 targets/originprotocol/full-test/meta_metrics.jsonl | jq '.hypotheses_count'
   # Should be: >0 (ideally 7)
   ```

---

## Next Steps

### Priority Order

1. **[IMMEDIATE]** Fix and test eth-hash dependency ← ✅ COMPLETED
2. **[HIGH]** Debug missing target mapping for 1/7 hypotheses
3. **[HIGH]** Review profit calculation logic and thresholds
4. **[MEDIUM]** Add Origin Protocol specific patterns to hypothesis generation
5. **[MEDIUM]** Enhance exploit attempt debugging and logging
6. **[LOW]** Implement long-term learning and feedback mechanisms

### Success Criteria

A successful fix should demonstrate:
- ✅ 0 dependency errors
- ✅ 7/7 hypotheses with concrete targets (or document why one is skipped)
- ✅ >0 exploit attempts generated
- ✅ Profit calculation runs successfully (even if finds 0 profit)
- ✅ Clear logging explaining why attempts were deemed non-profitable

---

## Additional Resources

### Relevant Files
- `secbrain/agents/vuln_hypothesis_agent.py` - Hypothesis generation logic
- `secbrain/agents/exploit_agent.py` - Exploit attempt generation
- `secbrain/core/profit_calculator.py` - Economic decision logic
- `targets/originprotocol/meta_metrics.jsonl` - Historical run data
- `targets/originprotocol/phases/*.json` - Per-phase outputs

### Commands
```bash
# View all hypothesis agent code
cat secbrain/secbrain/agents/vuln_hypothesis_agent.py

# Check exploit patterns
cat secbrain/secbrain/agents/exploit_pattern_db.py

# Review profit calculation
cat secbrain/secbrain/core/profit_calculator.py

# Analyze historical runs
cat targets/originprotocol/meta_metrics.jsonl | jq -s 'map({h: .hypotheses_count, a: .attempts_count, p: .attempts_with_profit, d: .total_duration_seconds})'
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-25  
**Maintainer:** SecBrain Team
