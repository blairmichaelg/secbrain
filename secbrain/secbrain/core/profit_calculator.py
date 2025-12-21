"""Unified profit calculation module for SecBrain.

This module provides a single source of truth for calculating profit values
across all agents (exploit, triage, reporting, meta).

This module provides a single source of truth for profit calculations,
preventing inconsistent prioritization and duplicated code across agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Maximum reasonable decimals for token (uint256 max is ~77 digits)
MAX_TOKEN_DECIMALS = 77

# Sanity check for raw amounts to avoid overflow
MAX_RAW_AMOUNT = 10**80

# Default ETH price when no dynamic pricing is available
ETH_PRICE_DEFAULT = 3000.0

# Maximum gas cost as fraction of profit before warning (50%)
MAX_GAS_COST_RATIO = 0.5

# Default gas price in wei (50 gwei)
DEFAULT_GAS_PRICE_WEI = 50e9


@dataclass(frozen=True)
class TokenSpec:
    """Specification for a token used in profit calculations.

    Attributes:
        symbol: Token symbol (e.g., 'USDC', 'WETH')
        address: Token contract address (checksummed)
        decimals: Number of decimals for the token (0-77)
        price_usd: Current USD price of the token
        eth_equiv_multiplier: Optional multiplier for ETH equivalence calculation
    """
    symbol: str
    address: str
    decimals: int
    price_usd: float = 0.0
    eth_equiv_multiplier: dict[str, int] | None = None

    def __post_init__(self) -> None:
        """Validate token specification fields."""
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        if not self.address or not self.address.strip():
            raise ValueError("address cannot be empty")
        if self.decimals < 0:
            raise ValueError(f"Invalid decimals: decimals must be non-negative, got {self.decimals}")
        if self.decimals > MAX_TOKEN_DECIMALS:
            raise ValueError(f"Invalid decimals: must be <= {MAX_TOKEN_DECIMALS}, got {self.decimals}")
        if self.price_usd < 0:
            raise ValueError(f"Negative price: price_usd must be non-negative, got {self.price_usd}")
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenSpec":
        """Create a TokenSpec from a dictionary.
        
        Args:
            data: Dictionary containing symbol, address, decimals, and optionally price_usd
            
        Returns:
            TokenSpec instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        if "symbol" not in data:
            raise ValueError("Missing required field: symbol")
        if "address" not in data:
            raise ValueError("Missing required field: address")
        if "decimals" not in data:
            raise ValueError("Missing required field: decimals")
        
        # Handle eth_equiv_multiplier in different formats
        eth_equiv_multiplier = data.get("eth_equiv_multiplier")
        if eth_equiv_multiplier is None and "mult_num" in data and "mult_den" in data:
            # Convert old format to new format
            eth_equiv_multiplier = {
                "numerator": data["mult_num"],
                "denominator": data["mult_den"],
            }
            
        return cls(
            symbol=str(data["symbol"]),
            address=str(data["address"]),
            decimals=int(data["decimals"]),
            price_usd=float(data.get("price_usd", 0.0)),
            eth_equiv_multiplier=eth_equiv_multiplier,
        )


@dataclass
class ProfitBreakdown:
    """Breakdown of profit by token.

    Attributes:
        by_token: USD value per token symbol
        total_usd: Total USD value across all tokens
        eth_equivalent: Total value expressed in ETH
    """
    by_token: dict[str, float] = field(default_factory=dict)
    total_usd: float = 0.0
    eth_equivalent: float = 0.0


class ProfitCalculator:
    """Unified profit calculator for SecBrain agents.

    This class provides a single source of truth for converting raw token
    amounts to USD and ETH-equivalent values. It handles:
    - Decimal normalization for various token types (6, 8, 18 decimals, etc.)
    - Price lookup from token specs or cache
    - ETH-equivalent calculation
    - Validation of token amounts and specifications

    Example:
        >>> specs = [TokenSpec("USDC", "0x...", 6, 1.0)]
        >>> calc = ProfitCalculator(specs, eth_price_usd=3000.0)
        >>> result = calc.compute_usd({"USDC": 1_000_000})
        >>> print(result.by_token)  # {'USDC': 1.0}
    """

    def __init__(
        self,
        token_specs: list[TokenSpec] | None = None,
        eth_price_usd: float = ETH_PRICE_DEFAULT,
        price_cache: dict[str, float] | None = None,
    ) -> None:
        """Initialize the profit calculator.

        Args:
            token_specs: List of token specifications for known tokens (default: empty list)
            eth_price_usd: Current ETH price in USD (default: 3000.0)
            price_cache: Optional cache of dynamic prices keyed by lowercase symbol
        """
        self.tokens: dict[str, TokenSpec] = {}
        for spec in (token_specs or []):
            key = spec.symbol.lower()
            self.tokens[key] = spec

        self.eth_price_usd = max(eth_price_usd, 0.0)
        self.price_cache = price_cache or {}

    def compute_usd(
        self,
        token_amounts: dict[str, int | float],
        price_cache: dict[str, float] | None = None,
    ) -> ProfitBreakdown:
        """Convert raw token amounts to USD values.

        Args:
            token_amounts: Mapping of token symbol to raw amount (in wei/smallest unit)
            price_cache: Optional cache of dynamic prices keyed by lowercase symbol

        Returns:
            ProfitBreakdown with USD values per token and totals
        """
        breakdown = ProfitBreakdown()

        for symbol, raw_amount in token_amounts.items():
            try:
                amount = float(raw_amount or 0)
            except (TypeError, ValueError):
                continue

            # Sanity check for overflow
            if amount > MAX_RAW_AMOUNT:
                continue

            if amount <= 0:
                continue

            spec = self.tokens.get(symbol.lower())
            if not spec:
                continue

            # Normalize by decimals
            normalized = amount / (10 ** spec.decimals)

            # Get price (cache takes precedence)
            price = spec.price_usd
            if price_cache:
                cached_price = price_cache.get(symbol.lower())
                if cached_price is not None and cached_price >= 0:
                    price = cached_price

            usd_value = normalized * price
            breakdown.by_token[symbol] = usd_value
            breakdown.total_usd += usd_value

        # Calculate ETH equivalent
        if self.eth_price_usd > 0:
            breakdown.eth_equivalent = breakdown.total_usd / self.eth_price_usd

        return breakdown

    def compute_usd_value(
        self,
        amount: float,
        token_spec: TokenSpec,
    ) -> float:
        """Compute USD value of token amount.
        
        Args:
            amount: Normalized token amount
            token_spec: Token specification
            
        Returns:
            USD value
        """
        token_price = self.get_token_price(token_spec)
        return amount * token_price

    def compute_eth_equivalent(
        self,
        token_amounts: dict[str, int | float],
        base_eth_profit: float = 0.0,
        price_cache: dict[str, float] | None = None,
    ) -> tuple[float, dict[str, float], float]:
        """Compute ETH-equivalent value from token amounts.

        This method provides a backward-compatible interface for existing code
        that expects the (eth_equiv, breakdown_usd, profit_usd) tuple format.

        Args:
            token_amounts: Mapping of token symbol to raw amount
            base_eth_profit: Direct ETH profit to add to the total
            price_cache: Optional cache of dynamic prices

        Returns:
            Tuple of (eth_equivalent, breakdown_by_address, total_usd)
        """
        breakdown = self.compute_usd(token_amounts, price_cache)

        # Convert breakdown to use addresses where available
        breakdown_by_address: dict[str, float] = {}
        for symbol, usd_value in breakdown.by_token.items():
            spec = self.tokens.get(symbol.lower())
            key = spec.address if spec and spec.address else symbol
            breakdown_by_address[key] = usd_value

        total_eth_equiv = breakdown.eth_equivalent + base_eth_profit

        return (total_eth_equiv, breakdown_by_address, breakdown.total_usd)

    def update_eth_price(self, new_price: float) -> None:
        """Update the ETH price used for conversions.

        Args:
            new_price: New ETH price in USD (must be non-negative)
        """
        if new_price < 0:
            raise ValueError(f"Negative ETH price: {new_price}")
        self.eth_price_usd = new_price

    def add_token(self, spec: TokenSpec) -> None:
        """Add or update a token specification.

        Args:
            spec: Token specification to add
        """
        self.tokens[spec.symbol.lower()] = spec

    @staticmethod
    def normalize_amount(raw_amount: int | float, decimals: int) -> float:
        """Normalize a raw token amount by its decimals.

        Args:
            raw_amount: Raw amount in smallest unit (e.g., wei)
            decimals: Token decimals (0-77)

        Returns:
            Normalized amount as float

        Raises:
            ValueError: If decimals is out of range
        """
        if not 0 <= decimals <= MAX_TOKEN_DECIMALS:
            raise ValueError(f"Invalid decimals: {decimals}")
        return float(raw_amount) / (10 ** decimals)

    def normalize_token_amount(self, raw_amount: int | float, decimals: int) -> float:
        """Normalize a raw token amount by its decimals (instance method).

        Args:
            raw_amount: Raw amount in smallest unit (e.g., wei)
            decimals: Token decimals (-1 for no normalization, 0-77 for valid decimals)

        Returns:
            Normalized amount as float. If decimals is negative, returns raw_amount unchanged.
        """
        if decimals < 0:
            # Special case: negative decimals means no normalization
            return float(raw_amount)
        return self.normalize_amount(raw_amount, decimals)

    def get_token_price(self, token_spec: TokenSpec) -> float:
        """Get token price from cache or spec.

        Args:
            token_spec: Token specification

        Returns:
            Token price in USD (0.0 if unavailable)
        """
        # Check cache first
        cached_price = self.price_cache.get(token_spec.symbol.lower())
        if cached_price is not None and cached_price > 0:
            return float(cached_price)
        
        # Fall back to spec price
        return float(token_spec.price_usd)

    def compute_eth_equiv(self, amount: float, token_spec: TokenSpec) -> float:
        """Compute ETH equivalent of token amount.

        Args:
            amount: Normalized token amount
            token_spec: Token specification

        Returns:
            ETH equivalent value
        """
        # Check for eth_equiv_multiplier in spec (backward compatibility)
        if token_spec.eth_equiv_multiplier is not None:
            multiplier = token_spec.eth_equiv_multiplier
            if isinstance(multiplier, dict):
                numerator = multiplier.get('numerator', 1)
                denominator = multiplier.get('denominator', 1)
                if denominator != 0:
                    return amount * numerator / denominator
        
        # Use price-based calculation
        token_price = self.get_token_price(token_spec)
        if self.eth_price_usd > 0 and token_price > 0:
            return (amount * token_price) / self.eth_price_usd
        
        return 0.0

    def calculate_profit_from_tokens(
        self,
        profit_tokens: dict[str, int | float],
        token_specs: list[TokenSpec],
    ) -> tuple[float, dict[str, float], float]:
        """Calculate profit from token amounts.

        Args:
            profit_tokens: Mapping of token symbol to raw amount
            token_specs: List of token specifications

        Returns:
            Tuple of (eth_equivalent, breakdown_by_address, total_usd)
        """
        if not isinstance(profit_tokens, dict):
            return (0.0, {}, 0.0)

        # Build token lookup from specs
        spec_lookup: dict[str, TokenSpec] = {}
        for spec in token_specs:
            spec_lookup[spec.symbol.lower()] = spec

        total_eth_equiv = 0.0
        total_usd = 0.0
        breakdown_by_address: dict[str, float] = {}

        for symbol, raw_amount in profit_tokens.items():
            try:
                amount = float(raw_amount or 0)
            except (TypeError, ValueError):
                continue

            if amount <= 0 or amount > MAX_RAW_AMOUNT:
                continue

            spec = spec_lookup.get(symbol.lower())
            if not spec:
                continue

            # Normalize amount
            normalized = self.normalize_token_amount(amount, spec.decimals)

            # Calculate USD value
            usd_value = self.compute_usd_value(normalized, spec)
            total_usd += usd_value

            # Calculate ETH equivalent
            eth_equiv = self.compute_eth_equiv(normalized, spec)
            total_eth_equiv += eth_equiv

            # Add to breakdown by address
            breakdown_by_address[spec.address] = usd_value

        return (total_eth_equiv, breakdown_by_address, total_usd)

    def calculate_profit_usd_from_list(
        self,
        profit_tokens: list[dict[str, Any]],
        token_specs: list[TokenSpec],
    ) -> dict[str, Any] | None:
        """Calculate profit from list format.

        Args:
            profit_tokens: List of dicts with 'address' and 'amount' keys
            token_specs: List of token specifications

        Returns:
            Dict with 'total_usd' and 'breakdown' keys, or None if empty
        """
        if not profit_tokens:
            return None

        # Build spec lookup by address
        spec_lookup: dict[str, TokenSpec] = {}
        for spec in token_specs:
            spec_lookup[spec.address.lower()] = spec

        total_usd = 0.0
        breakdown: dict[str, float] = {}

        for token_entry in profit_tokens:
            if not isinstance(token_entry, dict):
                continue

            address = str(token_entry.get('address', '')).lower()
            raw_amount = token_entry.get('amount', 0)

            try:
                amount = float(raw_amount or 0)
            except (TypeError, ValueError):
                continue

            if amount <= 0 or amount > MAX_RAW_AMOUNT:
                continue

            spec = spec_lookup.get(address)
            if not spec:
                continue

            # Normalize and calculate USD value
            normalized = self.normalize_token_amount(amount, spec.decimals)
            usd_value = self.compute_usd_value(normalized, spec)
            
            total_usd += usd_value
            breakdown[address] = usd_value

        return {
            'total_usd': total_usd,
            'breakdown': breakdown,
        }

    def estimate_gas_cost(
        self,
        gas_used: int | None,
        gas_price_wei: float | None = None,
    ) -> tuple[float, float]:
        """Estimate gas cost in ETH and USD.

        Args:
            gas_used: Gas units used (None = no gas)
            gas_price_wei: Gas price in wei (default: DEFAULT_GAS_PRICE_WEI)

        Returns:
            Tuple of (gas_cost_eth, gas_cost_usd)
        """
        if gas_used is None or gas_used <= 0:
            return (0.0, 0.0)

        if gas_price_wei is None:
            gas_price_wei = DEFAULT_GAS_PRICE_WEI

        # Calculate gas cost in ETH
        gas_cost_eth = (gas_used * gas_price_wei) / 1e18

        # Calculate gas cost in USD
        gas_cost_usd = gas_cost_eth * self.eth_price_usd

        return (gas_cost_eth, gas_cost_usd)

    def make_economic_decision(
        self,
        max_profit_usd: float,
        gas_cost_usd: float = 0.0,
        min_profit_threshold: float = 100.0,
    ) -> dict[str, Any]:
        """Make economic decision based on profit and costs.

        Args:
            max_profit_usd: Maximum profit in USD
            gas_cost_usd: Gas cost in USD
            min_profit_threshold: Minimum profit threshold in USD

        Returns:
            Dict with 'decision', 'reason', and 'net_usd' keys
        """
        # Validate inputs
        try:
            max_profit = float(max_profit_usd)
            gas_cost = float(gas_cost_usd)
        except (TypeError, ValueError):
            return {
                'decision': 'SKIP',
                'reason': 'Invalid profit or gas cost values',
                'net_usd': 0.0,
            }

        net_usd = max_profit - gas_cost

        # Check if gas cost is too high (>MAX_GAS_COST_RATIO of profit)
        if max_profit > 0 and gas_cost / max_profit > MAX_GAS_COST_RATIO:
            return {
                'decision': 'SKIP',
                'reason': 'Gas cost too high relative to profit',
                'net_usd': net_usd,
            }

        # Check if net profit is negative or zero
        if net_usd <= 0:
            return {
                'decision': 'SKIP',
                'reason': 'Negative or zero profit after gas',
                'net_usd': net_usd,
            }

        # Check if net profit meets threshold
        if net_usd >= min_profit_threshold:
            return {
                'decision': 'PURSUE',
                'reason': f'Net profit ${net_usd:.2f} meets threshold ${min_profit_threshold:.2f}',
                'net_usd': net_usd,
            }

        # Marginal profit
        return {
            'decision': 'CONSIDER',
            'reason': f'Marginal profit ${net_usd:.2f} below threshold ${min_profit_threshold:.2f}',
            'net_usd': net_usd,
        }


def create_profit_calculator_from_chain(
    chain_id: int,
    token_addresses: dict[int, list[dict[str, Any]]],
    eth_price_usd: float = ETH_PRICE_DEFAULT,
    scope_tokens: list[dict[str, Any]] | None = None,
) -> ProfitCalculator:
    """Create a ProfitCalculator from chain-specific token addresses.

    This is a factory function that creates a ProfitCalculator using the
    token configuration from TOKEN_ADDRESSES_BY_CHAIN or scope-provided tokens.

    Args:
        chain_id: Chain ID (e.g., 1 for Ethereum mainnet)
        token_addresses: Chain-specific token address mapping
        eth_price_usd: Current ETH price in USD
        scope_tokens: Optional scope-provided token list (takes precedence)

    Returns:
        Configured ProfitCalculator instance
    """
    specs: list[TokenSpec] = []

    # Scope tokens take precedence
    source_tokens = scope_tokens if scope_tokens else token_addresses.get(chain_id, [])

    for token_dict in source_tokens:
        try:
            spec = TokenSpec(
                symbol=str(token_dict.get("symbol", "")),
                address=str(token_dict.get("address", "")),
                decimals=int(token_dict.get("decimals", 18)),
                price_usd=float(token_dict.get("price_usd", 0.0) or 0.0),
            )
            specs.append(spec)
        except (ValueError, TypeError):
            # Skip invalid token specs
            continue

    return ProfitCalculator(specs, eth_price_usd)
