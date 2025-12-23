from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    tool_name: str
    operation: str
    risk_level: str
    timestamp: datetime


@dataclass(frozen=True)
class ApprovalResponse:
    request_id: str
    approved: bool
    approver: str
    reason: str | None
    timestamp: datetime


class ApprovalManager:
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
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def request_approval(self, req: ApprovalRequest) -> ApprovalResponse:
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
            approval_event=ApprovalEvent(
                approved=approved,
                approver=self.approver,
                reason=reason,
                timestamp=datetime.now(timezone.utc),
            ),
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
