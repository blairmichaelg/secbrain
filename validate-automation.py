#!/usr/bin/env python3
"""
Validation script for automated agent suite configuration.
Checks all workflow files, configuration files, and ensures everything is set up correctly.

Requirements: pyyaml
Install with: pip install pyyaml
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml is not installed.")
    print("Please install it with: pip install pyyaml")
    sys.exit(1)


def validate_yaml_file(file_path: Path) -> Tuple[bool, str]:
    """Validate YAML file syntax."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True, f"✅ {file_path.name}"
    except Exception as e:
        return False, f"❌ {file_path.name}: {str(e)}"


def validate_json_file(file_path: Path) -> Tuple[bool, str]:
    """Validate JSON file syntax."""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True, f"✅ {file_path.name}"
    except Exception as e:
        return False, f"❌ {file_path.name}: {str(e)}"


def check_workflow_permissions(workflow_path: Path) -> Tuple[bool, str]:
    """Check if workflow has appropriate permissions."""
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        if 'permissions' not in workflow:
            return False, f"⚠️  {workflow_path.name}: No permissions defined"
        
        return True, f"✅ {workflow_path.name}: Permissions OK"
    except Exception as e:
        return False, f"❌ {workflow_path.name}: {str(e)}"


def main():
    """Main validation function."""
    repo_root = Path(__file__).parent
    errors: List[str] = []
    warnings: List[str] = []
    
    print("🔍 Validating Automated Agent Suite Configuration\n")
    
    # Validate workflow files
    print("📋 Validating GitHub Workflows...")
    workflow_dir = repo_root / ".github" / "workflows"
    workflows = [
        "security-scan.yml",
        "solidity-security.yml",
        "dependency-audit.yml",
        "code-quality.yml",
        "ai-engineer.yml",
        "comprehensive-audit.yml"
    ]
    
    for workflow in workflows:
        workflow_path = workflow_dir / workflow
        if not workflow_path.exists():
            errors.append(f"❌ Missing workflow: {workflow}")
            continue
        
        valid, msg = validate_yaml_file(workflow_path)
        print(f"  {msg}")
        if not valid:
            errors.append(msg)
        
        # Check permissions
        valid, msg = check_workflow_permissions(workflow_path)
        if not valid and "⚠️" in msg:
            warnings.append(msg)
        elif not valid:
            errors.append(msg)
    
    # Validate configuration files
    print("\n🔧 Validating Configuration Files...")
    
    yaml_configs = [
        ".pre-commit-config.yaml",
        ".github/dependabot.yml"
    ]
    
    for config in yaml_configs:
        config_path = repo_root / config
        if not config_path.exists():
            errors.append(f"❌ Missing config: {config}")
            continue
        
        valid, msg = validate_yaml_file(config_path)
        print(f"  {msg}")
        if not valid:
            errors.append(msg)
    
    json_configs = [
        ".solhint.json",
        "slither.config.json",
        ".secrets.baseline"
    ]
    
    for config in json_configs:
        config_path = repo_root / config
        if not config_path.exists():
            errors.append(f"❌ Missing config: {config}")
            continue
        
        valid, msg = validate_json_file(config_path)
        print(f"  {msg}")
        if not valid:
            errors.append(msg)
    
    # Check foundry.toml exists
    foundry_config = repo_root / "foundry.toml"
    if foundry_config.exists():
        print("  ✅ foundry.toml")
    else:
        warnings.append("⚠️  foundry.toml not found (optional)")
    
    # Check documentation
    print("\n📚 Checking Documentation...")
    docs = [
        "secbrain/docs/automated-agents.md",
        "BADGES.md",
        "AUTOMATION-QUICK-REF.md"
    ]
    
    for doc in docs:
        doc_path = repo_root / doc
        if doc_path.exists():
            print(f"  ✅ {doc}")
        else:
            warnings.append(f"⚠️  Missing documentation: {doc}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 Validation Summary")
    print("="*60)
    
    if not errors and not warnings:
        print("✅ All validations passed! Automated agent suite is ready.")
        return 0
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
        print("\n💡 Fix errors before deploying automated agent suite.")
        return 1
    
    print("\n✅ Validation complete with warnings. Review and deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
