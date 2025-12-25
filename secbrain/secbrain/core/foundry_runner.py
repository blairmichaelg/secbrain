"""Utilities for parsing Foundry forge output."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class ForgeOutputParser:
    """Parse forge stdout/JSON for profit, gas, and state-change data."""

    _PROFIT_EQUIV_RE = re.compile(r"Profit\s*\(ETH-equivalent\)\s*:\s*(-?[0-9]+\.?[0-9]*)", re.IGNORECASE)
    _PROFIT_ETH_RE = re.compile(r"Profit\s*\(ETH\)\s*:\s*(-?[0-9]+\.?[0-9]*)", re.IGNORECASE)
    _TOKEN_RE = re.compile(r"Profit\s+([A-Za-z0-9_\-]{1,32})\s*:\s*(-?[0-9]+\.?[0-9]*)")
    _GAS_RE = re.compile(r"gas used[:\s]+([0-9]+)", re.IGNORECASE)
    _REVERT_RE = re.compile(r"revert(?: reason)?:\s*(.+)", re.IGNORECASE)

    @classmethod
    def parse_profit(cls, stdout: str) -> float | None:
        """Parse ETH/ETH-equivalent profit value from stdout."""
        text = stdout or ""
        match = cls._PROFIT_EQUIV_RE.search(text) or cls._PROFIT_ETH_RE.search(text)
        if not match:
            return None
        return cls._normalize_large_value(match.group(1))

    @classmethod
    def parse_tokens(cls, stdout: str) -> dict[str, float]:
        """Parse per-token profit logs."""
        tokens: dict[str, float] = {}
        for match in cls._TOKEN_RE.finditer(stdout or ""):
            symbol = match.group(1)
            try:
                tokens[symbol] = float(match.group(2))
            except ValueError:
                continue
        return tokens

    @classmethod
    def parse(
        cls,
        stdout: str,
        return_code: int,
        json_path: Path | None = None,
    ) -> dict[str, Any]:
        """Parse forge stdout/JSON into a structured summary."""
        status = "failed" if return_code else "success"
        profit_eth = cls.parse_profit(stdout)
        profit_tokens = cls.parse_tokens(stdout)
        profit_breakdown = dict(profit_tokens)
        revert_reason = cls._extract_revert(stdout)
        gas_used = cls._extract_gas(stdout)
        state_changes: dict[str, Any] = {}

        json_obj = cls._load_json(stdout, json_path)
        if json_obj is not None:
            json_status, json_profit, tokens_from_json, state_changes_json = cls._parse_json(json_obj)
            if json_status:
                status = json_status
            if json_profit is not None:
                profit_eth = json_profit
            if tokens_from_json:
                profit_tokens.update(tokens_from_json)
                profit_breakdown.update(tokens_from_json)
            if state_changes_json:
                state_changes.update(state_changes_json)

        if status == "success" and profit_eth is None:
            profit_eth = 0.0

        return {
            "status": status,
            "profit_eth": profit_eth,
            "profit_tokens": profit_tokens,
            "profit_breakdown": profit_breakdown,
            "gas_used": gas_used,
            "revert_reason": revert_reason,
            "logs": stdout.splitlines()[-50:],
            "state_changes": state_changes,
        }

    @staticmethod
    def _normalize_large_value(value: str | float) -> float:
        """Scale large wei-style values down to ETH."""
        try:
            val = float(value)
        except (TypeError, ValueError):
            return 0.0
        if abs(val) > 1e9:
            return val / 1e18
        return val

    @classmethod
    def _extract_gas(cls, stdout: str) -> int | None:
        match = cls._GAS_RE.search(stdout or "")
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    @classmethod
    def _extract_revert(cls, stdout: str) -> str | None:
        match = cls._REVERT_RE.search(stdout or "")
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _load_json(stdout: str, json_path: Path | None) -> Any:
        """Load forge --json output if available."""
        if json_path and json_path.exists():
            try:
                return json.loads(json_path.read_text())
            except Exception:
                return None
        try:
            return json.loads(stdout)
        except Exception:
            return None

    @classmethod
    def _parse_json(
        cls, json_obj: Any
    ) -> tuple[str | None, float | None, dict[str, float], dict[str, Any]]:
        """Extract status, profit, tokens, and state changes from forge JSON."""
        status = None
        profit_eth = None
        tokens: dict[str, float] = {}
        state_changes: dict[str, Any] = {}

        if isinstance(json_obj, dict) and "status" in json_obj:
            status = json_obj.get("status")

        for testcase in cls._iter_testcases(json_obj):
            if not isinstance(testcase, dict):
                continue
            decoded_logs = testcase.get("decoded_logs") or []
            for line in decoded_logs if isinstance(decoded_logs, Iterable) else []:
                if not isinstance(line, str):
                    continue
                profit_match = cls._PROFIT_EQUIV_RE.search(line) or cls._PROFIT_ETH_RE.search(line)
                if profit_match:
                    profit_eth = cls._normalize_large_value(profit_match.group(1))
                token_match = cls._TOKEN_RE.search(line)
                if token_match:
                    try:
                        tokens[token_match.group(1)] = float(token_match.group(2))
                    except ValueError:
                        continue
            state_changes.update(testcase.get("state_changes") or {})
            if testcase.get("status") == "Failure" and not status:
                status = "failed"
            if testcase.get("reason") and not state_changes.get("revert_reason"):
                state_changes["revert_reason"] = testcase.get("reason")

        return status, profit_eth, tokens, state_changes

    @staticmethod
    def _iter_testcases(obj: Any) -> Iterable[dict[str, Any]]:
        if isinstance(obj, dict):
            test_results = obj.get("test_results")
            if isinstance(test_results, dict):
                for value in test_results.values():
                    if isinstance(value, dict):
                        yield value
            for value in obj.values():
                yield from ForgeOutputParser._iter_testcases(value)
        elif isinstance(obj, list):
            for item in obj:
                yield from ForgeOutputParser._iter_testcases(item)
        return []
