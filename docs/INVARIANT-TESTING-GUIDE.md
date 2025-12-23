# Invariant Testing Guide for SecBrain Smart Contracts

## Overview

This guide explains the invariant testing approach implemented for SecBrain's smart contract security analysis. Invariant testing is a powerful property-based testing technique that helps discover edge cases and state inconsistencies in smart contracts.

## What is Invariant Testing?

Invariant testing uses fuzzing to repeatedly call contract functions in random sequences while checking that critical properties (invariants) always hold true. Unlike traditional unit tests that test specific scenarios, invariant tests explore the entire state space to find violations.

### Key Benefits

- **Discovers Edge Cases**: Finds unexpected state transitions and vulnerabilities
- **Comprehensive Coverage**: Tests random combinations of operations
- **State Consistency**: Ensures contracts maintain critical properties
- **Automated**: Runs thousands of test scenarios automatically

## Implemented Invariant Tests

### 1. SingleAssetStaking Invariant Tests

**File**: `targets/originprotocol/instascope/test/secbrain/SingleAssetStakingInvariant.t.sol`

**Critical Invariants**:
- `invariant_sufficientBalance()`: Contract balance must always be >= totalOutstanding
- `invariant_totalOutstandingNonNegative()`: totalOutstanding should never be negative
- `invariant_notPausedByDefault()`: Staking should not be paused during normal operations

**Handler Operations**:
- `stake()`: Stakes tokens with random amounts and durations
- `exit()`: Exits stakes after time has passed

**Ghost Variables**:
- `ghost_totalStaked`: Tracks total amount staked
- `ghost_totalRewards`: Tracks total rewards accrued
- `ghost_totalPaid`: Tracks total rewards paid out

### 2. WOETH (Wrapped OETH) Invariant Tests

**File**: `targets/originprotocol/instascope/test/secbrain/WOETHInvariant.t.sol`

**Critical Invariants**:
- `invariant_totalSupplyConsistency()`: Total supply should equal total assets (ERC4626 property)
- `invariant_balancesSumToTotalSupply()`: Sum of all balances equals total supply
- `invariant_sufficientBackingAssets()`: Contract must have enough OETH to back all WOETH
- `invariant_conversionConsistency()`: Share/asset conversion functions should be inverse operations

**Handler Operations**:
- `deposit()`: Deposits OETH to mint WOETH shares
- `withdraw()`: Withdraws OETH by burning WOETH shares
- `redeem()`: Redeems WOETH shares for OETH

**Ghost Variables**:
- `ghost_totalDeposited`: Tracks total deposits
- `ghost_totalWithdrawn`: Tracks total withdrawals

### 3. LidoARM (Automated Redemption Manager) Invariant Tests

**File**: `targets/originprotocol/instascope/test/secbrain/LidoARMInvariant.t.sol`

**Critical Invariants**:
- `invariant_sufficientLiquidity()`: ARM should maintain sufficient liquidity in WETH or stETH
- `invariant_sharesToAssetsConsistency()`: Share/asset ratio should be consistent
- `invariant_balancesSumToTotalSupply()`: Sum of all balances equals total supply

**Handler Operations**:
- `deposit()`: Deposits WETH to get ARM shares
- `swapExactTokensForTokens()`: Swaps between WETH and stETH

**Ghost Variables**:
- `ghost_totalDeposits`: Tracks total deposits
- `ghost_totalSwaps`: Tracks total swap volume

## Running Invariant Tests

### Quick Testing (32 runs)
```bash
cd targets/originprotocol/instascope
FOUNDRY_PROFILE=quick forge test --match-contract Invariant -vvv
```

### Standard Testing (256 runs)
```bash
cd targets/originprotocol/instascope
forge test --match-contract Invariant -vvv
```

### CI Profile (10,000 runs)
```bash
cd targets/originprotocol/instascope
FOUNDRY_PROFILE=ci forge test --match-contract Invariant -vvv
```

### Intense Testing (50,000 runs)
```bash
cd targets/originprotocol/instascope
FOUNDRY_PROFILE=intense forge test --match-contract Invariant -vvv
```

## Configuration

The invariant testing configuration is defined in `foundry.toml`:

```toml
[invariant]
runs = 256              # Number of invariant test runs
depth = 15              # Maximum call depth for invariants
fail_on_revert = false  # Continue testing even if a call reverts
call_override = false   # Don't override calls during invariant testing
dictionary_weight = 80  # Higher weight for dictionary in invariant tests
shrink_run_limit = 5000 # Limit for shrinking failing tests

[profile.ci]
fuzz_runs = 10000       # High fuzz runs for standard property tests
invariant_runs = 1000   # Increased invariant runs for CI
invariant_depth = 20    # Deeper call sequences for CI
```

## Handler Pattern

Invariant tests use the **Handler Pattern** to restrict fuzzer inputs to valid operations:

```solidity
contract MyHandler is Test {
    MyContract public target;
    
    // Ghost variables to track expected state
    uint256 public ghost_totalX;
    uint256 public ghost_totalY;
    
    // Restrict fuzzer inputs to valid ranges
    function doSomething(uint256 amount) external {
        amount = bound(amount, 1, 1000);  // Bound to valid range
        
        // Track state changes
        ghost_totalX += amount;
        
        // Call target contract
        target.doSomething(amount);
    }
}

contract InvariantTest is Test {
    function setUp() public {
        // Deploy and configure handler
        handler = new MyHandler(target);
        
        // Target handler for fuzzing
        targetContract(address(handler));
    }
    
    function invariant_someProperty() public {
        // Check invariant holds
        assertGe(target.x(), handler.ghost_totalX());
    }
}
```

## Ghost Variables

Ghost variables are used to track expected state independently of the contract:

- **Purpose**: Provide an oracle for checking contract state
- **Usage**: Track totals, counts, or derived values
- **Benefits**: Detect accounting errors and state inconsistencies

## Best Practices

### 1. Define Clear Invariants
- Identify properties that should **always** be true
- Focus on critical business logic and security properties
- Example: "Total supply equals sum of balances"

### 2. Use Bounded Inputs
- Restrict fuzzer inputs to valid ranges using `bound()`
- Prevent unrealistic scenarios that would always revert
- Example: `amount = bound(amount, 1e18, 1000e18)`

### 3. Track State with Ghost Variables
- Maintain independent accounting of expected state
- Use for complex derived properties
- Compare ghost state with actual contract state

### 4. Handle Reverts Gracefully
- Use `try/catch` to handle expected reverts
- Don't count failed operations in ghost variables
- Set `fail_on_revert = false` for exploration

### 5. Use Multiple Actors
- Test with multiple users to find interaction bugs
- Use bounded seeds to generate consistent actor addresses
- Track actors in an array for balance summation

### 6. Add Debug Output
- Include `invariant_callSummary()` for debugging
- Log ghost variables and call counts
- Use `-vvv` flag for detailed output

## Common Invariants to Test

### Token Contracts
- `balanceOf` sum equals `totalSupply`
- Individual balances never exceed `totalSupply`
- Transfers preserve total supply
- Allowances are respected

### Staking Contracts
- Contract balance >= total outstanding obligations
- Stake records match actual balances
- Rewards calculation is consistent
- Time-locked stakes cannot be withdrawn early

### Vault/Strategy Contracts
- Share price never decreases unexpectedly
- Total assets backs total shares
- Deposits/withdrawals preserve accounting
- Fee collection doesn't break invariants

### AMM/DEX Contracts
- Constant product formula (x * y = k) holds
- Liquidity pool balances stay positive
- Price impact is bounded
- No arbitrage opportunities exceed slippage

## Troubleshooting

### Tests Fail Immediately
- Check if contracts are properly deployed in `setUp()`
- Verify handler has necessary approvals/permissions
- Review bounded input ranges

### Tests Pass But Find Nothing
- Increase `runs` and `depth` in foundry.toml
- Review handler operations - are they too restrictive?
- Add more diverse operations to handler

### Assertion Failures in Invariants
- **Good!** You found a bug or edge case
- Use `-vvvv` to see the call sequence that triggered it
- Check ghost variable tracking for correctness
- Verify the invariant itself is correct

### Performance Issues
- Start with `quick` profile (32 runs) for development
- Use `default` (256 runs) for regular testing
- Reserve `ci` (1,000 invariant runs) and `intense` (5,000 runs) for CI/CD and audits

## Integration with CI/CD

Invariant tests run automatically in CI via `.github/workflows/foundry-fuzzing.yml`:

```yaml
- name: Run CI profile invariant tests
  env:
    FOUNDRY_PROFILE: ci
  run: |
    forge test --match-contract Invariant -vvv
```

The workflow runs multiple fuzzing profiles:
1. **Quick** (32 runs): Fast feedback
2. **Standard** (256 runs): Default testing
3. **CI** (1,000 invariant runs, 10,000 fuzz runs): Comprehensive pre-merge testing

## Expected Impact

Implementing invariant testing provides:

1. **Early Bug Detection**: Find edge cases before deployment
2. **State Consistency**: Ensure contracts maintain critical properties
3. **Security Assurance**: Discover potential exploit vectors
4. **Regression Prevention**: Catch breaking changes in CI
5. **Documentation**: Invariants serve as executable specifications

## Further Reading

- [Foundry Invariant Testing Documentation](https://book.getfoundry.sh/forge/invariant-testing)
- [Trail of Bits: Property-Based Testing](https://blog.trailofbits.com/2023/07/21/fuzzing-on-chain-contracts-with-echidna/)
- [Smart Contract Fuzzing Best Practices](https://github.com/crytic/building-secure-contracts/tree/master/program-analysis/echidna)

## Contributing

To add invariant tests for new contracts:

1. Identify critical properties that must always hold
2. Create a handler contract with bounded operations
3. Implement ghost variable tracking if needed
4. Define invariant test functions (prefix with `invariant_`)
5. Test locally with quick profile, then standard profile
6. Submit PR - CI will run comprehensive testing

---

*For questions or improvements to this guide, please open an issue or PR.*
