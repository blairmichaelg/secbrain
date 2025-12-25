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

from secbrain.core.foundry_runner import ForgeOutputParser


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
                            if solc.startswith(("0.8", "0.9")):
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

    async def _compile_with_cache(self, profile: str | None) -> None:
        """Precompile contracts per profile to reduce test latency."""
        if not self.project_root:
            return

        cache_key = profile or "default"
        cache_marker = self._compile_cache_dir / f"{cache_key}.compiled"
        if cache_marker.exists():
            return

        try:
            args = ["forge", "build"]
            env = os.environ.copy() if profile else None
            if profile and env is not None:
                env["FOUNDRY_PROFILE"] = profile

            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=self.project_root,
                env=env,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.communicate(), timeout=120)
            if proc.returncode == 0:
                cache_marker.touch()
        except Exception:
            # If compilation fails here, forge test will attempt compilation again.
            pass

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
                logs=["Nd; cannot run forge tests"],
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

        parsed = ForgeOutputParser.parse(stdout, return_code=(last_return_code or 1), json_path=output_path)
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

        token_interface = ""
        token_balance_init = ""
        token_balance_final = ""
        token_profit_calc = ""
        token_profit_logs = ""
        token_norm_helpers = ""
        token_total_before = ""
        token_total_after = ""

        if token_specs:
            token_interface = "interface IERC20 { function balanceOf(address) external view returns (uint256); }\n"
            token_norm_helpers = textwrap.dedent(
                """
                function _to18(uint256 amount, uint8 decimals) internal pure returns (uint256) {
                    if (decimals == 18) return amount;
                    if (decimals < 18) return amount * (10 ** (18 - decimals));
                    return amount / (10 ** (decimals - 18));
                }

                function _applyMultiplier(uint256 amount, uint256 numerator, uint256 denominator) internal pure returns (uint256) {
                    if (denominator == 0) return amount;
                    if (numerator == 0) return 0;
                    return (amount * numerator) / denominator;
                }
                """
            ).strip()
            for idx, spec in enumerate(token_specs):
                sym = spec["symbol"].replace('"', "")
                addr_expr = self._address_expr(spec["address"])
                token_balance_init += (
                    f"uint256 init_{idx} = IERC20({addr_expr}).balanceOf(address(this));\n"
                )
                token_balance_final += (
                    f"uint256 fin_{idx} = IERC20({addr_expr}).balanceOf(address(this));\n"
                )
                token_profit_calc += (
                    f"uint256 profit_{idx} = fin_{idx} > init_{idx} ? (fin_{idx} - init_{idx}) : 0;\n"
                )
                token_profit_logs += f"console2.log(\"Profit {sym}:\", profit_{idx});\n"
                dec = int(spec.get("decimals") or 18)
                if dec < 0:
                    dec = 18
                if dec > 255:
                    dec = 18
                mult_num = int(spec.get("mult_num") or 1)
                mult_den = int(spec.get("mult_den") or 1)
                token_total_before += f"totalBefore = totalBefore + _applyMultiplier(_to18(init_{idx}, uint8({dec})), {mult_num}, {mult_den});\n"
                token_total_after += f"totalAfter = totalAfter + _applyMultiplier(_to18(fin_{idx}, uint8({dec})), {mult_num}, {mult_den});\n"

        is_forked = bool(rpc_url)
        profit_assert = 'require(profitEquiv > 0, "Exploit failed: insufficient profit");' if is_forked else ""

        def _indent_block(block: str, spaces: int = 8) -> str:
            block = (block or "").strip()
            if not block:
                return ""
            return textwrap.indent(block + "\n", " " * spaces)

        norm_helper_block = _indent_block(token_norm_helpers, spaces=4)
        if norm_helper_block:
            norm_helper_block = "\n" + norm_helper_block.rstrip() + "\n"

        token_balance_init_block = _indent_block(token_balance_init)
        token_total_before_block = _indent_block(token_total_before)
        token_balance_final_block = _indent_block(token_balance_final)
        token_total_after_block = _indent_block(token_total_after)
        token_profit_calc_block = _indent_block(token_profit_calc)
        token_profit_logs_block = _indent_block(token_profit_logs)
        profit_assert_block = _indent_block(profit_assert) if profit_assert else ""

        # Sanitize attack_body to remove markdown fences that break Solidity compilation
        sanitized_attack_body = self._sanitize_attack_body(attack_body or "// TODO: add exploit logic")
        attack_block = _indent_block(sanitized_attack_body)

        success_suffix = ""
        if not is_forked:
            success_suffix = '        assertTrue(success, "Exploit failed: success flag not set");\n'

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
{token_balance_init_block if token_balance_init_block else ""}        uint256 totalBefore = initialBalance;
{token_total_before_block if token_total_before_block else ""}        bool success = false;
        // ATTACK_BODY_START
{attack_block if attack_block else ""}        // ATTACK_BODY_END
        uint256 finalBalance = address(this).balance;
        uint256 profit = finalBalance > initialBalance ? (finalBalance - initialBalance) : 0;
        console2.log("Profit (ETH):", profit);
{token_balance_final_block if token_balance_final_block else ""}        uint256 totalAfter = finalBalance;
{token_total_after_block if token_total_after_block else ""}        int256 profitEquiv = int256(totalAfter) - int256(totalBefore);
        console2.log("Profit (ETH-equivalent):", profitEquiv);
{token_profit_calc_block if token_profit_calc_block else ""}{token_profit_logs_block if token_profit_logs_block else ""}{profit_assert_block if profit_assert_block else ""}{success_suffix if success_suffix else ""}
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

    def _sanitize_attack_body(self, text: str) -> str:
        """Remove markdown/code fences and backticks that break Solidity compilation.

        This prevents compilation errors from injected markdown fences like:
        ```solidity
        // code here
        ```

        Args:
            text: Raw attack body that may contain markdown fences

        Returns:
            Sanitized text with all markdown fences and backticks removed
        """
        if not text:
            return ""
        # Strip fenced code blocks like ```solidity ... ``` and standalone backticks
        body = re.sub(r"```[\w-]*", "", text)
        body = body.replace("```", "")
        body = body.replace("`", "")
        return body.strip()

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

