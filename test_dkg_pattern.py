#!/usr/bin/env python3
"""Quick test to verify DKG threshold-raising pattern integration."""

import sys
import os

# Add the secbrain directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secbrain'))

def test_threshold_network_patterns():
    """Test that DKG_THRESHOLD_RAISING pattern is properly defined."""
    from secbrain.agents.threshold_network_patterns import (
        ThresholdNetworkPatterns,
        ThresholdVulnerabilityPattern,
        ImmunefiSeverity
    )
    
    print("Testing Threshold Network Patterns...")
    
    # Test 1: Enum exists
    assert hasattr(ThresholdVulnerabilityPattern, 'DKG_THRESHOLD_RAISING'), \
        "DKG_THRESHOLD_RAISING not found in enum"
    print("✓ DKG_THRESHOLD_RAISING enum exists")
    
    # Test 2: Pattern in all patterns
    all_patterns = ThresholdNetworkPatterns.get_all_patterns()
    assert 'dkg_threshold_raising' in all_patterns, \
        "dkg_threshold_raising not in all patterns"
    print(f"✓ Pattern found in all_patterns (total: {len(all_patterns)})")
    
    # Test 3: Pattern details
    dkg_pattern = all_patterns['dkg_threshold_raising']
    assert dkg_pattern.severity == ImmunefiSeverity.CRITICAL, \
        "Pattern should be CRITICAL severity"
    assert dkg_pattern.max_bounty_usd == 500_000, \
        "Max bounty should be $500,000"
    print(f"✓ Pattern severity: {dkg_pattern.severity.value}")
    print(f"✓ Pattern bounty: ${dkg_pattern.max_bounty_usd:,}")
    
    # Test 4: Detection heuristics
    assert len(dkg_pattern.detection_heuristics) > 0, \
        "Pattern should have detection heuristics"
    print(f"✓ Detection heuristics: {len(dkg_pattern.detection_heuristics)}")
    
    # Test 5: In critical patterns
    critical_patterns = ThresholdNetworkPatterns.get_critical_patterns()
    critical_keys = [p.pattern_type.value for p in critical_patterns]
    assert 'dkg_threshold_raising' in critical_keys, \
        "dkg_threshold_raising should be in critical patterns"
    print(f"✓ Pattern in critical patterns (total: {len(critical_patterns)})")
    
    # Test 6: Affected contracts
    assert 'WalletRegistry' in dkg_pattern.affected_contracts, \
        "WalletRegistry should be in affected contracts"
    print(f"✓ Affected contracts: {', '.join(dkg_pattern.affected_contracts)}")
    
    print("\n✓ All Threshold Network Patterns tests passed!")
    return True


def test_immunefi_intelligence():
    """Test that DKG pattern is in Immunefi intelligence."""
    from secbrain.agents.immunefi_intelligence import ImmunefiIntelligence
    
    print("\nTesting Immunefi Intelligence...")
    
    # Test 1: Pattern exists
    assert 'dkg_threshold_raising' in ImmunefiIntelligence.COMMON_VULNERABILITIES, \
        "dkg_threshold_raising not in COMMON_VULNERABILITIES"
    print("✓ DKG pattern in COMMON_VULNERABILITIES")
    
    # Test 2: Pattern details
    dkg_vuln = ImmunefiIntelligence.COMMON_VULNERABILITIES['dkg_threshold_raising']
    assert dkg_vuln.severity == 'critical', \
        "Vulnerability should be critical"
    assert dkg_vuln.typical_bounty_range == (100_000, 500_000), \
        "Bounty range should be $100K-$500K"
    print(f"✓ Severity: {dkg_vuln.severity}")
    print(f"✓ Bounty range: ${dkg_vuln.typical_bounty_range[0]:,} - ${dkg_vuln.typical_bounty_range[1]:,}")
    
    # Test 3: In threshold_network protocol mapping
    threshold_patterns = ImmunefiIntelligence.get_vulnerability_patterns_for_protocol('threshold_network')
    pattern_names = [p.name for p in threshold_patterns]
    assert 'DKG Threshold-Raising Vulnerability' in pattern_names, \
        "DKG pattern should be in threshold_network mapping"
    print(f"✓ Pattern in threshold_network mapping (total: {len(threshold_patterns)})")
    
    # Test 4: Detection techniques
    assert len(dkg_vuln.detection_techniques) > 0, \
        "Should have detection techniques"
    print(f"✓ Detection techniques: {len(dkg_vuln.detection_techniques)}")
    
    # Test 5: Recent examples
    assert len(dkg_vuln.recent_examples) > 0, \
        "Should have recent examples"
    assert any('FROST' in ex or 'Zcash' in ex for ex in dkg_vuln.recent_examples), \
        "Should reference FROST vulnerability"
    print(f"✓ Recent examples: {len(dkg_vuln.recent_examples)}")
    
    print("\n✓ All Immunefi Intelligence tests passed!")
    return True


def test_vuln_hypothesis_agent():
    """Test that DKG pattern is in vulnerability hypothesis agent."""
    import re
    
    print("\nTesting Vulnerability Hypothesis Agent...")
    
    # Read the file with proper path
    file_path = os.path.join(os.path.dirname(__file__), 'secbrain/secbrain/agents/vuln_hypothesis_agent.py')
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Test 1: Pattern in threshold_network list
    threshold_section = re.search(r'"threshold_network":\s*\[(.*?)\]', content, re.DOTALL)
    assert threshold_section, "threshold_network section not found"
    assert 'dkg_threshold_raising' in threshold_section.group(0), \
        "dkg_threshold_raising not in threshold_network vulnerability list"
    print("✓ Pattern in threshold_network vulnerability list")
    
    # Test 2: Pattern appears multiple times
    count = content.count('dkg_threshold_raising')
    assert count >= 2, \
        f"Pattern should appear at least 2 times, found {count}"
    print(f"✓ Pattern appears {count} times in file")
    
    print("\n✓ All Vulnerability Hypothesis Agent tests passed!")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("DKG Threshold-Raising Vulnerability Pattern Integration Test")
    print("=" * 60)
    
    try:
        test_threshold_network_patterns()
        test_immunefi_intelligence()
        test_vuln_hypothesis_agent()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nDKG threshold-raising vulnerability pattern successfully integrated:")
        print("  - Added to ThresholdVulnerabilityPattern enum")
        print("  - Added to threshold_network_patterns.py (18 total patterns)")
        print("  - Added to immunefi_intelligence.py (12 vulnerability classes)")
        print("  - Added to vuln_hypothesis_agent.py")
        print("  - CRITICAL severity: $100K-$500K bounty potential")
        print("  - References: FROST, Trail of Bits, Safeheron (Jan 2024)")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
