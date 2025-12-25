"""Reconnaissance agent for discovering assets and gathering information."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import tomllib
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from secbrain.agents.base import AgentResult, BaseAgent
from secbrain.tools.recon_cli_wrappers import ReconToolRunner

T = TypeVar("T")


class NonRetryableCompilationError(Exception):
    """Raised when forge compilation fails with a non-retryable error."""

    def __init__(self, message: str, *, stdout: str = "", stderr: str = "") -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


class CompilationRetryHelper:
    """Helper for retrying compilation with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_wait: float = 2.0,
        logger=None,
    ) -> None:
        self.max_retries = max_retries
        self.base_wait = base_wait
        self.logger = logger

    def is_retryable_error(self, error_text: str) -> bool:
        """Check if error is transient and retryable."""
        retryable_keywords = [
            "timeout",
            "connection",
            "network",
            "rpc",
            "econnrefused",
            "temporary",
        ]
        error_lower = (error_text or "").lower()
        return any(keyword in error_lower for keyword in retryable_keywords)

    async def retry_with_backoff(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        context: str = "operation",
    ) -> T:
        """Execute operation with exponential backoff retry."""
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return await operation()
            except TimeoutError as exc:
                last_exception = exc
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait ** (attempt + 1)
                    if self.logger:
                        self.logger.info(
                            f"{context}_timeout_retry",
                            attempt=attempt + 1,
                            wait_time=wait_time,
                        )
                    await asyncio.sleep(wait_time)
                    continue
            except Exception as exc:
                last_exception = exc
                if self.is_retryable_error(str(exc)) and attempt < self.max_retries - 1:
                    wait_time = self.base_wait ** (attempt + 1)
                    if self.logger:
                        self.logger.info(
                            f"{context}_exception_retry",
                            attempt=attempt + 1,
                            exception=str(exc)[:100],
                            wait_time=wait_time,
                        )
                    await asyncio.sleep(wait_time)
                    continue
                raise

        if last_exception:
            raise last_exception
        raise RuntimeError(f"{context} failed after {self.max_retries} retries")


class ReconAgent(BaseAgent):
    """
    Recon agent.

    Responsibilities:
    - Orchestrates recon tools
    - Builds endpoint/asset map
    - Research substep: given recon results, asks Perplexity about stack/vuln classes
    """

    name = "recon"
    phase = "recon"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Execute reconnaissance phase."""
        self._log("starting_recon")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        domains = self.run_context.scope.domains
        contracts = self.run_context.scope.contracts

        # Debug logging
        self._log("debug_scope", domains_count=len(domains), contracts_count=len(contracts))
        if contracts:
            self._log("first_contract", name=contracts[0].name, address=contracts[0].address)

        # Check if we have contracts to recon
        if contracts:
            return await self._recon_contracts(contracts)

        # Fall back to web-based recon
        if not domains:
            return self._failure("No domains or contracts in scope for recon")

        # Collect all assets
        all_assets: list[dict[str, Any]] = []
        technologies: list[str] = []

        # Run subdomain enumeration
        subdomains = await self._enumerate_subdomains(domains)
        all_assets.extend(subdomains)

        # Run HTTP probing
        live_hosts = []
        if subdomains:
            live_hosts = await self._probe_http([a["value"] for a in subdomains])
            all_assets.extend(live_hosts)

            # Extract technologies
            for host in live_hosts:
                techs = host.get("metadata", {}).get("technologies", [])
                technologies.extend(techs)

        # Run Nuclei vulnerability scanning on live hosts
        nuclei_findings = []
        if live_hosts:
            nuclei_findings = await self._scan_with_nuclei(
                [host["value"] for host in live_hosts]
            )
            # Add nuclei findings as assets
            all_assets.extend(nuclei_findings)

        # Research: understand the technology stack
        tech_research = {}
        if technologies and self.research_client:
            unique_techs = list(set(technologies))[:5]  # Limit to top 5
            tech_research = await self._research_technologies(unique_techs)

        # Store assets
        if self.storage:
            for asset in all_assets:
                await self.storage.save_asset(asset)

        return self._success(
            message=f"Recon complete: {len(all_assets)} assets discovered ({len(nuclei_findings)} vulnerabilities)",
            data={
                "assets": all_assets,
                "subdomains_count": len(subdomains),
                "live_hosts_count": len([a for a in all_assets if a.get("type") == "live_host"]),
                "nuclei_findings_count": len(nuclei_findings),
                "technologies": list(set(technologies)),
                "tech_research": tech_research,
            },
            next_actions=["hypothesis"],
        )

    async def _enumerate_subdomains(
        self,
        domains: list[str],
    ) -> list[dict[str, Any]]:
        """Enumerate subdomains for given domains."""

        assets: list[dict[str, Any]] = []
        runner = ReconToolRunner(self.run_context)

        for domain in domains:
            # Skip wildcard prefix
            domain_clean = domain[2:] if domain.startswith("*.") else domain

            self._log("enumerating_subdomains", domain=domain_clean)

            result = await runner.run_subfinder(domain_clean)

            if result.success:
                for item in result.parsed_data:
                    subdomain = item.get("subdomain", "")
                    if subdomain:
                        assets.append({
                            "id": f"sub-{uuid.uuid4().hex[:8]}",
                            "type": "subdomain",
                            "value": subdomain,
                            "metadata": {"source": "subfinder", "parent_domain": domain},
                        })

        return assets

    async def _probe_http(
        self,
        targets: list[str],
    ) -> list[dict[str, Any]]:
        """Probe targets for live HTTP services."""

        assets: list[dict[str, Any]] = []
        runner = ReconToolRunner(self.run_context)

        # Add protocol prefixes for httpx
        urls = []
        for target in targets:
            if not target.startswith("http"):
                urls.append(f"https://{target}")
                urls.append(f"http://{target}")
            else:
                urls.append(target)

        self._log("probing_http", count=len(urls))

        result = await runner.run_httpx(urls[:100])  # Limit to 100 for safety

        if result.success:
            for item in result.parsed_data:
                url = item.get("url", "")
                if url:
                    assets.append({
                        "id": f"host-{uuid.uuid4().hex[:8]}",
                        "type": "live_host",
                        "value": url,
                        "metadata": {
                            "status_code": item.get("status_code"),
                            "title": item.get("title"),
                            "technologies": item.get("tech", []),
                            "content_length": item.get("content_length"),
                            "webserver": item.get("webserver"),
                        },
                    })

        return assets

    async def _research_technologies(
        self,
        technologies: list[str],
    ) -> dict[str, Any]:
        """Research identified technologies for vulnerabilities."""
        research_results = {}

        for tech in technologies[:3]:  # Limit to 3 to save API calls
            result = await self._research(
                question=f"What are common security vulnerabilities and attack vectors for {tech}?",
                context="Technology stack analysis during recon phase",
            )
            research_results[tech] = {
                "answer": result.get("answer", "")[:500],
                "sources": result.get("sources", []),
            }

        return research_results

    async def _scan_with_nuclei(
        self,
        targets: list[str],
    ) -> list[dict[str, Any]]:
        """
        Run Nuclei vulnerability scanner on targets.

        Args:
            targets: List of URLs to scan

        Returns:
            List of finding assets discovered by Nuclei
        """
        # Import here to avoid hard dependency
        try:
            from secbrain.tools.scanners import NucleiScanner
        except ImportError:
            self._log("nuclei_scanner_unavailable", reason="import_error")
            return []

        scanner = NucleiScanner(self.run_context)

        # Check if nuclei is available
        if not scanner._find_nuclei():
            self._log(
                "nuclei_scanner_unavailable",
                reason="not_installed",
                hint="Install with: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
            )
            return []

        self._log("scanning_with_nuclei", target_count=len(targets))

        # Run nuclei scan with focus on critical/high severity
        result = await scanner.scan(
            targets=targets[:50],  # Limit to 50 targets for safety
            severity=["critical", "high", "medium"],
            tags=["cve", "exposure", "config", "misconfig"],
            exclude_tags=["dos", "fuzzing"],  # Exclude noisy/dangerous templates
            rate_limit=100,
            timeout=600,  # 10 minutes max
        )

        findings: list[dict[str, Any]] = []

        if result.success:
            self._log(
                "nuclei_scan_complete",
                findings_count=len(result.findings),
                duration_ms=result.duration_ms,
            )

            for item in result.findings:
                # Convert Nuclei finding to asset format
                findings.append({
                    "id": f"nuclei-{uuid.uuid4().hex[:8]}",
                    "type": "vulnerability",
                    "value": item.get("matched-at", ""),
                    "metadata": {
                        "source": "nuclei",
                        "template": item.get("template-id", ""),
                        "name": item.get("info", {}).get("name", ""),
                        "severity": item.get("info", {}).get("severity", ""),
                        "description": item.get("info", {}).get("description", ""),
                        "tags": item.get("info", {}).get("tags", []),
                        "reference": item.get("info", {}).get("reference", []),
                        "cvss_score": item.get("info", {}).get("classification", {}).get("cvss-score"),
                        "cve_id": item.get("info", {}).get("classification", {}).get("cve-id"),
                    },
                })
        else:
            self._log(
                "nuclei_scan_failed",
                error=result.error,
            )

        return findings

    def _extract_contract_metadata(
        self,
        foundry_root: str | Path,
        contract_name: str,
    ) -> tuple[list[Any], list[str]]:
        foundry_root_path = Path(foundry_root)
        out_dir = foundry_root_path / "out"
        if not out_dir.exists():
            return [], []

        candidate_paths = list(out_dir.rglob(f"{contract_name}.json"))
        if not candidate_paths:
            for p in out_dir.rglob("*.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if data.get("contractName") == contract_name and "abi" in data:
                    candidate_paths.append(p)
                    break

        artifact = None
        for p in candidate_paths:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if "abi" in data:
                artifact = data
                break

        if not artifact:
            return [], []

        abi = artifact.get("abi") or []
        functions: list[str] = []
        if isinstance(abi, list):
            for item in abi:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "function":
                    continue
                fn_name = item.get("name")
                inputs = item.get("inputs") or []
                if not fn_name or not isinstance(inputs, list):
                    continue
                arg_types: list[str] = []
                for inp in inputs:
                    if isinstance(inp, dict) and inp.get("type"):
                        arg_types.append(str(inp.get("type")))
                functions.append(f"{fn_name}({','.join(arg_types)})")

        return abi, sorted(set(functions))

    async def _recon_contracts(self, contracts: list) -> AgentResult:
        """Perform contract reconnaissance using Foundry."""
        self._log(f"Starting contract recon for {len(contracts)} contracts")

        all_assets = []
        compiled_contracts = []
        semaphore = asyncio.Semaphore(5)

        # Check if Foundry is available
        if not self.run_context.dry_run:
            try:
                import subprocess
                result = subprocess.run(["forge", "--version"], check=False, capture_output=True, text=True)
                if result.returncode != 0:
                    return self._failure("Foundry not installed or not in PATH")
            except FileNotFoundError:
                return self._failure("Foundry not installed or not in PATH")

        # Get Foundry root from scope
        foundry_root = self.run_context.scope.foundry_root
        if not foundry_root:
            return self._failure("No foundry_root specified in scope")

        foundry_root_path = Path(foundry_root)

        # Clean SecBrain-generated tests so they don't break `forge build` in subsequent runs.
        secbrain_test_dir = foundry_root_path / "test" / "secbrain"
        if secbrain_test_dir.exists():
            with contextlib.suppress(Exception):
                shutil.rmtree(secbrain_test_dir, ignore_errors=True)

        foundry_toml = {}
        try:
            foundry_toml_path = foundry_root_path / "foundry.toml"
            if foundry_toml_path.exists():
                foundry_toml = tomllib.loads(foundry_toml_path.read_text(encoding="utf-8"))
        except Exception:
            foundry_toml = {}

        retry_helper = CompilationRetryHelper(max_retries=3, base_wait=2.0, logger=self.logger)

        # Compile each contract using its profile
        async def _compile_contract(contract) -> dict[str, Any]:
            async with semaphore:
                if self._check_kill_switch():
                    return {"killed": True, "assets": [], "compiled": False}

                profile = contract.foundry_profile
                if not profile:
                    self._log(f"Skipping {contract.name} - no Foundry profile")
                    return {"killed": False, "assets": [], "compiled": False}

                self._log(f"Compiling contract {contract.name} with profile {profile}")
                metadata = getattr(contract, "metadata", {}) or {}
                abi: list[Any] = metadata.get("abi", []) or []
                functions: list[str] = metadata.get("functions", []) or []

                if self.run_context.dry_run:
                    classification = self._classify_contract(contract.name, functions)
                    asset = {
                        "type": "contract",
                        "value": contract.address,
                        "name": contract.name,
                        "chain_id": contract.chain_id,
                        "profile": profile,
                        "status": "simulated_compiled",
                        "metadata": {
                            "source_path": str(contract.source_path) if contract.source_path else None,
                            "verified": contract.verified,
                            "classification": classification,
                        },
                    }
                    return {"killed": False, "assets": [asset], "compiled": True, "address": contract.address}

                async def run_build_step() -> dict[str, Any]:
                    env = os.environ.copy()
                    env["FOUNDRY_PROFILE"] = profile

                    proc = await asyncio.create_subprocess_exec(
                        "forge",
                        "build",
                        cwd=foundry_root,
                        env=env,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    try:
                        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=300)
                    except TimeoutError as exc:
                        raise TimeoutError("Forge build timeout after 300s") from exc

                    stdout = stdout_bytes.decode()
                    stderr = stderr_bytes.decode()

                    if proc.returncode == 0:
                        solc_version = None
                        try:
                            solc_version = (
                                (foundry_toml.get("profile", {}) or {})
                                .get(profile, {})
                                .get("solc")
                            )
                        except Exception:
                            solc_version = None

                        abi, functions = self._extract_contract_metadata(foundry_root, contract.name)
                        classification = self._classify_contract(contract.name, functions)

                        asset = {
                            "type": "contract",
                            "value": contract.address,
                            "name": contract.name,
                            "chain_id": contract.chain_id,
                            "profile": profile,
                            "status": "compiled",
                            "metadata": {
                                "source_path": str(contract.source_path) if contract.source_path else None,
                                "verified": contract.verified,
                                "build_output": stdout,
                                "solc": solc_version,
                                "abi": abi,
                                "functions": functions,
                                "classification": classification,
                            },
                        }

                        if self.storage:
                            await self.storage.save_asset(asset)

                        return {"killed": False, "assets": [asset], "compiled": True, "address": contract.address}

                    if retry_helper.is_retryable_error(stderr):
                        raise RuntimeError(stderr or "retryable forge build failure")

                    raise NonRetryableCompilationError(
                        "Forge build failed",
                        stdout=stdout,
                        stderr=stderr,
                    )

                if self._check_kill_switch():
                    return {"killed": True, "assets": [], "compiled": False}

                try:
                    return await retry_helper.retry_with_backoff(
                        run_build_step,
                        context=f"forge_build_{contract.name}",
                    )
                except NonRetryableCompilationError as exc:
                    self._log_error(
                        "forge_build_failed",
                        contract=contract.name,
                        profile=profile,
                        stderr_msg=(exc.stderr or "Unknown error")[:500],
                    )
                    error_asset = {
                        "id": f"error-{uuid.uuid4().hex[:8]}",
                        "type": "compilation_error",
                        "value": contract.address,
                        "name": contract.name,
                        "chain_id": contract.chain_id,
                        "status": "compilation_failed",
                        "metadata": {
                            "error": exc.stderr,
                            "output": exc.stdout,
                        },
                    }
                    if self.storage:
                        await self.storage.save_asset(error_asset)
                    return {"killed": False, "assets": [error_asset], "compiled": False}
                except TimeoutError:
                    self._log_error(
                        "forge_build_timeout",
                        contract=contract.name,
                        profile=profile,
                        duration="300s",
                    )
                    error_asset = {
                        "id": f"error-{uuid.uuid4().hex[:8]}",
                        "type": "compilation_error",
                        "value": contract.address,
                        "name": contract.name,
                        "chain_id": contract.chain_id,
                        "status": "compilation_timeout",
                        "metadata": {
                            "error": "Forge build timeout after 300s",
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }
                    if self.storage:
                        await self.storage.save_asset(error_asset)
                    return {"killed": False, "assets": [error_asset], "compiled": False}
                except Exception as exc:
                    self._log_error(
                        "forge_build_exception",
                        contract=contract.name,
                        profile=profile,
                        exception=str(exc),
                        exception_type=type(exc).__name__,
                    )
                    error_asset = {
                        "id": f"error-{uuid.uuid4().hex[:8]}",
                        "type": "compilation_error",
                        "value": contract.address,
                        "name": contract.name,
                        "chain_id": contract.chain_id,
                        "status": "compilation_error",
                        "metadata": {
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }
                    if self.storage:
                        await self.storage.save_asset(error_asset)
                    return {"killed": False, "assets": [error_asset], "compiled": False}

        tasks = [asyncio.create_task(_compile_contract(contract)) for contract in contracts]
        compile_results = await asyncio.gather(*tasks)

        for res in compile_results:
            if res.get("killed"):
                return self._failure("Kill-switch activated during contract compilation")
            all_assets.extend(res.get("assets") or [])
            if res.get("compiled") and res.get("address"):
                compiled_contracts.append(res["address"])

        return self._success(
            message=f"Contract recon complete: {len(compiled_contracts)}/{len(contracts)} contracts compiled",
            data={
                "assets": all_assets,
                "contracts_count": len(contracts),
                "compiled_count": len(compiled_contracts),
                "failed_count": len(contracts) - len(compiled_contracts),
                "foundry_root": str(foundry_root),
            },
            next_actions=["static"],
        )

    def _classify_contract(self, name: str | None, functions: list[str]) -> dict[str, Any]:
        """Rudimentary protocol classification to inform downstream agents."""
        name = (name or "").lower()
        lower_functions = [f.lower() for f in functions or []]

        protocol_signatures = {
            "defi_vault": ["vault", "strategy", "oeth", "share", "rebalance", "deposit", "withdraw"],
            "amm": ["pool", "swap", "router", "pair", "liquidity", "exchange", "curve"],
            "lending": ["lend", "borrow", "collateral", "reserve", "interest", "rate", "loan"],
            "governance": ["gov", "dao", "proposal", "vote", "timelock", "delegate"],
        }

        def _matches_keywords(keywords: list[str]) -> bool:
            if any(k in name for k in keywords):
                return True
            return any(any(k in fn for k in keywords) for fn in lower_functions)

        protocol_type = "generic"
        indicators: list[str] = []
        for proto, keywords in protocol_signatures.items():
            if _matches_keywords(keywords):
                protocol_type = proto
                indicators = keywords
                break

        withdrawal_funcs = [fn for fn in lower_functions if any(w in fn for w in ["withdraw", "redeem", "claim"])]
        deposit_funcs = [fn for fn in lower_functions if any(w in fn for w in ["deposit", "mint", "stake", "supply"])]
        approval_funcs = [fn for fn in lower_functions if "approve" in fn or "permit" in fn]
        delegatecall_funcs = [fn for fn in lower_functions if "delegatecall" in fn]

        return {
            "protocol_type": protocol_type,
            "indicators": indicators,
            "function_count": len(functions),
            "withdrawal_functions": withdrawal_funcs,
            "deposit_functions": deposit_funcs,
            "approval_functions": approval_funcs,
            "delegatecall_functions": delegatecall_funcs,
        }
