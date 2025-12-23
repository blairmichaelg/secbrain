# SecBrain

**Multi-agent security bounty system with research integration, advisor models, and guarded tooling.**

## Overview

SecBrain is a CLI-first Python project that automates bug bounty workflows using a coordinated team of AI agents. It combines:

- **Multi-agent architecture**: Specialized agents for each phase (recon, hypothesis, exploit, triage, reporting)
- **Research-first approach**: Perplexity integration for external knowledge and learning
- **Advisor oversight**: Gemini model reviews critical decisions
- **Guarded execution**: ACLs, rate limits, kill-switch, and human approval checkpoints

## Key Features

- 🔍 **Automated recon** with subfinder, amass, httpx integration
- 🧠 **Vulnerability hypothesis generation** using AI reasoning
- 🔬 **Research-backed testing** with Perplexity for context
- ✅ **Advisor review** at critical checkpoints
- 🛡️ **Safety controls**: Scope enforcement, rate limits, kill-switch
- 📊 **Structured logging** in JSONL format
- 📝 **Report generation** with CWE/CVE references

## Architecture

```
CLI → Orchestrator → Agents → Models/Tools → Core Context
         ↓             ↓           ↓
    Supervisor    [Ingest,      [Worker,
                   Planner,      Advisor,
                   Recon,        Research]
                   Exploit,        +
                   Triage,      [HTTP,
                   Report]       Recon,
                                 Scanners]
```

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd secbrain

# Install with uv (recommended)
uv sync

# Or with pip (using hash-verified requirements for security)
pip install --require-hashes -r requirements.lock

# Or install in development mode
pip install -e ".[dev]"
```

For more details on dependency management and supply chain security, see [DEPENDENCY-MANAGEMENT.md](../DEPENDENCY-MANAGEMENT.md).

## Quick Start

1. **Set up API keys**:
```bash
export PERPLEXITY_API_KEY=pplx-xxxx
export GOOGLE_API_KEY=AIza-xxxx
```

2. **Run a dry-run test**:
```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/test \
  --dry-run
```

3. **Run a real bounty workflow**:
```bash
secbrain run \
  --scope path/to/scope.yaml \
  --program path/to/program.json \
  --workspace ./targets/my-target \
  --rpc-url https://mainnet.infura.io/v3/<key> \
  --block-number 12345678 \
  --chain-id 1 \
  --exploit-iterations 3 \
  --profit-threshold 0.1
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `secbrain run` | Execute bounty workflow |
| `secbrain insights` | Generate actionable insights report from workspace |
| `secbrain validate` | Validate configuration files |
| `secbrain version` | Show version |

### Run Options

| Option | Description |
|--------|-------------|
| `--scope` | Path to scope.yaml |
| `--program` | Path to program.json |
| `--workspace` | Output directory |
| `--dry-run` | Simulate without real calls |
| `--phases` | Comma-separated phase list |
| `--kill-switch-file` | External stop signal file |
| `--rpc-url` | RPC URL for forked exploit execution |
| `--block-number` | Block number to pin the fork |
| `--chain-id` | Chain ID for forked execution |
| `--exploit-iterations` | Attempts per hypothesis (default 3) |
| `--profit-threshold` | Stop iterating after profit (ETH) meets threshold (default 0.1) |

### Insights Options

After running SecBrain, generate actionable insights to guide your security research:

```bash
# Generate insights report
secbrain insights --workspace ./targets/protocol1

# Generate HTML report and open in browser
secbrain insights --workspace ./targets/protocol1 --format html --open

# Generate all formats (markdown, html, json, csv)
secbrain insights --workspace ./targets/protocol1 --format all --output ./reports
```

**What you get:**
- ✅ **Executive Summary**: Critical issues, status, next actions
- 📊 **Key Metrics**: Success rates, hypothesis quality, exploit results
- 🎯 **Actionable Insights**: Prioritized issues by category (Critical/High/Medium/Low)
- 📝 **Recommendations**: Clear next steps based on your data

See the [Insights Guide](docs/INSIGHTS-GUIDE.md) for detailed usage and examples.

## Documentation

- [Architecture](docs/architecture-updated.md) - System design and components
- [Workflows](docs/workflows.md) - Run modes and phases
- [Threat Model](docs/threat_model.md) - Security considerations
- [Operations](docs/ops.md) - Setup and usage guide
- [Dependency Management](../DEPENDENCY-MANAGEMENT.md) - Hash-verified dependencies and SBOM
- [Insights Guide](docs/INSIGHTS-GUIDE.md) - **NEW: Turn your data into actionable insights**

## Project Structure

```
secbrain/
├── secbrain/
│   ├── agents/        # Agent implementations
│   ├── cli/           # CLI interface
│   ├── core/          # Context, logging, types
│   ├── insights/      # Insights aggregation and reporting (NEW)
│   ├── models/        # Model abstractions
│   ├── tools/         # Tool wrappers
│   └── workflows/     # Orchestration logic
├── config/            # Configuration files
├── docs/              # Documentation
├── examples/          # Example targets
└── tests/             # Test suite
```

## Instascope bundles (Immunefi)

- Layout per protocol: `targets/<protocol>/instascope/` (Instascope sources: `src/`, `foundry.toml`, `build.sh`, generated `out/`/`cache/`); `targets/<protocol>/workspace/` (SecBrain artifacts: `logs/`, `findings/`, `reports/`, `audit.jsonl`, scope/program files).
- Fetch/unpack: `python secbrain/scripts/fetch_instascope.py --protocol <name> --source <zip_or_tar>`; add `--build` to run `build.sh` after unpack; add `--force` to overwrite existing.
- Build: run `forge build` (or `./build.sh`) with cwd `targets/<protocol>/instascope/`. Requires Foundry/forge on PATH and a shell (bash/WSL on Windows).
- Gitignore: `out/`, `cache/`, `lib/` under `targets/**/instascope` are ignored by default.

## Safety Controls

1. **Scope Enforcement**: All actions validated against scope.yaml
2. **Rate Limits**: Configurable per-tool and global caps
3. **Kill-Switch**: External file or API signal for immediate halt
4. **Human Approval**: Required for high-risk actions
5. **Dry-Run Mode**: Full simulation without network calls

## Implementation Status

### Completed ✅

- **Core Layer**: RunContext, Session, structured JSONL logging
- **Model Layer**: Worker models (OpenAI-compatible, Ollama), Gemini advisor, Perplexity research
- **Tool Layer**: HTTP client, recon CLI wrappers (subfinder, amass, httpx, ffuf, nmap), scanners (nuclei, semgrep), SQLite storage
- **Agent Layer**: All 10 agents (supervisor, ingest, planner, recon, hypothesis, exploit, static, triage, reporting, meta-learning)
- **Orchestration**: Phase graph workflow with supervisor checks
- **CLI**: Typer-based interface with async support
- **Safety Controls**: ACLs, rate limits, kill-switch, scope enforcement
- **Documentation**: Architecture, workflows, threat model, operations guide
- **Examples**: Scope/program configs, dry-run and smoke tests

### Stubs / Needs Enhancement 🔧

- Worker model clients need real API integration testing
- Recon CLI wrappers assume tools are installed on PATH
- Scanner integrations need template configuration
- Research caching uses simple in-memory dict (consider Redis)
- Approval flow is auto-approve in dry-run only

## Development

### Code Quality

The project uses `ruff` for linting and code formatting. To run the linter:

```bash
cd secbrain
python -m ruff check .
```

To automatically fix fixable issues:

```bash
cd secbrain
python -m ruff check . --fix
```

**Note**: Some ruff checks (F821 undefined-name, F841 unused-variable) are currently ignored in the configuration to allow development progress. These should be addressed in future PRs.

### Running Tests

SecBrain includes comprehensive testing strategies for maximum code quality and security:

```bash
cd secbrain

# Standard unit tests
python -m pytest tests/ -v

# Property-based tests with Hypothesis
python -m pytest tests/test_property_based.py -v

# Run with coverage
python -m pytest tests/ --cov=secbrain --cov-report=term-missing
```

For smart contract testing (Foundry):

```bash
# Quick fuzzing (32 runs)
FOUNDRY_PROFILE=quick forge test

# Standard fuzzing (256 runs)
forge test

# CI fuzzing (10,000 runs)
FOUNDRY_PROFILE=ci forge test

# Run invariant tests
forge test --match-contract Invariant -vvv
```

For advanced testing strategies including mutation testing and Echidna fuzzing, see:
- 📚 [Complete Testing Guide](../docs/TESTING-STRATEGIES.md)
- ⚡ [Quick Reference](../docs/TESTING-QUICK-REF.md)

## TODO

### High Priority

- [ ] Add unit tests for all agents and tools
- [ ] Implement real API key validation on startup
- [ ] Add retry logic with exponential backoff for API calls
- [ ] Create Docker container with pre-installed tools

### Medium Priority

- [ ] Deeper integration with LangGraph/AutoGen
- [ ] Browser automation tools (Playwright/Selenium)
- [ ] Burp Suite extension integration
- [ ] Fine-tuned prompts based on real usage data
- [ ] Multi-target orchestration
- [ ] Webhook notifications for findings

### Low Priority / Future

- [ ] Cloud deployment options (AWS Lambda, GCP Cloud Run)
- [ ] Web dashboard for monitoring runs
- [ ] Integration with bug bounty platforms (HackerOne, Bugcrowd APIs)
- [ ] Custom vulnerability template authoring
- [ ] Team collaboration features

## Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### For Beginners

- 📖 **Start here**: [Git Quick Start Guide](../docs/GIT_QUICK_START.md) - Learn the basics of Git and GitHub
- 📚 **Full guide**: [Contributing Guide](../CONTRIBUTING.md) - Detailed information about our workflow

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

**Note**: Type checking currently has many errors we're working to fix. Your PR won't be blocked by existing type errors, but please don't introduce new ones.

### Need Help?

- Check the [Contributing Guide](../CONTRIBUTING.md) for detailed instructions
- Open an issue if you have questions
- Join the discussion in existing PRs

## License

MIT
