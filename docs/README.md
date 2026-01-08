# 📚 SecBrain Documentation Index

Welcome! This directory contains comprehensive guides for contributing to SecBrain and understanding its various components.

## 📖 Documentation Overview

This docs directory contains contributor-focused guides. For core project documentation (architecture, workflows, operations), see [secbrain/docs/](../secbrain/docs/).

For workflow optimization and analysis guides, see [guides/](guides/) directory.

## 🎯 Quick Navigation

| Topic | Guide |
|-------|-------|
| **New to Git?** | [GIT_QUICK_START.md](GIT_QUICK_START.md) |
| **Git concepts explained** | [SUMMARY.md](SUMMARY.md) |
| **Contributing workflow** | [../CONTRIBUTING.md](../CONTRIBUTING.md) |
| **CI/CD status** | [CI_STATUS.md](CI_STATUS.md) |
| **Testing strategies** | [TESTING-STRATEGIES.md](TESTING-STRATEGIES.md) |
| **Security patterns** | [SOLIDITY_SECURITY_PATTERNS.md](SOLIDITY_SECURITY_PATTERNS.md) |
| **Troubleshooting** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| **SBOM & supply chain** | [SBOM-SECURITY.md](SBOM-SECURITY.md) |
| **Gas optimizations** | [GAS_OPTIMIZATION_GUIDE.md](GAS_OPTIMIZATION_GUIDE.md) |
| **Gas optimization how-to** ⭐ | [GAS_OPTIMIZATION_IMPLEMENTATION.md](GAS_OPTIMIZATION_IMPLEMENTATION.md) |
| **Implementation status** | [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) |

## 📖 Documentation Categories

### 🚀 Workflow & Optimization Guides

For detailed workflow and optimization documentation, see [guides/](guides/):
- **[Bounty Workflow Analysis](guides/BOUNTY_WORKFLOW_ANALYSIS.md)** - Complete workflow analysis and optimization roadmap
- **[Workflow Optimization Guide](guides/WORKFLOW_OPTIMIZATION_GUIDE.md)** - Optimization features and best practices  
- **[Optimization Guide](guides/OPTIMIZATION-GUIDE.md)** - Performance and efficiency best practices
- **[Run Analysis Guidance](guides/RUN_ANALYSIS_GUIDANCE.md)** - Debugging zero-finding runs
- **[Automation Quick Reference](guides/AUTOMATION-QUICK-REF.md)** - Daily workflows and tools
- **[Comprehensive Security Analysis](guides/COMPREHENSIVE_SECURITY_ANALYSIS_QUICKREF.md)** - Security analysis workflow guide

### 🛠️ Setup & Configuration

- **[Verification Guide](guides/VERIFICATION.md)** - How to verify installation and setup
- **[Free Tier Models](guides/FREE_TIER_MODELS.md)** - Using free API tiers
- **[Dependency Management](guides/DEPENDENCY-MANAGEMENT.md)** - Managing project dependencies

### 🔧 Testing & Quality

- **[TESTING-STRATEGIES.md](TESTING-STRATEGIES.md)** - Complete guide to property-based testing, fuzzing, and mutation testing
- **[TESTING-QUICK-REF.md](TESTING-QUICK-REF.md)** - Quick reference for running tests
- **[testing-examples/](testing-examples/)** - Example test files (Echidna, Invariant tests)

### 🔐 Security

- **[SOLIDITY_SECURITY_PATTERNS.md](SOLIDITY_SECURITY_PATTERNS.md)** - Advanced security patterns for smart contracts
- **[SBOM-SECURITY.md](SBOM-SECURITY.md)** - Software Bill of Materials and supply chain security
- **[GAS_OPTIMIZATION_GUIDE.md](GAS_OPTIMIZATION_GUIDE.md)** - Comprehensive gas optimization patterns with examples
- **[GAS_OPTIMIZATION_IMPLEMENTATION.md](GAS_OPTIMIZATION_IMPLEMENTATION.md)** ⭐ - Step-by-step implementation guide for gas optimizations

### 🆘 Operations & Troubleshooting

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common runtime issues and solutions (spend limits, RPC configuration, etc.)

### 🤝 Contributing

- **[SUMMARY.md](SUMMARY.md)** - Overview of what was fixed and Git concepts
- **[GIT_QUICK_START.md](GIT_QUICK_START.md)** - Daily Git reference for contributors
- **[CI_STATUS.md](CI_STATUS.md)** - Current CI pipeline state and known issues
- **[../CONTRIBUTING.md](../CONTRIBUTING.md)** - Complete contribution workflow guide
- **[IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md)** - Summary of major implementations

---

## 📖 Git & Contribution Guides

### For Beginners

1. **[SUMMARY.md](SUMMARY.md)** - Read this FIRST!
   - Friendly explanation of what was fixed
   - Git concepts in plain English
   - Real-world scenarios
   - 9KB, ~20 min read

2. **[GIT_QUICK_START.md](GIT_QUICK_START.md)** - Your daily reference
   - Quick command reference
   - Step-by-step workflows
   - Common scenarios with solutions
   - 7KB, ~15 min read
   - 🚀 Emoji-heavy and easy to scan!

### For Everyone

3. **[../CONTRIBUTING.md](../CONTRIBUTING.md)** - The complete guide
   - Everything about Git and GitHub
   - Detailed workflow explanations
   - Merge conflict resolution
   - CI/CD workflow
   - Common issues and solutions
   - 12KB, ~30 min read

### For CI/CD Questions

4. **[CI_STATUS.md](CI_STATUS.md)** - Current CI state
   - Why type checking is non-blocking
   - What contributors need to know
   - How to fix type errors
   - Long-term improvement plan
   - 6KB, ~15 min read

## 🗺️ Reading Path by Experience Level

### Never Used Git Before?
```
1. SUMMARY.md
2. GIT_QUICK_START.md (bookmark this!)
3. Try making a change
4. Refer to CONTRIBUTING.md as needed
```

### Used Git But Not GitHub?
```
1. GIT_QUICK_START.md (refresh basics)
2. CONTRIBUTING.md (sections on PRs and code review)
3. CI_STATUS.md (understand our CI)
```

### Experienced with Git & GitHub?
```
1. CONTRIBUTING.md (skim for project-specific details)
2. CI_STATUS.md (understand why mypy is non-blocking)
3. Jump in and contribute!
```

## 🎓 What You'll Learn

### From SUMMARY.md
- What was broken and how it was fixed
- Git concepts explained simply
- Why things work the way they do
- Quick reference card

### From GIT_QUICK_START.md
- Essential Git commands
- Common scenarios (with solutions!)
- Quick contribution workflow
- Best practices

### From CONTRIBUTING.md
- Complete Git workflow
- How commits, branches, and merges work
- Creating and reviewing PRs
- Dealing with merge conflicts
- CI/CD process
- Troubleshooting guide

### From CI_STATUS.md
- Current CI pipeline
- Type checking status
- What type errors mean
- How to fix type errors
- What contributors need to know

## ❓ Quick Answers

**"I want to make my first contribution"**
→ Read [GIT_QUICK_START.md](GIT_QUICK_START.md) and follow the workflow

**"I got a merge conflict"**
→ See [CONTRIBUTING.md](../CONTRIBUTING.md) section "Dealing with Merge Conflicts"

**"CI is failing on my PR"**
→ Check [CI_STATUS.md](CI_STATUS.md) and the CI logs on GitHub

**"I made a mistake with Git"**
→ See [GIT_QUICK_START.md](GIT_QUICK_START.md) section "Oh No! I Messed Up!"

**"What is Git/GitHub?"**
→ Start with [SUMMARY.md](SUMMARY.md) section "Understanding Git & GitHub"

**"I accidentally committed to main"**
→ See [CONTRIBUTING.md](../CONTRIBUTING.md) "Common Issues and Solutions"

**"SecBrain is giving errors about spend limits or RPC URLs"**
→ See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common runtime issues

## 🔗 External Resources

These guides are specific to this project. For general Git learning:

- **Interactive Tutorial**: https://learngitbranching.js.org/
- **Official Docs**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf
- **Book (free)**: https://git-scm.com/book/en/v2

## 📝 Document Summary

| File | Size | Read Time | Best For |
|------|------|-----------|----------|
| [SUMMARY.md](SUMMARY.md) | 9KB | 20 min | Understanding what was fixed |
| [GIT_QUICK_START.md](GIT_QUICK_START.md) | 7KB | 15 min | Daily Git reference |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 12KB | 30 min | Complete workflow guide |
| [CI_STATUS.md](CI_STATUS.md) | 6KB | 15 min | CI/CD questions |

**Total reading time**: ~1.5 hours to read everything
**Minimum to start**: ~20 minutes (SUMMARY + GIT_QUICK_START)

## 🆘 Getting Help

If you're stuck after reading the docs:

1. **Search the docs** - Use Ctrl+F to search these files
2. **Check GitHub Issues** - Someone might have had the same problem
3. **Ask in a PR** - Comment on your pull request
4. **Open an issue** - Create a new issue with the `question` label

## 🎉 You've Got This!

Remember:
- Everyone struggles with Git at first
- These docs are here to help
- No question is too basic
- The community is friendly
- Practice makes perfect!

---

**Last updated**: December 2024 (Current as of December 25, 2024)
**Questions?** Open an issue or ask in your PR!

---

## 📦 Core Project Documentation

For core project documentation, see the [secbrain/docs/](../secbrain/docs/) directory:

| Document | Description |
|----------|-------------|
| [Architecture](../secbrain/docs/architecture-updated.md) | System design and component overview |
| [Workflows](../secbrain/docs/workflows.md) | Run modes and phase documentation |
| [Operations](../secbrain/docs/ops.md) | Setup, configuration, and usage guide |
| [Threat Model](../secbrain/docs/threat_model.md) | Security considerations and mitigations |
| [Automated Agents](../secbrain/docs/automated-agents.md) | Documentation for the automated agent suite |

## 🔗 Related Documentation

- **[Main README](../README.md)** - Project overview and quick start (includes GitHub Actions status badges for security, quality, testing, and fuzzing)
- **[AUTOMATION-QUICK-REF.md](../AUTOMATION-QUICK-REF.md)** - Quick reference for automated agents
- **[IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md)** - Summary of major implementations
