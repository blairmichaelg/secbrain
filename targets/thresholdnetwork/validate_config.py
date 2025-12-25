#!/usr/bin/env python3
"""
Validation script for Threshold Network target configuration.
Run this to verify everything is set up correctly before running SecBrain.
"""

import sys
from pathlib import Path
import yaml
import json

def validate_config():
    """Validate Threshold Network configuration files."""
    errors = []
    warnings = []
    
    # Base path
    base = Path("/home/runner/work/secbrain/secbrain/targets/thresholdnetwork")
    
    # Check program.json exists and is valid
    program_path = base / "program.json"
    if not program_path.exists():
        errors.append(f"Missing program.json at {program_path}")
    else:
        try:
            with open(program_path) as f:
                program = json.load(f)
            
            # Validate required fields
            required = ["name", "platform", "focus_areas", "rules"]
            for field in required:
                if field not in program:
                    errors.append(f"program.json missing required field: {field}")
            
            # Check focus areas
            if "focus_areas" in program and len(program["focus_areas"]) < 5:
                warnings.append("program.json has fewer than 5 focus areas")
            
            print(f"✓ program.json is valid ({len(program.get('in_scope', []))} in-scope items)")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in program.json: {e}")
    
    # Check scope.yaml exists and is valid
    scope_path = base / "scope.yaml"
    if not scope_path.exists():
        errors.append(f"Missing scope.yaml at {scope_path}")
    else:
        try:
            with open(scope_path) as f:
                scope = yaml.safe_load(f)
            
            # Validate contracts
            if "contracts" not in scope:
                errors.append("scope.yaml missing 'contracts' section")
            else:
                contracts = scope["contracts"]
                print(f"✓ scope.yaml is valid ({len(contracts)} contracts configured)")
                
                # Check each contract has required fields
                for i, contract in enumerate(contracts):
                    required_fields = ["name", "address", "chain_id", "foundry_profile"]
                    for field in required_fields:
                        if field not in contract:
                            errors.append(f"Contract {i} missing field: {field}")
            
            # Check foundry_root
            if "foundry_root" in scope:
                foundry_root = Path(scope["foundry_root"])
                if not foundry_root.exists():
                    warnings.append(f"Foundry root directory not found: {foundry_root}")
                else:
                    print(f"✓ Foundry root exists: {foundry_root}")
            
            # Check RPC URLs
            if "rpc_urls" not in scope or len(scope.get("rpc_urls", [])) == 0:
                errors.append("scope.yaml missing RPC URLs")
            else:
                print(f"✓ RPC URLs configured ({len(scope['rpc_urls'])} endpoints)")
            
            # Check profit tokens
            if "profit_tokens" not in scope or len(scope.get("profit_tokens", [])) == 0:
                warnings.append("scope.yaml missing profit_tokens configuration")
            else:
                print(f"✓ Profit tokens configured ({len(scope['profit_tokens'])} tokens)")
                
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML in scope.yaml: {e}")
    
    # Check instascope directory
    instascope_path = base / "instascope"
    if not instascope_path.exists():
        errors.append(f"Missing instascope directory at {instascope_path}")
    else:
        # Check for foundry.toml
        foundry_toml = instascope_path / "foundry.toml"
        if not foundry_toml.exists():
            errors.append(f"Missing foundry.toml in instascope directory")
        else:
            print(f"✓ foundry.toml exists")
        
        # Check for build.sh
        build_sh = instascope_path / "build.sh"
        if not build_sh.exists():
            warnings.append(f"Missing build.sh script")
        else:
            print(f"✓ build.sh exists")
        
        # Check src directory
        src_path = instascope_path / "src"
        if not src_path.exists():
            errors.append(f"Missing src directory in instascope")
        else:
            # Count contract directories
            contract_dirs = [d for d in src_path.iterdir() if d.is_dir()]
            print(f"✓ Found {len(contract_dirs)} contract source directories")
    
    # Check for README
    readme_path = base / "README.md"
    if not readme_path.exists():
        warnings.append(f"Missing README.md")
    else:
        print(f"✓ README.md exists")
    
    # Print results
    print("\n" + "="*60)
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ All checks passed! Configuration is ready.")
    elif not errors:
        print("\n✅ No errors found. Configuration is usable.")
    else:
        print("\n❌ Configuration has errors. Please fix before running.")
        return 1
    
    print("\n" + "="*60)
    print("\nNext steps:")
    print("1. Run a dry-run test:")
    print("   secbrain run \\")
    print("     --scope targets/thresholdnetwork/scope.yaml \\")
    print("     --program targets/thresholdnetwork/program.json \\")
    print("     --workspace targets/thresholdnetwork/workspace \\")
    print("     --dry-run")
    print("\n2. If dry-run succeeds, run full analysis")
    print("\n3. Generate insights report")
    
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(validate_config())
