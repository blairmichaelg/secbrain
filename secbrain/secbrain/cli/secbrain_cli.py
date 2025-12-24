"""SecBrain CLI - Main entry point for the security bounty agent system."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from secbrain.models.base import DryRunModelClient, ModelClient
from secbrain.models.gemini_advisor import GeminiAdvisorClient
from secbrain.models.open_workers import OpenWorkerClient

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

    # Load model clients (worker/advisor)
    worker_model, advisor_model = _initialize_models(dry_run=dry_run)
    if worker_model:
        run_context.worker_model = worker_model
    if advisor_model:
        run_context.advisor_model = advisor_model

    # Set up logging
    logger = setup_logging(
        workspace_path=workspace_path,
        run_id=run_context.run_id,
    )

    # Run workflow
    try:
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
    finally:
        await _shutdown_model_client(worker_model)
        await _shutdown_model_client(advisor_model)

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


def _initialize_models(dry_run: bool) -> tuple[ModelClient | None, ModelClient | None]:
    """
    Load model configuration and initialize worker/advisor clients.

    Returns (worker_model, advisor_model)
    """
    if dry_run:
        dummy = DryRunModelClient()
        return dummy, dummy

    config_path = Path(__file__).parent.parent / "config" / "models.yaml"
    if not config_path.exists():
        console.print(
            "[yellow]Warning:[/] config/models.yaml not found; running without model clients."
        )
        return None, None

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    profile = os.environ.get("SECBRAIN_MODELS_PROFILE")
    config_data: dict[str, Any] = data
    if profile:
        profile_section = data.get(profile)
        if isinstance(profile_section, dict):
            config_data = profile_section
        else:
            console.print(
                f"[yellow]Warning:[/] Requested models profile '{profile}' not found; "
                "falling back to default."
            )

    worker_client = _create_worker_client(config_data.get("worker"))
    advisor_client = _create_advisor_client(config_data.get("advisor"))
    return worker_client, advisor_client


def _create_worker_client(config: dict[str, Any] | None) -> ModelClient | None:
    if not config:
        console.print("[yellow]Warning:[/] Worker model configuration missing.")
        return None

    provider = (config.get("provider") or "openai_compatible").lower()
    model_name = config.get("model", "deepseek-ai/DeepSeek-V3")
    base_url = config.get("base_url")
    api_key = config.get("api_key")
    extra_args = {
        key: config[key]
        for key in ("max_tokens", "temperature", "top_p", "presence_penalty", "frequency_penalty")
        if key in config
    }

    if provider in {"openai_compatible", "ollama"}:
        return OpenWorkerClient(model=model_name, base_url=base_url, api_key=api_key, **extra_args)

    console.print(
        f"[yellow]Warning:[/] Unsupported worker model provider '{provider}'. Worker calls disabled."
    )
    return None


def _create_advisor_client(config: dict[str, Any] | None) -> ModelClient | None:
    if not config:
        console.print("[yellow]Warning:[/] Advisor model configuration missing.")
        return None

    provider = (config.get("provider") or "openai_compatible").lower()
    model_name = config.get("model", "Qwen/Qwen2.5-Coder-32B-Instruct")
    base_url = config.get("base_url")
    api_key = config.get("api_key")
    extra_args = {
        key: config[key]
        for key in ("max_tokens", "temperature", "top_p", "presence_penalty", "frequency_penalty")
        if key in config
    }

    if provider in {"openai_compatible", "ollama"}:
        return OpenWorkerClient(model=model_name, base_url=base_url, api_key=api_key, **extra_args)
    if provider == "gemini":
        return GeminiAdvisorClient(model=model_name, api_key=api_key, **extra_args)

    console.print(
        f"[yellow]Warning:[/] Unsupported advisor model provider '{provider}'. Advisor calls disabled."
    )
    return None


async def _shutdown_model_client(client: ModelClient | None) -> None:
    """Attempt to gracefully close model client transports."""
    if client is None:
        return
    close_coro = getattr(client, "close", None)
    if close_coro is None:
        return
    maybe_coro = close_coro()
    if asyncio.iscoroutine(maybe_coro):
        try:
            await maybe_coro
        except Exception:
            pass


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


@app.command()
def insights(
    workspace: Path = typer.Option(
        ...,
        "--workspace",
        "-w",
        help="Path to workspace directory to analyze",
        exists=True,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        ".",
        "--output",
        "-o",
        help="Directory for output reports (default: current directory)",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, html, json, csv, or all",
    ),
    open_report: bool = typer.Option(
        False,
        "--open",
        help="Open the HTML report in browser after generation",
    ),
) -> None:
    """Generate actionable insights report from workspace data."""
    from secbrain.insights import InsightsAggregator, InsightsAnalyzer, InsightsReporter

    console.print("[bold blue]SecBrain Insights[/] Analyzing workspace...")
    console.print(f"Workspace: {workspace}")

    try:
        # Aggregate data
        aggregator = InsightsAggregator(workspace)
        data = aggregator.aggregate()
        console.print(f"  ✓ Loaded {data.total_runs} runs, {data.total_hypotheses} hypotheses, {data.total_attempts} attempts")

        # Analyze
        analyzer = InsightsAnalyzer()
        results = analyzer.analyze(data)
        console.print(f"  ✓ Generated {len(results.insights)} insights")

        # Display summary
        console.print()
        console.print("[bold]Executive Summary[/]")
        console.print(f"  Status: [{'red' if results.summary['status'] == 'requires_attention' else 'yellow' if results.summary['status'] == 'review_recommended' else 'green'}]{results.summary['status'].replace('_', ' ').title()}[/]")
        console.print(f"  Critical Issues: {results.summary['critical_count']}")
        console.print(f"  High Priority: {results.summary['high_count']}")
        console.print(f"  Next Action: {results.summary['next_action']}")

        # Display critical insights
        critical = results.get_critical_insights()
        if critical:
            console.print()
            console.print("[bold red]🔴 Critical Issues:[/]")
            for insight in critical:
                console.print(f"  • {insight.title}")
                console.print(f"    {insight.action}")

        # Generate reports
        reporter = InsightsReporter(output_dir)
        console.print()
        console.print("[bold]Generating reports...[/]")

        if format.lower() == "all":
            files = reporter.save_all_formats(results)
            for fmt, filepath in files.items():
                console.print(f"  ✓ {fmt.capitalize()}: {filepath}")
            html_file = files.get("html")
        else:
            filepath = reporter.save_report(results, format.lower())
            console.print(f"  ✓ {format.capitalize()}: {filepath}")
            html_file = filepath if format.lower() == "html" else None

        # Open in browser if requested
        if open_report and html_file:
            import webbrowser
            webbrowser.open(f"file://{html_file.absolute()}")
            console.print(f"  ✓ Opened {html_file} in browser")

        console.print()
        console.print("[green]✓ Insights generation complete![/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
