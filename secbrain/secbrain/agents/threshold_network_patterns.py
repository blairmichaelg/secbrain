"""Threshold Network and Immunefi-specific vulnerability patterns.

This module implements vulnerability patterns specifically tailored for:
1. Threshold Network (tBTC bridge, threshold cryptography, cross-chain security)
2. Immunefi bug bounty programs (severity classification, common attack vectors)

Based on research from:
- Immunefi bug bounty database (https://immunefi.com)
- Threshold Network documentation (https://docs.threshold.network/)
- tBTC v2 security considerations
- Cross-chain bridge exploits (2022-2024)
- Threshold cryptography vulnerabilities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar


class ThresholdVulnerabilityPattern(Enum):
    """Threshold Network specific vulnerability patterns."""

    # tBTC Bridge vulnerabilities
    BITCOIN_PEG_MANIPULATION = "bitcoin_peg_manipulation"
    WALLET_REGISTRY_COMPROMISE = "wallet_registry_compromise"
    BRIDGE_FUNDS_THEFT = "bridge_funds_theft"
    DEPOSIT_SWEEP_MANIPULATION = "deposit_sweep_manipulation"
    REDEMPTION_PROOF_FORGERY = "redemption_proof_forgery"
    GUARDIAN_KEY_COMPROMISE = "guardian_key_compromise"
    OPTIMISTIC_MINTING_EXPLOIT = "optimistic_minting_exploit"

    # Threshold cryptography vulnerabilities
    THRESHOLD_SIGNATURE_MANIPULATION = "threshold_signature_manipulation"
    DKG_PROTOCOL_ATTACK = "dkg_protocol_attack"  # Distributed Key Generation
    DKG_THRESHOLD_RAISING = "dkg_threshold_raising"  # Polynomial degree validation bypass
    OPERATOR_COLLUSION = "operator_collusion"
    SIGNING_GROUP_CORRUPTION = "signing_group_corruption"
    RANDOM_BEACON_MANIPULATION = "random_beacon_manipulation"

    # Cross-chain bridge vulnerabilities
    CROSS_CHAIN_MESSAGE_FORGERY = "cross_chain_message_forgery"
    WORMHOLE_BRIDGE_EXPLOIT = "wormhole_bridge_exploit"
    STARKNET_BRIDGE_ATTACK = "starknet_bridge_attack"
    RELAY_MESSAGE_MANIPULATION = "relay_message_manipulation"
    CROSS_CHAIN_REENTRANCY = "cross_chain_reentrancy"

    # Staking and governance vulnerabilities
    STAKING_REWARD_MANIPULATION = "staking_reward_manipulation"
    DELEGATION_ATTACK = "delegation_attack"
    GOVERNANCE_VOTE_BUYING = "governance_vote_buying"
    TIMELOCK_BYPASS = "timelock_bypass"
    PROXY_UPGRADE_EXPLOIT = "proxy_upgrade_exploit"

    # Token merger vulnerabilities (KEEP + NU -> T)
    TOKEN_RATIO_MANIPULATION = "token_ratio_manipulation"
    VENDING_MACHINE_EXPLOIT = "vending_machine_exploit"
    LEGACY_TOKEN_DOUBLE_SPEND = "legacy_token_double_spend"

    # New 2024-2025 patterns
    ZK_PROOF_VERIFICATION_FLAW = "zk_proof_verification_flaw"
    OPTIMISTIC_CHALLENGE_BYPASS = "optimistic_challenge_bypass"
    MEV_EXTRACTION_VULNERABILITY = "mev_extraction_vulnerability"
    WITHDRAWAL_QUEUE_MANIPULATION = "withdrawal_queue_manipulation"
    SLASHING_MECHANISM_BYPASS = "slashing_mechanism_bypass"


class ImmunefiSeverity(Enum):
    """Immunefi vulnerability severity classification."""

    CRITICAL = "critical"  # Direct theft, permanent freezing, protocol insolvency
    HIGH = "high"  # Theft/freezing of unclaimed yield, temporary freezing (1+ hours)
    MEDIUM = "medium"  # Contract inoperability, griefing, gas theft
    LOW = "low"  # Minor issues based on Immunefi classification


@dataclass
class ThresholdSecurityPattern:
    """Threshold Network specific security pattern."""

    pattern_type: ThresholdVulnerabilityPattern
    severity: ImmunefiSeverity
    description: str
    immunefi_category: str  # Maps to Immunefi scope categories
    max_bounty_usd: int  # Maximum bounty for this vulnerability type
    detection_heuristics: list[str] = field(default_factory=list)
    exploitation_steps: list[str] = field(default_factory=list)
    mitigation_strategies: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    affected_contracts: list[str] = field(default_factory=list)


import yaml
from pathlib import Path

def _load_threshold_yaml() -> dict:
    yaml_path = Path(__file__).parent.parent / "patterns" / "threshold_patterns.yaml"
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)

def _parse_threshold_patterns(data: dict) -> dict[str, ThresholdSecurityPattern]:
    res = {}
    if not data:
        return res
    for k, v in data.items():
        res[k] = ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern(v["pattern_type"]),
            severity=ImmunefiSeverity(v["severity"]),
            description=v["description"],
            immunefi_category=v["immunefi_category"],
            max_bounty_usd=v["max_bounty_usd"],
            detection_heuristics=v.get("detection_heuristics", []),
            exploitation_steps=v.get("exploitation_steps", []),
            mitigation_strategies=v.get("mitigation_strategies", []),
            references=v.get("references", []),
            affected_contracts=v.get("affected_contracts", []),
        )
    return res

_threshold_data = _load_threshold_yaml()

class ThresholdNetworkPatterns:
    """Comprehensive Threshold Network vulnerability patterns database."""

    TBTC_BRIDGE_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = _parse_threshold_patterns(_threshold_data.get("TBTC_BRIDGE_PATTERNS", {}))
    THRESHOLD_CRYPTO_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = _parse_threshold_patterns(_threshold_data.get("THRESHOLD_CRYPTO_PATTERNS", {}))
    CROSS_CHAIN_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = _parse_threshold_patterns(_threshold_data.get("CROSS_CHAIN_PATTERNS", {}))
    STAKING_GOVERNANCE_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = _parse_threshold_patterns(_threshold_data.get("STAKING_GOVERNANCE_PATTERNS", {}))
    TOKEN_MERGER_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = _parse_threshold_patterns(_threshold_data.get("TOKEN_MERGER_PATTERNS", {}))
    ADVANCED_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = _parse_threshold_patterns(_threshold_data.get("ADVANCED_PATTERNS", {}))


    @classmethod
    def get_all_patterns(cls) -> dict[str, ThresholdSecurityPattern]:
        """Get all Threshold Network vulnerability patterns."""
        all_patterns = {}
        all_patterns.update(cls.TBTC_BRIDGE_PATTERNS)
        all_patterns.update(cls.THRESHOLD_CRYPTO_PATTERNS)
        all_patterns.update(cls.CROSS_CHAIN_PATTERNS)
        all_patterns.update(cls.STAKING_GOVERNANCE_PATTERNS)
        all_patterns.update(cls.TOKEN_MERGER_PATTERNS)
        all_patterns.update(cls.ADVANCED_PATTERNS)
        return all_patterns

    @classmethod
    def get_critical_patterns(cls) -> list[ThresholdSecurityPattern]:
        """Get only critical severity patterns."""
        all_patterns = cls.get_all_patterns()
        return [
            pattern
            for pattern in all_patterns.values()
            if pattern.severity == ImmunefiSeverity.CRITICAL
        ]

    @classmethod
    def get_patterns_for_contract(cls, contract_name: str) -> list[ThresholdSecurityPattern]:
        """Get vulnerability patterns relevant to a specific contract."""
        all_patterns = cls.get_all_patterns()
        return [
            pattern
            for pattern in all_patterns.values()
            if contract_name in pattern.affected_contracts
            or any(contract_name.lower() in c.lower() for c in pattern.affected_contracts)
        ]

    @classmethod
    def get_immunefi_severity_guidance(cls) -> dict[str, Any]:
        """Get Immunefi-specific severity classification guidance."""
        return {
            "critical": {
                "max_bounty": 1_000_000,
                "categories": [
                    "Direct theft of any user funds, whether at-rest or in-motion",
                    "Permanent freezing of funds",
                    "Protocol insolvency",
                ],
                "examples": [
                    "Bridge fund theft via SPV proof forgery",
                    "Wallet registry compromise leading to Bitcoin theft",
                    "Threshold signature bypass",
                    "Cross-chain message forgery",
                    "Proxy upgrade to malicious implementation",
                ],
            },
            "high": {
                "max_bounty": 50_000,
                "categories": [
                    "Theft of unclaimed yield",
                    "Permanent freezing of unclaimed yield",
                    "Temporary freezing of funds for at least 1 hour",
                ],
                "examples": [
                    "Staking reward manipulation",
                    "Governance vote buying via flash loans",
                    "Operator collusion below threshold",
                    "Vending machine conversion exploit",
                ],
            },
            "medium": {
                "max_bounty": 10_000,
                "categories": [
                    "Smart contract unable to operate due to lack of token funds",
                    "Block stuffing",
                    "Griefing (no profit motive for attacker)",
                    "Theft of gas",
                    "Unbounded gas consumption",
                ],
                "examples": [
                    "DoS via unbounded loops",
                    "Gas griefing attacks",
                    "Block stuffing to prevent operations",
                ],
            },
            "low": {
                "max_bounty": 1_000,
                "categories": [
                    "Contract fails to deliver promised functionality",
                    "State handling issues",
                ],
                "examples": [
                    "Minor logic errors",
                    "Informational findings",
                ],
            },
        }
