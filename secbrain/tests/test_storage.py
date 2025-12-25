"""Tests for WorkspaceStorage."""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from secbrain.tools.storage import WorkspaceStorage


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def storage(temp_workspace):
    """Create and initialize a storage instance."""
    stor = WorkspaceStorage(temp_workspace, "test-run-001")
    await stor.initialize()
    yield stor
    await stor.close()


async def fetch_one(storage, cursor):
    """Helper to fetch one row from cursor, handling both aiosqlite and sqlite3."""
    if storage._sqlite_backend == "aiosqlite":
        return await cursor.fetchone()
    return await asyncio.to_thread(cursor.fetchone)


class TestWorkspaceStorageInit:
    """Test WorkspaceStorage initialization."""

    def test_init_with_path_and_run_id(self, temp_workspace) -> None:
        """Test initialization with Path and run_id."""
        storage = WorkspaceStorage(temp_workspace, "test-run")
        assert storage.workspace_path == temp_workspace
        assert storage.run_id == "test-run"
        assert storage.db_path == temp_workspace / "secbrain.db"

    def test_init_without_run_id_raises_error(self, temp_workspace) -> None:
        """Test initialization without run_id raises TypeError."""
        with pytest.raises(TypeError, match="requires run_id"):
            WorkspaceStorage(temp_workspace)

    @pytest.mark.asyncio
    async def test_initialize_creates_database(self, temp_workspace) -> None:
        """Test that initialize creates the database file."""
        storage = WorkspaceStorage(temp_workspace, "test-run")
        assert not storage.db_path.exists()

        await storage.initialize()
        assert storage.db_path.exists()

        await storage.close()

    @pytest.mark.asyncio
    async def test_execute_before_init_raises_error(self, temp_workspace) -> None:
        """Test that executing queries before initialization raises error."""
        storage = WorkspaceStorage(temp_workspace, "test-run")

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage._execute("SELECT 1")


class TestWorkspaceStorageRuns:
    """Test run tracking functionality."""

    @pytest.mark.asyncio
    async def test_start_run(self, storage) -> None:
        """Test starting a run."""
        await storage.start_run("scope-hash-123", {"key": "value"})

        # Verify run was created
        cursor = await storage._execute(
            "SELECT * FROM runs WHERE run_id = ?",
            (storage.run_id,)
        )
        row = await fetch_one(storage, cursor)

        assert row is not None
        assert row[0] == storage.run_id  # run_id
        assert row[3] == "running"  # status
        assert row[4] == "scope-hash-123"  # scope_hash

    @pytest.mark.asyncio
    async def test_end_run(self, storage) -> None:
        """Test ending a run."""
        await storage.start_run("scope-hash")
        await storage.end_run("completed")

        # Verify run was updated
        cursor = await storage._execute(
            "SELECT status, end_time FROM runs WHERE run_id = ?",
            (storage.run_id,)
        )
        row = await fetch_one(storage, cursor)

        assert row is not None
        assert row[0] == "completed"  # status
        assert row[1] is not None  # end_time

    @pytest.mark.asyncio
    async def test_start_run_with_metadata(self, storage) -> None:
        """Test starting a run with metadata."""
        metadata = {"target": "example.com", "mode": "full"}
        await storage.start_run("hash", metadata)

        cursor = await storage._execute(
            "SELECT metadata FROM runs WHERE run_id = ?",
            (storage.run_id,)
        )
        row = await fetch_one(storage, cursor)

        stored_metadata = json.loads(row[0])
        assert stored_metadata == metadata


class TestWorkspaceStorageAssets:
    """Test asset storage functionality."""

    @pytest.mark.asyncio
    async def test_save_asset(self, storage) -> None:
        """Test saving a single asset."""
        asset = {
            "id": "asset-1",
            "type": "domain",
            "value": "example.com",
            "technologies": ["nginx", "php"],
            "metadata": {"ip": "1.2.3.4"}
        }

        await storage.save_asset(asset)

        # Verify asset was saved
        cursor = await storage._execute(
            "SELECT * FROM assets WHERE id = ?",
            ("asset-1",)
        )
        row = await fetch_one(storage, cursor)

        assert row is not None
        assert row[2] == "domain"  # type
        assert row[3] == "example.com"  # value

    @pytest.mark.asyncio
    async def test_save_multiple_assets(self, storage) -> None:
        """Test saving multiple assets."""
        assets = [
            {"id": "asset-1", "type": "domain", "value": "example.com"},
            {"id": "asset-2", "type": "url", "value": "https://test.com"},
        ]

        await storage.save_assets(assets)

        # Verify both assets were saved
        cursor = await storage._execute(
            "SELECT COUNT(*) FROM assets WHERE run_id = ?",
            (storage.run_id,)
        )
        row = await fetch_one(storage, cursor)

        assert row[0] == 2

    @pytest.mark.asyncio
    async def test_get_assets(self, storage) -> None:
        """Test retrieving all assets."""
        await storage.save_asset({
            "id": "asset-1",
            "type": "domain",
            "value": "example.com",
            "technologies": ["nginx"],
            "metadata": {"test": "data"}
        })

        assets = await storage.get_assets()

        assert len(assets) == 1
        assert assets[0]["id"] == "asset-1"
        assert assets[0]["type"] == "domain"
        assert assets[0]["technologies"] == ["nginx"]
        assert assets[0]["metadata"] == {"test": "data"}

    @pytest.mark.asyncio
    async def test_get_assets_filtered_by_type(self, storage) -> None:
        """Test retrieving assets filtered by type."""
        await storage.save_assets([
            {"id": "asset-1", "type": "domain", "value": "example.com"},
            {"id": "asset-2", "type": "url", "value": "https://test.com"},
            {"id": "asset-3", "type": "domain", "value": "test.org"},
        ])

        domains = await storage.get_assets(asset_type="domain")

        assert len(domains) == 2
        assert all(a["type"] == "domain" for a in domains)

    @pytest.mark.asyncio
    async def test_save_asset_with_minimal_data(self, storage) -> None:
        """Test saving asset with minimal required data."""
        asset = {"id": "minimal", "type": "test", "value": "value"}
        await storage.save_asset(asset)

        assets = await storage.get_assets()
        assert len(assets) == 1
        assert assets[0]["id"] == "minimal"
        assert assets[0]["technologies"] == []
        assert assets[0]["metadata"] == {}


class TestWorkspaceStorageHypotheses:
    """Test hypothesis storage functionality."""

    @pytest.mark.asyncio
    async def test_save_hypothesis(self, storage) -> None:
        """Test saving a vulnerability hypothesis."""
        hypothesis = {
            "id": "hyp-1",
            "asset_id": "asset-1",
            "vuln_type": "sqli",
            "confidence": 0.85,
            "rationale": "SQL syntax in response",
            "status": "pending",
            "result": {"test": "data"}
        }

        await storage.save_hypothesis(hypothesis)

        # Verify hypothesis was saved
        cursor = await storage._execute(
            "SELECT * FROM hypotheses WHERE id = ?",
            ("hyp-1",)
        )
        row = await fetch_one(storage, cursor)

        assert row is not None
        assert row[3] == "sqli"  # vuln_type
        assert row[4] == 0.85  # confidence

    @pytest.mark.asyncio
    async def test_get_hypotheses(self, storage) -> None:
        """Test retrieving all hypotheses."""
        await storage.save_hypothesis({
            "id": "hyp-1",
            "asset_id": "asset-1",
            "vuln_type": "xss",
            "confidence": 0.7,
            "result": {"findings": [1, 2]}
        })

        hypotheses = await storage.get_hypotheses()

        assert len(hypotheses) == 1
        assert hypotheses[0]["id"] == "hyp-1"
        assert hypotheses[0]["vuln_type"] == "xss"
        assert hypotheses[0]["result"] == {"findings": [1, 2]}

    @pytest.mark.asyncio
    async def test_get_hypotheses_filtered_by_status(self, storage) -> None:
        """Test retrieving hypotheses filtered by status."""
        await storage.save_hypothesis({
            "id": "hyp-1",
            "asset_id": "asset-1",
            "vuln_type": "xss",
            "status": "pending"
        })
        await storage.save_hypothesis({
            "id": "hyp-2",
            "asset_id": "asset-2",
            "vuln_type": "sqli",
            "status": "confirmed"
        })

        pending = await storage.get_hypotheses(status="pending")

        assert len(pending) == 1
        assert pending[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_hypothesis_with_defaults(self, storage) -> None:
        """Test hypothesis creation with default values."""
        hypothesis = {
            "id": "hyp-1",
            "asset_id": "asset-1",
            "vuln_type": "test"
        }

        await storage.save_hypothesis(hypothesis)
        hypotheses = await storage.get_hypotheses()

        assert hypotheses[0]["confidence"] == 0.5
        assert hypotheses[0]["status"] == "pending"
        assert hypotheses[0]["result"] == {}


class TestWorkspaceStorageFindings:
    """Test finding storage functionality."""

    @pytest.mark.asyncio
    async def test_save_finding(self, storage) -> None:
        """Test saving a security finding."""
        finding = {
            "id": "finding-1",
            "title": "SQL Injection",
            "severity": "critical",
            "status": "confirmed",
            "vuln_type": "sqli",
            "target": "https://example.com/login",
            "description": "SQL injection in login form",
            "evidence": ["payload1", "payload2"]
        }

        await storage.save_finding(finding)

        # Verify finding was saved
        cursor = await storage._execute(
            "SELECT * FROM findings WHERE id = ?",
            ("finding-1",)
        )
        row = await fetch_one(storage, cursor)

        assert row is not None
        assert row[2] == "SQL Injection"  # title
        assert row[3] == "critical"  # severity

    @pytest.mark.asyncio
    async def test_get_findings(self, storage) -> None:
        """Test retrieving all findings."""
        await storage.save_finding({
            "id": "finding-1",
            "title": "XSS",
            "severity": "high",
            "vuln_type": "xss",
            "evidence": ["test1", "test2"]
        })

        findings = await storage.get_findings()

        assert len(findings) == 1
        assert findings[0]["id"] == "finding-1"
        assert findings[0]["title"] == "XSS"
        assert findings[0]["evidence"] == ["test1", "test2"]

    @pytest.mark.asyncio
    async def test_get_findings_filtered_by_severity(self, storage) -> None:
        """Test retrieving findings filtered by severity."""
        await storage.save_finding({
            "id": "finding-1",
            "title": "Critical Issue",
            "severity": "critical",
            "vuln_type": "test"
        })
        await storage.save_finding({
            "id": "finding-2",
            "title": "Minor Issue",
            "severity": "low",
            "vuln_type": "test"
        })

        critical = await storage.get_findings(severity="critical")

        assert len(critical) == 1
        assert critical[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_finding_with_default_status(self, storage) -> None:
        """Test finding creation with default status."""
        finding = {
            "id": "finding-1",
            "title": "Test",
            "severity": "low",
            "vuln_type": "test"
        }

        await storage.save_finding(finding)
        findings = await storage.get_findings()

        assert findings[0]["status"] == "potential"
        assert findings[0]["evidence"] == []


class TestWorkspaceStorageToolCalls:
    """Test tool call logging."""

    @pytest.mark.asyncio
    async def test_log_tool_call(self, storage) -> None:
        """Test logging a tool invocation."""
        await storage.log_tool_call(
            tool="nmap",
            action="scan",
            target="example.com",
            success=True,
            duration_ms=1234.5
        )

        # Verify tool call was logged
        cursor = await storage._execute(
            "SELECT * FROM tool_calls WHERE run_id = ?",
            (storage.run_id,)
        )
        row = await fetch_one(storage, cursor)

        assert row is not None
        assert row[2] == "nmap"  # tool
        assert row[3] == "scan"  # action
        assert row[4] == "example.com"  # target
        assert row[5] == 1  # success (True -> 1)
        assert row[6] == 1234.5  # duration_ms

    @pytest.mark.asyncio
    async def test_log_failed_tool_call(self, storage) -> None:
        """Test logging a failed tool invocation."""
        await storage.log_tool_call(
            tool="nuclei",
            action="scan",
            target="test.com",
            success=False,
            duration_ms=500.0
        )

        cursor = await storage._execute(
            "SELECT success FROM tool_calls WHERE tool = ?",
            ("nuclei",)
        )
        row = await fetch_one(storage, cursor)

        assert row[0] == 0  # success (False -> 0)


class TestWorkspaceStorageExport:
    """Test data export functionality."""

    @pytest.mark.asyncio
    async def test_export_to_json(self, storage, temp_workspace) -> None:
        """Test exporting all data to JSON files."""
        # Add some test data
        await storage.save_asset({"id": "asset-1", "type": "domain", "value": "example.com"})
        await storage.save_hypothesis({"id": "hyp-1", "asset_id": "asset-1", "vuln_type": "xss"})
        await storage.save_finding({"id": "finding-1", "title": "Test", "severity": "low", "vuln_type": "test"})

        # Export
        exports = await storage.export_to_json()

        # Verify files were created
        assert "assets" in exports
        assert "hypotheses" in exports
        assert "findings" in exports

        assert exports["assets"].exists()
        assert exports["hypotheses"].exists()
        assert exports["findings"].exists()

        # Verify content
        with exports["assets"].open() as f:
            assets = json.load(f)
            assert len(assets) == 1
            assert assets[0]["id"] == "asset-1"

    @pytest.mark.asyncio
    async def test_export_run(self, storage, temp_workspace) -> None:
        """Test exporting a complete run."""
        await storage.save_asset({"id": "asset-1", "type": "test", "value": "test"})

        output_dir = await storage.export_run()

        assert output_dir == temp_workspace
        assert (output_dir / "recon" / "assets.json").exists()

    @pytest.mark.asyncio
    async def test_export_to_custom_directory(self, storage, temp_workspace) -> None:
        """Test exporting to a custom directory."""
        custom_dir = temp_workspace / "custom_export"
        custom_dir.mkdir()

        await storage.save_asset({"id": "asset-1", "type": "test", "value": "test"})

        exports = await storage.export_to_json(output_dir=custom_dir)

        assert exports["assets"].parent.parent == custom_dir


class TestWorkspaceStorageClose:
    """Test database connection cleanup."""

    @pytest.mark.asyncio
    async def test_close(self, temp_workspace) -> None:
        """Test closing the database connection."""
        storage = WorkspaceStorage(temp_workspace, "test-run")
        await storage.initialize()

        # Should not raise an error
        await storage.close()

    @pytest.mark.asyncio
    async def test_close_without_init(self, temp_workspace) -> None:
        """Test closing before initialization."""
        storage = WorkspaceStorage(temp_workspace, "test-run")

        # Should not raise an error
        await storage.close()
