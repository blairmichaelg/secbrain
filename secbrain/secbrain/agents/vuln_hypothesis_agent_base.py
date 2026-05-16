"""Base components for vulnerability hypothesis agent."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, ClassVar

from secbrain.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# ABI preview limits for prompt generation
ABI_PREVIEW_MAX_ENTRIES = 30
ABI_PREVIEW_REDUCED_ENTRIES = 15
ABI_JSON_SIZE_LIMIT = 1500
FUNCTIONS_PREVIEW_LIMIT = 15

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

class BaseVulnHypothesisAgent(BaseAgent):
    """Abstract base class for vulnerability hypothesis agent."""
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
