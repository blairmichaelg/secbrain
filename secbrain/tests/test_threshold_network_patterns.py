"""Unit tests for Threshold Network vulnerability patterns."""

from __future__ import annotations

import pytest

from secbrain.agents.threshold_network_patterns import (
    ImmunefiSeverity,
    ThresholdNetworkPatterns,
    ThresholdSecurityPattern,
    ThresholdVulnerabilityPattern,
)


class TestThresholdNetworkPatterns:
    """Test suite for Threshold Network vulnerability patterns."""

    def test_dkg_threshold_raising_pattern_exists(self):
        """Test that DKG threshold-raising pattern exists in database."""
        all_patterns = ThresholdNetworkPatterns.get_all_patterns()
        assert "dkg_threshold_raising" in all_patterns
        assert isinstance(all_patterns["dkg_threshold_raising"], ThresholdSecurityPattern)

    def test_dkg_pattern_has_critical_severity(self):
        """Test that DKG threshold-raising is classified as CRITICAL."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        assert pattern.severity == ImmunefiSeverity.CRITICAL

    def test_dkg_pattern_max_bounty(self):
        """Test that max bounty is set correctly."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        assert pattern.max_bounty_usd == 1_000_000

    def test_dkg_pattern_detection_heuristics(self):
        """Test that detection heuristics are comprehensive."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        
        # Should have multiple heuristics
        assert len(pattern.detection_heuristics) >= 5
        
        # Should include key terms
        heuristics = [h.lower() for h in pattern.detection_heuristics]
        assert any("submitdkgresult" in h for h in heuristics)
        assert any("groupcommitment" in h for h in heuristics)
        assert any("polynomial" in h for h in heuristics)

    def test_dkg_pattern_exploitation_steps(self):
        """Test that exploitation steps are defined."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        
        # Should have multiple steps
        assert len(pattern.exploitation_steps) >= 5
        
        # Steps should be descriptive
        for step in pattern.exploitation_steps:
            assert len(step) > 20  # Each step should be reasonably detailed

    def test_dkg_pattern_mitigation_strategies(self):
        """Test that mitigation strategies are defined."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        
        # Should have multiple strategies
        assert len(pattern.mitigation_strategies) >= 5
        
        # Should include the critical polynomial check
        mitigations = " ".join(pattern.mitigation_strategies).lower()
        assert "groupcommitment.length" in mitigations or "polynomial degree" in mitigations

    def test_dkg_pattern_affected_contracts(self):
        """Test that affected contracts are listed."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        
        # Should list key contracts
        assert "WalletRegistry" in pattern.affected_contracts
        assert "EcdsaDkgValidator" in pattern.affected_contracts

    def test_dkg_pattern_references(self):
        """Test that references are provided."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        
        # Should have references
        assert len(pattern.references) >= 3
        
        # Should include FROST or academic reference
        refs = " ".join(pattern.references)
        assert "FROST" in refs or "frost" in refs or "iacr.org" in refs

    def test_dkg_pattern_in_critical_list(self):
        """Test that DKG pattern appears in critical patterns."""
        critical = ThresholdNetworkPatterns.get_critical_patterns()
        dkg_critical = [
            p for p in critical 
            if p.pattern_type == ThresholdVulnerabilityPattern.DKG_THRESHOLD_RAISING
        ]
        assert len(dkg_critical) == 1

    def test_dkg_pattern_for_wallet_registry(self):
        """Test that DKG pattern is associated with WalletRegistry."""
        patterns = ThresholdNetworkPatterns.get_patterns_for_contract("WalletRegistry")
        dkg_patterns = [
            p for p in patterns 
            if p.pattern_type == ThresholdVulnerabilityPattern.DKG_THRESHOLD_RAISING
        ]
        assert len(dkg_patterns) == 1

    def test_all_patterns_have_required_fields(self):
        """Test that all patterns have required fields populated."""
        all_patterns = ThresholdNetworkPatterns.get_all_patterns()
        
        for key, pattern in all_patterns.items():
            # Basic fields
            assert pattern.pattern_type is not None
            assert pattern.severity is not None
            assert pattern.description
            assert pattern.immunefi_category
            assert pattern.max_bounty_usd > 0
            
            # Lists should be populated
            assert len(pattern.detection_heuristics) > 0
            assert len(pattern.exploitation_steps) > 0
            assert len(pattern.mitigation_strategies) > 0
            assert len(pattern.affected_contracts) > 0

    def test_dkg_pattern_immunefi_category(self):
        """Test that Immunefi category is correct."""
        pattern = ThresholdNetworkPatterns.get_all_patterns()["dkg_threshold_raising"]
        
        # Should be protocol insolvency or permanent freezing
        category = pattern.immunefi_category.lower()
        assert "permanent" in category or "insolvency" in category or "freezing" in category

    def test_get_immunefi_severity_guidance(self):
        """Test that Immunefi severity guidance is available."""
        guidance = ThresholdNetworkPatterns.get_immunefi_severity_guidance()
        
        assert "critical" in guidance
        assert "high" in guidance
        assert guidance["critical"]["max_bounty"] == 1_000_000

    def test_pattern_count(self):
        """Test that we have a reasonable number of patterns."""
        all_patterns = ThresholdNetworkPatterns.get_all_patterns()
        
        # Should have multiple patterns (including our new DKG one)
        assert len(all_patterns) >= 10
        
        # DKG threshold-raising should be one of them
        assert "dkg_threshold_raising" in all_patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
