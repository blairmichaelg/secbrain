"""Tests for secbrain.tools.perplexity_research module."""

from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from secbrain.tools.perplexity_research import PerplexityResearch, create_research_client

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_run_context(tmp_path: Path):
    """Create a mock RunContext with research caching support."""
    ctx = MagicMock()
    ctx.dry_run = True
    ctx.workspace_path = tmp_path
    ctx._research_cache: dict = {}

    def _cache_research(key, value):
        ctx._research_cache[key] = value

    def _get_cached_research(key):
        return ctx._research_cache.get(key)

    ctx.cache_research = MagicMock(side_effect=_cache_research)
    ctx.get_cached_research = MagicMock(side_effect=_get_cached_research)
    return ctx


@pytest.fixture
def api_key():
    return "test-api-key-abc123"


@pytest.fixture
def research_client(api_key: str) -> PerplexityResearch:
    """Create a PerplexityResearch client with a test API key."""
    return PerplexityResearch(api_key=api_key)


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestPerplexityResearchInit:
    """Test PerplexityResearch initialization."""

    def test_init_with_explicit_api_key(self, api_key: str):
        """Test initialization with an explicitly provided API key."""
        client = PerplexityResearch(api_key=api_key)
        assert client.api_key == api_key
        assert client.model == "sonar"
        assert client.max_calls_per_run == 50
        assert client._call_count == 0

    def test_init_with_env_api_key(self, monkeypatch):
        """Test initialization using environment variable."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "env-key-xyz")
        client = PerplexityResearch()
        assert client.api_key == "env-key-xyz"

    def test_init_with_no_api_key_warns(self, monkeypatch):
        """Test that missing API key produces a warning."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client = PerplexityResearch(api_key=None)
            assert len(w) == 1
            assert "No API key provided" in str(w[0].message)
            # api_key should be set to empty string for header compatibility
            assert client.api_key == ""

    def test_init_custom_model_and_max_calls(self, api_key: str):
        """Test initialization with custom model and max call settings."""
        client = PerplexityResearch(
            api_key=api_key,
            model="sonar-medium-online",
            max_calls_per_run=100,
        )
        assert client.model == "sonar-medium-online"
        assert client.max_calls_per_run == 100

    def test_init_creates_http_client(self, api_key: str):
        """Test that httpx client is created with correct configuration."""
        client = PerplexityResearch(api_key=api_key)
        assert isinstance(client.client, httpx.AsyncClient)

    def test_init_rate_limit_defaults(self, api_key: str):
        """Test that rate limiting defaults are configured correctly."""
        client = PerplexityResearch(api_key=api_key)
        assert client._rate_limit_per_minute == 10
        assert client._request_times == []


# ---------------------------------------------------------------------------
# Cache key tests
# ---------------------------------------------------------------------------


class TestCacheKey:
    """Test cache key generation."""

    def test_cache_key_deterministic(self, research_client: PerplexityResearch):
        """Test that cache key is deterministic for same inputs."""
        key1 = research_client._cache_key("question", "context")
        key2 = research_client._cache_key("question", "context")
        assert key1 == key2

    def test_cache_key_different_for_different_inputs(self, research_client: PerplexityResearch):
        """Test that different inputs produce different cache keys."""
        key1 = research_client._cache_key("question1", "context")
        key2 = research_client._cache_key("question2", "context")
        assert key1 != key2

    def test_cache_key_is_hex_string(self, research_client: PerplexityResearch):
        """Test that cache key is a 16-character hex string."""
        key = research_client._cache_key("question", "context")
        assert len(key) == 16
        int(key, 16)  # Should not raise - valid hex

    def test_cache_key_empty_context(self, research_client: PerplexityResearch):
        """Test cache key with empty context."""
        key = research_client._cache_key("question", "")
        assert len(key) == 16


# ---------------------------------------------------------------------------
# Rate limiting tests
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """Test rate limiting behavior."""

    async def test_rate_limit_allows_requests_under_limit(self, research_client: PerplexityResearch):
        """Test that requests under the limit pass through."""
        # Should complete without blocking significantly
        for _ in range(5):
            await research_client._enforce_rate_limit()
        assert len(research_client._request_times) == 5

    async def test_rate_limit_records_request_times(self, research_client: PerplexityResearch):
        """Test that request times are recorded."""
        await research_client._enforce_rate_limit()
        assert len(research_client._request_times) == 1

    async def test_rate_limit_removes_old_requests(self, research_client: PerplexityResearch):
        """Test that requests older than 60 seconds are removed."""
        import time

        # Manually add an old request time (>60 seconds ago)
        research_client._request_times = [time.time() - 120]
        await research_client._enforce_rate_limit()
        # The old one should be removed, new one added
        assert len(research_client._request_times) == 1


# ---------------------------------------------------------------------------
# Cache validity tests
# ---------------------------------------------------------------------------


class TestCacheValidity:
    """Test cache validity checking."""

    def test_cache_valid_when_fresh(self, research_client: PerplexityResearch, mock_run_context):
        """Test that fresh cache is valid."""
        from datetime import UTC, datetime

        cache_key = "testkey"
        research_client._cache_ttl[cache_key] = datetime.now(UTC)
        mock_run_context.get_cached_research.side_effect = lambda k: {"data": "value"} if k == cache_key else None

        assert research_client._is_cache_valid(cache_key, ttl_hours=24, run_context=mock_run_context)

    def test_cache_invalid_when_missing_key(self, research_client: PerplexityResearch, mock_run_context):
        """Test that missing cache key returns invalid."""
        assert not research_client._is_cache_valid("nonexistent", ttl_hours=24, run_context=mock_run_context)

    def test_cache_invalid_when_data_missing(self, research_client: PerplexityResearch, mock_run_context):
        """Test that cache is invalid when TTL exists but data is missing."""
        from datetime import UTC, datetime

        cache_key = "testkey"
        research_client._cache_ttl[cache_key] = datetime.now(UTC)
        mock_run_context.get_cached_research.side_effect = lambda k: None

        assert not research_client._is_cache_valid(cache_key, ttl_hours=24, run_context=mock_run_context)
        # Stale TTL should be cleaned up
        assert cache_key not in research_client._cache_ttl

    def test_cache_invalid_when_expired(self, research_client: PerplexityResearch, mock_run_context):
        """Test that expired cache is invalid."""
        from datetime import UTC, datetime, timedelta

        cache_key = "testkey"
        research_client._cache_ttl[cache_key] = datetime.now(UTC) - timedelta(hours=48)
        mock_run_context.get_cached_research.side_effect = lambda k: {"data": "value"} if k == cache_key else None

        assert not research_client._is_cache_valid(cache_key, ttl_hours=24, run_context=mock_run_context)


# ---------------------------------------------------------------------------
# ask_research tests
# ---------------------------------------------------------------------------


class TestAskResearch:
    """Test the main ask_research method."""

    async def test_dry_run_returns_dry_run_result(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test that dry run mode returns a dry-run result."""
        mock_run_context.dry_run = True

        result = await research_client.ask_research(
            question="What are common vulnerabilities?",
            context="Smart contracts",
            run_context=mock_run_context,
        )

        assert result["cached"] is False
        assert "[DRY-RUN]" in result["answer"]
        assert "dry-run-source" in result["sources"]
        mock_run_context.cache_research.assert_called_once()

    async def test_cached_result_returned_when_valid(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test that valid cached results are returned."""

        # First call in dry-run to populate cache
        mock_run_context.dry_run = True
        await research_client.ask_research(
            question="What are common vulnerabilities?",
            context="Smart contracts",
            run_context=mock_run_context,
        )

        # Second call should return cached result
        result = await research_client.ask_research(
            question="What are common vulnerabilities?",
            context="Smart contracts",
            run_context=mock_run_context,
        )

        assert result["cached"] is True
        assert "cache_age_hours" in result

    async def test_call_limit_returns_limited_result(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test that exceeding call limit returns a limit message."""
        mock_run_context.dry_run = False
        mock_run_context.get_cached_research.side_effect = lambda k: None
        research_client._call_count = research_client.max_calls_per_run

        result = await research_client.ask_research(
            question="Test question",
            context="Test context",
            run_context=mock_run_context,
        )

        assert result["limited"] is True
        assert "[LIMIT]" in result["answer"]

    async def test_api_call_success(self, api_key: str, mock_run_context):
        """Test successful API call with mocked httpx."""
        mock_run_context.dry_run = False
        mock_run_context.get_cached_research.side_effect = lambda k: None

        client = PerplexityResearch(api_key=api_key)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Reentrancy is a common vulnerability"}}],
            "citations": ["https://source1.com", "https://source2.com"],
        }
        mock_response.raise_for_status = MagicMock()

        client.client = AsyncMock()
        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.ask_research(
            question="What is reentrancy?",
            context="Smart contract security",
            run_context=mock_run_context,
        )

        assert result["answer"] == "Reentrancy is a common vulnerability"
        assert result["sources"] == ["https://source1.com", "https://source2.com"]
        assert result["cached"] is False
        assert client._call_count == 1
        mock_run_context.cache_research.assert_called_once()

    async def test_api_call_http_error(self, api_key: str, mock_run_context):
        """Test HTTP error handling during API call."""
        mock_run_context.dry_run = False
        mock_run_context.get_cached_research.side_effect = lambda k: None

        client = PerplexityResearch(api_key=api_key)
        client.client = AsyncMock()
        client.client.post = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )

        result = await client.ask_research(
            question="Test question",
            context="Test context",
            run_context=mock_run_context,
        )

        assert result["error"] is True
        assert "[ERROR]" in result["answer"]
        assert "Connection failed" in result["error_detail"]

    async def test_no_api_key_returns_dry_run(self, mock_run_context, monkeypatch):
        """Test that no API key triggers dry-run behavior even if dry_run is False."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        mock_run_context.dry_run = False

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = PerplexityResearch(api_key=None)

        result = await client.ask_research(
            question="Test question",
            context="Test context",
            run_context=mock_run_context,
        )

        assert "[DRY-RUN]" in result["answer"]


# ---------------------------------------------------------------------------
# Specialized research methods tests
# ---------------------------------------------------------------------------


class TestSpecializedResearchMethods:
    """Test specialized convenience research methods."""

    async def test_research_severity_context(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test severity context research method."""
        mock_run_context.dry_run = True

        result = await research_client.research_severity_context(
            vuln_type="reentrancy",
            run_context=mock_run_context,
            details="Cross-function reentrancy in DeFi vault",
        )

        assert "[DRY-RUN]" in result["answer"]
        assert result["cached"] is False

    async def test_research_attack_vectors(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test attack vector research method."""
        mock_run_context.dry_run = True

        result = await research_client.research_attack_vectors(
            vuln_type="flash_loan",
            run_context=mock_run_context,
            contract_pattern="lending pool pattern",
        )

        assert "[DRY-RUN]" in result["answer"]

    async def test_research_market_conditions(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test market conditions research method."""
        mock_run_context.dry_run = True

        result = await research_client.research_market_conditions(
            target_protocol="Aave",
            exploit_type="flash_loan",
            run_context=mock_run_context,
        )

        assert "[DRY-RUN]" in result["answer"]

    async def test_research_technology(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test technology research backward compatibility method."""
        mock_run_context.dry_run = True

        result = await research_client.research_technology(
            technology="Solidity",
            run_context=mock_run_context,
        )

        assert "[DRY-RUN]" in result["answer"]

    async def test_research_endpoint(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test endpoint research backward compatibility method."""
        mock_run_context.dry_run = True

        result = await research_client.research_endpoint(
            endpoint="/api/v1/users",
            method="POST",
            parameters=["username", "password"],
            run_context=mock_run_context,
        )

        assert "[DRY-RUN]" in result["answer"]

    async def test_research_cwe(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test CWE research backward compatibility method."""
        mock_run_context.dry_run = True

        result = await research_client.research_cwe(
            cwe_id="CWE-89",
            run_context=mock_run_context,
        )

        assert "[DRY-RUN]" in result["answer"]

    async def test_research_writeups(
        self, research_client: PerplexityResearch, mock_run_context
    ):
        """Test writeup research backward compatibility method."""
        mock_run_context.dry_run = True

        result = await research_client.research_writeups(
            target_type="DeFi",
            vuln_class="reentrancy",
            run_context=mock_run_context,
        )

        assert "[DRY-RUN]" in result["answer"]


# ---------------------------------------------------------------------------
# Close and factory tests
# ---------------------------------------------------------------------------


class TestCloseAndFactory:
    """Test client cleanup and factory function."""

    async def test_close_client(self, research_client: PerplexityResearch):
        """Test that close properly closes the httpx client."""
        research_client.client = AsyncMock()
        research_client.client.aclose = AsyncMock()
        await research_client.close()
        research_client.client.aclose.assert_called_once()

    async def test_create_research_client_factory(self, mock_run_context):
        """Test the factory function creates a client."""
        client = await create_research_client(mock_run_context)
        assert isinstance(client, PerplexityResearch)
