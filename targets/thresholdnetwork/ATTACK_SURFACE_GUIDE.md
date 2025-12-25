# Threshold Network Attack Surface Testing Guide

**Purpose**: Practical guide for systematically testing the Threshold Network attack surface  
**Audience**: Security researchers and bug bounty hunters  
**Last Updated**: December 25, 2024

## Table of Contents

- [Testing Methodology](#testing-methodology)
- [Attack Surfaces by Component](#attack-surfaces-by-component)
- [Specific Test Cases](#specific-test-cases)
- [Common Vulnerability Patterns](#common-vulnerability-patterns)
- [Testing Checklist](#testing-checklist)

---

## Testing Methodology

### Systematic Approach

1. **Component Isolation**: Test each component independently
2. **Integration Testing**: Test interactions between components
3. **Edge Case Analysis**: Focus on boundary conditions
4. **State Machine Testing**: Verify all valid state transitions
5. **Invariant Checking**: Ensure critical invariants always hold

### Tools Setup

```bash
# Required tools
forge --version  # Foundry for testing
slither --version  # Static analysis
echidna --version  # Fuzzing (optional)

# Environment setup
export ETH_RPC_URL="https://eth.llamarpc.com"
export FORK_BLOCK=18500000  # Use recent block

# Clone and build
cd targets/thresholdnetwork/instascope
forge build --via-ir
```

---

## Attack Surfaces by Component

### 1. Bitcoin Bridge (CRITICAL)

#### 1.1 SPV Proof Verification

**Location**: `Bridge.sol` - `revealDeposit()` function

**Attack Vectors**:

```solidity
// Test Case 1: Fake Bitcoin Transaction
function testFakeBitcoinTransaction() public {
    // Create a Bitcoin transaction that never happened
    bytes memory fakeTx = /* malformed tx */;
    bytes32 fakeOutputIndex = bytes32(uint256(0));
    
    // Attempt to reveal fake deposit
    vm.expectRevert();
    bridge.revealDeposit(fakeTx, fakeOutputIndex);
}

// Test Case 2: Invalid Merkle Proof
function testInvalidMerkleProof() public {
    // Valid tx but invalid merkle proof
    // Should be rejected by proof verification
}

// Test Case 3: Insufficient Confirmations
function testInsufficientConfirmations() public {
    // Bitcoin tx with < 6 confirmations
    // Should be rejected
}

// Test Case 4: Wrong Network (Testnet vs Mainnet)
function testWrongNetwork() public {
    // Bitcoin testnet transaction on mainnet bridge
    // Should be rejected by header validation
}
```

**Critical Checks to Test**:
- [ ] Transaction format validation
- [ ] Output script matches expected format
- [ ] Merkle proof verification
- [ ] Block header validation via LightRelay
- [ ] Minimum confirmations (6 blocks)
- [ ] Network magic bytes (mainnet vs testnet)
- [ ] Output amount matches expected
- [ ] Correct treasury fee calculation

#### 1.2 Deposit Replay Prevention

**Location**: `Bridge.sol` - Deposit tracking

**Attack Vectors**:

```solidity
// Test Case 1: Same UTXO Double Spend
function testDepositReplay() public {
    bytes memory validTx = /* real Bitcoin tx */;
    bytes32 outputIndex = /* valid index */;
    
    // Reveal once (should succeed)
    bridge.revealDeposit(validTx, outputIndex);
    
    // Reveal again (should fail)
    vm.expectRevert("Deposit already revealed");
    bridge.revealDeposit(validTx, outputIndex);
}

// Test Case 2: Different Block, Same UTXO
function testCrossBlockReplay() public {
    // Submit same UTXO from different blocks
    // Should detect duplicate spending
}

// Test Case 3: Reorganization Attack
function testReorgAttack() public {
    // Simulate blockchain reorganization
    // Deposit in original chain, spend in reorg
}
```

**Critical Checks to Test**:
- [ ] Deposit uniqueness tracking
- [ ] UTXO double-spend detection
- [ ] Deposit key calculation
- [ ] State persistence across transactions

#### 1.3 Optimistic Minting

**Location**: `TBTCVault.sol` - Optimistic mint functions

**Attack Vectors**:

```solidity
// Test Case 1: Mint Without Bitcoin
function testOptimisticMintWithoutBitcoin() public {
    // Request optimistic mint
    // Never submit actual Bitcoin deposit
    // Try to finalize after waiting period
    
    vm.expectRevert("No deposit found");
    vault.finalizeOptimisticMint(/* depositKey */);
}

// Test Case 2: Cancel Bypass
function testCancelBypass() public {
    // Request optimistic mint
    // Prevent cancellation during fraud period
    // Possible via reentrancy or state manipulation
}

// Test Case 3: Debt Manipulation
function testDebtManipulation() public {
    // Manipulate debt tracking to mint more than allowed
    // Test debt calculations
}

// Test Case 4: Multiple Concurrent Optimistic Mints
function testConcurrentOptimisticMints() public {
    // Request multiple optimistic mints simultaneously
    // Check for race conditions
}
```

**Critical Checks to Test**:
- [ ] Guardian authorization
- [ ] Debt tracking accuracy
- [ ] Challenge period enforcement (3 hours)
- [ ] Cancellation conditions
- [ ] Finalization requirements
- [ ] Canonical deposit verification
- [ ] Debt limits per minter

#### 1.4 Redemption Flow

**Location**: `Bridge.sol` - Redemption functions

**Attack Vectors**:

```solidity
// Test Case 1: Redemption Without Bitcoin
function testRedemptionWithoutBitcoin() public {
    // Request redemption
    // Submit fake proof of Bitcoin transfer
    // Try to unlock tBTC without sending BTC
}

// Test Case 2: Double Redemption
function testDoubleRedemption() public {
    // Redeem once
    // Try to use same proof again
}

// Test Case 3: Timeout Exploitation
function testTimeoutExploitation() public {
    // Request redemption
    // Let it timeout
    // Exploit timeout handling
}

// Test Case 4: Proof Manipulation
function testProofManipulation() public {
    // Submit valid tx to different address
    // Or wrong amount
    // Should be rejected
}
```

**Critical Checks to Test**:
- [ ] Redemption request validation
- [ ] tBTC locking during redemption
- [ ] Bitcoin transaction proof verification
- [ ] Correct recipient address
- [ ] Correct amount transferred
- [ ] Treasury fee handling
- [ ] Timeout mechanism
- [ ] Proof replay prevention

### 2. Threshold Cryptography (CRITICAL)

#### 2.1 Distributed Key Generation

**Location**: `WalletRegistry.sol` - DKG validation

**Attack Vectors**:

```solidity
// Test Case 1: Malicious DKG Result
function testMaliciousDKGResult() public {
    // Submit invalid DKG result
    // Public key not matching key shares
    // Should be rejected by validator
}

// Test Case 2: Insufficient Participants
function testInsufficientParticipants() public {
    // DKG with fewer than required operators
    // Should fail validation
}

// Test Case 3: Invalid Public Key
function testInvalidPublicKey() public {
    // DKG result with invalid ECDSA public key
    // Not on curve, or malformed
}

// Test Case 4: Operator Collusion
function testOperatorCollusion() public {
    // Simulate colluding operators
    // Control >threshold shares
    // Should not break security if threshold not reached
}
```

**Critical Checks to Test**:
- [ ] DKG result validation
- [ ] Public key derivation
- [ ] Participant count
- [ ] Stake requirements
- [ ] Timeout handling
- [ ] Result submission authorization

#### 2.2 Threshold Signing

**Attack Vectors**:

```solidity
// Test Case 1: Signature Forgery
function testSignatureForgery() public {
    // Create fake ECDSA signature
    // Without proper threshold of signers
    // Should be rejected
}

// Test Case 2: Threshold Bypass
function testThresholdBypass() public {
    // Sign with fewer than threshold operators
    // Should be impossible mathematically
}

// Test Case 3: Message Manipulation
function testMessageManipulation() public {
    // Valid signature for wrong message
    // Should fail signature verification
}
```

**Critical Checks to Test**:
- [ ] Signature verification
- [ ] Public key matching
- [ ] Message hash correctness
- [ ] Threshold enforcement

#### 2.3 Operator Management

**Location**: `WalletRegistry.sol`, `TokenStaking.sol`

**Attack Vectors**:

```solidity
// Test Case 1: Unauthorized Operator Registration
function testUnauthorizedOperatorRegistration() public {
    // Register without sufficient stake
    // Should be rejected
}

// Test Case 2: Slashing Bypass
function testSlashingBypass() public {
    // Misbehave without getting slashed
    // Or reduce slash amount
}

// Test Case 3: Stake Withdrawal During Activity
function testStakeWithdrawalDuringActivity() public {
    // Withdraw stake while part of active wallet
    // Should be prevented
}
```

**Critical Checks to Test**:
- [ ] Stake requirements
- [ ] Authorization checks
- [ ] Slashing conditions
- [ ] Lock periods
- [ ] Operator deregistration

### 3. Token Staking (HIGH)

#### 3.1 Reward Calculation

**Location**: `TokenStaking.sol` - Reward distribution

**Attack Vectors**:

```solidity
// Test Case 1: Reward Inflation
function testRewardInflation() public {
    // Exploit rounding errors
    // Or reward calculation bugs
    // To inflate personal rewards
}

// Test Case 2: Reward Front-Running
function testRewardFrontRunning() public {
    // Stake right before reward distribution
    // Unstake right after
    // Get unfair rewards
}

// Test Case 3: Double Claiming
function testDoubleClaiming() public {
    // Claim rewards multiple times
    // Should track claimed amounts
}

// Test Case 4: Rounding Error Exploitation
function testRoundingErrors() public {
    // Stake minimal amount many times
    // Accumulate rounding errors
}
```

**Critical Checks to Test**:
- [ ] Reward calculation accuracy
- [ ] Rounding error handling
- [ ] Claim tracking
- [ ] Snapshot mechanisms
- [ ] Reward per token calculation
- [ ] Minimum stake requirements

#### 3.2 Staking Mechanics

**Attack Vectors**:

```solidity
// Test Case 1: Staking Without Tokens
function testStakingWithoutTokens() public {
    // Stake without having tokens
    // Or without approval
    vm.expectRevert();
    staking.stake(user, 1000 ether);
}

// Test Case 2: Unstaking During Lock
function testUnstakingDuringLock() public {
    // Unstake before lock period ends
    vm.expectRevert();
    staking.unstake(user, amount);
}

// Test Case 3: Authorization Manipulation
function testAuthorizationManipulation() public {
    // Manipulate authorization for applications
    // Stake for one app, use for another
}
```

**Critical Checks to Test**:
- [ ] Token transfer authorization
- [ ] Lock period enforcement
- [ ] Minimum/maximum stake amounts
- [ ] Application authorization
- [ ] Delegation mechanics

### 4. Governance (HIGH)

#### 4.1 Flash Loan Attacks

**Location**: `TokenholderGovernor.sol`

**Attack Vectors**:

```solidity
// Test Case 1: Flash Loan Voting
function testFlashLoanVoting() public {
    // Take flash loan of T tokens
    // Vote on proposal
    // Repay loan in same transaction
    
    // Modern governance uses snapshots, should be prevented
}

// Test Case 2: Delegation Flash Loan
function testDelegationFlashLoan() public {
    // Flash loan -> delegate -> vote -> return
    // Check if snapshot prevents this
}
```

**Critical Checks to Test**:
- [ ] Snapshot-based voting
- [ ] Delegation delay
- [ ] Voting delay
- [ ] Block number vs timestamp

#### 4.2 Timelock Bypass

**Attack Vectors**:

```solidity
// Test Case 1: Immediate Execution
function testImmediateExecution() public {
    // Pass proposal
    // Execute without timelock delay
    vm.expectRevert();
    governor.execute(proposalId);
}

// Test Case 2: Timelock Manipulation
function testTimelockManipulation() public {
    // Manipulate block.timestamp
    // Or timelock state
}
```

**Critical Checks to Test**:
- [ ] Timelock delay enforcement
- [ ] Queue-to-execute separation
- [ ] Cancellation conditions
- [ ] Expiration handling

#### 4.3 Quorum Manipulation

**Attack Vectors**:

```solidity
// Test Case 1: Quorum Bypass
function testQuorumBypass() public {
    // Pass proposal without meeting quorum
    // Check calculation accuracy
}

// Test Case 2: Vote Counting
function testVoteCountingManipulation() public {
    // Double voting
    // Vote manipulation
}
```

**Critical Checks to Test**:
- [ ] Quorum calculation
- [ ] Vote counting accuracy
- [ ] Vote weight calculation
- [ ] Delegation handling

### 5. Cross-Chain Bridges (HIGH)

#### 5.1 Wormhole Integration

**Location**: `BTCDepositorWormhole.sol`, `L1BTCRedeemerWormhole.sol`

**Attack Vectors**:

```solidity
// Test Case 1: Message Forgery
function testWormholeMessageForgery() public {
    // Forge Wormhole message
    // Without guardian signatures
    vm.expectRevert();
}

// Test Case 2: Replay Attack
function testWormholeReplay() public {
    // Replay valid message
    // Should be prevented by sequence numbers
}

// Test Case 3: Chain ID Manipulation
function testChainIDManipulation() public {
    // Message from wrong chain
    // Should be rejected
}
```

**Critical Checks to Test**:
- [ ] Guardian signature verification
- [ ] Message hash validation
- [ ] Sequence number tracking
- [ ] Chain ID verification
- [ ] Replay protection

#### 5.2 Starknet Integration

**Location**: `StarknetTokenBridge.sol`, `StarkNetBitcoinDepositor.sol`

**Attack Vectors**:

```solidity
// Test Case 1: L1→L2 Message Manipulation
function testL1ToL2Manipulation() public {
    // Send malicious message to L2
    // Manipulate bridge state
}

// Test Case 2: L2→L1 Proof Manipulation
function testL2ToL1ProofManipulation() public {
    // Fake L2→L1 message
    // Without valid state proof
}
```

**Critical Checks to Test**:
- [ ] Message encoding
- [ ] State proof verification
- [ ] Message consumption tracking
- [ ] L1/L2 synchronization

### 6. Proxy Patterns (MEDIUM)

#### 6.1 Upgrade Mechanism

**Location**: All `TransparentUpgradeableProxy` contracts

**Attack Vectors**:

```solidity
// Test Case 1: Unauthorized Upgrade
function testUnauthorizedUpgrade() public {
    vm.prank(attacker);
    vm.expectRevert();
    proxy.upgradeTo(maliciousImplementation);
}

// Test Case 2: Storage Collision
function testStorageCollision() public {
    // Upgrade to implementation with different storage layout
    // Cause storage collision
}

// Test Case 3: Uninitialized Implementation
function testUninitializedImplementation() public {
    // Upgrade to uninitialized implementation
    // Call initialize directly
}
```

**Critical Checks to Test**:
- [ ] Upgrade authorization (admin only)
- [ ] Storage layout compatibility
- [ ] Initialization protection
- [ ] Implementation validation
- [ ] Delegatecall safety

#### 6.2 Implementation Exploitation

**Attack Vectors**:

```solidity
// Test Case 1: Selfdestruct in Implementation
function testSelfdestruct() public {
    // Implementation with selfdestruct
    // Should be prevented or handled safely
}

// Test Case 2: Function Collision
function testFunctionCollision() public {
    // Implementation function with same selector as proxy
    // Should be handled by TransparentProxy pattern
}
```

**Critical Checks to Test**:
- [ ] No selfdestruct in implementation
- [ ] No delegatecall in implementation
- [ ] Proper function visibility
- [ ] Constructor vs initializer usage

---

## Common Vulnerability Patterns

### Pattern 1: Reentrancy

**Risk Level**: HIGH in any function that:
- Makes external calls
- Modifies state after external call
- Involves token transfers

**Test Template**:

```solidity
contract ReentrancyAttacker {
    function attack() external {
        // Call vulnerable function
        // Re-enter in callback
    }
    
    receive() external payable {
        // Reentrant call
    }
}

function testReentrancy() public {
    ReentrancyAttacker attacker = new ReentrancyAttacker();
    attacker.attack();
    // Verify attack failed
}
```

**Locations to Check**:
- [ ] TBTCVault mint/burn functions
- [ ] Bridge deposit/redemption
- [ ] TokenStaking stake/unstake
- [ ] All functions with external calls

### Pattern 2: Integer Overflow/Underflow

**Risk Level**: MEDIUM (Solidity 0.8+ has built-in checks)

**But still check**:
- [ ] Unchecked blocks
- [ ] Assembly code
- [ ] External library calls

### Pattern 3: Access Control

**Risk Level**: CRITICAL

**Test Template**:

```solidity
function testUnauthorizedAccess() public {
    vm.prank(attacker);
    vm.expectRevert("Unauthorized");
    contract.privilegedFunction();
}
```

**Locations to Check**:
- [ ] All onlyOwner functions
- [ ] All role-based functions
- [ ] All internal state-changing functions
- [ ] Proxy upgrade functions

### Pattern 4: Oracle Manipulation

**Risk Level**: HIGH (if present)

**Check for**:
- [ ] Price oracles (if used)
- [ ] Timestamp manipulation
- [ ] Block number manipulation
- [ ] External data dependencies

### Pattern 5: Griefing

**Risk Level**: MEDIUM

**Check for**:
- [ ] Unbounded loops
- [ ] Forced failure via revert in callbacks
- [ ] Block stuffing vectors
- [ ] Gas griefing attacks

---

## Testing Checklist

### Pre-Testing Setup

- [ ] Foundry installed and updated
- [ ] RPC endpoint configured
- [ ] Mainnet fork working
- [ ] All contracts compiled
- [ ] Test templates prepared
- [ ] Documentation reviewed

### Critical Tests (Must Complete)

#### Bitcoin Bridge
- [ ] SPV proof verification
- [ ] Deposit replay prevention
- [ ] Optimistic mint without Bitcoin
- [ ] Optimistic mint cancellation
- [ ] Redemption proof validation
- [ ] Redemption replay prevention
- [ ] Treasury fee calculations

#### Threshold Cryptography
- [ ] DKG result validation
- [ ] Public key verification
- [ ] Threshold signature validation
- [ ] Operator authorization
- [ ] Slashing mechanism

#### Staking
- [ ] Reward calculation accuracy
- [ ] Rounding error handling
- [ ] Lock period enforcement
- [ ] Claim tracking
- [ ] Authorization mechanics

#### Governance
- [ ] Flash loan prevention
- [ ] Timelock enforcement
- [ ] Quorum validation
- [ ] Vote counting
- [ ] Delegation safety

#### Cross-Chain
- [ ] Wormhole message verification
- [ ] Starknet state proofs
- [ ] Replay protection
- [ ] Chain ID validation

#### Proxies
- [ ] Upgrade authorization
- [ ] Storage compatibility
- [ ] Initialization safety

### High-Value Tests (Recommended)

- [ ] Cross-function reentrancy
- [ ] Multi-contract interactions
- [ ] Edge cases (0, max, overflow)
- [ ] State machine invariants
- [ ] Economic attacks
- [ ] Timing attacks

### Fuzzing Tests (Advanced)

- [ ] Echidna invariant testing
- [ ] Foundry fuzz testing
- [ ] Property-based testing
- [ ] Stateful fuzzing

---

## Reporting Template

### Vulnerability Report Structure

```markdown
# [SEVERITY] Vulnerability Title

## Summary
Brief description of the vulnerability in 2-3 sentences.

## Details

### Root Cause
Explain the underlying issue in the code.

### Attack Scenario
Step-by-step walkthrough of how to exploit it.

### Impact
Quantify the impact:
- Funds at risk: $X
- Users affected: Y
- Severity justification per Immunefi V2.3

## Proof of Concept

### Setup
```bash
# Commands to reproduce
```

### Code
```solidity
// Complete test file
```

### Output
```
// Logs showing exploit success
```

## Severity Classification

Per Immunefi V2.3:
- **Severity**: Critical/High/Medium/Low
- **Category**: [Direct theft | Freezing | etc.]
- **Bounty Range**: $X - $Y

## Remediation

### Recommended Fix
```solidity
// Suggested code changes
```

### Alternative Solutions
- Option 1
- Option 2
```

---

## Resources

### Testing Tools
- Foundry: https://book.getfoundry.sh/
- Slither: https://github.com/crytic/slither
- Echidna: https://github.com/crytic/echidna
- Mythril: https://github.com/ConsenSys/mythril

### References
- Threshold Docs: https://docs.threshold.network/
- tBTC Design: https://docs.threshold.network/applications/tbtc-v2
- Immunefi: https://immunefi.com/bug-bounty/thresholdnetwork/
- SWC Registry: https://swcregistry.io/

### Community
- Discord: https://discord.gg/threshold
- GitHub: https://github.com/threshold-network

---

## Conclusion

This guide provides a systematic approach to testing the Threshold Network attack surface. Focus on:

1. **Critical Severity First**: Bitcoin bridge and threshold cryptography
2. **Understand the System**: Deep knowledge beats shallow broad testing
3. **Reproducible PoCs**: Must work on mainnet fork
4. **Professional Reports**: Clear, detailed, actionable
5. **Stay in Scope**: Follow Immunefi rules strictly

Happy hunting! 🎯
