"""Tests for SOTA vulnerability coverage functionality."""

import json
from pathlib import Path

import pytest
import yaml

# Import any existing models that might be relevant

# Get the directory containing this test file
TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"


def test_sota_scope_loading():
    """Test that the SOTA scope file can be loaded and parsed."""
    scope_path = FIXTURES_DIR / "sota_scope.yaml"
    assert scope_path.exists(), f"Scope file not found at {scope_path}"

    # Load and parse the scope file
    with scope_path.open(encoding='utf-8') as f:
        scope_data = yaml.safe_load(f)

    # Basic validation of required fields
    assert isinstance(scope_data, dict), "Scope file should be a YAML dictionary"
    assert "targets" in scope_data, "Scope file missing 'targets' section"
    assert "test_config" in scope_data, "Scope file missing 'test_config' section"
    assert "vulnerability_classes" in scope_data, "Scope file missing 'vulnerability_classes' section"

    # Validate targets
    assert isinstance(scope_data["targets"], list), "Targets should be a list"
    for target in scope_data["targets"]:
        assert "name" in target, "Target missing 'name' field"
        assert "type" in target, f"Target {target.get('name')} missing 'type' field"

    # Validate test config
    test_config = scope_data["test_config"]
    assert isinstance(test_config, dict), "test_config should be a dictionary"
    assert "max_concurrent_requests" in test_config, "test_config missing 'max_concurrent_requests'"
    assert "request_timeout" in test_config, "test_config missing 'request_timeout'"

    # Validate vulnerability classes
    assert isinstance(scope_data["vulnerability_classes"], list), "vulnerability_classes should be a list"


def test_sota_program_loading():
    """Test that the SOTA program file can be loaded and parsed."""
    program_path = FIXTURES_DIR / "sota_program.json"
    assert program_path.exists(), f"Program file not found at {program_path}"

    # Load and parse the program file
    with program_path.open(encoding='utf-8') as f:
        program_data = json.load(f)

    # Basic validation of required fields
    assert isinstance(program_data, dict), "Program file should be a JSON object"
    assert "phases" in program_data, "Program file missing 'phases' section"
    assert "tools_config" in program_data, "Program file missing 'tools_config' section"
    assert "safety_controls" in program_data, "Program file missing 'safety_controls' section"

    # Validate phases
    assert isinstance(program_data["phases"], list), "Phases should be a list"
    for phase in program_data["phases"]:
        assert "name" in phase, f"Phase missing 'name' field: {phase}"
        assert "description" in phase, f"Phase {phase.get('name')} missing 'description' field"
        assert "enabled" in phase, f"Phase {phase.get('name')} missing 'enabled' field"
        assert "tools" in phase, f"Phase {phase.get('name')} missing 'tools' field"

    # Validate tools config
    assert isinstance(program_data["tools_config"], dict), "tools_config should be a dictionary"

    # Validate safety controls
    safety_controls = program_data["safety_controls"]
    assert isinstance(safety_controls, dict), "safety_controls should be a dictionary"
    assert "max_requests_per_second" in safety_controls, "safety_controls missing 'max_requests_per_second'"
    assert "max_concurrent_requests" in safety_controls, "safety_controls missing 'max_concurrent_requests'"


@pytest.mark.asyncio
async def test_sota_coverage_workflow():
    """Test the SOTA coverage workflow with a mock target."""
    # This is a placeholder for actual workflow testing
    # In a real test, we would mock the target and verify the workflow execution


def test_sota_fixtures_exist():
    """Verify that all required fixture files exist."""
    required_files = [
        FIXTURES_DIR / "sota_scope.yaml",
        FIXTURES_DIR / "sota_program.json",
        FIXTURES_DIR / "README.md"
    ]

    for file_path in required_files:
        assert file_path.exists(), f"Required file not found: {file_path}"
