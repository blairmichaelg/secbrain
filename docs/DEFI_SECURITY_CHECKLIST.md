# 🛡️ DeFi Security Deployment Checklist

**Use this checklist before deploying any DeFi smart contract to mainnet**

Last Updated: January 2024  
Based on: 1,384 Solidity files analyzed, 180 exploit attempts studied

---

## ⚠️ Pre-Deployment Verification

### 🔴 CRITICAL (Must Pass All)

#### Reentrancy Protection

- [ ] **All state-changing functions** have `nonReentrant` modifier
- [ ] **Critical view functions** (price calculations, share values) have `nonReentrantView` modifier
- [ ] **Checks-Effects-Interactions pattern** followed in all functions
  - [ ] Input validation first (Checks)
  - [ ] State updates second (Effects)
  - [ ] External calls last (Interactions)
- [ ] **Reentrancy attack tests** pass (minimum 100% coverage)
- [ ] **Read-only reentrancy tests** pass

**Test Command:**
```bash
forge test --match-test testReentrancy
```

**Example Test:**
```solidity
function testReentrancyProtection() public {
    ReentrancyAttacker attacker = new ReentrancyAttacker(address(vault));
    vm.expectRevert(ReentrantCall.selector);
    attacker.attack();
}
```

#### Oracle Security

- [ ] **NEVER using spot prices** for critical operations
- [ ] **TWAP oracle implemented** (minimum 30-minute period)
- [ ] **Chainlink price feed** configured with validation:
  - [ ] Staleness check (< 1 hour)
  - [ ] Round completion check
  - [ ] Positive price check
  - [ ] Deviation limits (< 10%)
- [ ] **Multi-oracle consensus** if TVL > $10M
  - [ ] At least 2 independent price sources
  - [ ] Deviation threshold ≤ 5%
  - [ ] Circuit breaker on disagreement
- [ ] **Oracle manipulation tests** pass
- [ ] **Flash loan price manipulation tests** pass

**Test Command:**
```bash
forge test --match-test testOracle
```

#### Access Control

- [ ] **Role-based access control** implemented
- [ ] **ADMIN_ROLE** assigned to multi-signature wallet (not EOA)
  - [ ] Minimum 3/5 multi-sig
  - [ ] All signers documented
- [ ] **PAUSER_ROLE** assigned to trusted addresses
- [ ] **OPERATOR_ROLE** (if used) has limited permissions
- [ ] **All admin functions** restricted with `onlyRole` modifier
- [ ] **Role grant/revoke** emits events
- [ ] **Access control tests** pass (unauthorized access blocked)

**Test Command:**
```bash
forge test --match-test testAccessControl
```

#### Flash Loan Protection

- [ ] **Same-block action detection** on deposit/withdraw functions
- [ ] **Flash loan tests** pass
- [ ] **Price manipulation** during flash loans prevented

**Test Command:**
```bash
forge test --match-test testFlashLoan
```

---

### 🟡 HIGH PRIORITY (Strongly Recommended)

#### MEV Protection

- [ ] **Slippage protection** on all swaps/trades
  - [ ] User can specify `minAmountOut`
  - [ ] Maximum slippage capped (≤ 5%)
- [ ] **Deadline enforcement** on time-sensitive operations
  - [ ] `deadline` parameter required
  - [ ] Validation: `block.timestamp <= deadline`
- [ ] **Price impact limits** to prevent sandwich attacks
  - [ ] Single transaction impact ≤ 1%
  - [ ] Block cumulative impact ≤ 3%
- [ ] **MEV protection tests** pass

**Test Command:**
```bash
forge test --match-test testMEV
forge test --match-test testSlippage
```

#### Emergency Controls

- [ ] **Pause functionality** implemented
- [ ] **Pause tests** verify:
  - [ ] Only PAUSER_ROLE can pause
  - [ ] Critical functions blocked when paused
  - [ ] Unpause requires same role
- [ ] **Emergency procedures** documented
- [ ] **Recovery mechanisms** tested

#### Events & Transparency

- [ ] **All state changes** emit events
- [ ] **Events include** relevant parameters
- [ ] **Indexed parameters** for filtering
- [ ] **Events tested** in test suite

---

### 🟢 RECOMMENDED (Best Practices)

#### Code Quality

- [ ] **NatSpec comments** on all public/external functions
- [ ] **Security assumptions** documented
- [ ] **Known limitations** documented
- [ ] **Upgrade procedures** documented (if upgradeable)
- [ ] **No TODO comments** in production code
- [ ] **No hardcoded addresses** (use constructor/initialization)

#### Testing Coverage

- [ ] **Unit tests** for all functions
- [ ] **Integration tests** for user flows
- [ ] **Fuzz testing** (≥ 256 runs)
  ```bash
  forge test --fuzz-runs 256
  ```
- [ ] **Invariant testing** with handlers
- [ ] **Code coverage** ≥ 95%
  ```bash
  forge coverage
  ```
- [ ] **Gas optimization** tests (if relevant)

#### Static Analysis

- [ ] **Slither** analysis passed
  ```bash
  slither . --filter-paths "test|mock"
  ```
- [ ] **Mythril** symbolic execution (no critical issues)
  ```bash
  myth analyze src/MyContract.sol
  ```
- [ ] **Solhint** linting passed
  ```bash
  solhint 'src/**/*.sol'
  ```
- [ ] **Aderyn** static analysis (if available)

---

## 🔍 Security Pattern Verification

### Pattern 1: Reentrancy Guard

**Verification Steps:**

1. Find all functions making external calls
   ```bash
   grep -r "\.call\|\.transfer\|\.send" src/
   ```

2. Verify each has `nonReentrant` modifier

3. Find all view functions reading critical state
   ```bash
   grep -r "function.*view.*returns" src/
   ```

4. Verify price/share calculations have `nonReentrantView`

**Pass Criteria:** ✅ All external-call functions protected, all critical views protected

### Pattern 2: Oracle Protection

**Verification Steps:**

1. Find all price read operations
   ```bash
   grep -r "getPrice\|price()\|latestRoundData" src/
   ```

2. Verify using TWAP (not spot price)

3. Check Chainlink validation:
   ```solidity
   require(answeredInRound >= roundId, "Stale");
   require(block.timestamp - updatedAt < 3600, "Stale");
   require(answer > 0, "Invalid");
   ```

4. If TVL > $10M, verify multi-oracle consensus

**Pass Criteria:** ✅ No spot prices, TWAP enabled, Chainlink validated, consensus if needed

### Pattern 3: Access Control

**Verification Steps:**

1. Find all admin functions
   ```bash
   grep -r "onlyOwner\|onlyAdmin\|onlyRole" src/
   ```

2. Verify multi-sig for critical roles

3. Test unauthorized access blocked
   ```solidity
   vm.prank(attacker);
   vm.expectRevert(Unauthorized.selector);
   vault.pause();
   ```

**Pass Criteria:** ✅ All admin functions restricted, multi-sig configured, tests pass

### Pattern 4: CEI Pattern

**Verification Steps:**

1. Review all state-changing functions

2. Verify order:
   ```solidity
   function withdraw(uint256 amount) external {
       // 1. CHECKS
       require(amount > 0);
       require(balances[msg.sender] >= amount);
       
       // 2. EFFECTS
       balances[msg.sender] -= amount;
       totalDeposits -= amount;
       emit Withdrawal(msg.sender, amount);
       
       // 3. INTERACTIONS
       (bool success, ) = msg.sender.call{value: amount}("");
       require(success);
   }
   ```

**Pass Criteria:** ✅ All functions follow CEI pattern

---

## 📊 Risk Assessment Matrix

Use this to determine which protections are critical for your protocol:

| Protocol Type | Reentrancy | Oracle | MEV | Flash Loan | Access Control |
|--------------|-----------|--------|-----|-----------|----------------|
| Vault/Staking | 🔴 Critical | 🟡 High | 🟢 Medium | 🔴 Critical | 🔴 Critical |
| Lending Protocol | 🔴 Critical | 🔴 Critical | 🟡 High | 🔴 Critical | 🔴 Critical |
| DEX/AMM | 🔴 Critical | 🔴 Critical | 🔴 Critical | 🔴 Critical | 🟡 High |
| Derivatives | 🔴 Critical | 🔴 Critical | 🔴 Critical | 🔴 Critical | 🔴 Critical |
| Bridge | 🔴 Critical | 🔴 Critical | 🟡 High | 🟡 High | 🔴 Critical |

**Legend:**
- 🔴 Critical: Must implement, deployment blocked without
- 🟡 High: Strongly recommended, document if not implemented
- 🟢 Medium: Recommended, case-by-case basis

---

## 🧪 Required Test Coverage

### Minimum Test Requirements

```bash
# Must pass all of these
forge test --match-test testReentrancy
forge test --match-test testAccessControl
forge test --match-test testFlashLoan
forge test --match-test testOracle
forge test --match-test testMEV
forge test --match-test testSlippage
```

### Fuzz Testing Requirements

```bash
# Minimum 256 runs
forge test --fuzz-runs 256

# CI: 10,000 runs
FOUNDRY_PROFILE=ci forge test
```

### Coverage Requirements

```bash
# Generate coverage report
forge coverage

# Must achieve:
# - Overall coverage: ≥ 95%
# - Function coverage: 100%
# - Branch coverage: ≥ 90%
```

---

## 🚀 Deployment Procedure

### Pre-Deployment

- [ ] All checklist items above completed
- [ ] Professional audit completed (for mainnet with funds)
- [ ] Audit findings addressed or documented
- [ ] Testnet deployment successful
- [ ] Multi-sig wallets configured
- [ ] Oracle feeds tested on target network

### Deployment Steps

1. **Deploy to testnet first**
   ```bash
   forge script script/Deploy.s.sol --rpc-url $TESTNET_RPC --broadcast
   ```

2. **Verify all protections work**
   - Test deposits/withdrawals
   - Test emergency pause
   - Test oracle price feeds
   - Test access control

3. **Run final security checks**
   ```bash
   slither . --filter-paths "test"
   forge test --fuzz-runs 10000
   ```

4. **Deploy to mainnet**
   ```bash
   forge script script/Deploy.s.sol --rpc-url $MAINNET_RPC --broadcast --verify
   ```

5. **Verify contract on Etherscan**
   ```bash
   forge verify-contract $CONTRACT_ADDRESS MyContract --chain-id 1
   ```

6. **Configure roles**
   ```solidity
   // Grant roles to multi-sig
   grantRole(ADMIN_ROLE, MULTISIG_ADDRESS);
   grantRole(PAUSER_ROLE, EMERGENCY_MULTISIG);
   
   // Revoke deployer roles
   revokeRole(ADMIN_ROLE, DEPLOYER_ADDRESS);
   ```

7. **Initialize oracles**
   - Configure Chainlink feeds
   - Set TWAP pools
   - Test price queries

8. **Final verification**
   ```bash
   # Verify contract state
   cast call $CONTRACT_ADDRESS "paused()(bool)"
   cast call $CONTRACT_ADDRESS "hasRole(bytes32,address)(bool)" $ADMIN_ROLE $MULTISIG
   ```

### Post-Deployment

- [ ] Monitor for unusual activity (first 24 hours critical)
- [ ] Verify oracle prices updating
- [ ] Test user deposits/withdrawals
- [ ] Document all contract addresses
- [ ] Share audit report (if public protocol)
- [ ] Set up monitoring/alerts
- [ ] Prepare incident response plan

---

## 🚨 Red Flags (DO NOT DEPLOY IF ANY ARE TRUE)

- ❌ Using spot prices for critical operations
- ❌ No reentrancy protection on external calls
- ❌ View functions reading state without protection
- ❌ Admin functions controlled by single EOA
- ❌ No test coverage for security patterns
- ❌ Failing any security tests
- ❌ Critical findings from audit unresolved
- ❌ No emergency pause functionality
- ❌ No multi-sig for admin operations
- ❌ No slippage protection on swaps

**If any red flag is present: STOP and fix before deployment**

---

## 📝 Deployment Checklist Summary

**Print this and check off before mainnet deployment:**

### Critical Security ✅
- [ ] Reentrancy protection (state-changing + view functions)
- [ ] Oracle security (TWAP + Chainlink, no spot prices)
- [ ] Access control (multi-sig for admin)
- [ ] Flash loan detection (same-block prevention)
- [ ] All security tests pass

### High Priority ✅
- [ ] MEV protection (slippage + deadline)
- [ ] Emergency pause functionality
- [ ] Events on all state changes
- [ ] Fuzz testing (≥ 256 runs)
- [ ] Code coverage ≥ 95%

### Deployment ✅
- [ ] Professional audit completed (if public/mainnet with funds)
- [ ] Testnet deployment successful
- [ ] Multi-sig configured correctly
- [ ] Oracle feeds tested
- [ ] Contract verified on Etherscan
- [ ] Monitoring set up

### Documentation ✅
- [ ] NatSpec on all functions
- [ ] Security assumptions documented
- [ ] Known limitations documented
- [ ] Emergency procedures documented

---

## 📞 Emergency Response

If a vulnerability is discovered:

1. **Pause the contract immediately**
   ```solidity
   // Call from PAUSER_ROLE
   contract.pause();
   ```

2. **Notify users** (Twitter, Discord, etc.)

3. **Assess the vulnerability**
   - How critical?
   - Funds at risk?
   - Already exploited?

4. **Coordinate response**
   - Security researchers
   - Auditors
   - Multi-sig signers

5. **Deploy fix** (if possible)
   - Upgrade contract (if upgradeable)
   - Deploy new contract
   - Migrate users

6. **Post-mortem**
   - Document what happened
   - How it was fixed
   - Lessons learned

---

## ✅ Final Sign-Off

**Before deploying to mainnet, the following must sign off:**

- [ ] **Lead Developer:** All code reviewed, tests pass
- [ ] **Security Lead:** All security patterns implemented
- [ ] **Auditor:** Audit complete, critical findings resolved
- [ ] **Protocol Lead:** Deployment approved

**Deployment Date:** ________________

**Contract Address:** ________________

**Deployed By:** ________________

**Multi-Sig Address:** ________________

**Audit Report:** ________________

---

## 🔗 Resources

- **Templates:** `/docs/testing-examples/`
- **Quick Start:** [DEFI_SECURITY_QUICKSTART.md](./DEFI_SECURITY_QUICKSTART.md)
- **Full Guide:** [DEFI_EXPLOIT_PROTECTION_GUIDE.md](./DEFI_EXPLOIT_PROTECTION_GUIDE.md)
- **Tests:** `/docs/testing-examples/DeFiSecurityTests.t.sol`

---

**⚠️ REMEMBER:** This checklist is a guide. Each protocol has unique risks. Always get professional security audits for production deployments.

**💰 Cost of proper security: $10k-$100k**  
**Cost of getting hacked: $MILLIONS + reputation damage**

**Choose wisely. Deploy safely. 🛡️**
