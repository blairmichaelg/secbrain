"""Evidence and verification types for exploit confirmation."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse


class VerificationMethod(Enum):
    """How a vulnerability was verified."""

    REFLECTION = "reflection"
    TIMING = "timing"
    ERROR_RESPONSE = "error_response"
    STATUS_CHANGE = "status_change"
    COMMAND_OUTPUT = "command_output"
    MANUAL = "manual"
    NONE = "none"


@dataclass
class ResponseFingerprint:
    """Fingerprint of HTTP response (redacted for privacy)."""

    status_code: int
    content_length: int
    content_type: str | None = None
    key_headers: dict[str, str] = field(default_factory=dict)
    body_hash: str | None = None
    body_snippet: str | None = None

    @classmethod
    def from_http_response(cls, response: Any) -> ResponseFingerprint:
        """Construct a fingerprint from SecBrain HTTPResponse-like objects."""

        headers = getattr(response, "headers", {}) or {}
        content_type = None
        if isinstance(headers, dict):
            ct = headers.get("content-type") or headers.get("Content-Type")
            if ct:
                content_type = ct.split(";")[0]

        key_headers: dict[str, str] = {}
        if isinstance(headers, dict):
            for k in ["server", "x-powered-by", "x-aspnet-version", "x-runtime"]:
                if k in headers:
                    key_headers[k] = headers.get(k, "")
                elif k.title() in headers:
                    key_headers[k] = headers.get(k.title(), "")

        body = getattr(response, "body", None)
        if body is None:
            body = getattr(response, "content", b"")
        if body is None:
            body = b""
        if isinstance(body, str):
            body_bytes = body.encode("utf-8", errors="replace")
        else:
            body_bytes = body

        try:
            text = response.text
        except Exception:
            try:
                text = body_bytes.decode("utf-8", errors="replace")
            except Exception:
                text = ""

        body_hash = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None
        body_snippet = text[:200] if text else None

        return cls(
            status_code=int(getattr(response, "status_code", 0) or 0),
            content_length=len(body_bytes),
            content_type=content_type,
            key_headers=key_headers,
            body_hash=body_hash,
            body_snippet=body_snippet,
        )


@dataclass
class EvidenceBundle:
    """Single piece of evidence for a vulnerability."""

    evidence_id: str
    trace_id: str
    method: str
    url_path: str
    injected_parameter: str
    payload_hash: str
    baseline_response: ResponseFingerprint
    test_response: ResponseFingerprint
    verification_method: VerificationMethod
    test_passed: bool
    confidence_score: float
    tool_name: str = "exploit_agent"
    model_name: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""

        return {
            "evidence_id": self.evidence_id,
            "trace_id": self.trace_id,
            "method": self.method,
            "url_path": self.url_path,
            "injected_parameter": self.injected_parameter,
            "payload_hash": self.payload_hash,
            "baseline_response": asdict(self.baseline_response),
            "test_response": asdict(self.test_response),
            "verification_method": self.verification_method.value,
            "test_passed": self.test_passed,
            "confidence_score": self.confidence_score,
            "tool_name": self.tool_name,
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes,
        }


@dataclass
class VerificationResult:
    """Result of attempting to verify a vulnerability."""

    verified: bool
    confidence_score: float
    evidence: EvidenceBundle | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""

        return {
            "verified": self.verified,
            "confidence_score": self.confidence_score,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "error": self.error,
        }


def get_url_path(url: str) -> str:
    try:
        return urlparse(url).path or "/"
    except Exception:
        return "/"
