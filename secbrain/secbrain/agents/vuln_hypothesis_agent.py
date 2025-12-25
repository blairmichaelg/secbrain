"""Vulnerability hypothesis agent - generates hypotheses for testing.

This module provides the VulnHypothesisAgent which:
- Generates vulnerability hypotheses from static analysis and recon data
- Scores and prioritizes hypotheses based on severity and likelihood
- Integrates with oracle manipulation detection
- Produces structured hypothesis data for exploit attempts
- Handles ABI analysis and function signature extraction
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, ClassVar

from eth_utils import is_address, to_checksum_address
from jsonschema import ValidationError, validate

from secbrain.agents.base import AgentResult, BaseAgent
from secbrain.agents.oracle_manipulation_detector import OracleManipulationDetector

logger = logging.getLogger(__name__)

# ABI preview limits for prompt generation
ABI_PREVIEW_MAX_ENTRIES = 30  # Maximum number of ABI entries to include
ABI_PREVIEW_REDUCED_ENTRIES = 15  # Reduced number if JSON is too large
ABI_JSON_SIZE_LIMIT = 1500  # Maximum JSON string length for ABI preview
FUNCTIONS_PREVIEW_LIMIT = 15  # Maximum number of function signatures to preview


@dataclass(slots=True)
class ProtocolProfile:
    """Protocol-aware sampling configuration."""

    protocol_type: str
    budget: int
    patterns: list[str] = field(default_factory=list)
    description: str = ""

    _DEFAULT_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "defi_vault": [
            "share_inflation",
            "rebasing_extraction",
            "flash_loan_drainage",
            "oracle_manipulation",
            "fee_extraction",
            "restaking_share_inflation",
            "avs_integration_flaw",
        ],
        "amm": [
            "sandwich_attack",
            "price_manipulation",
            "slippage_extraction",
            "flash_loan_arbitrage",
            "pool_balance_manipulation",
            "intent_front_running",
            "solver_collusion",
            "dutch_auction_manipulation",
        ],
        "lending": [
            "collateral_extraction",
            "liquidation_oracle_attack",
            "reserve_drainage",
            "interest_manipulation",
            "flashloan_liquidation_loop",
        ],
        "governance": [
            "admin_key_extraction",
            "voting_manipulation",
            "timelock_bypass",
            "parameter_extraction",
            "treasury_drainage",
        ],
        "bridge": [
            "bitcoin_peg_manipulation",
            "wallet_registry_compromise",
            "bridge_funds_theft",
            "deposit_sweep_manipulation",
            "redemption_proof_forgery",
            "cross_chain_message_forgery",
            "relay_message_manipulation",
            "zk_proof_verification_flaw",
            "optimistic_challenge_bypass",
        ],
        "threshold_network": [
            "bitcoin_peg_manipulation",
            "wallet_registry_compromise",
            "threshold_signature_manipulation",
            "dkg_protocol_attack",
            "operator_collusion",
            "cross_chain_message_forgery",
            "staking_reward_manipulation",
            "governance_vote_buying",
            "proxy_upgrade_exploit",
            "zk_proof_verification_flaw",
            "optimistic_challenge_bypass",
            "mev_extraction_vulnerability",
            "withdrawal_queue_manipulation",
            "slashing_mechanism_bypass",
        ],
        "account_abstraction": [
            "account_abstraction_exploit",
            "paymaster_exploitation",
            "userop_validation_bypass",
            "session_key_compromise",
        ],
        "generic": [
            "reentrancy",
            "access_control",
            "integer_overflow",
            "unchecked_call",
            "delegatecall_confusion",
        ],
    }

    _BUDGETS: ClassVar[dict[str, int]] = {
        "defi_vault": 10,
        "amm": 8,
        "lending": 10,
        "governance": 6,
        "bridge": 12,
        "threshold_network": 15,
        "account_abstraction": 8,
        "generic": 5,
    }

    _DESCRIPTIONS: ClassVar[dict[str, str]] = {
        "defi_vault": "Focus on vault share accounting, rebasing, and flash-loanable TVL manipulations.",
        "amm": "Focus on swap routing, price manipulation, MEV-prone flow control, and intent-based trading.",
        "lending": "Prioritize collateral, liquidation, and reserve accounting exploits.",
        "governance": "Prioritize voting power escalation, timelock bypass, and treasury drains.",
        "bridge": "Focus on cross-chain message forgery, proof verification, ZK proof flaws, and relay manipulation.",
        "threshold_network": "Prioritize tBTC bridge security, threshold cryptography, operator collusion, MEV, withdrawal queues, and cross-chain attacks per Immunefi bounty program.",
        "account_abstraction": "Focus on EIP-4337 UserOperation validation, paymaster exploits, session key security, and bundler manipulation.",
        "generic": "Use broad on-chain exploit classes (reentrancy, access control, arithmetic).",
    }

    @classmethod
    def from_type(cls, protocol_type: str | None) -> ProtocolProfile:
        key = (protocol_type or "generic").lower()
        patterns = list(cls._DEFAULT_PATTERNS.get(key, cls._DEFAULT_PATTERNS["generic"]))
        budget = cls._BUDGETS.get(key, cls._BUDGETS["generic"])
        desc = cls._DESCRIPTIONS.get(key, cls._DESCRIPTIONS["generic"])
        return cls(protocol_type=key, budget=budget, patterns=patterns, description=desc)


class VulnHypothesisAgent(BaseAgent):
    """
    Vulnerability hypothesis agent.

    Responsibilities:
    - Generates vulnerability hypotheses per asset/endpoint
    - Research substep for validation
    - Advisor review at the end
    """

    name = "vuln_hypothesis"
    phase = "hypothesis"
    CONFIDENCE_THRESHOLD: ClassVar[float] = 0.4

    HYPOTHESIS_SCHEMA: ClassVar[dict[str, Any]] = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["vuln_type", "confidence"],
            "properties": {
                "vuln_type": {
                    "type": "string",
                    "enum": [
                        "reentrancy",
                        "access_control",
                        "integer_overflow",
                        "unchecked_call",
                        "delegatecall_confusion",
                        "oracle_manipulation",
                        "flash_loan",
                        "mev_sandwich",
                        "precision_error",
                        "state_inconsistency",
                        "generic_contract",
                        "storage_collision",
                        "signature_replay",
                        "first_depositor_inflation",
                        "cross_function_reentrancy",
                        "unchecked_arithmetic",
                        # Advanced patterns (2023-2024)
                        "read_only_reentrancy",
                        "cei_violation",
                        "flash_loan_price_manipulation",
                        "flash_loan_governance_attack",
                        "same_block_borrow_repay",
                        "oracle_manipulation_flash",
                        "missing_access_control",
                        "weak_access_control",
                        "role_based_access_needed",
                        "front_running_vulnerable",
                        "missing_commit_reveal",
                        "no_timelock",
                        "missing_eip712_signature",
                        "stale_price_data",
                        "single_oracle_dependency",
                        "missing_twap",
                        "no_price_deviation_check",
                        # Threshold Network specific patterns (Immunefi bounty)
                        "bitcoin_peg_manipulation",
                        "wallet_registry_compromise",
                        "bridge_funds_theft",
                        "deposit_sweep_manipulation",
                        "redemption_proof_forgery",
                        "guardian_key_compromise",
                        "optimistic_minting_exploit",
                        "threshold_signature_manipulation",
                        "dkg_protocol_attack",
                        "operator_collusion",
                        "signing_group_corruption",
                        "random_beacon_manipulation",
                        "cross_chain_message_forgery",
                        "wormhole_bridge_exploit",
                        "starknet_bridge_attack",
                        "relay_message_manipulation",
                        "cross_chain_reentrancy",
                        "staking_reward_manipulation",
                        "delegation_attack",
                        "governance_vote_buying",
                        "timelock_bypass",
                        "proxy_upgrade_exploit",
                        "token_ratio_manipulation",
                        "vending_machine_exploit",
                        "legacy_token_double_spend",
                        # New 2024-2025 patterns
                        "zk_proof_verification_flaw",
                        "optimistic_challenge_bypass",
                        "mev_extraction_vulnerability",
                        "withdrawal_queue_manipulation",
                        "slashing_mechanism_bypass",
                        "account_abstraction_exploit",
                        "paymaster_exploitation",
                        "userop_validation_bypass",
                        "session_key_compromise",
                        "intent_front_running",
                        "solver_collusion",
                        "dutch_auction_manipulation",
                        "restaking_share_inflation",
                        "avs_integration_flaw",
                    ],
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "contract_address": {"type": "string"},
                "function_signature": {"type": "string"},
                "rationale": {"type": "string"},
                "attack_description": {"type": "string"},
                "expected_profit_hint_eth": {"type": "number", "minimum": 0},
                "exploit_notes": {"type": "array"},
            },
        },
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._oracle_detector = OracleManipulationDetector()
        # Configurable concurrency limits
        scope = getattr(self.run_context, "scope", None)
        if scope is None:
            class _DefaultScope:
                max_llm_concurrent = 5
            scope = _DefaultScope()
            self.run_context.scope = scope
        self._max_llm_concurrent = getattr(scope, "max_llm_concurrent", 5)
        self._contract_llm_sem = asyncio.Semaphore(self._max_llm_concurrent)

        # Add hypothesis enhancer
        self.hyp_enhancer = None
        if self.research_orch:
            from secbrain.agents.hypothesis_enhancer import HypothesisEnhancer

            self.hyp_enhancer = HypothesisEnhancer(self.research_orch)

    async def run(self, **kwargs: Any) -> AgentResult:
        """Generate vulnerability hypotheses."""
        self._log("starting_hypothesis_generation")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        recon_data = kwargs.get("recon_data", {})
        assets = recon_data.get("assets", [])
        technologies = recon_data.get("technologies", [])

        if not assets:
            return self._failure("No assets available for hypothesis generation")

        # Generate hypotheses for each asset type
        all_hypotheses: list[dict[str, Any]] = []

        # Filter to live hosts for hypothesis generation
        live_hosts = [a for a in assets if a.get("type") == "live_host"]

        # Filter to contracts for hypothesis generation
        contract_assets = [a for a in assets if a.get("type") == "contract"]

        # Parallelize with modest bounds to avoid flooding LLM or RPC
        host_sem = asyncio.Semaphore(5)

        async def _gen_host(asset: dict[str, Any]) -> list[dict[str, Any]]:
            async with host_sem:
                return await self._generate_hypotheses_for_asset(asset, technologies)

        host_tasks = [asyncio.create_task(_gen_host(h)) for h in live_hosts[:10]]
        if host_tasks:
            host_results = await asyncio.gather(*host_tasks)
            for hs in host_results:
                all_hypotheses.extend(hs or [])

        # Batch contract hypotheses to reduce sequential LLM calls
        if contract_assets:
            contract_batches = await self._generate_batch_hypotheses(contract_assets, batch_size=10)
            for batch in contract_batches:
                all_hypotheses.extend(batch or [])

        # Research: validate hypothesis viability
        if all_hypotheses and self.research_client:
            all_hypotheses = await self._research_validate_hypotheses(all_hypotheses)

        # Sort by exploit focus and cut to top 5 with confidence threshold
        ranked = self._rank_hypotheses(all_hypotheses)
        confidence_threshold = self.CONFIDENCE_THRESHOLD
        filtered = [h for h in ranked if h.get("confidence", 0) >= confidence_threshold]
        top_hypotheses = filtered[:5]
        self._log(
            "hypothesis_confidence_filter",
            total=len(ranked),
            above_threshold=len(filtered),
            threshold=confidence_threshold,
        )

        # Fallback: If no hypotheses above threshold, create generic ones from contract assets
        if not top_hypotheses and contract_assets:
            self._log("generating_fallback_hypotheses", contract_count=len(contract_assets))
            fallback_hypotheses = self._generate_fallback_hypotheses(contract_assets[:3])
            # Combine with existing hypotheses and re-rank
            all_hypotheses.extend(fallback_hypotheses)
            ranked = self._rank_hypotheses(all_hypotheses)
            filtered = [h for h in ranked if h.get("confidence", 0) >= confidence_threshold]
            top_hypotheses = filtered[:5]

        review = await self._advisor_review_hypotheses(top_hypotheses)

        missing_targets = [h for h in ranked if not h.get("contract_address") or not h.get("function_signature")]
        if missing_targets:
            self._log(
                "hypotheses_missing_contract_or_function",
                count=len(missing_targets),
                total=len(ranked),
            )
            # Expose summary in data for downstream metrics
            missing_summary = {
                "missing_contract_or_function": len(missing_targets),
                "total_hypotheses": len(ranked),
            }
        else:
            missing_summary = {"missing_contract_or_function": 0, "total_hypotheses": len(ranked)}

        # Store hypotheses
        if self.storage:
            for hyp in all_hypotheses:
                await self.storage.save_hypothesis(hyp)

        return self._success(
            message=f"Generated {len(all_hypotheses)} hypotheses",
            data={
                "hypotheses": ranked,
                "top_hypotheses": top_hypotheses,
                "review": review,
                "by_vuln_type": self._group_by_type(all_hypotheses),
                "missing_targets": missing_summary,
            },
            next_actions=["exploit"],
        )

    async def _generate_batch_hypotheses(
        self,
        contracts: list[dict[str, Any]],
        batch_size: int = 10,
    ) -> list[list[dict[str, Any]]]:
        """Generate hypotheses for multiple contracts in batches."""
        results: list[list[dict[str, Any]]] = []

        for i in range(0, len(contracts), batch_size):
            batch = contracts[i : i + batch_size]
            batch_tasks = [
                asyncio.create_task(self._generate_hypotheses_for_contract_asset(contract))
                for contract in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for contract, result in zip(batch, batch_results, strict=False):
                if isinstance(result, Exception):
                    self._log_error(
                        "batch_hypothesis_failed",
                        contract=contract.get("name"),
                        error=str(result),
                    )
                    results.append([])
                else:
                    results.append(result or [])

        return results

    async def _generate_hypotheses_for_contract_asset(
        self,
        asset: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate vulnerability hypotheses for a single contract asset."""
        try:
            contract_address = self._checksum_address(asset.get("value"))
        except ValueError as e:
            self._log_error(
                "invalid_contract_address_skipping",
                contract=asset.get("name"),
                address=asset.get("value"),
                error=str(e),
            )
            return []
        address = contract_address
        name = asset.get("name", "")
        chain_id = asset.get("chain_id")
        foundry_profile = asset.get("foundry_profile") or asset.get("profile")
        metadata = asset.get("metadata", {})
        functions = metadata.get("functions", []) or []
        abi = metadata.get("abi", []) or []
        solc = metadata.get("solc")

        scope_profit_tokens = []
        try:
            scope_profit_tokens = getattr(getattr(self.run_context, "scope", None), "profit_tokens", None) or []
        except Exception:
            scope_profit_tokens = []

        # Static patterns: zero-cost heuristics before LLM
        static_hypotheses = [
            hyp
            for hyp in self._static_vulnerability_patterns(
                abi=abi,
                functions=functions,
                metadata=metadata,
                contract_address=address,
                chain_id=chain_id,
                foundry_profile=foundry_profile,
                solc=solc,
                scope_profit_tokens=scope_profit_tokens,
            )
            if self._feasibility_gate(hyp, abi, functions) and self._validate_hypothesis(hyp)
        ]

        # If static signals are strong and numerous, skip LLM to save cost/latency
        static_conf_ok = [h for h in static_hypotheses if float(h.get("confidence", 0)) >= 0.6]
        if len(static_conf_ok) >= 3:
            return static_hypotheses

        # Keep prompts bounded
        functions_preview = functions[:FUNCTIONS_PREVIEW_LIMIT]
        abi_preview = abi[:ABI_PREVIEW_MAX_ENTRIES]
        try:
            # Limit ABI entries before serialization to avoid invalid JSON
            if len(json.dumps(abi_preview)) > ABI_JSON_SIZE_LIMIT:
                # If still too long, reduce ABI entries further
                abi_preview = abi[:ABI_PREVIEW_REDUCED_ENTRIES]
        except Exception:
            # On serialization failure, fall back to a smaller preview slice
            abi_preview = abi[:ABI_PREVIEW_REDUCED_ENTRIES]

        classification = (asset.get("metadata", {}) or {}).get("classification", {})
        protocol_type = classification.get("protocol_type", "generic")
        profile = ProtocolProfile.from_type(protocol_type)
        pattern_hint = ", ".join(profile.patterns)
        pool_registry = None
        try:
            pool_registry = getattr(getattr(self.run_context, "scope", None), "pool_registry", None)
        except Exception:
            pool_registry = None

        lower_functions = [fn.lower() for fn in functions]
        existing_types: set[str] = set()
        has_deposit = any("deposit" in fn for fn in lower_functions)
        has_withdraw = any("withdraw" in fn for fn in lower_functions)
        has_share = any("share" in fn for fn in lower_functions)

        # Use research_attack_vectors for real-world attack pattern data
        research_context = ""
        if self.research_client and pattern_hint:
            # Research attack vectors for the primary vulnerability pattern
            primary_pattern = profile.patterns[0] if profile.patterns else protocol_type
            try:
                research_result = await self.research_client.research_attack_vectors(
                    vuln_type=primary_pattern,
                    run_context=self.run_context,
                    contract_pattern=f"{protocol_type} with functions: {', '.join(functions_preview[:5])}",
                )
                if not research_result.get("error") and not research_result.get("limited"):
                    research_context = f"\n\nReal-world attack vectors for {primary_pattern}:\n{research_result.get('answer', '')[:400]}\n"  # Reduced from 600
            except Exception as e:
                self._log_error("research_attack_vectors_failed", error=str(e))

        prompt = f"""Contract: {name} ({address})
Chain: {chain_id}
Protocol: {protocol_type}
Functions (sample): {', '.join(functions_preview[:8])}

{research_context}

Generate 3-5 exploit hypotheses as a JSON array.

Each hypothesis MUST be a JSON object with at least these required fields:
- "vuln_type": short name of the vulnerability class
- "confidence": numeric confidence score in [0,1]

Optional fields you MAY include:
- "contract_address": the checksum address of the target contract (use "{address}")
- "chain_id": the numeric chain id (use {chain_id})
- "function_signature": primary function or entrypoint involved, if any
- "rationale": explanation of why this hypothesis is plausible
- "exploit_notes": array of short notes or assumptions

Example JSON object:
{{"vuln_type":"share_inflation","confidence":0.8,"rationale":"short explanation","function_signature":"deposit(uint256)","exploit_notes":["note 1","note 2"]}}

Always return a pure JSON array of such objects. Focus on {protocol_type}-specific high-severity issues."""

        async with self._contract_llm_sem:
            # Define precision-related keywords and checks for use in multiple blocks
            precision_keywords = ["share", "rebalance", "mint", "redeem", "deposit", "withdraw", "round", "ceil", "floor"]
            has_deposit = any("deposit" in fn for fn in lower_functions)
            has_withdraw = any("withdraw" in fn for fn in lower_functions)
            has_share = any("share" in fn for fn in lower_functions)

            if "mev_sandwich" not in existing_types:
                mev_keywords = ["swap", "router", "pair", "pool", "uniswap", "curve", "balancer"]
                price_keywords = ["price", "reserve", "twap"]
                has_swap = any("swap" in fn for fn in lower_functions)
                has_pool = any("pair" in fn or "pool" in fn for fn in lower_functions)
                has_price = any(any(pk in fn for pk in price_keywords) for fn in lower_functions)
                if has_swap and has_pool and has_price and any(any(k in fn for k in mev_keywords) for fn in lower_functions) and (has_deposit or has_withdraw or has_share):
                    prompt += f"""

Additional note: The contract contains functions that may be vulnerable to precision errors, such as {', '.join(precision_keywords)}. Please consider this when generating hypotheses."""

            if "precision_error" not in existing_types and (has_deposit or has_withdraw or has_share):
                prompt += f"""

Additional note: The contract contains functions that may be vulnerable to precision errors, such as {', '.join(precision_keywords)}. Please consider this when generating hypotheses."""

            response = await self._call_worker(prompt)
        raw_hypotheses = await self._parse_hypotheses_with_validation(
            response=response,
            contract_name=name,
            chain_id=chain_id,
            functions=functions,
            address=address,
            functions_preview=functions_preview,
        )

        # Combine static + LLM results
        combined_hypotheses = list(static_hypotheses)
        if raw_hypotheses:
            hypotheses: list[dict[str, Any]] = []
            for h in raw_hypotheses:
                func_sig = h.get("function_signature") or (functions[0] if functions else None)
                fn_name = (str(func_sig).split("(")[0] if func_sig else "").strip()
                abi_entry: dict[str, Any] | None = None
                if fn_name and isinstance(abi, list):
                    for item in abi:
                        if not isinstance(item, dict):
                            continue
                        if item.get("type") != "function":
                            continue
                        if item.get("name") == fn_name:
                            abi_entry = item
                            break

                state_mutability = ""
                param_types: list[str] = []
                returns_value = False
                is_payable = False
                writes_state = False
                if abi_entry:
                    state_mutability = str(abi_entry.get("stateMutability") or "")
                    inputs = abi_entry.get("inputs") or []
                    outputs = abi_entry.get("outputs") or []
                    if isinstance(inputs, list):
                        for inp in inputs:
                            if isinstance(inp, dict) and inp.get("type"):
                                param_types.append(str(inp.get("type")))
                    returns_value = isinstance(outputs, list) and len(outputs) > 0
                    is_payable = state_mutability == "payable"
                    writes_state = state_mutability in {"nonpayable", "payable"}

                # Oracle manipulation augmentation
                oracle_detector = OracleManipulationDetector()
                oracle_info = oracle_detector.detect_oracle_dependency(abi, functions)
                if oracle_info.get("has_oracle"):
                    self._log(
                        "oracle_functions_detected",
                        contract=name,
                        address=address,
                        oracle_functions=oracle_info.get("oracle_functions"),
                        phase=self.phase,
                        agent=self.name,
                    )
                exploit_notes = h.get("exploit_notes", [])
                exploit_body = h.get("exploit_body")
                if oracle_info.get("has_oracle") and h.get("vuln_type") == "oracle_manipulation":
                    exploit_body = oracle_detector.generate_manipulation_exploit(
                        {"contract_address": h.get("contract_address") or address},
                        oracle_info,
                        pool_registry=pool_registry,
                    )
                    exploit_notes = exploit_notes or [
                        "Flash swap to skew reserves",
                        "Oracle reads manipulated price",
                        "Execute price-dependent path",
                    ]
                    self._log(
                        "oracle_vulnerability_detected",
                        contract=name,
                        address=address,
                        oracle_functions=oracle_info.get("oracle_functions"),
                    )

                normalized_addr = self._validate_and_normalize_address(
                    h.get("contract_address") or contract_address,
                    context="hypothesis",
                )
                if not normalized_addr:
                    continue

                candidate = {
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "asset_id": asset.get("id"),
                    "target": f"{name}@{address}" if name else address,
                    "vuln_type": h.get("vuln_type", "unknown"),
                    "confidence": min(max(float(h.get("confidence", 0.5)), 0.0), 1.0),
                    "rationale": h.get("rationale", ""),
                    "test_approach": h.get("test_approach", ""),
                    "contract_address": normalized_addr,
                    "chain_id": h.get("chain_id") or chain_id,
                    "function_signature": func_sig,
                    "foundry_profile": foundry_profile,
                    "solc": solc,
                    "abi": abi,
                    "oracle_functions": oracle_info.get("oracle_functions"),
                    "profit_tokens": scope_profit_tokens,
                    "exploit_notes": h.get("exploit_notes", []),
                    "expected_profit_hint_eth": h.get("expected_profit_hint_eth"),
                    "function_state_mutability": state_mutability,
                    "function_is_payable": is_payable,
                    "function_writes_state": writes_state,
                    "function_returns_value": returns_value,
                    "function_param_count": len(param_types),
                    "function_param_types": param_types,
                    "exploit_body": exploit_body,
                    "status": "pending",
                }

                if not self._feasibility_gate(candidate, abi):
                    self._log("hypothesis_infeasible_dropped", hypothesis=candidate)
                    continue
                if not self._validate_hypothesis(candidate):
                    self._log("invalid_hypothesis_discarded", hypothesis=candidate)
                    continue

                hypotheses.append(candidate)

            # Heuristic enrichment for MEV/sandwich and precision/rounding issues
            hypotheses.extend(
                self._heuristic_enrich_hypotheses(
                    hypotheses,
                    address=address,
                    name=name,
                    chain_id=chain_id,
                    foundry_profile=foundry_profile,
                    solc=solc,
                    abi=abi,
                    functions=functions,
                    scope_profit_tokens=scope_profit_tokens,
                )
            )

            # If oracle functions detected but not already captured, add a dedicated oracle hypothesis
            oracle_info = self._oracle_detector.detect_oracle_dependency(abi, functions)
            if oracle_info.get("has_oracle"):
                oracle_sig = oracle_info["oracle_functions"][0] if oracle_info["oracle_functions"] else (functions[0] if functions else None)
                exploit_body = self._oracle_detector.generate_manipulation_exploit(
                    {"contract_address": address},
                    oracle_info,
                    pool_registry=pool_registry,
                )
                normalized_addr = self._validate_and_normalize_address(address, context="hypothesis_oracle")
                if normalized_addr:
                    hypotheses.append({
                        "id": f"hyp-{uuid.uuid4().hex[:8]}",
                        "asset_id": asset.get("id"),
                        "target": f"{name}@{address}" if name else address,
                        "vuln_type": "oracle_manipulation",
                        "confidence": 0.85,
                        "rationale": f"Detected oracle functions: {', '.join(oracle_info['oracle_functions'])}",
                        "test_approach": "Manipulate oracle via flash swap and trigger price-dependent path.",
                        "contract_address": normalized_addr,
                        "chain_id": chain_id,
                        "function_signature": oracle_sig,
                        "foundry_profile": foundry_profile,
                        "solc": solc,
                        "abi": abi,
                        "profit_tokens": scope_profit_tokens,
                        "exploit_notes": [
                            "Flash swap to skew reserves",
                            "Oracle reads manipulated price",
                            "Execute settlement with favorable price",
                        ],
                        "expected_profit_hint_eth": 5.0,
                        "function_state_mutability": state_mutability,
                        "function_is_payable": is_payable,
                        "function_writes_state": writes_state,
                        "function_returns_value": returns_value,
                        "function_param_count": len(param_types),
                        "function_param_types": param_types,
                        "status": "pending",
                        "exploit_body": exploit_body,
                    })

            combined_hypotheses.extend(hypotheses[: profile.budget])

        else:
            normalized_addr = self._validate_and_normalize_address(address, context="hypothesis_fallback")
            if not normalized_addr:
                return []

            combined_hypotheses.append({
                "id": f"hyp-{uuid.uuid4().hex[:8]}",
                "asset_id": asset.get("id"),
                "target": f"{name}@{address}" if name else address,
                "vuln_type": "generic_contract",
                "confidence": 0.3,
                "rationale": "Generic on-chain testing hypothesis",
                "test_approach": "Write a forked Foundry test for common exploit patterns",
                "contract_address": normalized_addr,
                "chain_id": chain_id,
                "function_signature": functions[0] if functions else None,
                "foundry_profile": foundry_profile,
                "solc": solc,
                "abi": abi,
                "profit_tokens": scope_profit_tokens,
                "status": "pending",
            })

        return combined_hypotheses

    async def _parse_hypotheses_with_validation(
        self,
        response: str,
        contract_name: str,
        chain_id: int | None,
        functions: list[str],
        address: str,
        functions_preview: list[str],
        max_retries: int = 2,
    ) -> list[dict[str, Any]]:
        """Parse hypothesis JSON with schema validation and corrective prompting."""

        def _extract_json_array(text: str) -> list[dict[str, Any]]:
            """Extract JSON array from LLM response with multiple fallback strategies.

            Handles:
            - Plain JSON arrays
            - Markdown code blocks with ```json or ```
            - JSON embedded in explanatory text
            - Malformed markdown fences
            """
            if not text:
                raise json.JSONDecodeError("empty", text, 0)
            s = text.strip()

            # Strategy 1: Try extracting from markdown code blocks
            if "```" in s:
                # Handle multiple code blocks by trying each one
                parts = s.split("```")
                for i in range(1, len(parts), 2):  # Odd indices are content between fences
                    block = parts[i].strip()
                    # Remove language identifier if present
                    if block.startswith("json"):
                        block = block[4:].strip()
                    elif block.startswith("javascript"):
                        block = block[10:].strip()
                    # Try to parse this block
                    try:
                        data = json.loads(block)
                        if isinstance(data, list):
                            return [item for item in data if isinstance(item, dict)]
                        if isinstance(data, dict):
                            # Single hypothesis wrapped in object, convert to list
                            return [data]
                    except (json.JSONDecodeError, ValueError):
                        # Try finding JSON array in this block
                        start = block.find("[")
                        end = block.rfind("]")
                        if start != -1 and end != -1 and end > start:
                            try:
                                data = json.loads(block[start : end + 1])
                                if isinstance(data, list):
                                    return [item for item in data if isinstance(item, dict)]
                            except (json.JSONDecodeError, ValueError):
                                continue

            # Strategy 2: Find JSON array boundaries in the entire text
            start = s.find("[")
            end = s.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(s[start : end + 1])
                    if isinstance(data, list):
                        out: list[dict[str, Any]] = []
                        for item in data:
                            if isinstance(item, dict):
                                out.append(item)
                        if out:  # Only return if we found valid dict items
                            return out
                except (json.JSONDecodeError, ValueError):
                    pass

            # Strategy 3: Try parsing the entire text as-is
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
                if isinstance(data, dict):
                    return [data]
            except (json.JSONDecodeError, ValueError):
                pass

            # All strategies failed
            raise json.JSONDecodeError(
                "Could not extract valid JSON array from response",
                text,
                0
            )

        parsed: list[dict[str, Any]] = []

        allowed_vuln_types = set(
            self.HYPOTHESIS_SCHEMA["items"]["properties"]["vuln_type"]["enum"]
        )

        def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
            """Coerce common LLM variations into the expected schema."""
            out = dict(item)
            # Map alternate keys
            if "vuln_type" not in out and "vulnerability" in out:
                out["vuln_type"] = str(out.get("vulnerability") or "").strip().lower()
            if "function_signature" not in out and "function" in out:
                out["function_signature"] = out.get("function")
            # Default confidence if missing
            if "confidence" not in out or out.get("confidence") is None:
                out["confidence"] = 0.5
            # Normalize vuln_type to allowed set
            vt = str(out.get("vuln_type") or "").strip().lower()
            if not vt:
                vt = "generic_contract"
            # Common alias mapping
            aliases = {
                "owner_privilege_escalation": "access_control",
                "privilege_escalation": "access_control",
                "admin_takeover": "access_control",
                "governance_hijack": "flash_loan_governance_attack",
                "price_oracle": "oracle_manipulation",
            }
            vt = aliases.get(vt, vt)
            if vt not in allowed_vuln_types:
                vt = "generic_contract"
            out["vuln_type"] = vt
            return out

        for attempt in range(max_retries):
            try:
                raw = _extract_json_array(response)
                normalized = [_normalize_item(i) for i in raw]
                validate(instance=normalized, schema=self.HYPOTHESIS_SCHEMA)
                parsed = normalized
                self._log(
                    "hypothesis_validation_success",
                    contract=contract_name,
                    count=len(parsed),
                    attempt=attempt + 1,
                )
                break
            except json.JSONDecodeError as e:
                self._log(
                    "hypothesis_json_parse_error",
                    contract=contract_name,
                    error=str(e),
                    response_preview=response[:500],
                )
                if attempt < max_retries - 1:
                    response = await self._call_worker(
                        f"""Your JSON response was malformed. Error: {e!s}

Original response (first 300 chars):
{response[:300]}

Return ONLY a JSON array with objects containing:
- vuln_type (string: reentrancy, access_control, oracle_manipulation, flash_loan, mev_sandwich, precision_error, state_inconsistency, generic_contract)
- confidence (0-1)
- contract_address (0x + 40 hex)
- chain_id (int)
- function_signature (use one from: {functions_preview})
"""
                    )
                continue
            except ValidationError as e:
                self._log(
                    "hypothesis_schema_validation_error",
                    contract=contract_name,
                    error=str(e),
                    failed_item=str(e.instance)[:200],
                )
                if attempt < max_retries - 1:
                    response = await self._call_worker(
                        f"""Your hypotheses failed validation: {e.message}

Failed item:
{json.dumps(e.instance, indent=2)[:200]}

Fix and return ONLY a JSON array matching the schema and using function signatures from: {functions_preview}
"""
                    )
                continue
            except Exception as e:
                self._log("hypothesis_parse_error", contract=contract_name, error=str(e))
                if attempt == max_retries - 1:
                    parsed = []
                continue

        return parsed

    def _checksum_address(self, address: str | None) -> str:
        """Validate and return checksummed Ethereum address."""
        if not address:
            raise ValueError("cannot be None or empty")
        if not isinstance(address, str):
            raise TypeError(f"Address must be string, got {type(address).__name__}")

        addr = address.strip()
        if not addr.startswith("0x"):
            raise ValueError("start with '0x'")

        try:
            int(addr, 16)
        except ValueError as exc:
            raise ValueError("invalid hex") from exc

        if len(addr) != 42:
            raise ValueError("42 characters")

        if not is_address(addr):
            raise ValueError(f"Invalid Ethereum address format: {address}")

        return to_checksum_address(addr)

    def _normalize_address(self, address: str | None) -> str | None:
        """Attempt to normalize an address, returning None if invalid."""
        if not address or not isinstance(address, str):
            return None

        try:
            addr = address.strip()
            if not addr.startswith("0x"):
                addr = "0x" + addr

            if len(addr) < 42:
                addr = addr + "0" * (42 - len(addr))
            if len(addr) > 42:
                addr = addr[:42]

            if is_address(addr):
                # Return uppercase hex with lowercase 0x prefix for test expectations
                return "0x" + to_checksum_address(addr)[2:].upper()
        except Exception as exc:
            logger.debug("Failed to normalize address '%s': %s", address, exc)

        return None

    def _validate_and_normalize_address(
        self,
        address: str | None,
        *,
        context: str = "hypothesis",
    ) -> str | None:
        """Validate address with logging, return None if invalid."""
        try:
            return self._checksum_address(address)
        except ValueError as e:
            self._log_error(
                f"invalid_address_in_{context}",
                address=address,
                error=str(e),
            )
            return None

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
        """
        Zero-cost heuristic hypotheses to reduce LLM dependence.
        Covers top missing classes from review:
        - Reentrancy (single + cross-function)
        - Access control
        - Oracle manipulation
        - Storage collision (upgradeable proxies)
        - Signature replay (permit/ecrecover)
        - First depositor inflation (ERC4626-style)
        - Unchecked arithmetic (Solc 0.8+ unchecked blocks)
        - Precision/rounding errors (share protocols)
        - MEV/Sandwich for AMM-like flows
        """
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

        # Signature replay (permit/ecrecover)
        sig_keywords = ["ecrecover", "permit", "signature", "sig"]
        if any(any(k in f for k in sig_keywords) for f in funcs_lower):
            add("signature_replay", "Signature recovery detected; nonce/deadline unknown", 0.6)

        # First depositor inflation for vault-like contracts (ERC4626 semantics)
        vault_keywords = ["deposit", "withdraw", "mint", "redeem", "totalassets", "totalsupply", "totalshares"]
        if any(any(k in f for k in vault_keywords) for f in funcs_lower):
            add("first_depositor_inflation", "Share-based vault semantics detected", 0.7)

        # Reentrancy hooks (external calls)
        external_callers = ["call(", "delegatecall(", "staticcall("]
        if any(c in "".join(funcs_lower) for c in external_callers):
            add("reentrancy", "External call present; check ordering", 0.65)

        # Cross-function reentrancy (withdraw + deposit/mint)
        withdraw_funcs = [f for f in funcs_lower if any(k in f for k in ["withdraw", "redeem", "claim"])]
        deposit_funcs = [f for f in funcs_lower if any(k in f for k in ["deposit", "mint", "stake"])]
        if withdraw_funcs and deposit_funcs:
            add(
                "cross_function_reentrancy",
                f"Withdraw {withdraw_funcs[0]} paired with deposit/mint {deposit_funcs[0]}",
                0.7,
            )

        # Access control gaps
        admin_keywords = ["owner", "admin", "governor", "upgrade", "pause", "set"]
        protected = any("only" in f or "auth" in f for f in funcs_lower)
        if any(any(k in f for k in admin_keywords) for f in funcs_lower) and not protected:
            add("access_control", "Admin-like functions without protection hints", 0.55)

        # Oracle hint from metadata
        if metadata.get("oracle_dependency"):
            add("oracle_manipulation", "Oracle dependency flagged in metadata", 0.75)

        # Precision / rounding errors in share-based protocols
        precision_keywords = ["share", "rebalance", "round", "ceil", "floor"]
        if any(any(k in f for k in precision_keywords) for f in funcs_lower):
            add("precision_error", "Share/rounding semantics detected", 0.65)

        # MEV/Sandwich heuristic for AMM-like functions
        amm_keywords = ["swap", "router", "pair", "pool", "reserve"]
        price_keywords = ["price", "twap"]
        if any(any(k in f for k in amm_keywords) for f in funcs_lower) and any(any(k in f for k in price_keywords) for f in funcs_lower):
            add("mev_sandwich", "AMM-like swap + price functions detected", 0.65)

        # Unchecked arithmetic hint (Solc 0.8+ unchecked blocks) - rely on metadata.solc if present
        solc_version = metadata.get("solc")
        math_keywords = ["mul", "div", "add", "sub", "calc", "compute"]
        if solc_version and solc_version.startswith("0.8") and any(any(k in f for k in math_keywords) for f in funcs_lower):
            add("unchecked_arithmetic", f"Solc {solc_version} math functions could use unchecked{{}}", 0.55)

        # Advanced patterns (2023-2024)

        # Read-only reentrancy detection
        view_funcs = [f for f in funcs_lower if "view" in f or "get" in f or "balanceof" in f or "totalsupply" in f]
        if view_funcs and any(c in "".join(funcs_lower) for c in external_callers):
            add("read_only_reentrancy", "View functions with external calls detected (read-only reentrancy risk)", 0.75)

        # CEI pattern violation detection
        state_update_keywords = ["balance", "state", "storage", "mapping"]
        if any(c in "".join(funcs_lower) for c in external_callers) and any(any(k in f for k in state_update_keywords) for f in funcs_lower):
            add("cei_violation", "External calls with state updates (potential CEI violation)", 0.7)

        # Flash loan attack patterns
        flash_keywords = ["flashloan", "borrow", "repay", "flashswap"]
        if any(any(k in f for k in flash_keywords) for f in funcs_lower):
            add("flash_loan_price_manipulation", "Flash loan functions detected", 0.8)
            add("same_block_borrow_repay", "Same-block borrow/repay pattern possible", 0.7)

        # Oracle manipulation via flash loans
        oracle_flash_keywords = ["price", "oracle", "twap", "reserve"]
        if any(any(k in f for k in flash_keywords) for f in funcs_lower) and any(any(k in f for k in oracle_flash_keywords) for f in funcs_lower):
            add("oracle_manipulation_flash", "Flash loan + oracle manipulation risk", 0.85)

        # Advanced access control patterns
        role_keywords = ["role", "permission", "grant", "revoke"]
        if any(any(k in f for k in admin_keywords) for f in funcs_lower) and not any(any(k in f for k in role_keywords) for f in funcs_lower):
            add("role_based_access_needed", "Admin functions without role-based access control", 0.65)

        # Front-running vulnerabilities
        frontrun_keywords = ["bid", "auction", "vote", "random", "lottery", "commit", "reveal"]
        if any(any(k in f for k in frontrun_keywords) for f in funcs_lower) and not any("commit" in f and "reveal" in f for f in funcs_lower):
            add("missing_commit_reveal", "Front-running vulnerable functions without commit-reveal", 0.6)

        # EIP-712 signature protection
        if any(any(k in f for k in sig_keywords) for f in funcs_lower) and not any("eip712" in f or "typehash" in f for f in funcs_lower):
            add("missing_eip712_signature", "Signatures without EIP-712 protection", 0.55)

        # Oracle security patterns
        oracle_keywords = ["oracle", "price", "feed", "chainlink", "aggregator"]
        if any(any(k in f for k in oracle_keywords) for f in funcs_lower):
            # Staleness check
            if not any("timestamp" in f or "updatedat" in f or "roundid" in f for f in funcs_lower):
                add("stale_price_data", "Oracle price feed without staleness checks", 0.75)

            # Single oracle dependency
            if not any("twap" in f or "median" in f or "consensus" in f for f in funcs_lower):
                add("single_oracle_dependency", "Single oracle dependency without redundancy", 0.65)

            # Missing TWAP
            spot_price_keywords = ["spot", "instant", "current"]
            if any(any(k in f for k in spot_price_keywords) for f in funcs_lower) and not any("twap" in f for f in funcs_lower):
                add("missing_twap", "Spot price usage without TWAP protection", 0.7)

            # Price deviation check
            if not any("deviation" in f or "threshold" in f or "limit" in f for f in funcs_lower):
                add("no_price_deviation_check", "Oracle without price deviation checks", 0.6)

        return hypotheses

    def _validate_hypothesis(self, hyp: dict[str, Any]) -> bool:
        """Validate hypothesis has required fields and valid data."""
        required_fields = ["vuln_type", "confidence", "contract_address", "function_signature"]
        for required_field in required_fields:
            if required_field not in hyp or not hyp[required_field]:
                logger.debug("Hypothesis missing required field '%s'", required_field)
                return False

        try:
            self._checksum_address(hyp["contract_address"])
        except ValueError as e:
            logger.debug("Hypothesis has invalid contract address: %s", e)
            return False

        try:
            conf = float(hyp["confidence"])
            if not 0.0 <= conf <= 1.0:
                logger.debug("Hypothesis confidence out of range: %s", conf)
                return False
        except (TypeError, ValueError) as e:
            logger.debug("Hypothesis has invalid confidence: %s", e)
            return False

        func_sig = hyp["function_signature"]
        if not isinstance(func_sig, str) or not re.match(r"^[a-zA-Z_]\w*\([^)]*\)$", func_sig):
            logger.debug("Hypothesis has invalid function signature: %s", func_sig)
            return False

        valid_vuln_types = {
            "reentrancy",
            "access_control",
            "integer_overflow",
            "unchecked_call",
            "delegatecall_confusion",
            "oracle_manipulation",
            "flash_loan",
            "mev_sandwich",
            "precision_error",
            "state_inconsistency",
            "generic_contract",
            "storage_collision",
            "signature_replay",
            "first_depositor_inflation",
            "cross_function_reentrancy",
            "unchecked_arithmetic",
            "read_only_reentrancy",
            "cei_violation",
            "flash_loan_price_manipulation",
            "flash_loan_governance_attack",
            "same_block_borrow_repay",
            "oracle_manipulation_flash",
            "missing_access_control",
            "weak_access_control",
            "role_based_access_needed",
            "front_running_vulnerable",
            "missing_commit_reveal",
            "no_timelock",
            "missing_eip712_signature",
            "stale_price_data",
            "single_oracle_dependency",
            "missing_twap",
            "no_price_deviation_check",
        }
        if hyp["vuln_type"] not in valid_vuln_types:
            logger.debug("Hypothesis has invalid vuln_type: %s", hyp["vuln_type"])
            return False

        return True

    def _feasibility_gate(self, hyp: dict[str, Any], abi: list[Any], functions: list[str] | None = None) -> bool:
        """
        Eliminate impossible hypotheses before downstream execution.
        Checks:
        - Function exists in ABI
        - Non-view/pure for exploitation
        - Payable alignment if hinted
        - Basic oracle dependency for oracle_manipulation
        """
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
            if h.get("vuln_type") == "mev_sandwich":
                mev_hypothesis = {
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "asset_id": h.get("asset_id"),
                    "target": h.get("target"),
                    "vuln_type": "mev_sandwich",
                    "confidence": h.get("confidence", 0.5),
                    "rationale": h.get("rationale", ""),
                    "test_approach": h.get("test_approach", ""),
                    "contract_address": h.get("contract_address"),
                    "chain_id": h.get("chain_id"),
                    "function_signature": h.get("function_signature"),
                    "foundry_profile": foundry_profile,
                    "solc": solc,
                    "abi": abi,
                    "profit_tokens": scope_profit_tokens,
                    "exploit_notes": h.get("exploit_notes", []),
                    "expected_profit_hint_eth": h.get("expected_profit_hint_eth"),
                    "status": "pending",
                }
                enriched.append(mev_hypothesis)
            elif h.get("vuln_type") == "precision_error":
                precision_hypothesis = {
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "asset_id": h.get("asset_id"),
                    "target": h.get("target"),
                    "vuln_type": "precision_error",
                    "confidence": h.get("confidence", 0.5),
                    "rationale": h.get("rationale", ""),
                    "test_approach": h.get("test_approach", ""),
                    "contract_address": h.get("contract_address"),
                    "chain_id": h.get("chain_id"),
                    "function_signature": h.get("function_signature"),
                    "foundry_profile": foundry_profile,
                    "solc": solc,
                    "abi": abi,
                    "profit_tokens": scope_profit_tokens,
                    "exploit_notes": h.get("exploit_notes", []),
                    "expected_profit_hint_eth": h.get("expected_profit_hint_eth"),
                    "status": "pending",
                }
                enriched.append(precision_hypothesis)
        return enriched

    async def _generate_hypotheses_for_asset(
        self,
        asset: dict[str, Any],
        technologies: list[str],
    ) -> list[dict[str, Any]]:
        """Generate vulnerability hypotheses for a single asset."""
        url = asset.get("value", "")
        metadata = asset.get("metadata", {})
        tech_list = metadata.get("technologies", []) + technologies

        prompt = f"""Analyze this web asset and generate vulnerability hypotheses.

URL: {url}
Status Code: {metadata.get('status_code')}
Title: {metadata.get('title')}
Technologies: {tech_list[:10]}
Webserver: {metadata.get('webserver')}

For each potential vulnerability, provide:
1. Vulnerability type (e.g., XSS, SQLi, IDOR, SSRF)
2. Confidence level (0.0 to 1.0)
3. Rationale for why this might exist
4. Initial test approach
5. Optional on-chain fields if applicable:
   - contract_address (hex)
   - chain_id (int)
   - function_signature (e.g., transfer(address,uint256))
   - exploit_notes (short array of bullet points)
   - expected_profit_hint_eth (float)

Output as JSON array:
[
  {{
    "vuln_type": "...",
    "confidence": 0.7,
    "rationale": "...",
    "test_approach": "...",
    "contract_address": "0x...",
    "chain_id": 1,
    "function_signature": "withdraw(uint256)",
    "exploit_notes": ["...","..."],
    "expected_profit_hint_eth": 1.2
  }}
]

Focus on realistic, high-value vulnerabilities. Limit to 5 hypotheses."""

        response = await self._call_worker(prompt)

        try:
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                raw_hypotheses = json.loads(json_str.strip())
            else:
                raw_hypotheses = json.loads(response)

            hypotheses = []
            for h in raw_hypotheses:
                hypotheses.append({
                    "id": f"hyp-{uuid.uuid4().hex[:8]}",
                    "asset_id": asset.get("id"),
                    "target": url,
                    "vuln_type": h.get("vuln_type", "unknown"),
                    "confidence": min(max(float(h.get("confidence", 0.5)), 0.0), 1.0),
                    "rationale": h.get("rationale", ""),
                    "test_approach": h.get("test_approach", ""),
                    "contract_address": h.get("contract_address"),
                    "chain_id": h.get("chain_id"),
                    "function_signature": h.get("function_signature"),
                    "exploit_notes": h.get("exploit_notes", []),
                    "expected_profit_hint_eth": h.get("expected_profit_hint_eth"),
                    "status": "pending",
                })

            return hypotheses

        except (json.JSONDecodeError, ValueError):
            # Return a generic hypothesis on parse failure
            return [{
                "id": f"hyp-{uuid.uuid4().hex[:8]}",
                "asset_id": asset.get("id"),
                "target": url,
                "vuln_type": "generic",
                "confidence": 0.3,
                "rationale": "Generic testing hypothesis",
                "test_approach": "Standard vulnerability scanning",
                "status": "pending",
            }]

    async def _research_validate_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Use research to validate and enhance hypotheses."""
        # Group hypotheses by vuln type
        by_type: dict[str, list[dict[str, Any]]] = {}
        for h in hypotheses:
            vtype = h.get("vuln_type", "unknown")
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(h)

        # Research each vulnerability type
        for vtype, hyps in list(by_type.items())[:3]:  # Limit to 3 types
            research = await self._research(
                question=f"What are effective testing techniques for {vtype} vulnerabilities in web applications?",
                context=f"Validating {len(hyps)} hypotheses for {vtype}",
            )

            # Enhance hypotheses with research
            for h in hyps:
                h["research_context"] = research.get("answer", "")[:200]

        return hypotheses

    async def _advisor_review_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Get advisor review of top hypotheses."""
        if not self.advisor_model or not hypotheses:
            return {"reviewed": False}

        prompt = f"""Review these vulnerability hypotheses for a bug bounty program.

Hypotheses:
{json.dumps(hypotheses[:10], indent=2)}

Evaluate:
1. Which hypotheses are most likely to yield real vulnerabilities?
2. Which should be deprioritized or skipped?
3. Are there any safety concerns with testing these?

Respond with JSON:
{{
  "priority_hypotheses": ["hyp-id-1", "hyp-id-2"],
  "skip_hypotheses": ["hyp-id-3"],
  "safety_concerns": ["..."],
  "recommendations": ["..."]
}}"""

        response = await self._call_advisor(prompt)

        try:
            if "```" in response:
                json_str = response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
            return json.loads(response)
        except json.JSONDecodeError:
            return {"reviewed": True, "error": "Failed to parse advisor response"}

    def _group_by_type(
        self,
        hypotheses: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Group hypotheses by vulnerability type."""
        counts: dict[str, int] = {}
        for h in hypotheses:
            vtype = h.get("vuln_type", "unknown")
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts

    def _generate_fallback_hypotheses(
        self,
        contract_assets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate generic fallback hypotheses when no hypotheses were generated.

        This ensures the workflow can continue even when LLM/research calls fail,
        by creating basic hypotheses from contract metadata.
        """
        fallback_hypotheses: list[dict[str, Any]] = []

        for asset in contract_assets:
            metadata = asset.get("metadata", {}) or {}
            address = metadata.get("address") or asset.get("value", "")
            name = metadata.get("name") or asset.get("name", "Unknown")
            chain_id = metadata.get("chain_id", 1)
            functions = metadata.get("functions", [])
            classification = metadata.get("classification", {})
            protocol_type = classification.get("protocol_type", "generic")

            # Get appropriate vulnerability patterns based on protocol type
            profile = ProtocolProfile.from_type(protocol_type)

            # Create a few generic hypotheses per contract
            for pattern in profile.patterns[:2]:  # Top 2 patterns for this protocol type
                hypothesis = {
                    "id": str(uuid.uuid4()),
                    "vuln_type": pattern,
                    "confidence": 0.45,  # Just above threshold but clearly a fallback
                    "contract_address": address,
                    "chain_id": chain_id,
                    "function_signature": functions[0] if functions else None,
                    "rationale": f"Fallback hypothesis for {protocol_type} contract. "
                                f"Pattern: {pattern}. Manual review recommended.",
                    "attack_description": f"Generic {pattern} attack vector based on protocol type",
                    "expected_profit_hint_eth": 0.0,
                    "exploit_notes": [
                        "Generated as fallback - LLM hypothesis generation failed or returned no results",
                        f"Contract: {name}",
                        f"Protocol type: {protocol_type}",
                        "Requires manual verification"
                    ],
                    "status": "pending",
                    "is_fallback": True,
                }
                fallback_hypotheses.append(hypothesis)

        self._log(
            "fallback_hypotheses_generated",
            count=len(fallback_hypotheses),
            contracts=len(contract_assets),
        )

        return fallback_hypotheses

    def _rank_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Rank hypotheses by exploitability and profit signal.

        Uses log-scaled profit to avoid capping mega-exploits. The formula:
        - confidence (50%): Weight for LLM-generated confidence
        - severity (30%): Weight based on vulnerability type
        - profit (20%): Log-scaled to handle wide range of profits
        - missing_penalty: Deduction for incomplete hypotheses
        """
        def score(h: dict[str, Any]) -> float:
            confidence = float(h.get("confidence", 0))
            est_profit = float(h.get("expected_profit_hint_eth", 0) or 0)

            # Severity weights for different vulnerability types
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

            # Find best matching severity weight
            sev_bonus = max(
                (weight for key, weight in severity_weight.items() if key in vt),
                default=0.4
            )

            # Log-scale profit to avoid capping mega-exploits
            # Normalized to 0-1 range for 0-100 ETH
            profit_score = math.log1p(est_profit) / math.log1p(100) if est_profit > 0 else 0.0
            profit_score = min(profit_score, 1.0)  # Cap at 1.0 for very large profits

            # Penalty for missing required fields
            missing_penalty = 0.2 if (not h.get("contract_address") or not h.get("function_signature")) else 0.0

            return (
                confidence * 0.5 +  # Reduced from 0.6 - LLM confidence may be uncalibrated
                sev_bonus * 0.3 +   # Increased from 0.2 - severity weights are defined
                profit_score * 0.2  # Log-scaled profit
                - missing_penalty
            )

        ranked = sorted(hypotheses, key=score, reverse=True)
        for idx, h in enumerate(ranked):
            h["exploit_score"] = round(score(h), 4)
            h["rank"] = idx + 1
        return ranked
