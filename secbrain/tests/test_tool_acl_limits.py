import asyncio
from pathlib import Path

from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig


def test_per_phase_acl_limits_block_when_exceeded(tmp_path: Path) -> None:
    run_context = RunContext(
        workspace_path=tmp_path,
        dry_run=True,
        scope=ScopeConfig(domains=["example.com"], allowed_methods=["GET"]),
        program=ProgramConfig(name="Test", platform="Test"),
    )

    # Force small caps for this test
    acl = run_context.tools_config.acls.get("http_client")
    if acl is None:
        raise AssertionError("tools.yaml missing http_client acl")
    acl.max_calls_per_phase = 1
    acl.max_calls_per_run = 5

    # Set phase and ensure first call is allowed
    run_context.set_phase("recon")
    assert run_context.check_tool_acl("http_client") is True

    # Record one call in this phase
    run_context.record_tool_call("http_client")

    # Next call in same phase should now be blocked by per-phase cap
    assert run_context.check_tool_acl("http_client") is False


async def _noop() -> None:
    return None


def test_approval_mode_auto_allows_without_prompt(tmp_path: Path) -> None:
    run_context = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"], allowed_methods=["GET"]),
        program=ProgramConfig(name="Test", platform="Test"),
        approval_mode="auto",
        approval_audit_log=tmp_path / "audit.jsonl",
    )

    # Ensure http_client requires approval, auto mode should allow it
    acl = run_context.tools_config.acls.get("http_client")
    if acl is None:
        raise AssertionError("tools.yaml missing http_client acl")
    acl.require_approval = True

    # Simulate an approval request
    from datetime import datetime

    from secbrain.core.approval import ApprovalRequest, new_request_id

    req = ApprovalRequest(
        request_id=new_request_id(),
        tool_name="http_client",
        operation="GET https://example.com",
        risk_level="high",
        timestamp=datetime.now(),
    )

    resp = asyncio.run(run_context.approval_manager.request_approval(req))
    assert resp.approved is True
