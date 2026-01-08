# Dependency Management with Hash Verification

## Overview

This project uses **hash-verified dependencies** for supply chain security. All Python dependencies are pinned with SHA256 hashes to prevent supply chain attacks and ensure reproducible builds.

## Architecture

### Files

- **`secbrain/requirements.in`**: Human-readable list of direct dependencies
- **`secbrain/requirements.lock`**: Auto-generated file with all dependencies and their SHA256 hashes (hash-pinned)
- **`secbrain/requirements-hashed.txt`**: Alternative name for hash-verified requirements (kept for compatibility)
- **`requirements.txt`**: Root requirements file (generated from pyproject.toml for CI)
- **`secbrain/pyproject.toml`**: Project metadata and dependency specifications

### Workflow

```
requirements.in (manual)
    ↓ [pip-compile --generate-hashes]
requirements.lock (auto-generated with hashes)
    ↓ [pip install --require-hashes]
Production environment
```

## Usage

### Adding a New Dependency

1. Add the package to `secbrain/requirements.in`:
   ```
   new-package>=1.0.0
   ```

2. Run pip-compile to update the hashed requirements:
   ```bash
   cd secbrain
   pip-compile --generate-hashes --output-file=requirements.lock requirements.in
   ```

3. Commit both files:
   ```bash
   git add requirements.in requirements.lock
   git commit -m "Add new-package dependency"
   ```

### Updating Dependencies

To update all dependencies to their latest compatible versions:

```bash
cd secbrain
pip-compile --generate-hashes --upgrade --output-file=requirements.lock requirements.in
```

To update a specific package:

```bash
cd secbrain
pip-compile --generate-hashes --upgrade-package package-name --output-file=requirements.lock requirements.in
```

### Installing Dependencies

**Development (with hash verification):**
```bash
cd secbrain
pip install --require-hashes -r requirements.lock
```

**CI/CD (automated with hash verification):**
The workflows automatically use hash-verified requirements with `--require-hashes` flag.

## Security Benefits

### Hash Verification (🔴 High Priority - Implemented)

- **Supply Chain Attack Prevention**: Each package version is locked to specific SHA256 hashes
- **Tamper Detection**: pip will reject packages that don't match the expected hash
- **Reproducible Builds**: Same hashes guarantee identical dependencies across environments
- **Audit Trail**: Hash changes are visible in version control

### Example

```txt
# Without hash verification (vulnerable)
requests==2.32.5

# With hash verification (secure)
requests==2.32.5 \
    --hash=sha256:2462f94637a34fd532264295e186976db0f5d453d1cdd31473c85a6a161affb6 \
    --hash=sha256:dbba0bac56e100853db0ea71b82b4dfd5fe2bf6d3754a8893c3af500cec7d7cf
    # via -r requirements.in
```

### Installation with Hash Verification

When installing with `--require-hashes`, pip will:
1. Verify each package's hash against the hashes in requirements.lock
2. Reject installation if ANY package hash doesn't match
3. Prevent installation of packages without hashes
4. Ensure all dependencies (including transitive ones) are verified

## Integration with CI/CD

All CI workflows use hash-verified requirements:

- **`dependency-audit.yml`**: Daily vulnerability scanning
- **`sbom-generation.yml`**: Weekly SBOM generation with hash tracking
- **`security-scan.yml`**: Continuous security validation

## Tools

### pip-compile (from pip-tools)

- **Purpose**: Generate requirements.lock from requirements.in
- **Installation**: `pip install pip-tools`
- **Documentation**: https://pip-tools.readthedocs.io/

### GitHub Dependabot

- **Schedule**: Daily updates for security patches
- **Config**: `.github/dependabot.yml`
- **Auto-merge**: Configured for trusted patches (patch/minor updates)

## SBOM (Software Bill of Materials)

Hash-verified dependencies are tracked in multiple SBOM formats:

- **CycloneDX JSON**: Machine-readable format for security tools
- **CycloneDX XML**: Compatible with OWASP tools
- **SPDX JSON**: Compliance and legal standard

SBOMs are automatically generated on:
- Every push to main/develop
- Weekly schedule (Mondays at 2 AM UTC)
- Manual workflow dispatch

## Vulnerability Monitoring

Dependencies are scanned daily for vulnerabilities:

- **pip-audit**: CVE database scanning
- **Safety**: Known vulnerability detection
- **License compliance**: Automatic license compatibility checks
- **Vendor risk**: Deprecated package detection

Critical vulnerabilities trigger automatic GitHub issues.

## Best Practices

1. **Always use hash-verified requirements** in production with `--require-hashes` flag
2. **Review dependency updates** before merging Dependabot PRs
3. **Keep requirements.in minimal** - only list direct dependencies
4. **Run pip-compile** after changing requirements.in to regenerate requirements.lock
5. **Test updates** in development before production deployment
6. **Monitor security advisories** for critical dependencies
7. **Use `pip install --require-hashes -r requirements.lock`** to enforce hash verification

## Troubleshooting

### Hash mismatch error

If you see an error like:
```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE
```

**Solution**: Regenerate hashes with:
```bash
cd secbrain
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
```

### Installing packages without hashes fails

When using `--require-hashes`, ALL packages must have hashes. If you need to install 
additional packages (like dev tools), either:

1. Install them without the requirements file: `pip install package-name`
2. Add them to requirements.in and regenerate requirements.lock
3. Use a separate requirements file for dev tools without the `--require-hashes` flag

### Dependency conflict

If dependencies have incompatible version requirements:

1. Check pip-compile output for conflicts
2. Adjust version constraints in requirements.in
3. Consider using `--resolver=backtracking` if needed

## References

- [CISA SBOM Best Practices](https://www.cisa.gov/sbom)
- [SLSA Framework](https://slsa.dev/)
- [pip-tools Documentation](https://pip-tools.readthedocs.io/)
- [Python Package Security Guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)

## Compliance

This dependency management approach supports:

- ✅ Supply chain security (SLSA Level 1+)
- ✅ SBOM generation (NTIA minimum elements)
- ✅ License compliance tracking
- ✅ Vulnerability monitoring
- ✅ Audit trail for all changes
