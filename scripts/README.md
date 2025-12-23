# AI Engineer Analysis Scripts

This directory contains scripts that power the dynamic AI-Powered Engineering Agent workflow, as well as example scripts for running SecBrain.

## Overview

The AI engineer workflow has been transformed from static, cookie-cutter suggestions to dynamic, context-aware recommendations based on actual codebase analysis and cutting-edge security intelligence.

## Example Scripts

### `run_example.sh` (Bash)

**Purpose:** Example bash script demonstrating proper RPC URL configuration and SecBrain execution.

**Features:**
- Proper environment variable quoting
- Configuration validation
- Clear error messages
- Best practices for array expansion

**Usage:**
```bash
chmod +x scripts/run_example.sh
./scripts/run_example.sh
```

### `run_example.ps1` (PowerShell)

**Purpose:** Example PowerShell script demonstrating proper RPC URL configuration to avoid concatenation issues.

**Features:**
- Parameter-based configuration
- Proper quoting to prevent PowerShell misinterpretation
- Array splatting for correct argument passing
- Inline tips for common PowerShell pitfalls

**Usage:**
```powershell
.\scripts\run_example.ps1
.\scripts\run_example.ps1 -RpcUrl "https://ethereum.publicnode.com"
.\scripts\run_example.ps1 -BlockNumber 18500000
```

**Important PowerShell Notes:**
- Always quote RPC URLs: `$env:RPC_URL = "https://..."`
- Use arrays for command arguments to ensure proper quoting
- Prefer `scope.yaml` for multiple RPC URLs instead of environment variables

See [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) for more details on RPC configuration.

## AI Engineering Scripts

### 1. `ai_engineer_analysis.py`

**Purpose:** Performs deep analysis of the SecBrain codebase to identify improvement areas.

**Analyzes:**
- Recent commit patterns and active development areas
- Code patterns, anti-patterns, and technical debt
- TODO/FIXME markers
- Type annotation coverage
- Security-sensitive code patterns (subprocess, SQL, HTTP)
- Dependency health
- Test coverage and testing approaches
- CI/CD workflow maturity
- Solidity contract presence and testing

**Output:** JSON file with comprehensive codebase metrics and identified improvement areas.

**Usage:**
```bash
python scripts/ai_engineer_analysis.py > codebase_analysis.json
```

### 2. `security_intelligence.py`

**Purpose:** Gathers latest security intelligence and best practices.

**Provides:**
- Recent Python CVE patterns and security concerns
- DeFi exploit patterns from 2023-2024 (read-only reentrancy, oracle manipulation, etc.)
- Solidity best practices and gas optimization techniques
- Python 3.11+ security features (LiteralString, Self type, etc.)
- Advanced testing strategies (property-based testing, fuzzing, invariant testing)

**Output:** JSON file with categorized security intelligence.

**Usage:**
```bash
python scripts/security_intelligence.py > security_intel.json
```

### 3. `generate_recommendations.py`

**Purpose:** Generates context-aware recommendations based on analysis and intelligence.

**Features:**
- Dynamic recommendation generation based on actual codebase state
- Prioritization by risk and impact
- Detailed implementation steps and code examples
- Links to latest research and best practices
- Formats recommendations as GitHub issues

**Input:** Combined JSON from analysis and intelligence scripts.

**Output:** JSON file with recommendations and formatted GitHub issues.

**Usage:**
```bash
python -c "
import json
with open('codebase_analysis.json') as f:
    codebase = json.load(f)
with open('security_intel.json') as f:
    intel = json.load(f)

combined = {
    'timestamp': codebase['timestamp'],
    'codebase_analysis': codebase,
    'security_intel': intel
}

print(json.dumps(combined))
" | python scripts/generate_recommendations.py > recommendations.json
```

## How It Works

### Workflow Integration

The AI-Powered Engineering Agent workflow (`.github/workflows/ai-engineer.yml`) runs these scripts in sequence:

1. **Deep Codebase Analysis** - Analyzes the repository state
2. **Security Intelligence Gathering** - Collects latest security patterns
3. **Recommendation Generation** - Creates context-specific suggestions
4. **Issue Creation** - Posts recommendations as GitHub issues with:
   - Smart deduplication (checks for existing issues)
   - Update capability (updates issues older than 1 week)
   - Rich formatting with examples and references

### Example Recommendations

The system generates recommendations like:

- **Critical Priority:** Protection against latest DeFi exploits (read-only reentrancy, flash loan attacks)
- **High Priority:** Property-based testing implementation, Type safety enhancements
- **Medium Priority:** Technical debt reduction, Dependency security hardening
- **Low Priority:** Code refactoring in high-churn files

### Dynamic Behavior

Unlike static suggestions, these recommendations:

✅ **Adapt to codebase state** - Only suggest property-based testing if not already implemented
✅ **Respond to activity** - Prioritize areas with recent development
✅ **Consider context** - Solidity recommendations only if contracts exist
✅ **Track history** - Avoid duplicate issues, update stale ones
✅ **Include cutting-edge patterns** - Latest DeFi exploits, Python 3.11+ features

## Dependencies

All scripts use **Python standard library only** - no additional dependencies required!

## Development

To add new analysis capabilities:

1. Add analysis functions to `ai_engineer_analysis.py`
2. Update `improvement_areas` detection logic
3. Add corresponding recommendations in `generate_recommendations.py`

To add new security intelligence:

1. Add new patterns to `security_intelligence.py`
2. Update recommendation generation logic to utilize them

## Testing

Run the full pipeline locally:

```bash
# Run analysis
python scripts/ai_engineer_analysis.py 2>&1 | grep -v "^🔍\|^🚀" > codebase_analysis.json

# Gather intelligence
python scripts/security_intelligence.py 2>&1 | grep -v "^🔍\|^🚀" > security_intel.json

# Generate recommendations
python -c "
import json
with open('codebase_analysis.json') as f:
    codebase = json.load(f)
with open('security_intel.json') as f:
    intel = json.load(f)

combined = {
    'timestamp': codebase['timestamp'],
    'codebase_analysis': codebase,
    'security_intel': intel
}

print(json.dumps(combined))
" | python scripts/generate_recommendations.py > recommendations.json

# View results
cat recommendations.json | python -m json.tool
```

## Scheduled Execution

The workflow runs:
- **Weekly** on Mondays at 6 AM UTC (scheduled)
- **On-demand** via workflow_dispatch

## Future Enhancements

Potential improvements:
- Integration with actual LLM APIs (GPT-4, Claude) for more sophisticated analysis
- GitHub Advisory Database API integration for real CVE data
- Machine learning to track recommendation effectiveness
- Automated PR creation for low-risk improvements
- Historical trend analysis across runs
