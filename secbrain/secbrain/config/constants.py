"""Centralized configuration constants for SecBrain.

This module provides configuration classes for various SecBrain subsystems:
- LLM client settings (timeouts, retries, concurrency)
- Hypothesis generation parameters
- Exploit execution thresholds
- Rate limiting and pricing configuration
- Tool-specific defaults

All configuration classes are frozen dataclasses to prevent accidental modification.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class LLMConfig:
    """LLM-related configuration.
    
    Provides default settings for LLM client operations including
    timeouts, retry logic, and concurrency limits.
    """

    MAX_CONCURRENT_CALLS: ClassVar[int] = 5
    DEFAULT_TIMEOUT_SECONDS: ClassVar[int] = 30
    MAX_RETRIES: ClassVar[int] = 3
    RETRY_BACKOFF_BASE: ClassVar[float] = 2.0


@dataclass(frozen=True)
class HypothesisConfig:
    """Hypothesis generation configuration.
    
    Controls parameters for vulnerability hypothesis generation
    including confidence thresholds and preview limits.
    """

    CONFIDENCE_THRESHOLD: ClassVar[float] = 0.4
    MAX_HYPOTHESES_PER_CONTRACT: ClassVar[int] = 5
    ABI_PREVIEW_MAX_ENTRIES: ClassVar[int] = 30
    ABI_PREVIEW_REDUCED_ENTRIES: ClassVar[int] = 15
    ABI_JSON_SIZE_LIMIT: ClassVar[int] = 1500
    FUNCTIONS_PREVIEW_LIMIT: ClassVar[int] = 15


@dataclass(frozen=True)
class ExploitConfig:
    """Exploitation configuration.
    
    Defines settings for exploit execution including iteration limits,
    profit thresholds, and build timeouts.
    """

    DEFAULT_ITERATIONS: ClassVar[int] = 3
    DEFAULT_PROFIT_THRESHOLD_ETH: ClassVar[float] = 0.1
    MAX_PARALLEL_EXPLOITS: ClassVar[int] = 2
    RPC_MAX_RETRIES: ClassVar[int] = 3
    RPC_RETRY_BACKOFF: ClassVar[float] = 2.0
    FORGE_BUILD_TIMEOUT: ClassVar[int] = 300


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limiting configuration.
    
    Configures rate limits for external API calls to prevent
    abuse and stay within service quotas.
    """

    COINGECKO_REQUESTS_PER_MINUTE: ClassVar[int] = 10
    COINGECKO_MIN_INTERVAL_SECONDS: ClassVar[float] = 6.0
    RESEARCH_MAX_CONCURRENT: ClassVar[int] = 3
    RESEARCH_MIN_QUERY_INTERVAL: ClassVar[float] = 6.0


@dataclass(frozen=True)
class PricingConfig:
    """Token pricing configuration.
    
    Defines default prices and thresholds for profitability calculations.
    """

    ETH_PRICE_DEFAULT: ClassVar[float] = 3000.0
    MIN_PROFIT_USD: ClassVar[float] = 300.0
    GAS_RATIO_THRESHOLD: ClassVar[float] = 0.5
    DEFAULT_GAS_PRICE_GWEI: ClassVar[float] = 50.0
