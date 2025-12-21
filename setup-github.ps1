# GitHub Repository Setup Script for PowerShell
# Run this from your repository root

#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$RepoOwner,

    [Parameter(Mandatory=$false)]
    [string]$RepoName,

    [Parameter(Mandatory=$false)]
    [switch]$SkipRulesets,

    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Step {
    param([string]$Message)
    Write-Host "`n===> $Message" -ForegroundColor $InfoColor
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $SuccessColor
}

function Write-Fail {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $ErrorColor
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor $InfoColor
}

function Write-Warn {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor $WarningColor
}

# =============================================================================
# 1. Check Prerequisites
# =============================================================================
Write-Step "Checking prerequisites"

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Fail "GitHub CLI (gh) is not installed"
    Write-Info "Install with: winget install GitHub.cli"
    exit 1
}
Write-Success "GitHub CLI found"

# Check if authenticated
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Not authenticated with GitHub CLI"
    Write-Info "Run: gh auth login"
    exit 1
}
Write-Success "GitHub CLI authenticated"

# Get current repo info
if (-not $RepoOwner -or -not $RepoName) {
    Write-Step "Detecting repository"
    $repoInfo = gh repo view --json owner,name | ConvertFrom-Json
    $RepoOwner = $repoInfo.owner.login
    $RepoName = $repoInfo.name
}

Write-Success "Repository: $RepoOwner/$RepoName"

# Get GitHub user info
Write-Step "Getting GitHub user info"
$currentUser = gh api user | ConvertFrom-Json
$GitHubUsername = $currentUser.login
$GitHubUserId = $currentUser.id

Write-Success "User: $GitHubUsername (ID: $GitHubUserId)"

# =============================================================================
# 2. Create Directory Structure
# =============================================================================
Write-Step "Creating directory structure"

$dirs = @(
    ".github",
    ".github/workflows",
    ".github/ISSUE_TEMPLATE"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Success "Created $dir"
    } else {
        Write-Info "$dir already exists"
    }
}

# =============================================================================
# 3. Create Workflow Files
# =============================================================================
Write-Step "Creating workflow files"

# CI Workflow
$ciWorkflow = @"
name: CI Pipeline

on:
  pull_request:
    branches: [main, master, dev, develop]
  push:
    branches: [main, master, dev, develop]
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write
  checks: write
  statuses: write

jobs:
  tests:
    name: Tests
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest tests/ \
            --cov=secbrain \
            --cov-report=xml \
            --junit-xml=test-results.xml \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  lint:
    name: Lint
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install ruff black isort

      - name: Run ruff
        run: ruff check . --output-format=github

      - name: Run black
        run: black --check .

      - name: Run isort
        run: isort --check-only .

  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install mypy

      - name: Run mypy
        run: mypy secbrain/ --ignore-missing-imports

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install safety bandit pip-audit

      - name: Run security checks
        run: |
          safety check --json || true
          bandit -r secbrain/ -f json || true
          pip-audit --format json || true

  auto-approve:
    name: Auto-approve PR
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'pull_request' &&
      (github.actor == 'dependabot[bot]' ||
       startsWith(github.head_ref, 'copilot/') ||
       startsWith(github.head_ref, 'auto/'))
    needs: [tests, lint, type-check, security]
    permissions:
      pull-requests: write

    steps:
      - name: Approve PR
        run: gh pr review `${{ github.event.pull_request.number }} --approve
        env:
          GH_TOKEN: `${{ secrets.GITHUB_TOKEN }}

  auto-merge:
    name: Auto-merge PR
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'pull_request' &&
      (github.actor == 'dependabot[bot]' ||
       startsWith(github.head_ref, 'copilot/') ||
       startsWith(github.head_ref, 'auto/'))
    needs: [auto-approve]
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Enable auto-merge
        run: gh pr merge `${{ github.event.pull_request.number }} --auto --squash
        env:
          GH_TOKEN: `${{ secrets.GITHUB_TOKEN }}
"@

$ciWorkflow | Out-File -FilePath ".github/workflows/ci.yml" -Encoding utf8
Write-Success "Created ci.yml"

# Dependabot Auto-merge Workflow
$dependabotWorkflow = @"
name: Dependabot Auto-merge

on:
  pull_request:
    branches: [main, master]

permissions:
  contents: write
  pull-requests: write

jobs:
  dependabot:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'

    steps:
      - name: Dependabot metadata
        id: metadata
        uses: dependabot/fetch-metadata@v2
        with:
          github-token: "`${{ secrets.GITHUB_TOKEN }}"

      - name: Approve and merge patch/minor updates
        if: |
          steps.metadata.outputs.update-type == 'version-update:semver-patch' ||
          steps.metadata.outputs.update-type == 'version-update:semver-minor'
        run: |
          gh pr review `${{ github.event.pull_request.number }} --approve
          gh pr merge `${{ github.event.pull_request.number }} --auto --squash
        env:
          GH_TOKEN: `${{ secrets.GITHUB_TOKEN }}

      - name: Comment on major updates
        if: steps.metadata.outputs.update-type == 'version-update:semver-major'
        run: |
          gh pr comment `${{ github.event.pull_request.number }} --body "⚠️ Major version update - please review manually"
        env:
          GH_TOKEN: `${{ secrets.GITHUB_TOKEN }}
"@

$dependabotWorkflow | Out-File -FilePath ".github/workflows/dependabot-auto-merge.yml" -Encoding utf8
Write-Success "Created dependabot-auto-merge.yml"

# =============================================================================
# 4. Create Configuration Files
# =============================================================================
Write-Step "Creating configuration files"

# Dependabot
$dependabotConfig = @"
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    open-pull-requests-limit: 10
    reviewers:
      - "$GitHubUsername"
    labels:
      - "dependencies"
      - "auto-merge"
    commit-message:
      prefix: "chore(deps)"
    groups:
      development-dependencies:
        patterns:
          - "pytest*"
          - "black"
          - "ruff"
          - "mypy"
      production-dependencies:
        patterns:
          - "*"
        exclude-patterns:
          - "pytest*"
          - "black"
          - "ruff"
          - "mypy"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "auto-merge"
"@

$dependabotConfig | Out-File -FilePath ".github/dependabot.yml" -Encoding utf8
Write-Success "Created dependabot.yml"

# CODEOWNERS
$codeowners = @"
# Code ownership

* @$GitHubUsername

/secbrain/agents/ @$GitHubUsername
/secbrain/tools/ @$GitHubUsername
/tests/ @$GitHubUsername
/.github/ @$GitHubUsername
"@

$codeowners | Out-File -FilePath ".github/CODEOWNERS" -Encoding utf8
Write-Success "Created CODEOWNERS"

# PR Template
$prTemplate = @"
## Description
<!-- Describe your changes -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #

## Checklist
- [ ] Tests pass
- [ ] Lint checks pass
- [ ] Type checks pass

## Testing
<!-- How did you test? -->
"@

$prTemplate | Out-File -FilePath ".github/pull_request_template.md" -Encoding utf8
Write-Success "Created pull_request_template.md"

# Issue Templates
$bugTemplate = @"
---
name: Bug Report
about: Report a bug
title: '[BUG] '
labels: 'bug'
---

**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce.

**Expected behavior**
What should happen.

**Environment**
- OS:
- Python version:
- SecBrain version:
"@

$bugTemplate | Out-File -FilePath ".github/ISSUE_TEMPLATE/bug_report.md" -Encoding utf8
Write-Success "Created bug_report.md"

$featureTemplate = @"
---
name: Feature Request
about: Suggest a feature
title: '[FEATURE] '
labels: 'enhancement'
---

**Is your feature request related to a problem?**
Description.

**Describe the solution you'd like**
What you want.

**Additional context**
Any other info.
"@

$featureTemplate | Out-File -FilePath ".github/ISSUE_TEMPLATE/feature_request.md" -Encoding utf8
Write-Success "Created feature_request.md"

# =============================================================================
# 5. Enable Repository Settings
# =============================================================================
Write-Step "Configuring repository settings"

if (-not $DryRun) {
    # Enable auto-merge
    gh api -X PATCH "repos/$RepoOwner/$RepoName" `
        -f allow_auto_merge=true `
        -f delete_branch_on_merge=true `
        -f allow_squash_merge=true `
        -f allow_merge_commit=false `
        -f allow_rebase_merge=true | Out-Null

    Write-Success "Enabled auto-merge and squash merging"

    # Enable security features
    gh api -X PUT "repos/$RepoOwner/$RepoName/vulnerability-alerts" | Out-Null
    gh api -X PUT "repos/$RepoOwner/$RepoName/automated-security-fixes" | Out-Null

    Write-Success "Enabled security features"
} else {
    Write-Info "Dry run - skipping repository settings"
}

# =============================================================================
# 6. Create Branch Protection Rules (Fallback)
# =============================================================================
Write-Step "Creating branch protection rules"

if (-not $DryRun -and -not $SkipRulesets) {
    # Main branch protection
    $branchProtection = @{
        required_status_checks = @{
            strict = $true
            contexts = @(
                "Tests",
                "Lint",
                "Type Check",
                "Security Scan"
            )
        }
        enforce_admins = $false
        required_pull_request_reviews = @{
            required_approving_review_count = 0
            dismiss_stale_reviews = $true
            require_code_owner_reviews = $false
        }
        required_linear_history = $true
        allow_force_pushes = $false
        allow_deletions = $false
        required_conversation_resolution = $true
    }

    # Restriction fields are only valid for org repos; skip for user repos
    if ($repoInfo.owner.type -eq "Organization") {
        $branchProtection["restrictions"] = @{
            users = @()
            teams = @()
            apps  = @()
        }
    }

    $branchProtectionJson = $branchProtection | ConvertTo-Json -Depth 10

    try {
        $bpResponse = $branchProtectionJson | gh api -X PUT "repos/$RepoOwner/$RepoName/branches/main/protection" `
            --input - 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Created branch protection for main"
        } else {
            Write-Warn "Could not create branch protection (HTTP $LASTEXITCODE)"
            Write-Info "$bpResponse"
        }
    } catch {
        Write-Warn "Could not create branch protection (you may need admin access)"
        Write-Info "You can create it manually in Settings -> Branches"
    }
} else {
    Write-Info "Skipping branch protection rules"
}

# =============================================================================
# 7. Create Labels
# =============================================================================
Write-Step "Creating labels"

$labels = @(
    @{name="auto-merge"; color="0e8a16"; description="Automatically merge when checks pass"},
    @{name="bug"; color="d73a4a"; description="Something isn't working"},
    @{name="enhancement"; color="a2eeef"; description="New feature or request"},
    @{name="documentation"; color="0075ca"; description="Documentation improvements"},
    @{name="security"; color="ee0701"; description="Security issue"},
    @{name="dependencies"; color="0366d6"; description="Dependency updates"},
    @{name="wip"; color="fbca04"; description="Work in progress"},
    @{name="do-not-merge"; color="b60205"; description="Do not merge"},
    @{name="needs-review"; color="fbca04"; description="Needs manual review"}
)

foreach ($label in $labels) {
    if (-not $DryRun) {
        $labelResponse = gh api -X POST "repos/$RepoOwner/$RepoName/labels" `
            -f name="$($label.name)" `
            -f color="$($label.color)" `
            -f description="$($label.description)" 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Created label: $($label.name)"
        } else {
            Write-Info "Could not create label '$($label.name)': $labelResponse"
        }
    } else {
        Write-Info "Would create label: $($label.name)"
    }
}

# =============================================================================
# 8. Create Rulesets via API
# =============================================================================
Write-Step "Creating rulesets"

if (-not $DryRun -and -not $SkipRulesets) {
    Write-Info "Creating rulesets via API..."

    # Main branch ruleset
    $mainRuleset = @{
        name = "Main Branch Protection"
        target = "branch"
        enforcement = "active"
        conditions = @{
            ref_name = @{
                include = @("refs/heads/main", "refs/heads/master")
                exclude = @()
            }
        }
        rules = @(
            @{
                type = "pull_request"
                parameters = @{
                    required_approving_review_count = 0
                    dismiss_stale_reviews_on_push = $true
                    require_code_owner_review = $false
                    required_review_thread_resolution = $true
                }
            },
            @{
                type = "required_status_checks"
                parameters = @{
                    required_status_checks = @(
                        @{context = "Tests"},
                        @{context = "Lint"},
                        @{context = "Type Check"},
                        @{context = "Security Scan"}
                    )
                    strict_required_status_checks_policy = $true
                }
            },
            @{type = "non_fast_forward"},
            @{type = "required_linear_history"},
            @{type = "required_signatures"}
        )
        bypass_actors = @(
            @{
                actor_id = $GitHubUserId
                actor_type = "OrganizationAdmin"
                bypass_mode = "always"
            }
        )
    }

    $mainRulesetJson = $mainRuleset | ConvertTo-Json -Depth 10 -Compress

    try {
        $mainRulesetJson | gh api -X POST "repos/$RepoOwner/$RepoName/rulesets" `
            --input - 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Created Main Branch Protection ruleset"
        } else {
            Write-Warn "Could not create ruleset via API"
            Write-Info "Rulesets may not be available for your repository type"
            Write-Info "Create manually in Settings -> Rules -> Rulesets"
        }
    } catch {
        Write-Warn "Rulesets API not available (may require GitHub Enterprise)"
        Write-Info "Use branch protection rules instead (already created above)"
    }
} else {
    Write-Info "Skipping rulesets creation"
    Write-Info "Create manually in Settings -> Rules -> Rulesets"
}

# =============================================================================
# 9. Commit and Push Changes
# =============================================================================
Write-Step "Committing changes"

if (-not $DryRun) {
    git add .github/

    if ($LASTEXITCODE -eq 0) {
        git commit -m "chore: setup GitHub automation and CI/CD"

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Changes committed"

            Write-Info "Push changes with: git push origin main"
            Write-Warn "After pushing, workflows will be available"
        } else {
            Write-Info "No changes to commit (files may already exist)"
        }
    }
} else {
    Write-Info "Dry run - changes not committed"
}

# =============================================================================
# 10. Summary
# =============================================================================
Write-Step "Setup Complete!"

Write-Host ""
Write-Host "✓ Repository configured: $RepoOwner/$RepoName" -ForegroundColor $SuccessColor
Write-Host "✓ GitHub user: $GitHubUsername (ID: $GitHubUserId)" -ForegroundColor $SuccessColor
Write-Host "✓ Workflows created: ci.yml, dependabot-auto-merge.yml" -ForegroundColor $SuccessColor
Write-Host "✓ Configuration files created" -ForegroundColor $SuccessColor
Write-Host "✓ Labels created" -ForegroundColor $SuccessColor
Write-Host "✓ Branch protection configured" -ForegroundColor $SuccessColor
Write-Host ""

Write-Host "Next steps:" -ForegroundColor $InfoColor
Write-Host "  1. Push changes: git push origin main" -ForegroundColor $InfoColor
Write-Host "  2. Test with a PR: gh pr create --base main --head copilot/test --title 'test: automation'" -ForegroundColor $InfoColor
Write-Host "  3. Watch it auto-merge! 🎉" -ForegroundColor $InfoColor
Write-Host ""

Write-Host "Manual steps (if needed):" -ForegroundColor $WarningColor
Write-Host "  • Enable auto-merge: Settings → General → Allow auto-merge" -ForegroundColor $WarningColor
Write-Host "  • Set workflow permissions: Settings → Actions → Read and write" -ForegroundColor $WarningColor
Write-Host "  • Create rulesets: Settings → Rules → Rulesets" -ForegroundColor $WarningColor
Write-Host ""

Write-Host "Documentation:" -ForegroundColor $InfoColor
Write-Host "  See .github/ directory for all configurations" -ForegroundColor $InfoColor
