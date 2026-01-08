# GitHub Copilot Instructions for SecBrain

## Project Overview

SecBrain is a multi-agent security bounty system with research integration, advisor models, and guarded tooling. It's a CLI-first Python project that automates bug bounty workflows using a coordinated team of AI agents for vulnerability research, exploit generation, and security analysis.

**Key Technologies:**
- Python 3.11+ (strict typing with mypy)
- Solidity/Foundry for smart contract testing
- Pytest for testing (coverage target: >60%)
- Ruff for linting
- AI agents with Perplexity and Gemini integration

## Code Style and Standards

### Python

**Style Guidelines:**
- Line length: 100 characters (enforced by ruff)
- Indentation: 4 spaces (not tabs)
- Type hints: Required for all function signatures (mypy strict mode)
- Docstrings: Use for public APIs and complex functions
- Import sorting: Use ruff/isort conventions (stdlib, third-party, local)

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `ContractAgent`, `ExploitPatternDB`)
- Functions/methods: `snake_case` (e.g., `generate_hypothesis`, `run_analysis`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private methods: `_leading_underscore` (e.g., `_internal_helper`)

**Code Quality:**
- Use f-strings for string formatting (not % or .format())
- Use pathlib.Path for file operations (not os.path)
- Prefer list/dict comprehensions over map/filter when readable
- Use context managers (with statements) for resources
- Avoid bare except clauses - catch specific exceptions
- No print statements in production code - use structured logging (structlog)

### Solidity

**Style Guidelines:**
- Line length: 100 characters
- Indentation: 4 spaces
- Follow latest Solidity style guide
- Use NatSpec documentation for all public functions

**Security Patterns:**
- Use latest security patterns from `docs/DEFI_SECURITY_QUICKSTART.md`
- Implement reentrancy guards where appropriate
- Add flash loan detection for DeFi protocols
- Use Chainlink oracles with TWAP fallbacks
- Implement comprehensive access control

## Testing Requirements

### Coverage Standards

- **Minimum coverage:** 60% (enforced in CI)
- **Target coverage:** 70% overall, 80%+ for critical modules
- **Test location:** All tests in `secbrain/tests/` directory

### Testing Best Practices

```python
# Use descriptive test names that explain what is being tested
def test_contract_agent_handles_missing_config_gracefully():
    """Verify ContractAgent raises ConfigurationError when config is None."""
    with pytest.raises(ConfigurationError):
        ContractAgent(config=None)

# Use fixtures from conftest.py for common setup
def test_exploit_pattern_db_with_fixture(exploit_db_fixture):
    """Test exploit pattern matching using shared fixture."""
    patterns = exploit_db_fixture.find_patterns("reentrancy")
    assert len(patterns) > 0

# Mark slow tests appropriately
@pytest.mark.slow
def test_full_vulnerability_scan():
    """Integration test for complete vulnerability scanning workflow."""
    # ... test implementation

# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_async_api_call():
    """Test asynchronous API interaction."""
    result = await make_api_call()
    assert result.status == "success"
```

### Running Tests

```bash
# Run all tests with coverage
cd secbrain && pytest tests/ -v --cov=secbrain --cov-report=term-missing

# Run specific test file
cd secbrain && pytest tests/test_contract_recon.py -v

# Run tests excluding slow tests
cd secbrain && pytest tests/ -v -m "not slow"

# Run with coverage report in HTML
cd secbrain && pytest tests/ --cov=secbrain --cov-report=html
```

## Build and Quality Checks

### Linting

```bash
# Run ruff linter (fast)
cd secbrain && ruff check .

# Auto-fix linting issues
cd secbrain && ruff check --fix .

# Check specific file
cd secbrain && ruff check secbrain/agents/contract_agent.py
```

### Type Checking

```bash
# Run mypy type checker (strict mode)
cd secbrain && mypy secbrain

# Check specific module
cd secbrain && mypy secbrain/agents/
```

### Running All Checks

```bash
# Pre-commit checks (run before committing)
cd secbrain && ruff check . && mypy secbrain && pytest tests/ -v --cov=secbrain
```

## Security Guidelines

### Security-First Development

1. **Input Validation:** Always validate and sanitize external inputs
2. **Rate Limiting:** Use `AdaptiveRateLimiter` for API calls
3. **Error Handling:** Never expose sensitive information in errors
4. **Secrets Management:** Use environment variables, never hardcode secrets
5. **Scope Enforcement:** Validate all user inputs against allowed scopes

### Secure Coding Patterns

```python
# BAD: Hardcoded secrets
api_key = "sk-1234567890abcdef"

# GOOD: Use environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    
    class Config:
        env_prefix = "SECBRAIN_"

# BAD: Unsafe string formatting
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# GOOD: Parameterized queries or proper validation
from pydantic import BaseModel, field_validator

class UserQuery(BaseModel):
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace('_', '').isalnum():
            raise ValueError('Invalid name format')
        return v

# BAD: Exposing internal errors
except Exception as e:
    return {"error": str(e)}

# GOOD: Structured error handling
except SpecificException as e:
    logger.error("operation_failed", error=str(e), context=context)
    return {"error": "Operation failed. Please contact support."}
```

### Smart Contract Security

- Always run security analysis before deployment
- Use provided DeFi security templates from `docs/testing-examples/`
- Implement comprehensive access control patterns
- Add reentrancy guards to state-changing functions
- Use SafeMath or Solidity 0.8+ overflow protection
- Validate oracle data with multiple sources
- Implement flash loan detection for DeFi applications

## Project Structure

```
secbrain/
├── .github/
│   ├── copilot/              # Copilot Space configuration and knowledge bases
│   ├── workflows/            # GitHub Actions CI/CD workflows
│   └── copilot-instructions.md  # This file
├── docs/                     # Documentation
├── secbrain/                 # Main Python package
│   ├── agents/              # AI agent implementations
│   ├── cli/                 # CLI interface (typer)
│   ├── config/              # Configuration models
│   ├── core/                # Core functionality
│   ├── insights/            # Analytics and insights
│   ├── models/              # Data models
│   ├── tools/               # Security tools and research integration (Perplexity)
│   ├── utils/               # Utility functions
│   ├── workflows/           # Workflow orchestration
│   └── tests/               # Test suite
├── scripts/                 # Utility scripts
├── targets/                 # Smart contract targets for analysis
└── pyproject.toml          # Python project configuration
```

## Common Development Tasks

### Adding a New Agent

1. Create agent class in `secbrain/agents/`
2. Inherit from appropriate base class
3. Implement required methods with type hints
4. Add comprehensive tests in `tests/`
5. Update documentation if it's a public API
6. Ensure >60% test coverage for the new module

### Adding a New CLI Command

1. Add command to `secbrain/cli/secbrain_cli.py`
2. Use Typer for argument parsing
3. Add help text and examples
4. Implement error handling
5. Add tests for the command
6. Update README.md if it's a major feature

### Adding a New Security Check

1. Implement check in appropriate module
2. Add to workflow in `secbrain/workflows/`
3. Create tests with both positive and negative cases
4. Document the check and its purpose
5. Update security documentation
6. Consider adding to Copilot Space knowledge base

## CI/CD Workflows

### Monitored Workflows

- **contract-audit-ci.yml**: Linting, type checking, security tests
- **sota-coverage-ci.yml**: State-of-the-art vulnerability coverage testing
- **python-testing.yml**: Python test suite
- **security-scan.yml**: Security vulnerability scanning
- **solidity-security.yml**: Smart contract security analysis

### Workflow Expectations

- All tests must pass before merge
- Coverage must be ≥60%
- No high/critical security vulnerabilities
- All linting and type checking must pass
- Execution time: <40s for contract-audit, <80s for SOTA coverage

## Working with the Repository

### Initial Setup

```bash
# Clone and setup
git clone https://github.com/blairmichaelg/secbrain.git
cd secbrain

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd secbrain
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Development Workflow

1. Work directly on `main` branch for most changes
2. Create feature branches only for experimental/breaking changes
3. Run pre-commit checks before committing
4. Write clear, descriptive commit messages
5. Ensure all tests pass locally before pushing

### Commit Message Format

```
<type>: <short description>

<optional longer description>

<optional footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
- `feat: Add flash loan detection to DeFi security template`
- `fix: Handle rate limit errors in Perplexity integration`
- `test: Add coverage for contract recon edge cases`
- `docs: Update DeFi security quickstart guide`

## AI Agent Integration

### Using Research Integration

```python
from secbrain.tools.perplexity_research import PerplexityResearch

# Use with rate limiting and caching
research = PerplexityResearch(
    api_key=settings.perplexity_api_key,
    cache_ttl=3600,  # 1 hour cache
    rate_limit=10,   # 10 requests per minute
)

results = await research.query(
    "recent DeFi exploits involving flash loans",
    timeframe_days=90
)
```

### Advisor Model Review

- Use Gemini model for critical decision reviews
- Implement human approval checkpoints for destructive operations
- Apply circuit breaker patterns for fault tolerance
- Use consensus engine for multi-agent coordination

## Reference Documentation

- **Main README:** `/README.md`
- **Contributing Guide:** `/CONTRIBUTING.md`
- **DeFi Security Guide:** `/docs/DEFI_SECURITY_QUICKSTART.md`
- **Exploit Protection:** `/docs/DEFI_EXPLOIT_PROTECTION_GUIDE.md`
- **Security Checklist:** `/docs/DEFI_SECURITY_CHECKLIST.md`
- **Copilot Space:** `/.github/copilot/README.md`

## Important Notes

- **Never commit secrets** - Use environment variables and .env files
- **Security first** - This is a security research tool, treat it seriously
- **Test coverage matters** - Aim for >60% minimum, >70% target
- **Type safety** - Use mypy strict mode, type hints are required
- **Structured logging** - Use structlog, not print statements
- **Rate limiting** - Always use rate limiters for external API calls
- **Error handling** - Catch specific exceptions, avoid bare except
- **Documentation** - Update docs when adding public APIs

## Getting Help

- Check existing documentation in `/docs`
- Review Copilot Space knowledge bases in `/.github/copilot`
- Look for similar patterns in existing code
- Run `secbrain --help` for CLI usage
- Open an issue with appropriate labels for questions
