# Invariant Testing for Origin Protocol Contracts

This directory contains invariant tests for key Origin Protocol smart contracts analyzed by SecBrain.

## Overview

Invariant testing is a property-based testing technique that uses fuzzing to verify that critical properties always hold true, regardless of the sequence of operations performed on the contract.

## Test Files

### SingleAssetStakingInvariant.t.sol
Tests the SingleAssetStaking contract for:
- Sufficient balance to cover all stakes and rewards
- Correct accounting of totalOutstanding
- Proper pause state management

### WOETHInvariant.t.sol
Tests the WOETH (Wrapped OETH) ERC4626 token for:
- Total supply consistency with total assets
- Sum of balances equals total supply
- Sufficient backing assets
- Conversion function consistency

### LidoARMInvariant.t.sol
Tests the Lido Automated Redemption Manager for:
- Sufficient liquidity maintenance
- Share to asset consistency
- Balance accounting

## Running Tests

From the `targets/originprotocol/instascope` directory:

### Quick Test (Development)
```bash
FOUNDRY_PROFILE=quick forge test --match-contract Invariant -vvv
```

### Standard Test
```bash
forge test --match-contract Invariant -vvv
```

### CI Profile (Comprehensive)
```bash
FOUNDRY_PROFILE=ci forge test --match-contract Invariant -vvv
```

### Specific Test
```bash
forge test --match-contract SingleAssetStakingInvariantTest -vvv
```

## Test Statistics

- **Test Files**: 3
- **Contracts Tested**: 3 core contracts
- **Total Invariants**: 11
- **Handler Functions**: 8
- **Ghost Variables**: 9

## Fuzzing Configuration

Tests use the configuration from `../../foundry.toml`:

| Profile | Invariant Runs | Depth | Purpose |
|---------|---------------|-------|---------|
| quick | 32 | 5 | Fast development feedback |
| default | 256 | 15 | Standard testing |
| ci | 1000 | 20 | CI/CD comprehensive testing |
| intense | 5000 | 50 | Security audits |

## Test Pattern

All tests follow the Handler Pattern:

1. **Handler Contract**: Restricts fuzzer inputs to valid operations
2. **Ghost Variables**: Track expected state independently
3. **Invariant Functions**: Assert properties that must always hold
4. **Bounded Inputs**: Use `bound()` to restrict fuzzer inputs to valid ranges

Example:
```solidity
contract MyHandler is Test {
    MyContract public target;
    uint256 public ghost_totalX;
    
    function doOperation(uint256 amount) external {
        amount = bound(amount, 1, 1000);
        ghost_totalX += amount;
        target.doOperation(amount);
    }
}

contract InvariantTest is Test {
    function invariant_totalConsistency() public {
        assertEq(target.total(), handler.ghost_totalX());
    }
}
```

## Key Invariants Tested

### Universal Invariants
- Balance accounting (sum of balances = total supply)
- Non-negative values
- Sufficient reserves to meet obligations

### Token-Specific Invariants
- ERC4626 share/asset conversion consistency
- Rebasing token compatibility
- Liquidity pool balance ratios

### Staking-Specific Invariants
- Contract has sufficient funds to pay rewards
- Stake timing and duration constraints
- Reward calculation consistency

## Continuous Integration

These tests run automatically in CI via `.github/workflows/foundry-fuzzing.yml`:
- On every push to main/develop branches
- On all pull requests
- Can be manually triggered with custom profiles

## Adding New Tests

To add invariant tests for a new contract:

1. Create a new test file following the naming convention: `{ContractName}Invariant.t.sol`
2. Implement a Handler contract with bounded operations
3. Define invariant functions (prefix with `invariant_`)
4. Add ghost variables for state tracking
5. Test locally before submitting PR

See the [Invariant Testing Guide](../../../docs/INVARIANT-TESTING-GUIDE.md) for detailed instructions.

## Coverage Goals

Current coverage: 3 out of 25 contracts (~12%)

Priority contracts for future invariant testing:
- VaultCore (critical asset management)
- OETHVaultCore (core vault logic)
- ExponentialStaking (complex staking mechanics)
- Governance (governance mechanisms)
- Migrator (token migration logic)

## Resources

- [Foundry Invariant Testing Docs](https://book.getfoundry.sh/forge/invariant-testing)
- [SecBrain Invariant Testing Guide](../../../docs/INVARIANT-TESTING-GUIDE.md)
- [Testing Strategies Guide](../../../docs/TESTING-STRATEGIES.md)
- [Example Invariant Tests](../../../docs/testing-examples/InvariantTestExample.sol)

## Troubleshooting

### Tests fail to compile
```bash
forge install foundry-rs/forge-std --no-git --no-commit
```

### Tests pass but don't find issues
- Increase `runs` and `depth` in foundry.toml
- Review handler operations - ensure they're diverse enough
- Check bounded ranges aren't too restrictive

### Need more verbose output
```bash
forge test --match-contract Invariant -vvvv
```

## Contributing

Contributions to improve test coverage are welcome! Please:
1. Follow the existing test patterns
2. Add comprehensive invariants for the contract
3. Include ghost variable tracking where appropriate
4. Test with multiple profiles before submitting
5. Update this README with new test details

---

*Part of the SecBrain automated security analysis framework*
