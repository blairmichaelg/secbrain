# Kiln Staking Contracts - Getting Started

Welcome to the Kiln/MetaMask Validator Staking Smart Contracts vulnerability hunting workflow!

## 📚 What's Included

This directory provides everything you need to hunt for valid vulnerabilities in the Kiln staking contracts and submit them to the HackenProof bug bounty program.

### Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| **[README.md](README.md)** | Main guide with setup and targets | 10 min |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Fast command reference | 5 min |
| **[REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)** | Professional report format | 5 min |
| **[SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)** | How to avoid rejections | 10 min |
| **[RESEARCH_NOTES.md](RESEARCH_NOTES.md)** | Advanced techniques & patterns | 15 min |

### Code Templates

| File | Vulnerability | Severity | Details |
|------|---------------|----------|---------|
| **[test/FeeExtractionDoS.t.sol](test/FeeExtractionDoS.t.sol)** | Fee recipient DoS | Critical | Freeze user funds |
| **[test/RoundingErrorDoS.t.sol](test/RoundingErrorDoS.t.sol)** | 1-wei rounding | Medium | Griefing attack |
| **[test/InitializableVulnerability.t.sol](test/InitializableVulnerability.t.sol)** | Re-initialization | Medium | Ownership takeover |

### Configuration Files

| File | Purpose |
|------|---------|
| **[foundry.toml](foundry.toml)** | Foundry configuration for mainnet forking |
| **[.env.example](.env.example)** | Environment variables template |
| **[setup.sh](setup.sh)** | Automated setup script |
| **[.gitignore](.gitignore)** | Ignore workspace and build artifacts |

## 🚀 Quick Start (3 Steps)

### 1. Set Your API Key
```bash
export MAINNET_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
```
Get a free API key from [Alchemy](https://www.alchemy.com/)

### 2. Run Setup
```bash
cd targets/kiln-staking
./setup.sh
```

### 3. Start Hunting
```bash
cd workspace/staking-contracts
forge test --fork-url $MAINNET_RPC_URL -vvv
```

## 📖 Learning Path

### For Beginners (First Time Bug Hunter)

1. **Day 1: Learn the Basics** (2 hours)
   - Read [README.md](README.md) completely
   - Understand the three vulnerability targets
   - Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
   - Skim [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)

2. **Day 2: Setup & Explore** (2 hours)
   - Run `./setup.sh` to set up your environment
   - Read the target contract source code
   - Try running the template tests
   - Practice with `cast` commands from QUICK_REFERENCE

3. **Day 3: First Hunt** (3 hours)
   - Pick one vulnerability target
   - Customize the PoC template
   - Test on mainnet fork
   - Write a practice report

### For Intermediate (Some Experience)

1. **Preparation** (30 min)
   - Review [SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)
   - Check previous audits for duplicates
   - Set up environment with `./setup.sh`

2. **Research** (1 hour)
   - Read contract source thoroughly
   - Map attack surface
   - Identify vulnerable patterns
   - Reference [RESEARCH_NOTES.md](RESEARCH_NOTES.md)

3. **Exploit Development** (1 hour)
   - Choose the most promising target
   - Customize PoC template
   - Test thoroughly on fork
   - Verify impact

4. **Reporting** (30 min)
   - Use [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)
   - Follow [SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)
   - Submit on HackenProof

### For Advanced (Experienced Hunter)

1. **Fast Track** (2.5 hours total)
   - Skim [README.md](README.md) for context
   - Run `./setup.sh`
   - Deep dive into contracts (1 hour)
   - Develop PoC for highest-impact finding (1 hour)
   - Write and submit report (30 min)

2. **Pro Tips**
   - Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands
   - Leverage [RESEARCH_NOTES.md](RESEARCH_NOTES.md) for advanced patterns
   - Cross-reference [SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md) before submitting

## 🎯 Target Information

| Property | Value |
|----------|-------|
| **Contract Address** | `0xdc71affc862fceb6ad32be58e098423a7727bebd` |
| **Network** | Ethereum Mainnet |
| **Repository** | [kilnfi/staking-contracts](https://github.com/kilnfi/staking-contracts) |
| **Target Commit** | `f33eb8dc37fab40217dbe1e69853ca3fcd884a2d` |
| **Bug Bounty Program** | [HackenProof](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts) |
| **Max Bounty** | $50,000+ (Critical) |

## ⚠️ Important Warnings

### ❌ Don't Submit These (Known Issues)
- Malicious operator attacks
- Operator fund theft
- Front-running by operators
- Withdrawal triggering (if funds go to right address)
- Uninitialized implementations

### ✅ Do Submit These
- Protocol logic errors (no malicious operator needed)
- Fee/Withdrawal DoS affecting user principal
- Griefing attacks (1-wei, etc.)
- Proxy re-initialization vulnerabilities

## 📊 Expected Outcomes

### Time Investment
- **Setup**: 15 minutes
- **Research**: 1-2 hours
- **PoC Development**: 1-2 hours
- **Report Writing**: 30 minutes
- **Total**: 2.5-4 hours

### Success Rates
- **Critical findings**: Rare but $30k-$50k+
- **High findings**: Moderate chance, $15k-$25k
- **Medium findings**: Good chance, $5k-$10k
- **Acceptance rate**: ~10-20% for quality submissions

### Learning Outcomes
Even if you don't find a new vulnerability:
- ✅ Learn smart contract security patterns
- ✅ Practice fork testing with Foundry
- ✅ Understand DoS and griefing attacks
- ✅ Gain experience with proxy patterns
- ✅ Learn professional report writing

## 🆘 Need Help?

### Common Issues

**"Forge not found"**
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

**"Fork connection failed"**
```bash
# Check your RPC URL is set
echo $MAINNET_RPC_URL

# Test connection
cast block-number --rpc-url $MAINNET_RPC_URL
```

**"Test reverts unexpectedly"**
```bash
# Increase verbosity to see details
forge test --fork-url $MAINNET_RPC_URL -vvvvv
```

### Where to Get Help

1. **Foundry Docs**: [book.getfoundry.sh](https://book.getfoundry.sh/)
2. **HackenProof Support**: Via platform messaging
3. **SecBrain Issues**: [GitHub Issues](https://github.com/blairmichaelg/secbrain/issues)

## 📝 Checklist

Before you start:
- [ ] Read [README.md](README.md)
- [ ] Get Alchemy API key
- [ ] Set `MAINNET_RPC_URL` environment variable
- [ ] Run `./setup.sh`
- [ ] Verify Foundry is installed
- [ ] Review [SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)

Before you submit:
- [ ] Check previous audits for duplicates
- [ ] Verify finding is not in Known Issues
- [ ] Test PoC on mainnet fork successfully
- [ ] Use [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)
- [ ] Set appropriate severity
- [ ] Explain why it's different from known issues
- [ ] Include all necessary files and documentation

## 🔗 Quick Links

- [HackenProof Program](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts)
- [Submit Report](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts/reports/new)
- [Target Repository](https://github.com/kilnfi/staking-contracts)
- [Foundry Book](https://book.getfoundry.sh/)

## 📞 Feedback

Found this guide helpful? Have suggestions for improvement? Open an issue or PR in the [SecBrain repository](https://github.com/blairmichaelg/secbrain).

---

**Good luck with your hunt! 🎯**

*Remember: Quality over quantity. One well-researched, properly documented finding is worth more than ten rushed submissions.*

---

*Last updated: 2024-12-26*
