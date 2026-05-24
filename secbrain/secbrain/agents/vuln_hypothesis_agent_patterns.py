"""Vulnerability hypothesis patterns and scoring mixin."""

from __future__ import annotations

import logging
import math
import re
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from secbrain.agents.vuln_hypothesis_agent_base import BaseVulnHypothesisAgent
    _Base = BaseVulnHypothesisAgent
else:
    _Base = object

logger = logging.getLogger(__name__)

class VulnHypothesisPatternsMixin(_Base):
    """Mixin for hypothesis generation patterns and scoring."""

    def _static_vulnerability_patterns(
        self,
        *,
        abi: list[Any],
        functions: list[str],
        metadata: dict[str, Any],
        contract_address: str | None,
        chain_id: int | None,
        foundry_profile: str | None,
        solc: str | None,
        scope_profit_tokens: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Zero-cost heuristic hypotheses to reduce LLM dependence."""
        hypotheses: list[dict[str, Any]] = []
        funcs_lower = [f.lower() for f in functions]

        def add(vuln_type: str, rationale: str, confidence: float = 0.6) -> None:
            hypotheses.append(
                {
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "vuln_type": vuln_type,
                    "confidence": confidence,
                    "rationale": rationale,
                    "function_signature": functions[0] if functions else None,
                    "contract_address": contract_address,
                    "chain_id": chain_id,
                    "foundry_profile": foundry_profile,
                    "solc": solc,
                    "profit_tokens": scope_profit_tokens,
                    "status": "pending",
                }
            )

        # Storage collision / proxy patterns
        has_delegate = any("delegatecall" in f for f in funcs_lower)
        has_upgrade = any("upgrade" in f or "initialize" in f for f in funcs_lower)
        has_proxy_slot = any("eip1967" in f or "implementation" in f for f in funcs_lower)
        if has_delegate or has_proxy_slot or has_upgrade:
            add("storage_collision", "Delegatecall/proxy slot usage detected", 0.7)

        # Signature replay
        sig_keywords = ["ecrecover", "permit", "signature", "sig"]
        if any(any(k in f for k in sig_keywords) for f in funcs_lower):
            add("signature_replay", "Signature recovery detected; nonce/deadline unknown", 0.6)

        # First depositor inflation
        vault_keywords = ["deposit", "withdraw", "mint", "redeem", "totalassets", "totalsupply", "totalshares"]
        if any(any(k in f for k in vault_keywords) for f in funcs_lower):
            add("first_depositor_inflation", "Share-based vault semantics detected", 0.7)

        # Reentrancy hooks
        external_callers = ["call(", "delegatecall(", "staticcall("]
        if any(c in "".join(funcs_lower) for c in external_callers):
            add("reentrancy", "External call present; check ordering", 0.65)

        # Cross-function reentrancy
        withdraw_funcs = [f for f in funcs_lower if any(k in f for k in ["withdraw", "redeem", "claim"])]
        deposit_funcs = [f for f in funcs_lower if any(k in f for k in ["deposit", "mint", "stake"])]
        if withdraw_funcs and deposit_funcs:
            add("cross_function_reentrancy", f"Withdraw {withdraw_funcs[0]} paired with deposit/mint {deposit_funcs[0]}", 0.7)

        # Access control
        admin_keywords = ["owner", "admin", "governor", "upgrade", "pause", "set"]
        protected = any("only" in f or "auth" in f for f in funcs_lower)
        if any(any(k in f for k in admin_keywords) for f in funcs_lower) and not protected:
            add("access_control", "Admin-like functions without protection hints", 0.55)

        # Oracle hint
        if metadata.get("oracle_dependency"):
            add("oracle_manipulation", "Oracle dependency flagged in metadata", 0.75)

        # Precision / rounding
        precision_keywords = ["share", "rebalance", "round", "ceil", "floor"]
        if any(any(k in f for k in precision_keywords) for f in funcs_lower):
            add("precision_error", "Share/rounding semantics detected", 0.65)

        # MEV/Sandwich
        amm_keywords = ["swap", "router", "pair", "pool", "reserve"]
        price_keywords = ["price", "twap"]
        if any(any(k in f for k in amm_keywords) for f in funcs_lower) and any(any(k in f for k in price_keywords) for f in funcs_lower):
            add("mev_sandwich", "AMM-like swap + price functions detected", 0.65)

        # Unchecked arithmetic
        solc_version = metadata.get("solc")
        math_keywords = ["mul", "div", "add", "sub", "calc", "compute"]
        if solc_version and solc_version.startswith("0.8") and any(any(k in f for k in math_keywords) for f in funcs_lower):
            add("unchecked_arithmetic", f"Solc {solc_version} math functions could use unchecked{{}}", 0.55)

        # Advanced patterns
        view_funcs = [f for f in funcs_lower if "view" in f or "get" in f or "balanceof" in f or "totalsupply" in f]
        if view_funcs and any(c in "".join(funcs_lower) for c in external_callers):
            add("read_only_reentrancy", "View functions with external calls detected (read-only reentrancy risk)", 0.75)

        state_update_keywords = ["balance", "state", "storage", "mapping"]
        if any(c in "".join(funcs_lower) for c in external_callers) and any(any(k in f for k in state_update_keywords) for f in funcs_lower):
            add("cei_violation", "External calls with state updates (potential CEI violation)", 0.7)

        flash_keywords = ["flashloan", "borrow", "repay", "flashswap"]
        if any(any(k in f for k in flash_keywords) for f in funcs_lower):
            add("flash_loan_price_manipulation", "Flash loan functions detected", 0.8)
            add("same_block_borrow_repay", "Same-block borrow/repay pattern possible", 0.7)

        oracle_flash_keywords = ["price", "oracle", "twap", "reserve"]
        if any(any(k in f for k in flash_keywords) for f in funcs_lower) and any(any(k in f for k in oracle_flash_keywords) for f in funcs_lower):
            add("oracle_manipulation_flash", "Flash loan + oracle manipulation risk", 0.85)

        role_keywords = ["role", "permission", "grant", "revoke"]
        if any(any(k in f for k in admin_keywords) for f in funcs_lower) and not any(any(k in f for k in role_keywords) for f in funcs_lower):
            add("role_based_access_needed", "Admin functions without role-based access control", 0.65)

        frontrun_keywords = ["bid", "auction", "vote", "random", "lottery", "commit", "reveal"]
        if any(any(k in f for k in frontrun_keywords) for f in funcs_lower) and not any("commit" in f and "reveal" in f for f in funcs_lower):
            add("missing_commit_reveal", "Front-running vulnerable functions without commit-reveal", 0.6)

        if any(any(k in f for k in sig_keywords) for f in funcs_lower) and not any("eip712" in f or "typehash" in f for f in funcs_lower):
            add("missing_eip712_signature", "Signatures without EIP-712 protection", 0.55)

        oracle_keywords = ["oracle", "price", "feed", "chainlink", "aggregator"]
        if any(any(k in f for k in oracle_keywords) for f in funcs_lower):
            if not any("timestamp" in f or "updatedat" in f or "roundid" in f for f in funcs_lower):
                add("stale_price_data", "Oracle price feed without staleness checks", 0.75)
            if not any("twap" in f or "median" in f or "consensus" in f for f in funcs_lower):
                add("single_oracle_dependency", "Single oracle dependency without redundancy", 0.65)
            spot_price_keywords = ["spot", "instant", "current"]
            if any(any(k in f for k in spot_price_keywords) for f in funcs_lower) and not any("twap" in f for f in funcs_lower):
                add("missing_twap", "Spot price usage without TWAP protection", 0.7)
            if not any("deviation" in f or "threshold" in f or "limit" in f for f in funcs_lower):
                add("no_price_deviation_check", "Oracle without price deviation checks", 0.6)

        return hypotheses

    def _validate_hypothesis(self, hyp: dict[str, Any]) -> bool:
        """Validate hypothesis has required fields and valid data."""
        required_fields = ["vuln_type", "confidence", "contract_address", "function_signature"]
        for required_field in required_fields:
            if required_field not in hyp or not hyp[required_field]:
                return False

        try:
            self._checksum_address(hyp["contract_address"])
        except (ValueError, TypeError):
            return False

        try:
            conf = float(hyp["confidence"])
            if not 0.0 <= conf <= 1.0:
                return False
        except (TypeError, ValueError):
            return False

        func_sig = hyp["function_signature"]
        if not isinstance(func_sig, str) or not re.match(r"^[a-zA-Z_]\w*\([^)]*\)$", func_sig):
            return False

        # Use the allowed types from the base class schema
        valid_vuln_types = set(self.HYPOTHESIS_SCHEMA["items"]["properties"]["vuln_type"]["enum"])
        if hyp["vuln_type"] not in valid_vuln_types:
            return False

        return True

    def _feasibility_gate(self, hyp: dict[str, Any], abi: list[Any], functions: list[str] | None = None) -> bool:
        """Eliminate impossible hypotheses before downstream execution."""
        func_sig = hyp.get("function_signature")
        if not func_sig:
            return False
        fn_name = str(func_sig).split("(")[0]
        abi_entry = self._get_abi_entry(fn_name, abi)
        if not abi_entry:
            return False

        state_mut = str(abi_entry.get("stateMutability") or "")
        if state_mut in {"view", "pure"}:
            return False
        if hyp.get("requires_payable") and state_mut != "payable":
            return False

        if hyp.get("vuln_type") in {"oracle_manipulation"}:
            oracle_info = self._oracle_detector.detect_oracle_dependency(abi, functions or [])
            if not oracle_info.get("has_oracle"):
                return False

        if hyp.get("vuln_type") in {"cross_function_reentrancy"}:
            lowers = [f.lower() for f in functions or []]
            has_withdraw = any(k in f for f in lowers for k in ["withdraw", "redeem", "claim"])
            has_deposit = any(k in f for f in lowers for k in ["deposit", "mint", "stake"])
            if not (has_withdraw and has_deposit):
                return False

        return True

    def _get_abi_entry(self, fn_name: str, abi: list[Any]) -> dict[str, Any] | None:
        for item in abi or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "function":
                continue
            if item.get("name") == fn_name:
                return item
        return None

    def _rank_hypotheses(self, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rank hypotheses by exploitability and profit signal."""
        def score(h: dict[str, Any]) -> float:
            confidence = float(h.get("confidence", 0))
            est_profit = float(h.get("expected_profit_hint_eth", 0) or 0)

            severity_weight = {
                "oracle_manipulation": 1.0,
                "oracle_manipulation_flash": 1.0,
                "mev": 0.95,
                "mev_sandwich": 0.95,
                "sandwich": 0.95,
                "flash_loan": 0.9,
                "flash_loan_price_manipulation": 0.9,
                "reentrancy": 0.9,
                "read_only_reentrancy": 0.85,
                "cross_function_reentrancy": 0.85,
                "cei_violation": 0.85,
                "precision": 0.8,
                "precision_error": 0.8,
                "round": 0.8,
                "first_depositor_inflation": 0.8,
                "access_control": 0.75,
                "missing_access_control": 0.75,
                "role_based_access_needed": 0.7,
                "integer": 0.7,
                "unchecked_arithmetic": 0.7,
                "unchecked_call": 0.65,
                "delegatecall": 0.65,
                "delegatecall_confusion": 0.65,
                "storage_collision": 0.65,
                "signature_replay": 0.6,
                "state_inconsistency": 0.6,
                "same_block_borrow_repay": 0.6,
                "stale_price_data": 0.55,
                "single_oracle_dependency": 0.55,
                "generic_contract": 0.5,
            }
            vt = h.get("vuln_type", "").lower()
            sev_bonus = max((weight for key, weight in severity_weight.items() if key in vt), default=0.4)
            profit_score = math.log1p(est_profit) / math.log1p(100) if est_profit > 0 else 0.0
            profit_score = min(profit_score, 1.0)
            missing_penalty = 0.2 if (not h.get("contract_address") or not h.get("function_signature")) else 0.0

            return (confidence * 0.5 + sev_bonus * 0.3 + profit_score * 0.2 - missing_penalty)

        ranked = sorted(hypotheses, key=score, reverse=True)
        for idx, h in enumerate(ranked):
            h["exploit_score"] = round(score(h), 4)
            h["rank"] = idx + 1
        return ranked

    def _heuristic_enrich_hypotheses(
        self,
        existing: list[dict[str, Any]],
        *,
        address: str,
        name: str,
        chain_id: int | None,
        foundry_profile: str | None,
        solc: str | None,
        abi: list[Any],
        functions: list[str],
        scope_profit_tokens: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Heuristically enrich hypotheses with additional information."""
        enriched: list[dict[str, Any]] = []
        for h in existing:
            v_type = h.get("vuln_type")
            if v_type in {"mev_sandwich", "precision_error"}:
                new_hyp = h.copy()
                new_hyp["id"] = f"hyp-{uuid.uuid4().hex[:8]}"
                new_hyp["foundry_profile"] = foundry_profile
                new_hyp["solc"] = solc
                new_hyp["abi"] = abi
                new_hyp["profit_tokens"] = scope_profit_tokens
                new_hyp["status"] = "pending"
                enriched.append(new_hyp)
        return enriched

    def _group_by_type(self, hypotheses: list[dict[str, Any]]) -> dict[str, int]:
        """Group hypotheses by vulnerability type."""
        counts: dict[str, int] = {}
        for h in hypotheses:
            vtype = h.get("vuln_type", "unknown")
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts
