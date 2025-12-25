#!/usr/bin/env python3
"""Test script to validate eth-hash backend installation.

This script tests that the eth-hash dependency is properly installed with
a hashing backend (pycryptodome), which is required for hypothesis generation.
"""

import sys


def test_eth_hash_backend():
    """Test that eth-hash has a working backend installed."""
    print("Testing eth-hash backend installation...")
    
    try:
        from eth_utils import is_address, to_checksum_address
        print("✅ eth-utils imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import eth-utils: {e}")
        return False
    
    # Test with a known Ethereum address (Origin Protocol Proxy contract)
    test_address = "0x85b78aca6deae198fbf201c82daf6ca21942acc6"
    expected_checksum = "0x85B78AcA6Deae198fBF201c82DAF6Ca21942acc6"
    
    try:
        # Test is_address
        if not is_address(test_address):
            print(f"❌ is_address({test_address}) returned False")
            return False
        print(f"✅ is_address validation works")
        
        # Test to_checksum_address
        checksum = to_checksum_address(test_address)
        if checksum != expected_checksum:
            print(f"❌ Checksum mismatch: got {checksum}, expected {expected_checksum}")
            return False
        print(f"✅ to_checksum_address works: {checksum}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print(f"   This likely means eth-hash backend is not installed")
        print(f"   Install with: pip install 'eth-hash[pycryptodome]'")
        return False
    
    print("\n✅ All tests passed! eth-hash backend is working correctly.")
    return True


def main():
    """Main entry point."""
    success = test_eth_hash_backend()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
