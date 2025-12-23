"""Tests for Hardhat runner stub."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from secbrain.tools.hardhat_runner import HardhatRunResult, HardhatRunner


class TestHardhatRunResult:
    """Test HardhatRunResult dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic HardhatRunResult initialization."""
        result = HardhatRunResult(status="success")
        assert result.status == "success"
        assert result.profit_eth is None
        assert result.gas_used is None
        assert result.execution_trace is None
        assert result.revert_reason is None
        assert result.logs is None
        assert result.attempt_index is None

    def test_full_initialization(self) -> None:
        """Test HardhatRunResult with all fields."""
        logs = ["log1", "log2"]
        result = HardhatRunResult(
            status="reverted",
            profit_eth=1.5,
            gas_used=21000,
            execution_trace="trace data",
            revert_reason="Insufficient funds",
            logs=logs,
            attempt_index=3,
        )
        assert result.status == "reverted"
        assert result.profit_eth == 1.5
        assert result.gas_used == 21000
        assert result.execution_trace == "trace data"
        assert result.revert_reason == "Insufficient funds"
        assert result.logs == logs
        assert result.attempt_index == 3

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        result = HardhatRunResult(
            status="success",
            profit_eth=0.5,
            gas_used=15000,
            attempt_index=1,
        )
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["status"] == "success"
        assert result_dict["profit_eth"] == 0.5
        assert result_dict["gas_used"] == 15000
        assert result_dict["attempt_index"] == 1
        assert result_dict["execution_trace"] is None
        assert result_dict["revert_reason"] is None
        assert result_dict["logs"] is None


class TestHardhatRunner:
    """Test HardhatRunner stub class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test HardhatRunner initialization."""
        run_context = Mock()
        run_context.workspace_path = str(tmp_path)
        
        runner = HardhatRunner(run_context)
        assert runner.run_context == run_context
        assert runner.logger is None
        assert runner.workspace == tmp_path / "hardhat_attempts"
        assert runner.workspace.exists()

    def test_initialization_with_logger(self, tmp_path: Path) -> None:
        """Test HardhatRunner initialization with logger."""
        run_context = Mock()
        run_context.workspace_path = str(tmp_path)
        logger = Mock()
        
        runner = HardhatRunner(run_context, logger=logger)
        assert runner.logger == logger

    def test_workspace_creation(self, tmp_path: Path) -> None:
        """Test that workspace directory is created."""
        run_context = Mock()
        run_context.workspace_path = str(tmp_path)
        
        workspace_path = tmp_path / "hardhat_attempts"
        assert not workspace_path.exists()
        
        HardhatRunner(run_context)
        assert workspace_path.exists()
        assert workspace_path.is_dir()

    @pytest.mark.asyncio
    async def test_run_exploit_attempt_not_implemented(self, tmp_path: Path) -> None:
        """Test that run_exploit_attempt returns not_implemented status."""
        run_context = Mock()
        run_context.workspace_path = str(tmp_path)
        
        runner = HardhatRunner(run_context)
        
        hypothesis = {
            "vuln_type": "reentrancy",
            "confidence": 0.8,
        }
        
        result = await runner.run_exploit_attempt(
            hypothesis=hypothesis,
            rpc_url="http://localhost:8545",
        )
        
        assert isinstance(result, HardhatRunResult)
        assert result.status == "not_implemented"
        assert result.profit_eth is None
        assert result.gas_used is None
        assert result.execution_trace is None
        assert result.revert_reason == "hardhat_runner_stub"
        assert result.logs == ["Hardhat runner not yet implemented; use FoundryRunner."]
        assert result.attempt_index == 1

    @pytest.mark.asyncio
    async def test_run_exploit_attempt_with_parameters(self, tmp_path: Path) -> None:
        """Test run_exploit_attempt with all parameters."""
        run_context = Mock()
        run_context.workspace_path = str(tmp_path)
        
        runner = HardhatRunner(run_context)
        
        result = await runner.run_exploit_attempt(
            hypothesis={"vuln_type": "overflow"},
            rpc_url="http://localhost:8545",
            block_number=12345,
            chain_id=1,
            attempt_index=5,
            attack_body="function attack() {}",
        )
        
        assert result.status == "not_implemented"
        assert result.attempt_index == 5

    @pytest.mark.asyncio
    async def test_run_exploit_attempt_default_attempt_index(self, tmp_path: Path) -> None:
        """Test that default attempt_index is 1."""
        run_context = Mock()
        run_context.workspace_path = str(tmp_path)
        
        runner = HardhatRunner(run_context)
        
        result = await runner.run_exploit_attempt(
            hypothesis={},
            rpc_url=None,
        )
        
        assert result.attempt_index == 1
