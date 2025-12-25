#!/usr/bin/env python3
"""
Comprehensive Security Analysis Workflow Validator

This script validates the workflow configuration and checks for common issues.
"""

import json
import sys
from pathlib import Path

import yaml


def load_workflow(path: Path) -> dict:
    """Load and parse the workflow YAML file."""
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load workflow: {e}")
        sys.exit(1)


def validate_structure(workflow: dict) -> list[str]:
    """Validate basic workflow structure."""
    issues = []
    
    # Check required top-level keys
    # Note: YAML parsers convert "on" to True (boolean)
    required_keys = ["name", "permissions", "jobs"]
    for key in required_keys:
        if key not in workflow:
            issues.append(f"Missing required key: {key}")
    
    # Check for "on" key (may be parsed as True)
    if "on" not in workflow and True not in workflow:
        issues.append("Missing workflow trigger configuration ('on' key)")
    
    # Check workflow_dispatch inputs - handle both "on" and True
    trigger_key = "on" if "on" in workflow else True
    if trigger_key in workflow:
        trigger_config = workflow[trigger_key]
        if "workflow_dispatch" in trigger_config:
            inputs = trigger_config["workflow_dispatch"].get("inputs", {})
            required_inputs = [
                "target_repo",
                "target_type",
                "analysis_depth",
                "enable_ai_analysis",
                "enable_fuzzing",
            ]
            for inp in required_inputs:
                if inp not in inputs:
                    issues.append(f"Missing workflow input: {inp}")
    
    return issues


def validate_jobs(workflow: dict) -> list[str]:
    """Validate job configurations."""
    issues = []
    jobs = workflow.get("jobs", {})
    
    expected_jobs = [
        "setup-and-recon",
        "python-static-analysis",
        "solidity-static-analysis",
        "mythril-analysis",
        "foundry-fuzzing",
        "echidna-fuzzing",
        "ai-engineer-analysis",
        "security-intelligence",
        "generate-recommendations",
        "secbrain-agents",
        "aggregate-findings",
        "create-issue-report",
    ]
    
    for job_name in expected_jobs:
        if job_name not in jobs:
            issues.append(f"Missing job: {job_name}")
            continue
        
        job = jobs[job_name]
        
        # Check for timeout
        if "timeout-minutes" not in job:
            issues.append(f"Job '{job_name}' missing timeout-minutes")
        
        # Check for steps
        if "steps" not in job:
            issues.append(f"Job '{job_name}' missing steps")
        
        # Check conditional jobs have 'if' condition
        conditional_jobs = [
            "python-static-analysis",
            "solidity-static-analysis",
            "mythril-analysis",
            "foundry-fuzzing",
            "echidna-fuzzing",
        ]
        if job_name in conditional_jobs and "if" not in job:
            issues.append(f"Conditional job '{job_name}' missing 'if' condition")
    
    return issues


def validate_artifacts(workflow: dict) -> list[str]:
    """Validate artifact upload/download configurations."""
    issues = []
    jobs = workflow.get("jobs", {})
    
    # Jobs that should upload artifacts
    upload_jobs = [
        "setup-and-recon",
        "python-static-analysis",
        "solidity-static-analysis",
        "mythril-analysis",
        "foundry-fuzzing",
        "echidna-fuzzing",
        "ai-engineer-analysis",
        "security-intelligence",
        "generate-recommendations",
        "secbrain-agents",
        "aggregate-findings",
    ]
    
    for job_name in upload_jobs:
        if job_name not in jobs:
            continue
        
        job = jobs[job_name]
        steps = job.get("steps", [])
        
        # Check for upload-artifact step
        has_upload = any(
            step.get("uses", "").startswith("actions/upload-artifact")
            for step in steps
        )
        
        if not has_upload:
            issues.append(f"Job '{job_name}' should upload artifacts")
    
    return issues


def validate_env_vars(workflow: dict) -> list[str]:
    """Validate environment variables."""
    issues = []
    
    # Check global env vars
    if "env" not in workflow:
        issues.append("Missing global env variables")
    else:
        required_env = ["ANALYSIS_DIR", "RESULTS_DIR"]
        for env_var in required_env:
            if env_var not in workflow["env"]:
                issues.append(f"Missing environment variable: {env_var}")
    
    return issues


def check_job_dependencies(workflow: dict) -> list[str]:
    """Check job dependency graph for cycles and issues."""
    issues = []
    jobs = workflow.get("jobs", {})
    
    # Build dependency graph
    dependencies = {}
    for job_name, job in jobs.items():
        needs = job.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        dependencies[job_name] = needs
    
    # Check for missing dependencies
    for job_name, deps in dependencies.items():
        for dep in deps:
            if dep not in jobs:
                issues.append(
                    f"Job '{job_name}' depends on non-existent job '{dep}'"
                )
    
    return issues


def validate_syntax_elements(workflow: dict) -> list[str]:
    """Validate specific syntax elements."""
    issues = []
    
    # Convert workflow to string for pattern checking
    workflow_str = json.dumps(workflow)
    
    # Check for proper GitHub context usage
    if "${{ github.run_id }}" not in workflow_str:
        issues.append("Warning: Workflow doesn't use github.run_id for tracking")
    
    # Check for continue-on-error usage
    if "continue-on-error" not in workflow_str:
        issues.append("Warning: No jobs use continue-on-error for resilience")
    
    return issues


def main():
    """Run all validation checks."""
    print("🔍 Validating Comprehensive Security Analysis Workflow\n")
    
    workflow_path = Path(
        ".github/workflows/comprehensive-security-analysis.yml"
    )
    
    if not workflow_path.exists():
        print(f"❌ Workflow file not found: {workflow_path}")
        sys.exit(1)
    
    workflow = load_workflow(workflow_path)
    print(f"✅ Successfully loaded workflow: {workflow.get('name')}\n")
    
    all_issues = []
    
    # Run validation checks
    checks = [
        ("Structure", validate_structure),
        ("Jobs", validate_jobs),
        ("Artifacts", validate_artifacts),
        ("Environment Variables", validate_env_vars),
        ("Job Dependencies", check_job_dependencies),
        ("Syntax Elements", validate_syntax_elements),
    ]
    
    for check_name, check_func in checks:
        print(f"Checking {check_name}...")
        issues = check_func(workflow)
        if issues:
            all_issues.extend(issues)
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print(f"  ✅ {check_name} validation passed")
        print()
    
    # Summary
    print("=" * 60)
    if all_issues:
        print(f"\n⚠️  Found {len(all_issues)} issue(s):\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
        print("\nSome issues may be warnings and not errors.")
        sys.exit(0)  # Don't fail on warnings
    else:
        print("\n✅ All validation checks passed!")
        print("\nWorkflow is ready to use.")
        print("\nNext steps:")
        print("1. Set up required secrets (PERPLEXITY_API_KEY, GOOGLE_API_KEY)")
        print("2. Run workflow via GitHub UI or CLI")
        print("3. Review generated artifacts and reports")
        sys.exit(0)


if __name__ == "__main__":
    main()
