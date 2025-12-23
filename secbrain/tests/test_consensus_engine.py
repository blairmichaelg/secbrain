"""Tests for consensus engine."""

from unittest.mock import Mock

from secbrain.core.consensus_engine import ConsensusEngine, ConsensusResult


class TestConsensusResult:
    """Test ConsensusResult dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic ConsensusResult initialization."""
        result = ConsensusResult(verified=True, confidence=0.8)
        assert result.verified is True
        assert result.confidence == 0.8
        assert result.evidence is None

    def test_with_evidence(self) -> None:
        """Test ConsensusResult with evidence."""
        evidence = {"type": "xss", "details": "reflected"}
        result = ConsensusResult(verified=True, confidence=0.9, evidence=evidence)
        assert result.verified is True
        assert result.confidence == 0.9
        assert result.evidence == evidence


class TestConsensusEngine:
    """Test ConsensusEngine class."""

    def test_decide_empty_results(self) -> None:
        """Test decide with empty results list."""
        engine = ConsensusEngine()
        result = engine.decide([])
        
        assert result.verified is False
        assert result.confidence == 0.0
        assert result.evidence is None

    def test_decide_single_verified(self) -> None:
        """Test decide with single verified result."""
        engine = ConsensusEngine()
        
        mock_result = Mock()
        mock_result.verified = True
        mock_result.confidence_score = 0.9
        mock_result.evidence = None
        
        result = engine.decide([mock_result])
        
        assert result.verified is True
        assert result.confidence == 0.9

    def test_decide_single_not_verified(self) -> None:
        """Test decide with single unverified result."""
        engine = ConsensusEngine()
        
        mock_result = Mock()
        mock_result.verified = False
        mock_result.confidence_score = 0.3
        mock_result.evidence = None
        
        result = engine.decide([mock_result])
        
        assert result.verified is False
        assert result.confidence == 0.3

    def test_decide_all_verified(self) -> None:
        """Test decide with all results verified."""
        engine = ConsensusEngine()
        
        mock1 = Mock()
        mock1.verified = True
        mock1.confidence_score = 0.8
        mock1.evidence = None
        
        mock2 = Mock()
        mock2.verified = True
        mock2.confidence_score = 0.9
        mock2.evidence = None
        
        result = engine.decide([mock1, mock2])
        
        assert result.verified is True
        assert abs(result.confidence - 0.85) < 0.001  # Average of 0.8 and 0.9

    def test_decide_mixed_verification(self) -> None:
        """Test decide with mixed verification results."""
        engine = ConsensusEngine()
        
        verified = Mock()
        verified.verified = True
        verified.confidence_score = 0.9
        verified.evidence = None
        
        not_verified = Mock()
        not_verified.verified = False
        not_verified.confidence_score = 0.4
        not_verified.evidence = None
        
        result = engine.decide([verified, not_verified])
        
        # Any verification should make overall result verified
        assert result.verified is True
        assert result.confidence == 0.65  # Average of 0.9 and 0.4

    def test_decide_none_verified(self) -> None:
        """Test decide with no results verified."""
        engine = ConsensusEngine()
        
        mock1 = Mock()
        mock1.verified = False
        mock1.confidence_score = 0.3
        mock1.evidence = None
        
        mock2 = Mock()
        mock2.verified = False
        mock2.confidence_score = 0.2
        mock2.evidence = None
        
        result = engine.decide([mock1, mock2])
        
        assert result.verified is False
        assert result.confidence == 0.25  # Average of 0.3 and 0.2

    def test_decide_with_evidence_from_highest_confidence(self) -> None:
        """Test that evidence is taken from highest confidence result."""
        engine = ConsensusEngine()
        
        low_conf = Mock()
        low_conf.verified = True
        low_conf.confidence_score = 0.6
        low_conf.evidence = Mock()
        low_conf.evidence.to_dict = lambda: {"source": "low"}
        
        high_conf = Mock()
        high_conf.verified = True
        high_conf.confidence_score = 0.9
        high_conf.evidence = Mock()
        high_conf.evidence.to_dict = lambda: {"source": "high"}
        
        result = engine.decide([low_conf, high_conf])
        
        assert result.evidence == {"source": "high"}

    def test_decide_with_evidence_no_to_dict(self) -> None:
        """Test evidence handling when it doesn't have to_dict method."""
        engine = ConsensusEngine()
        
        mock_result = Mock()
        mock_result.verified = True
        mock_result.confidence_score = 0.8
        mock_result.evidence = {"raw": "evidence"}
        
        result = engine.decide([mock_result])
        
        assert result.evidence == {"raw": "evidence"}

    def test_decide_average_confidence_calculation(self) -> None:
        """Test confidence score averaging with multiple results."""
        engine = ConsensusEngine()
        
        results = []
        for score in [0.1, 0.3, 0.5, 0.7, 0.9]:
            mock = Mock()
            mock.verified = False
            mock.confidence_score = score
            mock.evidence = None
            results.append(mock)
        
        result = engine.decide(results)
        
        # Average of [0.1, 0.3, 0.5, 0.7, 0.9] = 0.5
        assert result.confidence == 0.5

    def test_decide_handles_none_confidence_scores(self) -> None:
        """Test decide handles None confidence scores."""
        engine = ConsensusEngine()
        
        mock1 = Mock()
        mock1.verified = True
        mock1.confidence_score = None
        mock1.evidence = None
        
        mock2 = Mock()
        mock2.verified = True
        mock2.confidence_score = 0.8
        mock2.evidence = None
        
        result = engine.decide([mock1, mock2])
        
        # 0.0 (from None) + 0.8 / 2 = 0.4
        assert result.confidence == 0.4

    def test_decide_highest_confidence_with_tie(self) -> None:
        """Test evidence selection when multiple results have same highest confidence."""
        engine = ConsensusEngine()
        
        mock1 = Mock()
        mock1.verified = True
        mock1.confidence_score = 0.9
        mock1.evidence = Mock()
        mock1.evidence.to_dict = lambda: {"source": "first"}
        
        mock2 = Mock()
        mock2.verified = True
        mock2.confidence_score = 0.9
        mock2.evidence = Mock()
        mock2.evidence.to_dict = lambda: {"source": "second"}
        
        result = engine.decide([mock1, mock2])
        
        # Should pick one of them (max() is deterministic)
        assert result.evidence in [{"source": "first"}, {"source": "second"}]

    def test_decide_no_evidence_available(self) -> None:
        """Test decide when results have no evidence."""
        engine = ConsensusEngine()
        
        mock1 = Mock()
        mock1.verified = True
        mock1.confidence_score = 0.8
        mock1.evidence = None
        
        mock2 = Mock()
        mock2.verified = True
        mock2.confidence_score = 0.9
        mock2.evidence = None
        
        result = engine.decide([mock1, mock2])
        
        assert result.evidence is None

    def test_decide_accepts_iterable(self) -> None:
        """Test that decide accepts any iterable, not just list."""
        engine = ConsensusEngine()
        
        def result_generator():
            mock = Mock()
            mock.verified = True
            mock.confidence_score = 0.8
            mock.evidence = None
            yield mock
        
        result = engine.decide(result_generator())
        
        assert result.verified is True
        assert result.confidence == 0.8
