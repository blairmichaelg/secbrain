"""Out-of-band (OOB) interaction client with interactsh-style backend."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from secbrain.core.context import RunContext


@dataclass
class OOBProbe:
    probe_id: str
    url: str
    dns: str
    token: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class OOBClient:
    """Interactsh-compatible OOB client."""

    def __init__(self, run_context: RunContext | None = None, endpoint: str | None = None):
        self.run_context = run_context
        self.endpoint = endpoint.rstrip("/") if endpoint else "https://interact.sh"
        self._client: httpx.AsyncClient | None = None

    def generate_probe(self, label: str | None = None) -> OOBProbe:
        probe_id = uuid.uuid4().hex
        token = label or probe_id[:6]
        host = f"{token}.oob.secbrain"
        url = f"http://{host}"
        dns = host
        return OOBProbe(probe_id=probe_id, url=url, dns=dns, token=token)

    async def check_interactions(self, probe_id: str) -> list[dict[str, Any]]:
        """Poll backend for interactions."""
        if self.run_context and self.run_context.dry_run:
            return [
                {
                    "probe_id": probe_id,
                    "type": "dns",
                    "host": f"dry-run-{probe_id}.oob.secbrain",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ]

        if not self._client:
            self._client = httpx.AsyncClient(timeout=10.0, verify=True)

        url = f"{self.endpoint}/poll"
        payload = {"probe_id": probe_id}
        try:
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("interactions", [])
        except Exception:
            return []

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


def create_oob_client(run_context: RunContext | None = None, endpoint: str | None = None) -> OOBClient:
    """Factory for OOB client."""
    return OOBClient(run_context, endpoint=endpoint)
