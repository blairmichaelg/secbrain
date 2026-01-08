"""Stateful HTTP workflow runner with optional identity and artifact capture."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from secbrain.tools.http_client import HTTPResponse, SecBrainHTTPClient


@dataclass
class HTTPWorkflowStep:
    method: str
    url: str
    headers: dict[str, str] | None = None
    params: dict[str, Any] | None = None
    data: Any | None = None
    json_data: dict[str, Any] | None = None
    identity: str | None = None
    cookies: dict[str, str] | None = None
    label: str = ""


@dataclass
class HTTPWorkflowResult:
    steps: list[HTTPWorkflowStep] = field(default_factory=list)
    responses: list[HTTPResponse] = field(default_factory=list)
    success: bool = True
    errors: list[str] = field(default_factory=list)
    artifact_path: Path | None = None


class MultiStepHTTPWorkflow:
    """Run multiple HTTP steps sequentially with artifact capture."""

    def __init__(self, run_context: Any) -> None:
        self.run_context = run_context
        self.client = SecBrainHTTPClient(run_context)

    async def run(self, steps: list[HTTPWorkflowStep], *, artifact_name: str = "http_workflow.json") -> HTTPWorkflowResult:
        result = HTTPWorkflowResult(steps=steps)
        artifact_dir = self.run_context.logs_path
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / artifact_name

        for step in steps:
            resp = await self.client.request(
                method=step.method,
                url=step.url,
                headers=step.headers,
                params=step.params,
                data=step.data,
                json_data=step.json_data,
                identity_name=step.identity,
                cookies=step.cookies,
            )
            result.responses.append(resp)
            if not resp.success:
                result.success = False
                result.errors.append(resp.error or f"{step.method} {step.url} failed")
                # continue to collect full trace for reproducibility

        # Persist artifact
        serialized = []
        for step, resp in zip(steps, result.responses, strict=False):
            serialized.append(
                {
                    "step": {
                        "method": step.method,
                        "url": step.url,
                        "label": step.label,
                        "identity": step.identity,
                        "headers": step.headers or {},
                        "params": step.params or {},
                    },
                    "response": {
                        "status": resp.status_code,
                        "headers": resp.headers,
                        "body_snippet": resp.text[:1024] if resp.body else "",
                        "success": resp.success,
                        "error": resp.error,
                        "metadata": resp.metadata,
                    },
                }
            )

        artifact_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
        result.artifact_path = artifact_path
        return result
