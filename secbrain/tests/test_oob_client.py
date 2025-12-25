"""Tests for OOB (Out-of-Band) client functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from secbrain.core.context import RunContext
from secbrain.tools.oob_client import OOBClient, OOBProbe, create_oob_client


class TestOOBProbe:
    """Test OOBProbe dataclass."""

    def test_probe_creation(self):
        """Test creating an OOB probe."""
        probe = OOBProbe(
            probe_id="test123",
            url="http://test.oob.secbrain",
            dns="test.oob.secbrain",
            token="test",
        )
        assert probe.probe_id == "test123"
        assert probe.url == "http://test.oob.secbrain"
        assert probe.dns == "test.oob.secbrain"
        assert probe.token == "test"
        assert probe.created_at is not None


class TestOOBClient:
    """Test OOBClient functionality."""

    def test_init_default_endpoint(self):
        """Test initialization with default endpoint."""
        client = OOBClient()
        assert client.endpoint == "https://interact.sh"
        assert client.run_context is None

    def test_init_custom_endpoint(self):
        """Test initialization with custom endpoint."""
        client = OOBClient(endpoint="https://custom.endpoint.com/")
        assert client.endpoint == "https://custom.endpoint.com"

    def test_init_with_context(self):
        """Test initialization with run context."""
        ctx = Mock(spec=RunContext)
        client = OOBClient(run_context=ctx)
        assert client.run_context is ctx

    def test_generate_probe_default(self):
        """Test generating a probe without label."""
        client = OOBClient()
        probe = client.generate_probe()

        assert probe.probe_id
        assert len(probe.probe_id) == 32  # UUID hex is 32 chars
        assert probe.token == probe.probe_id[:6]
        assert probe.url == f"http://{probe.token}.oob.secbrain"
        assert probe.dns == f"{probe.token}.oob.secbrain"

    def test_generate_probe_with_label(self):
        """Test generating a probe with custom label."""
        client = OOBClient()
        probe = client.generate_probe(label="custom")

        assert probe.probe_id
        assert probe.token == "custom"
        assert probe.url == "http://custom.oob.secbrain"
        assert probe.dns == "custom.oob.secbrain"

    async def test_check_interactions_dry_run(self):
        """Test checking interactions in dry-run mode."""
        ctx = Mock(spec=RunContext)
        ctx.dry_run = True
        client = OOBClient(run_context=ctx)

        interactions = await client.check_interactions("test_probe_id")

        assert len(interactions) == 1
        assert interactions[0]["probe_id"] == "test_probe_id"
        assert interactions[0]["type"] == "dns"
        assert "dry-run-test_probe_id.oob.secbrain" in interactions[0]["host"]
        assert "timestamp" in interactions[0]

    async def test_check_interactions_success(self):
        """Test checking interactions with successful response."""
        client = OOBClient(endpoint="https://test.endpoint")

        mock_response = Mock()
        mock_response.json.return_value = {
            "interactions": [
                {"type": "http", "host": "test.oob.secbrain"},
                {"type": "dns", "host": "test.oob.secbrain"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value = mock_client
            mock_client.post.return_value = mock_response

            interactions = await client.check_interactions("test_probe")

            assert len(interactions) == 2
            assert interactions[0]["type"] == "http"
            assert interactions[1]["type"] == "dns"
            mock_client.post.assert_called_once()

    async def test_check_interactions_error(self):
        """Test checking interactions when request fails."""
        client = OOBClient()

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value = mock_client
            mock_client.post.side_effect = Exception("Network error")

            interactions = await client.check_interactions("test_probe")

            assert interactions == []

    async def test_close(self):
        """Test closing the client."""
        client = OOBClient()

        # Create a mock client
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None

    async def test_close_when_no_client(self):
        """Test closing when no client exists."""
        client = OOBClient()
        await client.close()  # Should not raise


class TestCreateOOBClient:
    """Test OOB client factory function."""

    def test_create_oob_client_default(self):
        """Test creating OOB client with defaults."""
        client = create_oob_client()
        assert isinstance(client, OOBClient)
        assert client.endpoint == "https://interact.sh"

    def test_create_oob_client_with_context(self):
        """Test creating OOB client with context."""
        ctx = Mock(spec=RunContext)
        client = create_oob_client(run_context=ctx)
        assert client.run_context is ctx

    def test_create_oob_client_with_endpoint(self):
        """Test creating OOB client with custom endpoint."""
        client = create_oob_client(endpoint="https://custom.endpoint")
        assert client.endpoint == "https://custom.endpoint"
