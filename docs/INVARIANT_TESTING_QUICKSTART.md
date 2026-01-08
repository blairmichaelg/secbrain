# Quick Start: Foundry Invariant Testing

This guide helps you get started with invariant testing for your smart contracts.

## Prerequisites

- **Foundry** - Smart contract testing framework
  - **Recommended**: Install from official source: https://book.getfoundry.sh/getting-started/installation
  ```bash
  curl -L https://foundry.paradigm.xyz | bash
  foundryup
  ```
- Basic understanding of Solidity
- Smart contracts to test

## Step 1: Run the Working Example

First, verify the setup works by running the included ERC20 example:

```bash
cd targets/originprotocol/instascope

# Quick test (32 runs)
forge test --match-path "test/invariants/ERC20.invariants.t.sol" -vv

# More thorough test (256 runs)
forge test --match-path "test/invariants/ERC20.invariants.t.sol"

# CI-level test (1,000 runs)
FOUNDRY_PROFILE=ci forge test --match-path "test/invariants/ERC20.invariants.t.sol"
```

**Expected output:**
```
Running 8 tests for test/invariants/ERC20.invariants.t.sol:ERC20InvariantTests
[PASS] invariant_balanceCannotExceedTotalSupply() (runs: 256, calls: 3840, reverts: 1234)
[PASS] invariant_balancesNonNegative() (runs: 256, calls: 3840, reverts: 1234)
[PASS] invariant_callSummary() (runs: 256, calls: 3840, reverts: 1234)
[PASS] invariant_totalSupplyDoesNotOverflow() (runs: 256, calls: 3840, reverts: 1234)
[PASS] invariant_totalSupplyEqualsBalances() (runs: 256, calls: 3840, reverts: 1234)
[PASS] invariant_totalSupplyEqualsGhostTracking() (runs: 256, calls: 3840, reverts: 1234)
[PASS] invariant_zeroAddressHasNoBalance() (runs: 256, calls: 3840, reverts: 1234)
Test result: ok. 7 passed; 0 failed;
```

## Step 2: Activate a Template Test

Let's activate the SingleAssetStaking template as an example:

### 2.1 Deploy Your Contract

Open `test/invariants/SingleAssetStaking.invariants.t.sol` and update the `setUp()` function:

```solidity
function setUp() public {
    // Deploy mock token
    token = new MockERC20();
    
    // Deploy your actual staking contract
    // Replace this with your actual contract deployment:
    staking = new SingleAssetStaking();
    
    // Configure staking parameters
    uint256[] memory durations = new uint256[](3);
    durations[0] = 30 days;
    durations[1] = 90 days;
    durations[2] = 365 days;
    
    uint256[] memory rates = new uint256[](3);
    rates[0] = 0.05e18; // 5%
    rates[1] = 0.10e18; // 10%
    rates[2] = 0.30e18; // 30%
    
    // Initialize staking contract
    staking.initialize(address(token), durations, rates);
    
    // Setup handler
    handler = new StakingHandler(staking, token);
    
    // Fund staking contract with rewards
    token.mint(address(staking), 10_000_000e18);
    
    // Target handler for invariant testing
    targetContract(address(handler));
    
    // Configure selectors
    bytes4[] memory selectors = new bytes4[](2);
    selectors[0] = StakingHandler.stake.selector;
    selectors[1] = StakingHandler.exit.selector;
    
    targetSelector(FuzzSelector({
        addr: address(handler),
        selectors: selectors
    }));
}
```

### 2.2 Uncomment Invariant Tests

Find each invariant function and uncomment the test code. For example:

```solidity
function invariant_sufficientLiquidity() public view {
    // Remove the /* and */ around this code:
    uint256 contractBalance = token.balanceOf(address(staking));
    uint256 totalOutstanding = staking.totalOutstanding();
    
    assertGe(
        contractBalance,
        totalOutstanding,
        "Contract balance must cover total outstanding obligations"
    );
}
```

### 2.3 Update Handler Configuration

In the `StakingHandler` constructor, ensure the valid durations match your contract:

```solidity
constructor(ISingleAssetStaking _staking, IERC20 _token) {
    staking = _staking;
    token = _token;
    
    // Set these to match your contract's allowed durations
    validDurations.push(30 days);
    validDurations.push(60 days);
    validDurations.push(90 days);
    validDurations.push(180 days);
    validDurations.push(365 days);
}
```

### 2.4 Run Your Tests

```bash
forge test --match-path "test/invariants/SingleAssetStaking.invariants.t.sol" -vv
```

## Step 3: Create a Custom Invariant Test

Here's a template for creating your own invariant test:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "forge-std/Test.sol";

/// @notice Your contract interface
interface IYourContract {
    function someFunction() external;
    function someState() external view returns (uint256);
}

/// @notice Handler for invariant testing
contract YourHandler is Test {
    IYourContract public target;
    
    uint256 public ghost_totalOperations;
    address[] public actors;
    mapping(address => bool) public isActor;
    
    constructor(IYourContract _target) {
        target = _target;
    }
    
    function doSomething(uint256 actorSeed, uint256 param) external {
        address actor = _getRandomActor(actorSeed);
        param = bound(param, 1, 1000);
        
        vm.prank(actor);
        try target.someFunction() {
            ghost_totalOperations++;
        } catch {
            // Expected failure, continue
        }
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        address actor = address(uint160(bound(seed, 1, 20)));
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        return actor;
    }
}

/// @notice Invariant tests
contract YourContractInvariantTests is Test {
    IYourContract public target;
    YourHandler public handler;
    
    function setUp() public {
        // Deploy your contract
        target = IYourContract(address(new YourContract()));
        
        // Setup handler
        handler = new YourHandler(target);
        
        // Configure fuzzer
        targetContract(address(handler));
    }
    
    /// @notice Your invariant - describe what should always be true
    function invariant_yourProperty() public view {
        // Add your assertion here
        assertTrue(
            target.someState() > 0,
            "State should always be positive"
        );
    }
}
```

## Step 4: Common Patterns

### Testing Token Balances

```solidity
function invariant_totalSupplyEqualsBalances() public view {
    uint256 sum = 0;
    for (uint256 i = 0; i < handler.actors().length; i++) {
        sum += token.balanceOf(handler.actors()[i]);
    }
    assertEq(token.totalSupply(), sum);
}
```

### Testing Accounting

```solidity
function invariant_assetsBackLiabilities() public view {
    uint256 assets = vault.totalAssets();
    uint256 liabilities = vault.totalLiabilities();
    assertGe(assets, liabilities, "Assets must back liabilities");
}
```

### Testing Access Control

```solidity
function invariant_onlyOwnerCanPause() public view {
    // This tests that the paused state can only be changed by owner
    // The handler would need to track authorized vs unauthorized calls
    assertTrue(true, "Handler enforces access control");
}
```

### Testing Conservation Laws

```solidity
function invariant_noValueCreated() public view {
    uint256 totalIn = handler.ghost_deposited();
    uint256 totalOut = handler.ghost_withdrawn();
    uint256 balance = vault.balance();
    
    assertEq(totalIn - totalOut, balance, "Value conservation");
}
```

## Step 5: Debugging Failures

When an invariant fails:

### 1. Enable Verbose Output

```bash
forge test --match-path "test/invariants/*.t.sol" -vvvv
```

### 2. Look at Call Sequence

Foundry will show the exact sequence that broke the invariant:

```
[FAIL. Reason: Invariant violation]
    Sequence:
        mint(actorSeed: 123, amount: 1000)
        burn(actorSeed: 456, amount: 500)
        transfer(from: 123, to: 789, amount: 600)
```

### 3. Reproduce in Unit Test

```solidity
function test_reproduceFailure() public {
    handler.mint(123, 1000);
    handler.burn(456, 500);
    handler.transfer(123, 789, 600);
    
    // Now debug why this breaks the invariant
}
```

### 4. Check Ghost Variables

Add this to your tests:

```solidity
function invariant_callSummary() public view {
    handler.callSummary();
}
```

## Step 6: Integration with CI

The tests automatically run via GitHub Actions. To customize:

Edit `.github/workflows/foundry-fuzzing.yml`:

```yaml
- name: Run invariant tests
  env:
    FOUNDRY_PROFILE: ci
  run: |
    forge test --match-path "test/invariants/*.t.sol" -vvv
```

## Best Practices

1. **Start simple** - Begin with basic invariants, add complexity gradually
2. **Bound inputs** - Always use `bound()` to keep values realistic
3. **Use ghost variables** - Track cumulative state for verification
4. **Handle failures** - Use try-catch for expected failures
5. **Test profiles** - Use `quick` for dev, `ci` for merges, `intense` for releases
6. **Document invariants** - Explain WHY each property should hold
7. **Limit actors** - Use 10-50 addresses, not unlimited
8. **Add summaries** - Include `invariant_callSummary()` for debugging

## Troubleshooting

### "No targets provided"
Make sure you call `targetContract()` in `setUp()`.

### "Too many test rejections"
Your bounds are too restrictive. Adjust `bound()` ranges or increase `fuzz_max_test_rejects`.

### Tests are slow
Use the `quick` profile during development:
```bash
FOUNDRY_PROFILE=quick forge test --match-path "test/invariants/*.t.sol"
```

### Invariant keeps failing
1. Check if the invariant is correct (maybe it's supposed to fail!)
2. Look at the call sequence
3. Add logging to handler functions
4. Reproduce in a unit test

## Resources

- **Full Documentation**: `/docs/INVARIANT_TESTING.md`
- **Local README**: `/targets/originprotocol/instascope/test/invariants/README.md`
- **Foundry Book**: https://book.getfoundry.sh/forge/invariant-testing
- **Working Example**: `test/invariants/ERC20.invariants.t.sol`

## Getting Help

1. Check the working ERC20 example
2. Review the documentation
3. Look at Foundry documentation
4. Open an issue with the `testing` label

---

Happy fuzzing! 🎲
