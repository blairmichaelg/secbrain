"""Foundry runner helper for forked exploit attempts."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
import textwrap
import tomllib
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


@dataclass
class FoundryRunResult:
    status: str
    profit_eth: float | None = None
    profit_tokens: dict[str, float] | None = None
    profit_breakdown: dict[str, float] | None = None
    gas_used: int | None = None
    execution_trace: str | None = None
    state_changes: dict[str, Any] | None = None
    revert_reason: str | None = None
    logs: list[Any] | None = None
    attempt_index: int | None = None
    rpc_url: str | None = None
    foundry_profile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FoundryRunner:
    """
    Minimal scaffold for running exploit attempts via Foundry.

    Current implementation is a stub to keep orchestration intact. It creates
    per-attempt directories and returns a placeholder result. Replace the
    stubbed body of `_execute_foundry_test` with real forge invocations.
    """

    def __init__(self, run_context, logger=None):
        self.run_context = run_context
        self.logger = logger
        self.workspace = Path(run_context.workspace_path) / "exploit_attempts"
        self.workspace.mkdir(parents=True, exist_ok=True)

        self.project_root: Path | None = None
        try:
            foundry_root = getattr(getattr(run_context, "scope", None), "foundry_root", None)
            if foundry_root:
                self.project_root = Path(foundry_root)
        except Exception:
            self.project_root = None

        self.test_root_rel = Path("test") / "secbrain"

        self._fallback_profile: str | None = None
        try:
            if self.project_root:
                toml_path = self.project_root / "foundry.toml"
                if toml_path.exists():
                    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
                    profiles = (data.get("profile") or {}) if isinstance(data, dict) else {}
                    if isinstance(profiles, dict):
                        for profile_name, cfg in profiles.items():
                            if profile_name == "default":
                                continue
                            if not isinstance(cfg, dict):
                                continue
                            solc = str(cfg.get("solc") or "")
                            if not solc:
                                continue
                            if solc.startswith("0.8") or solc.startswith("0.9"):
                                self._fallback_profile = str(profile_name)
                                break
        except Exception:
            self._fallback_profile = None

        tools_cfg = getattr(run_context, "tools_config", None)
        tools = getattr(tools_cfg, "tools", {}) if tools_cfg else {}
        self.forge_command = tools.get("forge_test_exploit", {}).get(
            "command",
            "forge test --match-test testExploit -vvvvv --json",
        )
        self.timeout = tools.get("forge_test_exploit", {}).get("timeout", 900)
        self._compile_cache_dir = Path(run_context.workspace_path) / ".secbrain_cache" / "compile"
        self._compile_cache_dir.mkdir(parents=True, exist_ok=True)

    async def _compile_with_cache(self, profile: str | None = None) -> None:
        """
        Stub compile hook to keep orchestration intact.

        In a full implementation, this should:
        - compute a cache key based on profile/solc/config
        - skip compile if cached artifacts exist
        - run `forge build` (or `forge test --match-path ...`) once per key
        For now, we no-op to avoid attribute errors.
        """
        return

    async def run_exploit_attempt(
        self,
        hypothesis: dict[str, Any],
        rpc_url: str | None,
        block_number: int | None = None,
        chain_id: int | None = None,
        attempt_index: int = 1,
        attack_body: str | None = None,
    ) -> FoundryRunResult:
        """
        Execute a single exploit attempt. Currently returns a stub result.
        """
        attempt_dir = self.workspace / f"{hypothesis.get('id','hyp')}" / f"attempt-{attempt_index}"
        attempt_dir.mkdir(parents=True, exist_ok=True)

        result = await self._execute_foundry_test(
            attempt_dir=attempt_dir,
            hypothesis=hypothesis,
            rpc_url=rpc_url,
            block_number=block_number,
            chain_id=chain_id,
            attempt_index=attempt_index,
            attack_body=attack_body or "",
        )

        # Persist raw result for later analysis
        (attempt_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2))
        return result

    async def _execute_foundry_test(
        self,
        attempt_dir: Path,
        hypothesis: dict[str, Any],
        rpc_url: str | None,
        block_number: int | None,
        chain_id: int | None,
        attempt_index: int,
        attack_body: str,
    ) -> FoundryRunResult:
        """
        Execute forge test and parse outcome. Falls back to stub in dry-run.
        """
        if self.run_context.dry_run:
            return FoundryRunResult(
                status="success",
                profit_eth=0.0,
                gas_used=None,
                execution_trace=None,
                revert_reason=None,
                logs=["[DRY-RUN] forge test skipped"],
                attempt_index=attempt_index,
            )

        if not self.project_root:
            # Fallback failure
            return FoundryRunResult(
                status="failed",
                profit_eth=None,
                profit_tokens=None,
                gas_used=None,
                execution_trace=None,
                revert_reason="missing_foundry_root",
                logs=["No scope.foundry_root configured; cannot run forge tests"],
                attempt_index=attempt_index,
            )
        if not self.project_root.exists():
            return FoundryRunResult(
                status="failed",
                profit_eth=None,
                gas_used=None,
                execution_trace=None,
                revert_reason="foundry_root_not_found",
                logs=[f"Foundry root does not exist: {self.project_root}"],
                attempt_index=attempt_index,
            )

        test_rel_path = self._render_foundry_files(
            attempt_dir=attempt_dir,
            hypothesis=hypothesis,
            rpc_url=rpc_url,
            block_number=block_number,
            chain_id=chain_id,
            attempt_index=attempt_index,
            attack_body=attack_body,
        )

        output_path = attempt_dir / "forge-output.json"
        args = self._build_command_args(
            rpc_url=rpc_url,
            block_number=block_number,
            match_path=test_rel_path,
        )
        stdout_path = attempt_dir / "stdout.txt"

        foundry_profile = hypothesis.get("foundry_profile")
        env = os.environ.copy()
        hyp_solc = hypothesis.get("solc")

        rpc_urls: list[str] = []
        if rpc_url:
            rpc_urls.append(str(rpc_url))
        try:
            scope_rpc_urls = getattr(getattr(self.run_context, "scope", None), "rpc_urls", None) or []
            rpc_urls.extend([str(u) for u in scope_rpc_urls if str(u)])
        except Exception:
            pass
        if not rpc_urls:
            rpc_urls = [None]

        profile_for_run: str | None = str(foundry_profile) if foundry_profile else None
        try:
            if hyp_solc and str(hyp_solc).startswith("0.5"):
                profile_for_run = self._fallback_profile
        except Exception:
            pass

        if profile_for_run:
            env["FOUNDRY_PROFILE"] = profile_for_run

        # Precompile with cache per profile/solc/config to reduce latency
        await self._compile_with_cache(profile_for_run)

        last_stdout = ""
        last_return_code: int | None = None
        used_rpc: str | None = None
        for rpc_candidate in rpc_urls:
            used_rpc = rpc_candidate
            args = self._build_command_args(
                rpc_url=rpc_candidate,
                block_number=block_number,
                match_path=test_rel_path,
            )

            max_retries = 3 if rpc_candidate else 1
            for retry_idx in range(max_retries):
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *args,
                        cwd=self.project_root,
                        env=env,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    try:
                        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                    except TimeoutError:
                        proc.kill()
                        last_stdout = "forge test timeout"
                        last_return_code = 124
                        break

                    last_return_code = int(proc.returncode or 0)
                    last_stdout = stdout_bytes.decode(errors="replace")

                    if (
                        rpc_candidate
                        and last_return_code
                        and (
                            "could not instantiate forked environment" in last_stdout.lower()
                            or "error sending request" in last_stdout.lower()
                            or ("provider" in last_stdout.lower() and "error" in last_stdout.lower())
                        )
                        and retry_idx < (max_retries - 1)
                    ):
                        await asyncio.sleep(2**retry_idx)
                        continue

                    break

                except FileNotFoundError:
                    return FoundryRunResult(
                        status="failed",
                        profit_eth=None,
                        profit_tokens=None,
                        gas_used=None,
                        execution_trace=None,
                        revert_reason="forge_not_found",
                        logs=["forge binary not found on PATH"],
                        attempt_index=attempt_index,
                        rpc_url=used_rpc,
                        foundry_profile=profile_for_run,
                    )

            if not rpc_candidate:
                break

            if last_return_code is not None and last_return_code == 0:
                break

        stdout = last_stdout
        stdout_path.write_text(stdout)
        output_path.write_text(stdout)

        parsed = self._parse_forge_output(stdout, return_code=(last_return_code or 1), json_path=output_path)
        return FoundryRunResult(
            status=parsed["status"],
            profit_eth=parsed["profit_eth"],
            profit_tokens=parsed.get("profit_tokens"),
            profit_breakdown=parsed.get("profit_breakdown"),
            gas_used=parsed["gas_used"],
            execution_trace=stdout,
            state_changes=parsed.get("state_changes"),
            revert_reason=parsed["revert_reason"],
            logs=parsed["logs"],
            attempt_index=attempt_index,
            rpc_url=used_rpc,
            foundry_profile=profile_for_run,
        )

    def _build_command_args(
        self,
        rpc_url: str | None,
        block_number: int | None,
        match_path: Path | None = None,
    ) -> list[str]:
        base = shlex.split(self.forge_command, posix=os.name != "nt")
        extras: list[str] = []
        if match_path:
            extras.extend(["--match-path", str(match_path.as_posix())])
        if rpc_url:
            extras.extend(["--fork-url", rpc_url])
        if block_number:
            extras.extend(["--fork-block-number", str(block_number)])
        return base + extras

    def _render_foundry_files(
        self,
        attempt_dir: Path,
        hypothesis: dict[str, Any],
        rpc_url: str | None,
        block_number: int | None,
        chain_id: int | None,
        attempt_index: int,
        attack_body: str,
    ) -> Path:
        """Write a minimal Exploit.t.sol harness into the Foundry project and copy it into attempt_dir."""
        foundry_toml = "[profile.default]\n"
        # Favor via-ir to avoid stack-too-deep in generated harnesses
        foundry_toml += "via_ir = true\n"
        foundry_toml += "optimizer = true\n"
        foundry_toml += "optimizer_runs = 200\n"
        # Prefer per-profile solc if available in instascope project; do not override here
        if rpc_url:
            foundry_toml += f'eth_rpc_url = "{rpc_url}"\n'
        if block_number:
            foundry_toml += f"block_number = {block_number}\n"
        if chain_id:
            foundry_toml += f"chain_id = {chain_id}\n"
        (attempt_dir / "foundry.toml").write_text(foundry_toml)

        name = hypothesis.get("vuln_type", "Exploit").title().replace(" ", "")

        hyp_id = hypothesis.get("id", "hyp")

        contract_address = hypothesis.get("contract_address")

        normalized_address = self._normalize_address(contract_address)
        address_expr = self._address_expr(normalized_address)
        address_payable_expr = self._address_expr(normalized_address, payable=True)

        profit_tokens = hypothesis.get("profit_tokens")
        if not isinstance(profit_tokens, list):
            try:
                profit_tokens = getattr(getattr(self.run_context, "scope", None), "profit_tokens", None) or []
            except Exception:
                profit_tokens = []

        token_specs: list[dict[str, Any]] = []
        for t in profit_tokens or []:
            if not isinstance(t, dict):
                continue
            addr = self._normalize_address(t.get("address") or "")
            if not addr:
                continue
            num, den = self._multiplier_ratio(t.get("eth_equiv_multiplier"))
            token_specs.append(
                {
                    "symbol": str(t.get("symbol") or "TOKEN"),
                    "address": addr,
                    "decimals": int(t.get("decimals") or 18),
                    "mult_num": num,
                    "mult_den": den,
                    "equiv_source": t.get("eth_equiv_source") or t.get("eth_equiv_method"),
                }
            )

        # Minimize locals to avoid stack-too-deep; drop token accounting in harness
        token_interface = ""
        norm_helper_block = ""
        token_balance_init_block = ""
        token_total_before_block = ""
        token_balance_final_block = ""
        token_total_after_block = ""
        token_profit_calc_block = ""
        token_profit_logs_block = ""
        profit_assert_block = ""

        is_forked = bool(rpc_url)

        def _indent_block(block: str, spaces: int = 8) -> str:
            block = (block or "").strip()
            if not block:
                return ""
            return textwrap.indent(block + "\n", " " * spaces)

        attack_block = attack_body or "// TODO: add exploit logic"
        attack_block = _indent_block(attack_block)

        # Simpler success condition to reduce locals
        success_suffix = '        assertTrue(success || profit > 0, "Exploit failed");\n'

        token_interface_decl = token_interface.strip()
        if token_interface_decl:
            token_interface_decl = token_interface_decl + "\n"

        exploit_test = textwrap.dedent(
            f"""
            // SPDX-License-Identifier: UNLICENSED
            pragma solidity >=0.8.0 <0.9.0;

            import "forge-std/Test.sol";
            import "forge-std/console2.sol";
            {token_interface_decl}
            contract Exploit{name}Test is Test {{
                address constant TARGET = {address_expr};
                address payable constant TARGET_PAYABLE = {address_payable_expr};
{norm_helper_block if norm_helper_block else ""}
                struct FlashloanRequest {{
                    address lender;
                    address asset;
                    uint256 amount;
                    bytes data;
                }}

                function _requestFlashloan(FlashloanRequest memory req) internal {{
                    console2.log("Flashloan stub lender:", req.lender);
                    console2.log("Flashloan stub asset:", req.asset);
                    console2.log("Flashloan stub amount:", req.amount);
                    console2.log("Flashloan stub params(bytes):", uint256(req.data.length));
                }}

                function setUp() public {{
                    vm.deal(address(this), 1_000 ether);
                }}

                function testExploit() public {{
                    uint256 initialBalance = address(this).balance;
        bool success = false;
        // ATTACK_BODY_START
{attack_block if attack_block else ""}        // ATTACK_BODY_END
        uint256 finalBalance = address(this).balance;
        uint256 profit = finalBalance > initialBalance ? (finalBalance - initialBalance) : 0;
        console2.log("Profit (ETH):", profit);
{success_suffix if success_suffix else ""}
                }}
            }}
            """
        ).strip() + "\n"

        # Write copy for inspection
        (attempt_dir / "Exploit.t.sol").write_text(exploit_test)

        # Write into the target Foundry project so forge can compile with its dependencies
        project_test_dir = self.project_root / self.test_root_rel
        project_test_dir.mkdir(parents=True, exist_ok=True)
        test_filename = f"SecBrainExploit_{hyp_id}_{attempt_index}.t.sol"
        test_rel_path = self.test_root_rel / test_filename
        (self.project_root / test_rel_path).write_text(exploit_test)
        return test_rel_path

    def _normalize_address(self, addr: Any) -> str | None:
        if not addr:
            return None
        s = str(addr).strip().strip('"').strip("'")
        if not s.startswith("0x"):
            return None
        h = s[2:]
        if len(h) != 40:
            return None
        if not re.fullmatch(r"[0-9a-fA-F]{40}", h):
            return None
        return "0x" + h.lower()

    def _address_expr(self, normalized_addr: str | None, payable: bool = False) -> str:
        if not normalized_addr:
            return "payable(address(0))" if payable else "address(0)"
        h = normalized_addr[2:]
        base = f"address(bytes20(hex\"{h}\"))"
        return f"payable({base})" if payable else base

    def _multiplier_ratio(self, value: Any) -> tuple[int, int]:
        if value is None:
            return (1, 1)
        if isinstance(value, dict):
            num = int(value.get("numerator") or value.get("num") or 1)
            den = int(value.get("denominator") or value.get("den") or 1)
            if den == 0:
                den = 1
            return (num, den)
        try:
            if isinstance(value, int | float):
                frac = Fraction(value).limit_denominator(10**6)
                return (frac.numerator, frac.denominator)
            if isinstance(value, str):
                s = value.strip()
                if not s:
                    return (1, 1)
                if "/" in s:
                    num_str, den_str = s.split("/", 1)
                    num = int(float(num_str.strip()))
                    den = int(float(den_str.strip()) or 1)
                    if den == 0:
                        den = 1
                    return (num, den)
                frac = Fraction(float(s)).limit_denominator(10**6)
                return (frac.numerator, frac.denominator)
        except Exception:
            return (1, 1)
        return (1, 1)

    def _parse_forge_output(self, stdout: str, return_code: int, json_path: Path | None = None) -> dict[str, Any]:
        """Parse forge output for profit, gas, and revert signals."""
        status = "failed" if return_code else "success"
        profit_eth = None
        profit_tokens: dict[str, float] = {}
        profit_breakdown: dict[str, float] = {}
        gas_used = None
        revert_reason = None
        state_changes: dict[str, Any] = {}

        # Regex scan of stdout
        profit_equiv_match = re.search(
            r"Profit\s*\(ETH-equivalent\)\s*:\s*(-?[0-9]+\.?[0-9]*)",
            stdout,
            re.IGNORECASE,
        )
        if profit_equiv_match:
            try:
                profit_eth = float(profit_equiv_match.group(1))
            except ValueError:
                profit_eth = None

        if profit_eth is None:
            profit_match = re.search(r"Profit\s*\(ETH\)\s*:\s*([0-9]+\.?[0-9]*)", stdout, re.IGNORECASE)
            if profit_match:
                try:
                    profit_eth = float(profit_match.group(1))
                except ValueError:
                    profit_eth = None

        # If profit was logged as a raw int/uint256 (common in solidity logs), treat large magnitudes as wei.
        if profit_eth is not None and abs(profit_eth) > 1e9:
            profit_eth = profit_eth / 1e18

        revert_match = re.search(r"revert(?: reason)?:\s*(.+)", stdout, re.IGNORECASE)
        if revert_match:
            revert_reason = revert_match.group(1).strip()

        gas_match = re.search(r"gas used[:\s]+([0-9]+)", stdout, re.IGNORECASE)
        if gas_match:
            try:
                gas_used = int(gas_match.group(1))
            except ValueError:
                gas_used = None

        # JSON parse (forge --json)
        json_obj = None
        if json_path and json_path.exists():
            try:
                json_obj = json.loads(json_path.read_text())
            except Exception:
                json_obj = None
        if json_obj is None:
            try:
                json_obj = json.loads(stdout)
            except Exception:
                json_obj = None

        if json_obj:
            try:
                def _iter_testcases(obj: Any):
                    if isinstance(obj, dict):
                        if "test_results" in obj and isinstance(obj.get("test_results"), dict):
                            for _k, v in obj.get("test_results", {}).items():
                                yield v
                        for v in obj.values():
                            yield from _iter_testcases(v)
                    elif isinstance(obj, list):
                        for v in obj:
                            yield from _iter_testcases(v)

                for tc in _iter_testcases(json_obj):
                    if not isinstance(tc, dict):
                        continue
                    decoded = tc.get("decoded_logs") or []
                    if not isinstance(decoded, list):
                        decoded = []
                    state_changes.update(tc.get("state_changes") or {})
                    for line in decoded:
                        if not isinstance(line, str):
                            continue
                        m_equiv = re.search(
                            r"Profit\s*\(ETH-equivalent\)\s*:\s*(-?[0-9]+\.?[0-9]*)",
                            line,
                            re.IGNORECASE,
                        )
                        if m_equiv:
                            profit_eth = float(m_equiv.group(1))
                            if abs(profit_eth) > 1e9:
                                profit_eth = profit_eth / 1e18
                        m_eth = re.search(r"Profit\s*\(ETH\)\s*:\s*([0-9]+\.?[0-9]*)", line, re.IGNORECASE)
                        if m_eth and profit_eth is None:
                            profit_eth = float(m_eth.group(1))
                            if abs(profit_eth) > 1e9:
                                profit_eth = profit_eth / 1e18
                        m_tok = re.search(r"Profit\s+([A-Za-z0-9_\-]{1,16})\s*:\s*([0-9]+\.?[0-9]*)", line)
                        if m_tok:
                            profit_tokens[m_tok.group(1)] = float(m_tok.group(2))
                            profit_breakdown[m_tok.group(1)] = float(m_tok.group(2))

                    if tc.get("status") == "Failure":
                        status = "failed"
                        revert_reason = revert_reason or tc.get("reason")
            except Exception:
                pass

        if status == "success" and profit_eth is None:
            profit_eth = 0.0

        return {
            "status": status,
            "profit_eth": profit_eth,
            "profit_tokens": profit_tokens or {},
            "profit_breakdown": profit_breakdown or (profit_tokens or {}),
            "gas_used": gas_used,
            "revert_reason": revert_reason,
            "logs": stdout.splitlines()[-50:],
            "state_changes": state_changes or {},
        }
