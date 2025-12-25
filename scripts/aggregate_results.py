#!/usr/bin/env python3
"""
Comprehensive Analysis Results Aggregator

This script aggregates results from multiple security tools into a unified JSON format
with proper severity classification and deduplication.
"""

import json
import sys
from pathlib import Path
from typing import Any


def load_json_safe(filepath: Path) -> dict[str, Any] | None:
    """Safely load JSON file, return None if file doesn't exist or is invalid."""
    try:
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}", file=sys.stderr)
    return None


def count_bandit_issues(results: dict[str, Any]) -> tuple[int, int, int, int]:
    """Count Bandit issues by severity."""
    if not results or "results" not in results:
        return 0, 0, 0, 0
    
    critical = 0
    high = 0
    medium = 0
    low = 0
    
    for issue in results["results"]:
        severity = issue.get("issue_severity", "").upper()
        if severity == "HIGH":
            high += 1
        elif severity == "MEDIUM":
            medium += 1
        elif severity == "LOW":
            low += 1
    
    return critical, high, medium, low


def count_slither_issues(results: dict[str, Any]) -> tuple[int, int, int, int]:
    """Count Slither issues by severity."""
    if not results or "results" not in results or "detectors" not in results["results"]:
        return 0, 0, 0, 0
    
    critical = 0
    high = 0
    medium = 0
    low = 0
    
    for detector in results["results"]["detectors"]:
        impact = detector.get("impact", "").lower()
        if impact == "high":
            high += 1
        elif impact == "medium":
            medium += 1
        elif impact == "low":
            low += 1
        elif impact == "informational":
            # Count informational as low
            low += 1
    
    return critical, high, medium, low


def count_safety_issues(results: dict[str, Any]) -> tuple[int, int, int, int]:
    """Count Safety (dependency vulnerability) issues."""
    if not results or "vulnerabilities" not in results:
        return 0, 0, 0, 0
    
    critical = 0
    high = 0
    medium = 0
    low = 0
    
    # Safety reports vulnerabilities with various attributes
    # We classify based on CVE severity if available, otherwise treat as high
    for vuln in results["vulnerabilities"]:
        # Check for severity indicators in the advisory or CVE data
        advisory = vuln.get("advisory", "").lower()
        cve = vuln.get("cve", "").lower()
        
        # Look for severity keywords
        if "critical" in advisory or "critical" in cve:
            critical += 1
        elif "high" in advisory or "high" in cve:
            high += 1
        elif "medium" in advisory or "moderate" in cve:
            medium += 1
        elif "low" in advisory or "low" in cve:
            low += 1
        else:
            # Default to high severity for dependency vulnerabilities without explicit severity
            high += 1
    
    return critical, high, medium, low


def count_semgrep_issues(results: dict[str, Any]) -> tuple[int, int, int, int]:
    """Count Semgrep issues by severity."""
    if not results or "results" not in results:
        return 0, 0, 0, 0
    
    critical = 0
    high = 0
    medium = 0
    low = 0
    
    for finding in results["results"]:
        severity = finding.get("extra", {}).get("severity", "").upper()
        if severity == "ERROR":
            high += 1
        elif severity == "WARNING":
            medium += 1
        elif severity == "INFO":
            low += 1
    
    return critical, high, medium, low


def aggregate_results(artifacts_dir: str) -> dict[str, Any]:
    """Aggregate all security tool results."""
    artifacts_path = Path(artifacts_dir)
    
    # Initialize counters
    total_critical = 0
    total_high = 0
    total_medium = 0
    total_low = 0
    
    tool_results = {}
    
    # Process Bandit results
    bandit_path = artifacts_path / "static-analysis-python" / "bandit" / "results.json"
    bandit_data = load_json_safe(bandit_path)
    if bandit_data:
        crit, high, med, low = count_bandit_issues(bandit_data)
        total_critical += crit
        total_high += high
        total_medium += med
        total_low += low
        tool_results["bandit"] = {
            "available": True,
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low,
        }
        print(f"✅ Bandit: {high} high, {med} medium, {low} low", file=sys.stderr)
    else:
        tool_results["bandit"] = {"available": False}
        print("⚠️  Bandit results not found", file=sys.stderr)
    
    # Process Slither results
    slither_path = artifacts_path / "static-analysis-solidity" / "slither" / "slither-results.json"
    slither_data = load_json_safe(slither_path)
    if slither_data:
        crit, high, med, low = count_slither_issues(slither_data)
        total_critical += crit
        total_high += high
        total_medium += med
        total_low += low
        tool_results["slither"] = {
            "available": True,
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low,
        }
        print(f"✅ Slither: {high} high, {med} medium, {low} low", file=sys.stderr)
    else:
        tool_results["slither"] = {"available": False}
        print("⚠️  Slither results not found", file=sys.stderr)
    
    # Process Safety results
    safety_path = artifacts_path / "static-analysis-python" / "safety" / "results.json"
    safety_data = load_json_safe(safety_path)
    if safety_data:
        crit, high, med, low = count_safety_issues(safety_data)
        total_critical += crit
        total_high += high
        total_medium += med
        total_low += low
        tool_results["safety"] = {
            "available": True,
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low,
            "total_vulnerabilities": crit + high + med + low,
        }
        print(f"✅ Safety: {crit} critical, {high} high, {med} medium, {low} low", file=sys.stderr)
    else:
        tool_results["safety"] = {"available": False}
        print("⚠️  Safety results not found", file=sys.stderr)
    
    # Process Semgrep results
    semgrep_path = artifacts_path / "static-analysis-python" / "semgrep" / "results.json"
    semgrep_data = load_json_safe(semgrep_path)
    if semgrep_data:
        crit, high, med, low = count_semgrep_issues(semgrep_data)
        total_critical += crit
        total_high += high
        total_medium += med
        total_low += low
        tool_results["semgrep"] = {
            "available": True,
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low,
        }
        print(f"✅ Semgrep: {high} high, {med} medium, {low} low", file=sys.stderr)
    else:
        tool_results["semgrep"] = {"available": False}
        print("⚠️  Semgrep results not found", file=sys.stderr)
    
    total_issues = total_critical + total_high + total_medium + total_low
    
    print(f"\n📊 Total: {total_issues} issues ({total_critical} critical, {total_high} high, {total_medium} medium, {total_low} low)", file=sys.stderr)
    
    return {
        "summary": {
            "total_issues": total_issues,
            "critical_issues": total_critical,
            "high_issues": total_high,
            "medium_issues": total_medium,
            "low_issues": total_low,
        },
        "tools": tool_results,
    }


def main() -> None:
    """Main aggregation function."""
    if len(sys.argv) < 2:
        print("Usage: aggregate_results.py <artifacts_dir>", file=sys.stderr)
        sys.exit(1)
    
    artifacts_dir = sys.argv[1]
    results = aggregate_results(artifacts_dir)
    
    # Output as JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
