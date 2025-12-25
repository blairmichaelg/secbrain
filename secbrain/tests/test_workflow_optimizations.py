"""Tests for workflow optimization features."""

import asyncio
from pathlib import Path

import pytest

from secbrain.workflows.checkpoint_manager import CheckpointManager
from secbrain.workflows.hypothesis_quality_filter import HypothesisQualityFilter
from secbrain.workflows.parallel_executor import ParallelExecutor
from secbrain.workflows.performance_metrics import PerformanceMetricsCollector


class TestCheckpointManager:
    """Test checkpoint save/resume functionality."""

    def test_save_and_load_checkpoint(self, tmp_path: Path) -> None:
        """Test saving and loading a checkpoint."""
        manager = CheckpointManager(tmp_path)

        # Save checkpoint
        checkpoint_file = manager.save_checkpoint(
            run_id="test-run-123",
            current_phase="exploit",
            completed_phases=["ingest", "plan", "recon", "hypothesis"],
            phase_data={"recon": {"contracts": 5}, "hypothesis": {"hypotheses": 10}},
            metadata={"test": "data"},
        )

        assert checkpoint_file.exists()

        # Load checkpoint
        loaded = manager.load_checkpoint("test-run-123")
        assert loaded is not None
        assert loaded.run_id == "test-run-123"
        assert loaded.current_phase == "exploit"
        assert len(loaded.completed_phases) == 4
        assert "recon" in loaded.phase_data
        assert loaded.metadata["test"] == "data"

    def test_has_checkpoint(self, tmp_path: Path) -> None:
        """Test checkpoint existence check."""
        manager = CheckpointManager(tmp_path)

        assert not manager.has_checkpoint("non-existent")

        manager.save_checkpoint(
            run_id="test-run",
            current_phase="recon",
            completed_phases=["ingest"],
            phase_data={},
        )

        assert manager.has_checkpoint("test-run")

    def test_delete_checkpoint(self, tmp_path: Path) -> None:
        """Test checkpoint deletion."""
        manager = CheckpointManager(tmp_path)

        manager.save_checkpoint(
            run_id="test-run",
            current_phase="recon",
            completed_phases=["ingest"],
            phase_data={},
        )

        assert manager.has_checkpoint("test-run")
        manager.delete_checkpoint("test-run")
        assert not manager.has_checkpoint("test-run")

    def test_list_checkpoints(self, tmp_path: Path) -> None:
        """Test listing available checkpoints."""
        manager = CheckpointManager(tmp_path)

        manager.save_checkpoint("run-1", "plan", ["ingest"], {})
        manager.save_checkpoint("run-2", "recon", ["ingest", "plan"], {})

        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 2
        run_ids = [run_id for run_id, _ in checkpoints]
        assert "run-1" in run_ids
        assert "run-2" in run_ids


class TestHypothesisQualityFilter:
    """Test hypothesis quality filtering."""

    def test_high_quality_hypothesis_passes(self) -> None:
        """Test that high-quality hypothesis passes filter."""
        filter = HypothesisQualityFilter(min_confidence=0.45, min_overall_score=0.5)

        hypothesis = {
            "vuln_type": "reentrancy",
            "confidence": 0.85,
            "contract_address": "0x1234567890123456789012345678901234567890",
            "function_signature": "withdraw(uint256)",
            "function_params": ["amount"],
            "rationale": "This contract exhibits a classic reentrancy vulnerability in the withdraw "
            "function. The function transfers ETH before updating the user's balance, "
            "allowing an attacker to recursively call withdraw and drain funds.",
            "exploit_steps": ["Deploy malicious contract", "Call withdraw", "Reenter on fallback"],
        }

        score = filter.evaluate_hypothesis(hypothesis)
        assert score.pass_threshold
        assert score.overall_score > 0.7
        assert score.confidence_score >= 0.85
        assert score.completeness_score == 1.0

    def test_low_quality_hypothesis_filtered(self) -> None:
        """Test that low-quality hypothesis is filtered out."""
        filter = HypothesisQualityFilter(min_confidence=0.45, min_overall_score=0.5)

        hypothesis = {
            "vuln_type": "unknown",
            "confidence": 0.3,
            "rationale": "Might be vulnerable",  # Too short
        }

        score = filter.evaluate_hypothesis(hypothesis)
        assert not score.pass_threshold
        assert score.overall_score < 0.5
        assert len(score.reasons) > 0

    def test_filter_hypotheses_splits_correctly(self) -> None:
        """Test filtering splits hypotheses into high/low quality."""
        filter = HypothesisQualityFilter(min_confidence=0.45, min_overall_score=0.5)

        hypotheses = [
            {
                "vuln_type": "reentrancy",
                "confidence": 0.85,
                "contract_address": "0x1234567890123456789012345678901234567890",
                "function_signature": "withdraw(uint256)",
                "rationale": "Detailed explanation of reentrancy vulnerability with code references "
                "and exploit scenario. The function makes an external call before state update.",
            },
            {
                "vuln_type": "unknown",
                "confidence": 0.2,
                "rationale": "Maybe bad",
            },
            {
                "vuln_type": "overflow",
                "confidence": 0.6,
                "contract_address": "0x9876543210987654321098765432109876543210",
                "rationale": "Integer overflow in arithmetic operations without SafeMath",
            },
        ]

        high_quality, low_quality = filter.filter_hypotheses(hypotheses)

        assert len(high_quality) == 2
        assert len(low_quality) == 1
        assert low_quality[0]["vuln_type"] == "unknown"

    def test_prioritize_hypotheses_orders_correctly(self) -> None:
        """Test hypothesis prioritization by quality score."""
        filter = HypothesisQualityFilter()

        hypotheses = [
            {"vuln_type": "low", "confidence": 0.3, "rationale": "Short"},
            {"vuln_type": "high", "confidence": 0.9, "rationale": "Very detailed analysis", "contract_address": "0x123"},
            {"vuln_type": "medium", "confidence": 0.6, "rationale": "Moderate explanation"},
        ]

        prioritized = filter.prioritize_hypotheses(hypotheses)

        # Should be ordered by quality score
        assert prioritized[0]["vuln_type"] == "high"
        assert prioritized[2]["vuln_type"] == "low"


class TestParallelExecutor:
    """Test parallel task execution."""

    @pytest.mark.asyncio
    async def test_execute_tasks_parallel(self) -> None:
        """Test executing multiple tasks in parallel."""
        executor = ParallelExecutor(max_concurrent=2)

        async def task1() -> dict:
            await asyncio.sleep(0.1)
            return {"result": "task1"}

        async def task2() -> dict:
            await asyncio.sleep(0.1)
            return {"result": "task2"}

        tasks = {"task1": task1, "task2": task2}
        results = await executor.execute_tasks(tasks)

        assert len(results) == 2
        assert results["task1"].success
        assert results["task1"].data["result"] == "task1"
        assert results["task2"].success
        assert results["task2"].data["result"] == "task2"

    @pytest.mark.asyncio
    async def test_task_timeout_handling(self) -> None:
        """Test that tasks timeout correctly."""
        executor = ParallelExecutor(max_concurrent=2)

        async def slow_task() -> dict:
            await asyncio.sleep(5)
            return {"result": "done"}

        tasks = {"slow": slow_task}
        results = await executor.execute_tasks(tasks, timeout_seconds=0.5)

        assert len(results) == 1
        assert not results["slow"].success
        assert "Timeout" in results["slow"].error

    @pytest.mark.asyncio
    async def test_task_error_isolation(self) -> None:
        """Test that one failing task doesn't stop others."""
        executor = ParallelExecutor(max_concurrent=2)

        async def failing_task() -> dict:
            raise ValueError("Task failed")

        async def success_task() -> dict:
            return {"result": "success"}

        tasks = {"fail": failing_task, "success": success_task}
        results = await executor.execute_tasks(tasks)

        assert len(results) == 2
        assert not results["fail"].success
        assert "Task failed" in results["fail"].error
        assert results["success"].success


class TestPerformanceMetricsCollector:
    """Test performance metrics collection."""

    def test_phase_tracking(self) -> None:
        """Test tracking individual phases."""
        collector = PerformanceMetricsCollector("test-run")

        collector.start_phase("recon")
        collector.record_api_call()
        collector.record_cache_hit()
        collector.complete_phase(success=True)

        collector.start_phase("hypothesis")
        collector.record_api_call()
        collector.record_cache_miss()
        collector.record_error()
        collector.complete_phase(success=False)

        metrics = collector.complete_workflow()

        assert len(metrics.phases) == 2
        assert metrics.phases["recon"].success
        assert metrics.phases["recon"].api_calls == 1
        assert metrics.phases["recon"].cache_hits == 1
        assert not metrics.phases["hypothesis"].success
        assert metrics.phases["hypothesis"].errors == 1

    def test_aggregate_metrics(self) -> None:
        """Test workflow-level aggregate metrics."""
        collector = PerformanceMetricsCollector("test-run")

        collector.start_phase("phase1")
        collector.record_api_call()
        collector.record_api_call()
        collector.record_cache_hit()
        collector.complete_phase(success=True)

        collector.start_phase("phase2")
        collector.record_api_call()
        collector.record_cache_miss()
        collector.complete_phase(success=True)

        metrics = collector.complete_workflow()

        assert metrics.total_api_calls == 3
        assert metrics.total_cache_hits == 1
        assert metrics.total_cache_misses == 1
        assert metrics.successful_phases == 2
        assert metrics.failed_phases == 0
        assert 0 < metrics.cache_hit_rate < 1

    def test_get_summary(self) -> None:
        """Test getting current metrics summary."""
        collector = PerformanceMetricsCollector("test-run")

        collector.start_phase("recon")
        collector.record_api_call()

        summary = collector.get_summary()

        assert summary["run_id"] == "test-run"
        assert summary["current_phase"] == "recon"
        assert summary["total_api_calls"] == 1
