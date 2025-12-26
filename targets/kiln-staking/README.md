# Kiln Staking Contracts - Vulnerability Hunting Guide

> **👉 New to this? Start with [GETTING_STARTED.md](GETTING_STARTED.md)**

## Overview

This directory contains the setup, templates, and documentation for conducting security vulnerability research on the Kiln/MetaMask Validator Staking Smart Contracts.

**Target Repository:** [kilnfi/staking-contracts](https://github.com/kilnfi/staking-contracts)  
**Target Commit:** `f33eb8dc37fab40217dbe1e69853ca3fcd884a2d`  
**Bug Bounty Program:** [HackenProof - MetaMask Validator Staking](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts)  
**Deployed Contract:** `0xdc71affc862fceb6ad32be58e098423a7727bebd`

## Important Notes

To successfully hunt and write a valid report, you must focus on vulnerabilities that are:
- ✅ **In-scope** per the HackenProof program
- ✅ **Not known issues** (extensive list, especially regarding malicious operators)
- ✅ **Technically verifiable** via provided source code

The "Known Issues" list is extensive (especially regarding malicious operator attacks), so most "operator bypass" bugs will be rejected. Focus on **Protocol logic errors** or **Fee/Withdrawal DoS** that happen *without* a malicious operator.

## 📚 Documentation Guide

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Start here! Beginner-friendly introduction
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast command reference for experienced hunters
- **[REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)** - Professional report format for submissions
- **[SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)** - How to avoid rejections and maximize acceptance
- **[RESEARCH_NOTES.md](RESEARCH_NOTES.md)** - Advanced techniques and vulnerability patterns

## Quick Start

### Prerequisites

- Foundry installed (`curl -L https://foundry.paradigm.xyz | bash && foundryup`)
- Alchemy API key for mainnet forking
- Git

### Setup (15 Minutes)

```bash
# 1. Clone the target repository
git clone https://github.com/kilnfi/staking-contracts
cd staking-contracts
git checkout f33eb8dc37fab40217dbe1e69853ca3fcd884a2d

# 2. Copy the foundry.toml from this directory
cp ../secbrain/targets/kiln-staking/foundry.toml .

# 3. Set your Alchemy API key
export MAINNET_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"

# 4. Install dependencies
forge install

# 5. Test the setup
forge test --fork-url $MAINNET_RPC_URL
```

## Valid Vulnerability Targets (3 High-Priority Paths)

Based on the HackenProof scope and "Known Issues" exclusions, these are the **3 valid paths** to a successful report:

### Target A: Fee Extraction Denial of Service (Critical/High)

**Why this is valid:**
- Scope excludes "Triggering withdrawal from a Recipient as long as funds go to the right address"
- But **does not exclude** permanently freezing funds if the fee transfer fails

**What to check:**
- Look at `withdraw` or `claimRewards` functions
- Does it send fees to a `feeRecipient`?
- Does it use `transfer` or `call`?
- **CRITICAL:** If `feeRecipient` is a smart contract that reverts (e.g., no `receive()` function or out of gas), does the *entire* user withdrawal fail?

**How to prove:**
Write a test where you mock the `feeRecipient` as a contract that always reverts. If the user cannot withdraw their principal, it's a valid Critical (Freezing of Funds).

**Template:** See `test/FeeExtractionDoS.t.sol`

### Target B: 1-Wei Rounding Error DoS (Medium)

**Why this is valid:**
- "Griefing" is in scope (Medium severity)

**What to check:**
- Look at accounting logic for shares or fee splits
- Can you leave exactly **1 wei** in the system?
- Can you deposit **1 wei** to mess up a division calculation for the next user?

**How to prove:**
Demonstrate that a 1-wei donation causes the next user's transaction to revert due to `DivisionByZero` or underflow.

**Template:** See `test/RoundingErrorDoS.t.sol`

### Target C: Initializable Vulnerability (Medium)

**Why this is valid:**
- "Potentially Uninitialized Implementations" is a known issue for *implementations*
- But if the **Proxy** itself allows re-initialization, it's valid

**What to check:**
- Does the contract inherit from `Initializable`?
- Is `initialize()` protected with `initializer` modifier?
- Is the constructor checking `_disableInitializers()`?
- Can you call `initialize()` on the live contract `0xdc71...` right now?

**How to prove:**
Call `initialize()` on a fork. If it succeeds, you can take over ownership.

**Template:** See `test/InitializableVulnerability.t.sol`

## Report Template

If you find a valid vulnerability, use the template in `REPORT_TEMPLATE.md` to minimize triage time.

## Submission Strategy

See `SUBMISSION_STRATEGY.md` for detailed guidance on:
1. Checking previous audits to avoid duplicate reports
2. Submitting to HackenProof
3. Setting appropriate severity levels
4. Attaching PoC files

## Time Estimate

- Recon & Code Read: 1 hour
- PoC Writing: 1 hour  
- Report Writing: 30 mins
- **Total:** ~2.5 hours to potential $50k+ finding

## Resources

- [HackenProof Program Page](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts)
- [Kiln Staking Contracts Repo](https://github.com/kilnfi/staking-contracts)
- [Previous Audits](https://github.com/kilnfi/staking-contracts/tree/main/audits) - Check Halborn/Spearbit PDFs
- [Foundry Book](https://book.getfoundry.sh/)

## License

MIT
