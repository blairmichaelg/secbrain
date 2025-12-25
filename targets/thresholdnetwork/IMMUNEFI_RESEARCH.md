# Threshold Network Immunefi Bounty Program - Comprehensive Research

**Last Updated**: December 25, 2024  
**Program URL**: https://immunefi.com/bug-bounty/thresholdnetwork/  
**Platform**: Immunefi  
**Max Bounty**: Up to $1,000,000 USD

## Table of Contents

- [Program Overview](#program-overview)
- [Scope Analysis](#scope-analysis)
- [Asset Inventory](#asset-inventory)
- [Attack Surface Analysis](#attack-surface-analysis)
- [Vulnerability Prioritization](#vulnerability-prioritization)
- [Submission Requirements](#submission-requirements)
- [Bug Bounty Strategy](#bug-bounty-strategy)

---

## Program Overview

### Background

Threshold Network is the result of a merger between Keep Network and NuCypher, bringing together threshold cryptography capabilities to create a decentralized trust layer. The network provides:

1. **tBTC v2**: A decentralized Bitcoin bridge to Ethereum
2. **Threshold Access Control (TACo)**: Privacy-preserving access control
3. **Threshold Network Token (T)**: Unified governance and utility token
4. **Decentralized Operator Network**: Threshold cryptography service providers

### Program Characteristics

- **Launch Date**: Program has been active for multiple years
- **Total Assets in Scope**: 39 smart contracts on Ethereum mainnet
- **Primary Focus**: Smart contract security
- **Network**: Ethereum Mainnet (Chain ID: 1)
- **KYC Requirement**: Only for payouts over $100,000
- **Payment Methods**: USDC, USDT, ETH, or T tokens
- **Typical Response Time**: 2-4 weeks for initial triage

---

## Scope Analysis

### In-Scope Vulnerabilities (By Severity)

#### Critical ($100,000 - $1,000,000)

1. **Direct theft of any user funds** (at-rest or in-motion)
   - Includes: Staked tokens, bridged BTC, T tokens, rewards
   - Excludes: Unclaimed yield

2. **Permanent freezing of funds**
   - Complete inability to withdraw or transfer
   - Indefinite lockup of user assets
   - Critical bridge functionality failure

3. **Protocol insolvency**
   - System-wide undercollateralization
   - Bridge peg breaking permanently
   - Total loss of backing assets

**Impact Requirement**: Must affect actual user funds or protocol solvency.

#### High ($10,000 - $50,000)

1. **Theft of unclaimed yield**
   - Stealing staking rewards
   - Manipulation of reward distribution
   - Unauthorized claim of protocol fees

2. **Permanent freezing of unclaimed yield**
   - Permanent lock of rewards
   - Inability to claim earned interest

3. **Temporary freezing of funds** (minimum 1 hour)
   - Temporary withdrawal delays
   - Short-term lockup mechanisms
   - Griefing attacks with time impact

**Impact Requirement**: Must demonstrate actual freezing period or yield theft amount.

#### Medium ($1,000 - $10,000)

1. **Smart contract unable to operate** due to lack of token funds
2. **Block stuffing** for profit or disruption
3. **Griefing attacks** (no direct profit, but user/protocol damage)
4. **Theft of gas**
5. **Unbounded gas consumption**

**Impact Requirement**: Must provide working exploit and demonstrate impact.

#### Low ($100 - $1,000)

Based on Immunefi Vulnerability Severity Classification System V2.3, includes:
- Minor functionality issues
- State handling bugs
- Edge cases with minimal impact

### Out of Scope

**Testing Restrictions**:
- ❌ Any testing on mainnet or public testnet deployed code
- ❌ Any testing with pricing oracles or third-party smart contracts
- ❌ Testing with third-party systems and applications
- ❌ Denial of service attacks against project assets
- ❌ Automated testing generating significant traffic

**Vulnerability Exclusions**:
- ❌ Incorrect data supplied by third-party oracles (except manipulation/flash loan attacks)
- ❌ Basic economic and governance attacks (e.g., 51% attack)
- ❌ Lack of liquidity impacts
- ❌ Sybil attacks
- ❌ Centralization risks
- ❌ Attacks already exploited by reporter
- ❌ Attacks requiring leaked keys/credentials
- ❌ Attacks requiring privileged address access without modifications
- ❌ Attacks relying on external stablecoin depegging
- ❌ Secrets/keys in GitHub without proof of production use
- ❌ Best practice recommendations
- ❌ Feature requests
- ❌ Impacts on test files and configuration files

**Public Disclosure**: 
- ❌ Public disclosure of unpatched vulnerabilities is prohibited

---

## Asset Inventory

### Critical Contracts (Priority 1)

#### 1. TBTC Token (`0x18084fbA666a33d37592fA2633fD49a74DD93a88`)
**Function**: Main tBTC ERC20 token representing Bitcoin on Ethereum
**Critical Functions**:
- `mint(address, uint256)` - Mint new tBTC upon Bitcoin deposit
- `burn(uint256)` - Burn tBTC for Bitcoin redemption
- `transfer`, `transferFrom` - Token movement

**Attack Vectors**:
- Unauthorized minting
- Burn without Bitcoin redemption
- Transfer restrictions bypass
- Total supply manipulation

#### 2. TBTCVault (`0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD`)
**Function**: Custodian for minted tBTC, manages minting and unminting operations
**Critical Functions**:
- `mint(bytes32, address)` - Mint tBTC for depositors
- `unmint(uint256)` - Initiate redemption process
- `requestOptimisticMint` - Request optimistic mint
- `finalizeOptimisticMint` - Finalize optimistic mint
- `cancelOptimisticMint` - Cancel fraudulent optimistic mint

**Attack Vectors**:
- Optimistic mint without BTC deposit
- Cancellation bypass
- Vault balance manipulation
- Minting cap bypass

#### 3. Bridge (`0x8d014903bf7867260584d714e11809fea5293234`)
**Function**: Core Bitcoin bridge logic, handles deposits and redemptions
**Critical Functions**:
- `revealDeposit(bytes, bytes32)` - Reveal Bitcoin deposit with proof
- `requestRedemption(address, uint256)` - Request BTC withdrawal
- `submitRedemptionProof(bytes, bytes)` - Prove Bitcoin redemption
- `notifyRedemptionTimeout` - Handle stalled redemptions

**Attack Vectors**:
- SPV proof forgery
- Replay attacks on deposits
- Redemption without burning tBTC
- Deposit frontrunning
- Malicious relay operators

#### 4. WalletRegistry (`0xfbae130e06bbc8ca198861beecae6e2b830398fb`)
**Function**: Manages ECDSA wallet groups for threshold signing
**Critical Functions**:
- `requestNewWallet()` - Request new threshold wallet creation
- `registerOperator(bytes)` - Register new operator
- `approveAuthorizationDecrease(address)` - Manage operator stake
- `seize(uint96, uint256, address)` - Slash misbehaving operators

**Attack Vectors**:
- Unauthorized wallet creation
- Operator collusion
- DKG manipulation
- Slashing mechanism bypass
- Unauthorized operator registration

#### 5. T Token (`0xCdF7028ceAB81fA0C6971208e83fa7872994beE5`)
**Function**: Threshold Network governance and utility token
**Critical Functions**:
- `transfer`, `transferFrom` - Token movement
- `delegate(address)` - Voting power delegation
- `burn(uint256)` - Token burning

**Attack Vectors**:
- Governance manipulation via flash loans
- Delegation vulnerabilities
- Supply manipulation

#### 6. TokenStaking (`0xf5a2ccfea213cb3ff0799e0c33ea2fa3da7cbb65`)
**Function**: Staking mechanism for T tokens
**Critical Functions**:
- `stake(address, uint96)` - Stake T tokens
- `unstake(address, uint96)` - Unstake T tokens
- `notifyRewardAmount(uint256)` - Distribute rewards
- `getReward()` - Claim staking rewards
- `slash(address, uint96)` - Slash misbehaving stakers

**Attack Vectors**:
- Reward manipulation
- Slashing bypass
- Unstaking restrictions bypass
- Reward calculation errors

### High Priority Contracts (Priority 2)

#### 7-15. TransparentUpgradeableProxy Contracts (Multiple addresses)
**Function**: Proxy pattern for upgradeable contracts
**Critical Functions**:
- `upgradeTo(address)` - Upgrade implementation
- `upgradeToAndCall(address, bytes)` - Upgrade with initialization

**Attack Vectors**:
- Unauthorized upgrades
- Storage collision
- Implementation replacement
- Initialization replay

#### 16. TokenholderGovernor (`0xd101f2b25bcbf992bdf55db67c104fe7646f5447`)
**Function**: DAO governance for T token holders
**Critical Functions**:
- `propose(...)` - Create governance proposal
- `castVote(uint256, uint8)` - Vote on proposal
- `execute(uint256)` - Execute passed proposal
- `queue(uint256)` - Queue proposal for execution

**Attack Vectors**:
- Flash loan governance attacks
- Quorum manipulation
- Timelock bypass
- Vote buying

#### 17. Bank (`0x65Fbae61ad2C8836fFbFB502A0dA41b0789D9Fc6`)
**Function**: Manages balances for bridge operations
**Critical Functions**:
- `updateBalance(bytes32, uint256)` - Update wallet balance
- `transferBalanceToRedeeming(bytes32, uint256)` - Handle redemptions

**Attack Vectors**:
- Balance manipulation
- Unauthorized transfers
- Balance underflow/overflow

### Medium Priority Contracts (Priority 3)

#### 18. BridgeGovernance (`0xA94DD662E2A247493fACCeab9f2459AAF90778Ee`)
**Function**: Governance for bridge parameters
**Attack Vectors**: Parameter manipulation, proposal exploits

#### 19-25. Cross-Chain Bridge Contracts
- **StarknetTokenBridge** (`0xf39d314c5ad7dc88958116dfa7d5ac095d563aff`)
- **BTCDepositorWormhole** (`0x9a5250c7bea10f7472eb9d50bb757b83d67fb5ed`)
- **L1BitcoinDepositor** (`0x3ffee7d7be970201a33d17e318e2421a06ad69f8`)
- **L1BTCRedeemerWormhole** (`0x14d93d4c4e07130fffe6083432b66b96d8eb9dc0`)

**Attack Vectors**: Cross-chain message forgery, relay manipulation, proof verification flaws

#### 26-30. Supporting Contracts
- **LightRelay** (`0x836cdFE63fe2d63f8Bdb69b96f6097F36635896E`) - Bitcoin block relay
- **ReimbursementPool** (`0x8adF3f35dBE4026112bCFc078872bcb967732Ea8`) - Gas reimbursement
- **DonationVault** (`0xa544b70dC6af906862f68eb8e68c27bb7150e672`) - Protocol donations
- **RedemptionWatchtower** (`0xbfd04e3928923ad8c86256b9a8f64ebd01cf1daf`) - Redemption monitoring
- **SortitionPool** (`0xc2731fb2823af3Efc2694c9bC86F444d5c5bb4Dc`) - Operator selection

---

## Attack Surface Analysis

### 1. Bitcoin Bridge Attack Surface

#### A. Deposit Flow
```
Bitcoin Network → SPV Proof → Bridge.revealDeposit() → TBTCVault.mint() → TBTC minted
```

**Critical Points**:
1. **SPV Proof Verification** (Bridge contract)
   - Bitcoin transaction parsing
   - Merkle proof validation
   - Block header verification via LightRelay
   - Minimum confirmations check (6 blocks)

2. **Deposit Uniqueness** (Bridge contract)
   - Prevent replay of same deposit
   - UTXO tracking
   - Deposit key generation

3. **Minting Authorization** (TBTCVault contract)
   - Only Bridge can call mint
   - Correct amount calculation
   - Treasury fee deduction

**Known Vulnerabilities to Test**:
- SPV proof forgery (create fake Bitcoin transaction)
- Replay attacks (submit same deposit multiple times)
- Race conditions (frontrun deposit revelation)
- Proof validation bypass
- Block header manipulation
- Insufficient confirmations

#### B. Redemption Flow
```
User requests redemption → Wallet signs BTC tx → BTC sent → Proof submitted → tBTC burned
```

**Critical Points**:
1. **Redemption Request** (Bridge contract)
   - User locks tBTC for redemption
   - Wallet assignment
   - Timeout tracking

2. **Bitcoin Transaction Signing** (WalletRegistry, off-chain)
   - Threshold signature generation
   - Transaction construction
   - Wallet balance tracking

3. **Redemption Proof** (Bridge contract)
   - Bitcoin transaction proof verification
   - Burning of locked tBTC
   - Treasury fee handling

**Known Vulnerabilities to Test**:
- Redemption without BTC transfer
- Proof replay attacks
- Timeout exploitation
- Wallet coordination attacks
- Double redemption

#### C. Optimistic Minting
```
User requests → Guardian approves → Instant mint → Verification period → Finalize or Cancel
```

**Critical Points**:
1. **Request Validation** (TBTCVault)
   - Guardian authorization check
   - Debt tracking
   - Collateralization requirements

2. **Challenge Period** (TBTCVault)
   - 3-hour window for cancellation
   - Cancellation conditions
   - Proof of fraud

3. **Finalization** (TBTCVault)
   - Convert optimistic mint to regular
   - Debt clearing
   - Canonical deposit verification

**Known Vulnerabilities to Test**:
- Optimistic mint without Bitcoin deposit
- Challenge bypass
- Cancellation prevention
- Debt manipulation
- Guardian compromise

### 2. Threshold Cryptography Attack Surface

#### A. Distributed Key Generation (DKG)
**Process**: Multiple operators generate shared ECDSA key without single point of control

**Critical Points**:
1. **Operator Selection** (SortitionPool)
   - Random selection from eligible operators
   - Stake requirements
   - Minimum operator count

2. **DKG Protocol** (WalletRegistry, off-chain)
   - Key share generation
   - Zero-knowledge proofs
   - Commitment schemes

3. **Wallet Creation** (WalletRegistry)
   - Public key aggregation
   - Wallet registration
   - Activation

**Known Vulnerabilities to Test**:
- DKG manipulation
- Operator collusion
- Insufficient randomness
- Key share exposure
- Wallet creation griefing

#### B. Threshold Signing
**Process**: Subset of operators collaboratively sign Bitcoin transactions

**Critical Points**:
1. **Signature Request** (Bridge/TBTCVault)
   - Valid redemption request
   - Signing group assignment

2. **Signature Generation** (Off-chain, coordinated via smart contract)
   - Partial signature creation
   - Signature aggregation
   - ECDSA math correctness

3. **Signature Verification** (Bridge)
   - Signature validation
   - Message hash verification
   - Public key matching

**Known Vulnerabilities to Test**:
- Signature forgery
- Threshold bypass (fewer operators)
- Malicious signature construction
- Double-signing prevention

### 3. Staking & Governance Attack Surface

#### A. Token Staking
**Critical Points**:
1. **Stake Management**
   - Minimum stake enforcement
   - Lock periods
   - Authorization for applications

2. **Reward Distribution**
   - Reward calculation accuracy
   - Fair distribution
   - Claim mechanisms

3. **Slashing**
   - Misbehavior detection
   - Penalty calculation
   - Asset seizure

**Known Vulnerabilities to Test**:
- Reward manipulation
- Slashing bypass
- Staking without tokens
- Unstaking during lockup
- Reward front-running

#### B. DAO Governance
**Critical Points**:
1. **Proposal Creation**
   - Proposer eligibility
   - Proposal validation
   - Cooldown periods

2. **Voting**
   - Vote counting
   - Delegation handling
   - Quorum calculation

3. **Execution**
   - Timelock enforcement
   - Execution authorization
   - State changes

**Known Vulnerabilities to Test**:
- Flash loan governance attacks
- Vote manipulation
- Quorum bypass
- Timelock bypass
- Proposal execution without passage

### 4. Cross-Chain Bridge Attack Surface

#### A. Wormhole Integration
**Critical Points**:
- Message verification
- Guardian signatures
- Replay protection
- Chain ID validation

**Known Vulnerabilities to Test**:
- Message forgery
- Signature bypass
- Cross-chain replay
- Guardian compromise

#### B. Starknet Integration
**Critical Points**:
- L1→L2 message passing
- L2→L1 message consumption
- State synchronization

**Known Vulnerabilities to Test**:
- Message manipulation
- State inconsistency
- Merkle proof issues

### 5. Proxy Pattern Attack Surface

**All Proxy Contracts**: 8+ TransparentUpgradeableProxy instances

**Critical Points**:
1. **Upgrade Mechanism**
   - Admin authorization
   - Implementation validation
   - Storage compatibility

2. **Delegatecall Safety**
   - Storage layout preservation
   - Function selector collision
   - Initialization protection

**Known Vulnerabilities to Test**:
- Unauthorized upgrades
- Storage collision
- Uninitialized implementation
- Selfdestruct in implementation
- Function collision

---

## Vulnerability Prioritization

### Priority 1: Critical Severity Targets (Bounty: $100K - $1M)

#### 1.1 Bitcoin Bridge Manipulation ($1M potential)
**Contracts**: Bridge, TBTCVault, TBTC
**Focus Areas**:
- [ ] SPV proof verification logic
- [ ] Deposit replay prevention
- [ ] Optimistic mint cancellation
- [ ] Redemption proof validation
- [ ] Mint authorization checks

**Testing Approach**:
1. Create malformed Bitcoin transaction proofs
2. Attempt deposit replay with same UTXO
3. Test optimistic mint without actual Bitcoin
4. Try redemption proof forgery
5. Test cross-function reentrancy in mint/burn

**Expected Impact**: Direct theft of user funds via unauthorized minting or burning

#### 1.2 Wallet Registry Compromise ($1M potential)
**Contracts**: WalletRegistry, EcdsaDkgValidator
**Focus Areas**:
- [ ] DKG result validation
- [ ] Operator authorization
- [ ] Wallet creation logic
- [ ] Slashing mechanism
- [ ] Operator collusion scenarios

**Testing Approach**:
1. Submit malicious DKG results
2. Register unauthorized operators
3. Create wallets without proper DKG
4. Bypass slashing conditions
5. Test operator collusion attack paths

**Expected Impact**: Control over Bitcoin signing, ability to steal all bridged BTC

#### 1.3 Threshold Signature Bypass ($1M potential)
**Contracts**: WalletRegistry, Bridge
**Focus Areas**:
- [ ] Signature verification
- [ ] Threshold enforcement
- [ ] Key share exposure
- [ ] Partial signature validation

**Testing Approach**:
1. Attempt signing with fewer than threshold operators
2. Test signature forgery techniques
3. Analyze key share leakage
4. Test signature malleability

**Expected Impact**: Unauthorized Bitcoin transactions, theft of all funds

### Priority 2: High Severity Targets (Bounty: $10K - $50K)

#### 2.1 Staking Reward Manipulation ($50K potential)
**Contracts**: TokenStaking, RebateStaking
**Focus Areas**:
- [ ] Reward calculation
- [ ] Distribution logic
- [ ] Claim mechanisms
- [ ] Accounting accuracy

**Testing Approach**:
1. Test reward inflation attacks
2. Multiple claim scenarios
3. Rounding error exploitation
4. Reward front-running

**Expected Impact**: Theft of unclaimed yield, unfair reward distribution

#### 2.2 Governance Attack ($50K potential)
**Contracts**: TokenholderGovernor
**Focus Areas**:
- [ ] Flash loan voting
- [ ] Quorum calculation
- [ ] Timelock enforcement
- [ ] Delegation safety

**Testing Approach**:
1. Flash loan governance attack simulation
2. Quorum manipulation tests
3. Timelock bypass attempts
4. Vote delegation exploits

**Expected Impact**: Unauthorized governance changes, protocol takeover

#### 2.3 Cross-Chain Message Forgery ($50K potential)
**Contracts**: StarknetTokenBridge, BTCDepositorWormhole, L1BTCRedeemerWormhole
**Focus Areas**:
- [ ] Message verification
- [ ] Signature validation
- [ ] Replay protection
- [ ] State synchronization

**Testing Approach**:
1. Forge cross-chain messages
2. Replay message attacks
3. State desynchronization
4. Guardian signature bypass

**Expected Impact**: Theft or freezing of cross-chain assets

### Priority 3: Medium Severity Targets (Bounty: $1K - $10K)

#### 3.1 Proxy Upgrade Exploitation ($10K potential)
**Contracts**: All TransparentUpgradeableProxy instances
**Focus Areas**:
- [ ] Upgrade authorization
- [ ] Storage collision
- [ ] Initialization safety

**Testing Approach**:
1. Unauthorized upgrade attempts
2. Storage collision creation
3. Uninitialized proxy exploitation

**Expected Impact**: Contract malfunction, potential for escalation

#### 3.2 Gas Griefing & DoS ($5K potential)
**Contracts**: All contracts with loops or external calls
**Focus Areas**:
- [ ] Unbounded loops
- [ ] External call failures
- [ ] Block stuffing vectors

**Testing Approach**:
1. Create scenarios with excessive gas consumption
2. Force external call failures
3. Test array size limitations

**Expected Impact**: Contract unavailability, user griefing

---

## Submission Requirements

### Proof of Concept (PoC) Requirements

**All submissions MUST include**:

1. **Foundry Test File**
   ```solidity
   // SPDX-License-Identifier: MIT
   pragma solidity ^0.8.0;
   
   import "forge-std/Test.sol";
   
   contract ExploitTest is Test {
       function setUp() public {
           // Fork mainnet at specific block
           vm.createSelectFork(vm.rpcUrl("mainnet"), BLOCK_NUMBER);
       }
       
       function testExploit() public {
           // Demonstrate exploit
           // Show before/after balances
           // Prove impact
       }
   }
   ```

2. **Detailed Explanation**
   - Root cause analysis
   - Step-by-step exploit walkthrough
   - Impact assessment
   - Affected functions/contracts

3. **Severity Justification**
   - Immunefi severity classification
   - Impact evidence (funds at risk, users affected)
   - Likelihood assessment
   - Reference to similar exploits if applicable

4. **Remediation Suggestion** (optional but valued)
   - Proposed fix
   - Code patch if possible
   - Alternative mitigations

### Submission Best Practices

1. **Test on Local Fork Only**
   ```bash
   # Use Anvil for local fork
   anvil --fork-url $ETH_RPC_URL --fork-block-number <BLOCK>
   
   # Run exploit test
   forge test --match-test testExploit -vvvv
   ```

2. **Document Clearly**
   - Use clear, professional language
   - Include all relevant code and logs
   - Provide transaction traces if helpful
   - Include video/screenshots for complex exploits

3. **Be Specific**
   - Exact contract addresses
   - Specific function names
   - Block numbers for reproducibility
   - Exact impact amounts (if quantifiable)

4. **Avoid**
   - Vague descriptions
   - Theoretical vulnerabilities without PoC
   - Out-of-scope findings
   - Public disclosure before fix

### Expected Timeline

1. **Submission**: Via Immunefi platform
2. **Initial Triage**: 2-4 weeks
3. **Investigation**: 2-8 weeks (depending on complexity)
4. **Fix Development**: 2-12 weeks
5. **Bounty Payment**: After fix deployment and verification

### Communication

- **Platform**: Immunefi dashboard only
- **Response Expectations**: Regular updates every 1-2 weeks
- **Escalation**: Use Immunefi mediation if needed
- **Questions**: Ask via Immunefi or Discord (careful not to reveal vuln)

---

## Bug Bounty Strategy

### Phase 1: Deep Reconnaissance (Week 1-2)

**Goals**:
1. Build complete mental model of system
2. Identify all trust boundaries
3. Map data flows
4. Understand invariants

**Activities**:
- [ ] Read all contract source code (39 contracts)
- [ ] Map out complete deposit flow
- [ ] Map out complete redemption flow
- [ ] Understand DKG and threshold signing
- [ ] Review governance mechanisms
- [ ] Study cross-chain integrations
- [ ] Analyze proxy implementations
- [ ] Review historical commits for recent changes
- [ ] Study Threshold Network documentation
- [ ] Review previous audits (if available)

**Tools**:
- Etherscan for verified source
- Foundry for local testing
- Slither for static analysis
- Mythril for symbolic execution
- Manual code review

### Phase 2: Vulnerability Hypothesis (Week 2-3)

**Goals**:
1. Generate targeted hypotheses
2. Prioritize by likelihood × impact
3. Create test scenarios

**Activities**:
- [ ] Run SecBrain hypothesis generation
- [ ] Cross-reference with known vulnerability patterns
- [ ] Focus on critical severity patterns first
- [ ] Create testing checklist for each hypothesis
- [ ] Set up Foundry test environment
- [ ] Prepare mainnet fork at recent block

**SecBrain Commands**:
```bash
# Generate hypotheses
secbrain run \
  --scope targets/thresholdnetwork/scope-critical.yaml \
  --program targets/thresholdnetwork/program.json \
  --workspace targets/thresholdnetwork/workspace

# Research emerging patterns
secbrain research --protocol "Threshold Network" \
  --timeframe 90 --output findings.json
```

### Phase 3: Exploit Development (Week 3-6)

**Goals**:
1. Test top hypotheses
2. Develop working exploits
3. Measure impact
4. Document findings

**Activities**:
- [ ] Test Priority 1 hypotheses (critical)
- [ ] Develop Foundry PoCs for viable exploits
- [ ] Quantify impact (funds at risk)
- [ ] Refine exploits for clarity
- [ ] Test Priority 2 hypotheses (high)
- [ ] Document all findings thoroughly

**Testing Pattern**:
```solidity
// For each hypothesis:
// 1. Setup fork
// 2. Capture initial state
// 3. Execute exploit
// 4. Measure impact
// 5. Verify findings
// 6. Document
```

### Phase 4: Validation & Submission (Week 6-7)

**Goals**:
1. Validate all findings
2. Prepare professional submissions
3. Submit via Immunefi
4. Track submissions

**Activities**:
- [ ] Re-test all exploits on fresh fork
- [ ] Verify impact calculations
- [ ] Prepare detailed write-ups
- [ ] Record video demonstrations (if helpful)
- [ ] Review submission for completeness
- [ ] Submit via Immunefi platform
- [ ] Track submission status
- [ ] Respond to triage questions promptly

**Quality Checks**:
- PoC works on latest mainnet block
- Impact is clearly demonstrated
- Severity classification is justified
- All submission requirements met
- No accidental disclosure

### Phase 5: Continuous Learning (Ongoing)

**Goals**:
1. Learn from responses
2. Improve detection techniques
3. Track new vulnerabilities

**Activities**:
- [ ] Study triage feedback
- [ ] Update detection patterns
- [ ] Monitor new exploits in wild
- [ ] Share learnings (anonymously)
- [ ] Refine tooling and methodology

---

## Optimized Testing Workflow

### Setup

```bash
# 1. Clone Threshold contracts (if needed)
cd targets/thresholdnetwork/instascope

# 2. Install Foundry (if not installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# 3. Configure RPC
export ETH_RPC_URL="https://eth.llamarpc.com"  # or your preferred RPC

# 4. Test compilation
forge build --via-ir

# 5. Fork mainnet
anvil --fork-url $ETH_RPC_URL --fork-block-number 18500000
```

### Testing Template

Create `test/ExploitTemplate.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

interface ITBTC {
    function balanceOf(address) external view returns (uint256);
    function mint(address, uint256) external;
}

interface IBridge {
    function revealDeposit(
        bytes calldata fundingTx,
        bytes32 fundingOutputIndex
    ) external;
}

contract ExploitTemplate is Test {
    ITBTC constant tbtc = ITBTC(0x18084fbA666a33d37592fA2633fD49a74DD93a88);
    IBridge constant bridge = IBridge(0x8d014903bf7867260584d714e11809fea5293234);
    
    address attacker = address(0x1337);
    
    function setUp() public {
        // Fork mainnet
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
        
        // Label addresses for better traces
        vm.label(address(tbtc), "TBTC");
        vm.label(address(bridge), "Bridge");
        vm.label(attacker, "Attacker");
    }
    
    function testExploitTemplate() public {
        // 1. Record initial state
        uint256 initialBalance = tbtc.balanceOf(attacker);
        console.log("Initial TBTC balance:", initialBalance);
        
        // 2. Execute exploit
        vm.startPrank(attacker);
        
        // TODO: Implement exploit steps
        
        vm.stopPrank();
        
        // 3. Verify impact
        uint256 finalBalance = tbtc.balanceOf(attacker);
        console.log("Final TBTC balance:", finalBalance);
        
        uint256 profit = finalBalance - initialBalance;
        console.log("Profit:", profit);
        
        // 4. Assert meaningful impact
        assertGt(profit, 0, "Exploit should be profitable");
    }
}
```

### Run Tests

```bash
# Run single test with verbose output
forge test --match-test testExploitTemplate -vvvv

# Run with gas reporting
forge test --match-test testExploitTemplate --gas-report

# Generate coverage
forge coverage

# Run specific contract tests
forge test --match-contract ExploitTemplate -vvvv
```

---

## Key Insights for Bug Hunters

### What Makes Threshold Network Unique

1. **Threshold Cryptography**: Unlike most bridges that use multisig, Threshold uses threshold ECDSA signatures generated by a distributed network. This is complex cryptography with many attack vectors.

2. **Optimistic Minting**: Allows instant minting with guardian approval before Bitcoin confirmations. High-risk feature that needs careful scrutiny.

3. **Legacy Token Migration**: T token is merger of KEEP and NU tokens. Vending machine logic is complex and potentially exploitable.

4. **Multiple Cross-Chain Bridges**: Not just Ethereum↔Bitcoin, but also Wormhole and Starknet integrations, each with their own attack surface.

5. **Extensive Proxy Usage**: Many contracts use TransparentUpgradeableProxy pattern. Storage collisions and upgrade logic are critical.

### Common Pitfalls to Avoid

1. **Out of Scope Findings**:
   - Don't submit oracle manipulation without proving you can manipulate the oracle
   - Don't submit governance attacks requiring majority token holdings
   - Don't submit issues requiring compromised admin keys

2. **Insufficient PoC**:
   - Must work on mainnet fork, not just theory
   - Must demonstrate actual impact, not just potential
   - Must be reproducible with clear instructions

3. **Wrong Severity Classification**:
   - Read Immunefi V2.3 severity system carefully
   - "Could lead to" is not the same as "does lead to"
   - Temporary vs permanent impact matters

4. **Public Disclosure**:
   - Never tweet about vulnerabilities before they're fixed
   - Don't discuss in public Discord channels
   - Don't share exploit code publicly

### High-Value Patterns to Focus On

Based on historical Immunefi payouts and Threshold architecture:

1. **SPV Proof Manipulation** (Critical - $1M potential)
   - Most valuable target
   - Complex verification logic
   - Direct path to unauthorized minting

2. **Optimistic Mint Bypass** (Critical - $1M potential)
   - Guardian assumptions
   - Challenge period manipulation
   - Debt tracking exploits

3. **Threshold Signature Forgery** (Critical - $1M potential)
   - ECDSA math errors
   - Partial signature validation
   - Threshold bypass

4. **Cross-Chain Message Forgery** (Critical - $1M potential)
   - Wormhole integration
   - Starknet bridge
   - Message verification bypass

5. **Governance Flash Loan** (High - $50K potential)
   - Flash loan voting power
   - Timelock bypass
   - Quorum manipulation

6. **Staking Reward Inflation** (High - $50K potential)
   - Reward calculation errors
   - Rounding errors at scale
   - Distribution logic flaws

7. **Proxy Storage Collision** (Medium - $10K potential)
   - Upgrade mechanism exploits
   - Storage layout issues
   - Initialization flaws

### Resources for Success

**Official Documentation**:
- Threshold Docs: https://docs.threshold.network/
- tBTC v2 Design: https://docs.threshold.network/applications/tbtc-v2
- Immunefi Rules: https://immunefi.com/rules/

**Smart Contract Security**:
- Trail of Bits: https://github.com/crytic/building-secure-contracts
- Consensys Best Practices: https://consensys.github.io/smart-contract-best-practices/
- SWC Registry: https://swcregistry.io/

**Testing Tools**:
- Foundry Book: https://book.getfoundry.sh/
- Slither: https://github.com/crytic/slither
- Echidna: https://github.com/crytic/echidna

**Community**:
- Threshold Discord: https://discord.gg/threshold
- Immunefi Discord: https://discord.gg/immunefi
- Twitter: @ThresholdDAO, @immunefi

---

## Conclusion

The Threshold Network bug bounty program offers up to $1,000,000 for critical vulnerabilities. The most valuable targets are:

1. Bitcoin bridge (SPV proofs, optimistic minting)
2. Threshold cryptography (DKG, signing)
3. Cross-chain bridges (message verification)
4. Governance (flash loans, timelocks)
5. Staking (reward calculation)

**Success Formula**:
- Deep understanding of threshold cryptography
- Expertise in Bitcoin SPV proofs
- Strong Foundry/Solidity skills
- Patient, methodical testing
- Professional documentation
- Compliance with all rules

**Expected Effort**:
- 6-8 weeks for comprehensive audit
- 100-200 hours of focused research
- High probability of finding medium severity issues
- Moderate probability of high severity
- Low but non-zero probability of critical

Good luck, and happy hunting! 🎯
