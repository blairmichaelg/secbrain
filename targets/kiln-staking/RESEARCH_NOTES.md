# Research Notes and Tips

This file contains advanced research techniques, common patterns, and lessons learned from hunting vulnerabilities in the Kiln staking contracts.

## Table of Contents
1. [Research Methodology](#research-methodology)
2. [Common Vulnerability Patterns](#common-vulnerability-patterns)
3. [Code Analysis Techniques](#code-analysis-techniques)
4. [Testing Strategies](#testing-strategies)
5. [Lessons Learned](#lessons-learned)

---

## Research Methodology

### Step-by-Step Approach

1. **Understand the Business Logic** (30 min)
   - What is the protocol trying to do?
   - Who are the stakeholders (users, operators, admins)?
   - What are the key security properties?
   - Where is value stored and transferred?

2. **Map the Attack Surface** (30 min)
   - Entry points: external/public functions
   - State changes: storage variables
   - Value flows: ETH/token transfers
   - Trust boundaries: access control

3. **Identify Trust Assumptions** (15 min)
   - What does the protocol assume about users?
   - What does it assume about operators?
   - What does it assume about external contracts?
   - What does it assume about timing/ordering?

4. **Test Boundary Conditions** (45 min)
   - Zero values
   - Maximum values
   - Minimum values
   - Edge cases (empty arrays, null addresses, etc.)

### Key Questions to Ask

**About Fees:**
- Who receives fees?
- How are fees calculated?
- What happens if fee transfer fails?
- Can fee recipient be changed?
- Is there a maximum fee cap?

**About Withdrawals:**
- Who can initiate withdrawals?
- Are there time locks or delays?
- What happens on partial withdrawals?
- Can withdrawals be paused?
- What's the withdrawal order (FIFO/LIFO)?

**About Shares/Accounting:**
- How are shares calculated?
- What's the share-to-asset ratio?
- Can ratio be manipulated?
- Are there minimum deposit/withdrawal amounts?
- How are rewards distributed?

**About Access Control:**
- Who has admin privileges?
- Can admins steal/freeze funds?
- Is there a timelock on admin actions?
- Can admin be changed?
- Are there emergency pause mechanisms?

**About Initialization:**
- Is the contract upgradeable?
- Is it using a proxy pattern?
- Can initialize() be called multiple times?
- Is the implementation protected?
- Was initialization atomic with deployment?

---

## Common Vulnerability Patterns

### 1. Fee Transfer DoS

**Pattern:**
```solidity
function withdraw() external {
    uint256 amount = userBalance[msg.sender];
    uint256 fee = calculateFee(amount);
    
    // VULNERABLE: If this fails, withdrawal fails
    feeRecipient.transfer(fee);
    
    payable(msg.sender).transfer(amount - fee);
}
```

**Why it's vulnerable:**
- `transfer()` only forwards 2300 gas
- Fee recipient might be a contract requiring more gas
- Fee recipient might intentionally revert
- No fallback if fee transfer fails

**Fix:**
```solidity
function withdraw() external {
    uint256 amount = userBalance[msg.sender];
    uint256 fee = calculateFee(amount);
    
    // Send user funds first
    payable(msg.sender).transfer(amount - fee);
    
    // Track fees separately (pull pattern)
    pendingFees[feeRecipient] += fee;
}

function claimFees() external {
    uint256 fees = pendingFees[msg.sender];
    pendingFees[msg.sender] = 0;
    payable(msg.sender).transfer(fees);
}
```

### 2. Share Inflation Attack

**Pattern:**
```solidity
function deposit() external payable {
    uint256 shares = msg.value * totalShares / totalAssets;
    balanceOf[msg.sender] += shares;
    totalShares += shares;
}
```

**Why it's vulnerable:**
- First depositor can inflate share value
- Subsequent deposits might round to 0
- Attacker: deposit 1 wei, get 1 share, donate 1000 ETH
- Next user: deposits 999 ETH, gets 0 shares (rounds down)

**Attack scenario:**
1. Attacker deposits 1 wei → gets 1 share
2. Attacker donates 1000 ETH directly to contract
3. Now: 1 share = 1000 ETH
4. Victim deposits 999 ETH
5. Victim gets: 999 ETH * 1 share / 1000 ETH = 0 shares
6. Victim's funds are stuck

**Fix:**
```solidity
uint256 constant MIN_DEPOSIT = 1e9; // 1 gwei minimum

function deposit() external payable {
    require(msg.value >= MIN_DEPOSIT, "Too small");
    
    uint256 shares;
    if (totalShares == 0) {
        shares = msg.value;
        // Mint dead shares to prevent inflation
        _mint(address(0), 1e9);
    } else {
        shares = msg.value * totalShares / totalAssets;
        require(shares > 0, "Zero shares");
    }
    
    balanceOf[msg.sender] += shares;
    totalShares += shares;
}
```

### 3. Re-initialization Vulnerability

**Pattern:**
```solidity
// VULNERABLE: No initializer modifier
function initialize(address _owner) external {
    owner = _owner;
}
```

**Why it's vulnerable:**
- Anyone can call initialize() again
- Attacker can reset owner to themselves
- Can change critical parameters

**Fix:**
```solidity
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract MyContract is Initializable {
    address public owner;
    
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }
    
    function initialize(address _owner) external initializer {
        owner = _owner;
    }
}
```

### 4. Reentrancy (Classic but still relevant)

**Pattern:**
```solidity
function withdraw() external {
    uint256 amount = balances[msg.sender];
    // VULNERABLE: External call before state update
    payable(msg.sender).call{value: amount}("");
    balances[msg.sender] = 0;
}
```

**Fix:**
```solidity
function withdraw() external nonReentrant {
    uint256 amount = balances[msg.sender];
    balances[msg.sender] = 0; // Update state first
    payable(msg.sender).call{value: amount}("");
}
```

---

## Code Analysis Techniques

### Static Analysis

**Using Slither:**
```bash
# Install
pip3 install slither-analyzer

# Run on target
slither . --exclude-dependencies

# Focus on specific issues
slither . --detect reentrancy-eth,unchecked-transfer
```

**Using Semgrep:**
```bash
# Run Solidity security rules
semgrep --config=p/smart-contracts .
```

**Manual Code Review Checklist:**
- [ ] External calls → Check for reentrancy
- [ ] Arithmetic operations → Check for overflow/underflow
- [ ] Division operations → Check for division by zero
- [ ] Access control → Verify modifiers on sensitive functions
- [ ] State changes → Ensure proper ordering
- [ ] Event emissions → Verify important state changes are logged

### Dynamic Analysis

**Using Foundry Fuzzing:**
```solidity
function testFuzz_Withdrawal(uint256 amount) public {
    // Bound to reasonable range
    amount = bound(amount, 1, 1000 ether);
    
    // Test withdrawal with random amount
    vm.assume(amount <= userBalance);
    contract.withdraw(amount);
    
    // Verify invariants
    assertLe(contract.totalAssets(), initialAssets);
}
```

**Invariant Testing:**
```solidity
contract InvariantTest is Test {
    function invariant_totalSharesMatchesBalances() public {
        uint256 sumOfBalances;
        for (uint i = 0; i < users.length; i++) {
            sumOfBalances += contract.balanceOf(users[i]);
        }
        assertEq(contract.totalShares(), sumOfBalances);
    }
}
```

### Symbolic Execution

**Using Mythril:**
```bash
# Install
pip3 install mythril

# Analyze contract
myth analyze contracts/Target.sol
```

---

## Testing Strategies

### 1. Fork Testing Best Practices

```solidity
function setUp() public {
    // Use specific block for deterministic testing
    vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 18500000);
    
    // Get target contract
    target = TargetContract(0xdc71...);
    
    // Snapshot state for reset between tests
    snapshotId = vm.snapshot();
}

function testScenario() public {
    // Test logic
    
    // Revert to snapshot
    vm.revertTo(snapshotId);
}
```

### 2. Gas Analysis

```bash
# Generate gas report
forge test --gas-report

# Focus on specific functions
forge test --gas-report --match-contract TargetContract
```

### 3. Coverage Analysis

```bash
# Generate coverage report
forge coverage

# View detailed coverage
forge coverage --report lcov
genhtml lcov.info -o coverage
```

### 4. Differential Testing

```solidity
// Compare two implementations
function testDifferential() public {
    uint256 result1 = oldImplementation.calculate(input);
    uint256 result2 = newImplementation.calculate(input);
    assertEq(result1, result2, "Implementations diverge");
}
```

---

## Lessons Learned

### What Makes a Good PoC

1. **Minimal**: Only necessary code, no fluff
2. **Self-contained**: All dependencies included
3. **Documented**: Comments explain each step
4. **Reproducible**: Others can run it easily
5. **Clear impact**: Shows exact damage/exploit

### What Makes a Good Report

1. **Clear title**: Severity + brief description
2. **Executive summary**: Impact in 2-3 sentences
3. **Technical details**: Step-by-step explanation
4. **Working PoC**: Attached and documented
5. **Fix suggestion**: Practical recommendation
6. **Scope justification**: Why it's in-scope and not known issue

### Common Mistakes to Avoid

1. ❌ Testing on local deployment instead of mainnet fork
2. ❌ Assuming functions exist without verifying
3. ❌ Not checking if vulnerability was already found in audits
4. ❌ Setting severity too high (inflation = instant rejection)
5. ❌ Submitting operator-related bugs (usually known issues)
6. ❌ Incomplete PoC (missing setup or dependencies)
7. ❌ Vague impact description ("bad things happen")
8. ❌ Not explaining why it's different from known issues

### Signs of a Valid Finding

✅ Not mentioned in audits  
✅ Affects user principal funds  
✅ No admin intervention can fix it  
✅ Doesn't require malicious operator  
✅ Reproducible on mainnet fork  
✅ Clear and quantifiable impact  
✅ Realistic attack cost vs. reward

### Signs to Move On

🚫 Already in audit report  
🚫 Requires malicious operator  
🚫 In the "Known Issues" list  
🚫 Cannot reproduce on fork  
🚫 Requires unrealistic conditions  
🚫 Impact is negligible  
🚫 Theoretical but not exploitable

---

## Advanced Research Techniques

### 1. Transaction Analysis

```bash
# Find recent transactions to target contract
cast logs --from-block 18000000 --to-block latest --address 0xdc71...

# Decode specific transaction
cast tx <tx-hash> --rpc-url $MAINNET_RPC_URL

# Trace transaction execution
cast run <tx-hash> --rpc-url $MAINNET_RPC_URL --trace
```

### 2. Storage Analysis

```bash
# Read all storage slots
for i in {0..100}; do
    slot=$(printf "0x%x" $i)
    cast storage 0xdc71... $slot --rpc-url $MAINNET_RPC_URL
done

# Find specific variable
# Example: owner is usually at slot 0
cast storage 0xdc71... 0 --rpc-url $MAINNET_RPC_URL
```

### 3. Event Analysis

```bash
# Get events from contract
cast logs --address 0xdc71... --from-block 18000000

# Filter specific event
cast logs --address 0xdc71... "Withdrawal(address,uint256)"
```

### 4. Bytecode Analysis

```bash
# Get contract bytecode
cast code 0xdc71... --rpc-url $MAINNET_RPC_URL

# Disassemble
cast disassemble <bytecode>
```

---

## Useful Resources

### Documentation
- [Foundry Book](https://book.getfoundry.sh/)
- [OpenZeppelin Docs](https://docs.openzeppelin.com/)
- [Ethereum Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf)
- [Solidity Docs](https://docs.soliditylang.org/)

### Security Resources
- [Smart Contract Weakness Classification](https://swcregistry.io/)
- [DeFi Threat Matrix](https://github.com/manifoldfinance/defi-threat)
- [Consensys Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [Rekt News](https://rekt.news/) - Learn from past exploits

### Tools
- [Slither](https://github.com/crytic/slither)
- [Mythril](https://github.com/ConsenSys/mythril)
- [Manticore](https://github.com/trailofbits/manticore)
- [Echidna](https://github.com/crytic/echidna)
- [Foundry](https://github.com/foundry-rs/foundry)

---

*This document is a living guide. Update it as you learn new techniques and patterns.*
