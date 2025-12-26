# Kiln Staking - Quick Reference Guide

## 🚀 Fast Start (30 seconds)

```bash
# 1. Set your API key
export MAINNET_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"

# 2. Run setup
cd targets/kiln-staking
./setup.sh

# 3. Start hunting!
cd workspace/staking-contracts
```

## 🎯 Three Valid Targets

| Target | Severity | Time | Template |
|--------|----------|------|----------|
| **Fee Extraction DoS** | Critical | 1.5h | `FeeExtractionDoS.t.sol` |
| **1-Wei Rounding Error** | Medium | 1h | `RoundingErrorDoS.t.sol` |
| **Proxy Re-init** | Medium | 1h | `InitializableVulnerability.t.sol` |

## 📋 Essential Commands

### Setup & Build
```bash
# Clone target
git clone https://github.com/kilnfi/staking-contracts
cd staking-contracts
git checkout f33eb8dc37fab40217dbe1e69853ca3fcd884a2d

# Install dependencies
forge install

# Build
forge build
```

### Testing
```bash
# Run all tests
forge test --fork-url $MAINNET_RPC_URL -vvv

# Run specific test
forge test --fork-url $MAINNET_RPC_URL --match-test testFeeRecipientDoS -vvvv

# Run contract tests
forge test --fork-url $MAINNET_RPC_URL --match-contract FeeExtractionDoSTest -vv
```

### Research Commands
```bash
# Get contract owner
cast call 0xdc71affc862fceb6ad32be58e098423a7727bebd "owner()(address)" --rpc-url $MAINNET_RPC_URL

# Get implementation address (EIP-1967)
cast storage 0xdc71affc862fceb6ad32be58e098423a7727bebd 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc --rpc-url $MAINNET_RPC_URL

# Check fee recipient
cast call 0xdc71affc862fceb6ad32be58e098423a7727bebd "feeRecipient()(address)" --rpc-url $MAINNET_RPC_URL

# Get contract code
cast code 0xdc71affc862fceb6ad32be58e098423a7727bebd --rpc-url $MAINNET_RPC_URL

# Decode transaction
cast tx <tx-hash> --rpc-url $MAINNET_RPC_URL
```

## 🔍 Research Checklist

### Phase 1: Reconnaissance (30 min)
- [ ] Read contract source code
- [ ] Identify all withdrawal functions
- [ ] Locate fee recipient mechanism
- [ ] Check share calculation logic
- [ ] Review initialization pattern
- [ ] Map out access control

### Phase 2: Audit Review (30 min)
- [ ] Download Halborn audit PDF
- [ ] Download Spearbit audit PDF
- [ ] Search for "fee", "DoS", "revert", "rounding", "initializ"
- [ ] Document all known issues
- [ ] Identify gaps in audit coverage

### Phase 3: PoC Development (1 hour)
- [ ] Select vulnerability template
- [ ] Customize for target contract
- [ ] Write test setup
- [ ] Implement attack scenario
- [ ] Verify impact
- [ ] Document findings

### Phase 4: Report Writing (30 min)
- [ ] Use REPORT_TEMPLATE.md
- [ ] Explain why it's not a known issue
- [ ] Provide working PoC
- [ ] Suggest fixes
- [ ] Set appropriate severity

## 🚫 Known Issues (AVOID THESE)

❌ **Will be rejected:**
- Malicious operator bypass attacks
- Operator can steal funds
- Front-running by operators
- Withdrawal triggering (if funds go to right address)
- Uninitialized implementation (for implementation contracts)

✅ **Valid findings:**
- Protocol logic errors (no malicious operator)
- Fee/Withdrawal DoS affecting user principal
- Griefing attacks (1-wei, etc.)
- Proxy re-initialization

## 🎯 Target Contract Info

| Property | Value |
|----------|-------|
| **Address** | `0xdc71affc862fceb6ad32be58e098423a7727bebd` |
| **Network** | Ethereum Mainnet |
| **Repository** | [kilnfi/staking-contracts](https://github.com/kilnfi/staking-contracts) |
| **Commit** | `f33eb8dc37fab40217dbe1e69853ca3fcd884a2d` |
| **Bug Bounty** | [HackenProof Program](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts) |

## 📊 Severity & Rewards

| Severity | Impact | Estimated Reward |
|----------|--------|------------------|
| **Critical** | Permanent fund freeze | $30k - $50k+ |
| **High** | Temporary fund freeze | $15k - $25k |
| **Medium** | Griefing, re-init | $5k - $10k |
| **Low** | Informational | $1k - $2.5k |

## 🛠️ Useful Patterns to Search

### In Source Code
```bash
# Search for fee transfers
grep -r "transfer.*fee" src/
grep -r "feeRecipient" src/

# Search for share calculations
grep -r "totalShares" src/
grep -r "/ totalAssets" src/

# Search for initialization
grep -r "initialize" src/
grep -r "initializer" src/
```

### In Tests
```bash
# Look at existing tests for patterns
find test/ -name "*.t.sol" -exec grep -l "withdraw\|fee\|share" {} \;
```

## 📚 Key Files to Review

1. **Main Contract**: Look for the primary staking contract
2. **Proxy**: If using proxy pattern, review proxy implementation
3. **Fee Management**: Any fee-related contracts/libraries
4. **Share Accounting**: ERC4626-like share calculation
5. **Access Control**: Owner/admin functions

## ⚡ Time Budget (2.5 hours total)

| Phase | Time | Activities |
|-------|------|------------|
| **Setup** | 15 min | Clone, install, configure |
| **Recon** | 30 min | Read code, understand flow |
| **Audit Review** | 30 min | Check for duplicates |
| **PoC Development** | 1 hour | Write and test exploit |
| **Report** | 30 min | Use template, submit |
| **Buffer** | 15 min | Final checks |

## 🔗 Important Links

- [HackenProof Program](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts)
- [Submit Report](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts/reports/new)
- [Target Repository](https://github.com/kilnfi/staking-contracts)
- [Audits Directory](https://github.com/kilnfi/staking-contracts/tree/main/audits)
- [Foundry Book](https://book.getfoundry.sh/)
- [OpenZeppelin Docs](https://docs.openzeppelin.com/)

## 💡 Pro Tips

1. **Test on mainnet fork**: Always use real state
2. **Check gas costs**: Unrealistic gas = invalid PoC
3. **Quantify impact**: "10,000 users affected" > "users affected"
4. **Explain differences**: Why your bug ≠ known issues
5. **Professional tone**: Clear, concise, respectful
6. **Respond quickly**: Triagers move fast
7. **Accept feedback**: Learn from rejections

## 🆘 Troubleshooting

### Forge build fails
```bash
# Clean and rebuild
forge clean
forge build --force
```

### Fork connection fails
```bash
# Verify RPC URL
echo $MAINNET_RPC_URL

# Test connection
cast block-number --rpc-url $MAINNET_RPC_URL
```

### Test reverts unexpectedly
```bash
# Increase verbosity
forge test --fork-url $MAINNET_RPC_URL -vvvvv

# Check trace
forge test --fork-url $MAINNET_RPC_URL --match-test <test> --trace
```

### Can't find function
```bash
# Get contract ABI
cast abi-encode <function-sig>

# Inspect contract
cast interface 0xdc71affc862fceb6ad32be58e098423a7727bebd --rpc-url $MAINNET_RPC_URL
```

## 📝 Next Steps After Finding

1. ✅ Complete all checklist items
2. ✅ Use REPORT_TEMPLATE.md
3. ✅ Attach working PoC
4. ✅ Set correct severity
5. ✅ Submit on HackenProof
6. ✅ Monitor for responses
7. ✅ Respond within 48h to questions

---

**Good luck hunting! 🎯**

*For full guide, see: [README.md](README.md)*  
*For report template, see: [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)*  
*For submission strategy, see: [SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)*
