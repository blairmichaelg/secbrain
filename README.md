# SecBrain

**Multi-agent security bounty system with research integration, advisor models, and guarded tooling.**

[![Security Scan](https://github.com/blairmichaelg/secbrain/actions/workflows/security-scan.yml/badge.svg)](https://github.com/blairmichaelg/secbrain/actions/workflows/security-scan.yml)
[![Solidity Security](https://github.com/blairmichaelg/secbrain/actions/workflows/solidity-security.yml/badge.svg)](https://github.com/blairmichaelg/secbrain/actions/workflows/solidity-security.yml)
[![Code Quality](https://github.com/blairmichaelg/secbrain/actions/workflows/code-quality.yml/badge.svg)](https://github.com/blairmichaelg/secbrain/actions/workflows/code-quality.yml)
[![Python Testing](https://github.com/blairmichaelg/secbrain/actions/workflows/python-testing.yml/badge.svg)](https://github.com/blairmichaelg/secbrain/actions/workflows/python-testing.yml)
[![Foundry Fuzzing](https://github.com/blairmichaelg/secbrain/actions/workflows/foundry-fuzzing.yml/badge.svg)](https://github.com/blairmichaelg/secbrain/actions/workflows/foundry-fuzzing.yml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

SecBrain is a CLI-first Python project that automates bug bounty workflows using a coordinated team of AI agents. It combines:

- **Multi-agent architecture**: Specialized agents for each phase (recon, hypothesis, exploit, triage, reporting)
- **Research-first approach**: Enhanced Perplexity integration with TTL-based caching, rate limiting, and specialized research methods for severity assessment, attack vectors, and market conditions
- **Advisor oversight**: Gemini model reviews critical decisions
- **Guarded execution**: ACLs, rate limits, kill-switch, and human approval checkpoints

## Key Features

- 🔍 **Automated recon** with subfinder, amass, httpx integration
- 🧠 **Vulnerability hypothesis generation** using AI reasoning
- 🔬 **Research-backed testing** with enhanced Perplexity integration:
  - Real-world severity context with exploit examples
  - Attack vector discovery from recent exploits
  - Market condition analysis for exploit validation
  - TTL-based intelligent caching (1h-168h)
  - Strict rate limiting (10 req/min)
- ✅ **Advisor review** at critical checkpoints
- 🛡️ **Safety controls**: Scope enforcement, rate limits, kill-switch
- 📊 **Structured logging** in JSONL format
- 📝 **Report generation** with CWE/CVE references
- 📈 **Insights dashboard** for actionable security findings

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/blairmichaelg/secbrain.git
cd secbrain

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Set up API keys

```bash
# Required for research integration
export PERPLEXITY_API_KEY=pplx-xxxx

# Required for advisor model
export GOOGLE_API_KEY=AIza-xxxx

# Required for worker model (choose one)
export TOGETHER_API_KEY=your-together-key      # Recommended: Together AI
# OR
export OPENROUTER_API_KEY=your-openrouter-key  # Alternative: OpenRouter
# OR
export OPENAI_API_KEY=your-openai-key          # Alternative: OpenAI
```

### Run a dry-run test

```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/test \
  --dry-run
```

### Test enhanced research capabilities

```bash
# Run the research integration test script
python test_research.py
```

This will verify:
- TTL-based caching behavior
- Rate limiting enforcement (10 req/min)
- Specialized research methods (severity, attack vectors, market conditions)
- Backward compatibility with existing methods

### Generate insights from results

```bash
# Generate insights report
secbrain insights --workspace ./targets/protocol1

# Generate HTML report and open in browser
secbrain insights --workspace ./targets/protocol1 --format html --open
```

## Documentation

### Core Documentation
- 📖 [Architecture](secbrain/docs/architecture-updated.md) - System design and components
- 🔄 [Workflows](secbrain/docs/workflows.md) - Run modes and phases
- 🛠️ [Operations Guide](secbrain/docs/ops.md) - Setup and usage
- 🔒 [Threat Model](secbrain/docs/threat_model.md) - Security considerations
- 📊 [Insights Guide](secbrain/docs/INSIGHTS-GUIDE.md) - Turn data into actionable insights
- 🧪 [Invariant Testing Guide](docs/INVARIANT-TESTING-GUIDE.md) - Property-based testing for smart contracts
- 🔧 [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Contributing & Quality
- 🤝 [Contributing Guide](CONTRIBUTING.md) - How to contribute
- 🌿 [Branch Strategy](BRANCH-STRATEGY.md) - Simple single-branch workflow
- 🧪 [Testing Strategies](docs/TESTING-STRATEGIES.md) - Advanced testing approaches
- 🔐 [Security Patterns](docs/SOLIDITY_SECURITY_PATTERNS.md) - Smart contract security
- 🎯 [Git Quick Start](docs/GIT_QUICK_START.md) - Git workflow basics
- 🤖 [Automated Agents](secbrain/docs/automated-agents.md) - CI/CD automation suite

### Quick References
- ⚡ [Automation Quick Ref](AUTOMATION-QUICK-REF.md) - Daily workflows and tools
- 📋 [Testing Quick Ref](docs/TESTING-QUICK-REF.md) - Quick testing commands
- 📚 [Documentation Index](docs/README.md) - All contributor guides

## CLI Commands

| Command | Description |
|---------|-------------|
| `secbrain run` | Execute bounty workflow |
| `secbrain insights` | Generate actionable insights report from workspace |
| `secbrain validate` | Validate configuration files |
| `secbrain version` | Show version |

For detailed CLI options, see the [Operations Guide](secbrain/docs/ops.md).

## Project Structure

```
secbrain/
├── secbrain/              # Main Python package
│   ├── agents/            # Agent implementations
│   ├── cli/               # CLI interface
│   ├── core/              # Context, logging, types
│   ├── insights/          # Insights aggregation and reporting
│   ├── models/            # Model abstractions
│   ├── tools/             # Tool wrappers
│   ├── workflows/         # Orchestration logic
│   └── docs/              # Core project documentation
├── docs/                  # Contributor-focused guides
├── config/                # Configuration files
├── examples/              # Example targets
├── scripts/               # Utility scripts
├── targets/               # Target analysis workspaces
└── tests/                 # Test suite
```

## Development

### Code Quality

```bash
# Run linter
cd secbrain
python -m ruff check .

# Auto-fix issues
python -m ruff check . --fix
```

### Security Scanning

SecBrain includes custom Semgrep rules for detecting security vulnerabilities:

```bash
# Run all custom security rules
semgrep --config=.semgrep/rules/ secbrain/

# Run specific rule categories
semgrep --config=.semgrep/rules/subprocess-injection.yml secbrain/
semgrep --config=.semgrep/rules/sql-injection.yml secbrain/
semgrep --config=.semgrep/rules/command-injection.yml secbrain/
semgrep --config=.semgrep/rules/general-security.yml secbrain/

# Run Solidity security rules
semgrep --config=.semgrep/rules/solidity-security.yml targets/

# Run with auto-fix (where available)
semgrep --config=.semgrep/rules/ --autofix secbrain/
```

Custom rules detect:
- 🔒 **Subprocess injection** - Shell injection via subprocess calls
- 🔒 **SQL injection** - Unsafe SQL query construction
- 🔒 **Command injection** - OS command injection vulnerabilities
- 🔒 **Solidity vulnerabilities** - Reentrancy, unchecked calls, access control issues
- 🔒 **General security** - Hardcoded secrets, weak crypto, path traversal

See [`.semgrep/README.md`](.semgrep/README.md) for detailed rule documentation.

### Running Tests

SecBrain uses a comprehensive, multi-layered testing strategy:

```bash
cd secbrain

# Standard unit tests
python -m pytest tests/ -v

# Property-based tests with Hypothesis
python -m pytest tests/test_property_based.py -v --hypothesis-show-statistics

# Run with coverage
python -m pytest tests/ --cov=secbrain --cov-report=term-missing

# Mutation testing (verifies test quality)
mutmut run --paths-to-mutate=secbrain/utils/
```

For smart contract testing:

```bash
# Quick fuzzing (32 runs)
FOUNDRY_PROFILE=quick forge test

# Standard fuzzing (256 runs)
forge test

# CI fuzzing (10,000 runs)
FOUNDRY_PROFILE=ci forge test

# Invariant tests only
forge test --match-contract Invariant -vvv

# Invariant tests with CI profile (comprehensive)
FOUNDRY_PROFILE=ci forge test --match-contract Invariant -vvv

# Echidna fuzzing (if installed)
echidna . --contract EchidnaTestExample --config echidna.yaml
```

**Invariant Test Coverage:**
- SingleAssetStaking: Balance consistency, accounting, pause state
- WOETH: ERC4626 properties, conversion consistency, backing assets
- LidoARM: Liquidity management, share accounting

See [Invariant Testing Guide](docs/INVARIANT-TESTING-GUIDE.md) for details.

**Advanced Testing Features:**
- 🧪 **Property-Based Testing**: Hypothesis generates thousands of random inputs
- 🔬 **Fuzzing**: Foundry/Echidna for comprehensive smart contract testing
- 🧬 **Mutation Testing**: Mutmut verifies test suite quality
- 📊 **Invariant Testing**: Handler-based state machine testing

See [Testing Strategies](docs/TESTING-STRATEGIES.md) for more details.

## Safety Controls

1. **Scope Enforcement**: All actions validated against scope.yaml
2. **Rate Limits**: Configurable per-tool and global caps
3. **Kill-Switch**: External file or API signal for immediate halt
4. **Human Approval**: Required for high-risk actions
5. **Dry-Run Mode**: Full simulation without network calls

## Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### For Beginners
- 📖 **Start here**: [Git Quick Start Guide](docs/GIT_QUICK_START.md)
- 📚 **Full guide**: [Contributing Guide](CONTRIBUTING.md)

### Quick Contribution Flow

```bash
# 1. Fork and clone the repository
git clone https://github.com/blairmichaelg/secbrain.git
cd secbrain

# 2. Create a feature branch
git checkout -b feature/my-improvement

# 3. Make changes and commit
git add .
git commit -m "Add: brief description of changes"

# 4. Push and create PR
git push -u origin feature/my-improvement
```

### Current CI Status

Our GitHub Actions CI automatically runs:
- ✅ **Linting** (ruff) - Code style checks
- ⚠️ **Type checking** (mypy) - Currently non-blocking while we fix legacy type errors
- ✅ **Unit tests** - pytest with coverage requirements
- ✅ **Integration tests** - Dry-run validation

See [CI Status](docs/CI_STATUS.md) for more details.

## License

MIT

---

**Need help?** Check the [documentation](docs/README.md) or open an issue!
