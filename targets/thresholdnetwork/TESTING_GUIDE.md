# Threshold Network Testing Guide

**Comprehensive testing strategies for Threshold Network bug bounty**  
**Last Updated**: December 25, 2024

## Table of Contents

- [Overview](#overview)
- [Testing Environment Setup](#testing-environment-setup)
- [Testing Strategy](#testing-strategy)
- [Phase-by-Phase Testing](#phase-by-phase-testing)
- [Automated Testing with SecBrain](#automated-testing-with-secbrain)
- [Manual Testing Techniques](#manual-testing-techniques)
- [Validation and Verification](#validation-and-verification)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

This guide provides a structured approach to testing the Threshold Network for vulnerabilities. It combines automated analysis with SecBrain and manual testing techniques for maximum coverage.

### Testing Objectives

1. **Identify Critical Vulnerabilities**: Focus on $100K-$1M bounties
2. **Validate Hypotheses**: Test AI-generated vulnerability hypotheses
3. **Discover Edge Cases**: Find issues missed by automated tools
4. **Build Proof-of-Concepts**: Create reproducible exploits
5. **Professional Reporting**: Document findings for Immunefi submission

### Time Allocation

| Phase | Time | Focus |
|-------|------|-------|
| Setup & Learning | 1-2 days | Environment, documentation, contracts |
| Automated Analysis | 2-4 hours | SecBrain hypothesis generation |
| Priority Testing | 1-2 weeks | Critical contracts and functions |
| Extended Testing | 1-2 weeks | Medium priority, edge cases |
| PoC Development | 3-5 days | Exploit refinement |
| Documentation | 2-3 days | Report preparation |

**Total**: 4-6 weeks for comprehensive audit

---

## Testing Environment Setup

### Prerequisites

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install SecBrain
cd /home/runner/work/secbrain/secbrain
pip install -e ".[dev]"

# Install additional tools
pip install slither-analyzer mythril
npm install -g @crytic/echidna
```

### Environment Variables

```bash
# Required for SecBrain
export PERPLEXITY_API_KEY="pplx-xxxx"
export GOOGLE_API_KEY="AIza-xxxx"
export TOGETHER_API_KEY="your-key"

# Required for testing
export ETH_RPC_URL="https://eth.llamarpc.com"
export FORK_BLOCK=18500000  # Recent block number

# Optional: Additional RPC endpoints
export ALCHEMY_MAINNET_RPC="https://eth-mainnet.g.alchemy.com/v2/YOUR-KEY"
export INFURA_MAINNET_RPC="https://mainnet.infura.io/v3/YOUR-KEY"
```

### Workspace Organization

```bash
cd targets/thresholdnetwork

# Create testing directories
mkdir -p testing/{manual,automated,pocs,findings}

# Directory structure:
# testing/
# ├── manual/          # Manual test scripts
# ├── automated/       # SecBrain outputs
# ├── pocs/           # Proof-of-concept exploits
# └── findings/       # Documented findings
```

---

## Testing Strategy

### Layered Testing Approach

#### Layer 1: Automated Analysis (SecBrain)
- **Tools**: SecBrain CLI
- **Coverage**: All 39 contracts
- **Time**: 2-4 hours
- **Output**: 15-25 hypotheses
- **Cost**: $10-30 in API calls

#### Layer 2: Static Analysis
- **Tools**: Slither, Semgrep, Mythril
- **Coverage**: Critical contracts (6 contracts)
- **Time**: 4-8 hours
- **Output**: Potential vulnerabilities, code smells
- **Cost**: $0 (local)

#### Layer 3: Dynamic Testing
- **Tools**: Foundry, Echidna
- **Coverage**: High-priority functions
- **Time**: 1-2 weeks
- **Output**: Working exploits
- **Cost**: $0 (local)

#### Layer 4: Manual Review
- **Tools**: Code review, logic analysis
- **Coverage**: Complex logic, edge cases
- **Time**: 1-2 weeks
- **Output**: Novel vulnerabilities
- **Cost**: $0 (time only)

---

## Phase-by-Phase Testing

### Phase 1: Reconnaissance (Days 1-2)

**Objective**: Understand the system deeply

**Activities**:

```bash
# 1. Read all documentation
cat README.md IMMUNEFI_RESEARCH.md ATTACK_SURFACE_GUIDE.md

# 2. Study contract source code
cd instascope/src
find . -name "*.sol" -exec wc -l {} + | sort -n

# 3. Map contract relationships
# Create mental model of:
# - Deposit flow (Bitcoin -> Bridge -> Vault -> TBTC)
# - Redemption flow (tBTC -> Vault -> Bridge -> Bitcoin)
# - Staking flow (T -> TokenStaking -> Rewards)
# - Governance flow (T -> Governor -> Proposals)

# 4. Identify trust boundaries
# - Who can call what?
# - What requires external authorization?
# - What crosses chain boundaries?

# 5. Document assumptions
# Write down:
# - System invariants
# - Security assumptions
# - Critical dependencies
```

**Deliverables**:
- System architecture diagram
- Contract relationship map
- List of critical functions
- Identified trust boundaries

### Phase 2: Automated Analysis (Day 3)

**Objective**: Generate vulnerability hypotheses using AI

**SecBrain Workflow**:

```bash
cd targets/thresholdnetwork

# 1. Dry run (validate setup, $0)
secbrain run \
  --scope scope-critical.yaml \
  --program program.json \
  --workspace testing/automated/dry-run \
  --dry-run

# 2. Critical contracts only ($5-15, 1-2 hours)
secbrain run \
  --scope scope-critical.yaml \
  --program program.json \
  --workspace testing/automated/critical

# 3. Full analysis ($10-30, 2-4 hours)
secbrain run \
  --scope scope.yaml \
  --program program.json \
  --workspace testing/automated/full

# 4. Research emerging patterns
secbrain research \
  --protocol "Threshold Network" \
  --timeframe 90 \
  --output testing/automated/research.json

# 5. Get Immunefi intelligence
secbrain immunefi intelligence \
  --program thresholdnetwork > testing/automated/immunefi.json
```

**Review Outputs**:

```bash
# Check hypotheses
cat testing/automated/critical/hypotheses/hypotheses.json | jq '.'

# Prioritize by:
# - Confidence > 0.7
# - Severity = "critical" or "high"
# - Detection priority >= 8

# Extract top 10 hypotheses
cat testing/automated/critical/hypotheses/hypotheses.json | \
  jq '[.[] | select(.confidence > 0.7 and .detection_priority >= 8)] | sort_by(-.confidence) | .[0:10]'
```

**Deliverables**:
- 15-25 AI-generated hypotheses
- Prioritized testing list
- Research insights

### Phase 3: Static Analysis (Days 4-5)

**Objective**: Find low-hanging fruit and code quality issues

**Slither Analysis**:

```bash
cd instascope

# Run Slither on all contracts
slither . \
  --config-file ../../slither.config.json \
  --json slither-report.json

# Focus on high/medium severity
slither . --exclude-low --exclude-informational

# Check specific contracts
slither src/Bridge.sol --solc-remaps "@openzeppelin=lib/openzeppelin-contracts"
slither src/TBTCVault.sol --solc-remaps "@openzeppelin=lib/openzeppelin-contracts"

# Custom detectors
slither . --detect reentrancy-eth,reentrancy-no-eth,reentrancy-benign
slither . --detect arbitrary-send,controlled-delegatecall
slither . --detect uninitialized-state,uninitialized-storage
```

**Semgrep Analysis**:

```bash
# Run Semgrep security rules
cd ../../
semgrep --config=.semgrep/rules/solidity-security.yml targets/thresholdnetwork/instascope/

# Check for:
# - Reentrancy patterns
# - Access control issues
# - Unchecked external calls
# - Integer overflow/underflow
```

**Mythril Analysis** (Optional):

```bash
# Symbolic execution (slow but thorough)
myth analyze src/Bridge.sol --solc-version 0.8.17
myth analyze src/TBTCVault.sol --solc-version 0.8.17
```

**Deliverables**:
- Slither report
- Semgrep findings
- List of suspicious patterns

### Phase 4: Priority Testing (Weeks 2-3)

**Objective**: Test critical hypotheses and high-value targets

**Focus Areas** (in order):

#### 4.1 Bitcoin Bridge SPV Proofs ($1M potential)

```bash
cd instascope

# Copy PoC template
cp ../POC_TEMPLATES.md test/exploits/SPVProofExploit.t.sol

# Test scenarios:
# 1. Fake Bitcoin transaction
# 2. Invalid merkle proof
# 3. Insufficient confirmations (< 6)
# 4. Replay attack (same UTXO twice)
# 5. Wrong network (testnet vs mainnet)
# 6. Malformed transaction structure

# Run tests
forge test --match-contract SPVProofExploit -vvvv
```

**Testing Checklist**:
- [ ] Transaction format validation
- [ ] Merkle proof verification
- [ ] Block header validation
- [ ] Confirmation count check
- [ ] Deposit uniqueness tracking
- [ ] Network magic bytes
- [ ] Output script validation
- [ ] Amount calculation

#### 4.2 Optimistic Minting ($1M potential)

```bash
# Copy template
cp ../POC_TEMPLATES.md test/exploits/OptimisticMintExploit.t.sol

# Test scenarios:
# 1. Mint without Bitcoin deposit
# 2. Cancel bypass during challenge period
# 3. Debt tracking manipulation
# 4. Concurrent optimistic mints
# 5. Guardian authorization bypass
# 6. Finalization without verification

# Run tests
forge test --match-contract OptimisticMintExploit -vvvv
```

**Testing Checklist**:
- [ ] Guardian authorization
- [ ] Debt limit enforcement
- [ ] Challenge period timing (3 hours)
- [ ] Cancellation conditions
- [ ] Finalization requirements
- [ ] Concurrent request handling
- [ ] Canonical deposit verification

#### 4.3 Threshold Signatures ($1M potential)

```bash
# Test scenarios:
# 1. Signature forgery
# 2. Threshold bypass (fewer signers)
# 3. DKG result manipulation
# 4. Public key verification
# 5. Message hash manipulation

# Note: Requires deep crypto knowledge
```

**Testing Checklist**:
- [ ] ECDSA signature verification
- [ ] Threshold enforcement
- [ ] DKG result validation
- [ ] Public key derivation
- [ ] Partial signature validation

#### 4.4 Staking Rewards ($50K potential)

```bash
# Copy template
cp ../POC_TEMPLATES.md test/exploits/StakingRewardExploit.t.sol

# Test scenarios:
# 1. Reward calculation rounding errors
# 2. Front-running reward distribution
# 3. Double claiming
# 4. Reward inflation
# 5. Unstaking during lock period

# Run tests
forge test --match-contract StakingRewardExploit -vvvv
```

**Testing Checklist**:
- [ ] Reward per token calculation
- [ ] Rounding error accumulation
- [ ] Claim tracking
- [ ] Lock period enforcement
- [ ] Stake/unstake timing

#### 4.5 Governance ($50K potential)

```bash
# Copy template
cp ../POC_TEMPLATES.md test/exploits/FlashLoanGovernance.t.sol

# Test scenarios:
# 1. Flash loan voting
# 2. Timelock bypass
# 3. Quorum manipulation
# 4. Vote delegation exploit

# Run tests
forge test --match-contract FlashLoanGovernanceExploit -vvvv
```

**Testing Checklist**:
- [ ] Snapshot-based voting
- [ ] Voting delay enforcement
- [ ] Timelock delay
- [ ] Quorum calculation
- [ ] Delegation mechanics

#### 4.6 Cross-Chain Bridges ($50K potential)

```bash
# Test scenarios:
# 1. Wormhole message forgery
# 2. Starknet state proof manipulation
# 3. Replay attacks
# 4. Chain ID validation

# Run tests
forge test --match-contract CrossChainExploit -vvvv
```

**Testing Checklist**:
- [ ] Guardian signature verification
- [ ] Message hash validation
- [ ] Sequence number tracking
- [ ] Chain ID enforcement
- [ ] State proof verification

**Deliverables**:
- Working exploit PoCs (if vulnerabilities found)
- Test results for all scenarios
- Documented findings

### Phase 5: Extended Testing (Week 4)

**Objective**: Cover remaining attack surfaces and edge cases

**Areas to Cover**:

```bash
# 1. Proxy patterns (all 8+ proxy contracts)
# - Unauthorized upgrades
# - Storage collisions
# - Initialization issues

# 2. Access control
# - Role-based access
# - Ownership transfers
# - Function modifiers

# 3. Reentrancy
# - Cross-function reentrancy
# - Read-only reentrancy
# - Cross-contract reentrancy

# 4. Economic attacks
# - MEV opportunities
# - Front-running
# - Griefing attacks

# 5. Edge cases
# - Zero values
# - Maximum values
# - Overflow conditions
# - Empty arrays
```

**Fuzzing** (Advanced):

```bash
# Foundry fuzzing
forge test --fuzz-runs 10000

# Echidna fuzzing (if configured)
echidna . --contract TestContract --config echidna.yaml
```

**Deliverables**:
- Additional test coverage
- Edge case findings
- Fuzzing results

### Phase 6: PoC Development (Week 5)

**Objective**: Refine exploits for submission

**For Each Finding**:

1. **Reproducibility**
   ```bash
   # Test on fresh fork
   forge test --match-test testExploit -vvvv
   ```

2. **Impact Quantification**
   ```solidity
   // Measure:
   uint256 profit = finalBalance - initialBalance;
   uint256 fundsAtRisk = vault.totalSupply();
   ```

3. **Documentation**
   ```markdown
   # Finding: [Vulnerability Name]
   
   ## Severity
   Critical - Direct theft of user funds
   
   ## Impact
   - Funds at risk: $X
   - Affected users: Y
   - Bounty estimate: $Z
   
   ## Root Cause
   [Detailed explanation]
   
   ## Proof of Concept
   [Foundry test]
   
   ## Remediation
   [Suggested fix]
   ```

4. **Video Recording** (Optional but helpful)
   ```bash
   # Record terminal session
   asciinema rec exploit-demo.cast
   
   # Convert to video or GIF
   ```

**Deliverables**:
- Polished PoC tests
- Professional documentation
- Impact analysis

### Phase 7: Validation (Week 6)

**Objective**: Final checks before submission

**Validation Checklist**:

```bash
# 1. Re-run all PoCs on latest mainnet block
export FORK_BLOCK=$(cast block-number)
forge test --match-path "test/exploits/*" -vvvv

# 2. Verify severity classification
# - Compare against Immunefi V2.3
# - Justify classification

# 3. Check submission requirements
# - Foundry test ✓
# - Root cause explanation ✓
# - Impact assessment ✓
# - Remediation suggestions ✓

# 4. Review for out-of-scope items
# - No mainnet testing
# - No third-party dependencies
# - No theoretical issues

# 5. Professional presentation
# - Clear writing
# - Code comments
# - Logical flow
```

**Deliverables**:
- Validated submissions
- Complete documentation
- Professional reports

---

## Automated Testing with SecBrain

### Command Reference

```bash
# List high-value programs
secbrain immunefi list --min-bounty 1000000

# Show program details
secbrain immunefi show --program thresholdnetwork

# Get trending vulnerabilities
secbrain immunefi trends --limit 10

# Get comprehensive intelligence
secbrain immunefi intelligence --program thresholdnetwork

# Research emerging patterns
secbrain research --timeframe 90 --output findings.json

# Research specific protocol
secbrain research \
  --protocol "Threshold Network" \
  --contracts "TBTC,Bridge,TBTCVault" \
  --output threshold_research.json

# Generate insights from results
secbrain insights --workspace workspace --format html --open

# Track metrics
secbrain metrics summary
secbrain metrics patterns
secbrain metrics insights
```

### Interpreting SecBrain Output

**Hypothesis Structure**:
```json
{
  "vuln_type": "bitcoin_peg_manipulation",
  "confidence": 0.85,
  "severity": "critical",
  "detection_priority": 10,
  "max_bounty_usd": 1000000,
  "rationale": "...",
  "detection_heuristics": [...],
  "exploitation_steps": [...]
}
```

**Prioritization Formula**:
```
Priority Score = (Confidence × 0.4) + (Severity × 0.3) + (Detection Priority × 0.3)

Test if: Priority Score > 7.0
```

---

## Manual Testing Techniques

### Code Review Checklist

For each critical function:

1. **Entry Points**
   - Who can call this?
   - What are the prerequisites?
   - Are there any access controls?

2. **State Changes**
   - What state is modified?
   - Are there any side effects?
   - Is the order of operations correct?

3. **External Calls**
   - What external contracts are called?
   - Are return values checked?
   - Is reentrancy possible?

4. **Math Operations**
   - Any division (rounding errors)?
   - Any unchecked blocks?
   - Overflow/underflow possible?

5. **Exit Conditions**
   - When does function revert?
   - Are all paths validated?
   - Can execution be griefed?

### Logic Flow Analysis

```solidity
// Example: Deposit flow analysis

// 1. Entry: Bridge.revealDeposit()
// - Check: SPV proof valid?
// - Check: Deposit not already revealed?
// - Check: Sufficient confirmations?

// 2. State change: Mark deposit as revealed
// - Check: Atomic with mint?
// - Check: Correct amount calculated?

// 3. External call: TBTCVault.mint()
// - Check: Only Bridge can call?
// - Check: Amount matches deposit?
// - Check: Treasury fee deducted?

// 4. Token mint: TBTC.mint()
// - Check: Only Vault can call?
// - Check: Total supply updated?
// - Check: Balance updated?

// Attack vectors:
// - Can I forge proof at step 1?
// - Can I replay at step 2?
// - Can I reenter at step 3?
// - Can I manipulate amount at step 4?
```

### Invariant Testing

Define and test system invariants:

```solidity
// Invariants for tBTC bridge:

// 1. Conservation: TBTC supply ≤ Bitcoin locked
function invariant_btcBacking() public {
    uint256 tbtcSupply = tbtc.totalSupply();
    uint256 btcLocked = getBitcoinLocked();
    assertTrue(tbtcSupply <= btcLocked, "Insufficient BTC backing");
}

// 2. No unauthorized minting
function invariant_onlyBridgeCanMint() public {
    // Verify mint() can only be called by Bridge
}

// 3. Redemption guarantee
function invariant_redemptionAlwaysPossible() public {
    // Verify redemption never permanently fails
}
```

---

## Validation and Verification

### Testing Best Practices

1. **Isolation**
   - Test one thing at a time
   - Clean state for each test
   - No dependencies between tests

2. **Reproducibility**
   - Document exact block number
   - List all dependencies
   - Provide setup instructions

3. **Clarity**
   - Clear test names
   - Descriptive assertions
   - Helpful error messages

4. **Coverage**
   - Test happy path
   - Test edge cases
   - Test failure modes

### Common Test Patterns

```solidity
// Pattern 1: Before/After Balance Check
function testExploit() public {
    uint256 before = token.balanceOf(attacker);
    // ... exploit ...
    uint256 after = token.balanceOf(attacker);
    assertGt(after, before, "Should profit");
}

// Pattern 2: State Invariant Check
function testInvariant() public {
    // ... exploit ...
    assertEq(invariant(), true, "Invariant broken");
}

// Pattern 3: Revert Expectation
function testShouldRevert() public {
    vm.expectRevert("Error message");
    contract.vulnerableFunction();
}

// Pattern 4: Event Emission
function testEmitsEvent() public {
    vm.expectEmit(true, true, false, true);
    emit SomeEvent(param1, param2);
    contract.function();
}
```

---

## Common Pitfalls

### Mistakes to Avoid

1. **Testing on Mainnet**
   - NEVER test on production
   - Always use local fork
   - Anvil/Hardhat for testing

2. **Insufficient PoC**
   - Must be reproducible
   - Must show clear impact
   - Must work on latest block

3. **Wrong Severity Classification**
   - Read Immunefi V2.3 carefully
   - Theoretical ≠ actual impact
   - Temporary ≠ permanent

4. **Out-of-Scope Submissions**
   - Check exclusion list
   - Verify testing restrictions
   - Confirm vulnerability type

5. **Premature Disclosure**
   - NO public discussion
   - NO Twitter posts
   - NO blog articles
   - Submit via Immunefi only

### Red Flags During Testing

If you see these, investigate further:

- Unchecked external calls
- Complex math without SafeMath
- Loops with user-controlled bounds
- Storage operations after external calls
- Missing access control modifiers
- Proxy with uninitialized variables
- Timestamps used for critical logic
- Block number for randomness
- Delegatecall to user input
- Selfdestruct in contract

---

## Conclusion

This testing guide provides a comprehensive framework for auditing Threshold Network. Remember:

1. **Start with automation** (SecBrain)
2. **Focus on critical targets** (Bridge, Vault, Staking)
3. **Be thorough** (test edge cases)
4. **Document everything** (professional reports)
5. **Validate findings** (reproducible PoCs)
6. **Stay in scope** (follow Immunefi rules)

**Expected Results**:
- 1-3 medium severity findings (likely)
- 0-1 high severity finding (possible)
- 0-1 critical finding (rare but achievable)

Good luck! 🎯
