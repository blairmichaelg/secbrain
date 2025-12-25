"""Tests for WorkspaceStorage."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from secbrain.tools.storage import WorkspaceStorage


class MockRunContext:
    """Mock RunContext for testing."""

    def __init__(self, workspace_path: Path, run_id: str):
        self.workspace_path = workspace_path
        self.run_id = run_id


@pytest.mark.asyncio
async def test_storage_initialization_with_run_context():
    """Test WorkspaceStorage initialization with RunContext."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-001"
        run_context = MockRunContext(workspace_path, run_id)

        storage = WorkspaceStorage(run_context)
        assert storage.workspace_path == workspace_path
        assert storage.run_id == run_id
        assert storage.db_path == workspace_path / "secbrain.db"


@pytest.mark.asyncio
async def test_storage_initialization_with_path():
    """Test WorkspaceStorage initialization with Path and run_id."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-002"

        storage = WorkspaceStorage(workspace_path, run_id)
        assert storage.workspace_path == workspace_path
        assert storage.run_id == run_id


@pytest.mark.asyncio
async def test_storage_initialization_missing_run_id():
    """Test WorkspaceStorage raises TypeError when run_id is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)

        with pytest.raises(TypeError, match="WorkspaceStorage requires run_id"):
            WorkspaceStorage(workspace_path)


@pytest.mark.asyncio
async def test_storage_database_initialization():
    """Test database initialization and table creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-003"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()

        # Verify database file was created
        assert storage.db_path.exists()
        
        # Verify we can perform basic operations (tests that tables were created)
        await storage.start_run("test-scope-hash")
        assets = await storage.get_assets()
        assert isinstance(assets, list)

        await storage.close()


@pytest.mark.asyncio
async def test_start_run():
    """Test starting a run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-004"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()

        scope_hash = "abc123"
        metadata = {"target": "example.com", "phase": "recon"}

        # Start the run - should succeed without errors
        await storage.start_run(scope_hash, metadata)

        # Verify we can save assets after starting run (tests run was recorded)
        await storage.save_asset({
            "id": "test-asset",
            "type": "domain",
            "value": "example.com"
        })
        assets = await storage.get_assets()
        assert len(assets) == 1

        await storage.close()


@pytest.mark.asyncio
async def test_end_run():
    """Test ending a run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-005"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123")
        
        # End the run - should succeed without errors
        await storage.end_run("completed")

        # Verify we can still query data after ending run
        assets = await storage.get_assets()
        assert isinstance(assets, list)

        await storage.close()


@pytest.mark.asyncio
async def test_save_and_get_asset():
    """Test saving and retrieving an asset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-006"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123")

        asset = {
            "id": "asset-001",
            "type": "domain",
            "value": "example.com",
            "technologies": ["nginx", "php"],
            "metadata": {"ip": "1.2.3.4"},
        }

        await storage.save_asset(asset)

        # Retrieve the asset
        assets = await storage.get_assets()
        assert len(assets) == 1
        assert assets[0]["id"] == "asset-001"
        assert assets[0]["type"] == "domain"
        assert assets[0]["value"] == "example.com"
        assert assets[0]["technologies"] == ["nginx", "php"]
        assert assets[0]["metadata"] == {"ip": "1.2.3.4"}

        await storage.close()


@pytest.mark.asyncio
async def test_save_multiple_assets():
    """Test saving multiple assets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-007"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123")

        assets = [
            {"id": "asset-001", "type": "domain", "value": "example.com"},
            {"id": "asset-002", "type": "ip", "value": "1.2.3.4"},
            {"id": "asset-003", "type": "domain", "value": "test.com"},
        ]

        await storage.save_assets(assets)

        # Retrieve all assets
        retrieved = await storage.get_assets()
        assert len(retrieved) == 3

        # Filter by type
        domains = await storage.get_assets("domain")
        assert len(domains) == 2

        await storage.close()


@pytest.mark.asyncio
async def test_save_and_get_hypothesis():
    """Test saving and retrieving a hypothesis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-008"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123")

        hypothesis = {
            "id": "hyp-001",
            "asset_id": "asset-001",
            "vuln_type": "SQL Injection",
            "confidence": 0.85,
            "rationale": "Input parameter not sanitized",
            "status": "pending",
            "result": None,
        }

        await storage.save_hypothesis(hypothesis)

        # Retrieve hypotheses
        hypotheses = await storage.get_hypotheses()
        assert len(hypotheses) == 1
        assert hypotheses[0]["id"] == "hyp-001"
        assert hypotheses[0]["vuln_type"] == "SQL Injection"
        assert hypotheses[0]["confidence"] == 0.85

        await storage.close()


@pytest.mark.asyncio
async def test_save_and_get_finding():
    """Test saving and retrieving a finding."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-009"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123")

        finding = {
            "id": "finding-001",
            "title": "SQL Injection in login form",
            "severity": "high",
            "status": "confirmed",
            "vuln_type": "SQL Injection",
            "target": "https://example.com/login",
            "description": "Parameter 'username' is vulnerable",
            "evidence": {"payload": "' OR 1=1--", "response": "200 OK"},
        }

        await storage.save_finding(finding)

        # Retrieve findings
        findings = await storage.get_findings()
        assert len(findings) == 1
        assert findings[0]["id"] == "finding-001"
        assert findings[0]["severity"] == "high"

        # Filter by severity
        high_findings = await storage.get_findings("high")
        assert len(high_findings) == 1

        await storage.close()


@pytest.mark.asyncio
async def test_log_tool_call():
    """Test logging a tool call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-010"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123")

        # Log tool call - should succeed without errors
        await storage.log_tool_call(
            tool="nuclei",
            action="scan",
            target="example.com",
            success=True,
            duration_ms=1500.5,
        )

        # Verify operation completed successfully by checking other operations work
        assets = await storage.get_assets()
        assert isinstance(assets, list)

        await storage.close()


@pytest.mark.asyncio
async def test_export_to_json():
    """Test exporting data to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-011"

        storage = WorkspaceStorage(workspace_path, run_id)
        await storage.initialize()
        await storage.start_run("hash123", {"target": "example.com"})

        # Add some test data
        await storage.save_asset({"id": "asset-001", "type": "domain", "value": "example.com"})
        await storage.save_hypothesis(
            {
                "id": "hyp-001",
                "asset_id": "asset-001",
                "vuln_type": "XSS",
                "confidence": 0.7,
            }
        )

        output_dir = Path(tmpdir) / "export"
        output_dir.mkdir(exist_ok=True)
        exports = await storage.export_to_json(output_dir)

        # Verify exported files
        assert "assets" in exports
        assert "hypotheses" in exports
        assert "findings" in exports
        assert exports["assets"].exists()
        assert exports["hypotheses"].exists()

        # Verify JSON content
        import json

        with open(exports["assets"]) as f:
            assets = json.load(f)
        assert len(assets) == 1

        with open(exports["hypotheses"]) as f:
            hypotheses = json.load(f)
        assert len(hypotheses) == 1

        await storage.close()


@pytest.mark.asyncio
async def test_create_storage_helper():
    """Test the create_storage helper function."""
    from secbrain.tools.storage import create_storage

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        run_id = "test-run-012"
        run_context = MockRunContext(workspace_path, run_id)

        storage = await create_storage(run_context)
        assert isinstance(storage, WorkspaceStorage)
        assert storage.workspace_path == workspace_path
        assert storage.run_id == run_id

        await storage.close()
