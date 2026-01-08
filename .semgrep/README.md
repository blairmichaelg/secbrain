# Semgrep Custom Security Rules

This directory contains custom Semgrep rules for detecting security vulnerabilities in SecBrain's codebase.

## Rules Overview

### Python Security Rules

#### 1. Subprocess Injection (`subprocess-injection.yml`)
- **subprocess-shell-injection**: Detects `shell=True` usage that can lead to command injection
- **unquoted-subprocess-args**: Identifies dynamic subprocess arguments that should use `shlex.quote()`
- **subprocess-with-user-input**: Catches subprocess calls with user-controlled input

#### 2. SQL Injection (`sql-injection.yml`)
- **sql-injection-format-string**: Detects SQL queries using string formatting
- **sql-injection-executemany**: Identifies unsafe `executemany()` usage
- **sql-injection-executescript**: Catches unsafe `executescript()` with dynamic content
- **sqlalchemy-text-with-format**: Detects unsafe SQLAlchemy text() queries
- **raw-sql-query-with-format**: Identifies raw SQL with string formatting

#### 3. Command Injection (`command-injection.yml`)
- **os-system-with-user-input**: Detects unsafe `os.system()` calls
- **os-popen-injection**: Identifies unsafe `os.popen()` usage
- **eval-with-user-input**: Catches dangerous `eval()` usage
- **exec-with-user-input**: Detects dangerous `exec()` usage
- **compile-with-user-input**: Identifies risky `compile()` usage
- **pickle-load-untrusted**: Warns about deserializing untrusted pickle data

#### 4. General Security (`general-security.yml`)
- **hardcoded-password**: Detects hardcoded credentials
- **insecure-hash-function**: Identifies use of MD5/SHA1
- **insecure-random**: Detects use of insecure random module
- **yaml-unsafe-load**: Catches unsafe YAML loading
- **path-traversal-open**: Identifies potential path traversal vulnerabilities
- **request-without-timeout**: Detects HTTP requests without timeouts
- **assert-used-for-validation**: Warns about using assert for validation
- **flask-debug-enabled**: Detects Flask debug mode in production
- **jwt-none-algorithm**: Identifies insecure JWT verification
- **xml-external-entity**: Detects XXE vulnerabilities

### Solidity Security Rules

#### 5. Solidity Security (`solidity-security.yml`)
- **solidity-reentrancy-external-call**: Detects potential reentrancy vulnerabilities
- **solidity-unchecked-low-level-call**: Identifies unchecked low-level calls
- **solidity-tx-origin-auth**: Catches dangerous tx.origin usage
- **solidity-selfdestruct-usage**: Warns about selfdestruct/suicide usage and access control
- **solidity-weak-randomness**: Identifies weak randomness sources
- **solidity-old-version**: Detects Solidity versions < 0.8 without overflow protection
- **solidity-delegatecall-usage**: Catches delegatecall usage requiring review
- **solidity-ether-transfer**: Detects Ether transfers needing access control checks

## Usage

### Running Semgrep with Custom Rules

Run all custom rules:
```bash
semgrep --config .semgrep/rules/ secbrain/
```

Run specific rule files:
```bash
# Python subprocess rules
semgrep --config .semgrep/rules/subprocess-injection.yml secbrain/

# SQL injection rules
semgrep --config .semgrep/rules/sql-injection.yml secbrain/

# Solidity security rules
semgrep --config .semgrep/rules/solidity-security.yml targets/
```

Run with JSON output:
```bash
semgrep --config .semgrep/rules/ --json --output results.json secbrain/
```

Run with auto-fix (where available):
```bash
semgrep --config .semgrep/rules/ --autofix secbrain/
```

### CI/CD Integration

These rules are automatically run by the GitHub Actions workflow in `.github/workflows/security-scan.yml`.

The workflow:
1. Runs on push to main/develop branches
2. Runs daily at 2 AM UTC
3. Can be triggered manually via workflow_dispatch
4. Uploads results as artifacts
5. Creates GitHub issues for HIGH severity findings

### Adding New Rules

1. Create a new YAML file in `.semgrep/rules/`
2. Follow the existing rule format:
   ```yaml
   rules:
     - id: rule-unique-id
       pattern: code pattern to match
       message: Description of the vulnerability
       severity: ERROR|WARNING|INFO
       languages: [python|solidity]
       metadata:
         category: security
         cwe: "CWE-XXX: Description"
         owasp: "A0X:2021 - Category"
         confidence: HIGH|MEDIUM|LOW
         likelihood: HIGH|MEDIUM|LOW
         impact: CRITICAL|HIGH|MEDIUM|LOW
   ```
3. Test the rule locally before committing
4. Update this README with the new rule documentation

## Severity Levels

- **ERROR**: Critical security issues that should block deployment
- **WARNING**: Important security concerns that should be reviewed
- **INFO**: Security best practices and recommendations

## References

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Semgrep Rule Syntax](https://semgrep.dev/docs/writing-rules/rule-syntax/)
- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CWE List](https://cwe.mitre.org/)

## Testing Rules

### Manual Testing

To test rules manually, create sample vulnerable code files and run Semgrep:

```bash
# Create test files in /tmp
mkdir -p /tmp/semgrep-test

# Run Semgrep on test files
semgrep --config .semgrep/rules/ /tmp/semgrep-test/
```

Example test files:

**Python Test (test_subprocess.py):**
```python
import subprocess

# Should trigger subprocess-shell-injection
subprocess.run("ls -la", shell=True)

# Should trigger unquoted-subprocess-args  
user_input = input()
subprocess.run(f"ls {user_input}")

# Safe - should not trigger
subprocess.run(["ls", "-la"])
```

**Solidity Test (test_contract.sol):**
```solidity
pragma solidity ^0.8.0;

contract Test {
    // Should trigger solidity-tx-origin-auth
    function bad() public {
        require(tx.origin == msg.sender);
    }
    
    // Should trigger solidity-unchecked-low-level-call
    function badCall(address target) public {
        target.call("");
    }
}
```

### Integration Testing

Rules are automatically tested in CI/CD via the `security-scan.yml` workflow, which runs on:
- Every push to main/develop branches
- Daily at 2 AM UTC
- Manual workflow dispatch

## Contributing

When adding new rules:
1. Test thoroughly with both positive and negative cases
2. Include clear fix guidance in the message
3. Add appropriate metadata (CWE, OWASP, severity)
4. Update this README
5. Consider adding test cases in the test suite
6. Run `semgrep --validate --config .semgrep/rules/` to check syntax
