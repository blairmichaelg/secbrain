# Foundry Invariant Testing Guide

This directory contains invariant tests for critical smart contracts in the Origin Protocol ecosystem. Invariant testing (also known as property-based testing) helps discover edge cases and ensure contracts maintain critical properties under all conditions.

## Overview

Invariant tests continuously call contract functions with random inputs and verify that certain properties (invariants) always hold true. This is more powerful than traditional unit tests because it can find unexpected state transitions and edge cases.

## Test Structure

Each invariant test file follows this pattern:

1. **Mock/Interface Setup** - Defines interfaces and mocks for testing
2. **Handler Contract** - Restricts random inputs to valid operations and tracks ghost variables
3. **Invariant Tests** - Define properties that must always be true

## Available Tests

### SingleAssetStaking Invariant Tests
**File:** `SingleAssetStaking.invariants.t.sol`

**Key Invariants:**
- Contract balance must always cover total outstanding obligations
- Sum of individual stake payouts must equal `totalOutstanding`
- Stakes cannot be claimed before maturity
- Total outstanding should never underflow

**Handler Functions:**
- `stake()` - Stakes tokens for a duration
- `exit()` - Exits matured stakes

### VaultCore Invariant Tests
**File:** `VaultCore.invariants.t.sol`

**Key Invariants:**
- Vault total value must back all OUSD supply
- Sum of user balances equals total supply
- Asset conservation: vault holdings + strategies = total value
- No user can have more OUSD than total supply

**Handler Functions:**
- `mint()` - Mints OUSD by depositing assets
- `redeem()` - Redeems OUSD for assets
- `rebase()` - Triggers vault rebase

### LidoARM Invariant Tests
**File:** `LidoARM.invariants.t.sol`

**Key Invariants:**
- Total assets equals direct holdings + Lido withdrawal queue
- Sum of LP shares equals total supply
- Total assets must back all shares
- Withdrawal queue amount bounded by total assets
- Price stability (WETH/stETH near 1:1)

**Handler Functions:**
- `deposit()` - Deposits WETH for LP shares
- `redeem()` - Redeems LP shares for assets
- `swapWETHForSTETH()` - Swaps WETH for stETH
- `swapSTETHForWETH()` - Swaps stETH for WETH

## Running Invariant Tests

### Basic Usage

```bash
# Run all invariant tests with default profile (256 runs)
forge test --match-path "test/invariants/*.t.sol"

# Run specific invariant test
forge test --match-path "test/invariants/SingleAssetStaking.invariants.t.sol"

# Run with increased verbosity
forge test --match-path "test/invariants/*.t.sol" -vvv
```

### Using Different Profiles

The `foundry.toml` configuration defines several profiles for different testing intensities:

```bash
# Quick testing (32 runs) - for rapid iteration
FOUNDRY_PROFILE=quick forge test --match-path "test/invariants/*.t.sol"

# CI profile (1,000 runs) - for continuous integration
FOUNDRY_PROFILE=ci forge test --match-path "test/invariants/*.t.sol"

# Intense profile (5,000 runs) - for comprehensive testing
FOUNDRY_PROFILE=intense forge test --match-path "test/invariants/*.t.sol"
```

### Profile Configurations

From `foundry.toml`:

```toml
[profile.default]
invariant_runs = 256
invariant_depth = 15

[profile.ci]
invariant_runs = 1000
invariant_depth = 20

[profile.intense]
invariant_runs = 5000
invariant_depth = 50
```

## Implementation Guide

### Activating Tests

The tests are currently templates with commented-out code. To activate them:

1. **Deploy actual contracts** in the `setUp()` function
2. **Uncomment test code** in each invariant function
3. **Configure handler** with correct addresses and parameters

Example for SingleAssetStaking:

```solidity
function setUp() public {
    token = new MockERC20();
    
    // Deploy actual contract
    staking = new SingleAssetStaking();
    
    uint256[] memory durations = new uint256[](3);
    durations[0] = 30 days;
    durations[1] = 90 days;
    durations[2] = 365 days;
    
    uint256[] memory rates = new uint256[](3);
    rates[0] = 0.05e18; // 5%
    rates[1] = 0.10e18; // 10%
    rates[2] = 0.30e18; // 30%
    
    staking.initialize(address(token), durations, rates);
    
    // Setup handler
    handler = new StakingHandler(staking, token);
    
    // Fund staking contract
    token.mint(address(staking), 10_000_000e18);
    
    // Target handler
    targetContract(address(handler));
}
```

### Adding New Invariants

To add a new invariant test:

1. Add a function starting with `invariant_` prefix
2. Add `public view` modifiers
3. Use assertions to verify the invariant

```solidity
function invariant_myNewInvariant() public view {
    // Your invariant logic here
    assertEq(
        contract.someValue(),
        expectedValue,
        "Invariant violation message"
    );
}
```

### Ghost Variables

Handler contracts use "ghost variables" to track cumulative statistics:

```solidity
uint256 public ghost_totalMinted;
uint256 public ghost_totalRedeemed;

function mint(...) external {
    // ... minting logic ...
    ghost_totalMinted += amount;
}
```

These help verify higher-level invariants about the system.

## Debugging Failed Invariants

When an invariant fails, Foundry will:

1. Show which invariant failed
2. Provide the sequence of calls that led to failure
3. Show the final state

### Viewing Call Sequences

```bash
# Run with high verbosity to see call traces
forge test --match-path "test/invariants/*.t.sol" -vvvv
```

### Using Call Summaries

Each handler has a `callSummary()` function that prints statistics:

```solidity
function invariant_callSummary() public view {
    handler.callSummary();
}
```

This runs after every test to show what happened.

## Best Practices

### 1. Start Small
Begin with simple invariants and gradually add complexity.

### 2. Use Bounded Inputs
Always bound fuzzer inputs to reasonable ranges:

```solidity
amount = bound(amount, 1e18, 1000e18);
```

### 3. Handle Failures Gracefully
Use try-catch to handle expected failures:

```solidity
try contract.someFunction() {
    // Success path
} catch {
    // Expected failure, continue
}
```

### 4. Track State Changes
Use ghost variables to track what the fuzzer does:

```solidity
uint256 public ghost_successfulMints;
uint256 public ghost_failedMints;
```

### 5. Limit Actor Pool
Use a limited set of actors for better collision testing:

```solidity
address actor = address(uint160(bound(seed, 1, 20)));
```

## Common Invariants

### Token Contracts
- Total supply equals sum of balances
- No balance exceeds total supply
- Transfers preserve total supply

### Staking Contracts
- Contract balance covers all obligations
- Rewards calculated correctly
- Stakes cannot be claimed early

### Vault Contracts
- Assets back all shares/tokens
- No value is created or destroyed
- Accounting remains consistent

### AMM/DEX Contracts
- No arbitrage opportunities
- K value preserved (for constant product AMMs)
- Price within expected bounds

## Integration with CI

Add to your GitHub Actions workflow:

```yaml
- name: Run Invariant Tests
  run: |
    FOUNDRY_PROFILE=ci forge test --match-path "test/invariants/*.t.sol"
```

## Resources

- [Foundry Book - Invariant Testing](https://book.getfoundry.sh/forge/invariant-testing)
- [Trail of Bits - Property Testing](https://blog.trailofbits.com/2023/07/21/fuzzing-on-chain-contracts-with-foundry/)
- [Nascent - Fuzzing Guide](https://www.nascent.xyz/idea/youre-writing-down-the-invariants-wrong)

## Troubleshooting

### "No invariant targets provided"
Make sure you call `targetContract()` in setUp().

### "Invariant test reverted"
Check that your handler functions handle edge cases and don't revert on invalid inputs.

### "Too many rejections"
Increase `fuzz_max_test_rejects` in foundry.toml or adjust input bounds in handler.

### Tests are slow
Reduce `invariant_runs` for development, use CI profile for final validation.

## Next Steps

1. Deploy actual contracts in test setUp
2. Uncomment invariant test code
3. Run with `quick` profile to iterate
4. Once passing, run with `ci` profile
5. Add to CI/CD pipeline
6. Consider `intense` profile for release candidates

## Contributing

When adding new invariant tests:

1. Follow the existing structure (interfaces, handler, tests)
2. Document all invariants clearly
3. Add ghost variables for tracking
4. Include in this README
5. Test with multiple profiles

---

**Note:** These tests are currently templates. Uncomment and configure them with actual contract deployments to activate them.
