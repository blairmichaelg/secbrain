"""Base utilities for the reconnaissance agent."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypeVar

from secbrain.agents.base import BaseAgent
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
        logger: Any = None,
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


class BaseReconAgent(BaseAgent):
    """
    Recon agent base.

    Shared state and helper methods for web and contract reconnaissance.
    """

    name = "recon"
    phase = "recon"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

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
