"""SecBrain CLI - Main entry point for the security bounty agent system."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import signal
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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


def _validate_run_options(
    rpc_url: str | None,
    block_number: int | None,
    chain_id: int | None,
    exploit_iterations: int | None,
    profit_threshold: float | None,
) -> None:
    """Validate CLI options that materially impact workflow execution."""
    errors: list[str] = []

    if block_number is not None and block_number < 0:
        errors.append("--block-number must be >= 0")

    if chain_id is not None and chain_id <= 0:
        errors.append("--chain-id must be a positive integer")

    if exploit_iterations is not None and exploit_iterations <= 0:
        errors.append("--exploit-iterations must be >= 1")

    if profit_threshold is not None and profit_threshold <= 0:
        errors.append("--profit-threshold must be greater than 0")

    if (block_number is not None or chain_id is not None) and not rpc_url:
        errors.append("--rpc-url is required when specifying block number or chain id")

    if rpc_url:
        parsed = urlparse(rpc_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("--rpc-url must be an absolute HTTP(S) URL")

    if errors:
        raise typer.BadParameter("\n".join(errors))


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
        False,
        "--dry-run/--no-dry-run",
        help="Simulate run without making real HTTP calls or tool executions",
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

    _validate_run_options(
        rpc_url=rpc_url,
        block_number=block_number,
        chain_id=chain_id,
        exploit_iterations=exploit_iterations,
        profit_threshold=profit_threshold,
    )

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
    with scope_path.open() as f:
        scope_data = yaml.safe_load(f)

    scope_config = ScopeConfig(**scope_data)

    # Load program config
    with program_path.open() as f:
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

    # Set up logging
    logger = setup_logging(
        workspace_path=workspace_path,
        run_id=run_context.run_id,
    )

    # Check tool availability
    try:
        from secbrain.utils.tool_checker import check_tools_on_startup

        console.print("[dim]Checking tool availability...[/]")
        tool_checker = check_tools_on_startup(logger)

        # Check for missing required tools
        missing_report = tool_checker.get_missing_tools_report()
        if "REQUIRED TOOLS MISSING" in missing_report:
            console.print(f"\n{missing_report}")
            console.print("[bold red]Cannot proceed: required tools are missing[/]")
            raise RuntimeError("Required tools are not installed")
        if "RECOMMENDED TOOLS MISSING" in missing_report:
            console.print(f"\n[dim]{missing_report}[/]")
            console.print(
                "[yellow]Warning: Some recommended tools are missing. "
                "Workflow will continue but functionality may be limited.[/]\n"
            )
        else:
            console.print("[dim]All tools available[/]\n")
    except ImportError as e:
        # Tool checker not available, skip check
        if logger:
            logger.warning("tool_checker_unavailable", reason="import_error", error=str(e))
        console.print(
            "[yellow]Warning:[/] Tool availability check could not run; "
            "ensure Foundry/Nuclei/etc. are installed."
        )

    # Load model clients (worker/advisor)
    worker_model, advisor_model = _initialize_models(dry_run=dry_run)

    missing_clients: list[str] = []
    if worker_model:
        run_context.worker_model = worker_model
    else:
        missing_clients.append("worker")
    if advisor_model:
        run_context.advisor_model = advisor_model
    else:
        missing_clients.append("advisor")

    if missing_clients and not dry_run:
        console.print(
            f"[yellow]Warning:[/] Missing model client(s): {', '.join(missing_clients)}. "
            "LLM-powered agents may be degraded."
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
        if worker_model:
            await _shutdown_model_client(worker_model)
        if advisor_model:
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

    with config_path.open(encoding="utf-8") as f:
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
    model_name = config.get("model", "meta-llama/Llama-3.2-3B-Instruct-Turbo")  # FREE tier default
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
    model_name = config.get("model", "meta-llama/Meta-Llama-3-8B-Instruct-Turbo")  # FREE tier default
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
        with contextlib.suppress(Exception):
            await maybe_coro


def _display_results(result: dict) -> None:
    """Display workflow results in a formatted table."""
    console.print("\n" + "=" * 30)
    console.print("[bold green]SecBrain Run Complete[/]")
    console.print("=" * 30)

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
            console.print(f"  - {error}")


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
        console.print(f"  Scope: {scope} [green]OK[/]")
    except ValidationError as e:
        errors.append(f"Scope invalid: {e}")

    if program:
        try:
            validate_program_file(program)
            console.print(f"  Program: {program} [green]OK[/]")
        except ValidationError as e:
            errors.append(f"Program invalid: {e}")

    if require_env:
        try:
            validate_environment(require_env)
            console.print(f"  Env: {', '.join(require_env)} [green]OK[/]")
        except ValidationError as e:
            errors.append(str(e))

    if require_tools:
        try:
            validate_tools_on_path(require_tools)
            console.print(f"  Tools: {', '.join(require_tools)} [green]OK[/]")
        except ValidationError as e:
            errors.append(str(e))

    if errors:
        console.print("[bold red]Configuration invalid[/]")
        for err in errors:
            console.print(f"  - {err}")
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
        console.print(f"  Loaded {data.total_runs} runs, {data.total_hypotheses} hypotheses, {data.total_attempts} attempts")

        # Analyze
        analyzer = InsightsAnalyzer()
        results = analyzer.analyze(data)
        console.print(f"  Generated {len(results.insights)} insights")

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
            console.print("[bold red]Critical Issues:[/]")
            for insight in critical:
                console.print(f"  - {insight.title}")
                console.print(f"    {insight.action}")

        # Generate reports
        reporter = InsightsReporter(output_dir)
        console.print()
        console.print("[bold]Generating reports...[/]")

        if format.lower() == "all":
            files = reporter.save_all_formats(results)
            for fmt, filepath in files.items():
                console.print(f"  {fmt.capitalize()}: {filepath}")
            html_file = files.get("html")
        else:
            filepath = reporter.save_report(results, format.lower())
            console.print(f"  {format.capitalize()}: {filepath}")
            html_file = filepath if format.lower() == "html" else None

        # Open in browser if requested
        if open_report and html_file:
            import webbrowser
            webbrowser.open(f"file://{html_file.absolute()}")
            console.print(f"  Opened {html_file} in browser")

        console.print()
        console.print("[green]Insights generation complete![/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1) from e


@app.command()
def immunefi(
    action: str = typer.Argument(
        ...,
        help="Action to perform: list, show, trends, or intelligence",
    ),
    program_id: str | None = typer.Option(
        None,
        "--program",
        "-p",
        help="Program ID for 'show' or 'intelligence' actions",
    ),
    min_bounty: int = typer.Option(
        500_000,
        "--min-bounty",
        "-m",
        help="Minimum bounty amount for filtering programs",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results to show",
    ),
) -> None:
    """Interact with Immunefi platform intelligence.

    Actions:
      list        - List high-value bounty programs
      show        - Show details for a specific program
      trends      - Show trending vulnerability patterns
      intelligence - Get comprehensive intelligence for a program
    """
    console.print("[bold blue]SecBrain Immunefi Intelligence[/]")

    async def _run_action():
        from secbrain.tools.immunefi_client import ImmunefiClient

        client = ImmunefiClient()
        try:
            if action == "list":
                programs = await client.get_high_value_programs(
                    min_bounty=min_bounty,
                    limit=limit,
                )

                table = Table(title=f"High-Value Programs (≥${min_bounty:,})")
                table.add_column("Program", style="cyan")
                table.add_column("Max Bounty", justify="right", style="green")
                table.add_column("Priority", justify="right", style="yellow")
                table.add_column("Blockchain", style="blue")

                for prog in programs:
                    table.add_row(
                        prog.name,
                        f"${prog.max_bounty:,}",
                        f"{prog.get_priority_score():.1f}",
                        ", ".join(prog.blockchain[:2]),
                    )

                console.print(table)

            elif action == "show":
                if not program_id:
                    console.print("[red]Error: --program (program ID) required for 'show' action[/]")
                    raise typer.Exit(code=1)

                program = await client.get_program_by_id(program_id)
                if not program:
                    console.print(f"[red]Program '{program_id}' not found[/]")
                    raise typer.Exit(code=1)

                console.print(f"\n[bold]{program.name}[/]")
                console.print("Platform: Immunefi")
                console.print(f"Max Bounty: [green]${program.max_bounty:,}[/]")
                console.print(f"Priority Score: [yellow]{program.get_priority_score():.1f}/100[/]")
                console.print(f"Blockchain: {', '.join(program.blockchain)}")
                console.print(f"Language: {', '.join(program.language)}")
                console.print(f"\nCritical Reward: ${program.critical_reward[0]:,} - ${program.critical_reward[1]:,}")
                console.print(f"High Reward: ${program.high_reward[0]:,} - ${program.high_reward[1]:,}")

                if program.assets_in_scope:
                    console.print("\n[bold]In Scope:[/]")
                    for asset in program.assets_in_scope:
                        console.print(f"  - {asset}")

            elif action == "trends":
                trends = await client.get_trending_vulnerabilities(days=90)

                table = Table(title="Trending Vulnerabilities (Last 90 Days)")
                table.add_column("Vulnerability Type", style="cyan")
                table.add_column("Severity", style="red")
                table.add_column("Count", justify="right", style="yellow")
                table.add_column("Avg Bounty", justify="right", style="green")

                for trend in trends[:limit]:
                    table.add_row(
                        trend.vulnerability_type,
                        trend.severity.upper(),
                        str(trend.occurrences),
                        f"${trend.avg_bounty:,.0f}",
                    )

                console.print(table)

            elif action == "intelligence":
                if not program_id:
                    console.print("[red]Error: --program (program ID) required for 'intelligence' action[/]")
                    raise typer.Exit(code=1)

                intel = await client.get_program_intelligence(program_id)

                if "error" in intel:
                    console.print(f"[red]{intel['error']}[/]")
                    raise typer.Exit(code=1)

                console.print(f"\n[bold]{intel['program']['name']}[/]")
                console.print(f"Priority Score: [yellow]{intel['program']['priority_score']:.1f}/100[/]")

                console.print("\n[bold]Statistics:[/]")
                stats = intel['statistics']
                console.print(f"  Total Paid: ${stats['total_paid']:,}")
                console.print(f"  Submissions: {stats['submission_count']}")
                console.print(f"  Avg Bounty: ${stats['avg_bounty']:,.0f}")

                if intel['recommended_focus_areas']:
                    console.print("\n[bold]Recommended Focus Areas:[/]")
                    for area in intel['recommended_focus_areas'][:5]:
                        console.print(f"  - {area}")

                if intel['relevant_trends']:
                    console.print("\n[bold]Relevant Vulnerabilities:[/]")
                    for trend in intel['relevant_trends'][:3]:
                        console.print(f"  - {trend['type']} ({trend['severity']}) - ${trend['avg_bounty']:,.0f}")

            else:
                console.print(f"[red]Unknown action: {action}[/]")
                console.print("Valid actions: list, show, trends, intelligence")
                raise typer.Exit(code=1)

        finally:
            await client.close()

    asyncio.run(_run_action())


@app.command()
def research(
    protocol: str | None = typer.Option(
        None,
        "--protocol",
        "-p",
        help="Protocol name to research",
    ),
    contracts: str | None = typer.Option(
        None,
        "--contracts",
        "-c",
        help="Comma-separated list of contract names",
    ),
    timeframe: int = typer.Option(
        90,
        "--timeframe",
        "-t",
        help="Days to look back for emerging patterns",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for research findings (JSON)",
    ),
) -> None:
    """Conduct advanced vulnerability research using cutting-edge techniques.

    This command analyzes emerging vulnerability patterns, protocol-specific
    risks, and generates novel vulnerability hypotheses based on the latest
    security research.
    """
    console.print("[bold blue]SecBrain Advanced Research[/]")

    async def _run_research():
        from secbrain.agents.advanced_research_agent import AdvancedResearchAgent
        from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig

        # Create minimal context for research
        workspace = Path.cwd() / "research_output"
        workspace.mkdir(exist_ok=True)

        scope_config = ScopeConfig(
            in_scope_domains=[],
            in_scope_ips=[],
            out_of_scope_domains=[],
        )

        program_config = ProgramConfig(
            name=protocol or "research",
            platform="research",
            focus_areas=[],
            rules=[],
            rewards={},
        )

        run_context = RunContext(
            scope=scope_config,
            program=program_config,
            workspace_path=workspace,
            dry_run=True,
        )

        agent = AdvancedResearchAgent(
            run_context=run_context,
            research_client=None,  # Will use curated data
        )

        results = {
            "emerging_patterns": [],
            "protocol_findings": [],
            "novel_hypotheses": [],
        }

        # Research emerging patterns
        console.print(f"🔍 Researching emerging patterns (last {timeframe} days)...")
        emerging = await agent.research_emerging_patterns(timeframe_days=timeframe)
        results["emerging_patterns"] = [
            {
                "title": f.title,
                "severity": f.severity,
                "confidence": f.confidence,
                "description": f.description,
                "attack_vectors": f.attack_vectors,
            }
            for f in emerging
        ]
        console.print(f"  Found {len(emerging)} emerging patterns")

        # Protocol-specific research
        if protocol:
            console.print(f"🔍 Analyzing {protocol}...")
            protocol_findings = await agent.analyze_protocol_specific(
                protocol_name=protocol,
                blockchain="Ethereum",
            )
            results["protocol_findings"] = [
                {
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                }
                for f in protocol_findings
            ]
            console.print(f"  Generated {len(protocol_findings)} protocol-specific findings")

        # Generate novel hypotheses
        if contracts:
            contract_list = [c.strip() for c in contracts.split(",")]
            console.print(f"🔍 Generating hypotheses for {len(contract_list)} contracts...")
            hypotheses = await agent.generate_novel_hypotheses(
                target_contracts=contract_list,
                context=f"Analyzing {protocol}" if protocol else "",
            )
            results["novel_hypotheses"] = hypotheses
            console.print(f"  Generated {len(hypotheses)} novel hypotheses")

        # Display summary
        console.print("\n[bold]Research Summary:[/]")
        console.print(f"  Emerging Patterns: {len(results['emerging_patterns'])}")
        console.print(f"  Protocol Findings: {len(results['protocol_findings'])}")
        console.print(f"  Novel Hypotheses: {len(results['novel_hypotheses'])}")

        # Show top findings
        if results["emerging_patterns"]:
            console.print("\n[bold]Top Emerging Patterns:[/]")
            for pattern in results["emerging_patterns"][:3]:
                console.print(f"  - [{pattern['severity'].upper()}] {pattern['title']}")

        # Save to file if requested
        if output:
            with output.open('w') as f:
                json.dump(results, f, indent=2)
            console.print(f"\nSaved results to {output}")

    asyncio.run(_run_research())


@app.command()
def metrics(
    action: str = typer.Argument(
        ...,
        help="Action: summary, programs, patterns, or insights",
    ),
    workspace: Path = typer.Option(
        Path.cwd() / "metrics",
        "--workspace",
        "-w",
        help="Metrics workspace directory",
    ),
    program: str | None = typer.Option(
        None,
        "--program",
        help="Program name for filtering",
    ),
    platform: str | None = typer.Option(
        None,
        "--platform",
        help="Platform name (e.g., immunefi)",
    ),
) -> None:
    """Track and analyze bug bounty success metrics.

    Actions:
      summary  - Show overall success metrics
      programs - Show per-program statistics
      patterns - Show vulnerability pattern effectiveness
      insights - Get learning insights for improvement
    """
    from secbrain.tools.bounty_metrics import BountyMetricsTracker

    console.print("[bold blue]SecBrain Bounty Metrics[/]")

    tracker = BountyMetricsTracker(workspace)

    if action == "summary":
        metrics = tracker.get_overall_metrics()

        if metrics.get("total_submissions", 0) == 0:
            console.print("\n[yellow]No submissions recorded yet.[/]")
            console.print("Submissions can be recorded programmatically using BountyMetricsTracker.")
            return

        console.print("\n[bold]Overall Metrics:[/]")
        console.print(f"  Total Submissions: {metrics['total_submissions']}")
        console.print(f"  Accepted: [green]{metrics['accepted']}[/]")
        console.print(f"  Rejected: [red]{metrics['rejected']}[/]")
        console.print(f"  Duplicates: [yellow]{metrics['duplicates']}[/]")
        console.print(f"  Acceptance Rate: [cyan]{metrics['acceptance_rate']:.1%}[/]")
        console.print(f"  Total Earned: [green]${metrics['total_earned']:,.2f}[/]")
        console.print(f"  Avg Bounty: [green]${metrics['avg_bounty']:,.2f}[/]")
        console.print(f"  Programs: {metrics['programs_participated']}")

    elif action == "programs":
        programs = tracker.get_top_performing_programs(limit=10)

        if not programs:
            console.print("\n[yellow]No program data available.[/]")
            return

        table = Table(title="Top Performing Programs")
        table.add_column("Program", style="cyan")
        table.add_column("Platform", style="blue")
        table.add_column("Submissions", justify="right")
        table.add_column("Accepted", justify="right", style="green")
        table.add_column("Rate", justify="right")
        table.add_column("Total Earned", justify="right", style="green")

        for prog in programs:
            table.add_row(
                prog.program,
                prog.platform,
                str(prog.total_submissions),
                str(prog.accepted_submissions),
                f"{prog.acceptance_rate:.1%}",
                f"${prog.total_earned:,.0f}",
            )

        console.print(table)

    elif action == "patterns":
        patterns = tracker.get_most_effective_patterns(limit=10)

        if not patterns:
            console.print("\n[yellow]No pattern data available.[/]")
            return

        table = Table(title="Most Effective Vulnerability Patterns")
        table.add_column("Pattern", style="cyan")
        table.add_column("Submitted", justify="right")
        table.add_column("Accepted", justify="right", style="green")
        table.add_column("Effectiveness", justify="right", style="yellow")
        table.add_column("Avg Bounty", justify="right", style="green")

        for pattern in patterns:
            table.add_row(
                pattern.pattern_name,
                str(pattern.times_submitted),
                str(pattern.times_accepted),
                f"{pattern.detection_effectiveness:.1%}",
                f"${pattern.avg_bounty:,.0f}",
            )

        console.print(table)

    elif action == "insights":
        insights = tracker.get_learning_insights()

        console.print("\n[bold]Learning Insights:[/]")

        if insights["high_value_patterns"]:
            console.print("\n[bold green]High-Value Patterns (Focus Here!):[/]")
            for pattern in insights["high_value_patterns"][:5]:
                console.print(
                    f"  - {pattern['pattern']} - "
                    f"{pattern['effectiveness']:.1%} success, "
                    f"${pattern['avg_bounty']:,.0f} avg"
                )

        if insights["low_confidence_patterns"]:
            console.print("\n[bold red]Low-Confidence Patterns (Avoid/Improve):[/]")
            for pattern in insights["low_confidence_patterns"][:5]:
                console.print(
                    f"  - {pattern['pattern']} - "
                    f"{pattern['effectiveness']:.1%} success, "
                    f"{pattern['times_submitted']} submissions"
                )

        if insights["recommended_focus_areas"]:
            console.print("\n[bold yellow]Recommended Focus Areas:[/]")
            for area in insights["recommended_focus_areas"][:5]:
                console.print(f"  - {area['pattern']}: {area['reason']}")

    else:
        console.print(f"[red]Unknown action: {action}[/]")
        console.print("Valid actions: summary, programs, patterns, insights")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
