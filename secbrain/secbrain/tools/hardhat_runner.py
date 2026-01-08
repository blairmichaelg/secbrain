"""Hardhat runner stub for exploit attempts (parity with FoundryRunner)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class HardhatRunResult:
    status: str
    profit_eth: float | None = None
    gas_used: int | None = None
    execution_trace: str | None = None
    revert_reason: str | None = None
    logs: list[Any] | None = None
    attempt_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HardhatRunner:
    """
    Minimal placeholder runner to mirror FoundryRunner contract.

    Currently not implemented; use FoundryRunner for execution. This stub exists
    to keep API surface compatible if you decide to add Hardhat parity.
    """

    def __init__(self, run_context: Any, logger: Any = None) -> None:
        self.run_context = run_context
        self.logger = logger
        self.workspace = Path(run_context.workspace_path) / "hardhat_attempts"
        self.workspace.mkdir(parents=True, exist_ok=True)

    async def run_exploit_attempt(
        self,
        hypothesis: dict[str, Any],
        rpc_url: str | None,
        block_number: int | None = None,
        chain_id: int | None = None,
        attempt_index: int = 1,
        attack_body: str | None = None,
    ) -> HardhatRunResult:
        """
        Stubbed executor: returns not_implemented. Extend to call hardhat test.
        """
        return HardhatRunResult(
            status="not_implemented",
            profit_eth=None,
            gas_used=None,
            execution_trace=None,
            revert_reason="hardhat_runner_stub",
            logs=["Hardhat runner not yet implemented; use FoundryRunner."],
            attempt_index=attempt_index,
        )
