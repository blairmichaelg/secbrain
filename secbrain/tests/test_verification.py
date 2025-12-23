"""Tests for verification utilities."""

import pytest

from secbrain.verification import EvidenceBundle, VerificationResult


class TestEvidenceBundle:
    """Test EvidenceBundle dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic EvidenceBundle initialization."""
        bundle = EvidenceBundle(
            verifier="test_verifier",
            target="https://example.com",
            vuln_type="xss",
            created_at="2024-01-01T00:00:00Z",
        )
        assert bundle.verifier == "test_verifier"
        assert bundle.target == "https://example.com"
        assert bundle.vuln_type == "xss"
        assert bundle.created_at == "2024-01-01T00:00:00Z"
        assert bundle.observations == []

    def test_with_observations(self) -> None:
        """Test EvidenceBundle with observations."""
        observations = [
            {"type": "response_code", "value": 200},
            {"type": "reflection", "value": "script reflected"},
        ]
        bundle = EvidenceBundle(
            verifier="xss_verifier",
            target="https://test.com/search",
            vuln_type="reflected_xss",
            created_at="2024-01-15T12:00:00Z",
            observations=observations,
        )
        assert bundle.observations == observations
        assert len(bundle.observations) == 2

    def test_is_frozen(self) -> None:
        """Test that EvidenceBundle is immutable."""
        bundle = EvidenceBundle(
            verifier="test",
            target="target",
            vuln_type="test",
            created_at="2024-01-01T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            bundle.verifier = "new_verifier"  # type: ignore

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        observations = [{"key": "value"}]
        bundle = EvidenceBundle(
            verifier="sql_verifier",
            target="https://api.test.com/user",
            vuln_type="sqli",
            created_at="2024-02-01T10:30:00Z",
            observations=observations,
        )
        result = bundle.to_dict()
        assert result["verifier"] == "sql_verifier"
        assert result["target"] == "https://api.test.com/user"
        assert result["vuln_type"] == "sqli"
        assert result["created_at"] == "2024-02-01T10:30:00Z"
        assert result["observations"] == observations

    def test_to_dict_empty_observations(self) -> None:
        """Test to_dict with empty observations."""
        bundle = EvidenceBundle(
            verifier="test",
            target="target",
            vuln_type="test",
            created_at="2024-01-01T00:00:00Z",
        )
        result = bundle.to_dict()
        assert result["observations"] == []


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic VerificationResult initialization."""
        result = VerificationResult(
            success=True,
            confidence=0.95,
            reason="Exploit successful",
        )
        assert result.success is True
        assert result.confidence == 0.95
        assert result.reason == "Exploit successful"
        assert result.evidence is None

    def test_with_evidence(self) -> None:
        """Test VerificationResult with evidence."""
        evidence = EvidenceBundle(
            verifier="test_verifier",
            target="https://example.com",
            vuln_type="xss",
            created_at="2024-01-01T00:00:00Z",
        )
        result = VerificationResult(
            success=True,
            confidence=0.8,
            reason="XSS confirmed",
            evidence=evidence,
        )
        assert result.evidence == evidence

    def test_is_frozen(self) -> None:
        """Test that VerificationResult is immutable."""
        result = VerificationResult(
            success=True,
            confidence=0.5,
            reason="Test",
        )
        with pytest.raises(AttributeError):
            result.success = False  # type: ignore

    def test_to_dict_without_evidence(self) -> None:
        """Test to_dict without evidence."""
        result = VerificationResult(
            success=False,
            confidence=0.3,
            reason="No vulnerability found",
        )
        result_dict = result.to_dict()
        assert result_dict["success"] is False
        assert result_dict["confidence"] == 0.3
        assert result_dict["reason"] == "No vulnerability found"
        assert result_dict["evidence"] is None

    def test_to_dict_with_evidence(self) -> None:
        """Test to_dict with evidence."""
        evidence = EvidenceBundle(
            verifier="sqli_verifier",
            target="https://test.com/api",
            vuln_type="sqli",
            created_at="2024-03-01T15:45:00Z",
            observations=[{"type": "error", "value": "SQL syntax error"}],
        )
        result = VerificationResult(
            success=True,
            confidence=0.9,
            reason="SQL injection confirmed",
            evidence=evidence,
        )
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["confidence"] == 0.9
        assert result_dict["reason"] == "SQL injection confirmed"
        assert result_dict["evidence"] is not None
        assert result_dict["evidence"]["verifier"] == "sqli_verifier"
        assert result_dict["evidence"]["vuln_type"] == "sqli"

    def test_failed_verification(self) -> None:
        """Test failed verification result."""
        result = VerificationResult(
            success=False,
            confidence=0.0,
            reason="Target not vulnerable",
        )
        assert result.success is False
        assert result.confidence == 0.0
        assert result.evidence is None

    def test_partial_confidence(self) -> None:
        """Test verification with partial confidence."""
        result = VerificationResult(
            success=True,
            confidence=0.5,
            reason="Some indicators present",
        )
        assert result.success is True
        assert result.confidence == 0.5
