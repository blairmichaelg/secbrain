"""Tests for advanced Solidity security patterns."""


from secbrain.agents.solidity_security_patterns import (
    FormalVerificationPatterns,
    SecurityPattern,
    SoliditySecurityPatterns,
    VulnerabilityPattern,
)


class TestSoliditySecurityPatterns:
    """Test suite for Solidity security patterns."""

    def test_reentrancy_patterns_exist(self):
        """Test that reentrancy patterns are defined."""
        patterns = SoliditySecurityPatterns.REENTRANCY_PATTERNS

        assert "classic_reentrancy" in patterns
        assert "read_only_reentrancy" in patterns
        assert "cei_violation" in patterns

        classic = patterns["classic_reentrancy"]
        assert classic.severity == "critical"
        assert classic.pattern_type == VulnerabilityPattern.CLASSIC_REENTRANCY
        assert len(classic.detection_heuristics) > 0
        assert len(classic.mitigation_code) > 0

    def test_flash_loan_patterns_exist(self):
        """Test that flash loan patterns are defined."""
        patterns = SoliditySecurityPatterns.FLASH_LOAN_PATTERNS

        assert "flash_loan_price_manipulation" in patterns
        assert "same_block_borrow_repay" in patterns

        flash_loan = patterns["flash_loan_price_manipulation"]
        assert flash_loan.severity == "critical"
        assert "flash loan" in flash_loan.detection_heuristics
        assert "TWAP" in flash_loan.mitigation_code

    def test_access_control_patterns_exist(self):
        """Test that access control patterns are defined."""
        patterns = SoliditySecurityPatterns.ACCESS_CONTROL_PATTERNS

        assert "role_based_access" in patterns

        role_based = patterns["role_based_access"]
        assert role_based.severity == "high"
        assert "AccessControl" in role_based.mitigation_code
        assert "ADMIN_ROLE" in role_based.mitigation_code

    def test_front_running_patterns_exist(self):
        """Test that front-running patterns are defined."""
        patterns = SoliditySecurityPatterns.FRONT_RUNNING_PATTERNS

        assert "commit_reveal" in patterns
        assert "eip712_signature" in patterns

        commit_reveal = patterns["commit_reveal"]
        assert commit_reveal.severity == "medium"
        assert "commit" in commit_reveal.detection_heuristics
        assert "reveal" in commit_reveal.mitigation_code

    def test_oracle_security_patterns_exist(self):
        """Test that oracle security patterns are defined."""
        patterns = SoliditySecurityPatterns.ORACLE_SECURITY_PATTERNS

        assert "chainlink_staleness" in patterns
        assert "multi_oracle_consensus" in patterns
        assert "twap_implementation" in patterns

        staleness = patterns["chainlink_staleness"]
        assert staleness.severity == "high"
        assert "latestrounddata" in staleness.detection_heuristics
        assert "answeredInRound" in staleness.mitigation_code

    def test_get_all_patterns(self):
        """Test that all patterns can be retrieved."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        # Should contain patterns from all categories
        assert len(all_patterns) >= 8
        assert "classic_reentrancy" in all_patterns
        assert "flash_loan_price_manipulation" in all_patterns
        assert "role_based_access" in all_patterns
        assert "commit_reveal" in all_patterns
        assert "chainlink_staleness" in all_patterns

    def test_detect_patterns_reentrancy(self):
        """Test pattern detection for reentrancy vulnerabilities."""
        contract_code = """
        contract Vulnerable {
            function withdraw() external {
                (bool success, ) = msg.sender.call{value: balance}("");
                balance = 0;
            }
        }
        """

        detected = SoliditySecurityPatterns.detect_patterns(contract_code, [])

        # Should detect reentrancy pattern
        pattern_types = [p.pattern_type for p in detected]
        assert VulnerabilityPattern.CLASSIC_REENTRANCY in pattern_types

    def test_detect_patterns_flash_loan(self):
        """Test pattern detection for flash loan vulnerabilities."""
        contract_code = """
        contract FlashLoanVulnerable {
            function flashLoan(uint256 amount) external {
                // Flash loan logic
            }

            function getPrice() public view returns (uint256) {
                return spotPrice;
            }
        }
        """

        detected = SoliditySecurityPatterns.detect_patterns(contract_code, [])

        # Should detect flash loan pattern
        pattern_types = [p.pattern_type for p in detected]
        assert VulnerabilityPattern.FLASH_LOAN_PRICE_MANIPULATION in pattern_types

    def test_detect_patterns_oracle(self):
        """Test pattern detection for oracle vulnerabilities."""
        contract_code = """
        contract OracleDependent {
            function latestRoundData() external view returns (uint256) {
                return oraclePrice;
            }
        }
        """

        detected = SoliditySecurityPatterns.detect_patterns(contract_code, [])

        # Should detect oracle pattern
        pattern_types = [p.pattern_type for p in detected]
        assert VulnerabilityPattern.STALE_PRICE_DATA in pattern_types

    def test_get_mitigation_for_pattern(self):
        """Test getting mitigation code for a specific pattern."""
        mitigation = SoliditySecurityPatterns.get_mitigation_for_pattern(
            VulnerabilityPattern.CLASSIC_REENTRANCY
        )

        assert len(mitigation) > 0
        assert "ReentrancyGuard" in mitigation
        assert "nonReentrant" in mitigation

    def test_read_only_reentrancy_pattern(self):
        """Test read-only reentrancy pattern (2023 attack vector)."""
        patterns = SoliditySecurityPatterns.REENTRANCY_PATTERNS
        read_only = patterns["read_only_reentrancy"]

        assert read_only.severity == "high"
        assert "view function" in read_only.detection_heuristics
        assert "2023" in read_only.description
        assert len(read_only.references) > 0

    def test_cei_violation_pattern(self):
        """Test CEI (Checks-Effects-Interactions) violation pattern."""
        patterns = SoliditySecurityPatterns.REENTRANCY_PATTERNS
        cei = patterns["cei_violation"]

        assert cei.severity == "high"
        assert "Checks-Effects-Interactions" in cei.description
        assert "1. Checks" in cei.mitigation_code
        assert "2. Effects" in cei.mitigation_code
        assert "3. Interactions" in cei.mitigation_code


class TestFormalVerificationPatterns:
    """Test suite for formal verification patterns."""

    def test_generate_natspec_invariants(self):
        """Test NatSpec invariant generation."""
        invariants = [
            "totalSupply == sum(balances)",
            "balance >= 0",
        ]

        natspec = FormalVerificationPatterns.generate_natspec_invariants(
            "transfer", invariants
        )

        assert "@notice transfer" in natspec
        assert "@invariant totalSupply == sum(balances)" in natspec
        assert "@invariant balance >= 0" in natspec
        assert "@dev Ensure all invariants hold" in natspec

    def test_generate_foundry_invariant_test(self):
        """Test Foundry invariant test generation."""
        invariants = [
            "target.totalSupply() > 0",
            "target.balanceOf(user) >= 0",
        ]

        test_code = FormalVerificationPatterns.generate_foundry_invariant_test(
            "MyToken", invariants
        )

        assert "contract MyTokenInvariantTest is Test" in test_code
        assert "function invariant_criticalInvariants()" in test_code
        assert "assertTrue(target.totalSupply() > 0" in test_code
        assert "assertTrue(target.balanceOf(user) >= 0" in test_code

    def test_get_common_invariants_erc20(self):
        """Test common invariants for ERC20 tokens."""
        invariants = FormalVerificationPatterns.get_common_invariants()

        assert "erc20" in invariants
        erc20_invariants = invariants["erc20"]

        assert len(erc20_invariants) >= 3
        assert any("totalSupply" in inv for inv in erc20_invariants)
        assert any("balanceOf" in inv for inv in erc20_invariants)

    def test_get_common_invariants_vault(self):
        """Test common invariants for vault contracts."""
        invariants = FormalVerificationPatterns.get_common_invariants()

        assert "vault" in invariants
        vault_invariants = invariants["vault"]

        assert len(vault_invariants) >= 3
        assert any("totalAssets" in inv for inv in vault_invariants)
        assert any("sharePrice" in inv for inv in vault_invariants)

    def test_get_common_invariants_lending(self):
        """Test common invariants for lending protocols."""
        invariants = FormalVerificationPatterns.get_common_invariants()

        assert "lending" in invariants
        lending_invariants = invariants["lending"]

        assert len(lending_invariants) >= 3
        assert any("totalBorrowed" in inv for inv in lending_invariants)
        assert any("collateral" in inv for inv in lending_invariants)

    def test_get_common_invariants_staking(self):
        """Test common invariants for staking contracts."""
        invariants = FormalVerificationPatterns.get_common_invariants()

        assert "staking" in invariants
        staking_invariants = invariants["staking"]

        assert len(staking_invariants) >= 3
        assert any("totalStaked" in inv for inv in staking_invariants)
        assert any("rewards" in inv for inv in staking_invariants)


class TestSecurityPatternIntegration:
    """Integration tests for security patterns."""

    def test_all_patterns_have_required_fields(self):
        """Test that all patterns have required fields."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        for _key, pattern in all_patterns.items():
            assert isinstance(pattern, SecurityPattern)
            assert pattern.pattern_type is not None
            assert pattern.severity in ["critical", "high", "medium", "low"]
            assert len(pattern.description) > 0
            assert isinstance(pattern.detection_heuristics, list)
            assert isinstance(pattern.references, list)

    def test_all_patterns_have_mitigation_code(self):
        """Test that all patterns have mitigation code."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        for key, pattern in all_patterns.items():
            assert len(pattern.mitigation_code) > 0, f"Pattern {key} missing mitigation code"

    def test_pattern_references_valid(self):
        """Test that pattern references are valid."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        for _key, pattern in all_patterns.items():
            for ref in pattern.references:
                assert isinstance(ref, str)
                assert len(ref) > 0

    def test_detection_heuristics_lowercase(self):
        """Test that detection heuristics are lowercase for matching."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        for key, pattern in all_patterns.items():
            for heuristic in pattern.detection_heuristics:
                assert isinstance(heuristic, str)
                # Heuristics should be lowercase for case-insensitive matching
                assert heuristic == heuristic.lower(), f"Heuristic '{heuristic}' in {key} should be lowercase"

    def test_vulnerability_pattern_enum_coverage(self):
        """Test that VulnerabilityPattern enum covers all pattern types."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        # Get all pattern types from the enum
        enum_values = {p.value for p in VulnerabilityPattern}

        # Check that all patterns in the database are in the enum
        for _key, pattern in all_patterns.items():
            assert pattern.pattern_type.value in enum_values

    def test_mitigation_code_has_solidity_keywords(self):
        """Test that mitigation code contains Solidity keywords."""
        all_patterns = SoliditySecurityPatterns.get_all_patterns()

        solidity_keywords = ["contract", "function", "pragma", "require", "import"]

        for key, pattern in all_patterns.items():
            has_keyword = any(keyword in pattern.mitigation_code for keyword in solidity_keywords)
            assert has_keyword, f"Pattern {key} mitigation code doesn't contain Solidity keywords"
