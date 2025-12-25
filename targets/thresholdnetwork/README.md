# Threshold Network Bug Bounty Target

This directory contains the configuration and setup for running SecBrain against the Threshold Network bug bounty program on Immunefi.

## Bug Bounty Information

- **Program URL**: https://immunefi.com/bug-bounty/thresholdnetwork/
- **Platform**: Immunefi
- **Max Bounty**: Up to $1,000,000 USD
- **Network**: Ethereum Mainnet
- **Contracts**: 39 smart contracts

## Quick Start

### Prerequisites

1. Install dependencies (from repository root):
   ```bash
   cd /home/runner/work/secbrain/secbrain
   pip install -e ".[dev]"
   ```

2. Set up API keys:
   ```bash
   # Required for research integration
   export PERPLEXITY_API_KEY=pplx-xxxx
   
   # Required for advisor model
   export GOOGLE_API_KEY=AIza-xxxx
   
   # Required for worker model (choose one)
   export TOGETHER_API_KEY=your-together-key
   # OR
   export OPENROUTER_API_KEY=your-openrouter-key
   # OR
   export OPENAI_API_KEY=your-openai-key
   ```

### Run Analysis

#### Dry Run (Recommended First)
```bash
secbrain run \
  --scope targets/thresholdnetwork/scope.yaml \
  --program targets/thresholdnetwork/program.json \
  --workspace targets/thresholdnetwork/workspace \
  --dry-run
```

#### Full Analysis
```bash
secbrain run \
  --scope targets/thresholdnetwork/scope.yaml \
  --program targets/thresholdnetwork/program.json \
  --workspace targets/thresholdnetwork/workspace
```

#### Generate Insights
```bash
secbrain insights --workspace targets/thresholdnetwork/workspace --format html --open
```

## Contract Overview

The Threshold Network consists of 39 deployed contracts focused on:

### Core Components
- **tBTC Bridge**: Bitcoin bridge contracts (TBTC, TBTCVault, Bridge, etc.)
- **Threshold Cryptography**: Core threshold signature and encryption functionality
- **Token System**: T token (merger of KEEP and NU tokens)
- **Staking**: TokenStaking, RebateStaking contracts
- **Governance**: TokenholderGovernor, BridgeGovernance, WalletRegistryGovernance

### Critical Contracts
1. **TBTC** (0x18084fbA666a33d37592fA2633fD49a74DD93a88) - Main tBTC token
2. **TBTCVault** (0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD) - tBTC vault
3. **Bridge** (0x8d014903bf7867260584d714e11809fea5293234) - Bridge logic
4. **T Token** (0xCdF7028ceAB81fA0C6971208e83fa7872994beE5) - Threshold token
5. **TokenStaking** (0xf5a2ccfea213cb3ff0799e0c33ea2fa3da7cbb65) - Staking contract
6. **WalletRegistry** (0xfbae130e06bbc8ca198861beecae6e2b830398fb) - Wallet registry

## Focus Areas

Based on the bug bounty program, prioritize:

1. **Direct theft of user funds** (Critical - up to $1M)
2. **Permanent freezing of funds** (Critical)
3. **Protocol insolvency** (Critical)
4. **Bridge vulnerabilities** (tBTC bridge security)
5. **Cross-chain attacks** (Starknet, Wormhole bridges)
6. **Governance exploits** (Voting, proposals)
7. **Staking vulnerabilities** (Rewards, slashing)
8. **Proxy pattern issues** (Many TransparentUpgradeableProxy contracts)

## Building Contracts

The instascope directory contains all contract source code with Foundry configuration.

```bash
cd targets/thresholdnetwork/instascope

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
