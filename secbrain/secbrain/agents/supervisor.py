"""Supervisor agent - orchestrates phases and enforces controls."""

from __future__ import annotations

from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates the overall workflow.

    Responsibilities:
    - Orchestrates phases
    - Enforces scope, ACLs, rate limits
    - Monitors kill-switch
    - Gates human approval for sensitive actions
    """

    name = "supervisor"
    phase = "orchestration"

    async def run(self, **kwargs: Any) -> AgentResult:
        """
        Run supervisor checks before/after agent execution.

        This is typically called by the orchestrator, not directly.
        """
        action = kwargs.get("action", "check")

        if action == "pre_phase":
            return await self._pre_phase_check(kwargs.get("phase_name", ""))
        if action == "post_phase":
            return await self._post_phase_check(kwargs.get("phase_name", ""), kwargs.get("result"))
        if action == "approval":
            return await self._handle_approval(kwargs.get("request"))
        return await self._status_check()

    async def _status_check(self) -> AgentResult:
        """Check overall system status."""
        if self._check_kill_switch():
            return self._failure("Kill-switch activated", ["Run terminated by kill-switch"])

        # Check rate limits
        tool_counts = self.run_context.session.tool_call_counts
        total_calls = sum(tool_counts.values())

        return self._success(
            message="System operational",
            data={
                "run_id": self.run_context.run_id,
                "current_phase": self.run_context.session.current_phase,
                "phases_completed": self.run_context.session.phases_completed,
                "total_tool_calls": total_calls,
                "dry_run": self.run_context.dry_run,
            },
        )

    async def _pre_phase_check(self, phase_name: str) -> AgentResult:
        """Check before starting a phase."""
        self._log("pre_phase_check", phase=phase_name)

        # Kill-switch check
        if self._check_kill_switch():
            return self._failure(f"Cannot start phase {phase_name}: kill-switch activated")

        # Check if phase should run
        if not self.run_context.should_run_phase(phase_name):
            return self._failure(f"Phase {phase_name} not in requested phases")

        # Update current phase
        self.run_context.set_phase(phase_name)

        return self._success(
            message=f"Phase {phase_name} cleared to start",
            data={"phase": phase_name},
        )

    async def _post_phase_check(
        self,
        phase_name: str,
        result: AgentResult | None,
    ) -> AgentResult:
        """Check after completing a phase."""
        self._log("post_phase_check", phase=phase_name, success=result.success if result else False)

        if self._check_kill_switch():
            return self._failure("Run stopped by kill-switch after phase completion")

        if result and not result.success:
            # Log phase failure but don't necessarily stop
            self._log_error(f"Phase {phase_name} failed", errors=result.errors)

        # Determine next actions
        next_phase = self._get_next_phase(phase_name)

        return self._success(
            message=f"Phase {phase_name} completed",
            data={
                "phase": phase_name,
                "phase_success": result.success if result else False,
            },
            next_actions=[next_phase] if next_phase else [],
        )

    async def _handle_approval(self, request: dict[str, Any] | None) -> AgentResult:
        """Handle approval request for sensitive actions."""
        if not request:
            return self._failure("No approval request provided")

        action = request.get("action", "unknown")
        reason = request.get("reason", "")
        risk_level = request.get("risk_level", "medium")

        self._log("approval_request", action=action, reason=reason, risk=risk_level)

        # In a real implementation, this would prompt the user
        # For now, auto-approve in dry-run mode, reject otherwise
        if self.run_context.dry_run:
            return self._success(
                message=f"[DRY-RUN] Auto-approved: {action}",
                data={"approved": True, "action": action},
            )

        # For real runs, require explicit approval
        return self._needs_approval(
            reason=f"{action}: {reason}",
            data={"action": action, "risk_level": risk_level},
        )

    def _get_next_phase(self, current_phase: str) -> str | None:
        """Determine the next phase in the workflow."""
        phase_order = [
            "ingest",
            "plan",
            "recon",
            "hypothesis",
            "exploit",
            "static",
            "triage",
            "report",
        ]

        try:
            idx = phase_order.index(current_phase)
            if idx + 1 < len(phase_order):
                next_phase = phase_order[idx + 1]
                if self.run_context.should_run_phase(next_phase):
                    return next_phase
                # Skip to next available phase
                for p in phase_order[idx + 2:]:
                    if self.run_context.should_run_phase(p):
                        return p
        except ValueError:
            pass

        return None

    async def enforce_scope(self, target: str) -> bool:
        """Check if a target is within scope."""
        return self.run_context.check_scope(target)

    async def check_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed in the current phase."""
        return self.run_context.check_tool_acl(tool_name)

    async def request_approval(
        self,
        action: str,
        reason: str,
        risk_level: str = "medium",
    ) -> AgentResult:
        """Request approval for a sensitive action."""
        return await self._handle_approval({
            "action": action,
            "reason": reason,
            "risk_level": risk_level,
        })
