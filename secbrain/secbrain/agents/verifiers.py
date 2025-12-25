"""Exploit verifiers: confirm vulnerability existence through evidence.

This module provides verification mechanisms to validate security vulnerabilities
through concrete evidence collection and analysis.
"""

from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import ClassVar, Protocol

from secbrain.core.verification import (
    EvidenceBundle,
    ResponseFingerprint,
    VerificationMethod,
    VerificationResult,
    get_url_path,
)


class ExploitVerifier(ABC):
    """Abstract base for vulnerability verifiers."""

    @abstractmethod
    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        """Verify exploitation by comparing baseline vs. test response."""

    def _build_evidence_bundle(
        self,
        *,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
        verification_method: VerificationMethod,
        test_passed: bool,
        confidence_score: float,
        notes: str | None = None,
    ) -> EvidenceBundle:
        payload_hash = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()

        return EvidenceBundle(
            evidence_id=str(uuid.uuid4()),
            trace_id=trace_id,
            method=str(getattr(test_response, "method", "GET")),
            url_path=get_url_path(str(getattr(test_response, "url", target_url))),
            injected_parameter=parameter_name,
            payload_hash=payload_hash,
            baseline_response=ResponseFingerprint.from_http_response(baseline_response),
            test_response=ResponseFingerprint.from_http_response(test_response),
            verification_method=verification_method,
            test_passed=test_passed,
            confidence_score=confidence_score,
            timestamp=datetime.now(UTC),
            notes=notes,
        )


class VerificationHttpResponse(Protocol):
    """Lightweight HTTP response shape for verification routines."""

    text: str | None
    status_code: int | None
    duration_ms: float | int | None


class ReflectedXSSVerifier(ExploitVerifier):
    """Verify Reflected XSS by checking payload reflection in response body."""

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        baseline_contains = payload in getattr(baseline_response, "text", "")
        test_contains = payload in getattr(test_response, "text", "")

        if test_contains and not baseline_contains:
            test_passed = True
            confidence_score = 0.85
            notes = "Payload reflected in response only when injected"
        elif test_contains and baseline_contains:
            test_passed = False
            confidence_score = 0.30
            notes = "Payload appears in both baseline and test"
        else:
            test_passed = False
            confidence_score = 0.0
            notes = "Payload not reflected in response"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.REFLECTION,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )


class SQLiErrorVerifier(ExploitVerifier):
    """Verify SQL Injection by detecting database error messages."""

    ERROR_PATTERNS: ClassVar[list[str]] = [
        "sql syntax error",
        "mysql_error",
        "ora-",
        "postgresql",
        "you have an error in your sql",
        "sqlserver",
        "unexpected end of file",
        "sqlite error",
        "sqlstate",
    ]

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        baseline_text = (getattr(baseline_response, "text", "") or "").lower()
        test_text = (getattr(test_response, "text", "") or "").lower()

        baseline_has_error = any(p in baseline_text for p in self.ERROR_PATTERNS)
        test_has_error = any(p in test_text for p in self.ERROR_PATTERNS)

        test_status = int(getattr(test_response, "status_code", 0) or 0)
        baseline_status = int(getattr(baseline_response, "status_code", 0) or 0)

        test_is_error = test_status >= 500
        baseline_is_ok = baseline_status < 400 and baseline_status > 0

        if test_has_error and not baseline_has_error:
            test_passed = True
            confidence_score = 0.8
            notes = "SQL error message detected"
        elif test_is_error and baseline_is_ok:
            test_passed = True
            confidence_score = 0.5
            notes = f"Server error ({test_status}) on payload"
        else:
            test_passed = False
            confidence_score = 0.0
            notes = "No SQL error detected"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.ERROR_RESPONSE,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )


class NaiveVerifier(ExploitVerifier):
    """Fallback verifier: no specific verification."""

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.NONE,
            test_passed=False,
            confidence_score=0.0,
            notes="No verifier implemented for this vuln type",
        )

        return VerificationResult(
            verified=False,
            confidence_score=0.0,
            evidence=evidence,
        )


class TimingVerifier(ExploitVerifier):
    """Detect timing-based anomalies between baseline and test."""

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        baseline_ms = float(getattr(baseline_response, "duration_ms", 0) or 0)
        test_ms = float(getattr(test_response, "duration_ms", 0) or 0)
        delta = test_ms - baseline_ms

        test_passed = delta >= 1000  # simple heuristic for blind/timing checks
        confidence_score = 0.6 if test_passed else 0.0
        notes = f"Timing delta {delta:.0f}ms (baseline {baseline_ms:.0f}ms)"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.TIMING,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )


class SSRFHeuristicVerifier(ExploitVerifier):
    """Heuristic SSRF verifier looking for external fetch indicators."""

    EXFIL_PATTERNS: ClassVar[list[str]] = [
        "169.254.169.254",
        "metadata.google.internal",
        "aws_session_token",
        "instance-id",
        "connection refused",
    ]

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response: VerificationHttpResponse,
        test_response: VerificationHttpResponse,
        trace_id: str,
    ) -> VerificationResult:
        test_text = (getattr(test_response, "text", "") or "").lower()
        baseline_status = int(getattr(baseline_response, "status_code", 0) or 0)
        test_status = int(getattr(test_response, "status_code", 0) or 0)

        indicators = any(p in test_text for p in self.EXFIL_PATTERNS)
        status_diff = test_status != baseline_status and test_status >= 500
        test_passed = indicators or status_diff
        confidence_score = 0.65 if indicators else (0.4 if status_diff else 0.0)
        notes = "SSRF indicators detected" if indicators else "Status delta on SSRF probe"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.STATUS_CHANGE,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )


class SSTIVerifier(ExploitVerifier):
    """Detect basic template injection via echo/delimiter reflection."""

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        test_text = (getattr(test_response, "text", "") or "")[:1000].lower()
        marker_hits = any(marker in test_text for marker in ["ssti_test_", "calc_ssti_", "42ssti"])
        test_passed = marker_hits
        confidence_score = 0.75 if marker_hits else 0.0
        notes = "SSTI marker reflected/executed" if marker_hits else "No SSTI marker observed"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.REFLECTION,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )


class PathTraversalVerifier(ExploitVerifier):
    """Detect traversal via sensitive file snippets."""

    SENSITIVE_SNIPPETS: ClassVar[list[str]] = [
        "root:x:0:0:",
        "[boot loader]",
        "[extensions]",
        "machine.config",
        "[drivers]",
    ]

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        test_text = (getattr(test_response, "text", "") or "").lower()
        hit = any(s.lower() in test_text for s in self.SENSITIVE_SNIPPETS)
        test_passed = hit
        confidence_score = 0.7 if hit else 0.0
        notes = "Sensitive file content detected" if hit else "No sensitive content detected"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.COMMAND_OUTPUT,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )


class NoSQLiErrorVerifier(ExploitVerifier):
    """Detect NoSQL injection error or logic behavior."""

    ERROR_PATTERNS: ClassVar[list[str]] = [
        "cast to objectid failed",
        "mongoerror",
        "mongodb",
        "pymongo",
        "bson",
        "json.parse",
    ]

    async def verify(
        self,
        target_url: str,
        parameter_name: str,
        payload: str,
        baseline_response,
        test_response,
        trace_id: str,
    ) -> VerificationResult:
        baseline_text = (getattr(baseline_response, "text", "") or "").lower()
        test_text = (getattr(test_response, "text", "") or "").lower()

        baseline_status = int(getattr(baseline_response, "status_code", 0) or 0)
        test_status = int(getattr(test_response, "status_code", 0) or 0)

        error_hit = any(p in test_text for p in self.ERROR_PATTERNS) and not any(
            p in baseline_text for p in self.ERROR_PATTERNS
        )
        status_delta = test_status >= 500 and (baseline_status < 500)

        test_passed = error_hit or status_delta
        confidence_score = 0.65 if error_hit else (0.35 if status_delta else 0.0)
        notes = "NoSQL error surfaced" if error_hit else "Status delta on NoSQL probe"

        evidence = self._build_evidence_bundle(
            target_url=target_url,
            parameter_name=parameter_name,
            payload=payload,
            baseline_response=baseline_response,
            test_response=test_response,
            trace_id=trace_id,
            verification_method=VerificationMethod.ERROR_RESPONSE,
            test_passed=test_passed,
            confidence_score=confidence_score,
            notes=notes,
        )

        return VerificationResult(
            verified=test_passed,
            confidence_score=confidence_score,
            evidence=evidence,
        )
