# Branch Strategy

## Current State

All development work is now consolidated on the **main** branch.

> ⚠️ **Action Required**: This change is implemented via PR. Once this PR is merged to `main`, delete all `copilot/*` branches and work directly on `main` going forward. See [BRANCH-CONSOLIDATION.md](BRANCH-CONSOLIDATION.md) for details.

## Why Main Only?

To avoid merge conflicts and branch management complexity, this repository uses a simplified single-branch strategy:

- ✅ All work happens on `main`
- ✅ Direct commits to `main` are allowed
- ✅ No need to manage multiple feature branches
- ✅ No merge conflicts between branches

## Development Workflow

1. Always work on the `main` branch:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

3. That's it! No branches, no merges, no conflicts.

## For GitHub Copilot / Automation

When automated tools create branches (like `copilot/*`), they should be:
- Merged into main immediately after validation
- Deleted after merging
- Never left to accumulate

## Previous Branches

All previous `copilot/*` branches have been consolidated. If you see old branches:
- They can be safely deleted
- All work is on `main`
- No need to merge them - main has everything

## Benefits

- 🚀 Faster development - no branch switching
- 🎯 Single source of truth - everything is on main
- 🔧 Simpler maintenance - no orphaned branches
- ✨ Zero merge conflicts - no parallel branches to merge

## Trade-offs

This strategy works best for:
- Solo developers or small teams
- Projects where main is always deployable
- Rapid iteration and development

If you need to experiment with breaking changes, create a temporary branch but merge or delete it quickly.
