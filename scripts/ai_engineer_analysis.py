#!/usr/bin/env python3
"""
AI Engineer Codebase Analysis Script

Performs deep analysis of the SecBrain codebase to generate context-aware,
cutting-edge security improvement suggestions.
"""
import json
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def run_command(cmd: list[str], cwd: Path | None = None) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command {' '.join(cmd)}: {e}", file=sys.stderr)
        return ""


def analyze_recent_commits(repo_path: Path, days: int = 90) -> dict[str, Any]:
    """Analyze recent commit patterns to identify active development areas."""
    print("🔍 Analyzing recent commits...", file=sys.stderr)
    
    # Get commit count by author
    authors = run_command(
        ["git", "log", f"--since={days} days ago", "--format=%an"],
        cwd=repo_path,
    )
    author_counts = defaultdict(int)
    for author in authors.split("\n"):
        if author:
            author_counts[author] += 1
    
    # Get files changed most frequently
    changed_files = run_command(
        ["git", "log", f"--since={days} days ago", "--name-only", "--format="],
        cwd=repo_path,
    )
    file_changes = defaultdict(int)
    for filepath in changed_files.split("\n"):
        if filepath and not filepath.startswith("."):
            file_changes[filepath] += 1
    
    # Get commit messages to identify themes
    commit_msgs = run_command(
        ["git", "log", f"--since={days} days ago", "--format=%s"],
        cwd=repo_path,
    )
    
    # Categorize commits
    categories = {
        "security": 0,
        "testing": 0,
        "refactor": 0,
        "feature": 0,
        "bugfix": 0,
        "docs": 0,
    }
    
    for msg in commit_msgs.lower().split("\n"):
        if any(word in msg for word in ["security", "vuln", "cve", "exploit"]):
            categories["security"] += 1
        if any(word in msg for word in ["test", "coverage", "pytest"]):
            categories["testing"] += 1
        if any(word in msg for word in ["refactor", "clean", "reorganize"]):
            categories["refactor"] += 1
        if any(word in msg for word in ["add", "feature", "implement"]):
            categories["feature"] += 1
        if any(word in msg for word in ["fix", "bug", "issue"]):
            categories["bugfix"] += 1
        if any(word in msg for word in ["doc", "readme", "comment"]):
            categories["docs"] += 1
    
    return {
        "total_commits": len(commit_msgs.split("\n")) if commit_msgs else 0,
        "active_contributors": len(author_counts),
        "top_contributors": dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
        "most_changed_files": dict(sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:10]),
        "commit_categories": categories,
    }


def analyze_code_patterns(repo_path: Path) -> dict[str, Any]:
    """Analyze code for patterns, anti-patterns, and technical debt."""
    print("🔍 Analyzing code patterns...", file=sys.stderr)
    
    secbrain_path = repo_path / "secbrain" / "secbrain"
    
    # Find TODO/FIXME markers
    todos = run_command(
        ["grep", "-r", "-n", "-E", "TODO|FIXME|XXX|HACK", str(secbrain_path), "--include=*.py"],
    )
    todo_list = [line for line in todos.split("\n") if line]
    
    # Count Python files
    py_files = list(secbrain_path.rglob("*.py"))
    
    # Find files without type hints (looking for function definitions without ->)
    untyped_functions = 0
    for py_file in py_files:
        try:
            content = py_file.read_text()
            # Simple heuristic: count 'def ' vs 'def ' with '->'
            def_count = content.count("def ")
            typed_def_count = content.count("->")
            untyped_functions += max(0, def_count - typed_def_count)
        except Exception:
            continue
    
    # Find security-sensitive patterns
    security_patterns = {
        "subprocess_usage": 0,
        "eval_exec_usage": 0,
        "sql_queries": 0,
        "http_requests": 0,
    }
    
    for py_file in py_files:
        try:
            content = py_file.read_text()
            if "subprocess." in content:
                security_patterns["subprocess_usage"] += 1
            if "eval(" in content or "exec(" in content:
                security_patterns["eval_exec_usage"] += 1
            if any(word in content.lower() for word in ["select ", "insert ", "update ", "delete "]):
                security_patterns["sql_queries"] += 1
            if "httpx" in content or "requests." in content:
                security_patterns["http_requests"] += 1
        except Exception:
            continue
    
    return {
        "total_python_files": len(py_files),
        "todo_count": len(todo_list),
        "todo_items": todo_list[:20],  # First 20
        "untyped_function_estimate": untyped_functions,
        "security_sensitive_areas": security_patterns,
    }


def analyze_dependencies(repo_path: Path) -> dict[str, Any]:
    """Analyze project dependencies for security and freshness."""
    print("🔍 Analyzing dependencies...", file=sys.stderr)
    
    pyproject = repo_path / "secbrain" / "pyproject.toml"
    requirements = repo_path / "requirements.txt"
    
    deps_info = {
        "has_pyproject": pyproject.exists(),
        "has_requirements": requirements.exists(),
        "dependency_count": 0,
        "dev_dependency_count": 0,
    }
    
    if pyproject.exists():
        content = pyproject.read_text()
        # Count dependencies in dependencies section
        if "dependencies = [" in content:
            deps_section = content.split("dependencies = [")[1].split("]")[0]
            deps_info["dependency_count"] = len([d for d in deps_section.split("\n") if d.strip() and d.strip().startswith('"')])
        
        if '[project.optional-dependencies]' in content and 'dev = [' in content:
            dev_section = content.split("dev = [")[1].split("]")[0]
            deps_info["dev_dependency_count"] = len([d for d in dev_section.split("\n") if d.strip() and d.strip().startswith('"')])
    
    return deps_info


def analyze_test_coverage(repo_path: Path) -> dict[str, Any]:
    """Analyze test coverage and test quality."""
    print("🔍 Analyzing test coverage...", file=sys.stderr)
    
    test_path = repo_path / "secbrain" / "tests"
    
    if not test_path.exists():
        return {"test_files": 0, "test_structure": "none"}
    
    test_files = list(test_path.rglob("test_*.py"))
    
    # Check for different types of tests
    has_unit_tests = any("test_" in f.name for f in test_files)
    has_integration_tests = any("integration" in str(f) for f in test_files)
    has_property_tests = False
    
    for test_file in test_files:
        try:
            content = test_file.read_text()
            if "hypothesis" in content.lower() or "@given" in content:
                has_property_tests = True
                break
        except Exception:
            continue
    
    return {
        "test_files": len(test_files),
        "has_unit_tests": has_unit_tests,
        "has_integration_tests": has_integration_tests,
        "has_property_tests": has_property_tests,
    }


def analyze_ci_workflows(repo_path: Path) -> dict[str, Any]:
    """Analyze CI/CD workflows and recent run results."""
    print("🔍 Analyzing CI/CD workflows...", file=sys.stderr)
    
    workflows_path = repo_path / ".github" / "workflows"
    
    if not workflows_path.exists():
        return {"workflow_count": 0}
    
    workflows = list(workflows_path.glob("*.yml"))
    
    workflow_types = {
        "security": [],
        "testing": [],
        "quality": [],
        "automation": [],
    }
    
    for workflow in workflows:
        name = workflow.stem
        if any(word in name for word in ["security", "audit", "scan", "cve"]):
            workflow_types["security"].append(name)
        elif any(word in name for word in ["test", "ci", "coverage"]):
            workflow_types["testing"].append(name)
        elif any(word in name for word in ["quality", "lint", "format"]):
            workflow_types["quality"].append(name)
        elif any(word in name for word in ["ai", "engineer", "insight", "auto"]):
            workflow_types["automation"].append(name)
    
    return {
        "workflow_count": len(workflows),
        "workflow_types": workflow_types,
    }


def analyze_solidity_contracts(repo_path: Path) -> dict[str, Any]:
    """Analyze Solidity contracts in the codebase."""
    print("🔍 Analyzing Solidity contracts...", file=sys.stderr)
    
    sol_files = list(repo_path.rglob("*.sol"))
    # Exclude venv and node_modules
    sol_files = [f for f in sol_files if ".venv" not in str(f) and "node_modules" not in str(f)]
    
    if not sol_files:
        return {"contract_count": 0}
    
    contract_info = {
        "contract_count": len(sol_files),
        "test_contracts": 0,
        "exploit_attempts": 0,
    }
    
    for sol_file in sol_files:
        filepath = str(sol_file)
        if ".t.sol" in filepath.lower() or "test" in filepath.lower():
            contract_info["test_contracts"] += 1
        if "exploit" in filepath.lower():
            contract_info["exploit_attempts"] += 1
    
    return contract_info


def get_open_issues_summary(repo_path: Path) -> dict[str, Any]:
    """Get summary of open issues from git repository."""
    print("🔍 Checking for open issue patterns...", file=sys.stderr)
    
    # Check if there are any issue templates or documentation
    issue_templates = list((repo_path / ".github").rglob("ISSUE_TEMPLATE*")) if (repo_path / ".github").exists() else []
    
    return {
        "has_issue_templates": len(issue_templates) > 0,
        "template_count": len(issue_templates),
    }


def identify_improvement_areas(analysis: dict[str, Any]) -> list[str]:
    """Identify key areas for improvement based on analysis."""
    areas = []
    
    commits = analysis.get("commits", {})
    code = analysis.get("code_patterns", {})
    tests = analysis.get("test_coverage", {})
    ci = analysis.get("ci_workflows", {})
    contracts = analysis.get("solidity_contracts", {})
    
    # Security focus areas
    if commits.get("commit_categories", {}).get("security", 0) > 0:
        areas.append("active_security_development")
    
    # Testing gaps
    if not tests.get("has_property_tests", False):
        areas.append("needs_property_based_testing")
    
    if tests.get("test_files", 0) < code.get("total_python_files", 0) * 0.5:
        areas.append("insufficient_test_coverage")
    
    # Type safety
    if code.get("untyped_function_estimate", 0) > 50:
        areas.append("needs_type_annotations")
    
    # Technical debt
    if code.get("todo_count", 0) > 20:
        areas.append("high_technical_debt")
    
    # Solidity security
    if contracts.get("contract_count", 0) > 0:
        areas.append("solidity_security_focus")
    
    # CI/CD maturity
    if ci.get("workflow_count", 0) < 5:
        areas.append("needs_more_automation")
    
    return areas


def main() -> None:
    """Main analysis function."""
    repo_path = Path(__file__).parent.parent
    
    print("🚀 Starting AI Engineer codebase analysis...\n", file=sys.stderr)
    
    # Perform all analyses
    analysis = {
        "timestamp": datetime.now(UTC).isoformat(),
        "repository": "secbrain",
        "commits": analyze_recent_commits(repo_path),
        "code_patterns": analyze_code_patterns(repo_path),
        "dependencies": analyze_dependencies(repo_path),
        "test_coverage": analyze_test_coverage(repo_path),
        "ci_workflows": analyze_ci_workflows(repo_path),
        "solidity_contracts": analyze_solidity_contracts(repo_path),
        "open_issues": get_open_issues_summary(repo_path),
    }
    
    # Identify improvement areas
    analysis["improvement_areas"] = identify_improvement_areas(analysis)
    
    # Output as JSON
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
