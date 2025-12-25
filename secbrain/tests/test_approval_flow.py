import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from secbrain.core.approval import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalResponse,
    new_request_id,
)
from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig
from secbrain.tools.http_client import SecBrainHTTPClient


def test_approval_manager_auto_mode(tmp_path: Path) -> None:
    """Test approval manager in auto mode."""
    manager = ApprovalManager(
        mode="auto",
        audit_log_path=tmp_path / "audit.jsonl",
    )
    req = ApprovalRequest(
        request_id="test-1",
        tool_name="test_tool",
        operation="test_op",
        risk_level="high",
        timestamp=datetime.now(UTC),
    )

    resp = __import__("asyncio").run(manager.request_approval(req))
    assert resp.approved is True
    assert resp.reason == "auto"
    assert (tmp_path / "audit.jsonl").exists()


def test_approval_manager_deny_mode(tmp_path: Path) -> None:
    """Test approval manager in deny mode."""
    manager = ApprovalManager(
        mode="deny",
        audit_log_path=tmp_path / "audit.jsonl",
    )
    req = ApprovalRequest(
        request_id="test-2",
        tool_name="test_tool",
        operation="test_op",
        risk_level="high",
        timestamp=datetime.now(UTC),
    )

    resp = __import__("asyncio").run(manager.request_approval(req))
    assert resp.approved is False
    assert resp.reason == "deny"


def test_approval_manager_unknown_mode(tmp_path: Path) -> None:
    """Test approval manager with unknown mode."""
    manager = ApprovalManager(
        mode="unknown_mode",
        audit_log_path=tmp_path / "audit.jsonl",
    )
    req = ApprovalRequest(
        request_id="test-3",
        tool_name="test_tool",
        operation="test_op",
        risk_level="high",
        timestamp=datetime.now(UTC),
    )

    resp = __import__("asyncio").run(manager.request_approval(req))
    assert resp.approved is False
    assert resp.reason == "unknown_mode:unknown_mode"


def test_new_request_id() -> None:
    """Test generating a new request ID."""
    req_id = new_request_id()
    assert isinstance(req_id, str)
    assert len(req_id) == 36  # UUID format


def test_approval_request_immutable() -> None:
    """Test that ApprovalRequest is immutable."""
    req = ApprovalRequest(
        request_id="test",
        tool_name="tool",
        operation="op",
        risk_level="low",
        timestamp=datetime.now(UTC),
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        req.request_id = "new"  # type: ignore


def test_approval_response_immutable() -> None:
    """Test that ApprovalResponse is immutable."""
    resp = ApprovalResponse(
        request_id="test",
        approved=True,
        approver="user",
        reason="reason",
        timestamp=datetime.now(UTC),
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        resp.approved = False  # type: ignore


def test_http_client_approval_deny_blocks_and_audits(tmp_path: Path) -> None:
    # Force http_client to require approval via tools.yaml by mutating config after init.
    run_context = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"], allowed_methods=["GET"]),
        program=ProgramConfig(name="Test", platform="Test"),
        approval_mode="deny",
        approval_audit_log=tmp_path / "audit.jsonl",
    )

    acl = run_context.tools_config.acls.get("http_client")
    if acl is None:
        raise AssertionError("tools.yaml missing http_client acl")
    acl.require_approval = True

    client = SecBrainHTTPClient(run_context)

    # This should be blocked before any network call by approval_mode=deny.
    resp = __import__("asyncio").run(client.get("https://example.com"))
    assert resp.success is False
    assert resp.status_code == 0
    assert resp.error is not None
    assert "Approval denied" in resp.error

    audit_path = tmp_path / "audit.jsonl"
    assert audit_path.exists()

    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1

    entry = json.loads(lines[-1])
    assert entry["request"]["tool_name"] == "http_client"
    assert entry["response"]["approved"] is False
