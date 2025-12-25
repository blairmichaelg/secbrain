# SecBrain Auto PR Workflow

This workflow automatically creates pull requests from SecBrain security analysis runs.

## Overview

The SecBrain Auto PR workflow allows you to:
- Run SecBrain analysis on any configured target
- Automatically create a new branch with results
- Open a pull request with detailed findings and metrics
- Share analysis results with your team

## Usage

### Triggering the Workflow

1. Go to **Actions** → **SecBrain Auto PR** in your GitHub repository
2. Click **Run workflow**
3. Configure the run:
   - **Target**: Name of the target directory (e.g., `thresholdnetwork`)
   - **Run mode**: Choose `dry-run` or `full`
   - **Branch name**: (Optional) Custom branch name, or leave empty for auto-generated

### Run Modes

#### Dry Run (Default)
- Simulates the analysis without making real API calls
- Fast and free
- Good for testing configuration
- No actual vulnerability testing

```bash
# Example: dry-run mode
Target: thresholdnetwork
Run mode: dry-run
```

#### Full Mode
- Performs complete security analysis
- Makes real API calls to LLMs and research services
- Tests actual exploit hypotheses
- **Incurs API costs** (estimated $10-30 per run)

```bash
# Example: full mode
Target: thresholdnetwork
Run mode: full
```

## What It Does

1. **Validation**: Validates scope.yaml and program.json configuration
2. **Branch Creation**: Creates a new branch with timestamp
3. **SecBrain Run**: Executes the security analysis workflow
4. **Insights Generation**: Creates HTML/JSON/Markdown reports
5. **Commit**: Commits workspace artifacts to the branch
6. **Pull Request**: Opens a PR with detailed summary
7. **Artifacts**: Uploads workspace for manual review

## Pull Request Contents

The automatically created PR includes:

- **Run Summary**: ID, mode, duration, phases completed
- **Findings**: Count of security issues discovered
- **Economic Analysis**: Profit potential and decision metrics
- **Metrics**: Hypothesis generation, attempt statistics
- **Errors**: Any issues encountered during the run
- **Artifacts**: Full workspace available for download

## Workspace Structure

After a run, the following files are created in `targets/{target}/workspace/`:

```
workspace/
├── run_summary.json          # High-level run results (committed)
├── phases/                   # Per-phase outputs (committed)
│   ├── ingest.json
│   ├── plan.json
│   ├── recon.json
│   ├── hypothesis.json
│   ├── exploit.json
│   ├── static.json
│   ├── triage.json
│   ├── report.json
│   └── meta.json
├── findings/                 # Security findings (committed)
│   └── *.json
├── insights/                 # Insights reports (committed)
│   ├── report.html
│   ├── report.json
│   ├── report.md
│   └── report.csv
└── logs/                     # Detailed logs (ignored by git)
    └── *.log
```

## Requirements

### Target Directory Setup

Each target must have:
- `scope.yaml` - Defines the attack surface (contracts, domains, etc.)
- `program.json` - Bug bounty program details and rules

Example:
```
targets/
└── thresholdnetwork/
    ├── scope.yaml
    ├── program.json
    └── workspace/          # Created by workflow
```

### API Keys (Full Mode Only)

For full analysis mode, set these repository secrets:
- `PERPLEXITY_API_KEY` - For research queries
- `GOOGLE_API_KEY` - For Gemini advisor
- `TOGETHER_API_KEY` or `OPENROUTER_API_KEY` - For worker model

## Reviewing Results

### In the Pull Request
- Check the PR description for high-level summary
- Review metrics and economic decision
- Look for any errors or warnings

### In Artifacts
1. Go to the workflow run
2. Download the `secbrain-workspace-{target}` artifact
3. Extract and review detailed phase outputs
4. Open `insights/report.html` in a browser

### In the Branch
- Clone the branch locally for detailed analysis
- Review `phases/` JSON files for raw data
- Examine `findings/` for discovered vulnerabilities

## Examples

### Example 1: Test Configuration (Dry Run)
```
Target: thresholdnetwork
Run mode: dry-run
Branch name: (leave empty)
```

This will:
- Validate Threshold Network configuration
- Run simulation without API costs
- Create PR with workflow structure verification

### Example 2: Full Analysis Run
```
Target: thresholdnetwork
Run mode: full
Branch name: threshold-full-analysis-2024
```

This will:
- Perform complete security analysis
- Generate real exploit hypotheses
- Test vulnerabilities on forked blockchain
- Create PR with actual findings and profit analysis

## Troubleshooting

### "Target directory not found"
- Ensure the target name matches the directory in `targets/`
- Check spelling and case sensitivity

### "No changes to commit"
- The run completed but generated no new artifacts
- Check workflow logs for errors
- May indicate configuration or API issues

### "API keys not set"
- Only applies to full mode
- Set required secrets in repository settings
- Dry run mode doesn't require API keys

### "No hypotheses generated"
- The workflow now includes fallback hypothesis generation
- Check if fallback hypotheses are being used (marked with `is_fallback: true`)
- Review contract metadata and classification

## Best Practices

1. **Start with Dry Run**: Always test configuration with dry-run first
2. **Review Before Merge**: Don't auto-merge PRs - review findings carefully
3. **Monitor Costs**: Full runs consume API credits - budget accordingly
4. **Label PRs**: Use labels to track dry-run vs full analysis
5. **Archive Results**: Keep workspace artifacts for compliance and future reference

## Integration with Other Workflows

This workflow can be triggered by other workflows using:

```yaml
- name: Trigger SecBrain Analysis
  uses: actions/github-script@v8
  with:
    script: |
      await github.rest.actions.createWorkflowDispatch({
        owner: context.repo.owner,
        repo: context.repo.repo,
        workflow_id: 'secbrain-auto-pr.yml',
        ref: 'main',
        inputs: {
          target: 'thresholdnetwork',
          run_mode: 'dry-run'
        }
      });
```

## Support

For issues or questions:
1. Check the workflow run logs
2. Review the SecBrain documentation
3. Open an issue on the repository

---

*Last updated: 2024-12-25*
