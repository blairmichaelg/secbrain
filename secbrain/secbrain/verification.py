"""Verification and evidence utilities for SecBrain.

This module provides lightweight, runtime verification helpers that can be used by
agents (primarily ExploitAgent) to attach structured evidence and confidence.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


@dataclass(frozen=True)
class EvidenceBundle:
    """Immutable evidence payload suitable for storage in findings."""

    verifier: str
    target: str
    vuln_type: str
    created_at: str
    observations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": self.verifier,
            "target": self.target,
            "vuln_type": self.vuln_type,
            "created_at": self.created_at,
            "observations": self.observations,
        }


@dataclass(frozen=True)
class VerificationResult:
    """Result of verifying a vulnerability signal."""

    success: bool
    confidence: float
    reason: str
    evidence: EvidenceBundle | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence": self.evidence.to_dict() if self.evidence else None,
        }


class ExploitVerifier(Protocol):
    """Verifier protocol used to validate exploit/test outcomes."""

    name: str

    def verify(
        self,
        *,
        vuln_type: str,
        target: str,
        results: list[dict[str, Any]],
    ) -> VerificationResult: ...


class ReflectedXSSVerifier:
    name = "reflected_xss"

    def verify(
        self,
        *,
        vuln_type: str,
        target: str,
        results: list[dict[str, Any]],
    ) -> VerificationResult:
        reflected = [r for r in results if r.get("contains_payload")]
        if not reflected:
            return VerificationResult(
                success=False,
                confidence=0.1,
                reason="No reflected payload observed",
            )

        observations: list[dict[str, Any]] = []
        for r in reflected[:3]:
            snippet = r.get("response_snippet") or ""
            observations.append(
                {
                    "payload": r.get("payload"),
                    "status_code": r.get("status_code"),
                    "response_length": r.get("response_length"),
                    "duration_ms": r.get("duration_ms"),
                    "response_snippet_sha256": _sha256_text(snippet),
                }
            )

        evidence = EvidenceBundle(
            verifier=self.name,
            target=target,
            vuln_type=vuln_type,
            created_at=datetime.now(UTC).isoformat(),
            observations=observations,
        )

        return VerificationResult(
            success=True,
            confidence=0.75,
            reason="Payload reflected in HTTP response",
            evidence=evidence,
        )


class BasicSQLiVerifier:
    name = "basic_sqli"

    _error_substrings = (
        "sql syntax",
        "you have an error in your sql syntax",
        "warning: mysql",
        "mysql",
        "postgres",
        "sqlite",
        "odbc",
        "jdbc",
        "pg::syntaxerror",
    )

    def verify(
        self,
        *,
        vuln_type: str,
        target: str,
        results: list[dict[str, Any]],
    ) -> VerificationResult:
        # Evidence: any response that looks like DB error or time-based delay.
        observations: list[dict[str, Any]] = []

        for r in results:
            snippet = (r.get("response_snippet") or "").lower()
            payload = (r.get("payload") or "").lower()
            duration_ms = float(r.get("duration_ms") or 0)

            hit = False
            hit_reason = ""

            if snippet and any(s in snippet for s in self._error_substrings):
                hit = True
                hit_reason = "db_error_signature"

            if not hit and ("sleep(" in payload or "waitfor" in payload) and duration_ms >= 4000:
                hit = True
                hit_reason = "time_delay"

            if hit:
                observations.append(
                    {
                        "payload": r.get("payload"),
                        "status_code": r.get("status_code"),
                        "response_length": r.get("response_length"),
                        "duration_ms": duration_ms,
                        "match": hit_reason,
                        "response_snippet_sha256": _sha256_text(r.get("response_snippet") or ""),
                    }
                )

        if not observations:
            return VerificationResult(
                success=False,
                confidence=0.1,
                reason="No SQL error patterns or time delay observed",
            )

        evidence = EvidenceBundle(
            verifier=self.name,
            target=target,
            vuln_type=vuln_type,
            created_at=datetime.now(UTC).isoformat(),
            observations=observations[:5],
        )

        # Keep conservative confidence: these are still heuristic signals.
        confidence = 0.65 if any(o.get("match") == "db_error_signature" for o in observations) else 0.55

        return VerificationResult(
            success=True,
            confidence=confidence,
            reason="SQLi signal detected via heuristic evidence",
            evidence=evidence,
        )


def get_default_verifier(vuln_type: str) -> ExploitVerifier | None:
    vt = (vuln_type or "").lower()
    if "xss" in vt:
        return ReflectedXSSVerifier()
    if "sqli" in vt or "sql" in vt:
        return BasicSQLiVerifier()
    return None
