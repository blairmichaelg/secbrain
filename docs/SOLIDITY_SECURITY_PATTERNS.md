# Advanced Solidity Security Patterns

## Overview

This document describes the advanced Solidity security patterns implemented in SecBrain for detecting and preventing state-of-the-art smart contract vulnerabilities.

## 📚 Reference Implementation Templates

SecBrain provides production-ready security pattern templates in `docs/testing-examples/`:

- **[SecureVaultTemplate.sol](../docs/testing-examples/SecureVaultTemplate.sol)** - Comprehensive reentrancy protection (classic + read-only), access control, and flash loan detection
- **[OracleSecurityTemplate.sol](../docs/testing-examples/OracleSecurityTemplate.sol)** - Chainlink integration, TWAP oracles, multi-oracle consensus, and price manipulation resistance
- **[MEVProtectionTemplate.sol](../docs/testing-examples/MEVProtectionTemplate.sol)** - Slippage protection, deadline enforcement, commit-reveal scheme, and sandwich attack prevention
- **[DeFiSecurityTests.t.sol](../docs/testing-examples/DeFiSecurityTests.t.sol)** - Comprehensive test suite for all security patterns

## Table of Contents

1. [Reentrancy Patterns](#reentrancy-patterns)
2. [Flash Loan Attack Patterns](#flash-loan-attack-patterns)
3. [Access Control Patterns](#access-control-patterns)
4. [Front-Running Protection](#front-running-protection)
5. [Oracle Security](#oracle-security)
6. [Formal Verification Hints](#formal-verification-hints)
7. [Implementation Templates](#implementation-templates)

## Reentrancy Patterns

### Classic Reentrancy

**Severity:** Critical

**Description:** Classic reentrancy attack via external call before state update.

**Detection Heuristics:**
- External call
- State update after call
- Balance transfer
- `call.value`, `transfer`, `send`

**Mitigation:**
```solidity
// Use OpenZeppelin's ReentrancyGuard
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Secure is ReentrancyGuard {
    function withdraw(uint256 amount) external nonReentrant {
        // Checks-Effects-Interactions pattern
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;  // Effect before interaction
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }
}
```

### Read-Only Reentrancy (2023 Attack Vector)

**Severity:** High

**Description:** Read-only reentrancy via view function calls during state changes. This is a newly discovered attack vector in 2023, notably used in the Curve Finance attack.

**Detection Heuristics:**
- View function
- External call in modifier
- Getters during state change
- `balanceOf`, `totalSupply`

**Mitigation:**
```solidity
// Protect view functions from read-only reentrancy
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Secure is ReentrancyGuard {
    // Add nonReentrant to view functions that read critical state
    function getBalance(address user) external view nonReentrant returns (uint256) {
        return balances[user];
    }
    
    // Or use a reentrancy lock for all state-reading functions
    modifier nonReentrantView() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _;
    }
}
```

**References:**
- [Curve LP Oracle Manipulation Post-Mortem](https://chainsecurity.com/curve-lp-oracle-manipulation-post-mortem/)
- [Read-Only Reentrancy Attacks](https://github.com/pcaversaccio/reentrancy-attacks#read-only-reentrancy)

### CEI Pattern Violation

**Severity:** High

**Description:** Violation of Checks-Effects-Interactions pattern.

**Mitigation:**
```solidity
// Follow Checks-Effects-Interactions (CEI) pattern
function withdraw(uint256 amount) external {
    // 1. Checks
    require(balances[msg.sender] >= amount, "Insufficient balance");
    require(amount > 0, "Amount must be positive");
    
    // 2. Effects (update state BEFORE external calls)
    balances[msg.sender] -= amount;
    emit Withdrawal(msg.sender, amount);
    
    // 3. Interactions (external calls LAST)
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

## Flash Loan Attack Patterns

### Flash Loan Price Manipulation

**Severity:** Critical

**Description:** Flash loan attack to manipulate price oracles.

**Detection Heuristics:**
- Flash loan
- Price oracle
- Spot price
- Reserve manipulation
- Liquidity check

**Mitigation:**
```solidity
// Protect against flash loan price manipulation
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract Secure {
    AggregatorV3Interface internal priceFeed;
    uint256 constant MAX_PRICE_DEVIATION = 5; // 5% max deviation
    uint256 constant TWAP_PERIOD = 1800; // 30 minutes
    
    function getSecurePrice() public view returns (uint256) {
        // Use Chainlink oracle with staleness check
        (
            uint80 roundId,
            int256 price,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();
        
        require(price > 0, "Invalid price");
        require(answeredInRound >= roundId, "Stale price");
        require(block.timestamp - updatedAt < 3600, "Price too old");
        
        // Additional: Check price deviation
        uint256 twapPrice = getTWAP(TWAP_PERIOD);
        uint256 deviation = abs(uint256(price), twapPrice) * 100 / twapPrice;
        require(deviation <= MAX_PRICE_DEVIATION, "Price deviation too high");
        
        return uint256(price);
    }
}
```

### Same-Block Borrow and Repay

**Severity:** High

**Description:** Detection and prevention of same-block borrow/repay attacks.

**Mitigation:**
```solidity
// Detect and prevent same-block borrow/repay attacks
contract Secure {
    mapping(address => uint256) public lastBorrowBlock;
    mapping(address => uint256) public lastActionBlock;
    
    function borrow(uint256 amount) external {
        require(
            block.number > lastActionBlock[msg.sender],
            "Same block action prevented"
        );
        
        lastBorrowBlock[msg.sender] = block.number;
        lastActionBlock[msg.sender] = block.number;
        
        // Borrow logic...
    }
    
    function sensitiveAction() external {
        require(
            block.number > lastBorrowBlock[msg.sender],
            "Cannot act in same block as borrow"
        );
        
        lastActionBlock[msg.sender] = block.number;
        // Sensitive action logic...
    }
}
```

## Access Control Patterns

### Role-Based Access Control

**Severity:** High

**Description:** Multi-level role-based access control needed instead of simple Ownable.

**Detection Heuristics:**
- `onlyOwner`
- `owner`
- `admin`
- Restricted function

**Mitigation:**
```solidity
// Use OpenZeppelin's AccessControl for role-based permissions
import "@openzeppelin/contracts/access/AccessControl.sol";

contract Secure is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }
    
    function criticalOperation() external onlyRole(ADMIN_ROLE) {
        // Only admins can execute
    }
    
    function operatorAction() external onlyRole(OPERATOR_ROLE) {
        // Only operators can execute
    }
    
    function pause() external onlyRole(PAUSER_ROLE) {
        // Only pausers can execute
    }
}
```

## Front-Running Protection

### Commit-Reveal Scheme

**Severity:** Medium

**Description:** Commit-reveal scheme needed to prevent front-running.

**Detection Heuristics:**
- Bid
- Auction
- Vote
- Random
- Lottery

**Mitigation:**
```solidity
// Implement commit-reveal scheme
contract Secure {
    mapping(address => bytes32) public commitments;
    mapping(address => uint256) public revealDeadline;
    
    function commit(bytes32 commitment) external {
        require(commitments[msg.sender] == 0, "Already committed");
        commitments[msg.sender] = commitment;
        revealDeadline[msg.sender] = block.timestamp + 1 hours;
    }
    
    function reveal(uint256 value, bytes32 salt) external {
        require(commitments[msg.sender] != 0, "No commitment");
        require(block.timestamp <= revealDeadline[msg.sender], "Reveal deadline passed");
        
        bytes32 hash = keccak256(abi.encodePacked(msg.sender, value, salt));
        require(hash == commitments[msg.sender], "Invalid reveal");
        
        delete commitments[msg.sender];
        // Process revealed value...
    }
}
```

### EIP-712 Typed Signatures

**Severity:** Medium

**Description:** EIP-712 typed data signatures for protection against signature replay.

**Mitigation:**
```solidity
// Use EIP-712 for signed messages
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";

contract Secure is EIP712 {
    bytes32 public constant PERMIT_TYPEHASH = 
        keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    
    mapping(address => uint256) public nonces;
    
    constructor() EIP712("SecureToken", "1") {}
    
    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(block.timestamp <= deadline, "Signature expired");
        
        bytes32 structHash = keccak256(
            abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonces[owner]++, deadline)
        );
        
        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = ECDSA.recover(hash, v, r, s);
        require(signer == owner, "Invalid signature");
        
        // Process permit...
    }
}
```

## Oracle Security

### Chainlink Staleness Checks

**Severity:** High

**Description:** Chainlink price feed staleness checks required.

**Mitigation:**
```solidity
// Implement Chainlink staleness checks
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract Secure {
    AggregatorV3Interface internal priceFeed;
    uint256 public constant STALENESS_THRESHOLD = 3600; // 1 hour
    
    function getLatestPrice() public view returns (uint256) {
        (
            uint80 roundId,
            int256 price,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeed.latestRoundData();
        
        // Check for stale data
        require(answeredInRound >= roundId, "Stale price: round not complete");
        require(block.timestamp - updatedAt <= STALENESS_THRESHOLD, "Stale price: too old");
        require(price > 0, "Invalid price: must be positive");
        
        return uint256(price);
    }
}
```

### Multi-Oracle Consensus

**Severity:** Medium

**Description:** Multi-oracle consensus for critical price data.

**Mitigation:**
```solidity
// Implement multi-oracle consensus
contract Secure {
    AggregatorV3Interface[] public priceFeeds;
    uint256 public constant MAX_PRICE_DEVIATION = 3; // 3%
    
    function getConsensusPrice() public view returns (uint256) {
        require(priceFeeds.length >= 3, "Need at least 3 oracles");
        
        uint256[] memory prices = new uint256[](priceFeeds.length);
        
        // Collect prices from all oracles
        for (uint256 i = 0; i < priceFeeds.length; i++) {
            (, int256 price, , uint256 updatedAt, ) = priceFeeds[i].latestRoundData();
            require(price > 0, "Invalid price");
            require(block.timestamp - updatedAt < 3600, "Stale price");
            prices[i] = uint256(price);
        }
        
        // Calculate median price
        uint256 medianPrice = _median(prices);
        
        // Verify all prices are within acceptable deviation
        for (uint256 i = 0; i < prices.length; i++) {
            uint256 deviation = abs(prices[i], medianPrice) * 100 / medianPrice;
            require(deviation <= MAX_PRICE_DEVIATION, "Price deviation too high");
        }
        
        return medianPrice;
    }
}
```

### TWAP Implementation

**Severity:** Medium

**Description:** Time-Weighted Average Price (TWAP) implementation for manipulation resistance.

**Mitigation:**
```solidity
// Implement TWAP oracle
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@uniswap/v3-periphery/contracts/libraries/OracleLibrary.sol";

contract Secure {
    IUniswapV3Pool public pool;
    uint32 public constant TWAP_PERIOD = 1800; // 30 minutes
    
    function getTWAP() public view returns (uint256) {
        uint32[] memory secondsAgos = new uint32[](2);
        secondsAgos[0] = TWAP_PERIOD;
        secondsAgos[1] = 0;
        
        (int56[] memory tickCumulatives, ) = pool.observe(secondsAgos);
        
        int56 tickCumulativesDelta = tickCumulatives[1] - tickCumulatives[0];
        int24 arithmeticMeanTick = int24(tickCumulativesDelta / int56(uint56(TWAP_PERIOD)));
        
        uint256 quoteAmount = OracleLibrary.getQuoteAtTick(
            arithmeticMeanTick,
            uint128(1e18),
            address(token0),
            address(token1)
        );
        
        return quoteAmount;
    }
}
```

## Formal Verification Hints

### NatSpec Invariants

Use NatSpec annotations to document contract invariants for formal verification:

```solidity
/// @notice Transfer tokens from one account to another
/// @invariant totalSupply == sum(balanceOf(user) for all users)
/// @invariant balanceOf(user) >= 0 for all users
/// @dev Ensure all invariants hold before and after execution
function transfer(address to, uint256 amount) external returns (bool) {
    // Implementation
}
```

### Foundry Invariant Testing

Generate Foundry invariant tests for critical contracts:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/MyToken.sol";

contract MyTokenInvariantTest is Test {
    MyToken public target;
    
    function setUp() public {
        target = new MyToken();
    }
    
    /// @dev Foundry will call this after every function call
    function invariant_criticalInvariants() public {
        assertTrue(target.totalSupply() > 0, "Invariant failed: totalSupply > 0");
        assertTrue(target.balanceOf(user) >= 0, "Invariant failed: balanceOf >= 0");
    }
}
```

### Common Invariants by Contract Type

#### ERC20 Tokens
- `totalSupply == sum(balanceOf(user) for all users)`
- `balanceOf(user) <= totalSupply for all users`
- `balanceOf(user) >= 0 for all users`

#### Vaults
- `totalAssets >= sum(userDeposits)`
- `sharePrice never decreases (except for losses)`
- `totalShares * sharePrice == totalAssets`

#### Lending Protocols
- `totalBorrowed <= totalDeposited`
- `userCollateral >= userBorrowedValue * collateralRatio`
- `sum(userDeposits) >= sum(userBorrows)`

#### Staking Contracts
- `totalStaked == sum(userStakes)`
- `rewardsDistributed <= rewardsAllocated`
- `userRewards >= 0`

## Implementation Priority

### 🔴 High Priority
- Reentrancy guards (classic, cross-function, read-only)
- Flash loan price manipulation checks
- Oracle staleness checks
- CEI pattern enforcement

### 🟡 Medium Priority
- Oracle security (TWAP, multi-oracle consensus)
- Role-based access control
- Front-running protection (commit-reveal, EIP-712)

### 🟢 Low Priority
- Formal verification hints
- NatSpec annotations for invariants
- Foundry invariant testing templates

## Implementation Templates

### SecureVaultTemplate.sol

**Location:** `docs/testing-examples/SecureVaultTemplate.sol`

**Features:**
- ✅ Reentrancy guards for state-changing functions
- ✅ Read-only reentrancy protection for view functions
- ✅ Checks-Effects-Interactions (CEI) pattern enforcement
- ✅ Role-based access control (ADMIN, OPERATOR, PAUSER)
- ✅ Flash loan detection (same-block action prevention)
- ✅ Slippage protection on withdrawals
- ✅ Emergency pause functionality
- ✅ TWAP oracle integration points

**Usage Example:**
```solidity
import "./SecureVaultTemplate.sol";

// Your contract inherits all security protections
contract MyVault is SecureVault {
    // Add your custom logic here
    // All security patterns are already implemented
}
```

**Key Patterns:**
- **Reentrancy Protection**: Both `nonReentrant` and `nonReentrantView` modifiers
- **Access Control**: Three-tier role system (ADMIN_ROLE, OPERATOR_ROLE, PAUSER_ROLE)
- **Flash Loan Detection**: `noFlashLoan` modifier prevents same-block actions
- **CEI Pattern**: All functions follow Checks → Effects → Interactions

### OracleSecurityTemplate.sol

**Location:** `docs/testing-examples/OracleSecurityTemplate.sol`

**Features:**
- ✅ Chainlink price feed integration with staleness checks
- ✅ TWAP (Time-Weighted Average Price) using Uniswap V3
- ✅ Multi-oracle consensus mechanism
- ✅ Price deviation detection and rejection
- ✅ Circuit breakers for extreme price movements
- ✅ Flash loan price manipulation resistance

**Usage Example:**
```solidity
import "./OracleSecurityTemplate.sol";

// Deploy oracle system
ChainlinkOracle chainlink = new ChainlinkOracle(CHAINLINK_FEED_ADDRESS);
TWAPOracle twap = new TWAPOracle(UNISWAP_V3_POOL);
MultiOracleConsensus consensus = new MultiOracleConsensus(
    address(chainlink),
    address(twap)
);

// Get secure price
uint256 price = consensus.getConsensusPrice();
```

**Key Patterns:**
- **Staleness Checks**: Validates Chainlink data is recent (< 1 hour)
- **TWAP Protection**: 30-minute time-weighted average prevents flash loan manipulation
- **Multi-Oracle Consensus**: Cross-validates Chainlink and TWAP (max 3% deviation)
- **Circuit Breakers**: Automatic shutdown on extreme price movements

### MEVProtectionTemplate.sol

**Location:** `docs/testing-examples/MEVProtectionTemplate.sol`

**Features:**
- ✅ Comprehensive slippage protection
- ✅ Transaction deadline enforcement
- ✅ Commit-reveal scheme for front-running resistance
- ✅ Sandwich attack detection and prevention
- ✅ Price impact validation
- ✅ MEV-aware transaction ordering

**Usage Example:**
```solidity
import "./MEVProtectionTemplate.sol";

// Deploy MEV-protected DEX
MEVProtectedDEX dex = new MEVProtectedDEX();

// Swap with full MEV protection
uint256 amountOut = dex.swapWithProtection(
    amountIn,
    minAmountOut,  // Slippage protection
    deadline       // Deadline protection
);

// Or use commit-reveal for sensitive trades
bytes32 commitHash = keccak256(abi.encodePacked(
    address(this),
    abi.encode(amountIn, minOut, deadline),
    salt
));
dex.commitSwap(commitHash);
// Wait minimum blocks...
dex.revealSwap(amountIn, minOut, deadline, salt);
```

**Key Patterns:**
- **Slippage Protection**: User-defined minimum output amounts (max 5%)
- **Deadline Enforcement**: Prevents stale transaction execution
- **Commit-Reveal**: Two-phase execution prevents front-running
- **Sandwich Detection**: Monitors per-block price impact (max 3%)

### DeFiSecurityTests.t.sol

**Location:** `docs/testing-examples/DeFiSecurityTests.t.sol`

**Test Coverage:**
- ✅ Reentrancy attack attempts (should fail)
- ✅ Read-only reentrancy protection
- ✅ CEI pattern validation
- ✅ Role-based access control enforcement
- ✅ Flash loan detection
- ✅ Slippage protection validation
- ✅ Deadline enforcement
- ✅ Commit-reveal workflow
- ✅ Sandwich attack detection
- ✅ Invariant testing with handlers

**Running Tests:**
```bash
# Quick test (32 runs)
FOUNDRY_PROFILE=quick forge test --match-path docs/testing-examples/DeFiSecurityTests.t.sol

# Standard test (256 runs)
forge test --match-path docs/testing-examples/DeFiSecurityTests.t.sol

# CI test (10,000 runs)
FOUNDRY_PROFILE=ci forge test --match-path docs/testing-examples/DeFiSecurityTests.t.sol
```

## Bug Bounty Impact

These patterns enable:
- Detection of critical vulnerabilities (read-only reentrancy, flash loan attacks)
- Improved exploit success rate
- Better understanding of attack vectors
- Coverage of latest 2023-2024 vulnerabilities

## References

1. [Consensys Smart Contract Best Practices](https://consensys.github.io/smart-contract-best-practices/)
2. [Trail of Bits Building Secure Contracts](https://github.com/crytic/building-secure-contracts)
3. [DeFi Security Summit 2024 Findings](https://defisecuritysummit.org/)
4. [Secureum Security Pitfalls](https://secureum.substack.com/)
5. [Curve Finance Reentrancy Attack Analysis](https://chainsecurity.com/curve-lp-oracle-manipulation-post-mortem/)
6. [Chainlink Price Feed Documentation](https://docs.chain.link/data-feeds/historical-data)
7. [Uniswap V3 TWAP Oracle](https://docs.uniswap.org/contracts/v3/guides/advanced/price-oracle)
8. [EIP-712: Typed Structured Data](https://eips.ethereum.org/EIPS/eip-712)
