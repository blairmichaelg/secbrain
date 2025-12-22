"""Core module for SecBrain - context, logging, and shared types."""

from secbrain.core.context import RunContext, Session
from secbrain.core.logging import log_event, setup_logging
from secbrain.core.profit_calculator import (
    ProfitBreakdown,
    ProfitCalculator,
    TokenSpec,
    create_profit_calculator_from_chain,
)
from secbrain.core.research_orchestrator import (
    ResearchOrchestrator,
    ResearchQuery,
    ResearchResult,
)
from secbrain.core.types import (
    # Constants
    ALLOWED_HTTP_METHODS,
    DEFAULT_RATE_LIMIT,
    MAX_CONFIDENCE,
    MIN_CONFIDENCE,
    # Pydantic Models
    AgentResult,
    Asset,
    # NewTypes for domain-specific type safety
    EthAddress,
    # TypedDicts for structured data
    EvidenceDict,
    Finding,
    FindingDict,
    FindingStatus,
    # Protocols for structural subtyping
    HTTPResponseProtocol,
    Hypothesis,
    ModelClientProtocol,
    Phase,
    ProfitTokenDict,
    ScopedURL,
    SecretStr,
    Severity,
    SHA256Hash,
    StorageProtocol,
    ToolCallDict,
    TxHash,
)

__all__ = [
    "ALLOWED_HTTP_METHODS",
    "DEFAULT_RATE_LIMIT",
    # Constants
    "MAX_CONFIDENCE",
    "MIN_CONFIDENCE",
    "AgentResult",
    "Asset",
    # NewTypes
    "EthAddress",
    # TypedDicts
    "EvidenceDict",
    # Pydantic Models
    "Finding",
    "FindingDict",
    "FindingStatus",
    # Protocols
    "HTTPResponseProtocol",
    "Hypothesis",
    "ModelClientProtocol",
    # Enums
    "Phase",
    # Profit Calculator
    "ProfitBreakdown",
    "ProfitCalculator",
    "ProfitTokenDict",
    # Research Orchestrator
    "ResearchOrchestrator",
    "ResearchQuery",
    "ResearchResult",
    # Context and Logging
    "RunContext",
    "SHA256Hash",
    "ScopedURL",
    "SecretStr",
    "Session",
    "Severity",
    "StorageProtocol",
    "TokenSpec",
    "ToolCallDict",
    "TxHash",
    "create_profit_calculator_from_chain",
    "log_event",
    "setup_logging",
]
