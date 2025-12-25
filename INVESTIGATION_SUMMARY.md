# Origin Protocol Run Investigation Summary

**Investigation Date:** 2025-12-25  
**Run Context:** Based on problem statement describing run with 25 hypotheses, 6 attempts, 0 findings

---

## Quick Summary

The investigation revealed:

1. **✅ FIXED:** Critical dependency issue preventing hypothesis generation
2. **⚠️ ANALYSIS PROVIDED:** Comprehensive guidance on zero-findings pattern
3. **📊 DATA ANALYZED:** Historical run metrics from meta_metrics.jsonl
4. **📝 DOCUMENTATION ADDED:** Troubleshooting and analysis guides

---

## What Was the Issue?

### Primary Problem: Missing Cryptographic Backend

The most recent runs failed during hypothesis generation due to missing `eth-hash` backend:

```
Error: None of these hashing backends are installed: ['pycryptodome', 'pysha3'].
Install with `python -m pip install "eth-hash[pycryptodome]"`.
```

**Impact:** This caused:
- Hypothesis phase to fail completely
- 0 hypotheses generated
- 0 exploit attempts
- 0 findings (by extension)

### Secondary Pattern: Zero Profitability

Historical data shows that even when hypotheses ARE generated successfully:
- 7 hypotheses generated consistently
- 6/7 have concrete targets (85.7% coverage)
- 0-15 exploit attempts per run
- **0 attempts with detected profit across ALL runs**
- Economic decision: SKIP in all cases

---

## What Was Fixed?

### 1. Dependency Fix ✅

**Added to `requirements.in` and `pyproject.toml`:**
```python
eth-hash[pycryptodome]>=0.7.0
```

**Regenerated:**
- `requirements.txt` (with SHA256 hashes)
- `requirements-hashed.txt`
- `requirements.lock`
- `requirements-dev.txt`

**Validation:**
Created test script: `scripts/test_eth_hash_fix.py`

```bash
# Test the fix
python3 scripts/test_eth_hash_fix.py
# Output: ✅ All tests passed! eth-hash backend is working correctly.
```

### 2. Documentation Added 📝

**Created comprehensive guidance documents:**

1. **`RUN_ANALYSIS_GUIDANCE.md`** (Main Analysis Document)
   - Root cause analysis of dependency and profitability issues
   - Detailed recommendations for improving hypothesis quality
   - Protocol-specific attack vectors to consider
   - Testing and validation procedures
   - Success criteria and metrics interpretation

2. **Updated `docs/TROUBLESHOOTING.md`**
   - Added "Dependency Issues" section
   - Documented eth-hash backend error and solution
   - Cross-referenced analysis document

3. **Created `scripts/test_eth_hash_fix.py`**
   - Automated test for eth-hash backend installation
   - Validates address checksumming works correctly

---

## Understanding the Data Discrepancy

The problem statement mentioned:
- **25 hypotheses generated**
- **6 attempts**

The actual data shows:
- **7 hypotheses** (when working)
- **0-15 attempts** (varying per run)

**Possible explanations:**
1. Problem statement may refer to a different environment/run
2. Numbers may be from an aggregated/historical view
3. System may have been configured differently

**Key insight:** Regardless of exact numbers, the pattern is consistent:
- **0 profitable attempts across all observed runs**
- This is the core issue to investigate

---

## Next Steps for the User

### Immediate (Required)

1. **Apply the dependency fix:**
   ```bash
   cd secbrain
   pip install "eth-hash[pycryptodome]"
   # OR reinstall from updated requirements
   pip install -r requirements.txt
   ```

2. **Validate the fix:**
   ```bash
   python3 scripts/test_eth_hash_fix.py
   ```

3. **Run a test hypothesis generation:**
   ```bash
   secbrain run --scope targets/originprotocol/scope.yaml \
                --program targets/originprotocol/program.json \
                --workspace targets/originprotocol/test-fix \
                --phases ingest,plan,recon,hypothesis
   ```

4. **Check results:**
   ```bash
   cat targets/originprotocol/test-fix/phases/hypothesis.json | jq '.success'
   # Should output: true
   
   cat targets/originprotocol/test-fix/phases/hypothesis.json | jq '.hypotheses | length'
   # Should output: >0 (likely 7)
   ```

### Short-term (Recommended)

5. **Review hypothesis quality:**
   - Check which patterns are being generated
   - Verify they align with Origin Protocol's architecture
   - See [RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md#short-term-improvements) Section 4

6. **Debug profit calculation:**
   - Review why 0 attempts are deemed profitable
   - Check gas estimates and profit thresholds
   - See [RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md#short-term-improvements) Section 5

7. **Analyze missing target mapping:**
   - Investigate why 1/7 hypotheses lacks concrete target
   - Check proxy contract resolution
   - See [RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md#root-cause-analysis) Section 2

### Long-term (Optional)

8. **Protocol-specific enhancements:**
   - Add Origin Protocol specific attack patterns
   - Enhance rebasing token mechanics testing
   - Improve AMO strategy vulnerability detection

9. **Implement feedback loops:**
   - Learn from historical run data
   - Refine hypothesis generation based on success patterns
   - Build corpus of known-good exploit patterns

---

## How to Use the Analysis Document

The main analysis document **[RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md)** provides:

### Section 1: Executive Summary
Quick overview of observed patterns

### Section 2: Root Cause Analysis
Deep dive into three main issues:
1. Dependency Issue (✅ FIXED)
2. Hypothesis Quality (⚠️ needs investigation)
3. Zero Profitability (⚠️ needs investigation)

### Section 3: Recommendations
10 prioritized actions with specific commands and code locations

### Section 4: Run Metrics Interpretation
Table showing what's normal vs. concerning

### Section 5: Testing the Fixes
Step-by-step validation procedures

### Section 6: Next Steps
Priority-ordered action items with success criteria

---

## Questions to Investigate Further

Based on the analysis, here are key questions to answer:

1. **Why are all exploit attempts non-profitable?**
   - Are gas estimates too conservative?
   - Is profit threshold too high?
   - Are we missing flash loan profit opportunities?
   - Is the test environment missing necessary state?

2. **Why does 1/7 hypotheses always lack a target?**
   - Which hypothesis pattern is failing?
   - Is it related to proxy contract complexity?
   - Should we skip this pattern for Origin Protocol?

3. **Are the generated hypotheses appropriate?**
   - Do they align with Origin Protocol's actual risk surface?
   - Should we add protocol-specific patterns?
   - Are we testing the right contracts?

4. **Is Origin Protocol simply secure?**
   - Has it been heavily audited?
   - Are the tested contracts battle-tested?
   - Should we focus on different attack vectors?

---

## Success Metrics

After applying the fixes, success looks like:

| Metric | Before Fix | After Fix Target |
|--------|-----------|------------------|
| Dependency Errors | ❌ 1 per run | ✅ 0 |
| Hypotheses Generated | ❌ 0 | ✅ 7 |
| Target Coverage | N/A | ✅ 100% (or document reason) |
| Attempts Generated | ❌ 0 | ✅ >0 |
| Profitable Attempts | ❌ 0 | ⚠️ TBD (may still be 0 if protocol is secure) |
| Clear Logging | ⚠️ Minimal | ✅ Explains economic decisions |

**Note:** Even with all fixes, 0 profitable attempts may be legitimate if Origin Protocol has no exploitable vulnerabilities in the tested contracts.

---

## Files Changed

```
Modified:
  secbrain/requirements.in          - Added eth-hash[pycryptodome]
  secbrain/pyproject.toml           - Added eth-hash[pycryptodome]
  docs/TROUBLESHOOTING.md           - Added dependency troubleshooting

Created:
  RUN_ANALYSIS_GUIDANCE.md          - Comprehensive analysis and guidance
  scripts/test_eth_hash_fix.py      - Validation test script

Regenerated:
  secbrain/requirements.txt         - With new dependency and hashes
  secbrain/requirements-hashed.txt  - Duplicate with hashes
  secbrain/requirements.lock        - Lock file
  secbrain/requirements-dev.txt     - Dev dependencies with hashes
```

---

## Additional Resources

- **Main Analysis:** [RUN_ANALYSIS_GUIDANCE.md](RUN_ANALYSIS_GUIDANCE.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Test Script:** [scripts/test_eth_hash_fix.py](scripts/test_eth_hash_fix.py)
- **Run Data:** `targets/originprotocol/meta_metrics.jsonl`

---

**Last Updated:** 2025-12-25  
**Issue:** Investigation of Origin Protocol run with 0 findings  
**Status:** ✅ Primary issue fixed, guidance provided for secondary issues
