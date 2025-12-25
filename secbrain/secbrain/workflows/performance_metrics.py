"""Performance metrics collection for workflow optimization."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""

    phase_name: str
    start_time: float
    end_time: float = 0.0
    duration_seconds: float = 0.0
    api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self) -> None:
        """Mark phase as complete and calculate duration."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WorkflowMetrics:
    """Aggregate metrics for entire workflow."""

    run_id: str
    start_time: float
    end_time: float = 0.0
    total_duration_seconds: float = 0.0
    phases: dict[str, PhaseMetrics] = field(default_factory=dict)
    total_api_calls: int = 0
    total_cache_hits: int = 0
    total_cache_misses: int = 0
    total_errors: int = 0
    cache_hit_rate: float = 0.0
    successful_phases: int = 0
    failed_phases: int = 0

    def complete(self) -> None:
        """Mark workflow as complete and calculate aggregate metrics."""
        self.end_time = time.time()
        self.total_duration_seconds = self.end_time - self.start_time

        # Aggregate phase metrics
        for phase_metrics in self.phases.values():
            self.total_api_calls += phase_metrics.api_calls
            self.total_cache_hits += phase_metrics.cache_hits
            self.total_cache_misses += phase_metrics.cache_misses
            self.total_errors += phase_metrics.errors

            if phase_metrics.success:
                self.successful_phases += 1
            else:
                self.failed_phases += 1

        # Calculate cache hit rate
        total_cache_ops = self.total_cache_hits + self.total_cache_misses
        if total_cache_ops > 0:
            self.cache_hit_rate = self.total_cache_hits / total_cache_ops

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_seconds": self.total_duration_seconds,
            "phases": {name: metrics.to_dict() for name, metrics in self.phases.items()},
            "total_api_calls": self.total_api_calls,
            "total_cache_hits": self.total_cache_hits,
            "total_cache_misses": self.total_cache_misses,
            "total_errors": self.total_errors,
            "cache_hit_rate": self.cache_hit_rate,
            "successful_phases": self.successful_phases,
            "failed_phases": self.failed_phases,
        }


class PerformanceMetricsCollector:
    """
    Collect and track performance metrics during workflow execution.

    Features:
    - Phase-level timing
    - API call tracking
    - Cache hit/miss tracking
    - Error counting
    - Aggregate statistics
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.workflow_metrics = WorkflowMetrics(
            run_id=run_id,
            start_time=time.time(),
        )
        self._current_phase: PhaseMetrics | None = None
        self._phase_counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def start_phase(self, phase_name: str) -> None:
        """Start tracking a new phase."""
        if self._current_phase:
            # Complete previous phase
            self._current_phase.complete()
            self.workflow_metrics.phases[self._current_phase.phase_name] = self._current_phase

        self._current_phase = PhaseMetrics(
            phase_name=phase_name,
            start_time=time.time(),
        )

    def complete_phase(self, success: bool = True, metadata: dict[str, Any] | None = None) -> None:
        """Complete current phase tracking."""
        if not self._current_phase:
            return

        self._current_phase.success = success
        if metadata:
            self._current_phase.metadata = metadata

        # Add counters
        counters = self._phase_counters.get(self._current_phase.phase_name, {})
        self._current_phase.api_calls = counters.get("api_calls", 0)
        self._current_phase.cache_hits = counters.get("cache_hits", 0)
        self._current_phase.cache_misses = counters.get("cache_misses", 0)
        self._current_phase.errors = counters.get("errors", 0)

        self._current_phase.complete()
        self.workflow_metrics.phases[self._current_phase.phase_name] = self._current_phase
        self._current_phase = None

    def record_api_call(self) -> None:
        """Record an API call in the current phase."""
        if self._current_phase:
            self._phase_counters[self._current_phase.phase_name]["api_calls"] += 1

    def record_cache_hit(self) -> None:
        """Record a cache hit in the current phase."""
        if self._current_phase:
            self._phase_counters[self._current_phase.phase_name]["cache_hits"] += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss in the current phase."""
        if self._current_phase:
            self._phase_counters[self._current_phase.phase_name]["cache_misses"] += 1

    def record_error(self) -> None:
        """Record an error in the current phase."""
        if self._current_phase:
            self._phase_counters[self._current_phase.phase_name]["errors"] += 1

    def complete_workflow(self) -> WorkflowMetrics:
        """Complete workflow tracking and return metrics."""
        # Complete any active phase
        if self._current_phase:
            self.complete_phase()

        self.workflow_metrics.complete()
        return self.workflow_metrics

    def get_summary(self) -> dict[str, Any]:
        """Get current metrics summary."""
        return {
            "run_id": self.run_id,
            "elapsed_seconds": time.time() - self.workflow_metrics.start_time,
            "phases_completed": len(self.workflow_metrics.phases),
            "current_phase": self._current_phase.phase_name if self._current_phase else None,
            "total_api_calls": sum(c.get("api_calls", 0) for c in self._phase_counters.values()),
            "total_cache_hits": sum(c.get("cache_hits", 0) for c in self._phase_counters.values()),
            "total_errors": sum(c.get("errors", 0) for c in self._phase_counters.values()),
        }
