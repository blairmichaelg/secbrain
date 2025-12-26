# Submission Strategy for Kiln Staking Contracts

This guide helps you avoid duplicate reports and maximize your chances of acceptance on the HackenProof platform.

## Pre-Submission Checklist

### 1. Verify Against Known Issues

The program has an extensive "Known Issues" list. **Most operator-related bugs will be rejected.**

**Common rejected findings:**
- ✗ Malicious operator can bypass restrictions
- ✗ Operator can steal funds through various mechanisms  
- ✗ Front-running by operators
- ✗ Triggering withdrawal from a Recipient (as long as funds go to right address)
- ✗ Uninitialized implementation contracts (known and accepted)

**Valid findings (not in known issues):**
- ✓ Protocol logic errors that freeze funds WITHOUT malicious operator
- ✓ Fee/Withdrawal DoS affecting user principal
- ✓ Griefing attacks (1-wei donations, etc.)
- ✓ Proxy re-initialization (different from implementation initialization)

### 2. Check Previous Audits

Before submitting, search these audit reports for your vulnerability:

**Audit Sources:**
- [Halborn Audit PDF](https://github.com/kilnfi/staking-contracts/tree/main/audits) 
- [Spearbit Audit PDF](https://github.com/kilnfi/staking-contracts/tree/main/audits)
- Other audits linked in the repository

**How to check:**
```bash
# Download audit PDFs
cd staking-contracts/audits
wget [audit-url]

# Search for keywords (macOS/Linux)
pdfgrep -i "fee transfer" *.pdf
pdfgrep -i "denial of service" *.pdf
pdfgrep -i "revert" *.pdf
pdfgrep -i "initializ" *.pdf

# Or use Preview/Adobe to search manually
```

**Red flags (STOP and don't submit):**
- Audit mentions "DoS on fee transfer" → Your finding is known
- Audit discusses "1-wei rounding" → Your finding is known  
- Audit covers "re-initialization" → Check if your scenario is different

**Green light (continue):**
- Audit doesn't mention your specific attack vector
- Audit mentions it but says "fixed" (verify it's not actually fixed)
- Your finding is in a different contract/function than audited

### 3. Verify on Mainnet Fork

**Critical:** Your PoC MUST work on a mainnet fork, not just local deployment.

```bash
# Test your PoC
forge test --fork-url $MAINNET_RPC_URL --match-test testYourVulnerability -vvvv

# Verify it fails as expected
# Check gas costs are realistic
# Ensure no false positives
```

**Common PoC mistakes:**
- Testing on local deployment instead of fork
- Using unrealistic contract states
- Assuming functions that don't exist
- Not verifying current contract version

## Submission Process

### Step 1: Prepare Your Submission

**Required materials:**
1. Completed report using `REPORT_TEMPLATE.md`
2. Working Foundry test file (`YourVulnerability.t.sol`)
3. Clear reproduction steps
4. Screenshots of test output
5. (Optional) Suggested fix with code

**File naming:**
- Report: `report_[vulnerability-name].md`
- PoC: `Exploit_[VulnerabilityName].t.sol`

### Step 2: Set Correct Severity

Use these guidelines (from HackenProof):

| Severity | Impact | Example |
|----------|--------|---------|
| **Critical** | Direct theft of funds<br>Permanent freezing of principal | Fee recipient DoS freezes all user funds permanently |
| **High** | Temporary freezing of funds<br>Theft of unclaimed yield | Fee DoS that can be fixed by admin action |
| **Medium** | Griefing attacks<br>Minor fund lockups | 1-wei donation causes next tx to fail |
| **Low** | Minimal impact<br>Information disclosure | Gas inefficiency, view function issues |

**Severity inflation = instant rejection**

If unsure between two severities, choose the **lower** one and explain why it could be higher in your report.

### Step 3: Submit via HackenProof

**Submission URL:** [https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts/reports/new](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts/reports/new)

**Form fields:**
1. **Title:** Use format from `REPORT_TEMPLATE.md`
2. **Severity:** Choose carefully (see table above)
3. **Description:** Paste your formatted report
4. **Proof of Concept:** Attach `.sol` file OR paste code
5. **Impact:** Clearly state user/protocol impact
6. **Recommendation:** Include fix suggestion

**Pro tips:**
- Use markdown formatting for readability
- Include both inline code and attached files
- Add screenshots of test output
- Reference specific line numbers in source code
- Link to relevant docs/audits

### Step 4: Monitor and Respond

**Response timeline:**
- Initial triage: 2-7 days
- Request for clarification: Respond within 48 hours
- Final decision: 1-4 weeks

**If triager requests changes:**
- Respond promptly and professionally
- Provide additional PoC if requested
- Clarify any misunderstandings
- Don't argue; provide evidence

**If marked duplicate:**
- Check the reference report
- If your finding is different, politely explain why
- Provide additional context/evidence
- Accept if legitimately duplicate

**If marked out-of-scope:**
- Re-read the scope carefully
- If you believe it's in-scope, provide clear reasoning
- Reference specific scope language
- Accept if legitimately out-of-scope

## Common Rejection Reasons (and How to Avoid)

### 1. "This is a known issue"
**Avoided by:**
- Carefully reading known issues list
- Checking previous audits
- Explaining why your finding is different

### 2. "Cannot reproduce"
**Avoided by:**
- Testing on actual mainnet fork
- Providing complete setup instructions
- Including all necessary code/imports
- Testing with realistic parameters

### 3. "Out of scope"
**Avoided by:**
- Reading scope section carefully
- Only targeting in-scope contracts
- Avoiding operator-related issues
- Focusing on protocol logic errors

### 4. "Low impact / Informational"
**Avoided by:**
- Demonstrating real impact (funds frozen, etc.)
- Showing attack is practical
- Quantifying the damage
- Connecting to security properties

### 5. "Incomplete report"
**Avoided by:**
- Following REPORT_TEMPLATE.md
- Including all required sections
- Providing working PoC
- Suggesting fixes

## Maximizing Your Success Rate

### Research Phase (Before Writing PoC)
1. ✅ Read scope thoroughly
2. ✅ Review known issues exhaustively  
3. ✅ Check all previous audits
4. ✅ Understand core protocol logic
5. ✅ Identify attack vectors not in audits

### Development Phase (Writing PoC)
1. ✅ Test on mainnet fork
2. ✅ Use realistic parameters
3. ✅ Document every step
4. ✅ Handle edge cases
5. ✅ Verify impact claims

### Submission Phase
1. ✅ Use professional tone
2. ✅ Follow template exactly
3. ✅ Set appropriate severity
4. ✅ Include all materials
5. ✅ Proofread everything

### Follow-up Phase
1. ✅ Respond quickly to questions
2. ✅ Provide additional evidence if requested
3. ✅ Accept feedback gracefully
4. ✅ Learn from rejections

## Time Budget

Based on the original problem statement:

- **Recon & Code Read:** 1 hour
- **PoC Writing:** 1 hour
- **Report Writing:** 30 mins
- **Pre-submission Checks:** 30 mins
- **Total:** ~3 hours

**Don't rush:** A well-researched, properly documented finding is worth more than multiple rushed submissions.

## Expected Returns

**Based on program maximums:**
- Critical: Up to $50,000+
- High: Up to $25,000
- Medium: Up to $10,000  
- Low: Up to $2,500

**Reality check:**
- Most accepted findings: $5,000-$15,000
- Critical findings are rare
- Quality > Quantity

## Resources

- [HackenProof Program Rules](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts)
- [HackenProof Triage Guidelines](https://hackenproof.com/triage-guidelines)
- [Immunefi Severity System](https://immunefi.com/severity-system/)
- [Foundry Book](https://book.getfoundry.sh/)

---

*Last updated: 2024-12-26*
