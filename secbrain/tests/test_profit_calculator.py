"""Unit tests for ProfitCalculator."""


import pytest

from secbrain.core.profit_calculator import (
    ProfitCalculator,
    TokenSpec,
    create_profit_calculator_from_chain,
)


class TestTokenSpec:
    """Tests for TokenSpec dataclass."""

    def test_valid_token_spec(self):
        """Test valid token spec creation."""
        spec = TokenSpec(
            symbol="USDC",
            address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            decimals=6,
            price_usd=1.0,
        )
        assert spec.symbol == "USDC"
        assert spec.decimals == 6
        assert spec.price_usd == 1.0

    def test_zero_decimals_valid(self):
        """Test token with 0 decimals is valid."""
        spec = TokenSpec(symbol="TOKEN", address="0x123", decimals=0, price_usd=10.0)
        assert spec.decimals == 0

    def test_max_decimals_valid(self):
        """Test token with max decimals (77) is valid."""
        spec = TokenSpec(symbol="TOKEN", address="0x123", decimals=77, price_usd=1.0)
        assert spec.decimals == 77

    def test_negative_decimals_invalid(self):
        """Test that negative decimals raises ValueError."""
        with pytest.raises(ValueError, match="Invalid decimals"):
            TokenSpec(symbol="TOKEN", address="0x123", decimals=-1, price_usd=1.0)

    def test_decimals_too_large_invalid(self):
        """Test that decimals > 77 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid decimals"):
            TokenSpec(symbol="TOKEN", address="0x123", decimals=78, price_usd=1.0)

    def test_negative_price_invalid(self):
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="Negative price"):
            TokenSpec(symbol="TOKEN", address="0x123", decimals=18, price_usd=-1.0)

    def test_zero_price_valid(self):
        """Test that zero price is valid (unknown price)."""
        spec = TokenSpec(symbol="TOKEN", address="0x123", decimals=18, price_usd=0.0)
        assert spec.price_usd == 0.0


class TestProfitCalculator:
    """Tests for ProfitCalculator class."""

    def test_usdc_conversion(self):
        """Test USDC conversion with 6 decimals."""
        specs = [TokenSpec("USDC", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"USDC": 1_000_000})  # 1 USDC

        assert result.by_token == {"USDC": pytest.approx(1.0)}
        assert result.total_usd == pytest.approx(1.0)
        assert result.eth_equivalent == pytest.approx(1.0 / 3000.0)

    def test_weth_conversion(self):
        """Test WETH conversion with 18 decimals."""
        specs = [TokenSpec("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18, 3000.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"WETH": 10**18})  # 1 WETH

        assert result.by_token == {"WETH": pytest.approx(3000.0)}
        assert result.total_usd == pytest.approx(3000.0)
        assert result.eth_equivalent == pytest.approx(1.0)

    def test_unknown_token_skipped(self):
        """Test that unknown tokens are skipped."""
        calc = ProfitCalculator([], eth_price_usd=3000.0)

        result = calc.compute_usd({"UNKNOWN": 1000})

        assert result.by_token == {}
        assert result.total_usd == 0.0
        assert result.eth_equivalent == 0.0

    def test_case_insensitive_symbol_lookup(self):
        """Test that symbol lookup is case insensitive."""
        specs = [TokenSpec("USDC", "0x123", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        # Use lowercase symbol in input
        result = calc.compute_usd({"usdc": 1_000_000})

        assert "usdc" in result.by_token
        assert result.total_usd == pytest.approx(1.0)

    def test_multiple_tokens(self):
        """Test calculation with multiple tokens."""
        specs = [
            TokenSpec("USDC", "0xUSDC", 6, 1.0),
            TokenSpec("WETH", "0xWETH", 18, 3000.0),
        ]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({
            "USDC": 10_000_000,  # 10 USDC
            "WETH": 2 * 10**18,  # 2 WETH
        })

        assert result.by_token["USDC"] == pytest.approx(10.0)
        assert result.by_token["WETH"] == pytest.approx(6000.0)
        assert result.total_usd == pytest.approx(6010.0)

    def test_price_cache_overrides_spec(self):
        """Test that price cache overrides token spec price."""
        specs = [TokenSpec("WETH", "0xWETH", 18, 3000.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        # Use different price in cache
        result = calc.compute_usd(
            {"WETH": 10**18},
            price_cache={"weth": 4000.0}
        )

        assert result.total_usd == pytest.approx(4000.0)

    def test_zero_amount_skipped(self):
        """Test that zero amounts are skipped."""
        specs = [TokenSpec("USDC", "0x123", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"USDC": 0})

        assert result.by_token == {}
        assert result.total_usd == 0.0

    def test_negative_amount_skipped(self):
        """Test that negative amounts are skipped."""
        specs = [TokenSpec("USDC", "0x123", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"USDC": -1000})

        assert result.by_token == {}
        assert result.total_usd == 0.0

    def test_overflow_protection(self):
        """Test that very large amounts are skipped."""
        specs = [TokenSpec("USDC", "0x123", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        # Amount exceeds MAX_RAW_AMOUNT (10**80)
        result = calc.compute_usd({"USDC": 10**81})

        assert result.by_token == {}
        assert result.total_usd == 0.0

    def test_zero_eth_price(self):
        """Test calculation with zero ETH price."""
        specs = [TokenSpec("USDC", "0x123", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=0.0)

        result = calc.compute_usd({"USDC": 1_000_000})

        assert result.total_usd == pytest.approx(1.0)
        assert result.eth_equivalent == 0.0  # Cannot calculate ETH equiv with 0 price

    def test_compute_eth_equivalent_legacy_format(self):
        """Test legacy tuple format for backward compatibility."""
        specs = [TokenSpec("USDC", "0xA0b", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        eth_equiv, breakdown, usd = calc.compute_eth_equivalent(
            {"USDC": 3_000_000},  # 3 USDC
            base_eth_profit=1.0  # 1 ETH direct profit
        )

        assert usd == pytest.approx(3.0)
        assert eth_equiv == pytest.approx(1.001)  # 1 ETH + 3 USDC / 3000

    def test_update_eth_price(self):
        """Test updating ETH price."""
        calc = ProfitCalculator([], eth_price_usd=3000.0)
        calc.update_eth_price(4000.0)

        assert calc.eth_price_usd == 4000.0

    def test_update_eth_price_negative_fails(self):
        """Test that negative ETH price update fails."""
        calc = ProfitCalculator([], eth_price_usd=3000.0)

        with pytest.raises(ValueError, match="Negative ETH price"):
            calc.update_eth_price(-100.0)

    def test_add_token(self):
        """Test adding a token to calculator."""
        calc = ProfitCalculator([], eth_price_usd=3000.0)

        calc.add_token(TokenSpec("DAI", "0xDAI", 18, 1.0))

        result = calc.compute_usd({"DAI": 100 * 10**18})
        assert result.total_usd == pytest.approx(100.0)

    def test_normalize_amount_static(self):
        """Test static normalize_amount method."""
        assert ProfitCalculator.normalize_amount(1_000_000, 6) == pytest.approx(1.0)
        assert ProfitCalculator.normalize_amount(10**18, 18) == pytest.approx(1.0)
        assert ProfitCalculator.normalize_amount(100, 0) == pytest.approx(100.0)

    def test_normalize_amount_invalid_decimals(self):
        """Test normalize_amount with invalid decimals."""
        with pytest.raises(ValueError, match="Invalid decimals"):
            ProfitCalculator.normalize_amount(100, -1)

        with pytest.raises(ValueError, match="Invalid decimals"):
            ProfitCalculator.normalize_amount(100, 78)


class TestCreateProfitCalculatorFromChain:
    """Tests for factory function."""

    def test_create_from_chain_id(self):
        """Test creating calculator from chain token addresses."""
        token_addresses = {
            1: [
                {"symbol": "USDC", "address": "0xUSDC", "decimals": 6, "price_usd": 1.0},
                {"symbol": "WETH", "address": "0xWETH", "decimals": 18, "price_usd": 3000.0},
            ]
        }

        calc = create_profit_calculator_from_chain(
            chain_id=1,
            token_addresses=token_addresses,
            eth_price_usd=3000.0
        )

        assert "usdc" in calc.tokens
        assert "weth" in calc.tokens

    def test_scope_tokens_take_precedence(self):
        """Test that scope tokens override chain tokens."""
        token_addresses = {
            1: [{"symbol": "USDC", "address": "0xOLD", "decimals": 6, "price_usd": 1.0}]
        }
        scope_tokens = [
            {"symbol": "USDC", "address": "0xNEW", "decimals": 6, "price_usd": 0.99}
        ]

        calc = create_profit_calculator_from_chain(
            chain_id=1,
            token_addresses=token_addresses,
            scope_tokens=scope_tokens,
            eth_price_usd=3000.0
        )

        assert calc.tokens["usdc"].address == "0xNEW"
        assert calc.tokens["usdc"].price_usd == pytest.approx(0.99)

    def test_invalid_token_specs_skipped(self):
        """Test that invalid token specs in source are skipped."""
        token_addresses = {
            1: [
                {"symbol": "GOOD", "address": "0x123", "decimals": 18, "price_usd": 1.0},
                {"symbol": "BAD", "address": "0x456", "decimals": -5, "price_usd": 1.0},  # Invalid
            ]
        }

        calc = create_profit_calculator_from_chain(
            chain_id=1,
            token_addresses=token_addresses,
            eth_price_usd=3000.0
        )

        assert "good" in calc.tokens
        assert "bad" not in calc.tokens

    def test_missing_chain_id(self):
        """Test creating calculator with missing chain ID."""
        calc = create_profit_calculator_from_chain(
            chain_id=999,
            token_addresses={1: []},
            eth_price_usd=3000.0
        )

        assert len(calc.tokens) == 0


class TestProfitCalculatorEdgeCases:
    """Edge case tests for profit calculation."""

    def test_wbtc_8_decimals(self):
        """Test WBTC with 8 decimals."""
        specs = [TokenSpec("WBTC", "0xWBTC", 8, 60000.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"WBTC": 10**8})  # 1 WBTC

        assert result.total_usd == pytest.approx(60000.0)
        assert result.eth_equivalent == pytest.approx(20.0)  # 60000 / 3000

    def test_float_amount_input(self):
        """Test that float amounts work."""
        specs = [TokenSpec("TOKEN", "0x123", 18, 10.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"TOKEN": 1.5 * 10**18})

        assert result.total_usd == pytest.approx(15.0)

    def test_invalid_amount_type_skipped(self):
        """Test that invalid amount types are skipped."""
        specs = [TokenSpec("TOKEN", "0x123", 18, 10.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd({"TOKEN": "invalid"})

        assert result.by_token == {}

    def test_none_in_price_cache(self):
        """Test that None in price cache uses spec price."""
        specs = [TokenSpec("USDC", "0x123", 6, 1.0)]
        calc = ProfitCalculator(specs, eth_price_usd=3000.0)

        result = calc.compute_usd(
            {"USDC": 1_000_000},
            price_cache={"usdc": None}  # type: ignore
        )

        # Should use spec price of 1.0
        assert result.total_usd == pytest.approx(1.0)
