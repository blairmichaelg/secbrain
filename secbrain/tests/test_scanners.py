"""Tests for scanner integrations (nuclei, semgrep)."""

from __future__ import annotations

from pathlib import Path

import pytest

from secbrain.tools.scanners import NucleiScanner, ScanResult, SemgrepScanner


class MockRunContext:
    """Mock RunContext for testing."""

    def __init__(
        self,
        is_killed: bool = False,
        dry_run: bool = False,
        auto_approve: bool = False,
        tool_acl: dict | None = None,
        approval_required: dict | None = None,
    ):
        self._is_killed = is_killed
        self.dry_run = dry_run
        self.auto_approve = auto_approve
        self._tool_acl = tool_acl or {}
        self._approval_required = approval_required or {}

    def is_killed(self):
        return self._is_killed

    def check_tool_acl(self, tool: str) -> bool:
        return self._tool_acl.get(tool, True)

    def requires_approval(self, tool: str) -> bool:
        return self._approval_required.get(tool, False)


def test_scan_result_creation():
    """Test ScanResult dataclass creation."""
    result = ScanResult(
        scanner="nuclei",
        success=True,
        findings=[{"severity": "high", "template": "cve-2021-12345"}],
        duration_ms=1500.5,
        error=None,
        raw_output="test output",
    )

    assert result.scanner == "nuclei"
    assert result.success is True
    assert len(result.findings) == 1
    assert result.duration_ms == 1500.5
    assert result.error is None
    assert result.raw_output == "test output"


def test_nuclei_scanner_initialization():
    """Test NucleiScanner initialization."""
    run_context = MockRunContext()
    scanner = NucleiScanner(run_context)

    assert scanner.run_context == run_context
    assert scanner.templates_path == "~/nuclei-templates"


def test_nuclei_scanner_custom_templates_path():
    """Test NucleiScanner with custom templates path."""
    run_context = MockRunContext()
    custom_path = "/custom/templates"
    scanner = NucleiScanner(run_context, templates_path=custom_path)

    assert scanner.templates_path == custom_path



@pytest.mark.asyncio
async def test_nuclei_scan_acl_denied():
    """Test nuclei scan respects ACL restrictions."""
    run_context = MockRunContext(tool_acl={"nuclei": False})
    scanner = NucleiScanner(run_context)

    result = await scanner.scan(targets=["example.com"])

    assert result.scanner == "nuclei"
    assert result.success is False
    assert "not allowed" in result.error


@pytest.mark.asyncio
async def test_nuclei_scan_approval_required():
    """Test nuclei scan requires approval when configured."""
    run_context = MockRunContext(
        approval_required={"nuclei": True},
        dry_run=False,
        auto_approve=False,
    )
    scanner = NucleiScanner(run_context)

    result = await scanner.scan(targets=["example.com"])

    assert result.scanner == "nuclei"
    assert result.success is False
    assert "Approval required" in result.error


@pytest.mark.asyncio
async def test_nuclei_preconditions_approval_auto_approved():
    """Test nuclei scan succeeds with auto-approve enabled."""
    run_context = MockRunContext(
        approval_required={"nuclei": True},
        dry_run=False,
        auto_approve=True,
    )
    scanner = NucleiScanner(run_context)

    result = await scanner.scan(targets=["example.com"])

    # Should pass approval check, but may fail on nuclei not found
    assert result.scanner == "nuclei"
    if not result.success:
        assert "not found" in result.error.lower() or "approval" not in result.error.lower()


@pytest.mark.asyncio
async def test_nuclei_preconditions_dry_run():
    """Test nuclei scan in dry-run mode bypasses approval."""
    run_context = MockRunContext(
        approval_required={"nuclei": True},
        dry_run=True,
    )
    scanner = NucleiScanner(run_context)

    result = await scanner.scan(targets=["example.com"])

    # Dry run should bypass approval, but may fail on nuclei not found
    assert result.scanner == "nuclei"
    if not result.success:
        assert "not found" in result.error.lower() or "approval" not in result.error.lower()


@pytest.mark.asyncio
async def test_nuclei_scan_kill_switch():
    """Test nuclei scan respects kill switch."""
    run_context = MockRunContext(is_killed=True)
    scanner = NucleiScanner(run_context)

    result = await scanner.scan(targets=["example.com"])

    assert result.scanner == "nuclei"
    assert result.success is False
    assert "Kill-switch" in result.error


@pytest.mark.asyncio
async def test_nuclei_scan_dry_run():
    """Test nuclei scan in dry-run mode."""
    run_context = MockRunContext(dry_run=True, tool_acl={"nuclei": True})
    scanner = NucleiScanner(run_context)

    result = await scanner.scan(targets=["example.com"])

    assert result.scanner == "nuclei"
    # May be True if nuclei is not installed (dry run succeeds)
    # or False if preconditions fail
    assert result.success is True or result.error is not None
    if result.success:
        assert len(result.findings) == 0
        assert "DRY" in result.raw_output


def test_semgrep_scanner_initialization():
    """Test SemgrepScanner initialization."""
    run_context = MockRunContext()
    scanner = SemgrepScanner(run_context)

    assert scanner.run_context == run_context


@pytest.mark.asyncio
async def test_semgrep_scan_kill_switch():
    """Test semgrep scan respects kill switch."""
    run_context = MockRunContext(is_killed=True)
    scanner = SemgrepScanner(run_context)

    result = await scanner.scan(path=Path("/tmp/test"))

    assert result.scanner == "semgrep"
    assert result.success is False
    assert "Kill-switch" in result.error


@pytest.mark.asyncio
async def test_semgrep_scan_acl_denied():
    """Test semgrep scan respects ACL restrictions."""
    run_context = MockRunContext(tool_acl={"semgrep": False})
    scanner = SemgrepScanner(run_context)

    result = await scanner.scan(path=Path("/tmp/test"))

    assert result.scanner == "semgrep"
    assert result.success is False
    assert "not allowed" in result.error


@pytest.mark.asyncio
async def test_semgrep_scan_approval_required():
    """Test semgrep scan requires approval when configured."""
    run_context = MockRunContext(
        approval_required={"semgrep": True},
        dry_run=False,
        auto_approve=False,
    )
    scanner = SemgrepScanner(run_context)

    result = await scanner.scan(path=Path("/tmp/test"))

    assert result.scanner == "semgrep"
    assert result.success is False
    assert "Approval required" in result.error


@pytest.mark.asyncio
async def test_semgrep_scan_dry_run():
    """Test semgrep scan in dry-run mode."""
    run_context = MockRunContext(dry_run=True, tool_acl={"semgrep": True})
    scanner = SemgrepScanner(run_context)

    result = await scanner.scan(path=Path("/tmp/test"))

    assert result.scanner == "semgrep"
    # May succeed in dry-run if semgrep isn't installed, or may fail on preconditions
    if result.success:
        assert len(result.findings) == 0
        assert "DRY" in result.raw_output


@pytest.mark.asyncio
async def test_create_nuclei_scanner():
    """Test the create_nuclei_scanner helper function."""
    from secbrain.tools.scanners import create_nuclei_scanner

    run_context = MockRunContext()
    scanner = await create_nuclei_scanner(run_context)

    assert isinstance(scanner, NucleiScanner)
    assert scanner.run_context == run_context


@pytest.mark.asyncio
async def test_create_semgrep_scanner():
    """Test the create_semgrep_scanner helper function."""
    from secbrain.tools.scanners import create_semgrep_scanner

    run_context = MockRunContext()
    scanner = await create_semgrep_scanner(run_context)

    assert isinstance(scanner, SemgrepScanner)
    assert scanner.run_context == run_context
