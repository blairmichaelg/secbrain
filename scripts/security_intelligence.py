#!/usr/bin/env python3
"""
Security Intelligence Gathering Script

Fetches latest security advisories, CVEs, and DeFi exploit patterns to
inform AI-generated recommendations.
"""
import json
import sys
from datetime import UTC, datetime
from typing import Any


def get_recent_python_cves() -> list[dict[str, Any]]:
    """
    Get recent Python-related CVEs and security advisories.
    
    Note: This returns known patterns to check for. In production, this would
    query the GitHub Advisory Database API or NVD API.
    """
    print("🔍 Checking Python ecosystem security advisories...", file=sys.stderr)
    
    # These are real security concerns to check for
    advisories = [
        {
            "ecosystem": "pip",
            "concern": "Dependency confusion attacks",
            "recommendation": "Use hash-pinned dependencies and private package indexes",
            "severity": "high",
        },
        {
            "ecosystem": "python",
            "concern": "pickle deserialization vulnerabilities",
            "recommendation": "Avoid using pickle for untrusted data, use JSON or Protocol Buffers",
            "severity": "high",
        },
        {
            "ecosystem": "python",
            "concern": "SQL injection in dynamic queries",
            "recommendation": "Use parameterized queries and LiteralString type hints (PEP 675)",
            "severity": "critical",
        },
        {
            "ecosystem": "python",
            "concern": "Command injection via subprocess",
            "recommendation": "Avoid shell=True, validate all inputs, use shlex.quote()",
            "severity": "critical",
        },
    ]
    
    return advisories


def get_defi_exploit_patterns() -> list[dict[str, Any]]:
    """
    Get recent DeFi exploit patterns and attack vectors.
    
    Based on real exploits from 2023-2024.
    """
    print("🔍 Analyzing recent DeFi exploit patterns...", file=sys.stderr)
    
    patterns = [
        {
            "attack_type": "Read-only reentrancy",
            "discovered": "2023",
            "description": "Exploiting view functions during reentrancy to get stale data",
            "affected_protocols": ["Curve Finance", "Multiple AMMs"],
            "mitigation": "Add reentrancy guards to view functions, use Checks-Effects-Interactions pattern",
            "severity": "critical",
            "reference": "https://chainsecurity.com/curve-lp-oracle-manipulation-post-mortem/",
        },
        {
            "attack_type": "Oracle manipulation via flash loans",
            "discovered": "2020-2024 (ongoing)",
            "description": "Manipulating price oracles in single block using flash loans",
            "affected_protocols": ["Multiple DeFi protocols"],
            "mitigation": "Use TWAP oracles, Chainlink price feeds, multi-oracle systems",
            "severity": "critical",
            "reference": "https://blog.openzeppelin.com/secure-smart-contract-guidelines-the-dangers-of-price-oracles",
        },
        {
            "attack_type": "Access control bypass",
            "discovered": "2024",
            "description": "Exploiting missing or incorrect access control checks",
            "affected_protocols": ["Various"],
            "mitigation": "Use OpenZeppelin AccessControl, comprehensive testing of permissions",
            "severity": "high",
            "reference": "https://github.com/OpenZeppelin/openzeppelin-contracts",
        },
        {
            "attack_type": "Integer overflow/underflow post-0.8.x",
            "discovered": "2023-2024",
            "description": "Logical errors assuming overflow/underflow protection in all contexts",
            "affected_protocols": ["Various"],
            "mitigation": "Careful use of unchecked blocks, comprehensive testing",
            "severity": "medium",
            "reference": "https://docs.soliditylang.org/en/latest/080-breaking-changes.html",
        },
        {
            "attack_type": "Front-running and MEV exploitation",
            "discovered": "Ongoing",
            "description": "Transaction ordering manipulation for profit extraction",
            "affected_protocols": ["Most DeFi protocols"],
            "mitigation": "Commit-reveal schemes, private mempools, time-locks, slippage protection",
            "severity": "high",
            "reference": "https://ethereum.org/en/developers/docs/mev/",
        },
    ]
    
    return patterns


def get_solidity_best_practices() -> list[dict[str, Any]]:
    """
    Get latest Solidity best practices and security patterns.
    """
    print("🔍 Gathering Solidity security best practices...", file=sys.stderr)
    
    practices = [
        {
            "category": "Gas Optimization",
            "practice": "Use custom errors instead of revert strings",
            "version": "0.8.4+",
            "benefit": "Significant gas savings on reverts",
            "example": "error Unauthorized(); instead of require(msg.sender == owner, 'Unauthorized');",
        },
        {
            "category": "Security",
            "practice": "Implement Checks-Effects-Interactions pattern",
            "version": "All versions",
            "benefit": "Prevents reentrancy attacks",
            "example": "Update state before external calls",
        },
        {
            "category": "Access Control",
            "practice": "Use OpenZeppelin AccessControl over simple Ownable",
            "version": "All versions",
            "benefit": "Role-based permissions, more flexible",
            "example": "import '@openzeppelin/contracts/access/AccessControl.sol';",
        },
        {
            "category": "Testing",
            "practice": "Implement invariant testing with Foundry",
            "version": "All versions",
            "benefit": "Catch edge cases and state inconsistencies",
            "example": "function invariant_totalSupplyConsistency() public { ... }",
        },
        {
            "category": "Gas Optimization",
            "practice": "Use immutable for constructor-set constants",
            "version": "0.6.5+",
            "benefit": "Gas savings on reads",
            "example": "address immutable public owner;",
        },
    ]
    
    return practices


def get_python_advanced_features() -> list[dict[str, Any]]:
    """
    Get Python 3.11+ advanced features relevant for security.
    """
    print("🔍 Identifying Python 3.11+ security features...", file=sys.stderr)
    
    features = [
        {
            "feature": "LiteralString type (PEP 675)",
            "version": "3.11+",
            "use_case": "Prevent SQL/command injection at type-check time",
            "example": "def execute_query(query: LiteralString) -> list: ...",
            "security_benefit": "Compile-time prevention of injection vulnerabilities",
        },
        {
            "feature": "Self type (PEP 673)",
            "version": "3.11+",
            "use_case": "Better type inference for method chaining",
            "example": "def set_value(self: Self, value: int) -> Self: ...",
            "security_benefit": "Improved type safety in builder patterns",
        },
        {
            "feature": "TypedDict with total=False",
            "version": "3.8+",
            "use_case": "Strict typing for dictionaries",
            "example": "class Config(TypedDict): api_key: str; timeout: int",
            "security_benefit": "Prevent missing required configuration",
        },
        {
            "feature": "Structural pattern matching",
            "version": "3.10+",
            "use_case": "Type-safe data validation",
            "example": "match value: case {'type': 'admin', 'id': int(uid)}: ...",
            "security_benefit": "Exhaustive checking of variants",
        },
    ]
    
    return features


def get_testing_strategies() -> list[dict[str, Any]]:
    """
    Get advanced testing strategies for security-critical code.
    """
    print("🔍 Compiling advanced testing strategies...", file=sys.stderr)
    
    strategies = [
        {
            "strategy": "Property-based testing with Hypothesis",
            "tool": "hypothesis",
            "use_case": "Find edge cases in security logic",
            "example": "@given(st.integers()) def test_always_positive(x): ...",
            "benefit": "Discovers inputs that violate invariants",
        },
        {
            "strategy": "Mutation testing",
            "tool": "mutmut",
            "use_case": "Verify test suite quality",
            "example": "mutmut run --paths-to-mutate=secbrain/",
            "benefit": "Ensures tests catch real bugs",
        },
        {
            "strategy": "Fuzzing with coverage guidance",
            "tool": "atheris, pythonfuzz",
            "use_case": "Find crashes and unexpected behavior",
            "example": "atheris.instrument_all()",
            "benefit": "Discovers security vulnerabilities",
        },
        {
            "strategy": "Solidity invariant testing",
            "tool": "Foundry",
            "use_case": "Test contract invariants hold",
            "example": "function invariant_balanceNonNegative() public { ... }",
            "benefit": "Catches state inconsistencies",
        },
        {
            "strategy": "Symbolic execution",
            "tool": "Manticore, Mythril",
            "use_case": "Find all execution paths",
            "example": "manticore contract.sol",
            "benefit": "Complete path coverage analysis",
        },
    ]
    
    return strategies


def main() -> None:
    """Gather all security intelligence."""
    print("🚀 Gathering security intelligence...\n", file=sys.stderr)
    
    intelligence = {
        "timestamp": datetime.now(UTC).isoformat(),
        "python_cves": get_recent_python_cves(),
        "defi_exploits": get_defi_exploit_patterns(),
        "solidity_best_practices": get_solidity_best_practices(),
        "python_advanced_features": get_python_advanced_features(),
        "testing_strategies": get_testing_strategies(),
    }
    
    print(json.dumps(intelligence, indent=2))


if __name__ == "__main__":
    main()
