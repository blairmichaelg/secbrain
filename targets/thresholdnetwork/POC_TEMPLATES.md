# Threshold Network PoC Templates

**Purpose**: Ready-to-use Foundry test templates for common vulnerability patterns  
**Usage**: Copy template, fill in exploit logic, run with `forge test`  
**Last Updated**: December 25, 2024

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [Template 1: SPV Proof Manipulation](#template-1-spv-proof-manipulation)
- [Template 2: Optimistic Mint Exploit](#template-2-optimistic-mint-exploit)
- [Template 3: Reentrancy Attack](#template-3-reentrancy-attack)
- [Template 4: Flash Loan Governance](#template-4-flash-loan-governance)
- [Template 5: Staking Reward Manipulation](#template-5-staking-reward-manipulation)
- [Template 6: Cross-Chain Message Forgery](#template-6-cross-chain-message-forgery)
- [Template 7: Proxy Upgrade Exploit](#template-7-proxy-upgrade-exploit)
- [Template 8: DKG Threshold-Raising Vulnerability](#template-8-dkg-threshold-raising-vulnerability)
- [Helper Functions](#helper-functions)

---

## Setup Instructions

### 1. Create Test Directory

```bash
cd targets/thresholdnetwork/instascope
mkdir -p test/exploits
```

### 2. Configure Foundry

Create or update `foundry.toml`:

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.17"
via_ir = true
optimizer = true
optimizer_runs = 200

[rpc_endpoints]
mainnet = "${ETH_RPC_URL}"

[profile.default.fuzz]
runs = 256

[profile.ci.fuzz]
runs = 10000
```

### 3. Install Dependencies

```bash
forge install foundry-rs/forge-std
```

### 4. Set Environment Variables

```bash
export ETH_RPC_URL="https://eth.llamarpc.com"
export FORK_BLOCK=18500000  # Use recent block number
```

---

## Template 1: SPV Proof Manipulation

**File**: `test/exploits/SPVProofExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title SPV Proof Manipulation Exploit
 * @notice Tests for Bitcoin SPV proof verification vulnerabilities
 * @dev Tests unauthorized tBTC minting via fake Bitcoin transaction proofs
 */
contract SPVProofExploit is Test {
    // Mainnet contract addresses
    address constant TBTC = 0x18084fbA666a33d37592fA2633fD49a74DD93a88;
    address constant BRIDGE = 0x8d014903bf7867260584d714e11809fea5293234;
    address constant VAULT = 0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD;
    address constant LIGHT_RELAY = 0x836cdFE63fe2d63f8Bdb69b96f6097F36635896E;
    
    // Test actors
    address attacker = address(0x1337);
    
    // Interfaces
    interface ITBTC {
        function balanceOf(address) external view returns (uint256);
        function totalSupply() external view returns (uint256);
    }
    
    interface IBridge {
        function revealDeposit(
            bytes calldata fundingTx,
            bytes calldata fundingOutputIndex
        ) external;
        
        function deposits(bytes32) external view returns (
            address depositor,
            uint64 amount,
            uint32 revealedAt,
            bytes32 walletPubKeyHash,
            bytes20 refundPubKeyHash,
            bytes4 blindingFactor,
            bytes20 refundLocktime
        );
    }
    
    ITBTC tbtc = ITBTC(TBTC);
    IBridge bridge = IBridge(BRIDGE);
    
    function setUp() public {
        // Fork mainnet at specific block
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
        
        // Label addresses for better traces
        vm.label(TBTC, "TBTC");
        vm.label(BRIDGE, "Bridge");
        vm.label(VAULT, "TBTCVault");
        vm.label(LIGHT_RELAY, "LightRelay");
        vm.label(attacker, "Attacker");
    }
    
    /**
     * @notice Test Case 1: Fake Bitcoin Transaction
     * @dev Attempt to mint tBTC with completely fabricated Bitcoin transaction
     */
    function testFakeBitcoinTransaction() public {
        // Record initial state
        uint256 initialSupply = tbtc.totalSupply();
        uint256 initialBalance = tbtc.balanceOf(attacker);
        
        console.log("Initial TBTC supply:", initialSupply);
        console.log("Initial attacker balance:", initialBalance);
        
        // Create fake Bitcoin transaction
        // TODO: Craft malformed/fake transaction bytes
        bytes memory fakeTx = hex""; // Fill in fake tx
        bytes memory fakeOutputIndex = hex""; // Fill in fake output
        
        // Attempt to reveal fake deposit
        vm.startPrank(attacker);
        
        // This should revert with proper validation
        vm.expectRevert();
        bridge.revealDeposit(fakeTx, fakeOutputIndex);
        
        vm.stopPrank();
        
        // Verify no tBTC was minted
        uint256 finalSupply = tbtc.totalSupply();
        uint256 finalBalance = tbtc.balanceOf(attacker);
        
        assertEq(finalSupply, initialSupply, "Supply should not change");
        assertEq(finalBalance, initialBalance, "Balance should not change");
    }
    
    /**
     * @notice Test Case 2: Replay Attack
     * @dev Attempt to reveal same Bitcoin deposit multiple times
     */
    function testDepositReplay() public {
        // TODO: Use a real Bitcoin transaction from mainnet
        bytes memory realTx = hex""; // Fill in from real deposit
        bytes memory realOutput = hex""; // Fill in real output
        
        vm.startPrank(attacker);
        
        // First reveal (should succeed if tx is valid and not yet revealed)
        // May fail if already revealed on mainnet
        try bridge.revealDeposit(realTx, realOutput) {
            console.log("First reveal succeeded");
            
            // Second reveal (should always fail)
            vm.expectRevert();
            bridge.revealDeposit(realTx, realOutput);
            console.log("Second reveal correctly rejected");
        } catch {
            console.log("First reveal failed (expected if already revealed)");
        }
        
        vm.stopPrank();
    }
    
    /**
     * @notice Test Case 3: Invalid Merkle Proof
     * @dev Test with valid Bitcoin tx but invalid merkle proof
     */
    function testInvalidMerkleProof() public {
        // TODO: Implement merkle proof manipulation
        // Valid transaction but wrong proof
        
        console.log("Testing invalid merkle proof...");
        
        // Should be rejected by proof verification
    }
    
    /**
     * @notice Test Case 4: Insufficient Confirmations
     * @dev Test with Bitcoin transaction that has < 6 confirmations
     */
    function testInsufficientConfirmations() public {
        // TODO: Simulate recent Bitcoin transaction
        // Bridge requires 6 confirmations
        
        console.log("Testing insufficient confirmations...");
        
        // Should be rejected
    }
    
    /**
     * @notice Helper: Decode Bitcoin transaction
     * @dev Utility to parse Bitcoin transaction structure
     */
    function decodeBitcoinTx(bytes memory txBytes) internal pure returns (
        bytes32 txHash,
        uint256 outputCount,
        uint256 outputValue
    ) {
        // TODO: Implement Bitcoin tx parsing
        // Reference: https://github.com/summa-tx/bitcoin-spv
    }
}
```

---

## Template 2: Optimistic Mint Exploit

**File**: `test/exploits/OptimisticMintExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title Optimistic Mint Exploit
 * @notice Tests for optimistic minting vulnerabilities
 * @dev Focus on minting without Bitcoin deposit and challenge bypass
 */
contract OptimisticMintExploit is Test {
    address constant VAULT = 0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD;
    address constant TBTC = 0x18084fbA666a33d37592fA2633fD49a74DD93a88;
    address constant BRIDGE = 0x8d014903bf7867260584d714e11809fea5293234;
    
    address attacker = address(0x1337);
    address guardian = address(0x999); // Actual guardian from contract
    
    interface ITBTCVault {
        function requestOptimisticMint(
            bytes32 depositKey,
            uint64 amount
        ) external;
        
        function finalizeOptimisticMint(bytes32 depositKey) external;
        
        function cancelOptimisticMint(bytes32 depositKey) external;
        
        function optimisticMintingRequests(bytes32) external view returns (
            uint64 requestedAt,
            uint64 finalizedAt,
            uint64 amount,
            address depositor
        );
    }
    
    interface ITBTC {
        function balanceOf(address) external view returns (uint256);
    }
    
    ITBTCVault vault = ITBTCVault(VAULT);
    ITBTC tbtc = ITBTC(TBTC);
    
    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
        vm.label(VAULT, "TBTCVault");
        vm.label(TBTC, "TBTC");
        vm.label(attacker, "Attacker");
    }
    
    /**
     * @notice Test Case 1: Optimistic Mint Without Bitcoin
     * @dev Try to request and finalize mint without depositing BTC
     */
    function testOptimisticMintWithoutBitcoin() public {
        uint256 initialBalance = tbtc.balanceOf(attacker);
        console.log("Initial balance:", initialBalance);
        
        // Create deposit key (would normally come from Bitcoin deposit)
        bytes32 fakeDepositKey = keccak256(abi.encode(attacker, block.timestamp));
        uint64 amount = 1 ether; // 1 tBTC
        
        vm.startPrank(attacker);
        
        // Attempt to request optimistic mint
        // Should fail without guardian authorization
        vm.expectRevert();
        vault.requestOptimisticMint(fakeDepositKey, amount);
        
        vm.stopPrank();
        
        // Even if we could request, finalize should fail
        // because no actual Bitcoin deposit exists
    }
    
    /**
     * @notice Test Case 2: Challenge Period Bypass
     * @dev Try to finalize before 3-hour challenge period ends
     */
    function testChallengePeriodBypass() public {
        // TODO: Get valid optimistic mint request
        // Try to finalize immediately
        
        bytes32 depositKey = bytes32(0);
        
        vm.startPrank(attacker);
        
        // Should fail if challenge period not elapsed
        vm.expectRevert();
        vault.finalizeOptimisticMint(depositKey);
        
        vm.stopPrank();
    }
    
    /**
     * @notice Test Case 3: Cancellation Prevention
     * @dev Try to prevent cancellation of fraudulent mint
     */
    function testCancellationPrevention() public {
        // TODO: Request optimistic mint
        // Try to prevent cancellation via reentrancy or state manipulation
        
        console.log("Testing cancellation prevention...");
    }
    
    /**
     * @notice Test Case 4: Debt Manipulation
     * @dev Try to manipulate debt tracking to exceed limits
     */
    function testDebtManipulation() public {
        // TODO: Check debt tracking mechanism
        // Try to mint more than allowed debt
        
        console.log("Testing debt manipulation...");
    }
    
    /**
     * @notice Test Case 5: Concurrent Optimistic Mints
     * @dev Request multiple optimistic mints in same block
     */
    function testConcurrentOptimisticMints() public {
        // Multiple requests with same or different deposit keys
        // Check for race conditions
        
        console.log("Testing concurrent mints...");
    }
}
```

---

## Template 3: Reentrancy Attack

**File**: `test/exploits/ReentrancyExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title Reentrancy Exploit
 * @notice Tests for reentrancy vulnerabilities in Threshold Network
 * @dev Focus on cross-function and read-only reentrancy
 */
contract ReentrancyExploit is Test {
    address constant VAULT = 0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD;
    address constant BRIDGE = 0x8d014903bf7867260584d714e11809fea5293234;
    address constant STAKING = 0xf5a2ccfea213cb3ff0799e0c33ea2fa3da7cbb65;
    
    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
    }
    
    /**
     * @notice Test Case 1: Mint/Burn Reentrancy
     * @dev Try to reenter mint during burn or vice versa
     */
    function testMintBurnReentrancy() public {
        ReentrancyAttacker attacker = new ReentrancyAttacker();
        
        // Setup attacker with initial balance
        // Attempt reentrancy
        
        console.log("Testing mint/burn reentrancy...");
    }
    
    /**
     * @notice Test Case 2: Stake/Unstake Reentrancy
     * @dev Try to reenter during stake/unstake operations
     */
    function testStakeReentrancy() public {
        console.log("Testing stake reentrancy...");
    }
    
    /**
     * @notice Test Case 3: Read-Only Reentrancy
     * @dev Exploit view functions during state transitions
     */
    function testReadOnlyReentrancy() public {
        console.log("Testing read-only reentrancy...");
    }
}

/**
 * @title Reentrancy Attacker Contract
 * @dev Helper contract to execute reentrancy attacks
 */
contract ReentrancyAttacker {
    address public target;
    bool public attacking;
    
    function setTarget(address _target) external {
        target = _target;
    }
    
    function attack() external {
        attacking = true;
        // TODO: Call vulnerable function
    }
    
    // Callback for reentrancy
    receive() external payable {
        if (attacking) {
            // TODO: Reentrant call
        }
    }
}
```

---

## Template 4: Flash Loan Governance

**File**: `test/exploits/FlashLoanGovernance.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title Flash Loan Governance Attack
 * @notice Tests for flash loan attacks on governance
 * @dev Modern governance should use snapshots to prevent this
 */
contract FlashLoanGovernanceExploit is Test {
    address constant T_TOKEN = 0xCdF7028ceAB81fA0C6971208e83fa7872994beE5;
    address constant GOVERNOR = 0xd101f2b25bcbf992bdf55db67c104fe7646f5447;
    
    // Flash loan provider (e.g., Uniswap V3, Aave)
    address constant FLASH_LOAN_PROVIDER = 0x0000000000000000000000000000000000000000;
    
    address attacker = address(0x1337);
    
    interface IToken {
        function balanceOf(address) external view returns (uint256);
        function delegate(address) external;
        function transfer(address, uint256) external returns (bool);
    }
    
    interface IGovernor {
        function propose(
            address[] memory targets,
            uint256[] memory values,
            bytes[] memory calldatas,
            string memory description
        ) external returns (uint256);
        
        function castVote(uint256 proposalId, uint8 support) external returns (uint256);
        
        function getVotes(address account, uint256 blockNumber) external view returns (uint256);
    }
    
    IToken token = IToken(T_TOKEN);
    IGovernor governor = IGovernor(GOVERNOR);
    
    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
        vm.label(T_TOKEN, "T Token");
        vm.label(GOVERNOR, "Governor");
    }
    
    /**
     * @notice Test Case 1: Flash Loan Vote
     * @dev Try to vote with flash loaned tokens
     */
    function testFlashLoanVote() public {
        uint256 initialVotingPower = governor.getVotes(attacker, block.number - 1);
        console.log("Initial voting power:", initialVotingPower);
        
        // Modern governance uses checkpoints/snapshots
        // Flash loan in current block shouldn't affect voting power
        
        vm.startPrank(attacker);
        
        // TODO: Execute flash loan
        // TODO: Attempt to vote
        // Should fail if snapshot-based voting is implemented
        
        vm.stopPrank();
        
        console.log("Flash loan vote test complete");
    }
    
    /**
     * @notice Test Case 2: Delegation Flash Loan
     * @dev Flash loan -> delegate -> vote -> return
     */
    function testDelegationFlashLoan() public {
        console.log("Testing delegation flash loan...");
        
        // Should be prevented by voting delay and snapshots
    }
    
    /**
     * @notice Test Case 3: Proposal Creation with Flash Loan
     * @dev Try to meet proposal threshold with flash loaned tokens
     */
    function testProposalCreationFlashLoan() public {
        console.log("Testing proposal creation flash loan...");
        
        // Check if proposal threshold can be bypassed
    }
}
```

---

## Template 5: Staking Reward Manipulation

**File**: `test/exploits/StakingRewardExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title Staking Reward Manipulation
 * @notice Tests for reward calculation vulnerabilities
 * @dev Focus on rounding errors and reward inflation
 */
contract StakingRewardExploit is Test {
    address constant STAKING = 0xf5a2ccfea213cb3ff0799e0c33ea2fa3da7cbb65;
    address constant T_TOKEN = 0xCdF7028ceAB81fA0C6971208e83fa7872994beE5;
    
    address attacker = address(0x1337);
    
    interface IStaking {
        function stake(address stakingProvider, uint96 amount) external;
        function unstake(address stakingProvider, uint96 amount) external;
        function getReward(address stakingProvider) external;
        function earned(address account) external view returns (uint256);
    }
    
    interface IToken {
        function balanceOf(address) external view returns (uint256);
        function approve(address, uint256) external returns (bool);
    }
    
    IStaking staking = IStaking(STAKING);
    IToken token = IToken(T_TOKEN);
    
    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
        vm.label(STAKING, "TokenStaking");
        vm.label(T_TOKEN, "T Token");
    }
    
    /**
     * @notice Test Case 1: Reward Rounding Error
     * @dev Stake minimal amounts many times to accumulate rounding errors
     */
    function testRewardRoundingError() public {
        console.log("Testing reward rounding errors...");
        
        // TODO: Stake minimal amount
        // TODO: Calculate expected vs actual rewards
        // TODO: Check for profitable rounding errors
    }
    
    /**
     * @notice Test Case 2: Reward Front-Running
     * @dev Stake before reward distribution, unstake after
     */
    function testRewardFrontRunning() public {
        console.log("Testing reward front-running...");
        
        // TODO: Monitor for reward distribution tx
        // TODO: Front-run with stake
        // TODO: Back-run with unstake
    }
    
    /**
     * @notice Test Case 3: Double Claiming
     * @dev Try to claim same rewards multiple times
     */
    function testDoubleClaiming() public {
        vm.startPrank(attacker);
        
        // TODO: Claim rewards
        uint256 earned1 = staking.earned(attacker);
        
        // TODO: Try to claim again
        // Should track claimed amounts
        
        vm.stopPrank();
        
        console.log("Earned after second claim:", earned1);
    }
    
    /**
     * @notice Test Case 4: Reward Calculation Overflow
     * @dev Test extreme values for reward calculation
     */
    function testRewardCalculationOverflow() public {
        console.log("Testing reward calculation overflow...");
        
        // TODO: Test with maximum stake amounts
        // TODO: Test with extreme time periods
    }
}
```

---

## Template 6: Cross-Chain Message Forgery

**File**: `test/exploits/CrossChainExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title Cross-Chain Message Forgery
 * @notice Tests for cross-chain bridge vulnerabilities
 * @dev Focus on Wormhole and Starknet integration
 */
contract CrossChainExploit is Test {
    address constant WORMHOLE_DEPOSITOR = 0x9a5250c7bea10f7472eb9d50bb757b83d67fb5ed;
    address constant WORMHOLE_REDEEMER = 0x14d93d4c4e07130fffe6083432b66b96d8eb9dc0;
    address constant STARKNET_BRIDGE = 0xf39d314c5ad7dc88958116dfa7d5ac095d563aff;
    
    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
    }
    
    /**
     * @notice Test Case 1: Wormhole Message Forgery
     * @dev Try to forge Wormhole VAA (Verified Action Approval)
     */
    function testWormholeMessageForgery() public {
        console.log("Testing Wormhole message forgery...");
        
        // TODO: Create fake Wormhole VAA
        // TODO: Submit to depositor/redeemer
        // Should be rejected by guardian signature verification
    }
    
    /**
     * @notice Test Case 2: Replay Attack
     * @dev Replay valid cross-chain message
     */
    function testCrossChainReplay() public {
        console.log("Testing cross-chain replay...");
        
        // TODO: Get valid message from past
        // TODO: Try to replay
        // Should be prevented by sequence numbers
    }
    
    /**
     * @notice Test Case 3: Chain ID Manipulation
     * @dev Send message for wrong chain
     */
    function testChainIDManipulation() public {
        console.log("Testing chain ID manipulation...");
        
        // TODO: Message from testnet to mainnet
        // Should be rejected
    }
}
```

---

## Template 7: Proxy Upgrade Exploit

**File**: `test/exploits/ProxyUpgradeExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title Proxy Upgrade Exploit
 * @notice Tests for proxy pattern vulnerabilities
 * @dev Focus on unauthorized upgrades and storage collisions
 */
contract ProxyUpgradeExploit is Test {
    // Example proxy (many exist in Threshold Network)
    address constant PROXY = 0x46d52E41C2F300BC82217Ce22b920c34995204eb;
    
    address attacker = address(0x1337);
    address admin; // Will be fetched from proxy
    
    interface IProxy {
        function upgradeTo(address newImplementation) external;
        function upgradeToAndCall(address newImplementation, bytes calldata data) external payable;
        function admin() external view returns (address);
        function implementation() external view returns (address);
    }
    
    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
        
        // Get actual admin
        IProxy proxy = IProxy(PROXY);
        admin = proxy.admin();
        
        vm.label(PROXY, "Proxy");
        vm.label(admin, "Admin");
        vm.label(attacker, "Attacker");
    }
    
    /**
     * @notice Test Case 1: Unauthorized Upgrade
     * @dev Try to upgrade without admin privileges
     */
    function testUnauthorizedUpgrade() public {
        address maliciousImplementation = address(new MaliciousImplementation());
        
        vm.startPrank(attacker);
        
        // Should revert - only admin can upgrade
        vm.expectRevert();
        IProxy(PROXY).upgradeTo(maliciousImplementation);
        
        vm.stopPrank();
        
        console.log("Unauthorized upgrade correctly rejected");
    }
    
    /**
     * @notice Test Case 2: Storage Collision
     * @dev Upgrade to implementation with incompatible storage
     */
    function testStorageCollision() public {
        // TODO: Create implementation with different storage layout
        // Upgrade (as admin)
        // Check for storage corruption
        
        console.log("Testing storage collision...");
    }
    
    /**
     * @notice Test Case 3: Uninitialized Implementation
     * @dev Try to call initialize on implementation directly
     */
    function testUninitializedImplementation() public {
        IProxy proxy = IProxy(PROXY);
        address impl = proxy.implementation();
        
        // Try to initialize implementation directly
        // Should be prevented by initializer modifier
        
        console.log("Testing uninitialized implementation...");
    }
}

/**
 * @title Malicious Implementation
 * @dev Example malicious implementation for testing
 */
contract MaliciousImplementation {
    function stealFunds() external {
        // Malicious logic
    }
}
```

---

## Helper Functions

### Bitcoin Transaction Helpers

```solidity
library BitcoinTxHelper {
    /**
     * @notice Parse Bitcoin transaction
     * @dev Extract relevant information from Bitcoin tx bytes
     */
    function parseTx(bytes memory txBytes) internal pure returns (
        bytes32 txHash,
        uint256 outputCount,
        uint256 totalValue
    ) {
        // TODO: Implement Bitcoin tx parsing
        // Reference: github.com/summa-tx/bitcoin-spv
    }
    
    /**
     * @notice Create fake Bitcoin transaction
     * @dev For testing purposes only
     */
    function createFakeTx(
        address recipient,
        uint256 amount
    ) internal pure returns (bytes memory) {
        // TODO: Construct malformed Bitcoin transaction
    }
}
```

### Merkle Proof Helpers

```solidity
library MerkleHelper {
    /**
     * @notice Verify Merkle proof
     * @dev Check if leaf is part of merkle tree
     */
    function verify(
        bytes32[] memory proof,
        bytes32 root,
        bytes32 leaf
    ) internal pure returns (bool) {
        bytes32 computedHash = leaf;
        
        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 proofElement = proof[i];
            
            if (computedHash <= proofElement) {
                computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
            } else {
                computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
            }
        }
        
        return computedHash == root;
    }
    
    /**
     * @notice Create fake Merkle proof
     * @dev For testing proof verification
     */
    function createFakeProof(bytes32 leaf) internal pure returns (bytes32[] memory) {
        bytes32[] memory proof = new bytes32[](1);
        proof[0] = keccak256(abi.encodePacked(leaf));
        return proof;
    }
}
```

### Signature Helpers

```solidity
library SignatureHelper {
    /**
     * @notice Create ECDSA signature
     * @dev For testing signature verification
     */
    function createSignature(
        bytes32 messageHash,
        uint256 privateKey
    ) internal pure returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(privateKey, messageHash);
        return abi.encodePacked(r, s, v);
    }
    
    /**
     * @notice Recover signer from signature
     */
    function recoverSigner(
        bytes32 messageHash,
        bytes memory signature
    ) internal pure returns (address) {
        require(signature.length == 65, "Invalid signature length");
        
        bytes32 r;
        bytes32 s;
        uint8 v;
        
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
        
        return ecrecover(messageHash, v, r, s);
    }
}
```

---

## Running Tests

### Single Test

```bash
# Run specific test
forge test --match-test testFakeBitcoinTransaction -vvvv

# Run specific contract
forge test --match-contract SPVProofExploit -vvvv
```

### All Tests

```bash
# Run all exploit tests
forge test --match-path "test/exploits/*" -vvvv

# With gas reporting
forge test --match-path "test/exploits/*" --gas-report

# Generate coverage
forge coverage --match-path "test/exploits/*"
```

### Debug Failed Test

```bash
# Maximum verbosity
forge test --match-test testName -vvvvv

# With traces
forge test --match-test testName --debug
```

---

## Best Practices

### 1. Always Test on Fork

```solidity
function setUp() public {
    // Always fork mainnet
    vm.createSelectFork(vm.rpcUrl("mainnet"), BLOCK_NUMBER);
}
```

### 2. Label Addresses

```solidity
vm.label(address, "ReadableName");
```

### 3. Log Important State

```solidity
console.log("Important value:", value);
console.logBytes32(hash);
console.logAddress(addr);
```

### 4. Use Proper Assertions

```solidity
// Good
assertEq(actual, expected, "Values should match");
assertGt(profit, 0, "Should be profitable");

// Bad
assert(actual == expected);
```

### 5. Document Expected Behavior

```solidity
/**
 * @notice Clear test description
 * @dev What should happen vs what shouldn't
 */
function testSomething() public {
    // Setup
    // Execute
    // Verify
}
```

---

## Template 8: DKG Threshold-Raising Vulnerability

**File**: `test/exploits/DKGThresholdRaisingExploit.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "forge-std/Test.sol";

/**
 * @title DKG Threshold-Raising Vulnerability Test
 * @notice Tests for polynomial degree validation in DKG result submission
 * @dev Critical vulnerability: Permanent freezing of all tBTC funds in new wallets
 * 
 * Vulnerability Description:
 * - The DKG (Distributed Key Generation) protocol should enforce that the
 *   commitment polynomial degree matches the expected threshold parameter
 * - If validation is missing, malicious operators can submit a higher-degree
 *   polynomial, which makes the resulting wallet unable to sign transactions
 * - This causes PERMANENT FREEZING of all Bitcoin deposited to that wallet
 * 
 * Expected Check (should exist):
 *   require(result.groupCommitment.length == threshold + 1, "Invalid polynomial degree");
 * 
 * References:
 * - FROST DKG vulnerability: https://eprint.iacr.org/2020/852.pdf
 * - Trail of Bits threshold cryptography audits
 * - Safeheron DKG implementation vulnerabilities
 */
contract DKGThresholdRaisingExploit is Test {
    // Mainnet contract addresses
    address constant WALLET_REGISTRY = 0x9C070027cdC9dc8F82416B2e5314E11DFb4FE3CD;
    address constant DKG_VALIDATOR = 0x5499f54b4a1cb4816eefcf78962040461be3d80b; // EcdsaDkgValidator
    address constant BRIDGE = 0x8d014903bf7867260584d714e11809fea5293234;
    address constant SORTITION_POOL = 0x6aed6cC30D1b2770771052555d257Da86eD47fe8;
    
    // Test actors
    address operator1 = address(0x1001);
    address operator2 = address(0x1002);
    address operator3 = address(0x1003);
    address attacker = address(0x1337);
    
    // Interfaces
    interface IWalletRegistry {
        function submitDkgResult(DkgResult calldata result) external;
        function dkgParameters() external view returns (
            uint256 seedTimeout,
            uint256 resultChallengePeriodLength,
            uint256 resultChallengeExtraGas,
            uint256 submissionTimeout,
            uint256 submitterPrecedencePeriodLength
        );
        function getWalletCreationState() external view returns (uint256);
    }
    
    interface IDkgValidator {
        function validate(
            DkgResult calldata result,
            uint256 seed,
            uint256 startBlock
        ) external view returns (bool, string memory);
    }
    
    // DKG Result structure (based on Threshold Network contracts)
    struct DkgResult {
        bytes32 submitterMemberIndex;
        bytes groupPubKey;  // 64 bytes for uncompressed ECDSA public key
        uint8[] misbehavedMembersIndices;
        bytes signatures;  // Concatenated signatures from honest operators
        uint256[] signingMembersIndices;
        uint32[] members;
        bytes32 membersHash;
        // CRITICAL: groupCommitment array - its length should equal threshold + 1
        bytes[] groupCommitment;  // This is the vulnerability target
    }
    
    function setUp() public {
        // Fork mainnet at a recent block
        vm.createSelectFork(vm.rpcUrl("mainnet"), 18500000);
    }
    
    /**
     * @notice Test Case 1: Validate Normal DKG Result
     * @dev Baseline test - submit valid DKG result with correct polynomial degree
     */
    function testValidDkgResultSubmission() public {
        console.log("=== Test Case 1: Valid DKG Result ===");
        
        IWalletRegistry registry = IWalletRegistry(WALLET_REGISTRY);
        
        // Get expected threshold from contract
        // Note: threshold is typically 51 out of 100 operators for Threshold Network
        uint256 expectedThreshold = 51;
        
        // Create a valid DKG result with groupCommitment.length == threshold + 1
        DkgResult memory validResult = _createDkgResult(expectedThreshold + 1);
        
        console.log("Expected threshold:", expectedThreshold);
        console.log("Valid commitment length:", validResult.groupCommitment.length);
        console.log("Should be:", expectedThreshold + 1);
        
        vm.startPrank(operator1);
        
        // This should succeed (or revert with unrelated errors, not polynomial degree error)
        try registry.submitDkgResult(validResult) {
            console.log("Valid DKG result accepted (expected)");
        } catch Error(string memory reason) {
            console.log("Reverted with:", reason);
            // Analyze revert reason - should NOT be about polynomial degree
            assertFalse(
                _containsString(reason, "polynomial") || _containsString(reason, "degree"),
                "Valid result rejected due to polynomial degree - unexpected"
            );
        }
        
        vm.stopPrank();
    }
    
    /**
     * @notice Test Case 2: CRITICAL - Submit DKG Result with Higher Polynomial Degree
     * @dev This is the vulnerability test - submit result with commitment.length > threshold + 1
     * 
     * EXPECTED BEHAVIOR (if vulnerability exists):
     *   - submitDkgResult accepts the malformed result
     *   - New wallet is created with invalid polynomial
     *   - Wallet cannot sign transactions (permanent fund lock)
     * 
     * EXPECTED BEHAVIOR (if patched):
     *   - submitDkgResult reverts with "Invalid polynomial degree" or similar
     */
    function testDkgThresholdRaisingAttack() public {
        console.log("=== Test Case 2: DKG Threshold-Raising Attack ===");
        
        IWalletRegistry registry = IWalletRegistry(WALLET_REGISTRY);
        
        uint256 expectedThreshold = 51;
        
        // ATTACK: Create DKG result with higher polynomial degree
        // Instead of threshold + 1 = 52, we use 54 (threshold + 3)
        uint256 maliciousCommitmentLength = expectedThreshold + 3;
        DkgResult memory maliciousResult = _createDkgResult(maliciousCommitmentLength);
        
        console.log("Expected threshold:", expectedThreshold);
        console.log("Expected commitment length:", expectedThreshold + 1);
        console.log("MALICIOUS commitment length:", maliciousResult.groupCommitment.length);
        console.log("Degree difference:", maliciousResult.groupCommitment.length - (expectedThreshold + 1));
        
        vm.startPrank(attacker);
        
        bool vulnerabilityExists = false;
        
        try registry.submitDkgResult(maliciousResult) {
            console.log("!!! CRITICAL VULNERABILITY CONFIRMED !!!");
            console.log("Malicious DKG result with higher polynomial degree was ACCEPTED");
            console.log("Impact: All funds deposited to this wallet will be PERMANENTLY FROZEN");
            console.log("Severity: CRITICAL - Protocol Insolvency");
            console.log("Max Bounty: $1,000,000");
            vulnerabilityExists = true;
            
            // Document the vulnerability
            emit log_named_string("Vulnerability", "DKG_THRESHOLD_RAISING");
            emit log_named_uint("Malicious Commitment Length", maliciousResult.groupCommitment.length);
            emit log_named_uint("Expected Commitment Length", expectedThreshold + 1);
            
        } catch Error(string memory reason) {
            console.log("Malicious DKG result REJECTED:", reason);
            
            // Check if rejection was due to polynomial degree validation
            if (_containsString(reason, "polynomial") || 
                _containsString(reason, "degree") || 
                _containsString(reason, "commitment length") ||
                _containsString(reason, "Invalid degree")) {
                console.log("SAFE: Contract validates polynomial degree");
                vulnerabilityExists = false;
            } else {
                console.log("WARNING: Rejected for different reason - check manually");
                console.log("Revert reason:", reason);
            }
        } catch {
            console.log("Malicious DKG result rejected (generic revert)");
            console.log("Need manual code review to confirm if degree validation exists");
        }
        
        vm.stopPrank();
        
        // If vulnerability exists, this would be a critical finding
        if (vulnerabilityExists) {
            console.log("\n=== EXPLOIT STEPS ===");
            console.log("1. Coordinate with enough malicious operators off-chain");
            console.log("2. Generate DKG result with commitment.length > threshold + 1");
            console.log("3. Submit via submitDkgResult()");
            console.log("4. If accepted, all future Bitcoin deposits to this wallet are frozen");
            console.log("5. Protocol insolvency - users cannot recover funds");
            
            console.log("\n=== MITIGATION ===");
            console.log("Add to EcdsaDkgValidator.validate():");
            console.log("  require(result.groupCommitment.length == threshold + 1, 'Invalid polynomial degree');");
        }
    }
    
    /**
     * @notice Test Case 3: Verify DKG Validator Logic
     * @dev Direct test of the DkgValidator.validate function
     */
    function testDkgValidatorPolynomialCheck() public {
        console.log("=== Test Case 3: DKG Validator Polynomial Check ===");
        
        IDkgValidator validator = IDkgValidator(DKG_VALIDATOR);
        
        uint256 expectedThreshold = 51;
        uint256 seed = uint256(keccak256("test_seed"));
        uint256 startBlock = block.number - 100;
        
        // Test 1: Valid commitment length
        DkgResult memory validResult = _createDkgResult(expectedThreshold + 1);
        (bool isValid, string memory errorMsg) = validator.validate(validResult, seed, startBlock);
        
        console.log("Valid result validation:", isValid);
        if (!isValid) {
            console.log("Error:", errorMsg);
        }
        
        // Test 2: Invalid (higher) commitment length
        DkgResult memory invalidResult = _createDkgResult(expectedThreshold + 3);
        (bool isInvalid, string memory invalidErrorMsg) = validator.validate(invalidResult, seed, startBlock);
        
        console.log("Invalid result validation:", isInvalid);
        console.log("Error:", invalidErrorMsg);
        
        // VULNERABILITY CHECK: If both return true, vulnerability exists
        if (isValid && isInvalid) {
            console.log("!!! VULNERABILITY: Validator accepts both valid and invalid polynomial degrees !!!");
        } else if (!isInvalid) {
            console.log("SAFE: Validator rejects invalid polynomial degree");
        }
    }
    
    /**
     * @notice Test Case 4: End-to-End Impact Simulation
     * @dev Simulate the full impact if vulnerability is exploited
     */
    function testE2EFundFreezingImpact() public {
        console.log("=== Test Case 4: End-to-End Fund Freezing Impact ===");
        
        // Step 1: Malicious DKG result is submitted and accepted
        console.log("\n[Step 1] Malicious operators submit invalid DKG result");
        console.log("  - Polynomial degree: threshold + 3 instead of threshold + 1");
        
        // Step 2: New wallet is created with invalid polynomial
        console.log("\n[Step 2] New wallet created with ID: wallet_123");
        console.log("  - Public key is derived from invalid polynomial");
        console.log("  - Wallet appears normal but CANNOT sign transactions");
        
        // Step 3: Users deposit Bitcoin to this wallet
        uint256 depositAmount = 10 ether; // 10 BTC worth of value
        console.log("\n[Step 3] Users deposit Bitcoin to compromised wallet");
        console.log("  - Total deposits: 10 BTC (~$400,000 at current prices)");
        
        // Step 4: Users try to redeem/withdraw
        console.log("\n[Step 4] Users request redemption");
        console.log("  - Redemption requires threshold signature from wallet");
        console.log("  - Wallet operators cannot produce valid signature (invalid polynomial)");
        console.log("  - Transaction fails - FUNDS PERMANENTLY FROZEN");
        
        // Impact summary
        console.log("\n=== IMPACT SUMMARY ===");
        console.log("Financial Impact: PERMANENT LOSS of all deposited funds");
        console.log("Affected Amount: Unlimited (all future deposits to compromised wallet)");
        console.log("Severity: CRITICAL");
        console.log("Classification: Protocol Insolvency");
        console.log("Immunefi Bounty: $100,000 - $1,000,000");
        
        console.log("\n=== ATTACK FEASIBILITY ===");
        console.log("Prerequisites:");
        console.log("  - Coordination of malicious operators (off-chain)");
        console.log("  - No slashing if DKG result is technically valid but semantically wrong");
        console.log("Difficulty: MEDIUM (requires operator coordination)");
        console.log("Detection: HARD (wallet appears normal until signing is attempted)");
    }
    
    // ============================================
    // HELPER FUNCTIONS
    // ============================================
    
    /**
     * @notice Create mock DKG result for testing
     * @param commitmentLength Length of the groupCommitment array
     */
    function _createDkgResult(uint256 commitmentLength) internal pure returns (DkgResult memory) {
        // Create mock data
        bytes memory groupPubKey = new bytes(64); // 64 bytes for uncompressed ECDSA key
        
        // Create groupCommitment with specified length
        bytes[] memory commitment = new bytes[](commitmentLength);
        for (uint256 i = 0; i < commitmentLength; i++) {
            commitment[i] = abi.encodePacked(keccak256(abi.encodePacked("commitment", i)));
        }
        
        // Create minimal valid structure
        uint8[] memory misbehavedIndices = new uint8[](0);
        uint256[] memory signingIndices = new uint256[](51); // 51 honest signers
        uint32[] memory members = new uint32[](100); // 100 total members
        
        for (uint256 i = 0; i < 51; i++) {
            signingIndices[i] = i;
        }
        for (uint32 i = 0; i < 100; i++) {
            members[i] = i;
        }
        
        return DkgResult({
            submitterMemberIndex: bytes32(uint256(0)),
            groupPubKey: groupPubKey,
            misbehavedMembersIndices: misbehavedIndices,
            signatures: new bytes(51 * 65), // 51 signatures, 65 bytes each
            signingMembersIndices: signingIndices,
            members: members,
            membersHash: keccak256(abi.encode(members)),
            groupCommitment: commitment  // CRITICAL: This is what we're testing
        });
    }
    
    /**
     * @notice Check if string contains substring (case-insensitive)
     */
    function _containsString(string memory haystack, string memory needle) internal pure returns (bool) {
        bytes memory haystackBytes = bytes(haystack);
        bytes memory needleBytes = bytes(needle);
        
        if (needleBytes.length > haystackBytes.length) {
            return false;
        }
        
        // Simple case-insensitive substring search
        for (uint256 i = 0; i <= haystackBytes.length - needleBytes.length; i++) {
            bool found = true;
            for (uint256 j = 0; j < needleBytes.length; j++) {
                bytes1 h = haystackBytes[i + j];
                bytes1 n = needleBytes[j];
                
                // Convert to lowercase for comparison
                if (h >= 0x41 && h <= 0x5A) h = bytes1(uint8(h) + 32);
                if (n >= 0x41 && n <= 0x5A) n = bytes1(uint8(n) + 32);
                
                if (h != n) {
                    found = false;
                    break;
                }
            }
            if (found) return true;
        }
        
        return false;
    }
}
```

**Usage Instructions:**

1. **Set up environment:**
   ```bash
   export ETH_RPC_URL="https://eth.llamarpc.com"
   cd targets/thresholdnetwork/instascope
   ```

2. **Run the test:**
   ```bash
   forge test --match-contract DKGThresholdRaisingExploit -vvv
   ```

3. **Analyze results:**
   - If Test Case 2 shows "CRITICAL VULNERABILITY CONFIRMED" → Bug bounty submission
   - If Test Case 2 shows "SAFE: Contract validates polynomial degree" → Move to next hypothesis

4. **Manual code review:**
   Even if tests pass/fail, manually review `EcdsaDkgValidator.sol` for:
   ```solidity
   require(result.groupCommitment.length == threshold + 1, "Invalid polynomial degree");
   ```

**Expected Findings:**

- **VULNERABLE**: Missing polynomial degree check → $100K+ bounty
- **SAFE**: Check exists → Document and move on
- **UNCLEAR**: Need source code review to confirm

---

## Conclusion

These templates provide a starting point for testing Threshold Network. Remember to:

1. **Customize** each template for your specific hypothesis
2. **Fill in** the TODO sections with actual exploit logic
3. **Verify** that tests fail appropriately (if exploit is prevented)
4. **Document** your findings clearly
5. **Never test** on mainnet directly

Good luck with your security research! 🔒
