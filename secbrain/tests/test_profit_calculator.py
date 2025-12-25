import pytest

from secbrain.core.profit_calculator import (
    MAX_RAW_AMOUNT,
    MAX_TOKEN_DECIMALS,
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


def test_token_spec_empty_symbol():
    """Test that empty symbol raises error."""
    with pytest.raises(ValueError, match="symbol cannot be empty"):
        TokenSpec("", "0x" + "a" * 40, 18, 1.0)
    
    with pytest.raises(ValueError, match="symbol cannot be empty"):
        TokenSpec("   ", "0x" + "a" * 40, 18, 1.0)


def test_token_spec_empty_address():
    """Test that empty address raises error."""
    with pytest.raises(ValueError, match="address cannot be empty"):
        TokenSpec("TOKEN", "", 18, 1.0)
    
    with pytest.raises(ValueError, match="address cannot be empty"):
        TokenSpec("TOKEN", "   ", 18, 1.0)


def test_token_spec_max_decimals():
    """Test maximum decimals validation."""
    # At max should work
    spec = TokenSpec("TOKEN", "0xabc", MAX_TOKEN_DECIMALS, 1.0)
    assert spec.decimals == MAX_TOKEN_DECIMALS
    
    # Over max should fail
    with pytest.raises(ValueError, match="Invalid decimals"):
        TokenSpec("TOKEN", "0xabc", MAX_TOKEN_DECIMALS + 1, 1.0)


def test_token_spec_from_dict_basic():
    """Test creating TokenSpec from dictionary."""
    data = {
        "symbol": "USDC",
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6,
        "price_usd": 1.0,
    }
    spec = TokenSpec.from_dict(data)
    assert spec.symbol == "USDC"
    assert spec.address == "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    assert spec.decimals == 6
    assert spec.price_usd == 1.0


def test_token_spec_from_dict_missing_symbol():
    """Test that missing symbol raises error."""
    data = {"address": "0xabc", "decimals": 18}
    with pytest.raises(ValueError, match="Missing required field: symbol"):
        TokenSpec.from_dict(data)


def test_token_spec_from_dict_missing_address():
    """Test that missing address raises error."""
    data = {"symbol": "TOKEN", "decimals": 18}
    with pytest.raises(ValueError, match="Missing required field: address"):
        TokenSpec.from_dict(data)


def test_token_spec_from_dict_missing_decimals():
    """Test that missing decimals raises error."""
    data = {"symbol": "TOKEN", "address": "0xabc"}
    with pytest.raises(ValueError, match="Missing required field: decimals"):
        TokenSpec.from_dict(data)


def test_token_spec_from_dict_with_price():
    """Test from_dict with explicit price."""
    data = {
        "symbol": "WETH",
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "decimals": 18,
        "price_usd": 3000.0,
    }
    spec = TokenSpec.from_dict(data)
    assert spec.price_usd == 3000.0


def test_token_spec_from_dict_default_price():
    """Test from_dict with default price."""
    data = {
        "symbol": "TOKEN",
        "address": "0xabc",
        "decimals": 18,
    }
    spec = TokenSpec.from_dict(data)
    assert spec.price_usd == 0.0


def test_token_spec_from_dict_with_eth_equiv():
    """Test from_dict with eth_equiv_multiplier."""
    data = {
        "symbol": "TOKEN",
        "address": "0xabc",
        "decimals": 18,
        "eth_equiv_multiplier": {"numerator": 1, "denominator": 2},
    }
    spec = TokenSpec.from_dict(data)
    assert spec.eth_equiv_multiplier == {"numerator": 1, "denominator": 2}


def test_token_spec_from_dict_old_format_mult():
    """Test from_dict with old format multiplier."""
    data = {
        "symbol": "TOKEN",
        "address": "0xabc",
        "decimals": 18,
        "mult_num": 3,
        "mult_den": 4,
    }
    spec = TokenSpec.from_dict(data)
    assert spec.eth_equiv_multiplier == {"numerator": 3, "denominator": 4}


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


def test_profit_calculator_empty_specs():
    """Test calculator with no token specs."""
    calc = ProfitCalculator([], eth_price_usd=3000.0)
    result = calc.compute_usd({"UNKNOWN": 1000})
    assert result.total_usd == 0.0


def test_profit_calculator_unknown_token():
    """Test calculating profit with unknown token."""
    spec = TokenSpec("KNOWN", "0xabc", 18, 1.0)
    calc = ProfitCalculator([spec], eth_price_usd=3000.0)
    
    result = calc.compute_usd({"UNKNOWN": 1_000_000_000_000_000_000})
    assert result.total_usd == 0.0
    assert "UNKNOWN" not in result.by_token


def test_profit_calculator_multiple_tokens():
    """Test calculating profit with multiple tokens."""
    specs = [
        TokenSpec("USDC", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6, 1.0),
        TokenSpec("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18, 3000.0),
    ]
    calc = ProfitCalculator(specs, eth_price_usd=3000.0)
    
    # 1 USDC + 1 WETH
    result = calc.compute_usd({
        "USDC": 1_000_000,  # 1 USDC (6 decimals)
        "WETH": 1_000_000_000_000_000_000,  # 1 WETH (18 decimals)
    })
    
    assert result.by_token["USDC"] == pytest.approx(1.0, abs=0.01)
    assert result.by_token["WETH"] == pytest.approx(3000.0, abs=0.01)
    assert result.total_usd == pytest.approx(3001.0, abs=0.01)
