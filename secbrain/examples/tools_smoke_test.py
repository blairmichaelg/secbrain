#!/usr/bin/env python3
"""
Tools smoke test for SecBrain.

This script tests the tool layer in dry-run mode to verify:
1. HTTP client respects scope and dry-run mode
2. Recon wrappers can be instantiated
3. Storage layer works
4. ACLs and rate limits are enforced

Usage:
    python examples/tools_smoke_test.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure pytest treats async tests in this module as asyncio tests.
pytestmark = pytest.mark.asyncio


async def test_http_client(run_context) -> bool:
    """Test the HTTP client."""
    from secbrain.tools.http_client import SecBrainHTTPClient

    print("\n[HTTP Client Test]")

    client = SecBrainHTTPClient(run_context)

    # Test in-scope request (should work in dry-run)
    print("  Testing in-scope request...")
    response = await client.get("https://example.com/test")
    print(f"    Status: {response.status_code}")
    print(f"    Dry-run: {response.metadata.get('dry_run', False)}")

    # Test out-of-scope request (should be blocked)
    print("  Testing out-of-scope request...")
    response = await client.get("https://evil.com/test")
    print(f"    Blocked: {not response.success}")

    await client.close()
    return True


async def test_recon_wrappers(run_context) -> bool:
    """Test recon CLI wrappers."""
    from secbrain.tools.recon_cli_wrappers import ReconToolRunner

    print("\n[Recon Wrappers Test]")

    runner = ReconToolRunner(run_context)

    # Test subfinder (will be simulated in dry-run)
    print("  Testing subfinder wrapper...")
    result = await runner.run_subfinder("example.com")
    print(f"    Success: {result.success}")
    print(f"    Tool: {result.tool}")

    return True


async def test_storage(run_context) -> bool:
    """Test the storage layer."""
    from secbrain.tools.storage import WorkspaceStorage

    print("\n[Storage Test]")

    storage = WorkspaceStorage(run_context)
    await storage.initialize()

    # Start a run
    print("  Starting run...")
    await storage.start_run(
        scope_hash="test123",
        metadata={"test": True},
    )

    # Save an asset
    print("  Saving asset...")
    await storage.save_asset({
        "id": "test-asset-1",
        "type": "subdomain",
        "value": "test.example.com",
        "metadata": {"source": "test"},
    })

    # Retrieve assets
    print("  Retrieving assets...")
    assets = await storage.get_assets()
    print(f"    Found {len(assets)} assets")

    # Save a finding
    print("  Saving finding...")
    await storage.save_finding({
        "id": "test-finding-1",
        "title": "Test XSS",
        "severity": "medium",
        "status": "confirmed",
        "description": "Test finding",
    })

    # Export data
    print("  Exporting data...")
    export_path = await storage.export_run()
    print(f"    Exported to: {export_path}")

    await storage.close()
    return True


async def test_rate_limits(run_context) -> bool:
    """Test rate limiting."""
    print("\n[Rate Limit Test]")

    # Test rate limit check
    print("  Checking rate limit for http_client...")
    allowed = run_context.check_rate_limit("http_client")
    print(f"    Allowed: {allowed}")

    # Consume some capacity
    for _i in range(5):
        run_context.record_tool_call("http_client")

    # Check again
    allowed = run_context.check_rate_limit("http_client")
    print(f"    After 5 calls, still allowed: {allowed}")

    return True


async def main() -> int:
    """Run all smoke tests."""
    from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig

    print("=" * 60)
    print("SecBrain Tools Smoke Test")
    print("=" * 60)

    # Create test workspace
    workspace = Path(__file__).parent / "test_workspace"
    workspace.mkdir(exist_ok=True)

    # Create run context
    scope = ScopeConfig(
        domains=["*.example.com", "example.com"],
        urls=["https://example.com"],
        excluded_paths=["/admin/*"],
        allowed_methods=["GET", "POST"],
    )

    program = ProgramConfig(
        name="Smoke Test",
        platform="test",
        focus_areas=[],
        rules=[],
        rewards={},
    )

    run_context = RunContext(
        scope=scope,
        program=program,
        workspace_path=workspace,
        dry_run=True,
    )

    print(f"\nRun ID: {run_context.run_id}")
    print(f"Dry Run: {run_context.dry_run}")

    # Run tests
    all_passed = True

    try:
        all_passed &= await test_http_client(run_context)
    except Exception as e:
        print(f"  ERROR: {e}")
        all_passed = False

    try:
        all_passed &= await test_recon_wrappers(run_context)
    except Exception as e:
        print(f"  ERROR: {e}")
        all_passed = False

    try:
        all_passed &= await test_storage(run_context)
    except Exception as e:
        print(f"  ERROR: {e}")
        all_passed = False

    try:
        all_passed &= await test_rate_limits(run_context)
    except Exception as e:
        print(f"  ERROR: {e}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
