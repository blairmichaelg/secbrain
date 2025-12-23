"""Enhanced Perplexity research integration for SecBrain.

This module provides specialized security research queries with:
- TTL-based intelligent caching
- Strict rate limiting enforcement
- Domain-specific research methods
- Real-world data grounding for decisions
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
import warnings
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from secbrain.core.context import RunContext


class PerplexityResearch:
    """
    Enhanced research integration via Perplexity API.

    Features:
    - Specialized security research queries
    - TTL-based caching (1h-168h depending on data type)
    - Strict rate limiting (10 req/min enforced)
    - Real-world data for severity, attacks, market conditions
    - Fallback strategies for API failures

    Used for:
    - Severity assessment with real-world context
    - Attack vector discovery from recent exploits
    - Market condition validation before execution
    - Historical exploit pattern matching
    - Profitability analysis
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "sonar",  # Changed to sonar (faster, cheaper) from sonar-medium-online
        max_calls_per_run: int = 50,  # Increased from 20 for intensive research
    ):
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        
        # Validate API key is provided (will be None in dry-run mode)
        if self.api_key is None:
            warnings.warn(
                "No API key provided for PerplexityResearch. "
                "Set PERPLEXITY_API_KEY environment variable. "
                "Research queries will return dry-run results unless API key is provided.",
                stacklevel=2
            )
            # Use empty string for header compatibility
            self.api_key = ""
        
        self.model = model
        self.max_calls_per_run = max_calls_per_run
        self._call_count = 0

        # Rate limiting state
        self._request_times: list[float] = []
        self._rate_limit_per_minute = 10
        self._rate_limit_lock = asyncio.Lock()

        # TTL cache state
        self._cache_ttl: dict[str, datetime] = {}
        self._default_ttl = timedelta(hours=24)

        # HTTP client with optimized connection pooling
        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    def _cache_key(self, question: str, context: str = "") -> str:
        """Generate cache key for a research query."""
        combined = f"{question}:{context}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    async def _enforce_rate_limit(self) -> None:
        """Enforce 10 requests per minute rate limit with proper concurrency control."""
        async with self._rate_limit_lock:
            while True:
                now = time.time()
                
                # Remove requests older than 60 seconds
                self._request_times = [
                    t for t in self._request_times
                    if now - t < 60
                ]
                
                # If under the limit, record this request and exit
                if len(self._request_times) < self._rate_limit_per_minute:
                    self._request_times.append(now)
                    break
                
                # At limit: wait for the oldest request to age out, then re-check
                wait_time = 60 - (now - self._request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

    def _is_cache_valid(self, cache_key: str, ttl_hours: int, run_context: RunContext) -> bool:
        """Check if cached data is still valid based on TTL.
        
        Validates both the TTL timestamp exists AND the cached data exists
        to prevent stale timestamp issues.
        """
        if cache_key not in self._cache_ttl:
            return False
        
        # Check that cached data actually exists in run_context
        cached_data = run_context.get_cached_research(cache_key)
        if not cached_data:
            # TTL exists but data is missing - clean up stale timestamp
            del self._cache_ttl[cache_key]
            return False
        
        cached_time = self._cache_ttl[cache_key]
        age = datetime.now() - cached_time
        return age < timedelta(hours=ttl_hours)

    async def ask_research(
        self,
        question: str,
        context: str,
        run_context: RunContext,
        ttl_hours: int = 24,
    ) -> dict[str, Any]:
        """
        Ask a research question with TTL-aware caching.

        Args:
            question: The research question
            context: Additional context (target info, phase, etc.)
            run_context: Current run context for caching and limits
            ttl_hours: Cache TTL in hours (default: 24)

        Returns:
            {
                "answer": str,
                "sources": list[str],
                "cached": bool,
                "cache_age_hours": float | None
            }
        """
        # Generate cache key
        cache_key = self._cache_key(question, context)
        
        # Check cache with TTL
        cached = run_context.get_cached_research(cache_key)
        if cached and self._is_cache_valid(cache_key, ttl_hours, run_context):
            cache_age = (datetime.now() - self._cache_ttl[cache_key]).total_seconds() / 3600
            return {
                **cached,
                "cached": True,
                "cache_age_hours": cache_age,
            }

        # Check call limits
        if self._call_count >= self.max_calls_per_run:
            return {
                "answer": f"[LIMIT] Research call limit ({self.max_calls_per_run}) reached for this run.",
                "sources": [],
                "cached": False,
                "limited": True,
            }

        # Check dry-run mode
        if run_context.dry_run:
            result = {
                "answer": f"[DRY-RUN] Would research: {question[:100]}...",
                "sources": ["dry-run-source"],
                "cached": False,
            }
            
            # Cache dry-run results for consistency
            run_context.cache_research(cache_key, result)
            self._cache_ttl[cache_key] = datetime.now()
            
            return result

        # Enforce rate limiting
        await self._enforce_rate_limit()

        # Make the API call
        try:
            self._call_count += 1

            prompt = f"""Context: {context}

Question: {question}

Provide a focused, technical answer relevant to security research and bug bounty hunting. 
Include specific techniques, tools, CVE references, exploit dates, and profit amounts when applicable.
Prioritize data from within the last 6 months (from {datetime.now().strftime('%B %Y')})."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security research assistant specializing in smart contract exploitation and bug bounty hunting. Provide accurate, actionable information with sources and specific data points.",
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

            # Cache the result with timestamp
            run_context.cache_research(cache_key, result)
            self._cache_ttl[cache_key] = datetime.now()

            return result

        except httpx.HTTPError as e:
            return {
                "answer": f"[ERROR] Research failed: {str(e)}",
                "sources": [],
                "cached": False,
                "error": True,
                "error_detail": str(e),
            }

    # ============================================================
    # SPECIALIZED SECURITY RESEARCH METHODS
    # ============================================================

    async def research_severity_context(
        self,
        vuln_type: str,
        run_context: RunContext,
        details: str = "",
    ) -> dict[str, Any]:
        """
        Research real-world severity assessment for a vulnerability type.

        Returns:
            {
                "answer": str with severity consensus and real examples,
                "sources": list[str],
                "cached": bool
            }

        Cache: 168 hours (7 days - severity standards change very slowly)
        """
        from datetime import datetime, timedelta
        
        # Calculate date range for recent data (last 6 months)
        current_date = datetime.now()
        six_months_ago = current_date - timedelta(days=180)
        
        question = f"""
Current severity assessment for {vuln_type} vulnerabilities in smart contracts (as of {current_date.strftime('%B %Y')}):

Required information:
1. Security researcher consensus on severity level (Critical/High/Medium/Low)
2. Recent exploit examples from the last 6 months (since {six_months_ago.strftime('%B %Y')}) with:
   - Specific dates
   - Contract names
   - Financial impact in USD
3. Attack success rates and reliability
4. Typical remediation difficulty
5. Detection difficulty and time-to-exploit

{f'Additional context: {details}' if details else ''}

Provide concrete, data-driven assessment with specific examples and amounts.
"""
        
        return await self.ask_research(
            question=question,
            context=f"Severity research for {vuln_type}",
            run_context=run_context,
            ttl_hours=168,  # 7 day cache (severity standards change slowly)
        )

    async def research_attack_vectors(
        self,
        vuln_type: str,
        run_context: RunContext,
        contract_pattern: str = "",
    ) -> dict[str, Any]:
        """
        Research successful attack patterns and techniques.

        Returns:
            {
                "answer": str with attack techniques and real exploits,
                "sources": list[str],
                "cached": bool
            }

        Cache: 48 hours (attack patterns evolve moderately fast)
        """
        from datetime import datetime, timedelta
        
        # Calculate date range for recent data (last 6 months)
        current_date = datetime.now()
        six_months_ago = current_date - timedelta(days=180)
        
        question = f"""
Successful attack vectors and exploitation techniques for {vuln_type} vulnerabilities in EVM smart contracts:

For each attack pattern, provide:
1. Step-by-step attack technique
2. Real exploit examples from the last 6 months (since {six_months_ago.strftime('%B %Y')}) with:
   - Exact dates
   - Contract names and addresses
   - Transaction hashes (if public)
3. Gas costs in USD
4. Actual profit made (if known)
5. Time to execute (seconds/minutes)
6. Success rate / reliability
7. Detection difficulty and time-to-detect

{f'Contract pattern context: {contract_pattern}' if contract_pattern else ''}

Prioritize recent, successful exploits with verified outcomes.
"""
        
        return await self.ask_research(
            question=question,
            context=f"Attack vector research for {vuln_type}",
            run_context=run_context,
            ttl_hours=48,  # 2 day cache
        )

    async def research_market_conditions(
        self,
        target_protocol: str,
        exploit_type: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """
        Research current market conditions for exploit validation.

        Returns:
            {
                "answer": str with market analysis and timing recommendations,
                "sources": list[str],
                "cached": bool
            }

        Cache: 1 hour (market conditions change rapidly)
        """
        question = f"""
Bug bounty analysis for {exploit_type} vulnerability in {target_protocol}:

For bug bounty hunters evaluating if this is worth pursuing:
1. Current TVL and liquidity depth
2. Recent similar vulnerability reports (last 30 days) with outcomes and bounty amounts
3. Current gas prices and network congestion
4. Protocol's bug bounty program details (if any) and typical payout ranges
5. Competition level from other security researchers
6. Estimated time investment required
7. Risk factors and likelihood of discovery by others
8. Expected bounty profitability range given current market state

Provide actionable intelligence for deciding whether to pursue this bug bounty opportunity.
"""
        
        return await self.ask_research(
            question=question,
            context=f"Market conditions for {target_protocol} {exploit_type}",
            run_context=run_context,
            ttl_hours=1,  # 1 hour cache (market data changes fast)
        )

    # ============================================================
    # BACKWARD COMPATIBILITY METHODS
    # ============================================================

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
