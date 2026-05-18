"""Reconnaissance agent facade."""

from __future__ import annotations

from secbrain.agents.recon_agent_base import (
    BaseReconAgent,
    CompilationRetryHelper,
    NonRetryableCompilationError,
)
from secbrain.agents.recon_agent_runner import ReconRunnerMixin


class ReconAgent(ReconRunnerMixin, BaseReconAgent):
    """Recon agent composed from base helpers and runner orchestration."""

    pass


__all__ = [
    "ReconAgent",
    "BaseReconAgent",
    "CompilationRetryHelper",
    "NonRetryableCompilationError",
]
