# Invariant Testing Implementation

## Overview

This document describes the invariant testing infrastructure implemented for SecBrain smart contracts.

## What is Invariant Testing?

Invariant testing (also called property-based testing) is a powerful technique where:

1. The fuzzer generates random sequences of function calls
2. After each sequence, certain properties (invariants) are checked
3. If an invariant fails, the fuzzer provides the exact sequence that caused the failure

This is more thorough than traditional unit tests because it explores state transitions you might not think to test manually.

## Implementation Structure

### Location

All invariant tests are located in:
- **Origin Protocol**: `/targets/originprotocol/instascope/test/invariants/`
- **Template files**: For SingleAssetStaking, VaultCore, and LidoARM
- **Working example**: ERC20.invariants.t.sol (ready to run)

### Test Organization

Each invariant test file contains three main components:

1. **Interfaces/Mocks** - Contracts needed for testing
2. **Handler Contract** - Restricts fuzzer inputs to valid operations
3. **Invariant Tests** - Properties that must always hold

## Available Tests

### 1. SingleAssetStaking Invariant Tests
**File**: `SingleAssetStaking.invariants.t.sol`

Tests the staking contract's critical properties:
- Contract liquidity always covers obligations
- Total outstanding matches sum of expected payouts
- Stakes cannot be claimed before maturity

**Status**: Template (requires contract deployment to activate)

### 2. VaultCore Invariant Tests
**File**: `VaultCore.invariants.t.sol`

Tests the vault's accounting and rebasing:
- Vault value backs all OUSD supply
- Balance sum equals total supply
- Asset conservation across strategies

**Status**: Template (requires contract deployment to activate)

### 3. LidoARM Invariant Tests
**File**: `LidoARM.invariants.t.sol`

Tests the Lido ARM's liquidity management:
- Total assets accounting
- Share-to-asset backing
- Withdrawal queue bounds
- Price stability

**Status**: Template (requires contract deployment to activate)

### 4. ERC20 Invariant Tests (Working Example)
**File**: `ERC20.invariants.t.sol`

Fully implemented and ready to run:
- Total supply equals sum of balances
- Balances never exceed supply
- Mint/burn tracking with ghost variables

**Status**: ✅ Active and runnable

## Running Invariant Tests

### Quick Test (Development)
```bash
cd targets/originprotocol/instascope
FOUNDRY_PROFILE=quick forge test --match-path "test/invariants/*.t.sol"
```

### CI Profile (1,000 runs)
```bash
cd targets/originprotocol/instascope
FOUNDRY_PROFILE=ci forge test --match-path "test/invariants/*.t.sol"
```

### Intense Profile (5,000 runs)
```bash
cd targets/originprotocol/instascope
FOUNDRY_PROFILE=intense forge test --match-path "test/invariants/*.t.sol"
```

### Run Specific Test
```bash
cd targets/originprotocol/instascope
forge test --match-path "test/invariants/ERC20.invariants.t.sol" -vv
```

## GitHub Actions Integration

The invariant tests automatically run via the `foundry-fuzzing.yml` workflow:

```yaml
- name: Run CI profile invariant tests
  env:
    FOUNDRY_PROFILE: ci
  run: |
    forge test --match-contract Invariant -vvv
```

**Triggers:**
- Push to main/develop branches (if .sol files change)
- Pull requests to main/develop
- Manual workflow dispatch

## Foundry Configuration

The `foundry.toml` includes specialized invariant testing configurations:

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

**Parameters:**
- `invariant_runs`: Number of random call sequences to test
- `invariant_depth`: Maximum number of calls in each sequence
- `fail_on_revert`: Whether to fail test if any call reverts
- `dictionary_weight`: How much to favor dictionary values

## Activating Template Tests

To activate the template tests (SingleAssetStaking, VaultCore, LidoARM):

### Step 1: Deploy Contracts in setUp()

```solidity
function setUp() public {
    // Deploy your actual contract
    token = new MockERC20();
    staking = new SingleAssetStaking();
    
    // Initialize with proper parameters
    staking.initialize(address(token), durations, rates);
    
    // Setup handler
    handler = new StakingHandler(staking, token);
    
    // Configure invariant testing
    targetContract(address(handler));
}
```

### Step 2: Uncomment Test Code

Each invariant test has commented-out assertions. Remove the `/*` and `*/` to activate:

```solidity
function invariant_sufficientLiquidity() public view {
    // Uncomment below:
    uint256 contractBalance = token.balanceOf(address(staking));
    uint256 totalOutstanding = staking.totalOutstanding();
    
    assertGe(
        contractBalance,
        totalOutstanding,
        "Contract must cover obligations"
    );
}
```

### Step 3: Adjust Handler Configuration

Update handler constructor with correct addresses and parameters:

```solidity
constructor(ISingleAssetStaking _staking, IERC20 _token) {
    staking = _staking;
    token = _token;
    
    // Set valid durations based on your contract
    validDurations.push(30 days);
    validDurations.push(90 days);
    validDurations.push(365 days);
}
```

## Best Practices

### 1. Start with Simple Invariants
Begin with basic properties and add complexity gradually:
```solidity
// Simple: Total supply is valid
assertTrue(token.totalSupply() >= 0);

// Complex: Sum of balances equals supply
assertEq(token.totalSupply(), sumOfAllBalances());
```

### 2. Use Ghost Variables
Track cumulative actions for verification:
```solidity
uint256 public ghost_totalMinted;
uint256 public ghost_totalBurned;

function invariant_ghostTracking() public view {
    assertEq(
        token.totalSupply(),
        ghost_totalMinted - ghost_totalBurned
    );
}
```

### 3. Bound Fuzzer Inputs
Always use `bound()` to keep inputs realistic:
```solidity
function stake(uint256 amount) external {
    amount = bound(amount, 1e18, 1000e18);
    // ... staking logic
}
```

### 4. Handle Expected Failures
Use try-catch for operations that can fail:
```solidity
try staking.stake(amount, duration) {
    ghost_successfulStakes++;
} catch {
    // Expected failure, continue fuzzing
}
```

### 5. Add Call Summaries
Include a summary function for debugging:
```solidity
function invariant_callSummary() public view {
    handler.callSummary();
}
```

## Common Invariants by Contract Type

### Token Contracts
- ✅ Total supply = sum of balances
- ✅ No balance exceeds total supply  
- ✅ Transfers preserve total supply
- ✅ Mint increases supply by amount
- ✅ Burn decreases supply by amount

### Staking Contracts
- ✅ Contract balance ≥ total obligations
- ✅ Sum of stakes = total outstanding
- ✅ Stakes locked until maturity
- ✅ Rewards calculated correctly

### Vault Contracts
- ✅ Total value ≥ share supply
- ✅ Asset conservation
- ✅ Balance accounting consistency
- ✅ Rebase only increases balances

### AMM/DEX Contracts
- ✅ No arbitrage opportunities
- ✅ K value preserved (for constant product)
- ✅ Price within bounds
- ✅ Liquidity adequacy

## Debugging Failed Invariants

When an invariant fails:

### 1. View the Call Sequence
```bash
forge test --match-path "test/invariants/*.t.sol" -vvvv
```

This shows the exact sequence of calls that broke the invariant.

### 2. Check Call Summary
The `invariant_callSummary()` function shows what the fuzzer did:
```
=== Handler Summary ===
Total minted: 15000000000000000000
Total burned: 3000000000000000000
Total supply: 12000000000000000000
```

### 3. Reproduce Manually
Copy the failing sequence into a regular test:
```solidity
function test_reproduceFailure() public {
    // Copy exact sequence from fuzzer output
    handler.mint(123, 1000e18);
    handler.burn(456, 500e18);
    // ... etc
}
```

## Performance Considerations

### Test Duration vs. Coverage

| Profile | Runs | Depth | Time | Use Case |
|---------|------|-------|------|----------|
| quick | 32 | 5 | ~30s | Development |
| default | 256 | 15 | ~2min | Standard testing |
| ci | 1,000 | 20 | ~5min | CI/CD |
| intense | 5,000 | 50 | ~20min | Security audits |

### Optimization Tips

1. **Limit actor pool** - Use 10-50 addresses instead of unlimited
2. **Bound inputs early** - Reduce rejection rate
3. **Use simpler checks** - Complex invariants slow down fuzzing
4. **Skip expensive operations** - Cache values when possible

## Integration with Other Tools

### Echidna
For contracts requiring property testing with Echidna:
```bash
echidna . --contract YourContract --config echidna.yaml
```

### Slither
Invariant tests complement static analysis:
```bash
slither . --exclude-low --exclude-informational
```

### Myth
Symbolic execution for deeper analysis:
```bash
myth analyze contracts/YourContract.sol
```

## Resources

- **Foundry Book**: https://book.getfoundry.sh/forge/invariant-testing
- **Trail of Bits Guide**: https://blog.trailofbits.com/fuzzing-on-chain-contracts
- **Nascent Best Practices**: https://www.nascent.xyz/idea/youre-writing-down-the-invariants-wrong
- **Local README**: `/targets/originprotocol/instascope/test/invariants/README.md`

## Contributing

When adding new invariant tests:

1. ✅ Follow the three-part structure (interface, handler, tests)
2. ✅ Document all invariants with clear comments
3. ✅ Include ghost variables for state tracking
4. ✅ Test with multiple profiles (quick → ci → intense)
5. ✅ Update this documentation
6. ✅ Add examples to the README

## Future Improvements

- [ ] Activate template tests with actual contract deployments
- [ ] Add more contract-specific invariants
- [ ] Integrate with continuous fuzzing service
- [ ] Add mutation testing for invariants
- [ ] Create invariant test generator

## Questions?

For questions about invariant testing:
1. Check `/targets/originprotocol/instascope/test/invariants/README.md`
2. Review the working ERC20 example
3. Consult Foundry documentation
4. Open an issue with the `testing` label

---

**Status**: ✅ Infrastructure complete, templates ready for activation

**Last Updated**: 2026-01-08
