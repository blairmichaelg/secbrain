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


class ThresholdNetworkPatterns:
    """Comprehensive Threshold Network vulnerability patterns database."""

    # tBTC Bridge Patterns
    TBTC_BRIDGE_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = {
        "bitcoin_peg_manipulation": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.BITCOIN_PEG_MANIPULATION,
            severity=ImmunefiSeverity.CRITICAL,
            description="Manipulation of Bitcoin peg mechanism to mint unbacked tBTC or prevent redemptions",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "mint",
                "mintTBTC",
                "optimisticMint",
                "requestRedemption",
                "bridge deposit",
                "BTC transaction proof",
                "SPV proof verification",
            ],
            exploitation_steps=[
                "1. Find flaw in Bitcoin SPV proof verification",
                "2. Craft malicious Bitcoin transaction proof",
                "3. Submit proof to bridge to mint unbacked tBTC",
                "4. Alternative: Block legitimate redemptions by manipulating proof validation",
            ],
            mitigation_strategies=[
                "Rigorous SPV proof validation with multiple confirmations",
                "Time-delayed optimistic minting with challenge period",
                "Guardian oversight for large mints",
                "Rate limiting on mint operations",
                "Multi-oracle consensus for Bitcoin transaction confirmation",
            ],
            references=[
                "https://docs.threshold.network/applications/tbtc-v2",
                "https://immunefi.com/bug-bounty/thresholdnetwork/",
            ],
            affected_contracts=["TBTC", "TBTCVault", "Bridge"],
        ),
        "wallet_registry_compromise": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.WALLET_REGISTRY_COMPROMISE,
            severity=ImmunefiSeverity.CRITICAL,
            description="Compromise of wallet registry to control Bitcoin wallets or signing groups",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "registerWallet",
                "updateWallet",
                "walletOwner",
                "signingGroup",
                "operator registration",
                "wallet public key",
            ],
            exploitation_steps=[
                "1. Find access control flaw in wallet registration",
                "2. Register malicious wallet or compromise existing wallet",
                "3. Gain control of signing authority",
                "4. Steal deposited Bitcoin or prevent redemptions",
            ],
            mitigation_strategies=[
                "Strict access controls on wallet registry modifications",
                "Multi-signature requirements for wallet updates",
                "Time-delayed wallet changes with governance oversight",
                "Operator stake slashing for malicious behavior",
            ],
            references=[
                "https://docs.threshold.network/staking-and-running-a-node/threshold-stake",
            ],
            affected_contracts=["WalletRegistry", "WalletCoordinator", "Bridge"],
        ),
        "redemption_proof_forgery": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.REDEMPTION_PROOF_FORGERY,
            severity=ImmunefiSeverity.CRITICAL,
            description="Forging redemption proofs to steal Bitcoin from the bridge",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "requestRedemption",
                "proveRedemption",
                "submitRedemptionProof",
                "Bitcoin transaction proof",
                "redemption verification",
            ],
            exploitation_steps=[
                "1. Analyze redemption proof verification logic",
                "2. Craft forged proof that bypasses validation",
                "3. Submit forged proof to claim Bitcoin",
                "4. Drain bridge funds through repeated false redemptions",
            ],
            mitigation_strategies=[
                "Cryptographic proof verification with multiple validators",
                "Challenge period for redemptions",
                "Rate limiting and anomaly detection",
                "Guardian monitoring of large redemptions",
            ],
            references=[
                "https://docs.threshold.network/applications/tbtc-v2/tbtc-v2-technical-design",
            ],
            affected_contracts=["Bridge", "TBTCVault", "RedemptionWatchtower"],
        ),
    }

    # Threshold Cryptography Patterns
    THRESHOLD_CRYPTO_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = {
        "threshold_signature_manipulation": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.THRESHOLD_SIGNATURE_MANIPULATION,
            severity=ImmunefiSeverity.CRITICAL,
            description="Manipulation of threshold signature scheme to bypass multi-party signing",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "threshold signature",
                "ECDSA",
                "signing group",
                "signature aggregation",
                "submitSignature",
                "verifySignature",
            ],
            exploitation_steps=[
                "1. Identify flaw in signature aggregation or verification",
                "2. Manipulate signature components to bypass threshold requirement",
                "3. Execute unauthorized transactions with forged signatures",
            ],
            mitigation_strategies=[
                "Formal verification of signature scheme implementation",
                "Multiple independent signature verification layers",
                "Operator stake requirements to prevent malicious signing",
                "Slashing mechanism for invalid signatures",
            ],
            references=[
                "https://docs.threshold.network/app-development/threshold-access-control",
            ],
            affected_contracts=["WalletRegistry", "Bridge", "ECDSA"],
        ),
        "dkg_protocol_attack": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.DKG_PROTOCOL_ATTACK,
            severity=ImmunefiSeverity.CRITICAL,
            description="Attack on Distributed Key Generation protocol to compromise wallet keys",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "DKG",
                "key generation",
                "group formation",
                "operator selection",
                "randomness",
            ],
            exploitation_steps=[
                "1. Exploit randomness source in DKG protocol",
                "2. Influence operator selection to include malicious nodes",
                "3. Compromise key shares during generation",
                "4. Reconstruct private key to steal funds",
            ],
            mitigation_strategies=[
                "Secure randomness source (Random Beacon)",
                "Verification of DKG process integrity",
                "Minimum stake requirements for operators",
                "Key rotation and refreshing mechanisms",
            ],
            references=[
                "https://docs.threshold.network/staking-and-running-a-node/random-beacon-overview",
            ],
            affected_contracts=["WalletRegistry", "RandomBeacon", "SortitionPool"],
        ),
        "operator_collusion": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.OPERATOR_COLLUSION,
            severity=ImmunefiSeverity.HIGH,
            description="Collusion attack where operators combine to bypass threshold requirements",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "operator count",
                "threshold parameter",
                "signature threshold",
                "minimum operators",
            ],
            exploitation_steps=[
                "1. Compromise or collude with enough operators to meet threshold",
                "2. Execute unauthorized signing operations",
                "3. Steal funds or disrupt protocol operation",
            ],
            mitigation_strategies=[
                "Higher threshold requirements (e.g., 51 of 100 instead of 3 of 5)",
                "Economic incentives against collusion (high stake requirements)",
                "Operator diversity and geographic distribution",
                "Monitoring and anomaly detection for operator behavior",
            ],
            references=[
                "https://docs.threshold.network/staking-and-running-a-node/threshold-stake",
            ],
            affected_contracts=["WalletRegistry", "TokenStaking"],
        ),
    }

    # Cross-chain Bridge Patterns
    CROSS_CHAIN_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = {
        "cross_chain_message_forgery": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.CROSS_CHAIN_MESSAGE_FORGERY,
            severity=ImmunefiSeverity.CRITICAL,
            description="Forging cross-chain messages to execute unauthorized operations",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "cross-chain message",
                "relayer",
                "message verification",
                "bridge message",
                "L2 communication",
            ],
            exploitation_steps=[
                "1. Analyze cross-chain message verification",
                "2. Craft forged message that bypasses validation",
                "3. Submit to destination chain to execute malicious operation",
            ],
            mitigation_strategies=[
                "Cryptographic message authentication",
                "Multiple relayer consensus",
                "Time-delayed execution with challenge period",
                "Message replay protection",
            ],
            references=[
                "https://docs.threshold.network/",
            ],
            affected_contracts=["ArbitrumBridge", "StarknetBridge", "WormholeBridge"],
        ),
        "wormhole_bridge_exploit": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.WORMHOLE_BRIDGE_EXPLOIT,
            severity=ImmunefiSeverity.CRITICAL,
            description="Exploit in Wormhole integration to steal cross-chain assets",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "wormhole",
                "VAA",  # Verified Action Approval
                "guardian signature",
                "cross-chain transfer",
            ],
            exploitation_steps=[
                "1. Find vulnerability in Wormhole message verification",
                "2. Forge or manipulate VAA (Verified Action Approval)",
                "3. Mint or unlock tokens on destination chain without proper backing",
            ],
            mitigation_strategies=[
                "Independent verification of Wormhole messages",
                "Rate limiting on cross-chain transfers",
                "Multi-oracle validation",
                "Circuit breakers for anomalous activity",
            ],
            references=[
                "https://immunefi.com/bug-bounty/thresholdnetwork/",
            ],
            affected_contracts=["WormholeGateway", "Bridge"],
        ),
    }

    # Staking and Governance Patterns
    STAKING_GOVERNANCE_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = {
        "staking_reward_manipulation": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.STAKING_REWARD_MANIPULATION,
            severity=ImmunefiSeverity.HIGH,
            description="Manipulation of staking rewards calculation to steal funds",
            immunefi_category="Theft of unclaimed yield",
            max_bounty_usd=50_000,
            detection_heuristics=[
                "stake",
                "unstake",
                "reward calculation",
                "mintRewards",
                "claimRewards",
                "reward rate",
            ],
            exploitation_steps=[
                "1. Analyze reward calculation logic",
                "2. Find integer overflow, rounding error, or logic flaw",
                "3. Stake/unstake in pattern that exploits flaw",
                "4. Claim inflated rewards",
            ],
            mitigation_strategies=[
                "Careful reward math with SafeMath or checked arithmetic",
                "Upper bounds on reward claims",
                "Time-weighted reward calculations",
                "Audit of all reward computation paths",
            ],
            references=[
                "https://docs.threshold.network/staking-and-running-a-node/staking-providers",
            ],
            affected_contracts=["TokenStaking", "RebateStaking"],
        ),
        "governance_vote_buying": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.GOVERNANCE_VOTE_BUYING,
            severity=ImmunefiSeverity.HIGH,
            description="Flash loan attack to temporarily acquire voting power for malicious proposals",
            immunefi_category="Theft of unclaimed yield",
            max_bounty_usd=50_000,
            detection_heuristics=[
                "governance",
                "voting power",
                "flash loan",
                "snapshot",
                "delegate",
                "proposal",
            ],
            exploitation_steps=[
                "1. Flash loan large amount of governance tokens",
                "2. Delegate to self to gain voting power",
                "3. Vote on malicious proposal",
                "4. Repay flash loan in same transaction",
            ],
            mitigation_strategies=[
                "Snapshot-based voting (voting power at specific block)",
                "Time-locked delegation (delay before voting power activates)",
                "Minimum holding period for voters",
                "Quorum and time-delay requirements",
            ],
            references=[
                "https://docs.threshold.network/governance/threshold-dao",
            ],
            affected_contracts=["TokenholderGovernor", "T"],
        ),
        "proxy_upgrade_exploit": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.PROXY_UPGRADE_EXPLOIT,
            severity=ImmunefiSeverity.CRITICAL,
            description="Exploit proxy upgrade mechanism to inject malicious implementation",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "upgradeTo",
                "upgradeToAndCall",
                "proxy",
                "implementation",
                "delegatecall",
                "TransparentUpgradeableProxy",
            ],
            exploitation_steps=[
                "1. Find access control flaw in upgrade function",
                "2. Deploy malicious implementation contract",
                "3. Upgrade proxy to point to malicious implementation",
                "4. Execute theft through malicious code",
            ],
            mitigation_strategies=[
                "Multi-sig control over upgrades",
                "Timelock on upgrade execution",
                "Governance voting for upgrades",
                "Immutable critical functions",
            ],
            references=[
                "https://docs.openzeppelin.com/contracts/4.x/api/proxy",
            ],
            affected_contracts=[
                "TBTC",
                "TBTCVault",
                "Bridge",
                "TokenStaking",
                "WalletRegistry",
            ],
        ),
    }

    # Token Merger Patterns (KEEP + NU -> T)
    TOKEN_MERGER_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = {
        "vending_machine_exploit": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.VENDING_MACHINE_EXPLOIT,
            severity=ImmunefiSeverity.HIGH,
            description="Exploit vending machine contracts that convert KEEP/NU to T tokens",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=50_000,
            detection_heuristics=[
                "vending machine",
                "wrap",
                "unwrap",
                "conversion ratio",
                "KEEP",
                "NU",
                "T token",
            ],
            exploitation_steps=[
                "1. Analyze conversion ratio calculation",
                "2. Find flaw in wrap/unwrap logic",
                "3. Exploit to get favorable conversion rate",
                "4. Drain one side of the vending machine",
            ],
            mitigation_strategies=[
                "Fixed conversion ratios based on snapshot",
                "One-way conversion (no unwrap)",
                "Supply caps on conversions",
                "Rate limiting",
            ],
            references=[
                "https://docs.threshold.network/governance/threshold-dao/dao-tooling",
            ],
            affected_contracts=["VendingMachine", "T"],
        ),
    }

    # New 2024-2025 Attack Patterns
    ADVANCED_PATTERNS: ClassVar[dict[str, ThresholdSecurityPattern]] = {
        "zk_proof_verification_flaw": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.ZK_PROOF_VERIFICATION_FLAW,
            severity=ImmunefiSeverity.CRITICAL,
            description="Vulnerabilities in zero-knowledge proof verification for cross-chain operations",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "zk proof",
                "zkSNARK",
                "zkSTARK",
                "verify proof",
                "proof validation",
                "circuit verification",
            ],
            exploitation_steps=[
                "1. Analyze ZK proof verification circuit",
                "2. Find edge case or malformed proof acceptance",
                "3. Craft malicious proof that passes verification",
                "4. Execute unauthorized cross-chain operation",
            ],
            mitigation_strategies=[
                "Formal verification of ZK circuits",
                "Multiple independent proof verifiers",
                "Trusted setup validation",
                "Proof challenge period",
            ],
            references=[
                "https://docs.threshold.network/",
            ],
            affected_contracts=["Bridge", "L2Bridge"],
        ),
        "optimistic_challenge_bypass": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.OPTIMISTIC_CHALLENGE_BYPASS,
            severity=ImmunefiSeverity.CRITICAL,
            description="Bypass optimistic assumption challenge mechanisms in bridge operations",
            immunefi_category="Direct theft of any user funds",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "challenge",
                "dispute",
                "fraud proof",
                "optimistic",
                "challenge period",
                "finalize",
            ],
            exploitation_steps=[
                "1. Identify optimistic bridge operations",
                "2. Find weakness in challenge mechanism",
                "3. Submit fraudulent operation during challenge window",
                "4. Prevent or bypass valid challenges",
                "5. Finalize fraudulent operation after timeout",
            ],
            mitigation_strategies=[
                "Multiple independent watchers",
                "Economic incentives for challengers",
                "Sufficient challenge periods",
                "Automated fraud detection",
            ],
            references=[
                "https://docs.threshold.network/applications/tbtc-v2",
            ],
            affected_contracts=["Bridge", "TBTCVault", "RedemptionWatchtower"],
        ),
        "mev_extraction_vulnerability": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.MEV_EXTRACTION_VULNERABILITY,
            severity=ImmunefiSeverity.HIGH,
            description="MEV extraction vulnerabilities in deposit/withdrawal/redemption operations",
            immunefi_category="Theft of unclaimed yield",
            max_bounty_usd=50_000,
            detection_heuristics=[
                "deposit",
                "withdraw",
                "redemption",
                "front-run",
                "sandwich",
                "atomic arbitrage",
            ],
            exploitation_steps=[
                "1. Monitor mempool for bridge operations",
                "2. Identify profitable MEV opportunities",
                "3. Front-run or sandwich user transactions",
                "4. Extract value from operation ordering",
            ],
            mitigation_strategies=[
                "Commit-reveal schemes",
                "Time-delayed operations",
                "Flashbots private transactions",
                "Fair ordering mechanisms",
            ],
            references=[
                "https://docs.threshold.network/",
            ],
            affected_contracts=["Bridge", "TBTCVault", "TokenStaking"],
        ),
        "withdrawal_queue_manipulation": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.WITHDRAWAL_QUEUE_MANIPULATION,
            severity=ImmunefiSeverity.HIGH,
            description="Manipulation of withdrawal queue to gain unfair advantage or grief users",
            immunefi_category="Temporary freezing of funds for at least 1 hour",
            max_bounty_usd=50_000,
            detection_heuristics=[
                "withdrawal queue",
                "withdraw",
                "unstake",
                "exit queue",
                "withdrawal delay",
            ],
            exploitation_steps=[
                "1. Analyze withdrawal queue mechanics",
                "2. Find queue jumping or griefing vectors",
                "3. Manipulate queue position or timing",
                "4. Delay or front-run other withdrawals",
            ],
            mitigation_strategies=[
                "FIFO queue enforcement",
                "Proportional withdrawal processing",
                "Anti-griefing mechanisms",
                "Queue size limits",
            ],
            references=[
                "https://docs.threshold.network/staking-and-running-a-node",
            ],
            affected_contracts=["TokenStaking", "RebateStaking", "TBTCVault"],
        ),
        "slashing_mechanism_bypass": ThresholdSecurityPattern(
            pattern_type=ThresholdVulnerabilityPattern.SLASHING_MECHANISM_BYPASS,
            severity=ImmunefiSeverity.CRITICAL,
            description="Bypass or exploit slashing mechanisms to avoid penalties for malicious behavior",
            immunefi_category="Protocol insolvency",
            max_bounty_usd=1_000_000,
            detection_heuristics=[
                "slash",
                "seize",
                "penalize",
                "malicious operator",
                "stake burn",
            ],
            exploitation_steps=[
                "1. Analyze slashing conditions and triggers",
                "2. Find bypass or exploit in slash execution",
                "3. Perform malicious operations without penalty",
                "4. Withdraw stake before slashing occurs",
            ],
            mitigation_strategies=[
                "Immediate stake locking on malicious detection",
                "Multiple independent slash enforcers",
                "Economic guarantees for slashing",
                "Timelock on stake withdrawals",
            ],
            references=[
                "https://docs.threshold.network/staking-and-running-a-node/threshold-stake",
            ],
            affected_contracts=["TokenStaking", "WalletRegistry", "RandomBeacon"],
        ),
    }

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
