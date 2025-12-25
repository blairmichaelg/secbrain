import pytest

from secbrain.agents.exploit_agent import ExploitAgent


class _DummyRunContext:
    """Minimal stub to satisfy BaseAgent expectations."""

    def __init__(self):
        self.workspace_path = "."
        self.worker_model = None
        self.advisor_model = None

    def is_killed(self):
        return False


def test_compute_profit_eth_equiv_with_tokens():
    agent = ExploitAgent(run_context=_DummyRunContext())
    attempt = {
        "profit_tokens": {
            "USDC": 1_000_000,  # 1 USDC with 6 decimals
        }
    }
    scope_tokens = [
        {
            "symbol": "USDC",
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "decimals": 6,
            "price_usd": 1.0,
            "mult_num": 1,
            "mult_den": 1,
        }
    ]

    eth_equiv, breakdown, profit_usd = agent._compute_profit_eth_equiv(attempt, chain_id=1, scope_profit_tokens=scope_tokens)

    assert eth_equiv == pytest.approx(1.0)
    assert breakdown == {"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": pytest.approx(1.0)}
    assert profit_usd == pytest.approx(1.0)


def test_compute_profit_eth_equiv_handles_missing_tokens():
    agent = ExploitAgent(run_context=_DummyRunContext())
    attempt = {"profit_tokens": {"UNKNOWN": 123}}

    eth_equiv, breakdown, profit_usd = agent._compute_profit_eth_equiv(attempt, chain_id=1, scope_profit_tokens=[])

    assert eth_equiv == 0.0
    assert breakdown == {}
    assert profit_usd == 0.0


def test_compute_profit_eth_equiv_uses_price_cache():
    agent = ExploitAgent(run_context=_DummyRunContext())
    attempt = {"profit_tokens": {"WETH": 10 * 10**18}}  # 10 WETH
    scope_tokens = [
        {"symbol": "WETH", "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "decimals": 18, "mult_num": 1, "mult_den": 1},
    ]
    price_cache = {"weth": 2000.0}
    eth_equiv, _breakdown, profit_usd = agent._compute_profit_eth_equiv(
        attempt,
        chain_id=1,
        scope_profit_tokens=scope_tokens,
        price_cache=price_cache,
    )
    assert eth_equiv == pytest.approx(10.0)
    assert profit_usd == pytest.approx(20000.0)
