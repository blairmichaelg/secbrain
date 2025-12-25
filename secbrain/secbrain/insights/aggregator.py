"""Insights aggregator - collects data from workspace.

This module aggregates and analyzes data from SecBrain workspace including:
- Run summary collection and analysis
- Learning data aggregation
- Meta-metrics tracking
- Phase data compilation
- Exploit attempt history
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkspaceData:
    """Aggregated workspace data."""

    workspace_path: Path
    run_summaries: list[dict[str, Any]] = field(default_factory=list)
    learnings: list[dict[str, Any]] = field(default_factory=list)
    meta_metrics: list[dict[str, Any]] = field(default_factory=list)
    phases: dict[str, Any] = field(default_factory=dict)
    exploit_attempts: list[dict[str, Any]] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_runs(self) -> int:
        """Total number of runs."""
        return len(self.run_summaries)

    @property
    def successful_runs(self) -> int:
        """Number of successful runs."""
        return sum(1 for r in self.run_summaries if r.get("success"))

    @property
    def total_hypotheses(self) -> int:
        """Total hypotheses generated across all runs."""
        return sum(m.get("hypotheses_count", 0) for m in self.meta_metrics)

    @property
    def total_attempts(self) -> int:
        """Total exploit attempts across all runs."""
        return sum(m.get("attempts_count", 0) for m in self.meta_metrics)


class InsightsAggregator:
    """Aggregates data from a SecBrain workspace."""

    def __init__(self, workspace_path: str | Path):
        """Initialize aggregator.

        Args:
            workspace_path: Path to the workspace directory
            
        Raises:
            ValueError: If workspace path does not exist or is not a directory
        """
        self.workspace_path = Path(workspace_path)
        if not self.workspace_path.exists():
            raise ValueError(f"Workspace path does not exist: {workspace_path}")
        if not self.workspace_path.is_dir():
            raise ValueError(f"Workspace path is not a directory: {workspace_path}")

    def aggregate(self) -> WorkspaceData:
        """
        Aggregate all data from the workspace.

        Returns:
            WorkspaceData object with aggregated data
        """
        data = WorkspaceData(workspace_path=self.workspace_path)

        # Load run summary
        run_summary_path = self.workspace_path / "run_summary.json"
        if run_summary_path.exists():
            with run_summary_path.open() as f:
                data.run_summaries.append(json.load(f))

        # Load learnings
        learnings_dir = self.workspace_path / "learnings"
        if learnings_dir.exists():
            for learning_file in learnings_dir.glob("*.json"):
                with learning_file.open() as f:
                    data.learnings.append(json.load(f))

        # Load meta metrics
        meta_metrics_path = self.workspace_path / "meta_metrics.jsonl"
        if meta_metrics_path.exists():
            with meta_metrics_path.open() as f:
                for line in f:
                    if line.strip():
                        data.meta_metrics.append(json.loads(line))

        # Load phases
        phases_dir = self.workspace_path / "phases"
        if phases_dir.exists():
            for phase_file in phases_dir.glob("*.json"):
                with phase_file.open() as f:
                    phase_name = phase_file.stem
                    data.phases[phase_name] = json.load(f)

        # Load exploit attempts
        exploit_dir = self.workspace_path / "exploit_attempts"
        if exploit_dir.exists():
            for hyp_dir in exploit_dir.iterdir():
                if hyp_dir.is_dir():
                    for attempt_dir in hyp_dir.iterdir():
                        if attempt_dir.is_dir():
                            result_file = attempt_dir / "result.json"
                            if result_file.exists():
                                with result_file.open() as f:
                                    attempt_data = json.load(f)
                                    attempt_data["hypothesis_id"] = hyp_dir.name
                                    attempt_data["attempt_dir"] = str(attempt_dir)
                                    data.exploit_attempts.append(attempt_data)

        # Load logs (sample recent entries)
        logs_dir = self.workspace_path / "logs"
        if logs_dir.exists():
            # Get all log files and find the most recent one
            log_files_with_mtime = [(p, p.stat().st_mtime) for p in logs_dir.glob("*.jsonl")]
            if log_files_with_mtime:
                # Sort by modification time and get the most recent
                most_recent_log = max(log_files_with_mtime, key=lambda x: x[1])[0]
                with most_recent_log.open() as f:
                    for line in f:
                        if line.strip():
                            data.logs.append(json.loads(line))

        return data

    def aggregate_multi_workspace(self, workspace_paths: list[str | Path]) -> list[WorkspaceData]:
        """
        Aggregate data from multiple workspaces.

        Args:
            workspace_paths: List of workspace paths

        Returns:
            List of WorkspaceData objects
        """
        results = []
        for path in workspace_paths:
            aggregator = InsightsAggregator(path)
            results.append(aggregator.aggregate())
        return results
