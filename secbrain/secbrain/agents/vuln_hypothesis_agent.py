"""Vulnerability hypothesis agent - generates hypotheses for testing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from secbrain.agents.oracle_manipulation_detector import OracleManipulationDetector
from secbrain.agents.vuln_hypothesis_agent_base import BaseVulnHypothesisAgent
from secbrain.agents.vuln_hypothesis_agent_patterns import VulnHypothesisPatternsMixin
from secbrain.agents.vuln_hypothesis_agent_runner import VulnHypothesisRunnerMixin

logger = logging.getLogger(__name__)

class VulnHypothesisAgent(
    VulnHypothesisPatternsMixin,
    VulnHypothesisRunnerMixin,
    BaseVulnHypothesisAgent
):
    """
    Vulnerability hypothesis agent.

    Responsibilities:
    - Generates vulnerability hypotheses per asset/endpoint
    - Research substep for validation
    - Advisor review at the end
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._oracle_detector = OracleManipulationDetector()
        
        # Configurable concurrency limits
        scope = getattr(self.run_context, "scope", None)
        if scope is None:
            class _DefaultScope:
                max_llm_concurrent = 5
            scope = _DefaultScope()
            self.run_context.scope = scope
            
        self._max_llm_concurrent = getattr(scope, "max_llm_concurrent", 5)
        self._contract_llm_sem = asyncio.Semaphore(self._max_llm_concurrent)

        # Add hypothesis enhancer
        self.hyp_enhancer = None
        if self.research_orch:
            from secbrain.agents.hypothesis_enhancer import HypothesisEnhancer
            self.hyp_enhancer = HypothesisEnhancer(self.research_orch)
