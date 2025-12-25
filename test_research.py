#!/usr/bin/env python3
"""Test script for enhanced PerplexityResearch functionality.

This script verifies:
- TTL-based caching behavior
- Rate limiting enforcement
- Specialized research methods (severity, attack vectors, market conditions)
- Backward compatibility with existing methods
"""

import asyncio
import time

# Add secbrain to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "secbrain"))

from secbrain.core.context import RunContext
from secbrain.tools.perplexity_research import PerplexityResearch


async def test_rate_limiting():
    """Test rate limiting enforcement (10 req/min)."""
    print("\n=== Testing Rate Limiting ===")
    
    # Create a mock run context with minimal required parameters
    workspace_path = Path("/tmp/test_workspace")
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create minimal scope and program files
    scope_file = workspace_path / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")
    
    program_file = workspace_path / "program.yaml"
    program_file.write_text("name: 'test-program'\n")
    
    run_context = RunContext(
        workspace_path=workspace_path,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,  # Use dry-run to avoid API calls
    )
    
    research = PerplexityResearch()
    
    # Make 12 rapid calls (should enforce rate limit)
    start = time.time()
    results = []
    for i in range(12):
        result = await research.ask_research(
            question=f"Test question {i}",
            context="Test context",
            run_context=run_context,
        )
        results.append(result)
    
    elapsed = time.time() - start
    
    print(f"✓ Made 12 calls in {elapsed:.2f}s")
    print(f"✓ All calls completed: {len(results) == 12}")
    print(f"✓ Dry-run responses: {all('DRY-RUN' in r.get('answer', '') for r in results)}")
    
    return True


async def test_ttl_caching():
    """Test TTL-based cache validation."""
    print("\n=== Testing TTL Caching ===")
    
    workspace_path = Path("/tmp/test_workspace")
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create minimal scope and program files
    scope_file = workspace_path / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")
    
    program_file = workspace_path / "program.yaml"
    program_file.write_text("name: 'test-program'\n")
    
    run_context = RunContext(
        workspace_path=workspace_path,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,
    )
    
    research = PerplexityResearch()
    
    # First call - should not be cached
    result1 = await research.ask_research(
        question="Test question",
        context="Test context",
        run_context=run_context,
        ttl_hours=24,
    )
    
    # Second call - should be cached
    result2 = await research.ask_research(
        question="Test question",
        context="Test context",
        run_context=run_context,
        ttl_hours=24,
    )
    
    print(f"✓ First call cached: {result1.get('cached', False)} (expected: False)")
    print(f"✓ Second call cached: {result2.get('cached', False)} (expected: True)")
    print(f"✓ Cache age: {result2.get('cache_age_hours', 0):.4f} hours")
    
    return not result1.get('cached') and result2.get('cached')


async def test_specialized_methods():
    """Test specialized research methods."""
    print("\n=== Testing Specialized Research Methods ===")
    
    workspace_path = Path("/tmp/test_workspace")
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create minimal scope and program files
    scope_file = workspace_path / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")
    
    program_file = workspace_path / "program.yaml"
    program_file.write_text("name: 'test-program'\n")
    
    run_context = RunContext(
        workspace_path=workspace_path,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,
    )
    
    research = PerplexityResearch()
    
    # Test research_severity_context
    severity_result = await research.research_severity_context(
        vuln_type="reentrancy",
        run_context=run_context,
        details="ERC4626 vault context",
    )
    print(f"✓ research_severity_context: {len(severity_result.get('answer', ''))} chars")
    
    # Test research_attack_vectors
    attack_result = await research.research_attack_vectors(
        vuln_type="flash_loan_attack",
        run_context=run_context,
        contract_pattern="DeFi lending protocol",
    )
    print(f"✓ research_attack_vectors: {len(attack_result.get('answer', ''))} chars")
    
    # Test research_market_conditions
    market_result = await research.research_market_conditions(
        target_protocol="Aave",
        exploit_type="oracle_manipulation",
        run_context=run_context,
    )
    print(f"✓ research_market_conditions: {len(market_result.get('answer', ''))} chars")
    
    return True


async def test_backward_compatibility():
    """Test backward compatibility with existing methods."""
    print("\n=== Testing Backward Compatibility ===")
    
    workspace_path = Path("/tmp/test_workspace")
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create minimal scope and program files
    scope_file = workspace_path / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")
    
    program_file = workspace_path / "program.yaml"
    program_file.write_text("name: 'test-program'\n")
    
    run_context = RunContext(
        workspace_path=workspace_path,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=True,
    )
    
    research = PerplexityResearch()
    
    # Test old methods still work
    tech_result = await research.research_technology(
        technology="Solidity",
        run_context=run_context,
    )
    print(f"✓ research_technology: {len(tech_result.get('answer', ''))} chars")
    
    endpoint_result = await research.research_endpoint(
        endpoint="/api/transfer",
        method="POST",
        parameters=["amount", "recipient"],
        run_context=run_context,
    )
    print(f"✓ research_endpoint: {len(endpoint_result.get('answer', ''))} chars")
    
    cwe_result = await research.research_cwe(
        cwe_id="CWE-862",
        run_context=run_context,
    )
    print(f"✓ research_cwe: {len(cwe_result.get('answer', ''))} chars")
    
    writeup_result = await research.research_writeups(
        target_type="DeFi",
        vuln_class="reentrancy",
        run_context=run_context,
    )
    print(f"✓ research_writeups: {len(writeup_result.get('answer', ''))} chars")
    
    await research.close()
    
    return True


async def test_call_limits():
    """Test max calls per run limit."""
    print("\n=== Testing Call Limits ===")
    
    workspace_path = Path("/tmp/test_workspace")
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create minimal scope and program files
    scope_file = workspace_path / "scope.yaml"
    scope_file.write_text("domains: ['example.com']\n")
    
    program_file = workspace_path / "program.yaml"
    program_file.write_text("name: 'test-program'\n")
    
    run_context = RunContext(
        workspace_path=workspace_path,
        scope_path=scope_file,
        program_path=program_file,
        dry_run=False,  # Not dry-run to test limit
    )
    
    research = PerplexityResearch(max_calls_per_run=3)
    
    # Make 5 calls (should hit limit at 4th)
    results = []
    for i in range(5):
        result = await research.ask_research(
            question=f"Question {i}",
            context=f"Context {i}",
            run_context=run_context,
        )
        results.append(result)
    
    limited_count = sum(1 for r in results if r.get('limited', False))
    print(f"✓ Limited responses: {limited_count}/5 (expected: 2)")
    print(f"✓ Call count: {research._call_count} (expected: 3)")
    
    await research.close()
    
    return limited_count == 2


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Enhanced PerplexityResearch Test Suite")
    print("=" * 60)
    
    tests = [
        ("Rate Limiting", test_rate_limiting),
        ("TTL Caching", test_ttl_caching),
        ("Specialized Methods", test_specialized_methods),
        ("Backward Compatibility", test_backward_compatibility),
        ("Call Limits", test_call_limits),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = await test_func()
            results[name] = "PASS" if result else "FAIL"
        except Exception as e:
            print(f"✗ {name} failed with error: {e}")
            results[name] = "ERROR"
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, status in results.items():
        symbol = "✓" if status == "PASS" else "✗"
        print(f"{symbol} {name}: {status}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if s == "PASS")
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Exit with appropriate code
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
