#!/usr/bin/env python3
"""Parse foundry.toml to extract contract profiles for SecBrain scope configuration."""

import re
from pathlib import Path

import toml


def extract_address_from_profile_name(profile_name: str) -> str:
    """Extract address from profile name like 'contract_MelonPort_cfe2'."""
    # Pattern: contract_<Name>_<address_suffix>
    match = re.match(r'contract_[^_]+_(.+)', profile_name)
    if match:
        # Pad to 40 characters (20 bytes) for full address
        suffix = match.group(1)
        if len(suffix) < 40:
            # Pad with leading zeros if needed
            suffix = suffix.rjust(40, '0')
        return "0x" + suffix
    return ""

def parse_foundry_profiles(toml_path: Path) -> list[dict[str, str]]:
    """Parse foundry.toml and extract contract profiles with addresses."""
    contracts = []

    with open(toml_path) as f:
        data = toml.load(f)

    profiles = data.get('profile', {})

    for profile_name, profile_config in profiles.items():
        if profile_name.startswith('contract_'):
            address = extract_address_from_profile_name(profile_name)
            if not address:
                continue

            # Extract contract name from profile name
            name_parts = profile_name.split('_')
            contract_name = '_'.join(name_parts[1:-1]) if len(name_parts) >= 3 else profile_name

            # Get source path from profile config
            src = profile_config.get('src', '')
            if src:
                # Convert relative path to absolute
                source_path = toml_path.parent / src
            else:
                source_path = None

            contracts.append({
                'name': contract_name,
                'address': address,
                'foundry_profile': profile_name,
                'source_path': str(source_path) if source_path else None,
                'chain_id': 1,  # Default to mainnet
                'verified': True
            })

    return contracts

def generate_scope_yaml(contracts: list[dict[str, str]], output_path: Path) -> None:
    """Generate enzyme_scope.yaml from contract list."""
    scope_data = {
        'contracts': contracts,
        'domains': [],
        'ips': [],
        'urls': [],
        'excluded_paths': [],
        'allowed_methods': ['GET', 'POST', 'PUT', 'HEAD', 'OPTIONS'],
        'max_depth': 3,
        'notes': 'Enzyme Finance smart contracts - local Instascope bundle',
        'foundry_root': str(Path.cwd()),
        'max_requests_per_second': 10,
        'respect_robots_txt': True
    }

    import yaml
    with open(output_path, 'w') as f:
        yaml.dump(scope_data, f, default_flow_style=False, sort_keys=False)


def main():
    """Main function to parse foundry.toml and generate scope configuration."""
    root_dir = Path(__file__).parent.parent.parent
    toml_path = root_dir / 'foundry.toml'
    output_path = root_dir / 'secbrain' / 'examples' / 'enzyme_scope.yaml'

    if not toml_path.exists():
        return

    contracts = parse_foundry_profiles(toml_path)

    # Save contracts list for reference
    contracts_path = root_dir / 'secbrain' / 'examples' / 'enzyme_contracts.json'
    import json
    with open(contracts_path, 'w') as f:
        json.dump(contracts, f, indent=2)

    generate_scope_yaml(contracts, output_path)

if __name__ == '__main__':
    main()
