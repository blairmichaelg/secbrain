# Threshold Network Bug Bounty Target

This directory contains comprehensive resources for hunting bugs in the Threshold Network bug bounty program on Immunefi.

## 📚 Documentation Hub

**Start Here**: New to Threshold Network bounty hunting?

1. **[IMMUNEFI_RESEARCH.md](IMMUNEFI_RESEARCH.md)** ⭐ - Complete Immunefi program research
   - Program overview and background
   - Detailed scope analysis
   - Asset inventory with priorities
   - Attack surface breakdown
   - Vulnerability prioritization
   - Submission requirements
   - Bug bounty strategy

2. **[ATTACK_SURFACE_GUIDE.md](ATTACK_SURFACE_GUIDE.md)** ⭐ - Systematic testing approach
   - Testing methodology
   - Attack surfaces by component
   - Specific test cases
   - Common vulnerability patterns
   - Testing checklist

3. **[POC_TEMPLATES.md](POC_TEMPLATES.md)** ⭐ - Ready-to-use Foundry templates
   - 7 exploit templates
   - Helper functions
   - Running instructions

4. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** ⭐ - Comprehensive testing guide
   - Phase-by-phase workflow
   - Automated & manual techniques
   - Validation procedures

5. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands and tips

## Bug Bounty Information

- **Program URL**: https://immunefi.com/bug-bounty/thresholdnetwork/
- **Platform**: Immunefi
- **Max Bounty**: Up to $1,000,000 USD
- **Network**: Ethereum Mainnet
- **Contracts**: 39 smart contracts (6 critical priority)
- **Program Type**: Smart Contract Security
- **KYC**: Required only for payouts > $100,000
- **PoC**: Required for all severity levels

## 🚀 Enhanced Bug Bounty Workflow

### Step-by-Step Process

### Step-by-Step Process

#### Phase 1: Setup & Research (Day 1-2)

```bash
# 1. Read all documentation
cat IMMUNEFI_RESEARCH.md  # Complete program research
cat ATTACK_SURFACE_GUIDE.md  # Testing strategies
cat TESTING_GUIDE.md  # Phase-by-phase workflow

# 2. Install dependencies
cd /home/runner/work/secbrain/secbrain
pip install -e ".[dev]"

# 3. Set up API keys
export PERPLEXITY_API_KEY=pplx-xxxx
export GOOGLE_API_KEY=AIza-xxxx
export TOGETHER_API_KEY=your-key

# 4. Set up testing environment
export ETH_RPC_URL="https://eth.llamarpc.com"
cd targets/thresholdnetwork
```

#### Phase 2: Automated Analysis (Day 3)

```bash
# 1. Dry run (validate setup, $0 cost)
secbrain run \
  --scope scope-critical.yaml \
  --program program.json \
  --workspace workspace/dry-run \
  --dry-run

# 2. Critical contracts analysis ($5-15, 1-2 hours)
secbrain run \
  --scope scope-critical.yaml \
  --program program.json \
  --workspace workspace/critical

# 3. Research emerging patterns
secbrain research \
  --protocol "Threshold Network" \
  --contracts "TBTC,Bridge,TBTCVault" \
  --timeframe 90 \
  --output research_findings.json

# 4. Get Immunefi intelligence
secbrain immunefi intelligence --program thresholdnetwork

# 5. Review generated hypotheses
cat workspace/critical/hypotheses/hypotheses.json | \
  jq '[.[] | select(.confidence > 0.7 and .detection_priority >= 8)] | sort_by(-.confidence) | .[0:10]'
```

#### Phase 3: Priority Testing (Week 2-3)

```bash
cd instascope

# 1. Set up Foundry
forge install foundry-rs/forge-std

# 2. Copy PoC templates
cp ../POC_TEMPLATES.md test/exploits/

# 3. Test critical vulnerabilities (see TESTING_GUIDE.md for details)

# Test 1: SPV Proof Manipulation ($1M potential)
forge test --match-contract SPVProofExploit -vvvv

# Test 2: Optimistic Mint Exploit ($1M potential)  
forge test --match-contract OptimisticMintExploit -vvvv

# Test 3: Staking Reward Manipulation ($50K potential)
forge test --match-contract StakingRewardExploit -vvvv

# Test 4: Flash Loan Governance ($50K potential)
forge test --match-contract FlashLoanGovernanceExploit -vvvv

# Test 5: Cross-Chain Message Forgery ($50K potential)
forge test --match-contract CrossChainExploit -vvvv
```

#### Phase 4: PoC Development (Week 4-5)

```bash
# For each finding:
# 1. Refine exploit PoC
# 2. Measure impact (funds at risk, users affected)
# 3. Document root cause
# 4. Prepare remediation suggestions
# 5. Create professional report

# Example: Test on latest block
export FORK_BLOCK=$(cast block-number)
forge test --match-test testMyExploit -vvvv

# Generate insights
cd ..
secbrain insights --workspace workspace/critical --format html --open
```

#### Phase 5: Submission (Week 6)

```bash
# 1. Final validation
# - PoC works on latest mainnet fork
# - Impact is clearly demonstrated
# - Severity is correctly classified
# - All requirements met

# 2. Prepare submission package
# - Foundry test file
# - Detailed explanation
# - Impact assessment
# - Remediation suggestions
# - Video/screenshots (optional)

# 3. Submit via Immunefi platform
# https://immunefi.com/bug-bounty/thresholdnetwork/

# 4. Track submission status
# Expect initial response in 2-4 weeks
```

### Prerequisites

**Required Tools**:
```bash
# Foundry for testing
curl -L https://foundry.paradigm.xyz | bash
foundryup

# SecBrain for analysis
pip install -e ".[dev]"

# Optional: Additional security tools
pip install slither-analyzer mythril
```

**Required API Keys**:
```bash
# For SecBrain analysis (all FREE tier available)
export PERPLEXITY_API_KEY=pplx-xxxx     # Research integration
export GOOGLE_API_KEY=AIza-xxxx         # Advisor model
export TOGETHER_API_KEY=your-key        # Worker model

# For testing
export ETH_RPC_URL="https://eth.llamarpc.com"  # Or your preferred RPC
```

### Quick Analysis Commands

#### Dry Run (Recommended First)
```bash
secbrain run \
  --scope scope.yaml \
  --program program.json \
  --workspace workspace \
  --dry-run
```

#### Critical Contracts Only
```bash
secbrain run \
  --scope scope-critical.yaml \
  --program program.json \
  --workspace workspace
```

#### Full Analysis (All 39 Contracts)
```bash
secbrain run \
  --scope scope.yaml \
  --program program.json \
  --workspace workspace
```

#### Generate Insights
```bash
secbrain insights --workspace workspace --format html --open
```

## 🎯 Priority Targets

### Top 6 Critical Contracts

### Top 6 Critical Contracts

| # | Contract | Address | Priority | Max Bounty | Focus |
|---|----------|---------|----------|------------|-------|
| 1 | **TBTC** | 0x1808...3a88 | 10/10 | $1M | Mint, burn, token transfers |
| 2 | **TBTCVault** | 0x9C07...E3CD | 10/10 | $1M | Optimistic minting, vault operations |
| 3 | **Bridge** | 0x8d01...3234 | 10/10 | $1M | SPV proofs, deposits, redemptions |
| 4 | **WalletRegistry** | 0xfbae...8fb | 9/10 | $1M | DKG, threshold signing, operators |
| 5 | **T Token** | 0xCdF7...beE5 | 8/10 | $50K | Governance, delegation |
| 6 | **TokenStaking** | 0xf5a2...b65 | 8/10 | $50K | Staking rewards, slashing |

### Top 6 High-Value Vulnerabilities

1. **SPV Proof Manipulation** ($1M) - Forge Bitcoin transaction proofs to mint unauthorized tBTC
2. **Optimistic Mint Exploit** ($1M) - Mint tBTC without depositing Bitcoin
3. **Threshold Signature Bypass** ($1M) - Bypass threshold requirements to control Bitcoin
4. **Cross-Chain Message Forgery** ($500K) - Forge messages to Wormhole/Starknet bridges
5. **Staking Reward Manipulation** ($50K) - Inflate staking rewards via calculation errors
6. **Flash Loan Governance** ($50K) - Manipulate votes using flash-loaned tokens

## 📋 Testing Resources

### PoC Templates Available

All templates in [POC_TEMPLATES.md](POC_TEMPLATES.md):

1. **SPVProofExploit.t.sol** - Bitcoin SPV proof manipulation
2. **OptimisticMintExploit.t.sol** - Optimistic minting vulnerabilities
3. **ReentrancyExploit.t.sol** - Reentrancy attacks
4. **FlashLoanGovernance.t.sol** - Governance flash loan attacks
5. **StakingRewardExploit.t.sol** - Staking reward manipulation
6. **CrossChainExploit.t.sol** - Cross-chain message forgery
7. **ProxyUpgradeExploit.t.sol** - Proxy upgrade vulnerabilities

### 🆕 Active Hypothesis Tests

**hyp-5430acaa: ApproveAndCall Reentrancy** (December 2024)

Based on the L2WormholeGateway precedent (Oct 2023 Critical finding), comprehensive tests for approveAndCall reentrancy in recipient contracts:

**Location**: `instascope/test/exploits/`

**Quick Start**:
```bash
cd instascope
./setup_exploit_tests.sh
FOUNDRY_PROFILE=exploit_tests forge test --match-path test/exploits/ApproveAndCallReentrancyExploit.t.sol -vv
```

**Target Contracts**:
- TokenStaking - Staking and authorization (Critical priority)
- WalletRegistry - Operator management (Critical priority)  
- VendingMachine - Token migration (High priority)
- L2WormholeGateway - Regression test across all L2s (Critical if found)

**Documentation**:
- [Test Suite](instascope/test/exploits/ApproveAndCallReentrancyExploit.t.sol)
- [Full Documentation](instascope/test/exploits/README.md)
- [Quick Reference](instascope/test/exploits/QUICK_REFERENCE.md)
- [Hypothesis Analysis](hypotheses/hyp-5430acaa-approveandcall-reentrancy.md)

**Key Insight**: The vulnerability is NOT in the token contracts (TBTC, T) - they implement the intended ERC-1363 pattern. The vulnerability would be in recipient contracts that lack proper reentrancy guards.

### Attack Surface Checklist

See [ATTACK_SURFACE_GUIDE.md](ATTACK_SURFACE_GUIDE.md) for complete checklists:

**Bitcoin Bridge**:
- [ ] SPV proof verification bypass
- [ ] Deposit replay attacks
- [ ] Optimistic mint without Bitcoin
- [ ] Optimistic mint challenge bypass
- [ ] Redemption proof forgery

**Threshold Cryptography**:
- [ ] DKG manipulation
- [ ] Threshold signature bypass
- [ ] Operator collusion
- [ ] Key share exposure

**Staking & Governance**:
- [ ] Reward calculation errors
- [ ] Flash loan voting
- [ ] Timelock bypass
- [ ] Quorum manipulation

**Cross-Chain Bridges**:
- [ ] Wormhole message forgery
- [ ] Starknet state proof manipulation
- [ ] Replay attacks
- [ ] Chain ID validation

## 💰 Bounty Expectations

### Realistic Targets (6-8 weeks effort)

| Severity | Probability | Bounty Range | Expected Findings |
|----------|-------------|--------------|-------------------|
| Critical | 5-15% | $100K-$1M | 0-1 findings |
| High | 30-50% | $10K-$50K | 0-1 findings |
| Medium | 80%+ | $1K-$10K | 1-3 findings |
| Low | 100% | $100-$1K | 2-5 findings |

**Most Likely Outcome**: 1-2 medium severity findings ($1K-$10K each)

**Best Case Scenario**: 1 critical + 1-2 high + 2-3 medium ($150K-$1.1M+)

**Worst Case**: Only low severity findings or duplicates ($100-$1K)

## 🛠️ Testing Environment

### Build Contracts

The instascope directory contains all contract source code with Foundry configuration:

```bash
cd instascope

# Build all contracts
./build.sh

# Build specific contract
FOUNDRY_PROFILE=contract_TBTC_1808 forge build

# Test specific contract (if tests exist)
FOUNDRY_PROFILE=contract_TBTC_1808 forge test
```

## Important Notes

### Testing Rules
- ⚠️ **NEVER test on mainnet or public testnets**
- ✅ Always use local forks for testing
- ✅ Proof of Concept required for all submissions
- ✅ Follow Immunefi safe harbor rules

### Out of Scope
- Oracle manipulation (unless direct oracle manipulation)
- Governance attacks requiring 51% control
- Attacks requiring leaked credentials
- Attacks requiring privileged address access
- Testing with third-party systems

## Optimization Tips

Based on OPTIMIZATION-GUIDE.md:

1. **Model Selection**:
   - Worker: DeepSeek-Chat (fast, cost-effective)
   - Advisor: Gemini 2.0 Flash Exp (quick reviews)
   - Research: Perplexity Sonar (real-time exploit data)

2. **Connection Pooling**: Already configured for HTTP clients

3. **Caching Strategy**:
   - Severity context: 7 days TTL
   - Attack vectors: 2 days TTL
   - Market conditions: 1 hour TTL

4. **Rate Limiting**: 10 req/min for research calls

## Expected Workflow

1. **Recon Phase**: 
   - Compile all 39 contracts
   - Extract ABIs and function signatures
   - Map contract relationships

2. **Hypothesis Phase**:
   - Generate vulnerability hypotheses
   - Focus on high-value targets (TBTC, Bridge, Staking)
   - Prioritize critical severity patterns

3. **Exploit Phase**:
   - Test hypotheses on local forks
   - Measure profitability
   - Validate exploitation paths

4. **Triage Phase**:
   - Validate findings
   - Calculate severity
   - Assess impact

5. **Report Phase**:
   - Generate PoC
   - Document exploit steps
   - Submit to Immunefi

## Directory Structure

```
targets/thresholdnetwork/
├── README.md                    # This file
├── program.json                 # Bug bounty program details
├── scope.yaml                   # Contract scope configuration
├── instascope/                  # Source code from Immunefi Instascope
│   ├── foundry.toml            # Foundry profiles for each contract
│   ├── build.sh                # Build all contracts
│   ├── src/                    # Contract source code (39 contracts)
│   └── README.md               # Instascope documentation
└── workspace/                   # Analysis workspace (created on first run)
    ├── logs/                   # Run logs
    ├── phases/                 # Phase outputs
    ├── hypotheses/             # Generated hypotheses
    ├── findings/               # Discovered findings
    └── reports/                # Generated reports
```

## Troubleshooting

### Common Issues

1. **eth-hash backend missing**:
   ```bash
   pip install "eth-hash[pycryptodome]"
   ```

2. **Foundry compilation errors**:
   - Ensure you're in the instascope directory
   - Use the correct profile: `FOUNDRY_PROFILE=contract_<name>_<addr> forge build`
   - Check Solidity version matches the contract

3. **RPC rate limiting**:
   - Use multiple RPC endpoints (configured in scope.yaml)
   - Add your own Alchemy/Infura endpoint if needed

4. **Memory issues**:
   - Reduce concurrent contract analysis
   - Focus on high-priority contracts first
   - Clear workspace between runs if needed

## Resources

- **Immunefi Program**: https://immunefi.com/bug-bounty/thresholdnetwork/
- **Threshold Docs**: https://docs.threshold.network/
- **tBTC Docs**: https://docs.threshold.network/applications/tbtc-v2
- **GitHub**: https://github.com/threshold-network
- **Discord**: https://discord.gg/threshold

## Next Steps

1. Run a dry-run to validate configuration
2. Review the generated hypotheses
3. Focus on critical severity patterns
4. Test on local forks only
5. Document any findings with PoC
6. Submit validated findings to Immunefi

---

**Last Updated**: 2025-12-25
**SecBrain Version**: Latest
**Target Network**: Ethereum Mainnet (Chain ID: 1)
