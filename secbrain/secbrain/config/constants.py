"""Centralized configuration constants for SecBrain."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limiting configuration."""

    COINGECKO_MIN_INTERVAL_SECONDS: ClassVar[float] = 6.0


@dataclass(frozen=True)
class PricingConfig:
    """Token pricing configuration."""

    ETH_PRICE_DEFAULT: ClassVar[float] = 3000.0
    GAS_RATIO_THRESHOLD: ClassVar[float] = 0.5
    DEFAULT_GAS_PRICE_GWEI: ClassVar[float] = 50.0
