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

## Conclusion

These templates provide a starting point for testing Threshold Network. Remember to:

1. **Customize** each template for your specific hypothesis
2. **Fill in** the TODO sections with actual exploit logic
3. **Verify** that tests fail appropriately (if exploit is prevented)
4. **Document** your findings clearly
5. **Never test** on mainnet directly

Good luck with your security research! 🔒
