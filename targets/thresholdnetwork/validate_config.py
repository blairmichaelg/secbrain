#!/usr/bin/env python3
"""
Threshold Network configuration validator.

Usage::

    python validate_config.py [--strict] [--json-report]
        [--base BASE_DIR] [--scope scope.yaml] [--program program.json]

The script reuses SecBrain's internal validators (Pydantic schemas) and adds
Threshold-specific hardening checks so you can catch configuration drift
before running `secbrain run`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    REPO_ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    REPO_ROOT = Path(__file__).resolve().parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from secbrain.core.context import ProgramConfig, ScopeConfig
    from secbrain.core.validation import (
        ValidationError,
        validate_program_file,
        validate_scope_file,
    )
except ImportError as exc:  # pragma: no cover - defensive
    raise SystemExit(
        "Unable to import SecBrain modules. Run this script from the project "
        "repository or install SecBrain in editable mode."
    ) from exc


ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
HTTP_SCHEMES = ("http://", "https://")


@dataclass
class CheckMessage:
    level: Literal["ok", "info", "warning", "error"]
    message: str


@dataclass
class ValidationReport:
    quiet: bool = False
    messages: list[CheckMessage] = field(default_factory=list)

    def _log(self, level: Literal["ok", "info", "warning", "error"], message: str) -> None:
        self.messages.append(CheckMessage(level, message))
        if self.quiet:
            return

        prefix = {
            "ok": "[OK]  ",
            "info": "[INFO]",
            "warning": "[WARN]",
            "error": "[ERR] ",
        }[level]
        print(f"{prefix} {message}")

    def ok(self, message: str) -> None:
        self._log("ok", message)

    def info(self, message: str) -> None:
        self._log("info", message)

    def warning(self, message: str) -> None:
        self._log("warning", message)

    def error(self, message: str) -> None:
        self._log("error", message)

    @property
    def errors(self) -> list[str]:
        return [msg.message for msg in self.messages if msg.level == "error"]

    @property
    def warnings(self) -> list[str]:
        return [msg.message for msg in self.messages if msg.level == "warning"]

    def as_dict(self) -> dict[str, object]:
        return {
            "messages": [msg.__dict__ for msg in self.messages],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Threshold Network target configuration.")
    default_base = Path(__file__).resolve().parent
    parser.add_argument(
        "--base",
        type=Path,
        default=default_base,
        help="Base directory for the Threshold Network target (defaults to script directory).",
    )
    parser.add_argument(
        "--scope",
        type=Path,
        help="Optional path to scope.yaml (relative paths are resolved against --base).",
    )
    parser.add_argument(
        "--program",
        type=Path,
        help="Optional path to program.json (relative paths are resolved against --base).",
    )
    parser.add_argument(
        "--instascope",
        type=Path,
        help="Override path to instascope project (defaults to scope.foundry_root or BASE/instascope).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (useful for CI).",
    )
    parser.add_argument(
        "--json-report",
        action="store_true",
        help="Emit a machine-readable JSON report after the summary.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-check logging; only the summary (and JSON if requested) is printed.",
    )
    return parser.parse_args(argv)


def _resolve_path(base: Path, override: Path | None, default_name: str) -> Path:
    if override is None:
        candidate = base / default_name
    else:
        candidate = Path(override)
    candidate = candidate.expanduser()
    if not candidate.is_absolute():
        candidate = (base / candidate).expanduser()
    return candidate.resolve()


def validate_program_section(program_path: Path, report: ValidationReport) -> ProgramConfig | None:
    if not program_path.exists():
        report.error(f"Missing program.json at {program_path}")
        return None
    try:
        program = validate_program_file(program_path)
    except (ValidationError, OSError, json.JSONDecodeError) as exc:
        report.error(f"Program configuration invalid: {exc}")
        return None

    report.ok(
        f"program.json parsed ({len(program.in_scope)} in-scope entries, {len(program.rules)} rules, "
        f"{len(program.focus_areas)} focus areas)",
    )
    if len(program.focus_areas) < 5:
        report.warning("program.json should list at least 5 focus areas for full coverage.")
    if not program.rules:
        report.error("program.json must include at least one rule entry.")
    if not program.platform:
        report.warning("program.json missing platform metadata.")
    if not program.contacts:
        report.warning("program.json missing contacts section.")
    return program


def validate_scope_section(scope_path: Path, report: ValidationReport) -> ScopeConfig | None:
    if not scope_path.exists():
        report.error(f"Missing scope.yaml at {scope_path}")
        return None
    try:
        scope = validate_scope_file(scope_path)
    except (ValidationError, OSError) as exc:
        report.error(f"Scope configuration invalid: {exc}")
        return None

    report.ok(
        f"scope.yaml parsed ({len(scope.contracts)} contracts, "
        f"{len(scope.rpc_urls)} RPC URLs, {len(scope.profit_tokens)} profit tokens)",
    )
    _validate_contracts(scope, report)
    _validate_rpc_urls(scope, report)
    _validate_profit_tokens(scope, report)
    _validate_foundry_config(scope, report)
    _validate_rate_limits(scope, report)
    return scope


def _validate_contracts(scope: ScopeConfig, report: ValidationReport) -> None:
    if not scope.contracts:
        report.warning("No contracts defined in scope.yaml.")
        return

    address_groups: dict[str, set[str]] = {}
    profile_groups: dict[str, set[str]] = {}

    for idx, contract in enumerate(scope.contracts, start=1):
        label = f"Contract #{idx}"
        if not contract.name:
            report.warning(f"{label}: missing name.")
        if not contract.address or not ADDRESS_RE.match(contract.address):
            report.error(f"{label} ({contract.name or 'unnamed'}) has invalid address: {contract.address!r}")
        else:
            address_groups.setdefault(contract.address.lower(), set()).add(contract.address)
        if contract.foundry_profile:
            profile_groups.setdefault(contract.foundry_profile.lower(), set()).add(contract.foundry_profile)
        else:
            report.warning(f"{label} ({contract.name or contract.address}) missing foundry_profile.")
        if contract.chain_id is None:
            report.error(f"{label} ({contract.name or contract.address}) missing chain_id.")

    duplicate_addresses = [
        "/".join(sorted(values)) for values in address_groups.values() if len(values) > 1
    ]
    if duplicate_addresses:
        report.error(f"Duplicate contract addresses detected: {', '.join(duplicate_addresses)}")

    duplicate_profiles = [
        "/".join(sorted(values)) for values in profile_groups.values() if len(values) > 1
    ]
    if duplicate_profiles:
        report.warning(f"Duplicate foundry_profile names detected: {', '.join(duplicate_profiles)}")

    chain_ids = sorted({contract.chain_id for contract in scope.contracts if contract.chain_id is not None})
    if len(chain_ids) > 1:
        report.warning(f"Multiple chain IDs detected across contracts: {chain_ids}")
    elif chain_ids and chain_ids[0] != 1:
        report.warning(f"Expected Ethereum mainnet (chain_id 1) but found {chain_ids[0]}.")
    else:
        report.ok("All contracts target Ethereum mainnet (chain_id 1).")


def _validate_rpc_urls(scope: ScopeConfig, report: ValidationReport) -> None:
    if not scope.rpc_urls:
        report.error("scope.yaml missing rpc_urls entries.")
        return
    invalid = [url for url in scope.rpc_urls if not url.startswith(HTTP_SCHEMES)]
    if invalid:
        report.warning(f"RPC URLs with unexpected scheme detected: {', '.join(invalid)}")
    if len(scope.rpc_urls) < 2:
        report.warning("Configure at least two RPC endpoints for redundancy.")
    duplicates = [url for url, count in Counter(scope.rpc_urls).items() if count > 1]
    if duplicates:
        report.warning(f"Duplicate RPC URLs detected: {', '.join(duplicates)}")
    report.ok(f"RPC URLs configured ({len(scope.rpc_urls)} endpoints).")


def _validate_profit_tokens(scope: ScopeConfig, report: ValidationReport) -> None:
    tokens = scope.profit_tokens
    if not tokens:
        report.warning("scope.yaml missing profit_tokens configuration.")
        return

    symbol_groups: dict[str, set[str]] = {}
    address_groups: dict[str, set[str]] = {}
    for idx, token in enumerate(tokens, start=1):
        symbol = token.get("symbol")
        address = token.get("address")
        decimals = token.get("decimals")
        if not symbol:
            report.error(f"Profit token #{idx} missing symbol.")
        if not address or not ADDRESS_RE.match(address):
            report.error(f"Profit token {symbol or idx} has invalid address: {address!r}")
        else:
            address_groups.setdefault(address.lower(), set()).add(address)
        if decimals is None or not isinstance(decimals, int) or decimals <= 0 or decimals > 36:
            report.error(f"Profit token {symbol or idx} has invalid decimals value: {decimals!r}")
        if symbol:
            symbol_groups.setdefault(symbol.lower(), set()).add(symbol)

    duplicate_symbols = [
        "/".join(sorted(values)) for values in symbol_groups.values() if len(values) > 1
    ]
    duplicate_addresses = [
        "/".join(sorted(values)) for values in address_groups.values() if len(values) > 1
    ]
    if duplicate_symbols:
        report.warning(f"Duplicate profit token symbols detected: {', '.join(duplicate_symbols)}")
    if duplicate_addresses:
        report.warning(f"Duplicate profit token addresses detected: {', '.join(duplicate_addresses)}")

    report.ok(f"Profit tokens configured ({len(tokens)} entries).")


def _validate_foundry_config(scope: ScopeConfig, report: ValidationReport) -> None:
    if scope.foundry_root is None:
        report.warning("scope.yaml missing foundry_root path; required for local Foundry builds.")
        return
    foundry_root = Path(scope.foundry_root)
    if not foundry_root.exists():
        report.error(f"Foundry root directory not found: {foundry_root}")
        return
    report.ok(f"Foundry root exists: {foundry_root}")


def _validate_rate_limits(scope: ScopeConfig, report: ValidationReport) -> None:
    if scope.max_requests_per_second <= 0:
        report.error("max_requests_per_second must be greater than zero.")
    if scope.max_parallel_exploits <= 0:
        report.warning("max_parallel_exploits should be at least 1.")
    if not scope.allowed_methods:
        report.error("allowed_methods list must not be empty.")
    elif "GET" not in scope.allowed_methods:
        report.warning("allowed_methods does not include GET; double-check scope restrictions.")


def validate_instascope(instascope_path: Path, scope: ScopeConfig | None, report: ValidationReport) -> None:
    if not instascope_path.exists():
        report.error(f"Missing instascope directory at {instascope_path}")
        return
    report.ok(f"instascope directory present: {instascope_path}")

    foundry_toml = instascope_path / "foundry.toml"
    if not foundry_toml.exists():
        report.error("Missing foundry.toml in instascope directory.")
    else:
        report.ok("instascope/foundry.toml detected.")

    build_scripts = [instascope_path / "build.sh", instascope_path / "build.ps1"]
    if not any(script.exists() for script in build_scripts):
        report.warning("No build script found (expected build.sh or build.ps1).")
    else:
        report.ok("Build script present for instascope.")

    required_dirs = ["src", "script"]
    for folder in required_dirs:
        path = instascope_path / folder
        if not path.exists():
            report.error(f"Missing instascope/{folder} directory.")
        else:
            if folder == "src":
                contract_dirs = [p for p in path.iterdir() if p.is_dir()]
                report.ok(f"instascope/src contains {len(contract_dirs)} contract directories.")
            else:
                report.ok(f"instascope/{folder} directory ready.")

    if scope and scope.foundry_root:
        declared_root = Path(scope.foundry_root).resolve()
        actual_root = instascope_path.resolve()
        if declared_root != actual_root:
            report.warning(
                f"scope.yaml foundry_root ({declared_root}) does not match --instascope path ({actual_root})."
            )


def validate_workspace(base: Path, report: ValidationReport) -> None:
    workspace = base / "workspace"
    if workspace.exists():
        report.ok(f"Workspace directory present: {workspace}")
    else:
        report.warning(f"Workspace directory missing at {workspace}. Create it before running SecBrain.")

    workspace_archive = base / "workspace-archive"
    if workspace_archive.exists():
        try:
            entry_count = sum(1 for _ in workspace_archive.iterdir())
        except OSError:
            entry_count = "unknown"
        report.info(f"workspace-archive available ({entry_count} entries).")


def validate_readme(base: Path, report: ValidationReport) -> None:
    readme_path = base / "README.md"
    if readme_path.exists():
        report.ok("README.md present.")
    else:
        report.warning("Missing README.md in Threshold target directory.")


def finalize(report: ValidationReport, strict: bool, json_report: bool) -> int:
    divider = "\n" + "=" * 60
    print(divider)

    if report.errors:
        print(f"\n❌ ERRORS ({len(report.errors)}):")
        for error in report.errors:
            print(f"  - {error}")

    if report.warnings:
        print(f"\n[WARN] WARNINGS ({len(report.warnings)}):")
        for warning in report.warnings:
            print(f"  - {warning}")

    success = not report.errors
    if strict and report.warnings:
        success = False

    if success and not report.warnings:
        print("\n[OK] All checks passed! Configuration is ready.")
    elif success:
        print("\n[OK] No errors found. Configuration is usable, but warnings remain.")
    else:
        print("\n❌ Configuration has blocking issues.")
        if strict and report.warnings:
            print("\n[WARN] Strict mode treats warnings as failures.")

    if json_report:
        print(divider)
        print(json.dumps(report.as_dict(), indent=2))

    if success:
        print(divider)
        print("\nNext steps:")
        print("1. Run a dry-run test:")
        print("   secbrain run \\")
        print("     --scope targets/thresholdnetwork/scope.yaml \\")
        print("     --program targets/thresholdnetwork/program.json \\")
        print("     --workspace targets/thresholdnetwork/workspace \\")
        print("     --dry-run")
        print("\n2. If dry-run succeeds, run full analysis.")
        print("\n3. Generate insights report.")

    return 0 if success else 1


def validate_config(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base = Path(args.base).expanduser().resolve()
    if not base.exists():
        raise SystemExit(f"Base path does not exist: {base}")

    report = ValidationReport(quiet=args.quiet)

    program_path = _resolve_path(base, args.program, "program.json")
    scope_path = _resolve_path(base, args.scope, "scope.yaml")

    program = validate_program_section(program_path, report)
    scope = validate_scope_section(scope_path, report)

    instascope_override = args.instascope
    if instascope_override is None and scope and scope.foundry_root is not None:
        instascope_override = scope.foundry_root
    instascope_path = _resolve_path(base, instascope_override, "instascope")

    validate_instascope(instascope_path, scope, report)
    validate_readme(base, report)
    validate_workspace(base, report)

    return finalize(report, strict=args.strict, json_report=args.json_report)


if __name__ == "__main__":
    sys.exit(validate_config())
