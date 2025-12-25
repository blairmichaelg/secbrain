#!/usr/bin/env python3
"""
Example: Generate insights for all workspaces and create a summary dashboard.

This script demonstrates how to use the SecBrain insights module programmatically
to analyze multiple targets and generate a consolidated report.
"""

from pathlib import Path

from secbrain.insights import InsightsAggregator, InsightsAnalyzer, InsightsReporter


def main():
    """Generate insights for all workspaces."""

    # Find all workspaces (adjust path based on where you run from)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    targets_dir = project_root / "targets"

    if not targets_dir.exists():
        print(f"Targets directory not found at {targets_dir}")
        print("Adjust the targets_dir path in the script or run from project root")
        return

    workspaces = []

    for workspace in targets_dir.iterdir():
        if workspace.is_dir() and (workspace / "run_summary.json").exists():
            workspaces.append(workspace)

    if not workspaces:
        print("No workspaces found in targets directory")
        return

    print(f"Found {len(workspaces)} workspace(s)")

    # Analyze each workspace
    all_results = []

    for workspace in workspaces:
        protocol = workspace.name
        print(f"\n📊 Analyzing {protocol}...")

        try:
            # Aggregate data
            aggregator = InsightsAggregator(workspace)
            data = aggregator.aggregate()

            # Analyze
            analyzer = InsightsAnalyzer()
            results = analyzer.analyze(data)

            # Store results with protocol name
            results.summary["protocol"] = protocol
            all_results.append(results)

            # Print summary
            print(f"  Status: {results.summary['status']}")
            print(f"  Critical: {results.summary['critical_count']}")
            print(f"  High: {results.summary['high_count']}")

            # Generate individual report
            reporter = InsightsReporter(workspace / "insights")
            reporter.save_all_formats(results, base_filename=f"{protocol}_insights")
            print(f"  ✓ Reports saved to {workspace}/insights/")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Generate consolidated dashboard
    print("\n" + "="*60)
    print("CONSOLIDATED DASHBOARD")
    print("="*60)

    # Count by status
    requires_attention = sum(1 for r in all_results if r.summary["status"] == "requires_attention")
    review_recommended = sum(1 for r in all_results if r.summary["status"] == "review_recommended")
    healthy = sum(1 for r in all_results if r.summary["status"] == "healthy")

    print("\n📈 Overall Status:")
    print(f"  🔴 Requires Attention: {requires_attention}")
    print(f"  🟡 Review Recommended: {review_recommended}")
    print(f"  🟢 Healthy: {healthy}")

    # Total critical issues
    total_critical = sum(r.summary["critical_count"] for r in all_results)
    total_high = sum(r.summary["high_count"] for r in all_results)

    print("\n⚠️  Issues:")
    print(f"  Critical: {total_critical}")
    print(f"  High: {total_high}")

    # Top priorities
    print("\n🎯 Top Priorities:")

    priority_protocols = sorted(
        all_results,
        key=lambda r: (r.summary["critical_count"], r.summary["high_count"]),
        reverse=True
    )

    for i, result in enumerate(priority_protocols[:5], 1):
        protocol = result.summary.get("protocol", "unknown")
        critical = result.summary["critical_count"]
        high = result.summary["high_count"]
        status = result.summary["status"]

        print(f"  {i}. {protocol}: {critical} critical, {high} high ({status})")

    # Save consolidated JSON report
    import json
    from datetime import UTC, datetime

    dashboard_data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "total_workspaces": len(all_results),
            "requires_attention": requires_attention,
            "review_recommended": review_recommended,
            "healthy": healthy,
            "total_critical": total_critical,
            "total_high": total_high,
        },
        "workspaces": [
            {
                "protocol": r.summary.get("protocol", "unknown"),
                "status": r.summary["status"],
                "critical_count": r.summary["critical_count"],
                "high_count": r.summary["high_count"],
                "next_action": r.summary["next_action"],
                "metrics": r.metrics,
            }
            for r in all_results
        ],
    }

    dashboard_path = Path("insights-dashboard.json")
    with dashboard_path.open("w") as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"\n✓ Consolidated dashboard saved to {dashboard_path}")
    print("\nDone! 🎉")


if __name__ == "__main__":
    main()
