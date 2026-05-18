"""Runner orchestration for the reconnaissance agent."""

from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from secbrain.agents.base import AgentResult
from secbrain.agents.recon_agent_base import CompilationRetryHelper, NonRetryableCompilationError

if TYPE_CHECKING:
    from secbrain.agents.recon_agent_base import BaseReconAgent
    _Base = BaseReconAgent
else:
    _Base = object


class ReconRunnerMixin(_Base):
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
        live_hosts: list[dict[str, Any]] = []
        if subdomains:
            live_hosts = await self._probe_http([a["value"] for a in subdomains])
            all_assets.extend(live_hosts)

            # Extract technologies
            for host in live_hosts:
                techs = host.get("metadata", {}).get("technologies", [])
                technologies.extend(techs)

        # Run Nuclei vulnerability scanning on live hosts
        nuclei_findings: list[dict[str, Any]] = []
        if live_hosts:
            nuclei_findings = await self._scan_with_nuclei(
                [host["value"] for host in live_hosts]
            )
            # Add nuclei findings as assets
            all_assets.extend(nuclei_findings)

        # Research: understand the technology stack
        tech_research: dict[str, Any] = {}
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

    async def _recon_contracts(self, contracts: list) -> AgentResult:
        """Perform contract reconnaissance using Foundry."""
        self._log(f"Starting contract recon for {len(contracts)} contracts")

        all_assets: list[dict[str, Any]] = []
        compiled_contracts: list[str] = []
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

        foundry_toml: dict[str, Any] = {}
        try:
            foundry_toml_path = foundry_root_path / "foundry.toml"
            if foundry_toml_path.exists():
                foundry_toml = tomllib.loads(foundry_toml_path.read_text(encoding="utf-8"))
        except Exception:
            foundry_toml = {}

        retry_helper = CompilationRetryHelper(max_retries=3, base_wait=2.0, logger=self.logger)

        # Compile each contract using its profile
        async def _compile_contract(contract: Any) -> dict[str, Any]:
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

