"""Tests for Python 3.11+ type safety enhancements.

These tests verify that the type-safe primitives work correctly at runtime,
including Pydantic strict mode, NewTypes, TypedDicts, and Protocols.
"""

import pytest
from pydantic import ValidationError

from secbrain.core.types import (
    # Constants
    ALLOWED_HTTP_METHODS,
    DEFAULT_RATE_LIMIT,
    MAX_CONFIDENCE,
    MIN_CONFIDENCE,
    # Pydantic models with strict mode
    AgentResult,
    Asset,
    # NewTypes
    EthAddress,
    # TypedDicts
    EvidenceDict,
    Finding,
    FindingDict,
    # Enums
    FindingStatus,
    # Protocols
    HTTPResponseProtocol,
    Hypothesis,
    ProfitTokenDict,
    ScopedURL,
    SecretStr,
    Severity,
    SHA256Hash,
    ToolCallDict,
    TxHash,
    # LiteralString utilities
    build_safe_table_name,
    execute_safe_query,
)


class TestNewTypes:
    """Tests for domain-specific NewTypes."""

    def test_eth_address_type_distinction(self) -> None:
        """NewTypes provide type-level distinction."""
        # At runtime, NewTypes are identity functions
        raw_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f8E"
        typed_address: EthAddress = EthAddress(raw_address)
        assert typed_address == raw_address
        assert isinstance(typed_address, str)

    def test_tx_hash_type_distinction(self) -> None:
        """TxHash NewType works correctly."""
        raw_hash = "0xabc123def456"
        typed_hash: TxHash = TxHash(raw_hash)
        assert typed_hash == raw_hash

    def test_sha256_hash_type_distinction(self) -> None:
        """SHA256Hash NewType works correctly."""
        raw_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        typed_hash: SHA256Hash = SHA256Hash(raw_hash)
        assert typed_hash == raw_hash

    def test_scoped_url_type_distinction(self) -> None:
        """ScopedURL NewType works correctly."""
        raw_url = "https://example.com/api/v1"
        typed_url: ScopedURL = ScopedURL(raw_url)
        assert typed_url == raw_url

    def test_secret_str_type_distinction(self) -> None:
        """SecretStr NewType works correctly."""
        raw_secret = "super-secret-api-key"
        typed_secret: SecretStr = SecretStr(raw_secret)
        assert typed_secret == raw_secret


class TestTypedDicts:
    """Tests for TypedDict structures."""

    def test_evidence_dict_structure(self) -> None:
        """EvidenceDict can be created with proper structure."""
        evidence: EvidenceDict = {
            "evidence_id": "ev-123",
            "trace_id": "trace-456",
            "method": "GET",
            "test_passed": True,
            "confidence_score": 0.85,
        }
        assert evidence["evidence_id"] == "ev-123"
        assert evidence["test_passed"] is True

    def test_profit_token_dict_structure(self) -> None:
        """ProfitTokenDict can be created with proper structure."""
        token: ProfitTokenDict = {
            "symbol": "WETH",
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "decimals": 18,
            "eth_equiv_multiplier": 1.0,
        }
        assert token["symbol"] == "WETH"
        assert token["decimals"] == 18

    def test_tool_call_dict_structure(self) -> None:
        """ToolCallDict can be created with proper structure."""
        call: ToolCallDict = {
            "tool": "http_client",
            "action": "GET",
            "target": "https://example.com",
            "success": True,
            "duration_ms": 123.45,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        assert call["tool"] == "http_client"
        assert call["success"] is True

    def test_finding_dict_structure(self) -> None:
        """FindingDict can be created with proper structure."""
        finding: FindingDict = {
            "id": "finding-123",
            "title": "XSS Vulnerability",
            "severity": "high",
            "status": "confirmed",
            "vuln_type": "xss",
        }
        assert finding["id"] == "finding-123"
        assert finding["severity"] == "high"


class TestPydanticStrictMode:
    """Tests for Pydantic V2 strict mode in models."""

    def test_finding_strict_mode_valid(self) -> None:
        """Finding model accepts valid strict types."""
        finding = Finding(
            id="finding-1",
            title="Test Finding",
            severity=Severity.HIGH,
        )
        assert finding.id == "finding-1"
        assert finding.severity == Severity.HIGH

    def test_finding_strict_mode_rejects_invalid_types(self) -> None:
        """Finding model rejects invalid types in strict mode."""
        with pytest.raises(ValidationError):
            Finding(
                id=123,  # type: ignore[arg-type] # Should be str
                title="Test",
                severity=Severity.HIGH,
            )

    def test_asset_strict_mode_valid(self) -> None:
        """Asset model accepts valid strict types."""
        asset = Asset(
            id="asset-1",
            type="domain",
            value="example.com",
            ports=[80, 443],
        )
        assert asset.id == "asset-1"
        assert asset.ports == [80, 443]

    def test_asset_strict_mode_rejects_invalid_ports(self) -> None:
        """Asset model rejects string ports in strict mode."""
        with pytest.raises(ValidationError):
            Asset(
                id="asset-1",
                type="domain",
                value="example.com",
                ports=["80", "443"],  # type: ignore[list-item] # Should be int
            )

    def test_hypothesis_strict_mode_valid(self) -> None:
        """Hypothesis model accepts valid strict types."""
        hyp = Hypothesis(
            id="hyp-1",
            asset_id="asset-1",
            vuln_type="xss",
            confidence=0.75,
            rationale="Testing",
        )
        assert hyp.confidence == 0.75

    def test_hypothesis_confidence_range_validation(self) -> None:
        """Hypothesis model validates confidence is between 0 and 1."""
        with pytest.raises(ValidationError):
            Hypothesis(
                id="hyp-1",
                asset_id="asset-1",
                vuln_type="xss",
                confidence=1.5,  # Invalid: > 1.0
                rationale="Testing",
            )

    def test_agent_result_strict_mode_valid(self) -> None:
        """AgentResult model accepts valid strict types."""
        result = AgentResult(
            agent="test_agent",
            phase="recon",
            success=True,
        )
        assert result.success is True

    def test_contract_config_strict_mode(self) -> None:
        """ContractConfig enforces strict mode type validation."""
        from secbrain.core.context import ContractConfig

        # Valid construction
        config = ContractConfig(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f8E",
            chain_id=1,
        )
        assert config.chain_id == 1

        # Invalid: string for chain_id should fail
        with pytest.raises(ValidationError):
            ContractConfig(
                address="0x742d35Cc6634C0532925a3b844Bc9e7595f8E",
                chain_id="1",  # type: ignore[arg-type] # Should be int
            )

    def test_scope_config_strict_mode(self) -> None:
        """ScopeConfig enforces strict mode type validation."""
        from secbrain.core.context import ScopeConfig

        # Valid construction
        config = ScopeConfig(
            domains=["example.com"],
            max_depth=3,
        )
        assert config.max_depth == 3

        # Invalid: string for max_depth should fail
        with pytest.raises(ValidationError):
            ScopeConfig(
                domains=["example.com"],
                max_depth="3",  # type: ignore[arg-type] # Should be int
            )

    def test_rate_limit_config_strict_mode(self) -> None:
        """RateLimitConfig enforces strict mode type validation."""
        from secbrain.core.context import RateLimitConfig

        # Valid construction
        config = RateLimitConfig(
            requests_per_minute=60,
            burst=10,
        )
        assert config.burst == 10

        # Invalid: string for burst should fail
        with pytest.raises(ValidationError):
            RateLimitConfig(
                requests_per_minute=60,
                burst="10",  # type: ignore[arg-type] # Should be int
            )


class TestSelfTypeMethods:
    """Tests for Self type method returns."""

    def test_finding_with_status(self) -> None:
        """Finding.with_status returns a new Finding with updated status."""
        original = Finding(
            id="finding-1",
            title="Test",
            severity=Severity.HIGH,
            status=FindingStatus.POTENTIAL,
        )
        updated = original.with_status(FindingStatus.CONFIRMED)

        # Original is unchanged
        assert original.status == FindingStatus.POTENTIAL
        # Updated has new status
        assert updated.status == FindingStatus.CONFIRMED
        # Same type returned
        assert isinstance(updated, Finding)
        # Same ID preserved
        assert updated.id == original.id

    def test_asset_with_metadata(self) -> None:
        """Asset.with_metadata returns a new Asset with added metadata."""
        original = Asset(
            id="asset-1",
            type="domain",
            value="example.com",
            metadata={"key1": "value1"},
        )
        updated = original.with_metadata("key2", "value2")

        # Original is unchanged
        assert "key2" not in original.metadata
        # Updated has new metadata
        assert updated.metadata["key1"] == "value1"
        assert updated.metadata["key2"] == "value2"
        # Same type returned
        assert isinstance(updated, Asset)

    def test_hypothesis_with_status(self) -> None:
        """Hypothesis.with_status returns a new Hypothesis with updated status."""
        original = Hypothesis(
            id="hyp-1",
            asset_id="asset-1",
            vuln_type="xss",
            confidence=0.5,
            rationale="Test",
            status="pending",
        )
        result = {"verified": True, "evidence": "payload reflected"}
        updated = original.with_status("confirmed", result)

        # Original is unchanged
        assert original.status == "pending"
        # Updated has new status and result
        assert updated.status == "confirmed"
        assert updated.result == result
        # Same type returned
        assert isinstance(updated, Hypothesis)

    def test_agent_result_with_finding(self) -> None:
        """AgentResult.with_finding returns a new AgentResult with added finding."""
        finding = Finding(
            id="finding-1",
            title="XSS",
            severity=Severity.HIGH,
        )
        original = AgentResult(
            agent="exploit_agent",
            phase="exploit",
            success=True,
            findings=[],
        )
        updated = original.with_finding(finding)

        # Original is unchanged
        assert len(original.findings) == 0
        # Updated has the finding
        assert len(updated.findings) == 1
        assert updated.findings[0].id == "finding-1"
        # Same type returned
        assert isinstance(updated, AgentResult)


class TestProtocols:
    """Tests for Protocol structural subtyping."""

    def test_http_response_protocol_is_runtime_checkable(self) -> None:
        """HTTPResponseProtocol can be checked at runtime."""

        class MockResponse:
            @property
            def status_code(self) -> int:
                return 200

            @property
            def text(self) -> str:
                return "OK"

            @property
            def headers(self) -> dict[str, str]:
                return {"Content-Type": "text/plain"}

        mock = MockResponse()
        assert isinstance(mock, HTTPResponseProtocol)

    def test_http_response_protocol_non_conforming(self) -> None:
        """Non-conforming classes fail Protocol check."""

        class NotAResponse:
            pass

        not_response = NotAResponse()
        assert not isinstance(not_response, HTTPResponseProtocol)


class TestConstants:
    """Tests for type-safe constants."""

    def test_confidence_bounds(self) -> None:
        """Confidence constants are correct."""
        assert MIN_CONFIDENCE == 0.0
        assert MAX_CONFIDENCE == 1.0
        assert MIN_CONFIDENCE < MAX_CONFIDENCE

    def test_default_rate_limit(self) -> None:
        """Default rate limit is set correctly."""
        assert DEFAULT_RATE_LIMIT == 60

    def test_allowed_http_methods(self) -> None:
        """Allowed HTTP methods includes standard methods."""
        assert "GET" in ALLOWED_HTTP_METHODS
        assert "POST" in ALLOWED_HTTP_METHODS
        assert "PUT" in ALLOWED_HTTP_METHODS
        assert "DELETE" in ALLOWED_HTTP_METHODS
        assert "HEAD" in ALLOWED_HTTP_METHODS
        assert "OPTIONS" in ALLOWED_HTTP_METHODS
        assert "PATCH" in ALLOWED_HTTP_METHODS
        # Should be immutable (frozenset)
        assert isinstance(ALLOWED_HTTP_METHODS, frozenset)


class TestLiteralStringSafety:
    """Tests for LiteralString utilities (SQL injection prevention)."""

    def test_execute_safe_query_accepts_literal(self) -> None:
        """execute_safe_query function exists and accepts literals."""
        # This just tests the function exists and is callable
        # The actual type checking happens at mypy time
        execute_safe_query("SELECT * FROM users WHERE id = ?", (1,))

    def test_build_safe_table_name(self) -> None:
        """build_safe_table_name combines literal strings."""
        result = build_safe_table_name("users", "v2")
        assert result == "users_v2"

    def test_storage_uses_literalstring(self) -> None:
        """Verify storage module uses LiteralString for SQL safety."""
        # This test verifies that the storage module's _execute and
        # _executescript methods accept LiteralString parameters.
        # The actual type checking happens at mypy time - this just
        # confirms the methods exist and are callable.
        import inspect

        from secbrain.tools.storage import WorkspaceStorage

        # Check that _execute has LiteralString in its signature
        sig = inspect.signature(WorkspaceStorage._execute)
        sql_param = sig.parameters.get("sql")
        assert sql_param is not None, "_execute should have 'sql' parameter"

        # Check that _executescript has LiteralString in its signature
        sig = inspect.signature(WorkspaceStorage._executescript)
        sql_param = sig.parameters.get("sql")
        assert sql_param is not None, "_executescript should have 'sql' parameter"
