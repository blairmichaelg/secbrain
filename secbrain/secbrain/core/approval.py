from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    """Immutable request payload for approval checks."""

    request_id: str
    tool_name: str
    operation: str
    risk_level: str
    timestamp: datetime


@dataclass(frozen=True)
class ApprovalResponse:
    """Immutable response payload describing an approval decision."""

    request_id: str
    approved: bool
    approver: str
    reason: str | None
    timestamp: datetime


class ApprovalManager:
    """Coordinate human-in-the-loop approval flows for sensitive tool use."""

    def __init__(
        self,
        *,
        mode: str,
        audit_log_path: Path,
        approver: str = "operator",
    ) -> None:
        self.mode = mode
        self.audit_log_path = audit_log_path
        self.approver = approver

    def _append_audit(self, entry: dict[str, Any]) -> None:
        """Persist an audit record as JSONL."""
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def request_approval(self, req: ApprovalRequest) -> ApprovalResponse:
        """Request approval for a high-risk operation.

        This method implements the approval workflow based on the configured mode:

        - ``auto``: Automatically approves every request.
        - ``deny``: Automatically denies every request.
        - ``ask``: Prompts the operator interactively for each request.

        All requests and responses are logged to the audit log for compliance.
        Timestamps are stored in UTC to ensure consistency across systems.

        Args:
            req: The approval request containing the operation metadata.

        Returns:
            ApprovalResponse containing the decision and accompanying metadata.

        Raises:
            OSError: If writing to the audit log fails. The exception is propagated
                after logging, but the approval result is still returned to callers.

        Example:
            >>> manager = ApprovalManager(mode="ask", audit_log_path=Path("audit.jsonl"))
            >>> request = ApprovalRequest(
            ...     request_id="123",
            ...     tool_name="http_client",
            ...     operation="GET https://example.com",
            ...     risk_level="medium",
            ...     timestamp=datetime.now(timezone.utc),
            ... )
            >>> response = await manager.request_approval(request)
            >>> print(response.approved)
            True
        """
        approved = False
        reason: str | None = None

        mode = (self.mode or "deny").lower()
        if mode == "auto":
            approved = True
            reason = "auto"
        elif mode == "deny":
            approved = False
            reason = "deny"
        elif mode == "ask":
            from secbrain.cli.approval_ui import interactive_approval_prompt

            approved, reason = await interactive_approval_prompt(req)
        else:
            approved = False
            reason = f"unknown_mode:{mode}"

        resp = ApprovalResponse(
            request_id=req.request_id,
            approved=approved,
            approver=self.approver,
            reason=reason,
            timestamp=datetime.now(UTC),
        )

        self._append_audit(
            {
                "request": {
                    "request_id": req.request_id,
                    "tool_name": req.tool_name,
                    "operation": req.operation,
                    "risk_level": req.risk_level,
                    "timestamp": req.timestamp.isoformat(),
                },
                "response": {
                    "request_id": resp.request_id,
                    "approved": resp.approved,
                    "approver": resp.approver,
                    "reason": resp.reason,
                    "timestamp": resp.timestamp.isoformat(),
                },
            }
        )

        return resp


def new_request_id() -> str:
    return str(uuid.uuid4())
