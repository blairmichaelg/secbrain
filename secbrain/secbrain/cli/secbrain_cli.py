"""SecBrain CLI - Main entry point for the security bounty agent system."""

from __future__ import annotations

import asyncio
import json
import signal
import sys
from pathlib import Path
import os
import subprocess
import tempfile

import typer
import yaml
from rich.console import Console
from rich.table import Table

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # Non-fatal if python-dotenv is not installed
    pass

from secbrain.core.model_manager import reset_model_manager, get_model_manager
from eth_utils import is_address

app = typer.Typer(
    name="secbrain",
    help="Multi-agent security bounty system with research integration and guarded tooling.",
    no_args_is_help=True,
)
console = Console()

# Global flag for kill-switch
_kill_requested = False


def _signal_handler(signum: int, frame: object) -> None:
    """Handle interrupt signals for graceful shutdown."""
    global _kill_requested
    _kill_requested = True
    console.print("\n[bold red]Kill-switch activated![/] Stopping run...")


@app.command()
def run(
    scope: Path = typer.Option(
        ...,
        "--scope",
        "-s",
        help="Path to scope.yaml defining target boundaries",
        exists=True,
        readable=True,
    ),
    program: Path = typer.Option(
        ...,
        "--program",
        "-p",
        help="Path to program.json with bounty program details",
        exists=True,
        readable=True,
    ),
    workspace: Path = typer.Option(
        ...,
        "--workspace",
        "-w",
        help="Directory for run artifacts, logs, and findings",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="Simulate run without making real HTTP calls or tool executions (default: dry-run)",
    ),
    phases: str | None = typer.Option(
        None,
        "--phases",
        help="Comma-separated list of phases to run (e.g., recon,exploit,report)",
    ),
    kill_switch_file: Path | None = typer.Option(
        None,
        "--kill-switch-file",
        help="Path to file that, if created, will stop the run immediately",
    ),
    source_path: Path | None = typer.Option(
        None,
        "--source",
        help="Path to source code for static analysis",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve/--require-approval",
        help="Auto-approve sensitive actions (default: auto-approve for solo use)",
    ),
    approval_mode: str = typer.Option(
        "deny",
        "--approval-mode",
        help="How to handle approval-required actions: deny | auto | ask (default: deny)",
    ),
    local_only_dry_run: bool = typer.Option(
        True,
        "--local-only-dry-run/--no-local-only-dry-run",
        help="When in dry-run, restrict targets to localhost/127.0.0.1 (default: on)",
    ),
    rpc_url: str | None = typer.Option(
        None,
        "--rpc-url",
        help="RPC URL for forked exploit execution",
    ),
    block_number: int | None = typer.Option(
        None,
        "--block-number",
        help="Block number for forked execution",
    ),
    chain_id: int | None = typer.Option(
        None,
        "--chain-id",
        help="Chain ID for forked execution",
    ),
    exploit_iterations: int | None = typer.Option(
        3,
        "--exploit-iterations",
        help="Number of exploit attempts per hypothesis (default: 3)",
    ),
    profit_threshold: float | None = typer.Option(
        0.1,
        "--profit-threshold",
        help="Profit (ETH) threshold to stop exploit iterations (default: 0.1)",
    ),
) -> None:
    """
    Run a full bug bounty workflow against the specified target.

    This command orchestrates all agents through the defined phases:
    ingest → plan → recon → hypothesis → exploit → triage → report
    """
    # Set up signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    phase_list: list[str] | None = None
    if phases:
        phase_list = [p.strip() for p in phases.split(",")]

    workspace.mkdir(parents=True, exist_ok=True)

    console.print("[bold blue]SecBrain[/] Starting bounty run...")
    console.print(f"  Scope: {scope}")
    console.print(f"  Program: {program}")
    console.print(f"  Workspace: {workspace}")
    console.print(f"  Dry Run: {dry_run}")
    if phase_list:
        console.print(f"  Phases: {', '.join(phase_list)}")

    try:
        result = asyncio.run(
            _run_workflow(
                scope_path=scope,
                program_path=program,
                workspace_path=workspace,
                dry_run=dry_run,
                phases=phase_list,
                kill_switch_file=kill_switch_file,
                source_path=source_path,
                auto_approve=auto_approve,
                approval_mode=approval_mode,
                local_only_dry_run=local_only_dry_run,
                rpc_url=rpc_url,
                block_number=block_number,
                chain_id=chain_id,
                exploit_iterations=exploit_iterations,
                profit_threshold=profit_threshold,
            )
        )

        # Display results
        _display_results(result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Run interrupted by user.[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {e}")
        sys.exit(1)


async def _run_workflow(
    scope_path: Path,
    program_path: Path,
    workspace_path: Path,
    dry_run: bool,
    phases: list[str] | None,
    kill_switch_file: Path | None,
    source_path: Path | None,
    auto_approve: bool,
    approval_mode: str,
    local_only_dry_run: bool,
    rpc_url: str | None,
    block_number: int | None,
    chain_id: int | None,
    exploit_iterations: int | None,
    profit_threshold: float | None,
) -> dict:
    """Execute the bug bounty workflow."""
    from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig
    from secbrain.core.logging import setup_logging
    from secbrain.workflows.bug_bounty_run import run_bug_bounty

    # Load scope config
    with open(scope_path) as f:
        scope_data = yaml.safe_load(f)

    scope_config = ScopeConfig(**scope_data)

    # Load program config
    with open(program_path) as f:
        program_data = json.load(f)

    program_config = ProgramConfig(
        name=program_data.get("name", "unknown"),
        platform=program_data.get("platform", ""),
        focus_areas=program_data.get("focus_areas", []),
        rules=program_data.get("rules", []),
        rewards=program_data.get("rewards", {}),
    )

    _validate_api_keys(dry_run=dry_run)

    # Preflight checks
    errors: list[str] = []
    # 1) Foundry availability (when not dry-run)
    if not dry_run:
        try:
            result = subprocess.run(
                ["forge", "--version"],
                capture_output=True,
                timeout=5,
                check=False,
                text=True,
            )
            if result.returncode != 0:
                errors.append(f"Foundry not working: {result.stderr.strip()}")
        except FileNotFoundError:
            errors.append("Foundry not installed or not in PATH")
        except subprocess.TimeoutExpired:
            errors.append("Foundry --version timed out")
        except Exception as e:
            errors.append(f"Foundry check unexpected error: {e}")

    # 2) Workspace writable
    try:
        workspace_path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=workspace_path, delete=True) as tmp:
            tmp.write(b"test")
            tmp.flush()
    except Exception as e:
        errors.append(f"Workspace not writable: {e}")

    # 3) foundry_root existence if provided
    foundry_root = getattr(scope_config, "foundry_root", None)
    if foundry_root:
        fr = Path(foundry_root)
        if not fr.exists():
            errors.append(f"Foundry root does not exist: {foundry_root}")
        elif not (fr / "foundry.toml").exists():
            errors.append(f"Foundry root missing foundry.toml: {foundry_root}")

    # 4) RPC URL presence when contracts exist
    has_contracts = bool(getattr(scope_config, "contracts", None))
    scope_rpc = getattr(scope_config, "rpc_url", None)
    if has_contracts and not (rpc_url or scope_rpc):
        errors.append("RPC URL required for contract exploitation but not configured")

    # 5) Validate contract addresses
    contracts = getattr(scope_config, "contracts", []) or []
    for c in contracts:
        try:
            addr = c.get("address") if isinstance(c, dict) else getattr(c, "address", None)
            if not addr or not is_address(addr):
                errors.append(f"Invalid contract address: {addr}")
        except Exception:
            errors.append(f"Malformed contract address entry: {c}")

    if errors:
        console.print("[bold red]Preflight checks failed:[/]")
        for e in errors:
            console.print(f"  - {e}")
        raise SystemExit(1)

    # Create run context
    run_context = RunContext(
        scope=scope_config,
        program=program_config,
        workspace_path=workspace_path,
        dry_run=dry_run,
        kill_switch_file=kill_switch_file,
        phases=phases,
        auto_approve=auto_approve or (approval_mode.lower() == "auto"),
        local_only_dry_run=local_only_dry_run,
        approval_mode=approval_mode,
        approval_audit_log=workspace_path / "audit.jsonl",
    )

    # Initialize model clients from config/models.yaml defaults
    try:
        models_cfg_path = Path(__file__).parent.parent / "config" / "models.yaml"
        if models_cfg_path.exists():
            with open(models_cfg_path, "r", encoding="utf-8") as f:
                models_cfg = yaml.safe_load(f) or {}
        else:
            models_cfg = {}

        # Use centralized ModelManager for Groq/Perplexity
        reset_model_manager()
        model_manager = get_model_manager()
        run_context.model_manager = model_manager  # for downstream access if needed

        worker_cfg = models_cfg.get("worker", {})
        advisor_cfg = models_cfg.get("advisor", {})

        console.print(
            "[green]Models initialized (ModelManager):[/]\n"
            f"  worker={worker_cfg.get('model')} base_url={worker_cfg.get('base_url')} key_present={bool(os.environ.get('GROQ_API_KEY'))}\n"
            f"  advisor={advisor_cfg.get('model')} base_url={advisor_cfg.get('base_url')} key_present={bool(os.environ.get('GROQ_API_KEY'))}"
        )
    except Exception as e:
        console.print(f"[yellow]Model initialization warning:[/] {e}")

    # Set up logging
    logger = setup_logging(
        workspace_path=workspace_path,
        run_id=run_context.run_id,
    )

    # Run workflow
    result = await run_bug_bounty(
        run_context=run_context,
        phases=phases,
        source_path=source_path,
        logger=logger,
        rpc_url=rpc_url,
        block_number=block_number,
        chain_id=chain_id,
        exploit_iterations=exploit_iterations,
        profit_threshold=profit_threshold,
    )

    return {
        "run_id": result.run_id,
        "success": result.success,
        "phases_completed": [p.value for p in result.phases_completed],
        "phases_failed": [p.value for p in result.phases_failed],
        "findings_count": result.findings_count,
        "reports_generated": result.reports_generated,
        "duration": result.total_duration_seconds,
        "errors": result.errors,
    }


def _validate_api_keys(*, dry_run: bool) -> None:
    """
    Fail fast if required API keys are missing for non-dry runs.

    Defaults are sourced from config/models.yaml:
    - Worker/Advisor (Groq): GROQ_API_KEY
    - Research (Perplexity): PERPLEXITY_API_KEY
    """
    if dry_run:
        return

    required = {
        "worker": ["GROQ_API_KEY"],
        "advisor": ["GROQ_API_KEY"],
        "research": ["PERPLEXITY_API_KEY"],
    }

    missing: list[str] = []
    for group in required.values():
        if not any(os.environ.get(key) for key in group):
            missing.extend(group)

    if missing:
        raise RuntimeError(
            "Missing required API keys for non-dry run: "
            + ", ".join(sorted(set(missing)))
        )


def _display_results(result: dict) -> None:
    """Display workflow results in a formatted table."""
    console.print()
    console.print("[bold blue]═══ SecBrain Run Complete ═══[/]")
    console.print()

    # Summary table
    table = Table(title="Run Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Run ID", result["run_id"])
    table.add_row("Status", "[green]Success[/]" if result["success"] else "[red]Failed[/]")
    table.add_row("Duration", f"{result['duration']:.1f}s")
    table.add_row("Phases Completed", ", ".join(result["phases_completed"]) or "None")
    table.add_row("Phases Failed", ", ".join(result["phases_failed"]) or "None")
    table.add_row("Findings", str(result["findings_count"]))
    table.add_row("Reports Generated", str(result["reports_generated"]))

    console.print(table)

    if result["errors"]:
        console.print()
        console.print("[bold red]Errors:[/]")
        for error in result["errors"]:
            console.print(f"  • {error}")


@app.command()
def version() -> None:
    """Display the current SecBrain version."""
    from secbrain import __version__

    console.print(f"[bold blue]SecBrain[/] v{__version__}")


@app.command()
def validate(
    scope: Path = typer.Option(
        ...,
        "--scope",
        "-s",
        help="Path to scope.yaml to validate",
        exists=True,
        readable=True,
    ),
    program: Path | None = typer.Option(
        None,
        "--program",
        "-p",
        help="Path to program.json to validate",
        exists=True,
        readable=True,
    ),
    require_env: list[str] = typer.Option(
        None,
        "--require-env",
        help="Environment variables that must be set (can be specified multiple times)",
    ),
    require_tools: list[str] = typer.Option(
        None,
        "--require-tool",
        help="CLI tools that must be on PATH (can be specified multiple times)",
    ),
) -> None:
    """Validate scope and program configuration files."""
    from secbrain.core.validation import (
        ValidationError,
        validate_environment,
        validate_program_file,
        validate_scope_file,
        validate_tools_on_path,
    )

    console.print("[bold blue]SecBrain[/] Validating configuration...")
    errors: list[str] = []

    try:
        validate_scope_file(scope)
        console.print(f"  Scope: {scope} [green]✓[/]")
    except ValidationError as e:
        errors.append(f"Scope invalid: {e}")

    if program:
        try:
            validate_program_file(program)
            console.print(f"  Program: {program} [green]✓[/]")
        except ValidationError as e:
            errors.append(f"Program invalid: {e}")

    if require_env:
        try:
            validate_environment(require_env)
            console.print(f"  Env: {', '.join(require_env)} [green]✓[/]")
        except ValidationError as e:
            errors.append(str(e))

    if require_tools:
        try:
            validate_tools_on_path(require_tools)
            console.print(f"  Tools: {', '.join(require_tools)} [green]✓[/]")
        except ValidationError as e:
            errors.append(str(e))

    if errors:
        console.print("[bold red]Configuration invalid[/]")
        for err in errors:
            console.print(f"  • {err}")
        raise typer.Exit(code=1)

    console.print("[green]Configuration valid.[/]")


if __name__ == "__main__":
    app()
