# Kiln Staking Contracts - Complete File Index

This is a complete index of all files in the Kiln staking contracts vulnerability hunting workflow.

## 📖 Start Here

- **[GETTING_STARTED.md](GETTING_STARTED.md)** ⭐
  - **New users start here**
  - Learning paths for beginners, intermediate, and advanced hunters
  - Quick setup guide and checklist
  - Common issues and troubleshooting

## 📚 Main Documentation

### Essential Guides

1. **[README.md](README.md)**
   - Main technical guide
   - Complete setup instructions (15 min)
   - Three valid vulnerability targets with detailed descriptions
   - Time estimates and resource links

2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
   - Fast command reference
   - Essential forge/cast commands
   - Research checklist
   - Troubleshooting tips
   - **Use this**: When you need quick access to commands

3. **[SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)**
   - How to avoid rejections
   - Pre-submission checklist
   - Audit checking procedures
   - Severity guidelines
   - Response strategies
   - **Use this**: Before submitting any finding

### Templates

4. **[REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)**
   - Professional report format
   - Title conventions
   - Impact descriptions
   - PoC structure
   - Fix recommendations
   - **Use this**: When writing your report

### Advanced Resources

5. **[RESEARCH_NOTES.md](RESEARCH_NOTES.md)**
   - Advanced vulnerability patterns
   - Code analysis techniques
   - Testing strategies
   - Lessons learned
   - Tool usage guides
   - **Use this**: For deep technical research

## 💻 Code Templates

Located in `test/` directory:

### 1. Fee Extraction DoS
**File:** [test/FeeExtractionDoS.t.sol](test/FeeExtractionDoS.t.sol)
- **Severity:** Critical
- **Impact:** Permanent freezing of user funds
- **Pattern:** Fee recipient revert causes withdrawal DoS
- **Lines:** ~160
- **Testing checklist included:** ✅
- **Use when:** Looking for critical DoS vulnerabilities

### 2. Rounding Error DoS
**File:** [test/RoundingErrorDoS.t.sol](test/RoundingErrorDoS.t.sol)
- **Severity:** Medium
- **Impact:** Griefing attack, 1-wei donation breaks accounting
- **Pattern:** Share inflation, division by zero
- **Lines:** ~200
- **Multiple test cases:** ✅
- **Use when:** Analyzing share/vault accounting

### 3. Initializable Vulnerability
**File:** [test/InitializableVulnerability.t.sol](test/InitializableVulnerability.t.sol)
- **Severity:** Medium
- **Impact:** Ownership takeover via re-initialization
- **Pattern:** Proxy pattern vulnerabilities
- **Lines:** ~230
- **Implementation vs Proxy tests:** ✅
- **Use when:** Checking upgradeable contracts

## ⚙️ Configuration Files

### 1. Foundry Configuration
**File:** [foundry.toml](foundry.toml)
- Optimized for mainnet fork testing
- Fuzz settings: 256 runs (default)
- RPC endpoints configured
- Compiler: Solidity 0.8.20
- **Copy to target repo** after cloning

### 2. Environment Template
**File:** [.env.example](.env.example)
- Required: MAINNET_RPC_URL
- Optional: Etherscan API keys
- Target contract addresses for reference
- **Copy to .env** and fill in your values

### 3. Git Ignore
**File:** [.gitignore](.gitignore)
- Excludes workspace/ directory
- Excludes .env (secrets)
- Excludes build artifacts (out/, cache/)
- Keeps .env.example

## 🚀 Automation

### Setup Script
**File:** [setup.sh](setup.sh)
- **Executable:** ✅ (chmod +x)
- **Features:**
  - Prerequisite checking (git, forge, API key)
  - Repository cloning and checkout
  - Dependency installation
  - Template copying
  - Environment validation
- **Usage:** `./setup.sh`
- **Time:** ~5 minutes

## 📊 File Statistics

| Category | Files | Total Lines | Total Size |
|----------|-------|-------------|------------|
| Documentation | 7 | ~2,000 | ~45 KB |
| Code Templates | 3 | ~600 | ~22 KB |
| Configuration | 3 | ~150 | ~3 KB |
| **Total** | **13** | **~2,750** | **~70 KB** |

## 🗺️ Usage Workflow

### Quick Hunt (2.5 hours)
```
GETTING_STARTED.md (5 min)
    ↓
setup.sh (5 min)
    ↓
README.md (vulnerability targets) (15 min)
    ↓
Choose PoC template (5 min)
    ↓
Research & customize PoC (1 hour)
    ↓
Test on fork (30 min)
    ↓
REPORT_TEMPLATE.md (write report) (20 min)
    ↓
SUBMISSION_STRATEGY.md (final check) (10 min)
    ↓
Submit on HackenProof
```

### Deep Research (1 day)
```
GETTING_STARTED.md
    ↓
RESEARCH_NOTES.md (study patterns)
    ↓
setup.sh
    ↓
Deep contract analysis (4 hours)
    ↓
Multiple PoC attempts (3 hours)
    ↓
Report writing (30 min)
    ↓
Submit
```

## 🎯 Quick Access by Task

### "I need to set up my environment"
→ [setup.sh](setup.sh) or [GETTING_STARTED.md](GETTING_STARTED.md)

### "I need a command reference"
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### "I found a fee DoS vulnerability"
→ [test/FeeExtractionDoS.t.sol](test/FeeExtractionDoS.t.sol)

### "I found a rounding error"
→ [test/RoundingErrorDoS.t.sol](test/RoundingErrorDoS.t.sol)

### "I found a re-initialization bug"
→ [test/InitializableVulnerability.t.sol](test/InitializableVulnerability.t.sol)

### "I need to write a report"
→ [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)

### "Should I submit this finding?"
→ [SUBMISSION_STRATEGY.md](SUBMISSION_STRATEGY.md)

### "I want advanced techniques"
→ [RESEARCH_NOTES.md](RESEARCH_NOTES.md)

### "I'm a complete beginner"
→ [GETTING_STARTED.md](GETTING_STARTED.md)

## 📋 Reading Order Recommendations

### For First-Time Users
1. GETTING_STARTED.md (10 min)
2. README.md (10 min)
3. QUICK_REFERENCE.md (skim, 5 min)
4. Pick one PoC template (read, 10 min)
5. REPORT_TEMPLATE.md (5 min)

**Total time:** 40 minutes before starting

### For Experienced Hunters
1. README.md (5 min)
2. QUICK_REFERENCE.md (5 min)
3. Skim PoC templates (5 min)
4. Reference other docs as needed

**Total time:** 15 minutes before starting

## 🔗 External Resources

- **Target Contract:** `0xdc71affc862fceb6ad32be58e098423a7727bebd`
- **Repository:** [kilnfi/staking-contracts](https://github.com/kilnfi/staking-contracts)
- **Bug Bounty:** [HackenProof Program](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts)
- **Submit:** [Report Submission](https://dashboard.hackenproof.com/user/programs/metamask-validator-staking-smart-contracts/reports/new)
- **Foundry:** [book.getfoundry.sh](https://book.getfoundry.sh/)

## 🔄 Updates and Maintenance

This file index is current as of 2024-12-26.

**File structure:**
```
targets/kiln-staking/
├── .env.example
├── .gitignore
├── GETTING_STARTED.md       ⭐ Start here
├── INDEX.md                 📖 This file
├── QUICK_REFERENCE.md       ⚡ Commands
├── README.md                📚 Main guide
├── REPORT_TEMPLATE.md       📝 Report format
├── RESEARCH_NOTES.md        🔬 Advanced
├── SUBMISSION_STRATEGY.md   ✅ Pre-submit
├── foundry.toml             ⚙️ Config
├── setup.sh                 🚀 Setup script
└── test/
    ├── FeeExtractionDoS.t.sol
    ├── InitializableVulnerability.t.sol
    └── RoundingErrorDoS.t.sol
```

---

**Happy hunting! 🎯**

*For questions or improvements, open an issue in the [SecBrain repository](https://github.com/blairmichaelg/secbrain).*
