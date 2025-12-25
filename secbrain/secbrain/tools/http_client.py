"""HTTP client with scope enforcement, rate limiting, and kill-switch for SecBrain."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from secbrain.core.context import RunContext

from secbrain.core.approval import ApprovalRequest, new_request_id


@dataclass
class HTTPResponse:
    """Structured HTTP response."""

    status_code: int
    headers: dict[str, str]
    body: bytes
    url: str
    method: str
    duration_ms: float
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.error is None and 200 <= self.status_code < 400

    @property
    def text(self) -> str:
        try:
            return self.body.decode("utf-8")
        except UnicodeDecodeError:
            return self.body.decode("latin-1")

    def json(self) -> Any:
        import json
        return json.loads(self.body)


class SecBrainHTTPClient:
    """
    HTTP client with security controls.

    Features:
    - Scope enforcement (hosts, methods)
    - Rate limiting
    - Kill-switch checking
    - Request/response logging (metadata only by default)
    """

    def __init__(
        self,
        run_context: RunContext,
        timeout: float = 30.0,
        max_redirects: int = 5,
        verify_ssl: bool = True,
        max_retries: int = 2,
        backoff_factor: float = 0.5,
        retry_statuses: Iterable[int] | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.run_context = run_context
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.verify_ssl = verify_ssl

        self.client = client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            max_redirects=max_redirects,
            verify=verify_ssl,
        )

        self._request_count = 0
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_statuses = set(retry_statuses or {500, 502, 503, 504, 429})

    def _check_preconditions(self, url: str, method: str) -> str | None:
        """Check all preconditions before making a request. Returns error message if failed."""
        # Kill-switch check
        if self.run_context.is_killed():
            return "Kill-switch activated"

        # Scope check
        if not self.run_context.check_scope(url):
            return f"URL not in scope: {url}"

        # Method check
        allowed_methods = self.run_context.scope.allowed_methods
        if method.upper() not in [m.upper() for m in allowed_methods]:
            return f"Method not allowed: {method}"

        # ACL check
        if not self.run_context.check_tool_acl("http_client"):
            return "HTTP client not allowed in current phase"

        return None

    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_data: dict[str, Any] | None = None,
        identity_name: str | None = None,
        cookies: dict[str, str] | None = None,
    ) -> HTTPResponse:
        """Make an HTTP request with all safety checks."""
        start_time = time.time()

        # Check preconditions
        error = self._check_preconditions(url, method)
        if error:
            return HTTPResponse(
                status_code=0,
                headers={},
                body=b"",
                url=url,
                method=method,
                duration_ms=0,
                error=error,
            )

        # Merge identity context if provided
        if identity_name:
            identity = self.run_context.identities.get(identity_name)
            headers, cookies = identity.apply(headers=headers, cookies=cookies)

        # Dry-run mode
        if self.run_context.dry_run:
            return HTTPResponse(
                status_code=200,
                headers={"x-dry-run": "true"},
                body=b'{"dry_run": true}',
                url=url,
                method=method,
                duration_ms=0,
                metadata={"dry_run": True, "identity": identity_name},
            )

        if self.run_context.requires_approval("http_client") and not self.run_context.auto_approve:
            approval = await self.run_context.approval_manager.request_approval(
                ApprovalRequest(
                    request_id=new_request_id(),
                    tool_name="http_client",
                    operation=f"{method.upper()} {url}",
                    risk_level="high",
                    timestamp=datetime.now(UTC),
                )
            )
            if not approval.approved:
                return HTTPResponse(
                    status_code=0,
                    headers={},
                    body=b"",
                    url=url,
                    method=method,
                    duration_ms=0,
                    error=f"Approval denied: http_client ({approval.reason})",
                )

        # Acquire rate limit
        await self.run_context.acquire_rate_limit("http_client")

        attempt = 0
        while True:
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    cookies=cookies,
                )

                duration_ms = (time.time() - start_time) * 1000

                # Record the call
                self.run_context.record_tool_call("http_client")
                self._request_count += 1

                if response.status_code in self.retry_statuses and attempt < self.max_retries:
                    await self._sleep_with_backoff(attempt)
                    attempt += 1
                    continue

                return HTTPResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.content,
                    url=str(response.url),
                    method=method,
                    duration_ms=duration_ms,
                    metadata={
                        "identity": identity_name,
                        "retries": attempt,
                    }
                    if identity_name or attempt
                    else {"retries": attempt},
                )

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    await self._sleep_with_backoff(attempt)
                    attempt += 1
                    continue

                duration_ms = (time.time() - start_time) * 1000
                return HTTPResponse(
                    status_code=0,
                    headers={},
                    body=b"",
                    url=url,
                    method=method,
                    duration_ms=duration_ms,
                    error=str(e),
                    metadata={"retries": attempt},
                )

    async def get(self, url: str, **kwargs: Any) -> HTTPResponse:
        """HTTP GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> HTTPResponse:
        """HTTP POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> HTTPResponse:
        """HTTP PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> HTTPResponse:
        """HTTP DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> HTTPResponse:
        """HTTP HEAD request."""
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> HTTPResponse:
        """HTTP OPTIONS request."""
        return await self.request("OPTIONS", url, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @property
    def request_count(self) -> int:
        """Number of requests made."""
        return self._request_count

    async def _sleep_with_backoff(self, attempt: int) -> None:
        """Sleep using exponential backoff with jitter."""
        base = self.backoff_factor * (2**attempt)
        jitter = random.uniform(0, base / 2)
        await asyncio.sleep(base + jitter)


async def create_http_client(run_context: RunContext) -> SecBrainHTTPClient:
    """Create an HTTP client for the given run context."""
    return SecBrainHTTPClient(run_context)
