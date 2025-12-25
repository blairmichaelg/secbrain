# Contributing to SecBrain

This guide will help you understand how to work with this repository, including Git workflows, committing changes, merging code, and dealing with CI/CD issues.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Git Workflow](#git-workflow)
3. [Making Changes](#making-changes)
4. [Committing Code](#committing-code)
5. [Creating Pull Requests](#creating-pull-requests)
6. [Merging Changes](#merging-changes)
7. [Dealing with Merge Conflicts](#dealing-with-merge-conflicts)
8. [CI/CD Workflow](#cicd-workflow)
9. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Getting Started

### Prerequisites
- **Git**: Install from [git-scm.com](https://git-scm.com/)
- **Python 3.11+**: Required for this project
- **GitHub Account**: To contribute to this repository

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/blairmichaelg/secbrain.git
cd secbrain

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd secbrain
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e ".[dev]"
```

---

## Git Workflow

> 📌 **Updated Workflow**: This repository now uses a simplified single-branch workflow. See [BRANCH-STRATEGY.md](BRANCH-STRATEGY.md) for details.

### Simplified Approach

**All work happens on `main`:**
- Direct commits to `main` are encouraged
- No feature branches needed for most work
- Faster iteration and zero merge conflicts

### When to Use Branches (Optional)

Only create a branch if:
- Testing breaking/experimental changes
- Working on something that needs review before merging

**If you create a branch:**
- Merge it quickly (same day or next day)
- Delete it immediately after merging
- Don't let branches accumulate

### Best Practices

1. **Work directly on `main`** for most changes
2. **Keep main up to date**: `git pull origin main` before starting work
3. **Write clear, descriptive commit messages**
4. **Test your changes** before pushing

---

## Making Changes

### 1. Start Working on Main

```bash
# Make sure you're on main and it's up to date
git checkout main
git pull origin main
```

### 2. Make Your Changes

Edit files as needed, then check what you've changed:

```bash
# See which files have been modified
git status

# See the actual changes in detail
git diff

# See changes for a specific file
git diff path/to/file.py
```

### 3. Test Your Changes

```bash
# Run linting
python -m ruff check .

# Run type checking (note: currently has many errors we're working on fixing)
python -m mypy secbrain

# Run tests
python -m pytest tests/ -v
```

---

## Committing Code

### Understanding Git Commits

A **commit** is a snapshot of your code at a specific point in time. Think of it as a save point in a video game.

### Staging Changes

Before committing, you need to **stage** files (tell Git which changes you want to include):

```bash
# Stage a specific file
git add path/to/file.py

# Stage all changes in current directory
git add .

# Stage all Python files
git add *.py

# See what's staged
git status
```

### Writing Good Commit Messages

A good commit message has two parts:

1. **Summary line** (50 characters or less): What does this commit do?
2. **Detailed description** (optional): Why did you make this change?

**Good examples:**
```
Fix type errors in exploit_agent.py

- Add missing import for httpx
- Fix function signature inconsistencies  
- Add type annotations where needed
```

```
Add user authentication feature

Implement JWT-based authentication system with
login, logout, and token refresh endpoints.
```

**Bad examples:**
```
fix stuff
```
```
updates
```
```
asdfasdf
```

### Making a Commit

```bash
# Stage your changes
git add .

# Commit with a message
git commit -m "Add feature X to improve Y"

# For longer messages, use an editor
git commit
# This opens your default text editor for a detailed message
```

### Checking Your Commit History

```bash
# See recent commits
git log --oneline

# See recent commits with details
git log

# See what changed in the last commit
git show

# See what changed in a specific commit
git show abc123
```

---

## Creating Pull Requests

> 📌 **Note**: With the simplified single-branch workflow, PRs are optional for most work. You can commit directly to `main`. PRs are useful for:
> - Getting review on complex changes
> - Discussing architectural decisions
> - Automated testing via GitHub Actions

### Option 1: Direct Push to Main (Recommended for most changes)

```bash
# Stage and commit your changes
git add .
git commit -m "Add feature X to improve Y"

# Push directly to main
git push origin main
```

### Option 2: Create a Pull Request (For changes needing review)

**1. Create a temporary branch:**
```bash
# Create a branch for review
git checkout -b review/my-changes

# Push the branch
git push -u origin review/my-changes
```

**2. Create the PR:**
1. Go to https://github.com/blairmichaelg/secbrain
2. Click "Compare & pull request"
3. Fill in the PR description:
   - **Title**: Clear summary of what this PR does
   - **Description**: Explain what changes you made and why
4. Click "Create pull request"

**3. After approval, merge and delete:**
```bash
# After PR is merged, delete the branch
git push origin --delete review/my-changes
git checkout main
git pull origin main
git branch -d review/my-changes
```

### Responding to Review Comments

```bash
# Make the requested changes
git add .
git commit -m "Address review feedback"

# Push the updates
git push origin your-branch-name
```

The PR will automatically update!

---

## Merging Changes

### What is Merging?

**Merging** combines changes from one branch into another. For example, merging your feature branch into `main`.

### Types of Merges

1. **Merge Commit** - Creates a new commit that combines both branches
2. **Squash and Merge** - Combines all commits into one before merging
3. **Rebase and Merge** - Replays your commits on top of the target branch

### When Your PR is Approved

**GitHub will handle the merge** - just click the "Merge pull request" button!

### Keeping Your Branch Updated

```bash
# While working on a feature, periodically sync with main
git checkout main
git pull origin main
git checkout feature/my-new-feature
git merge main

# Or use rebase (more advanced)
git checkout feature/my-new-feature
git rebase main
```

---

## Dealing with Merge Conflicts

### With Single-Branch Workflow

> 🎉 **Good News**: With everyone working on `main`, merge conflicts are **extremely rare**!

Since there are no parallel branches being developed:
- No need to merge feature branches
- No conflicts between different development lines
- Linear history is easy to understand

### If a Conflict Does Happen

Conflicts might still occur if:
- Multiple people push to `main` at the exact same time
- You have local unpushed commits and someone else pushed first

**Simple resolution:**

```bash
# Pull the latest changes
git pull origin main

# If there's a conflict, Git will tell you which files
# Open the conflicted files and look for conflict markers
```

1. **Git will mark the conflict** in your files:

```python
<<<<<<< HEAD
# Your version of the code
def my_function():
    return "my way"
=======
# Their version of the code  
def my_function():
    return "their way"
>>>>>>> main
```

2. **Edit the file** to keep what you want:

```python
# Keep the best version or combine them
def my_function():
    return "combined way"
```

3. **Mark as resolved and commit**:

```bash
# After fixing all conflicts
git add path/to/conflicted/file.py

# Finish the merge
git commit -m "Resolve merge conflicts"

# Push the resolution
git push origin feature/my-new-feature
```

### Avoiding Conflicts

1. **Pull frequently** from main
2. **Communicate** with your team about what you're working on
3. **Keep PRs small** and focused
4. **Merge your PRs quickly** once approved

---

## CI/CD Workflow

### Understanding CI/CD

**CI (Continuous Integration)** automatically tests your code when you push changes.

**CD (Continuous Deployment)** automatically deploys your code when it passes tests.

### Our CI Pipeline

When you push code or create a PR, GitHub Actions runs:

1. **Linting** - Checks code style (ruff)
2. **Type Checking** - Verifies type annotations (mypy) - *Currently non-blocking*
3. **Unit Tests** - Runs test suite
4. **Coverage** - Ensures adequate test coverage
5. **Integration Tests** - Tests real-world scenarios

### Viewing CI Results

1. Go to your PR on GitHub
2. Scroll down to see "Checks" section
3. Click "Details" next to any failed check to see logs

### Current Known Issues

⚠️ **Type Checking**: We're currently fixing extensive mypy errors. The type check step is set to `continue-on-error: false` but we're working on fixing these gradually.

**What you can do:**
- If mypy fails on your PR, check if YOUR changes introduced new errors
- You're not responsible for fixing all existing type errors
- Focus on not making the problem worse

---

## Common Issues and Solutions

### Issue: "Please commit your changes or stash them before you switch branches"

**What happened:** You have uncommitted changes and Git doesn't want you to lose them.

**Solution:**
```bash
# Option 1: Commit your changes
git add .
git commit -m "WIP: save progress"

# Option 2: Stash changes temporarily
git stash
git checkout other-branch
# When you come back:
git checkout your-branch
git stash pop
```

### Issue: "Your branch is behind 'origin/main' by X commits"

**What happened:** Other people pushed changes to main.

**Solution:**
```bash
git checkout main
git pull origin main
git checkout your-branch
git merge main  # or git rebase main
```

### Issue: "fatal: refusing to merge unrelated histories"

**What happened:** You're trying to merge two branches with no common ancestor.

**Solution:**
```bash
git merge --allow-unrelated-histories origin/main
# or
git rebase --rebase-merges origin/main
```

### Issue: CI is failing but it works locally

**Possible causes:**
1. Different Python version (CI uses 3.11)
2. Missing dependencies
3. Environment-specific issues

**Solution:**
```bash
# Match the CI environment
python3.11 -m pytest tests/
python -m mypy secbrain

# Check workflow file
cat .github/workflows/contract-audit-ci.yml
```

### Issue: Accidentally committed to main

**Solution:**
```bash
# Create a new branch from your current position
git branch feature/my-changes

# Reset main to match origin
git checkout main
git reset --hard origin/main

# Continue work on the feature branch
git checkout feature/my-changes
```

### Issue: Want to undo last commit

**Solution:**
```bash
# Undo commit but keep changes
git reset --soft HEAD~1

# Undo commit and discard changes (careful!)
git reset --hard HEAD~1

# Undo commit on a pushed branch (creates new commit)
git revert HEAD
```

---

## Quick Reference

### Essential Git Commands

```bash
# Status and info
git status                     # See current state
git log --oneline             # See commit history
git diff                      # See unstaged changes

# Branching
git branch                    # List branches
git checkout -b new-branch    # Create and switch to branch
git checkout main             # Switch to main
git branch -d old-branch      # Delete branch

# Saving changes
git add .                     # Stage all changes
git commit -m "message"       # Commit with message
git push origin branch-name   # Push to GitHub

# Getting updates
git pull origin main          # Get latest from main
git fetch origin              # Download updates without merging

# Fixing mistakes
git checkout -- file.py       # Discard changes to file
git reset HEAD file.py        # Unstage file
git revert abc123             # Undo a specific commit
```

### Getting Help

```bash
# Get help on any Git command
git help <command>
git <command> --help

# Examples
git help commit
git merge --help
```

---

## Learning Resources

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **Interactive Git Tutorial**: https://learngitbranching.js.org/
- **Git Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf

---

## Getting Help

If you're stuck:

1. **Read the error message carefully** - it often tells you what's wrong
2. **Check this guide** for common issues
3. **Search GitHub issues** - someone might have had the same problem
4. **Ask in the PR** - maintainers are happy to help
5. **Stack Overflow** - search for similar questions

Remember: Everyone struggles with Git sometimes. Don't be afraid to ask for help!

---

## Summary: Basic Workflow

Here's the simple workflow to follow every time:

```bash
# 1. Start from main
git checkout main
git pull origin main

# 2. Create a feature branch  
git checkout -b feature/my-feature

# 3. Make changes and commit often
git add .
git commit -m "Descriptive message"

# 4. Push your branch
git push origin feature/my-feature

# 5. Create a PR on GitHub
# (Use the GitHub web interface)

# 6. Address review feedback
git add .
git commit -m "Address feedback"
git push origin feature/my-feature

# 7. Once approved, merge on GitHub
# (Click the "Merge" button)

# 8. Clean up
git checkout main
git pull origin main
git branch -d feature/my-feature
```

That's it! Follow this flow and you'll be a Git pro in no time.

---

**Questions?** Open an issue or ask in your PR!

---

*Last updated: December 25, 2024*
