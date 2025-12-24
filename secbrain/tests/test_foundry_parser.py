import pytest

from secbrain.core.foundry_runner import ForgeOutputParser


def test_parse_profit_eth():
    """Test parsing ETH profit from forge output."""
    stdout = """
    Running test...
    Profit (ETH): 1.5
    Test passed
    """
    profit = ForgeOutputParser.parse_profit(stdout)
    assert profit == pytest.approx(1.5, abs=0.01)


def test_parse_profit_wei():
    """Test parsing wei amounts and converting to ETH."""
    stdout = """
    Running test...
    Profit (ETH-equivalent): 1500000000000000000
    Test passed
    """
    profit = ForgeOutputParser.parse_profit(stdout)
    assert profit == pytest.approx(1.5, abs=0.01)


def test_parse_tokens():
    """Test parsing token profits."""
    stdout = """
    Profit USDC: 1000000
    Profit WETH: 500000000000000000
    """
    tokens = ForgeOutputParser.parse_tokens(stdout)
    assert "USDC" in tokens
    assert "WETH" in tokens
    assert tokens["USDC"] == 1000000.0
