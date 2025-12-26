# Vulnerability Report Template

Use this template when submitting to HackenProof to minimize triage time and maximize acceptance chances.

---

## Title Format

```
[Severity] Brief Description of Impact
```

**Examples:**
- `[Critical] Permanent Freezing of User Funds via Fee Recipient Revert DoS`
- `[High] Temporary Fund Lockup Due to Fee Transfer Failure`
- `[Medium] 1-Wei Donation Causes Division by Zero in Share Accounting`
- `[Medium] Proxy Re-initialization Allows Ownership Takeover`

---

## Report Structure

### 1. Description

**Template:**
```
The [function/mechanism] in [ContractName].sol [describe the vulnerable behavior]. 
If [trigger condition], [describe the negative outcome]. 
This allows [attacker capability] to [impact], violating the [security property] requirement.
```

**Example:**
```
The `withdraw` function in `StakingContract.sol` blindly executes a fee transfer to 
`feeRecipient` without checking the return value or using try/catch. If the fee 
recipient is a contract that reverts (e.g., no receive() function), the entire 
transaction reverts. This allows a broken or malicious fee recipient to permanently 
freeze all user staked funds, violating the "Solvency" requirement.
```

### 2. Impact

**Template:**
```
- **Severity:** [Critical/High/Medium/Low] ([impact type])
- **Direct Loss:** [Describe what users lose or cannot do]
- **Reference:** [Explain why this is NOT a known issue or excluded finding]
```

**Example:**
```
- **Severity:** Critical (Permanent freezing of principal funds)
- **Direct Loss:** Users cannot exit their positions or claim rewards; funds are permanently locked
- **Reference:** This is distinct from "Triggering withdrawal from a Recipient" in the exclusion 
  list because it prevents *principal* recovery, not just a specific withdrawal recipient behavior.
```

### 3. Proof of Concept

**Always include:**
1. Complete, runnable Foundry test file
2. Clear setup instructions
3. Expected vs actual behavior
4. Screenshots/logs of the failing test

**Template:**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/TargetContract.sol";

contract VulnerabilityPoC is Test {
    TargetContract target;
    address user = address(0x1234);
    
    function setUp() public {
        // Fork mainnet at specific block
        vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 18500000);
        
        // Get target contract
        target = TargetContract(0xdc71affc862fceb6ad32be58e098423a7727bebd);
        
        // Setup test conditions
        vm.deal(user, 100 ether);
    }
    
    function testVulnerability() public {
        // Step 1: [Setup initial state]
        
        // Step 2: [Trigger vulnerability]
        
        // Step 3: [Verify negative outcome]
        vm.expectRevert(); // Or assert conditions
        
        // Clean explanation of what failed and why
    }
}
```

**How to run:**
```bash
forge test --fork-url $MAINNET_RPC_URL --match-test testVulnerability -vvvv
```

### 4. Recommended Fix

**Template:**
```
[Specific code-level recommendation]

Alternative approaches:
1. [Option 1]
2. [Option 2]
```

**Example:**
```
Use a "Pull over Push" pattern for fees:

```solidity
// Instead of:
feeRecipient.transfer(feeAmount);  // Can cause DoS

// Use:
pendingFees[feeRecipient] += feeAmount;  // User withdraws separately
```

Alternative approaches:
1. Wrap the fee transfer in a try/catch block to ensure user withdrawals succeed
2. Use a separate claimFees() function that doesn't block withdrawals
```

---

## Severity Guidelines

### Critical
- Direct theft of funds
- Permanent freezing of funds (principal)
- Protocol insolvency

### High
- Temporary freezing of funds
- Theft of unclaimed yield
- Significant manipulation of protocol state

### Medium
- Griefing attacks (1-wei DoS, etc.)
- Re-initialization vulnerabilities
- Minor fund lockups with workarounds

### Low
- Information disclosure
- Gas griefing
- Non-critical state inconsistencies

---

## Pre-Submission Checklist

Before submitting, verify:

- [ ] The vulnerability is NOT in the "Known Issues" list
- [ ] The vulnerability is in-scope per the program rules
- [ ] Your PoC runs successfully on a mainnet fork
- [ ] You've checked previous audits (Halborn/Spearbit PDFs) for duplicates
- [ ] Your report clearly explains WHY it's not a known issue
- [ ] You've set the correct severity level
- [ ] All code is properly formatted and commented
- [ ] You've included all necessary imports and setup

---

## Submission URL

[HackenProof Submit Report Page](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts/reports/new)

---

## Additional Tips

1. **Be specific:** Vague reports get rejected
2. **Show, don't tell:** Working PoC is worth 1000 words
3. **Explain the difference:** If similar to a known issue, explain why yours is different
4. **Be professional:** Clear, concise, respectful communication
5. **Include impact:** Quantify the risk where possible (e.g., "affects all 10,000 stakers")

---

*Template last updated: 2024-12-26*
