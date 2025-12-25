# Threshold Network - Quick Reference Card

**Target**: Threshold Network Bug Bounty  
**Platform**: Immunefi  
**Max Bounty**: $1,000,000 USD  
**Contracts**: 39 (15 critical)

## 🚀 Quick Commands

```bash
# Navigate to target
cd targets/thresholdnetwork

# Validate configuration
python validate_config.py
# OR
secbrain validate --scope scope.yaml --program program.json

# Dry-run (no API calls, $0 cost)
./run-threshold.sh dry-run

# Critical contracts only ($5-15, 1-2 hours)
./run-threshold.sh critical

# Full analysis ($10-30, 2-4 hours)
./run-threshold.sh full

# Generate insights
secbrain insights --workspace workspace --format html --open
```

## 📋 Files

| File | Purpose |
|------|---------|
| `program.json` | Bug bounty program details |
| `scope.yaml` | All 39 contracts |
| `scope-critical.yaml` | 15 critical contracts |
| `README.md` | Full documentation |
| `OPTIMIZATION_CHECKLIST.md` | Pre-run checklist |
| `SETUP_COMPLETE.md` | Setup summary |
| `validate_config.py` | Config validator |
| `run-threshold.sh` | Run script |

## 🎯 Priority Contracts

**Highest Priority** (tBTC Core):
- TBTC (0x1808...)
- TBTCVault (0x9C07...)
- Bridge (0x8d01...)

**High Priority** (Tokens & Staking):
- T Token (0xCdF7...)
- TokenStaking (0xf5a2...)
- WalletRegistry (0xfbae...)

**Medium-High** (Governance & Bridges):
- TokenholderGovernor (0xd101...)
- StarknetTokenBridge (0xf39d...)
- BTCDepositorWormhole (0x9a52...)

## 💰 Focus Areas

1. Direct theft of funds → **$1M**
2. Permanent freezing → **$1M**
3. Protocol insolvency → **$1M**
4. Bridge vulnerabilities → **High**
5. Cross-chain attacks → **High**
6. Governance exploits → **Medium-High**

## 🔧 API Keys Required

```bash
export PERPLEXITY_API_KEY=pplx-xxxx     # Research
export GOOGLE_API_KEY=AIza-xxxx         # Advisor
export TOGETHER_API_KEY=your-key        # Worker (recommended)
```

## 📊 Expected Results

- **Hypotheses**: 10-20 generated
- **Target Coverage**: 85%+
- **Run Time**: 2-4 hours (full), 1-2 hours (critical)
- **API Cost**: $10-30 (full), $5-15 (critical), $0 (dry-run)

## ⚠️ Safety Rules

✅ **DO**:
- Use local forks for testing
- Include PoC in submissions
- Follow Immunefi safe harbor
- Report responsibly

❌ **DON'T**:
- Test on mainnet
- Test on public testnets
- Exploit for personal gain
- Disclose publicly before fix

## 🔍 Debugging

```bash
# Check logs
cat workspace/logs/*.jsonl | jq '.'

# View findings
cat workspace/findings/findings.json | jq '.'

# Check hypotheses
cat workspace/hypotheses/hypotheses.json | jq '.'

# Review meta metrics
cat workspace/meta_metrics.jsonl | jq '.'
```

## 📚 Resources

- **Program**: https://immunefi.com/bug-bounty/thresholdnetwork/
- **Docs**: https://docs.threshold.network/
- **Discord**: https://discord.gg/threshold
- **Local Docs**: See README.md

## 🎉 Ready to Start?

1. Set API keys
2. Run: `./run-threshold.sh dry-run`
3. Review output
4. Run: `./run-threshold.sh critical` or `full`
5. Check findings in `workspace/findings/`
6. Submit to Immunefi

---

**Last Updated**: 2025-12-25  
**Setup Status**: ✅ COMPLETE  
**All Files Validated**: ✅ YES
