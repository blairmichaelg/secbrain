#!/usr/bin/env python3
"""Unit tests for contract reconnaissance functionality."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from secbrain.agents.recon_agent import ReconAgent
from secbrain.core.context import ContractConfig, ProgramConfig, RunContext, ScopeConfig


class TestContractRecon:
    """Test cases for contract reconnaissance functionality."""

    @pytest.fixture
    def mock_run_context(self, tmp_path):
        """Create a mock RunContext for testing."""
        foundry_root = tmp_path / "test_forge_project"
        foundry_root.mkdir(parents=True, exist_ok=True)
        scope = ScopeConfig(
            contracts=[
                ContractConfig(
                    address="0x00000000000000000000000000000000000049af",
                    name="ZeroExV4Adapter",
                    foundry_profile="contract_ZeroExV4Adapter_49af",
                    chain_id=1,
                    verified=True
                ),
                ContractConfig(
                    address="0x00000000000000000000000000000000000096ef",
                    name="NoDepegOnRedeemSharesForSpecificAssetsPolicy",
                    foundry_profile="contract_NoDepegOnRedeemSharesForSpecificAssetsPolicy_96ef",
                    chain_id=1,
                    verified=True
                )
            ],
            foundry_root=foundry_root
        )

        program = ProgramConfig(
            name="Test Program",
            platform="Test"
        )

        return RunContext(
            workspace_path=Path("/tmp/test_workspace"),
            dry_run=True,
            scope=scope,
            program=program
        )


    @pytest.fixture
    def recon_agent(self, mock_run_context):
        """Create a ReconAgent for testing."""
        # Create a proper mock storage with async methods
        mock_storage = MagicMock()
        mock_storage.save_asset = AsyncMock()

        return ReconAgent(
            run_context=mock_run_context,
            storage=mock_storage,
            research_client=MagicMock()
        )

    def test_contract_recon_dry_run(self, recon_agent, mock_run_context):
        """Test contract reconnaissance in dry-run mode."""
        # Run the contract recon
        result = asyncio.run(recon_agent._recon_contracts(mock_run_context.scope.contracts))

        # Verify the result structure
        assert result.success is True
        assert "assets" in result.data
        assert "contracts_count" in result.data
        assert "compiled_count" in result.data
        assert "failed_count" in result.data
        assert "foundry_root" in result.data

        # Verify all contracts were "simulated compiled"
        assets = result.data["assets"]
        assert len(assets) == 2

        for asset in assets:
            assert asset["type"] == "contract"
            assert asset["status"] == "simulated_compiled"
            assert "metadata" in asset
            assert asset["metadata"]["verified"] is True

        # Verify counts
        assert result.data["contracts_count"] == 2
        assert result.data["compiled_count"] == 2
        assert result.data["failed_count"] == 0

    @patch('subprocess.run')
    @patch('asyncio.create_subprocess_exec')
    def test_contract_recon_real_mode_success(self, mock_subprocess_exec, mock_subprocess_run, recon_agent, mock_run_context):
        """Test contract reconnaissance in real mode with successful compilation."""
        # Mock forge --version
        mock_version = MagicMock()
        mock_version.returncode = 0
        mock_version.stdout = "forge 0.2.0"
        mock_subprocess_run.return_value = mock_version
        # Mock successful forge build via async subprocess
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"Compiler run successful", b""))
        mock_proc.returncode = 0
        mock_subprocess_exec.return_value = mock_proc

        # Set dry_run to False
        mock_run_context.dry_run = False

        # Run the contract recon
        result = asyncio.run(recon_agent._recon_contracts(mock_run_context.scope.contracts))

        # Verify the result
        assert result.success is True
        assert result.data["compiled_count"] == 2
        assert result.data["failed_count"] == 0

        # Verify forge was called for each contract
        assert mock_subprocess_exec.call_count == len(mock_run_context.scope.contracts)

    @patch('subprocess.run')
    @patch('asyncio.create_subprocess_exec')
    def test_contract_recon_compilation_failure(self, mock_subprocess_exec, mock_subprocess_run, recon_agent, mock_run_context):
        """Test contract reconnaissance with compilation failure."""
        # Mock forge --version
        mock_version = MagicMock()
        mock_version.returncode = 0
        mock_version.stdout = "forge 0.2.0"
        mock_subprocess_run.return_value = mock_version
        # Mock build failure via async subprocess
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"Compiling...", b"Error: Compiler run failed"))
        mock_proc.returncode = 1
        mock_subprocess_exec.return_value = mock_proc

        # Set dry_run to False
        mock_run_context.dry_run = False

        # Run the contract recon
        result = asyncio.run(recon_agent._recon_contracts(mock_run_context.scope.contracts))

        # Verify the result
        assert result.success is True  # Recon still succeeds, but with failures recorded
        assert result.data["compiled_count"] == 0
        assert result.data["failed_count"] == 2

        # Verify assets show failure status
        assets = result.data["assets"]
        for asset in assets:
            assert asset["status"] == "compilation_failed"
            assert "error" in asset["metadata"]

    def test_recon_agent_run_with_contracts(self, recon_agent, mock_run_context):
        """Test the full ReconAgent.run method with contracts."""
        result = asyncio.run(recon_agent.run())

        # Should choose contract recon path
        assert result.success is True
        assert result.data["contracts_count"] == 2
        assert result.data["compiled_count"] == 2
        assert result.next_actions == ["static"]

    def test_recon_agent_run_no_scope(self, mock_run_context):
        """Test ReconAgent.run with empty scope."""
        # Create agent with empty scope
        empty_scope = ScopeConfig()
        mock_run_context.scope = empty_scope

        agent = ReconAgent(run_context=mock_run_context)

        result = asyncio.run(agent.run())

        # Should fail with no scope error
        assert result.success is False
        assert "No domains or contracts in scope" in result.errors[0]


if __name__ == "__main__":
    pytest.main([__file__])
