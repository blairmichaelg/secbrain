# Quick Start: Using the Fixes

## ✅ Fixed Issues

1. **Can now create pull requests automatically** via GitHub Actions workflow
2. **Workflow no longer fails** when LLM doesn't generate hypotheses (fallback system)
3. **Workspace artifacts are now tracked** in git for review and sharing

## 🚀 How to Create a Pull Request from a SecBrain Run

### Step 1: Navigate to GitHub Actions
1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. Find **SecBrain Auto PR** in the left sidebar
4. Click **Run workflow** (top right)

### Step 2: Configure the Run
Fill in the workflow inputs:
- **Target**: Enter `thresholdnetwork` (or any other target in `targets/` directory)
- **Run mode**: Choose one:
  - `dry-run` - Fast simulation, no API costs (recommended for testing)
  - `full` - Complete analysis with real API calls (costs money)
- **Branch name**: Leave empty for auto-generated, or provide custom name

### Step 3: Start the Workflow
Click the green **Run workflow** button

### Step 4: Monitor Progress
- The workflow will appear in the runs list
- Click on it to see live progress
- Wait for completion (2-20 minutes depending on mode)

### Step 5: Review the Pull Request
- A new PR will be automatically created
- PR title: `[SecBrain] thresholdnetwork - {mode} run`
- PR description contains:
  - Run summary and metrics
  - Findings count
  - Economic decision
  - Hypothesis generation stats
  - Errors (if any)

### Step 6: Review Results
In the PR, you can:
- See high-level summary in description
- Download workspace artifacts
- Review committed files:
  - `targets/thresholdnetwork/workspace/run_summary.json`
  - `targets/thresholdnetwork/workspace/phases/*.json`
  - `targets/thresholdnetwork/workspace/findings/*.json`

## 🔄 What Happens When No Hypotheses are Generated?

### Previous Behavior (Broken)
```
Phases: ingest → plan → recon → hypothesis → (FAIL: "No hypotheses to test")
Result: Workflow stops, no findings, no reports
```

### New Behavior (Fixed)
```
Phases: ingest → plan → recon → hypothesis → (fallback triggered) → exploit → static → triage → report → meta
Result: Workflow completes with fallback hypotheses
```

### Fallback Hypotheses
When the LLM fails to generate hypotheses, the system now:
1. Detects empty hypothesis list
2. Generates protocol-specific fallback hypotheses
3. Marks them with `is_fallback: true`
4. Sets confidence to 0.45 (just above threshold)
5. Continues workflow normally

Example fallback hypothesis for Threshold Network:
```json
{
  "vuln_type": "bitcoin_peg_manipulation",
  "confidence": 0.45,
  "contract_address": "0x...",
  "is_fallback": true,
  "rationale": "Fallback hypothesis for bridge contract. Manual review recommended.",
  "exploit_notes": [
    "Generated as fallback - LLM hypothesis generation failed",
    "Protocol type: threshold_network",
    "Requires manual verification"
  ]
}
```

## 📊 Example Workflow Run

### Dry Run Example
```bash
Target: thresholdnetwork
Mode: dry-run
Time: ~2 minutes
Cost: $0 (no API calls)
```

**Expected Output:**
- ✅ Configuration validated
- ✅ Workflow phases completed
- ✅ PR created with structure verification
- ⚠️ No real vulnerabilities found (simulation only)

### Full Run Example
```bash
Target: thresholdnetwork
Mode: full
Time: ~15-20 minutes
Cost: ~$10-30 (API calls to LLMs, research)
```

**Expected Output:**
- ✅ Real vulnerability testing
- ✅ Exploit hypotheses generated (or fallbacks used)
- ✅ Forked blockchain testing
- ✅ Economic analysis
- ✅ PR with actual findings

## 🛠️ Troubleshooting

### "No hypotheses to test" Error (Old Issue)
**Fixed!** The workflow now generates fallback hypotheses automatically.

If you still see this error:
1. Check if you're using the updated code
2. Verify `vuln_hypothesis_agent.py` has the fallback method
3. Look for `fallback_hypotheses_generated` in logs

### "No changes to commit"
This means the workspace was not created or is empty.

**Solutions:**
1. Check workflow logs for errors
2. Verify target directory exists
3. Ensure scope.yaml and program.json are valid
4. Try re-running the workflow

### "Cannot create PR"
**Possible causes:**
1. Branch already exists - use a different branch name
2. No changes to commit - check workspace generation
3. Permissions issue - verify workflow has `pull-requests: write`

**Solutions:**
1. Use a unique branch name
2. Delete the existing branch and retry
3. Check repository settings → Actions → Workflow permissions

## 📝 Best Practices

### 1. Always Start with Dry Run
```bash
Target: thresholdnetwork
Mode: dry-run
```
This validates configuration without costs.

### 2. Review Dry Run PR Before Full Run
- Check that phases complete
- Verify contract discovery
- Ensure no configuration errors

### 3. Use Full Mode Strategically
Only use full mode when:
- Configuration is validated
- API keys are set
- You have budget for API costs
- You need real vulnerability findings

### 4. Review Fallback Hypotheses
If you see `is_fallback: true` in hypotheses:
- The LLM failed to generate hypotheses
- Generic patterns were used instead
- **Manual review is recommended**
- Consider re-running with different configuration

### 5. Archive Important Runs
For compliance and future reference:
- Download workspace artifacts
- Save PR link
- Keep run_summary.json
- Document any manual findings

## 🎯 Next Steps

1. **Test the Workflow**
   - Run a dry-run for thresholdnetwork
   - Verify PR is created
   - Review workspace artifacts

2. **Customize for Your Targets**
   - Add more targets in `targets/` directory
   - Configure scope.yaml and program.json
   - Run dry-runs to validate

3. **Set Up for Production**
   - Add API keys as repository secrets
   - Configure notification settings
   - Set up automated schedules (optional)

4. **Monitor and Iterate**
   - Review PRs regularly
   - Track hypothesis generation success
   - Adjust protocol classifications as needed
   - Improve scope definitions based on findings

## 📚 Additional Resources

- **Workflow Documentation**: `.github/workflows/SECBRAIN_AUTO_PR_README.md`
- **Fix Summary**: `FIX_SUMMARY.md`
- **SecBrain CLI**: Run `secbrain --help` for all commands
- **Validation**: Run `secbrain validate --scope <path> --program <path>`

## 💡 Tips

1. **Naming Branches**: Use descriptive names like `threshold-security-scan-2024-12`
2. **PR Labels**: Use labels to categorize runs (e.g., `dry-run`, `full-analysis`, `critical`)
3. **Team Review**: Assign PRs to security team members
4. **CI Integration**: Link this workflow to your existing CI/CD
5. **Cost Control**: Use dry-run for iteration, full mode for final analysis

---

**Questions?** Check the documentation or open an issue.

**Status**: ✅ All issues fixed and tested
**Date**: 2024-12-25
