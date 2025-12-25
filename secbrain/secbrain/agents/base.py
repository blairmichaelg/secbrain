"""Base agent class for SecBrain."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog

    from secbrain.core.context import RunContext
    from secbrain.models.base import ModelClient
    from secbrain.tools.perplexity_research import PerplexityResearch
    from secbrain.tools.storage import WorkspaceStorage


@dataclass
class AgentResult:
    """Result from an agent execution."""

    agent: str
    phase: str
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    next_actions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    requires_approval: bool = False
    approval_reason: str = ""
    reasoning_chain: list[dict[str, Any]] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for all SecBrain agents.

    Each agent:
    - Exposes run(run_context, ...)
    - Uses worker models by default
    - Calls advisor only at key checkpoints
    - Calls research via perplexity at defined substeps
    """

    name: str = "base_agent"
    phase: str = "unknown"

    def __init__(
        self,
        run_context: RunContext,
        worker_model: ModelClient | None = None,
        advisor_model: ModelClient | None = None,
        research_client: PerplexityResearch | None = None,
        storage: WorkspaceStorage | None = None,
        logger: structlog.stdlib.BoundLogger | None = None,
    ):
        self.run_context = run_context
        self.worker_model = worker_model or run_context.worker_model
        self.advisor_model = advisor_model or run_context.advisor_model
        self.research_client = research_client
        self.storage = storage
        self.logger = logger
        self._reasoning_chain: list[dict[str, Any]] = []

        # Initialize research orchestrator
        self.research_orch: ResearchOrchestrator | None = None
        if self.research_client:
            from secbrain.agents.research_orchestrator import ResearchOrchestrator

            self.research_orch = ResearchOrchestrator(
                run_context=self.run_context,
                research_client=self.research_client,
            )

    def _check_kill_switch(self) -> bool:
        """Check if kill-switch is activated."""
        return self.run_context.is_killed()

    def _log(self, event: str, **kwargs: Any) -> None:
        """Log an event if logger is available."""
        if self.logger:
            if "agent" not in kwargs:
                kwargs["agent"] = self.name
            if "phase" not in kwargs:
                kwargs["phase"] = self.phase
            self.logger.info(event, **kwargs)

    def _record_reasoning(self, step: str, content: str, result: Any | None = None) -> None:
        """Record a ReAct-style reasoning step."""
        entry = {"step": step, "content": content}
        if result is not None:
            entry["result"] = result
        self._reasoning_chain.append(entry)

    def _drain_reasoning_chain(self) -> list[dict[str, Any]]:
        chain = list(self._reasoning_chain)
        self._reasoning_chain.clear()
        return chain

    def _log_error(self, error: str, **kwargs: Any) -> None:
        """Log an error if logger is available."""
        if self.logger:
            if "agent" not in kwargs:
                kwargs["agent"] = self.name
            if "phase" not in kwargs:
                kwargs["phase"] = self.phase
            self.logger.error(error, **kwargs)

    async def _call_worker(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Call the worker model."""
        if not self.worker_model:
            return "[NO WORKER MODEL] " + prompt[:100]

        cache_key: str | None = None
        try:
            if hasattr(self.run_context, "get_cached_llm"):
                raw_key = f"{system or ''}|||{prompt}"
                cache_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
                cached = self.run_context.get_cached_llm(cache_key)
                if cached is not None:
                    return cached
        except Exception:
            cache_key = None

        response = await self.worker_model.generate(
            prompt=prompt,
            system=system,
            **kwargs,
        )
        content = response.content

        if cache_key:
            with contextlib.suppress(Exception):
                self.run_context.cache_llm(cache_key, content)

        return content

    async def _call_advisor(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Call the advisor model for critical decisions."""
        if not self.advisor_model:
            return "[NO ADVISOR MODEL] " + prompt[:100]

        self._log("advisor_call", prompt_preview=prompt[:100])

        response = await self.advisor_model.generate(
            prompt=prompt,
            system=system,
            **kwargs,
        )
        return response.content

    async def _research(
        self,
        question: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Call the research client."""
        if not self.research_client:
            return {"answer": "[NO RESEARCH CLIENT]", "sources": [], "cached": False}

        self._log("research_call", question=question[:100])

        cache_key = f"{question}|||{context}"
        cached = None
        try:
            cached = self.run_context.get_cached_research(cache_key)
        except Exception:
            cached = None
        if cached is not None:
            return {**cached, "cached": True}

        result = await self.research_client.ask_research(
            question=question,
            context=context,
            run_context=self.run_context,
        )
        with contextlib.suppress(Exception):
            self.run_context.cache_research(cache_key, result)
        result.setdefault("cached", False)
        return result

    @abstractmethod
    async def run(self, **kwargs: Any) -> AgentResult:
        """
        Execute the agent's main logic.

        Returns:
            AgentResult with success status and data
        """

    def _success(
        self,
        message: str = "",
        data: dict[str, Any] | None = None,
        next_actions: list[str] | None = None,
    ) -> AgentResult:
        """Create a success result."""
        return AgentResult(
            agent=self.name,
            phase=self.phase,
            success=True,
            message=message,
            data=data or {},
            next_actions=next_actions or [],
        )

    def _failure(
        self,
        message: str = "",
        errors: list[str] | None = None,
    ) -> AgentResult:
        """Create a failure result."""
        return AgentResult(
            agent=self.name,
            phase=self.phase,
            success=False,
            message=message,
            errors=errors or [message],
        )

    def _needs_approval(
        self,
        reason: str,
        data: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Create a result that requires human approval."""
        return AgentResult(
            agent=self.name,
            phase=self.phase,
            success=True,
            message=f"Approval required: {reason}",
            data=data or {},
            requires_approval=True,
            approval_reason=reason,
        )

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------
    class HealthStatus(Enum):
        """Health check status."""

        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"

    @dataclass
    class HealthCheck:
        """Health check result."""

        component: str
        status: BaseAgent.HealthStatus
        timestamp: datetime
        message: str = ""
        metrics: dict[str, Any] | None = None

    async def health_check(self) -> BaseAgent.HealthCheck:
        """Perform health check on agent (models, storage, kill switch)."""
        checks: list[tuple[str, BaseAgent.HealthStatus, str]] = []

        # Kill switch
        if self._check_kill_switch():
            checks.append(("kill_switch", BaseAgent.HealthStatus.UNHEALTHY, "Kill switch activated"))

        # Worker model availability
        if self.worker_model:
            try:
                await asyncio.wait_for(
                    self.worker_model.generate("test", system="reply 'ok'"),
                    timeout=5.0,
                )
                checks.append(("worker_model", BaseAgent.HealthStatus.HEALTHY, ""))
            except TimeoutError:
                checks.append(("worker_model", BaseAgent.HealthStatus.DEGRADED, "Slow response"))
            except Exception as exc:  # pragma: no cover - external service
                checks.append(("worker_model", BaseAgent.HealthStatus.UNHEALTHY, str(exc)))

        # Storage availability
        if self.storage:
            try:
                await self.storage.ping()
                checks.append(("storage", BaseAgent.HealthStatus.HEALTHY, ""))
            except Exception as exc:  # pragma: no cover - external service
                checks.append(("storage", BaseAgent.HealthStatus.UNHEALTHY, str(exc)))

        statuses = [status for _, status, _ in checks]
        if BaseAgent.HealthStatus.UNHEALTHY in statuses:
            overall = BaseAgent.HealthStatus.UNHEALTHY
        elif BaseAgent.HealthStatus.DEGRADED in statuses:
            overall = BaseAgent.HealthStatus.DEGRADED
        else:
            overall = BaseAgent.HealthStatus.HEALTHY

        return BaseAgent.HealthCheck(
            component=self.name,
            status=overall,
            timestamp=datetime.now(UTC),
            message="; ".join(f"{comp}: {msg}" for comp, _, msg in checks if msg),
            metrics={
                "checks": len(checks),
                "healthy": sum(1 for _, s, _ in checks if s == BaseAgent.HealthStatus.HEALTHY),
                "degraded": sum(1 for _, s, _ in checks if s == BaseAgent.HealthStatus.DEGRADED),
                "unhealthy": sum(1 for _, s, _ in checks if s == BaseAgent.HealthStatus.UNHEALTHY),
            },
        )
