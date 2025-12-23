"""Perplexity research integration for SecBrain."""

from __future__ import annotations

import hashlib
import os
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from secbrain.core.context import RunContext


class PerplexityResearch:
    """
    Research integration via Perplexity API.

    Used for:
    - Fetching related writeups and techniques
    - Understanding target technology stacks
    - Finding known vulnerabilities and CVEs
    - Learning from public security research
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "sonar-medium-online",
        max_calls_per_run: int = 20,
    ):
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY", "")
        self.model = model
        self.max_calls_per_run = max_calls_per_run
        self._call_count = 0

        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def _cache_key(self, question: str, context: str) -> str:
        """Generate a cache key for a research query."""
        combined = f"{question}:{context}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    async def ask_research(
        self,
        question: str,
        context: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """
        Ask a research question using Perplexity.

        Args:
            question: The research question
            context: Additional context (target info, phase, etc.)
            run_context: Current run context for caching and limits

        Returns:
            {
                "answer": str,
                "sources": list[str],
                "cached": bool
            }
        """
        # Check cache first
        cache_key = self._cache_key(question, context)
        cached = run_context.get_cached_research(cache_key)
        if cached:
            return {**cached, "cached": True}

        # Check call limits
        if self._call_count >= self.max_calls_per_run:
            return {
                "answer": "[LIMIT] Research call limit reached for this run.",
                "sources": [],
                "cached": False,
                "limited": True,
            }

        # Check dry-run mode
        if run_context.dry_run:
            return {
                "answer": f"[DRY-RUN] Would research: {question[:100]}...",
                "sources": ["dry-run-source"],
                "cached": False,
            }

        # Make the API call
        try:
            self._call_count += 1

            prompt = f"""Context: {context}

Question: {question}

Provide a focused, technical answer relevant to security research and bug bounty hunting. Include specific techniques, tools, or CVE references when applicable."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security research assistant helping with bug bounty hunting. Provide accurate, actionable information with sources.",
                    },
                    {"role": "user", "content": prompt},
                ],
            }

            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            sources = data.get("citations", [])

            result = {
                "answer": answer,
                "sources": sources,
                "cached": False,
            }

            # Cache the result
            run_context.cache_research(cache_key, result)

            return result

        except httpx.HTTPError as e:
            return {
                "answer": f"[ERROR] Research failed: {e!s}",
                "sources": [],
                "cached": False,
                "error": True,
            }

    async def research_technology(
        self,
        technology: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Research common vulnerabilities for a technology."""
        question = f"What are the most common security vulnerabilities and attack vectors for {technology}? Include recent CVEs if applicable."
        context = f"Researching technology: {technology}"
        return await self.ask_research(question, context, run_context)

    async def research_endpoint(
        self,
        endpoint: str,
        method: str,
        parameters: list[str],
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Research vulnerability patterns for an endpoint."""
        question = f"What vulnerability classes should be tested for a {method} endpoint at {endpoint} with parameters: {', '.join(parameters)}?"
        context = f"Endpoint analysis: {method} {endpoint}"
        return await self.ask_research(question, context, run_context)

    async def research_cwe(
        self,
        cwe_id: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Research a specific CWE for exploitation techniques."""
        question = f"How can {cwe_id} be exploited in web applications? What are the best testing techniques and payloads?"
        context = f"CWE research: {cwe_id}"
        return await self.ask_research(question, context, run_context)

    async def research_writeups(
        self,
        target_type: str,
        vuln_class: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Find relevant bug bounty writeups."""
        question = f"Find recent bug bounty writeups about {vuln_class} vulnerabilities in {target_type} applications. What techniques were successful?"
        context = f"Writeup research: {vuln_class} in {target_type}"
        return await self.ask_research(question, context, run_context)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


async def create_research_client(run_context: RunContext) -> PerplexityResearch:
    """Create a research client with run-specific configuration."""
    return PerplexityResearch()
