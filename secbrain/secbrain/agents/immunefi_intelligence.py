"""Immunefi intelligence gathering for bug bounty optimization.

This module provides intelligence from Immunefi bug bounty programs to enhance
vulnerability detection and prioritization. It includes:
- Common vulnerability patterns from Immunefi submissions
- Severity classification guidance
- Bounty ranges and prioritization
- Protocol-specific attack vectors
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImmunefiVulnerabilityClass:
    """Represents a class of vulnerabilities in Immunefi programs."""

    name: str
    severity: str  # critical, high, medium, low
    typical_bounty_range: tuple[int, int]  # (min, max) in USD
    description: str
    common_patterns: list[str] = field(default_factory=list)
    detection_techniques: list[str] = field(default_factory=list)
    recent_examples: list[str] = field(default_factory=list)


class ImmunefiIntelligence:
    """Intelligence database for Immunefi bug bounty programs."""

    # Based on Immunefi Vulnerability Severity Classification System V2.3
    SEVERITY_CLASSIFICATION = {
        "critical": {
            "smart_contract": [
                "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield",
                "Permanent freezing of funds",
                "Protocol insolvency",
            ],
            "typical_bounty": (100_000, 1_000_000),
            "calculation": "10% of funds at risk, capped at program maximum",
        },
        "high": {
            "smart_contract": [
                "Theft of unclaimed yield",
                "Permanent freezing of unclaimed yield",
                "Temporary freezing of funds for at least 1 hour",
            ],
            "typical_bounty": (10_000, 50_000),
        },
        "medium": {
            "smart_contract": [
                "Smart contract unable to operate due to lack of token funds",
                "Block stuffing",
                "Griefing (e.g. no profit motive for an attacker, but damage to the users or the protocol)",
                "Theft of gas",
                "Unbounded gas consumption",
            ],
            "typical_bounty": (1_000, 10_000),
        },
        "low": {
            "smart_contract": [
                "Contract fails to deliver promised functionality",
                "State handling issues",
            ],
            "typical_bounty": (100, 1_000),
        },
    }

    # Common vulnerability patterns from Immunefi programs (2022-2025)
    COMMON_VULNERABILITIES = {
        "bridge_exploits": ImmunefiVulnerabilityClass(
            name="Cross-chain Bridge Exploits",
            severity="critical",
            typical_bounty_range=(500_000, 10_000_000),
            description="Exploits in cross-chain bridges allowing theft or manipulation of bridged assets",
            common_patterns=[
                "Message verification bypass",
                "Proof forgery (SPV, Merkle proofs)",
                "Signature validation flaws",
                "Relay manipulation",
                "Cross-chain reentrancy",
                "Deposit/withdrawal mismatch",
                "Intent-based bridge exploits (2024+)",
                "ZK proof verification flaws",
                "Optimistic bridge challenge bypass",
            ],
            detection_techniques=[
                "Analyze proof verification logic",
                "Test signature validation edge cases",
                "Check for replay protection",
                "Verify cross-chain message authentication",
                "Test relay censorship resistance",
                "Test ZK proof verification circuits",
                "Validate optimistic challenge periods",
                "Test intent settlement atomicity",
            ],
            recent_examples=[
                "Wormhole ($320M, 2022) - Signature verification bypass",
                "Ronin Bridge ($625M, 2022) - Compromised validator keys",
                "Nomad Bridge ($190M, 2022) - Merkle root verification flaw",
                "BNB Bridge ($586M, 2022) - Proof verification exploit",
                "Multichain ($126M, 2023) - Key compromise",
                "Socket ($3.3M, 2024) - Incomplete input validation",
                "LI.FI ($10M, 2024) - Arbitrary external call vulnerability",
            ],
        ),
        "flash_loan_attacks": ImmunefiVulnerabilityClass(
            name="Flash Loan Attacks",
            severity="critical",
            typical_bounty_range=(50_000, 500_000),
            description="Exploitation using flash loans for price manipulation or governance attacks",
            common_patterns=[
                "Oracle price manipulation",
                "Governance vote buying",
                "Liquidity pool drainage",
                "Collateral manipulation",
                "Same-block borrow/repay exploits",
                "Multi-block MEV attacks (2024+)",
                "Intent-based flash loan sandwiching",
                "Cross-chain flash loan arbitrage",
            ],
            detection_techniques=[
                "Check for TWAP usage vs spot price",
                "Verify governance voting has time delays",
                "Test price deviation limits",
                "Check for same-block action restrictions",
                "Validate MEV protection mechanisms",
                "Test multi-block state manipulation",
                "Check for intent front-running protection",
            ],
            recent_examples=[
                "Euler Finance ($197M, 2023) - Donation attack + flash loan",
                "Mango Markets ($110M, 2022) - Oracle manipulation via flash loan",
                "Cream Finance ($130M, 2021) - Flash loan price manipulation",
                "KyberSwap ($48M, 2023) - Complex flash loan arbitrage",
                "Curve Finance ($73M, 2024) - Multi-pool flash loan attack",
            ],
        ),
        "access_control": ImmunefiVulnerabilityClass(
            name="Access Control Vulnerabilities",
            severity="critical",
            typical_bounty_range=(100_000, 1_000_000),
            description="Missing or bypassable access controls on critical functions",
            common_patterns=[
                "Missing onlyOwner modifiers",
                "Unprotected initializers",
                "Proxy upgrade vulnerabilities",
                "Role-based access bypass",
                "Delegatecall to untrusted contracts",
            ],
            detection_techniques=[
                "Test all admin functions for access controls",
                "Check initializer protection",
                "Verify upgrade mechanisms",
                "Test role assignment/revocation",
            ],
            recent_examples=[
                "Poly Network ($611M, 2021) - Access control bypass",
                "Vulcan Forged ($140M, 2021) - Key compromise",
            ],
        ),
        "reentrancy": ImmunefiVulnerabilityClass(
            name="Reentrancy Attacks",
            severity="high",
            typical_bounty_range=(50_000, 200_000),
            description="Classic, cross-function, or read-only reentrancy vulnerabilities",
            common_patterns=[
                "Classic reentrancy (pre-state update external calls)",
                "Cross-function reentrancy",
                "Read-only reentrancy (2023 pattern)",
                "Cross-contract reentrancy",
                "CEI pattern violations",
            ],
            detection_techniques=[
                "Identify external calls before state updates",
                "Check for reentrancy guards",
                "Test view functions during state changes",
                "Verify CEI pattern compliance",
            ],
            recent_examples=[
                "Curve Finance ($62M potential, 2023) - Read-only reentrancy",
                "Grim Finance ($30M, 2021) - Cross-function reentrancy",
            ],
        ),
        "oracle_manipulation": ImmunefiVulnerabilityClass(
            name="Oracle Manipulation",
            severity="critical",
            typical_bounty_range=(100_000, 500_000),
            description="Manipulation of price oracles to exploit protocol logic",
            common_patterns=[
                "Reliance on manipulable spot prices",
                "Single oracle dependency",
                "Stale price data acceptance",
                "Missing price deviation checks",
                "Flash loan price manipulation",
            ],
            detection_techniques=[
                "Check oracle staleness validation",
                "Verify multi-oracle consensus",
                "Test price deviation limits",
                "Check for TWAP usage",
            ],
            recent_examples=[
                "Platypus Finance ($8.5M, 2023) - Oracle manipulation",
                "Hundred Finance ($7M, 2023) - Oracle price manipulation",
            ],
        ),
        "governance_attacks": ImmunefiVulnerabilityClass(
            name="Governance Attacks",
            severity="high",
            typical_bounty_range=(50_000, 300_000),
            description="Attacks on governance mechanisms to drain funds or manipulate protocol",
            common_patterns=[
                "Flash loan vote buying",
                "Proposal execution bypass",
                "Timelock manipulation",
                "Quorum manipulation",
                "Delegation attacks",
            ],
            detection_techniques=[
                "Check for snapshot-based voting",
                "Verify timelock on critical operations",
                "Test quorum requirements",
                "Check voting power calculation",
            ],
            recent_examples=[
                "Beanstalk ($182M, 2022) - Flash loan governance attack",
                "Fortress DAO ($3M, 2022) - Governance manipulation",
            ],
        ),
        "erc4626_vault_attacks": ImmunefiVulnerabilityClass(
            name="ERC4626 Vault Attacks",
            severity="critical",
            typical_bounty_range=(100_000, 500_000),
            description="Attacks on ERC4626 vaults through share inflation or donation attacks",
            common_patterns=[
                "First depositor inflation attack",
                "Donation attack",
                "Rounding error exploitation",
                "Share price manipulation",
                "Withdrawal/deposit race conditions",
            ],
            detection_techniques=[
                "Test first deposit scenarios",
                "Check for virtual shares protection",
                "Verify rounding in favor of vault",
                "Test large deposit/withdrawal sequences",
            ],
            recent_examples=[
                "Euler Finance ($197M, 2023) - Donation attack",
                "Sentiment ($1M, 2023) - Read-only reentrancy in vault",
            ],
        ),
        "proxy_patterns": ImmunefiVulnerabilityClass(
            name="Proxy Pattern Vulnerabilities",
            severity="critical",
            typical_bounty_range=(100_000, 1_000_000),
            description="Vulnerabilities in upgradeable proxy patterns",
            common_patterns=[
                "Unprotected proxy upgrades",
                "Storage collision",
                "Selfdestruct in implementation",
                "Delegatecall to untrusted contracts",
                "Initialize function exploits",
            ],
            detection_techniques=[
                "Check upgrade function access controls",
                "Verify storage layout compatibility",
                "Test initializer protection",
                "Check for selfdestruct usage",
            ],
            recent_examples=[
                "Audius ($6M, 2022) - Proxy upgrade exploit",
                "Harvest Finance ($34M, 2020) - Proxy manipulation",
            ],
        ),
        "account_abstraction": ImmunefiVulnerabilityClass(
            name="Account Abstraction (EIP-4337) Vulnerabilities",
            severity="critical",
            typical_bounty_range=(100_000, 1_000_000),
            description="Vulnerabilities in EIP-4337 account abstraction implementations",
            common_patterns=[
                "UserOperation validation bypass",
                "Paymaster exploitation",
                "Signature aggregation flaws",
                "EntryPoint contract manipulation",
                "Bundler MEV exploitation",
                "Session key compromise",
                "Gas estimation manipulation",
            ],
            detection_techniques=[
                "Test UserOperation signature validation",
                "Verify paymaster sponsor limits",
                "Test bundler replay protection",
                "Check session key expiration",
                "Validate gas griefing protection",
                "Test aggregator signature verification",
            ],
            recent_examples=[
                "Zyfi Paymaster ($200K, 2024) - Paymaster validation bypass",
                "Safe{Wallet} ($100K, 2024) - Signature replay in module",
                "Biconomy ($50K, 2024) - Session key validation flaw",
            ],
        ),
        "intent_based_protocols": ImmunefiVulnerabilityClass(
            name="Intent-Based Protocol Vulnerabilities",
            severity="critical",
            typical_bounty_range=(50_000, 500_000),
            description="Vulnerabilities in intent-based trading and settlement protocols",
            common_patterns=[
                "Intent front-running",
                "Solver collusion",
                "Settlement atomicity bypass",
                "Intent signature forgery",
                "Dutch auction manipulation",
                "Cross-chain intent settlement issues",
            ],
            detection_techniques=[
                "Test intent signature validation",
                "Verify solver selection fairness",
                "Check settlement atomicity guarantees",
                "Test auction price manipulation",
                "Validate cross-chain settlement finality",
            ],
            recent_examples=[
                "UniswapX ($75K, 2024) - Filler front-running vulnerability",
                "CowSwap ($120K, 2024) - Solver manipulation",
                "1inch Fusion ($90K, 2024) - Dutch auction exploit",
            ],
        ),
        "restaking_protocols": ImmunefiVulnerabilityClass(
            name="Restaking Protocol Vulnerabilities",
            severity="critical",
            typical_bounty_range=(100_000, 1_000_000),
            description="Vulnerabilities in liquid staking and restaking protocols (EigenLayer-style)",
            common_patterns=[
                "Withdrawal queue manipulation",
                "Slashing condition bypass",
                "Operator delegation exploits",
                "AVS (Actively Validated Service) integration flaws",
                "Share price manipulation",
                "Withdrawal delay exploitation",
            ],
            detection_techniques=[
                "Test withdrawal queue fairness",
                "Verify slashing conditions",
                "Check operator registration controls",
                "Test AVS integration security",
                "Validate share price calculations",
            ],
            recent_examples=[
                "Renzo Protocol ($150K, 2024) - Withdrawal queue exploit",
                "Puffer Finance ($200K, 2024) - Share price manipulation",
                "EigenLayer Testnet ($50K, 2024) - Delegation bypass",
            ],
        ),
    }

    @classmethod
    def get_vulnerability_patterns_for_protocol(
        cls, protocol_type: str
    ) -> list[ImmunefiVulnerabilityClass]:
        """Get relevant vulnerability patterns for a specific protocol type."""
        protocol_mapping = {
            "bridge": [
                "bridge_exploits",
                "oracle_manipulation",
                "access_control",
                "intent_based_protocols",
            ],
            "threshold_network": [
                "bridge_exploits",
                "governance_attacks",
                "access_control",
                "proxy_patterns",
                "restaking_protocols",
            ],
            "defi_vault": [
                "erc4626_vault_attacks",
                "flash_loan_attacks",
                "reentrancy",
                "oracle_manipulation",
            ],
            "lending": [
                "flash_loan_attacks",
                "oracle_manipulation",
                "reentrancy",
                "access_control",
            ],
            "amm": [
                "flash_loan_attacks",
                "oracle_manipulation",
                "reentrancy",
                "intent_based_protocols",
            ],
            "governance": [
                "governance_attacks",
                "flash_loan_attacks",
                "access_control",
                "proxy_patterns",
            ],
            "account_abstraction": [
                "account_abstraction",
                "access_control",
                "reentrancy",
            ],
            "restaking": [
                "restaking_protocols",
                "access_control",
                "oracle_manipulation",
            ],
        }

        pattern_keys = protocol_mapping.get(protocol_type, [])
        return [cls.COMMON_VULNERABILITIES[key] for key in pattern_keys if key in cls.COMMON_VULNERABILITIES]

    @classmethod
    def classify_severity(
        cls, impact_description: str, funds_at_risk: float | None = None
    ) -> tuple[str, int, int]:
        """
        Classify vulnerability severity based on Immunefi standards.

        Returns: (severity_level, min_bounty, max_bounty)
        """
        impact_lower = impact_description.lower()

        # Critical severity indicators
        critical_indicators = [
            "direct theft",
            "steal funds",
            "drain",
            "protocol insolvency",
            "permanent freezing",
            "loss of funds",
            "unauthorized withdrawal",
        ]
        if any(indicator in impact_lower for indicator in critical_indicators):
            if funds_at_risk:
                # Critical smart contract bugs: 10% of funds at risk
                bounty = int(funds_at_risk * 0.1)
                return ("critical", bounty, min(bounty, 1_000_000))
            return ("critical", 100_000, 1_000_000)

        # High severity indicators
        high_indicators = [
            "unclaimed yield",
            "temporary freezing",
            "freezing of funds for",
        ]
        if any(indicator in impact_lower for indicator in high_indicators):
            return ("high", 10_000, 50_000)

        # Medium severity indicators
        medium_indicators = [
            "griefing",
            "gas theft",
            "unbounded gas",
            "block stuffing",
            "unable to operate",
        ]
        if any(indicator in impact_lower for indicator in medium_indicators):
            return ("medium", 1_000, 10_000)

        # Default to low
        return ("low", 100, 1_000)

    @classmethod
    def get_detection_priority(cls, contract_name: str, function_name: str) -> int:
        """
        Get detection priority (1-10) for a contract/function combination.
        Higher priority = more likely to contain critical vulnerabilities.
        """
        # High priority contract patterns
        high_priority_contracts = {
            "bridge": 10,
            "vault": 9,
            "tbtc": 10,
            "wallet": 9,
            "staking": 8,
            "governance": 8,
            "token": 7,
        }

        # High priority function patterns
        high_priority_functions = {
            "mint": 9,
            "burn": 8,
            "upgrade": 10,
            "withdraw": 9,
            "deposit": 8,
            "transfer": 7,
            "redemption": 9,
            "execute": 8,
            "approve": 7,
            "initialize": 9,
            "validateuserop": 10,  # EIP-4337
            "handlepaymaster": 9,  # Paymaster
            "settleintent": 9,  # Intent-based
            "fillorder": 8,  # Intent settlement
            "slash": 9,  # Restaking slashing
            "delegateto": 8,  # Delegation
        }

        contract_lower = contract_name.lower()
        function_lower = function_name.lower()

        # Check contract priority
        contract_priority = max(
            (priority for pattern, priority in high_priority_contracts.items() if pattern in contract_lower),
            default=5,
        )

        # Check function priority
        function_priority = max(
            (priority for pattern, priority in high_priority_functions.items() if pattern in function_lower),
            default=5,
        )

        # Return the higher of the two
        return max(contract_priority, function_priority)

    @classmethod
    def get_threshold_network_focus_areas(cls) -> dict[str, Any]:
        """Get specific focus areas for Threshold Network based on Immunefi program."""
        return {
            "critical_contracts": [
                "TBTC",
                "TBTCVault",
                "Bridge",
                "WalletRegistry",
                "T",
                "TokenStaking",
            ],
            "critical_functions": [
                "mint*",
                "burn*",
                "redemption*",
                "deposit*",
                "withdraw*",
                "upgrade*",
                "initialize*",
                "submitProof*",
            ],
            "priority_vulnerabilities": [
                {
                    "type": "bitcoin_peg_manipulation",
                    "severity": "critical",
                    "max_bounty": 1_000_000,
                    "focus": "SPV proof verification, optimistic minting",
                },
                {
                    "type": "wallet_registry_compromise",
                    "severity": "critical",
                    "max_bounty": 1_000_000,
                    "focus": "Wallet registration, signing group selection",
                },
                {
                    "type": "cross_chain_message_forgery",
                    "severity": "critical",
                    "max_bounty": 1_000_000,
                    "focus": "Message verification, relay security",
                },
                {
                    "type": "threshold_signature_bypass",
                    "severity": "critical",
                    "max_bounty": 1_000_000,
                    "focus": "Signature aggregation, DKG protocol",
                },
                {
                    "type": "proxy_upgrade_exploit",
                    "severity": "critical",
                    "max_bounty": 1_000_000,
                    "focus": "Upgrade mechanisms, storage layout",
                },
            ],
            "testing_priorities": [
                "Test all Bitcoin proof verification logic",
                "Test wallet registry access controls",
                "Test cross-chain message validation",
                "Test signature aggregation and verification",
                "Test proxy upgrade mechanisms",
                "Test staking reward calculations",
                "Test governance voting mechanisms",
            ],
        }
