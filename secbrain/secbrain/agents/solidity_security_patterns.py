"""Advanced Solidity security patterns for vulnerability detection.

This module implements state-of-the-art smart contract security patterns
including reentrancy guards, flash loan attack detection, access control,
front-running protection, oracle security, and formal verification hints.

References:
- Consensys Smart Contract Best Practices
- Trail of Bits Building Secure Contracts
- DeFi Security Summit 2024 Findings
- Secureum Security Pitfalls
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar


class VulnerabilityPattern(Enum):
    """Advanced vulnerability patterns based on latest security research."""

    # Reentrancy patterns
    CLASSIC_REENTRANCY = "classic_reentrancy"
    CROSS_FUNCTION_REENTRANCY = "cross_function_reentrancy"
    READ_ONLY_REENTRANCY = "read_only_reentrancy"  # New attack vector (2023)
    CEI_VIOLATION = "checks_effects_interactions_violation"

    # Flash loan patterns
    FLASH_LOAN_PRICE_MANIPULATION = "flash_loan_price_manipulation"
    FLASH_LOAN_GOVERNANCE_ATTACK = "flash_loan_governance_attack"
    SAME_BLOCK_BORROW_REPAY = "same_block_borrow_repay"
    ORACLE_MANIPULATION_FLASH = "oracle_manipulation_flash"

    # Access control patterns
    MISSING_ACCESS_CONTROL = "missing_access_control"
    WEAK_ACCESS_CONTROL = "weak_access_control"
    ROLE_BASED_ACCESS_NEEDED = "role_based_access_needed"
    MULTI_LEVEL_ACCESS_MISSING = "multi_level_access_missing"

    # Front-running patterns
    FRONT_RUNNING_VULNERABLE = "front_running_vulnerable"
    MISSING_COMMIT_REVEAL = "missing_commit_reveal"
    NO_TIMELOCK = "no_timelock"
    MISSING_EIP712_SIGNATURE = "missing_eip712_signature"

    # Oracle security patterns
    STALE_PRICE_DATA = "stale_price_data"
    SINGLE_ORACLE_DEPENDENCY = "single_oracle_dependency"
    MISSING_TWAP = "missing_twap"
    NO_PRICE_DEVIATION_CHECK = "no_price_deviation_check"
    NO_MULTI_ORACLE_CONSENSUS = "no_multi_oracle_consensus"

    # Bridge security patterns (cross-chain)
    BRIDGE_MESSAGE_FORGERY = "bridge_message_forgery"
    MERKLE_PROOF_MANIPULATION = "merkle_proof_manipulation"
    SPV_PROOF_BYPASS = "spv_proof_bypass"
    CROSS_CHAIN_REPLAY = "cross_chain_replay"
    RELAY_CENSORSHIP = "relay_censorship"
    DEPOSIT_WITHDRAWAL_MISMATCH = "deposit_withdrawal_mismatch"
    BRIDGE_SIGNATURE_BYPASS = "bridge_signature_bypass"

    # DAO governance patterns
    GOVERNANCE_FLASH_LOAN_ATTACK = "governance_flash_loan_attack"
    PROPOSAL_EXECUTION_BYPASS = "proposal_execution_bypass"
    TIMELOCK_BYPASS = "timelock_bypass"
    QUORUM_MANIPULATION = "quorum_manipulation"
    DELEGATION_ATTACK = "delegation_attack"


@dataclass
class SecurityPattern:
    """Represents a security pattern with detection and mitigation."""

    pattern_type: VulnerabilityPattern
    severity: str  # "critical", "high", "medium", "low"
    description: str
    detection_heuristics: list[str] = field(default_factory=list)
    mitigation_code: str = ""
    references: list[str] = field(default_factory=list)


from pathlib import Path

import yaml


def _load_solidity_yaml() -> dict:
    yaml_path = Path(__file__).parent.parent / "patterns" / "solidity_patterns.yaml"
    with open(yaml_path) as f:
        return yaml.safe_load(f)

def _parse_solidity_patterns(data: dict) -> dict[str, SecurityPattern]:
    res: dict[str, SecurityPattern] = {}
    if not data:
        return res
    for k, v in data.items():
        res[k] = SecurityPattern(
            pattern_type=VulnerabilityPattern(v["pattern_type"]),
            severity=v["severity"],
            description=v["description"],
            detection_heuristics=v.get("detection_heuristics", []),
            mitigation_code=v.get("mitigation_code", ""),
            references=v.get("references", []),
        )
    return res

_solidity_data = _load_solidity_yaml()

class SoliditySecurityPatterns:
    """Advanced Solidity security patterns database."""

    REENTRANCY_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("REENTRANCY_PATTERNS", {}))
    FLASH_LOAN_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("FLASH_LOAN_PATTERNS", {}))
    ACCESS_CONTROL_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("ACCESS_CONTROL_PATTERNS", {}))
    FRONT_RUNNING_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("FRONT_RUNNING_PATTERNS", {}))
    ORACLE_SECURITY_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("ORACLE_SECURITY_PATTERNS", {}))
    BRIDGE_SECURITY_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("BRIDGE_SECURITY_PATTERNS", {}))
    DAO_GOVERNANCE_PATTERNS: ClassVar[dict[str, SecurityPattern]] = _parse_solidity_patterns(_solidity_data.get("DAO_GOVERNANCE_PATTERNS", {}))

    @classmethod
    def get_all_patterns(cls) -> dict[str, SecurityPattern]:
        """Get all security patterns."""
        all_patterns = {}
        all_patterns.update(cls.REENTRANCY_PATTERNS)
        all_patterns.update(cls.FLASH_LOAN_PATTERNS)
        all_patterns.update(cls.ACCESS_CONTROL_PATTERNS)
        all_patterns.update(cls.FRONT_RUNNING_PATTERNS)
        all_patterns.update(cls.ORACLE_SECURITY_PATTERNS)
        all_patterns.update(cls.BRIDGE_SECURITY_PATTERNS)
        all_patterns.update(cls.DAO_GOVERNANCE_PATTERNS)
        return all_patterns

    @classmethod
    def detect_patterns(cls, contract_code: str, abi: list[Any]) -> list[SecurityPattern]:
        """Detect security patterns in contract code."""
        detected = []
        all_patterns = cls.get_all_patterns()

        code_lower = contract_code.lower()

        for _pattern_key, pattern in all_patterns.items():
            # Check if any detection heuristics match
            for heuristic in pattern.detection_heuristics:
                if heuristic.lower() in code_lower:
                    detected.append(pattern)
                    break

        return detected

    @classmethod
    def get_mitigation_for_pattern(cls, pattern_type: VulnerabilityPattern) -> str:
        """Get mitigation code for a specific pattern."""
        all_patterns = cls.get_all_patterns()

        for pattern in all_patterns.values():
            if pattern.pattern_type == pattern_type:
                return pattern.mitigation_code

        return ""


class FormalVerificationPatterns:
    """Formal verification hints and patterns for invariant testing."""

    @staticmethod
    def generate_natspec_invariants(function_name: str, invariants: list[str]) -> str:
        """Generate NatSpec annotations for invariants."""
        invariant_docs = "\n".join([f"    /// @invariant {inv}" for inv in invariants])

        return f'''
    /// @notice {function_name}
{invariant_docs}
    /// @dev Ensure all invariants hold before and after execution
'''

    @staticmethod
    def generate_foundry_invariant_test(contract_name: str, invariants: list[str]) -> str:
        """Generate Foundry invariant test template."""
        invariant_checks = "\n        ".join([
            f"assertTrue({inv}, \"Invariant failed: {inv}\");"
            for inv in invariants
        ])

        return f'''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/{contract_name}.sol";

contract {contract_name}InvariantTest is Test {{
    {contract_name} public target;

    function setUp() public {{
        target = new {contract_name}();
    }}

    /// @dev Foundry will call this after every function call
    function invariant_criticalInvariants() public {{
        {invariant_checks}
    }}
}}
'''

    @staticmethod
    def get_common_invariants() -> dict[str, list[str]]:
        """Get common invariants for different contract types."""
        return {
            "erc20": [
                "totalSupply == sum(balanceOf(user) for all users)",
                "balanceOf(user) <= totalSupply for all users",
                "balanceOf(user) >= 0 for all users",
            ],
            "vault": [
                "totalAssets >= sum(userDeposits)",
                "sharePrice never decreases (except for losses)",
                "totalShares * sharePrice == totalAssets",
            ],
            "lending": [
                "totalBorrowed <= totalDeposited",
                "userCollateral >= userBorrowedValue * collateralRatio",
                "sum(userDeposits) >= sum(userBorrows)",
            ],
            "staking": [
                "totalStaked == sum(userStakes)",
                "rewardsDistributed <= rewardsAllocated",
                "userRewards >= 0",
            ],
        }
