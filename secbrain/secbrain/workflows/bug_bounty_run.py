"""Bug bounty workflow orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog

    from secbrain.core.context import RunContext

from secbrain.agents.exploit_agent import ExploitAgent
from secbrain.agents.meta_learning_agent import MetaLearningAgent
from secbrain.agents.planner_agent import PlannerAgent
from secbrain.agents.program_ingest_agent import ProgramIngestAgent
from secbrain.agents.recon_agent import ReconAgent
from secbrain.agents.reporting_agent import ReportingAgent
from secbrain.agents.static_analysis_agent import StaticAnalysisAgent
from secbrain.agents.supervisor import SupervisorAgent
from secbrain.agents.triage_agent import TriageAgent
from secbrain.agents.vuln_hypothesis_agent import VulnHypothesisAgent
from secbrain.core.logging import log_event, log_phase_transition
from secbrain.workflows.checkpoint_manager import CheckpointManager
from secbrain.workflows.hypothesis_quality_filter import HypothesisQualityFilter
from secbrain.workflows.performance_metrics import PerformanceMetricsCollector


class Phase(str, Enum):
    """Workflow phases."""

    INGEST = "ingest"
    PLAN = "plan"
    RECON = "recon"
    HYPOTHESIS = "hypothesis"
    EXPLOIT = "exploit"
    STATIC = "static"
    TRIAGE = "triage"
    REPORT = "report"
    META = "meta"


@dataclass
class PhaseResult:
    """Result from a phase execution."""

    phase: Phase
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """Result from the full workflow."""

    run_id: str
    success: bool
    phases_completed: list[Phase] = field(default_factory=list)
    phases_failed: list[Phase] = field(default_factory=list)
    phase_results: dict[str, PhaseResult] = field(default_factory=dict)
    total_duration_seconds: float = 0.0
    findings_count: int = 0
    reports_generated: int = 0
    errors: list[str] = field(default_factory=list)


# Phase graph: defines allowed transitions
PHASE_GRAPH: dict[Phase, list[Phase]] = {
    Phase.INGEST: [Phase.PLAN],
    Phase.PLAN: [Phase.RECON],
    Phase.RECON: [Phase.HYPOTHESIS],
    Phase.HYPOTHESIS: [Phase.EXPLOIT],
    Phase.EXPLOIT: [Phase.STATIC, Phase.TRIAGE],  # Can go to static or skip to triage
    Phase.STATIC: [Phase.TRIAGE],
    Phase.TRIAGE: [Phase.REPORT],
    Phase.REPORT: [Phase.META],
    Phase.META: [],  # Terminal phase
}

# Immediate prerequisites required before entering a phase
PHASE_PREREQS: dict[Phase, list[Phase]] = {
    Phase.PLAN: [Phase.INGEST],
    Phase.RECON: [Phase.PLAN],
    Phase.HYPOTHESIS: [Phase.RECON],
    Phase.EXPLOIT: [Phase.HYPOTHESIS],
    Phase.STATIC: [Phase.EXPLOIT],
    Phase.TRIAGE: [Phase.EXPLOIT],
    Phase.REPORT: [Phase.TRIAGE],
    Phase.META: [Phase.REPORT],
}


class BugBountyWorkflow:
    """
    Main workflow orchestrator for bug bounty runs.

    Responsibilities:
    - Executes phases in order according to phase graph
    - Manages phase transitions with supervisor checks
    - Handles kill-switch and approvals
    - Collects and passes data between phases
    """

    def __init__(
        self,
        run_context: RunContext,
        logger: structlog.stdlib.BoundLogger | None = None,
        enable_checkpoints: bool = True,
        enable_quality_filter: bool = True,
    ):
        self.run_context = run_context
        self.logger = logger
        self.phase_data: dict[str, dict[str, Any]] = {}

        # Initialize optimization features
        self.enable_checkpoints = enable_checkpoints
        self.enable_quality_filter = enable_quality_filter

        # Initialize checkpoint manager
        self.checkpoint_manager = CheckpointManager(run_context.workspace_path) if enable_checkpoints else None

        # Initialize performance metrics collector
        self.metrics_collector = PerformanceMetricsCollector(run_context.run_id)

        # Initialize hypothesis quality filter
        self.quality_filter = HypothesisQualityFilter(
            min_confidence=0.45,
            min_overall_score=0.5,
        ) if enable_quality_filter else None

        # Initialize agents
        self._init_agents()

    def _init_agents(self) -> None:
        """Initialize all agents."""
        common_kwargs = {
            "run_context": self.run_context,
            "logger": self.logger,
        }

        self.supervisor = SupervisorAgent(**common_kwargs)
        self.ingest_agent = ProgramIngestAgent(**common_kwargs)
        self.planner_agent = PlannerAgent(**common_kwargs)
        self.recon_agent = ReconAgent(**common_kwargs)
        self.hypothesis_agent = VulnHypothesisAgent(**common_kwargs)
        self.exploit_agent = ExploitAgent(**common_kwargs)
        self.static_agent = StaticAnalysisAgent(**common_kwargs)
        self.triage_agent = TriageAgent(**common_kwargs)
        self.reporting_agent = ReportingAgent(**common_kwargs)
        self.meta_agent = MetaLearningAgent(**common_kwargs)

        # Map phases to agents
        self.phase_agents: dict[Phase, Any] = {
            Phase.INGEST: self.ingest_agent,
            Phase.PLAN: self.planner_agent,
            Phase.RECON: self.recon_agent,
            Phase.HYPOTHESIS: self.hypothesis_agent,
            Phase.EXPLOIT: self.exploit_agent,
            Phase.STATIC: self.static_agent,
            Phase.TRIAGE: self.triage_agent,
            Phase.REPORT: self.reporting_agent,
            Phase.META: self.meta_agent,
        }

    async def run(
        self,
        phases: list[str] | None = None,
        source_path: Path | None = None,
        rpc_url: str | None = None,
        block_number: int | None = None,
        chain_id: int | None = None,
        exploit_iterations: int | None = None,
        profit_threshold: float | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """
        Execute the bug bounty workflow.

        Args:
            phases: Optional list of phases to run. If None, runs all phases.
            source_path: Optional path to source code for static analysis.

        Returns:
            WorkflowResult with all phase outcomes
        """
        start_time = datetime.now(UTC)
        result = WorkflowResult(run_id=self.run_context.run_id, success=True)

        # Check for existing checkpoint
        checkpoint_loaded = False
        checkpoint = None
        if self.checkpoint_manager and self.checkpoint_manager.has_checkpoint(self.run_context.run_id):
            checkpoint = self.checkpoint_manager.load_checkpoint(self.run_context.run_id)
            if checkpoint:
                log_event(
                    self.logger,
                    "checkpoint_loaded",
                    run_id=self.run_context.run_id,
                    current_phase=checkpoint.current_phase,
                    completed_phases=checkpoint.completed_phases,
                )
                # Restore phase data
                self.phase_data = checkpoint.phase_data
                result.phases_completed = [Phase(p) for p in checkpoint.completed_phases]
                checkpoint_loaded = True

        # Determine phases to run
        phases_to_run = self._determine_phases(phases)

        # Skip completed phases if resuming from checkpoint
        if checkpoint_loaded and checkpoint:
            phases_to_run = [p for p in phases_to_run if p not in checkpoint.completed_phases]

        try:
            completed_phase_names = {p.value for p in result.phases_completed}
            self._validate_phase_sequence(phases_to_run, completed_phase_names)
        except ValueError as err:
            result.success = False
            result.errors.append(str(err))
            return result

        log_event(
            self.logger,
            "workflow_started",
            run_id=self.run_context.run_id,
            phases=phases_to_run,
            dry_run=self.run_context.dry_run,
            checkpoint_loaded=checkpoint_loaded,
        )

        try:
            # Execute phases in order
            current_phase = phases_to_run[0] if phases_to_run else None

            while current_phase:
                # Start phase metrics tracking
                self.metrics_collector.start_phase(current_phase)

                if self.run_context.is_killed():
                    log_event(self.logger, "workflow_killed", phase=current_phase)
                    result.errors.append(f"Kill-switch activated during {current_phase}")
                    result.success = False
                    self.metrics_collector.complete_phase(success=False)
                    break

                # Run supervisor pre-check
                pre_check = await self.supervisor.run(
                    action="pre_phase",
                    phase_name=current_phase,
                )

                if not pre_check.success:
                    result.phases_failed.append(Phase(current_phase))
                    result.errors.extend(pre_check.errors)
                    self.metrics_collector.complete_phase(success=False)
                    if self.checkpoint_manager:
                        self.checkpoint_manager.save_checkpoint(
                            run_id=self.run_context.run_id,
                            current_phase=current_phase,
                            completed_phases=[p.value for p in result.phases_completed],
                            phase_data=self.phase_data,
                            metadata={
                                "reason": "pre_check_failed",
                                "phase": current_phase,
                                "errors": pre_check.errors,
                            },
                        )
                    break

                # Execute phase
                phase_result = await self._execute_phase(
                    Phase(current_phase),
                    source_path=source_path,
                    rpc_url=rpc_url,
                    block_number=block_number,
                    chain_id=chain_id,
                    exploit_iterations=exploit_iterations,
                    profit_threshold=profit_threshold,
                )

                result.phase_results[current_phase] = phase_result

                if phase_result.success:
                    result.phases_completed.append(Phase(current_phase))
                    self.phase_data[current_phase] = phase_result.data
                    self.metrics_collector.complete_phase(success=True, metadata=phase_result.data)

                    # Save checkpoint after successful phase
                    if self.checkpoint_manager:
                        self.checkpoint_manager.save_checkpoint(
                            run_id=self.run_context.run_id,
                            current_phase=current_phase,
                            completed_phases=[p.value for p in result.phases_completed],
                            phase_data=self.phase_data,
                            metadata={"timestamp": datetime.now(UTC).isoformat()},
                        )
                else:
                    result.phases_failed.append(Phase(current_phase))
                    result.errors.extend(phase_result.errors)
                    self.metrics_collector.complete_phase(success=False)
                    self.metrics_collector.record_error()
                    # Don't necessarily stop on failure - let supervisor decide
                    if current_phase in ["ingest", "plan"]:
                        # Critical phases - must stop
                        result.success = False
                        break

                # Run supervisor post-check
                await self.supervisor.run(
                    action="post_phase",
                    phase_name=current_phase,
                )

                # Determine next phase
                next_phase = self._get_next_phase(current_phase, phases_to_run)
                current_phase = next_phase

        except Exception as e:
            log_event(self.logger, "workflow_error", error=str(e))
            result.errors.append(str(e))
            result.success = False
            self.metrics_collector.record_error()

        # Complete performance metrics tracking
        workflow_metrics = self.metrics_collector.complete_workflow()

        # Calculate totals
        end_time = datetime.now(UTC)
        result.total_duration_seconds = (end_time - start_time).total_seconds()

        # Extract summary metrics
        triage_data = self.phase_data.get("triage", {})
        result.findings_count = len(triage_data.get("findings", []))
        economic = triage_data.get("economic", {})

        report_data = self.phase_data.get("report", {})
        result.reports_generated = len(report_data.get("reports", []))

        # Meta metrics
        meta_metrics = metrics or {}
        exploit_data = self.phase_data.get("exploit", {})
        hypothesis_data = self.phase_data.get("hypothesis", {})
        hypotheses = hypothesis_data.get("hypotheses", [])
        missing_targets = hypothesis_data.get("missing_targets", {})
        hypotheses_with_concrete_target = len(
            [h for h in hypotheses if h.get("contract_address") and h.get("function_signature")]
        )

        # Add hypothesis quality metrics if filtering was enabled
        quality_metrics = {}
        if self.quality_filter and hypotheses:
            high_quality, low_quality = self.quality_filter.filter_hypotheses(hypotheses)
            quality_metrics = {
                "total_hypotheses": len(hypotheses),
                "high_quality_hypotheses": len(high_quality),
                "low_quality_hypotheses": len(low_quality),
                "quality_filter_enabled": True,
            }

        meta_metrics.update({
            "hypotheses_count": len(hypotheses),
            "hypotheses_with_concrete_target": hypotheses_with_concrete_target,
            "missing_targets": missing_targets,
            "attempts_count": len(exploit_data.get("attempts", [])),
            "attempts_with_profit": len([a for a in exploit_data.get("attempts", []) if a.get("profit_eth")]),
            "economic_decision": economic.get("decision"),
            "total_duration_seconds": result.total_duration_seconds,
            "performance": workflow_metrics.to_dict(),
            "quality_metrics": quality_metrics,
        })

        log_event(
            self.logger,
            "workflow_completed",
            run_id=self.run_context.run_id,
            success=result.success,
            phases_completed=[p.value for p in result.phases_completed],
            findings=result.findings_count,
            duration=result.total_duration_seconds,
            performance_summary=workflow_metrics.to_dict(),
        )

        # Persist run summary artifact
        summary_path = self.run_context.workspace_path / "run_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "success": result.success,
                    "phases_completed": [p.value for p in result.phases_completed],
                    "phases_failed": [p.value for p in result.phases_failed],
                    "findings_count": result.findings_count,
                    "reports_generated": result.reports_generated,
                    "duration_seconds": result.total_duration_seconds,
                    "errors": result.errors,
                    "economic": economic,
                    "attempts_count": len(exploit_data.get("attempts", [])),
                    "meta_metrics": meta_metrics,
                },
                indent=2,
            )
        )

        # Persist per-phase artifacts for easy manual validation
        phases_dir = self.run_context.workspace_path / "phases"
        phases_dir.mkdir(parents=True, exist_ok=True)
        for phase_name, pr in result.phase_results.items():
            (phases_dir / f"{phase_name}.json").write_text(
                json.dumps(
                    {
                        "run_id": result.run_id,
                        "phase": phase_name,
                        "success": pr.success,
                        "duration_seconds": pr.duration_seconds,
                        "errors": pr.errors,
                        "data": pr.data,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                    indent=2,
                )
            )

        # Append meta metrics to workspace log for longitudinal tracking
        meta_log_path = self.run_context.workspace_path / "meta_metrics.jsonl"
        with meta_log_path.open("a") as f:
            f.write(json.dumps(meta_metrics) + "\n")

        # Save performance metrics
        perf_metrics_path = self.run_context.workspace_path / "performance_metrics.json"
        perf_metrics_path.write_text(json.dumps(workflow_metrics.to_dict(), indent=2))

        # Clean up checkpoint if workflow completed successfully
        if result.success and self.checkpoint_manager:
            self.checkpoint_manager.delete_checkpoint(self.run_context.run_id)

        return result

    def _validate_phase_sequence(self, pending_phases: list[str], completed: set[str]) -> None:
        """
        Ensure pending phases respect dependency ordering when resuming or running subsets.

        Args:
            pending_phases: Ordered list of phase names that will be executed.
            completed: Set of phase names already completed.

        Raises:
            ValueError: If a pending phase is missing required prerequisites.
        """
        seen = set(completed)
        for phase_name in pending_phases:
            try:
                phase = Phase(phase_name)
            except ValueError as exc:
                raise ValueError(f"Unknown phase '{phase_name}' in execution list") from exc

            missing = [
                prereq.value
                for prereq in PHASE_PREREQS.get(phase, [])
                if prereq.value not in seen
            ]
            if missing:
                raise ValueError(
                    f"Cannot execute phase '{phase_name}' before required phase(s): {', '.join(missing)}"
                )
            seen.add(phase_name)

    def _determine_phases(self, phases: list[str] | None) -> list[str]:
        """Determine which phases to run."""
        all_phases = [p.value for p in Phase]

        if phases is None:
            return all_phases

        # Filter to requested phases in correct order
        return [p for p in all_phases if p in phases]

    def _get_next_phase(
        self,
        current: str,
        allowed_phases: list[str],
    ) -> str | None:
        """Get the next phase to execute."""
        try:
            current_phase = Phase(current)
            next_phases = PHASE_GRAPH.get(current_phase, [])

            for next_phase in next_phases:
                if next_phase.value in allowed_phases:
                    return next_phase.value

            return None
        except ValueError:
            return None

    async def _execute_phase(
        self,
        phase: Phase,
        source_path: Path | None = None,
        rpc_url: str | None = None,
        block_number: int | None = None,
        chain_id: int | None = None,
        exploit_iterations: int | None = None,
        profit_threshold: float | None = None,
    ) -> PhaseResult:
        """Execute a single phase."""
        start_time = datetime.now(UTC)

        log_phase_transition(
            self.logger,
            from_phase=self.run_context.session.current_phase,
            to_phase=phase.value,
        )

        agent = self.phase_agents.get(phase)
        if not agent:
            return PhaseResult(
                phase=phase,
                success=False,
                errors=[f"No agent for phase {phase}"],
            )

        try:
            # Build kwargs based on phase
            kwargs = self._build_phase_kwargs(
                phase,
                source_path,
                rpc_url=rpc_url,
                block_number=block_number,
                chain_id=chain_id,
                exploit_iterations=exploit_iterations,
                profit_threshold=profit_threshold,
            )

            # Execute agent
            agent_result = await agent.run(**kwargs)

            # Post-process hypothesis results with quality filtering
            if phase == Phase.HYPOTHESIS and self.quality_filter and agent_result.success:
                hypotheses = agent_result.data.get("hypotheses", [])
                if hypotheses:
                    # Apply quality filtering
                    high_quality, low_quality = self.quality_filter.filter_hypotheses(hypotheses)

                    # Log filtering results
                    log_event(
                        self.logger,
                        "hypothesis_quality_filtering",
                        total=len(hypotheses),
                        high_quality=len(high_quality),
                        low_quality=len(low_quality),
                        filter_rate=len(low_quality) / len(hypotheses) if hypotheses else 0,
                    )

                    # Update agent result with filtered hypotheses
                    # Keep all hypotheses but mark quality for downstream use
                    agent_result.data["hypotheses_all"] = hypotheses
                    agent_result.data["hypotheses"] = high_quality
                    agent_result.data["hypotheses_filtered_out"] = low_quality
                    agent_result.data["quality_filtering_applied"] = True

            duration = (datetime.now(UTC) - start_time).total_seconds()

            return PhaseResult(
                phase=phase,
                success=agent_result.success,
                data=agent_result.data,
                duration_seconds=duration,
                errors=agent_result.errors,
            )

        except Exception as e:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            return PhaseResult(
                phase=phase,
                success=False,
                duration_seconds=duration,
                errors=[str(e)],
            )

    def _build_phase_kwargs(
        self,
        phase: Phase,
        source_path: Path | None,
        rpc_url: str | None = None,
        block_number: int | None = None,
        chain_id: int | None = None,
        exploit_iterations: int | None = None,
        profit_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Build keyword arguments for a phase based on previous results."""
        kwargs: dict[str, Any] = {}

        if phase == Phase.PLAN:
            kwargs["ingest_data"] = self.phase_data.get("ingest", {})

        elif phase == Phase.RECON:
            kwargs["plan_data"] = self.phase_data.get("plan", {})

        elif phase == Phase.HYPOTHESIS:
            kwargs["recon_data"] = self.phase_data.get("recon", {})

        elif phase == Phase.EXPLOIT:
            kwargs["hypothesis_data"] = self.phase_data.get("hypothesis", {})
            kwargs["rpc_url"] = rpc_url
            kwargs["block_number"] = block_number
            kwargs["chain_id"] = chain_id
            kwargs["iterations"] = exploit_iterations
            kwargs["profit_threshold"] = profit_threshold

        elif phase == Phase.STATIC:
            kwargs["exploit_data"] = self.phase_data.get("exploit", {})
            kwargs["source_path"] = source_path

        elif phase == Phase.TRIAGE:
            kwargs["exploit_data"] = self.phase_data.get("exploit", {})
            kwargs["static_data"] = self.phase_data.get("static", {})

        elif phase == Phase.REPORT:
            kwargs["triage_data"] = self.phase_data.get("triage", {})

        elif phase == Phase.META:
            kwargs["ingest_data"] = self.phase_data.get("ingest", {})
            kwargs["plan_data"] = self.phase_data.get("plan", {})
            kwargs["recon_data"] = self.phase_data.get("recon", {})
            kwargs["hypothesis_data"] = self.phase_data.get("hypothesis", {})
            kwargs["exploit_data"] = self.phase_data.get("exploit", {})
            kwargs["triage_data"] = self.phase_data.get("triage", {})
            kwargs["report_data"] = self.phase_data.get("report", {})

        return kwargs


async def run_bug_bounty(
    run_context: RunContext,
    phases: list[str] | None = None,
    source_path: Path | None = None,
    logger: Any = None,
    rpc_url: str | None = None,
    block_number: int | None = None,
    chain_id: int | None = None,
    exploit_iterations: int | None = None,
    profit_threshold: float | None = None,
) -> WorkflowResult:
    """
    Convenience function to run the bug bounty workflow.

    Args:
        run_context: The run context with configuration
        phases: Optional list of phases to run
        source_path: Optional path to source code
        logger: Optional logger instance

    Returns:
        WorkflowResult
    """
    workflow = BugBountyWorkflow(run_context, logger=logger)
    return await workflow.run(
        phases=phases,
        source_path=source_path,
        rpc_url=rpc_url,
        block_number=block_number,
        chain_id=chain_id,
        exploit_iterations=exploit_iterations,
        profit_threshold=profit_threshold,
    )
