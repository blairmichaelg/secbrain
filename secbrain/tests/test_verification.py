"""Tests for verification utilities."""

import pytest

from secbrain.verification import (
    BasicSQLiVerifier,
    EvidenceBundle,
    ReflectedXSSVerifier,
    VerificationResult,
    _sha256_text,
    get_default_verifier,
)


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


class TestReflectedXSSVerifier:
    """Test ReflectedXSSVerifier."""

    def test_name_attribute(self) -> None:
        """Test verifier has correct name."""
        verifier = ReflectedXSSVerifier()
        assert verifier.name == "reflected_xss"

    def test_verify_no_reflected_payload(self) -> None:
        """Test verification when no payload is reflected."""
        verifier = ReflectedXSSVerifier()
        results = [
            {"contains_payload": False, "response_snippet": "normal response"},
            {"contains_payload": False, "response_snippet": "another response"},
        ]
        
        result = verifier.verify(
            vuln_type="xss",
            target="https://example.com",
            results=results
        )
        
        assert result.success is False
        assert result.confidence == 0.1
        assert "No reflected payload observed" in result.reason
        assert result.evidence is None

    def test_verify_with_reflected_payload(self) -> None:
        """Test verification when payload is reflected."""
        verifier = ReflectedXSSVerifier()
        results = [
            {
        "contains_payload": True,
        "payload": "<script>alert(1)</script>",
        "status_code": 200,
        "response_length": 1500,
        "duration_ms": 120,
        "response_snippet": "Found: <script>alert(1)</script>"
            }
        ]
        
        result = verifier.verify(
            vuln_type="reflected_xss",
            target="https://example.com/search",
            results=results
        )
        
        assert result.success is True
        assert result.confidence == 0.75
        assert "Payload reflected" in result.reason
        assert result.evidence is not None
        assert result.evidence.verifier == "reflected_xss"
        assert result.evidence.vuln_type == "reflected_xss"
        assert len(result.evidence.observations) == 1

    def test_verify_multiple_reflections(self) -> None:
        """Test verification with multiple reflected payloads."""
        verifier = ReflectedXSSVerifier()
        results = [
            {
        "contains_payload": True,
        "payload": "<script>1</script>",
        "status_code": 200,
        "response_length": 1000,
        "duration_ms": 100,
        "response_snippet": "Test 1"
            },
            {
        "contains_payload": True,
        "payload": "<img src=x>",
        "status_code": 200,
        "response_length": 1100,
        "duration_ms": 105,
        "response_snippet": "Test 2"
            },
            {
        "contains_payload": True,
        "payload": "alert(1)",
        "status_code": 200,
        "response_length": 1200,
        "duration_ms": 110,
        "response_snippet": "Test 3"
            },
            {
        "contains_payload": True,
        "payload": "test4",
        "status_code": 200,
        "response_length": 1300,
        "duration_ms": 115,
        "response_snippet": "Test 4"
            }
        ]
        
        result = verifier.verify(
            vuln_type="xss",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True
        # Should only include first 3 observations
        assert len(result.evidence.observations) == 3

    def test_verify_observations_include_required_fields(self) -> None:
        """Test that observations include all required fields."""
        verifier = ReflectedXSSVerifier()
        results = [
            {
        "contains_payload": True,
        "payload": "test",
        "status_code": 200,
        "response_length": 500,
        "duration_ms": 50,
        "response_snippet": "test response"
            }
        ]
        
        result = verifier.verify(
            vuln_type="xss",
            target="https://test.com",
            results=results
        )
        
        obs = result.evidence.observations[0]
        assert "payload" in obs
        assert "status_code" in obs
        assert "response_length" in obs
        assert "duration_ms" in obs
        assert "response_snippet_sha256" in obs

    def test_verify_empty_results(self) -> None:
        """Test verification with empty results."""
        verifier = ReflectedXSSVerifier()
        result = verifier.verify(
            vuln_type="xss",
            target="https://test.com",
            results=[]
        )
        
        assert result.success is False
        assert result.confidence == 0.1


class TestBasicSQLiVerifier:
    """Test BasicSQLiVerifier."""

    def test_name_attribute(self) -> None:
        """Test verifier has correct name."""
        verifier = BasicSQLiVerifier()
        assert verifier.name == "basic_sqli"

    def test_verify_no_sql_indicators(self) -> None:
        """Test verification when no SQL indicators present."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "' OR 1=1--",
        "status_code": 200,
        "response_snippet": "normal response",
        "duration_ms": 100
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://example.com/login",
            results=results
        )
        
        assert result.success is False
        assert result.confidence == 0.1
        assert "No SQL error patterns" in result.reason
        assert result.evidence is None

    def test_verify_sql_error_detected(self) -> None:
        """Test verification when SQL error is detected."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "' OR 1=1--",
        "status_code": 500,
        "response_snippet": "You have an error in your SQL syntax",
        "response_length": 800,
        "duration_ms": 150
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://example.com/api",
            results=results
        )
        
        assert result.success is True
        assert result.confidence == 0.65  # Higher confidence for error signature
        assert "SQLi signal detected" in result.reason
        assert result.evidence is not None
        assert len(result.evidence.observations) == 1
        assert result.evidence.observations[0]["match"] == "db_error_signature"

    def test_verify_mysql_error(self) -> None:
        """Test detection of MySQL error."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "test'",
        "status_code": 500,
        "response_snippet": "Warning: mysql_fetch_array(): supplied argument",
        "duration_ms": 120
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True
        assert result.evidence.observations[0]["match"] == "db_error_signature"

    def test_verify_time_delay(self) -> None:
        """Test detection of time-based SQL injection."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "1' AND SLEEP(5)--",
        "status_code": 200,
        "response_snippet": "Loading...",
        "duration_ms": 5200
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True
        assert result.confidence == 0.55  # Lower confidence for time delay
        assert result.evidence.observations[0]["match"] == "time_delay"

    def test_verify_waitfor_delay(self) -> None:
        """Test detection of WAITFOR DELAY SQL injection."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "1'; WAITFOR DELAY '00:00:05'--",
        "status_code": 200,
        "response_snippet": "Processing...",
        "duration_ms": 5100
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True
        assert result.evidence.observations[0]["match"] == "time_delay"

    def test_verify_multiple_indicators(self) -> None:
        """Test verification with multiple SQL injection indicators."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "1'",
        "status_code": 500,
        "response_snippet": "SQL syntax error near '1''",
        "duration_ms": 100
            },
            {
        "payload": "1' OR 1=1--",
        "status_code": 200,
        "response_snippet": "postgres error: syntax error",
        "duration_ms": 110
            },
            {
        "payload": "1' UNION SELECT NULL--",
        "status_code": 500,
        "response_snippet": "ODBC Driver error",
        "duration_ms": 105
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True
        assert result.confidence == 0.65
        assert len(result.evidence.observations) == 3

    def test_verify_limits_observations_to_five(self) -> None:
        """Test that observations are limited to 5."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": f"test{i}",
        "status_code": 500,
        "response_snippet": f"SQL syntax error {i}",
        "duration_ms": 100 + i
            }
            for i in range(10)
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True
        # Should be limited to 5 observations
        assert len(result.evidence.observations) <= 5

    def test_verify_case_insensitive_detection(self) -> None:
        """Test that error detection is case insensitive."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "test",
        "status_code": 500,
        "response_snippet": "MYSQL ERROR: SYNTAX",
        "duration_ms": 100
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is True

    def test_verify_time_delay_insufficient(self) -> None:
        """Test that short delays are not flagged."""
        verifier = BasicSQLiVerifier()
        results = [
            {
        "payload": "1' AND SLEEP(5)--",
        "status_code": 200,
        "response_snippet": "Fast response",
        "duration_ms": 500  # Less than 4000ms threshold
            }
        ]
        
        result = verifier.verify(
            vuln_type="sqli",
            target="https://test.com",
            results=results
        )
        
        assert result.success is False


class TestGetDefaultVerifier:
    """Test get_default_verifier function."""

    def test_get_xss_verifier(self) -> None:
        """Test getting XSS verifier."""
        verifier = get_default_verifier("xss")
        assert isinstance(verifier, ReflectedXSSVerifier)

    def test_get_xss_verifier_case_insensitive(self) -> None:
        """Test XSS verifier retrieval is case insensitive."""
        verifier = get_default_verifier("XSS")
        assert isinstance(verifier, ReflectedXSSVerifier)
        
        verifier = get_default_verifier("reflected_xss")
        assert isinstance(verifier, ReflectedXSSVerifier)

    def test_get_sqli_verifier(self) -> None:
        """Test getting SQLi verifier."""
        verifier = get_default_verifier("sqli")
        assert isinstance(verifier, BasicSQLiVerifier)

    def test_get_sqli_verifier_variations(self) -> None:
        """Test SQLi verifier with various inputs."""
        assert isinstance(get_default_verifier("sqli"), BasicSQLiVerifier)
        assert isinstance(get_default_verifier("SQLI"), BasicSQLiVerifier)
        assert isinstance(get_default_verifier("sql"), BasicSQLiVerifier)
        assert isinstance(get_default_verifier("SQL Injection"), BasicSQLiVerifier)

    def test_get_unknown_verifier(self) -> None:
        """Test getting verifier for unknown type."""
        verifier = get_default_verifier("unknown_vuln")
        assert verifier is None

    def test_get_verifier_empty_string(self) -> None:
        """Test getting verifier with empty string."""
        verifier = get_default_verifier("")
        assert verifier is None

    def test_get_verifier_none(self) -> None:
        """Test getting verifier with None."""
        verifier = get_default_verifier(None)  # type: ignore
        assert verifier is None


class TestSha256Text:
    """Test the _sha256_text helper function."""

    def test_sha256_basic(self) -> None:
        """Test basic SHA256 hashing."""
        result = _sha256_text("test")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 produces 64 hex characters

    def test_sha256_consistent(self) -> None:
        """Test that same input produces same hash."""
        hash1 = _sha256_text("test string")
        hash2 = _sha256_text("test string")
        assert hash1 == hash2

    def test_sha256_different_inputs(self) -> None:
        """Test that different inputs produce different hashes."""
        hash1 = _sha256_text("test1")
        hash2 = _sha256_text("test2")
        assert hash1 != hash2

    def test_sha256_empty_string(self) -> None:
        """Test hashing empty string."""
        result = _sha256_text("")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_sha256_unicode(self) -> None:
        """Test hashing unicode strings."""
        result = _sha256_text("Hello 世界 🔒")
        assert isinstance(result, str)
        assert len(result) == 64
