"""Tests for insights aggregator."""

import json
from pathlib import Path

import pytest

from secbrain.insights.aggregator import InsightsAggregator, WorkspaceData


class TestWorkspaceData:
    """Test WorkspaceData dataclass."""

    def test_basic_initialization(self, tmp_path: Path) -> None:
        """Test basic WorkspaceData initialization."""
        data = WorkspaceData(workspace_path=tmp_path)
        assert data.workspace_path == tmp_path
        assert data.run_summaries == []
        assert data.learnings == []
        assert data.meta_metrics == []
        assert data.phases == {}
        assert data.exploit_attempts == []
        assert data.logs == []

    def test_total_runs_empty(self, tmp_path: Path) -> None:
        """Test total_runs with no data."""
        data = WorkspaceData(workspace_path=tmp_path)
        assert data.total_runs == 0

    def test_total_runs_with_data(self, tmp_path: Path) -> None:
        """Test total_runs with data."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            run_summaries=[{"id": 1}, {"id": 2}, {"id": 3}],
        )
        assert data.total_runs == 3

    def test_successful_runs_empty(self, tmp_path: Path) -> None:
        """Test successful_runs with no data."""
        data = WorkspaceData(workspace_path=tmp_path)
        assert data.successful_runs == 0

    def test_successful_runs_all_successful(self, tmp_path: Path) -> None:
        """Test successful_runs when all runs are successful."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            run_summaries=[
                {"id": 1, "success": True},
                {"id": 2, "success": True},
            ],
        )
        assert data.successful_runs == 2

    def test_successful_runs_mixed(self, tmp_path: Path) -> None:
        """Test successful_runs with mixed results."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            run_summaries=[
                {"id": 1, "success": True},
                {"id": 2, "success": False},
                {"id": 3, "success": True},
                {"id": 4, "success": False},
            ],
        )
        assert data.successful_runs == 2

    def test_total_hypotheses_empty(self, tmp_path: Path) -> None:
        """Test total_hypotheses with no data."""
        data = WorkspaceData(workspace_path=tmp_path)
        assert data.total_hypotheses == 0

    def test_total_hypotheses_with_data(self, tmp_path: Path) -> None:
        """Test total_hypotheses with data."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[
                {"hypotheses_count": 5},
                {"hypotheses_count": 3},
                {"hypotheses_count": 7},
            ],
        )
        assert data.total_hypotheses == 15

    def test_total_hypotheses_missing_keys(self, tmp_path: Path) -> None:
        """Test total_hypotheses with missing keys."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[
                {"hypotheses_count": 5},
                {},
                {"hypotheses_count": 3},
            ],
        )
        assert data.total_hypotheses == 8

    def test_total_attempts_empty(self, tmp_path: Path) -> None:
        """Test total_attempts with no data."""
        data = WorkspaceData(workspace_path=tmp_path)
        assert data.total_attempts == 0

    def test_total_attempts_with_data(self, tmp_path: Path) -> None:
        """Test total_attempts with data."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[
                {"attempts_count": 10},
                {"attempts_count": 5},
                {"attempts_count": 8},
            ],
        )
        assert data.total_attempts == 23

    def test_total_attempts_missing_keys(self, tmp_path: Path) -> None:
        """Test total_attempts with missing keys."""
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[
                {"attempts_count": 10},
                {},
                {"attempts_count": 5},
            ],
        )
        assert data.total_attempts == 15


class TestInsightsAggregator:
    """Test InsightsAggregator class."""

    def test_initialization_valid_path(self, tmp_path: Path) -> None:
        """Test initialization with valid workspace path."""
        aggregator = InsightsAggregator(tmp_path)
        assert aggregator.workspace_path == tmp_path

    def test_initialization_string_path(self, tmp_path: Path) -> None:
        """Test initialization with string path."""
        aggregator = InsightsAggregator(str(tmp_path))
        assert aggregator.workspace_path == tmp_path

    def test_initialization_nonexistent_path(self) -> None:
        """Test initialization with nonexistent path raises error."""
        with pytest.raises(ValueError, match="Workspace path does not exist"):
            InsightsAggregator("/nonexistent/path")

    def test_aggregate_empty_workspace(self, tmp_path: Path) -> None:
        """Test aggregate with empty workspace."""
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert isinstance(data, WorkspaceData)
        assert data.workspace_path == tmp_path
        assert data.run_summaries == []
        assert data.learnings == []
        assert data.meta_metrics == []
        assert data.exploit_attempts == []

    def test_aggregate_with_run_summary(self, tmp_path: Path) -> None:
        """Test aggregate with run summary file."""
        run_summary = {"id": "run-1", "success": True, "duration": 300}
        run_summary_path = tmp_path / "run_summary.json"
        run_summary_path.write_text(json.dumps(run_summary))
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.run_summaries) == 1
        assert data.run_summaries[0] == run_summary

    def test_aggregate_with_learnings(self, tmp_path: Path) -> None:
        """Test aggregate with learnings directory."""
        learnings_dir = tmp_path / "learnings"
        learnings_dir.mkdir()
        
        learning1 = {"type": "pattern", "value": "reentrancy"}
        learning2 = {"type": "tool", "value": "slither"}
        
        (learnings_dir / "learning1.json").write_text(json.dumps(learning1))
        (learnings_dir / "learning2.json").write_text(json.dumps(learning2))
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.learnings) == 2
        assert learning1 in data.learnings
        assert learning2 in data.learnings

    def test_aggregate_with_meta_metrics(self, tmp_path: Path) -> None:
        """Test aggregate with meta metrics file."""
        metric1 = {"hypotheses_count": 5, "attempts_count": 10}
        metric2 = {"hypotheses_count": 3, "attempts_count": 7}
        
        meta_path = tmp_path / "meta_metrics.jsonl"
        meta_path.write_text(
            json.dumps(metric1) + "\n" + json.dumps(metric2) + "\n"
        )
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.meta_metrics) == 2
        assert metric1 in data.meta_metrics
        assert metric2 in data.meta_metrics

    def test_aggregate_with_exploit_attempts(self, tmp_path: Path) -> None:
        """Test aggregate with exploit attempts directory."""
        attempts_dir = tmp_path / "exploit_attempts"
        attempts_dir.mkdir()
        
        # Create nested structure: exploit_attempts/hyp1/attempt1/result.json
        hyp_dir = attempts_dir / "hyp1"
        hyp_dir.mkdir()
        attempt_dir = hyp_dir / "attempt1"
        attempt_dir.mkdir()
        
        attempt1 = {"id": 1, "status": "success", "profit": 1.5}
        (attempt_dir / "result.json").write_text(json.dumps(attempt1))
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.exploit_attempts) == 1
        assert data.exploit_attempts[0]["id"] == 1
        assert data.exploit_attempts[0]["status"] == "success"
        assert data.exploit_attempts[0]["hypothesis_id"] == "hyp1"

    def test_aggregate_complete_workspace(self, tmp_path: Path) -> None:
        """Test aggregate with complete workspace data."""
        # Create run summary
        run_summary = {"id": "run-1", "success": True}
        (tmp_path / "run_summary.json").write_text(json.dumps(run_summary))
        
        # Create learnings
        learnings_dir = tmp_path / "learnings"
        learnings_dir.mkdir()
        (learnings_dir / "learning1.json").write_text(json.dumps({"type": "test"}))
        
        # Create meta metrics
        (tmp_path / "meta_metrics.jsonl").write_text(json.dumps({"hypotheses_count": 5}) + "\n")
        
        # Create exploit attempts
        attempts_dir = tmp_path / "exploit_attempts"
        attempts_dir.mkdir()
        hyp_dir = attempts_dir / "hyp1"
        hyp_dir.mkdir()
        attempt_dir = hyp_dir / "attempt1"
        attempt_dir.mkdir()
        (attempt_dir / "result.json").write_text(json.dumps({"id": 1}))
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.run_summaries) == 1
        assert len(data.learnings) == 1
        assert len(data.meta_metrics) == 1
        assert len(data.exploit_attempts) == 1
        assert data.total_runs == 1
        assert data.successful_runs == 1
        assert data.total_hypotheses == 5

    def test_aggregate_with_phases(self, tmp_path: Path) -> None:
        """Test aggregate with phases directory."""
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        
        phase1 = {"name": "recon", "duration": 120}
        phase2 = {"name": "exploit", "duration": 300}
        
        (phases_dir / "recon.json").write_text(json.dumps(phase1))
        (phases_dir / "exploit.json").write_text(json.dumps(phase2))
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.phases) == 2
        assert data.phases["recon"] == phase1
        assert data.phases["exploit"] == phase2

    def test_aggregate_with_logs(self, tmp_path: Path) -> None:
        """Test aggregate with logs directory."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        
        log_entry1 = {"level": "info", "message": "Starting"}
        log_entry2 = {"level": "debug", "message": "Processing"}
        
        log_path = logs_dir / "run.jsonl"
        log_path.write_text(
            json.dumps(log_entry1) + "\n" + json.dumps(log_entry2) + "\n"
        )
        
        aggregator = InsightsAggregator(tmp_path)
        data = aggregator.aggregate()
        
        assert len(data.logs) == 2
        assert log_entry1 in data.logs
        assert log_entry2 in data.logs

    def test_aggregate_multi_workspace(self, tmp_path: Path) -> None:
        """Test aggregate_multi_workspace."""
        # Create two workspaces
        ws1 = tmp_path / "workspace1"
        ws1.mkdir()
        ws2 = tmp_path / "workspace2"
        ws2.mkdir()
        
        # Add data to each
        (ws1 / "run_summary.json").write_text(json.dumps({"id": 1, "success": True}))
        (ws2 / "run_summary.json").write_text(json.dumps({"id": 2, "success": False}))
        
        aggregator = InsightsAggregator(ws1)
        results = aggregator.aggregate_multi_workspace([ws1, ws2])
        
        assert len(results) == 2
        assert isinstance(results[0], WorkspaceData)
        assert isinstance(results[1], WorkspaceData)
        assert results[0].run_summaries[0]["id"] == 1
        assert results[1].run_summaries[0]["id"] == 2
