# Automated Agent Suite - Quick Reference

## 🚀 NEW: Comprehensive Security Analysis

**Analyze ANY repository with 12+ security tools:**

```bash
# Quick scan (5-15 min)
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/owner/repo \
  -f analysis_depth=quick

# Standard analysis (30-60 min) - RECOMMENDED
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/owner/repo \
  -f target_type=mixed \
  -f analysis_depth=standard \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true

# Deep audit (2-4 hours)
gh workflow run comprehensive-security-analysis.yml \
  -f target_repo=https://github.com/owner/repo \
  -f analysis_depth=deep \
  -f enable_ai_analysis=true \
  -f enable_fuzzing=true
```

**See:** [Quick Reference](COMPREHENSIVE_SECURITY_ANALYSIS_QUICKREF.md) | [Examples](COMPREHENSIVE_SECURITY_ANALYSIS_EXAMPLES.md) | [Full Docs](.github/workflows/COMPREHENSIVE_SECURITY_ANALYSIS_README.md)

---

## Daily Workflows

### Morning Security Review (After 2-4 AM UTC)
1. Check GitHub Issues for new security findings
2. Review HIGH/CRITICAL severity issues
3. Plan remediation for urgent items

### On Every PR
- Code quality checks run automatically
- Address linting and type checking errors
- Review PR comments from quality analysis

## Weekly Workflows

### Monday Morning (After 6 AM UTC)
- Review AI Engineer suggestions
- Prioritize enhancement issues
- Add selected items to sprint backlog

### Sunday Evening/Monday Morning (After 1 AM UTC)
- Review comprehensive audit report
- Check trend analysis vs previous weeks
- Update security metrics dashboard

## Tool Cheat Sheet

### Python Security
```bash
# Run all security checks locally
cd secbrain
bandit -r secbrain/ -ll
safety check
pip-audit
semgrep --config=auto secbrain/
```

### Python Quality
```bash
# Format code
black secbrain/

# Fix auto-fixable issues
ruff check --fix secbrain/

# Type checking
mypy secbrain/

# Full quality check
pylint secbrain/
radon cc secbrain/ -a
vulture secbrain/ --min-confidence 80
```

### Solidity Security
```bash
# In exploit attempt directory
cd targets/originprotocol/exploit_attempts/hyp-xxx/attempt-1/

# Run Slither
slither .

# Run Mythril (on specific file)
myth analyze src/Exploit.sol

# Run Solhint
solhint src/**/*.sol

# Format with Prettier
prettier --write src/**/*.sol
```

### Pre-commit Hooks
```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run mypy --all-files

# Update hooks
pre-commit autoupdate
```

## Issue Label Guide

### Priority
- `critical-severity`: Fix immediately, blocks deployment
- `high-severity`: Fix in current sprint
- `medium-severity`: Plan for next sprint
- `low-severity`: Backlog item

### Type
- `security`: Security vulnerability or weakness
- `quality`: Code quality improvement
- `dependencies`: Dependency update or vulnerability
- `ai-suggestion`: AI-generated improvement idea
- `automated-scan`: Created by automation

### Language
- `python`: Python code
- `solidity`: Solidity smart contracts
- `github-actions`: CI/CD workflows

## Workflow Triggers

### Manual Triggers
All workflows support manual triggering via GitHub UI:
1. Go to Actions tab
2. Select workflow
3. Click "Run workflow"
4. Select branch
5. Click green "Run workflow" button

### Scheduled Triggers
- **2 AM UTC**: Daily Python security scan
- **3 AM UTC**: Daily Solidity security scan
- **4 AM UTC**: Daily dependency audit
- **1 AM UTC Sunday**: Weekly comprehensive audit
- **6 AM UTC Monday**: Weekly AI suggestions

## Common Commands

### Update Dependencies
```bash
# Update Python dependencies
cd secbrain
pip-compile --upgrade pyproject.toml
pip install -r requirements.lock

# Check for vulnerabilities
safety check
pip-audit
```

### Run Tests
```bash
cd secbrain
pytest tests/ -v --cov=secbrain
```

### Check Coverage
```bash
cd secbrain
pytest --cov=secbrain --cov-report=html
# Open htmlcov/index.html
```

### Generate SBOM
```bash
cd secbrain
pip-audit --format cyclonedx-json --output sbom.json
```

## Emergency Procedures

### Critical Vulnerability Found
1. **Assess**: Determine impact and exploitability
2. **Isolate**: Disable affected features if possible
3. **Fix**: Implement and test fix
4. **Verify**: Re-run security scans
5. **Deploy**: Fast-track through review
6. **Document**: Update security log

### Build/Test Failure
1. Check workflow logs in Actions tab
2. Download artifacts for detailed analysis
3. Reproduce locally using same commands
4. Fix and re-run tests
5. Commit and push fix

### False Positives
1. Verify it's truly a false positive
2. Document why it's safe
3. Add exclusion to tool config
4. Add comment in code if needed
5. Update issue with explanation

## Configuration File Locations

```
.
├── .github/
│   ├── workflows/           # All workflow definitions
│   └── dependabot.yml       # Dependency update config
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .secrets.baseline        # Secret detection baseline
├── .solhint.json           # Solidity linter config
├── foundry.toml            # Foundry/Forge config
├── slither.config.json     # Slither analyzer config
└── secbrain/
    └── pyproject.toml       # Python tool configs
```

## Useful Links

### GitHub Actions
- [Workflow runs](https://github.com/blairmichaelg/secbrain/actions)
- [Security tab](https://github.com/blairmichaelg/secbrain/security)
- [Dependabot](https://github.com/blairmichaelg/secbrain/security/dependabot)

### Documentation
- [Full Documentation](secbrain/docs/automated-agents.md)
- [Architecture](secbrain/docs/architecture-updated.md)
- [Workflows](secbrain/docs/workflows.md)
- [Threat Model](secbrain/docs/threat_model.md)

### Tool Docs
- [Bandit](https://bandit.readthedocs.io/)
- [Slither](https://github.com/crytic/slither)
- [Ruff](https://docs.astral.sh/ruff/)
- [MyPy](https://mypy.readthedocs.io/)
- [Pre-commit](https://pre-commit.com/)

## Metrics to Track

### Security Metrics
- Open security issues by severity
- Mean time to remediation
- Dependencies with known vulnerabilities
- Security scan pass rate

### Quality Metrics
- Code coverage percentage
- Type hint coverage
- Average cyclomatic complexity
- Linting error count

### Automation Metrics
- Workflow success rate
- Average workflow duration
- Issues created vs resolved
- Dependabot PR merge rate

## Tips & Tricks

### Speed Up Local Development
```bash
# Skip slow hooks for quick commits
SKIP=mypy,bandit git commit -m "WIP: quick fix"

# Run only formatting
pre-commit run black --all-files

# Run tests in parallel
pytest -n auto
```

### Debug Workflow Issues
```bash
# Download workflow artifacts
gh run download <run-id>

# View workflow logs
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id> --failed
```

### Customize for Your Project
1. Edit `.pre-commit-config.yaml` to add/remove hooks
2. Update `secbrain/pyproject.toml` to adjust tool settings
3. Modify workflow schedules in `.github/workflows/*.yml`
4. Add custom security rules to Semgrep/Slither configs

## Support

For issues with automated agents:
1. Check workflow logs for error messages
2. Review tool documentation
3. Create issue with `automation` label
4. Tag with specific tool name

## Version Info

- **Pre-commit framework**: v3.x
- **Python**: 3.11+
- **Solidity**: 0.8.x
- **Foundry**: Latest nightly
- **Node.js**: 20.x
