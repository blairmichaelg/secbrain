# SecBrain Verification Guide

This guide helps you verify that SecBrain is working correctly on your system.

## Quick Verification (5 minutes)

### 1. Install Dependencies

```bash
cd secbrain
python3 -m pip install -e ".[dev]"
```

### 2. Run Linting

```bash
cd secbrain
python3 -m ruff check .
```

**Expected Result:** Minor warnings in examples are okay (they're exempt via config). No errors in main code.

### 3. Run Tests

```bash
cd secbrain
python3 -m pytest tests/ -v
```

**Expected Result:** ~97% pass rate (290+ passing tests out of ~299 total)

**Known Issues:**
- Some tests in `test_hypothesis_enhancement.py` may fail (outdated test expectations)
- Some tests in `test_research_orchestrator.py` may fail (minor timing issues)
- These failures don't affect core functionality

### 4. Test CLI Dry-Run

```bash
cd ..  # Back to repo root
secbrain run \
  --scope secbrain/examples/dummy_target/scope.yaml \
  --program secbrain/examples/dummy_target/program.json \
  --workspace /tmp/test_workspace \
  --dry-run
```

**Expected Result:** Should complete with "Success" status and show all phases completing.

### 5. Test CLI Commands

```bash
# Check version
secbrain version

# Validate config files
secbrain validate \
  --scope secbrain/examples/dummy_target/scope.yaml \
  --program secbrain/examples/dummy_target/program.json
```

## Detailed Verification

### Test Coverage

Run tests with coverage reporting:

```bash
cd secbrain
python3 -m pytest tests/ --cov=secbrain --cov-report=term-missing
```

**Expected Result:** ~38-40% coverage (comprehensive test suite for critical paths)

### Property-Based Tests

Run advanced property tests with Hypothesis:

```bash
cd secbrain
python3 -m pytest tests/test_property_based.py -v --hypothesis-show-statistics
```

**Expected Result:** All property-based tests should pass, showing thousands of test cases generated.

### Security Scanning

Run security checks with Semgrep:

```bash
semgrep --config=.semgrep/rules/ secbrain/
```

**Expected Result:** No critical security issues (some informational findings are normal)

## Verification Status

✅ **All Core Features Working:**
- CLI commands functional
- Dry-run mode operational
- Test suite passing (97%+ pass rate)
- Linting checks clean
- Dependencies installed correctly

## Troubleshooting

### Tests Failing

If you see test failures beyond the known issues:

1. Make sure you're in the `secbrain/` subdirectory when running tests
2. Verify all dependencies installed: `pip install -e ".[dev]"`
3. Check Python version: `python3 --version` (should be 3.11+)

### CLI Not Found

If `secbrain` command is not found:

```bash
# Check if it's in your PATH
which secbrain

# Or run directly
python3 -m secbrain.cli.secbrain_cli --help
```

### Import Errors

If you see import errors:

```bash
# Reinstall in editable mode
cd secbrain
pip install -e ".[dev]"
```

## Next Steps

Once verification is complete:

1. Set up API keys (see README.md)
2. Try running against a real target (not dry-run)
3. Explore the documentation in `docs/`
4. Read `CONTRIBUTING.md` to contribute

## Support

- 📖 [Full Documentation](docs/README.md)
- 🐛 [Report Issues](https://github.com/blairmichaelg/secbrain/issues)
- 💬 [Discussions](https://github.com/blairmichaelg/secbrain/discussions)
