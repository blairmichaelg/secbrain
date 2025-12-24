import pytest

from secbrain.core.profit_calculator import (
    MAX_RAW_AMOUNT,
    ProfitCalculator,
    TokenSpec,
)


def test_token_spec_validation():
    """Test TokenSpec validation."""
    # Valid spec
    spec = TokenSpec("USDC", "0x" + "a" * 40, 6, 1.0)
    assert spec.symbol == "USDC"

    # Invalid decimals
    with pytest.raises(ValueError, match="decimals"):
        TokenSpec("BAD", "0x" + "a" * 40, -1, 1.0)

    # Invalid price
    with pytest.raises(ValueError, match="price"):
        TokenSpec("BAD", "0x" + "a" * 40, 18, -10.0)


def test_profit_calculator_overflow_protection():
    """Test overflow protection in profit calculation."""
    spec = TokenSpec("HUGE", "0x" + "b" * 40, 18, 1.0)
    calc = ProfitCalculator([spec], eth_price_usd=3000.0)

    # Should skip amounts over MAX_RAW_AMOUNT
    result = calc.compute_usd({"HUGE": MAX_RAW_AMOUNT + 1})
    assert result.total_usd == 0.0


def test_profit_calculator_price_cache():
    """Test price cache takes precedence over spec price."""
    spec = TokenSpec("TOKEN", "0x" + "c" * 40, 18, 1.0)
    calc = ProfitCalculator([spec], eth_price_usd=3000.0)

    # Without cache, uses spec price
    result1 = calc.compute_usd({"TOKEN": 1_000_000_000_000_000_000})
    assert result1.by_token["TOKEN"] == pytest.approx(1.0, abs=0.01)

    # With cache, uses cached price
    cache = {"token": 2.0}
    result2 = calc.compute_usd({"TOKEN": 1_000_000_000_000_000_000}, cache)
    assert result2.by_token["TOKEN"] == pytest.approx(2.0, abs=0.01)
