"""Tests for Immunefi integration and advanced research features."""

import pytest

from secbrain.agents.advanced_research_agent import AdvancedResearchAgent, ResearchFinding
from secbrain.tools.bounty_metrics import BountyMetricsTracker, BountySubmission
from secbrain.tools.immunefi_client import ImmunefiClient, ImmunefiProgram


class TestImmunefiClient:
    """Test Immunefi client functionality."""

    @pytest.mark.asyncio
    async def test_get_all_programs(self):
        """Test fetching all programs."""
        client = ImmunefiClient()
        try:
            programs = await client.get_all_programs()

            assert len(programs) > 0
            assert all(isinstance(p, ImmunefiProgram) for p in programs)

            # Check program has required fields
            program = programs[0]
            assert program.id
            assert program.name
            assert program.max_bounty > 0

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_high_value_programs(self):
        """Test filtering high-value programs."""
        client = ImmunefiClient()
        try:
            programs = await client.get_high_value_programs(
                min_bounty=500_000,
                limit=5,
            )

            assert len(programs) <= 5
            assert all(p.max_bounty >= 500_000 for p in programs)

            # Should be sorted by priority
            if len(programs) > 1:
                priorities = [p.get_priority_score() for p in programs]
                assert priorities == sorted(priorities, reverse=True)

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_program_by_id(self):
        """Test fetching specific program."""
        client = ImmunefiClient()
        try:
            # Get all programs first to find a valid ID
            programs = await client.get_all_programs()
            assert len(programs) > 0

            # Test with first available program
            first_program_id = programs[0].id
            program = await client.get_program_by_id(first_program_id)

            assert program is not None
            assert program.id == first_program_id
            assert program.max_bounty > 0

            # Test non-existent program
            missing = await client.get_program_by_id("nonexistent")
            assert missing is None

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_trending_vulnerabilities(self):
        """Test trending vulnerabilities."""
        client = ImmunefiClient()
        try:
            trends = await client.get_trending_vulnerabilities(days=90)

            assert len(trends) > 0

            # Check trend structure
            trend = trends[0]
            assert trend.vulnerability_type
            assert trend.severity in ["critical", "high", "medium", "low"]
            assert trend.occurrences > 0
            assert trend.avg_bounty > 0

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_program_priority_scoring(self):
        """Test program priority scoring algorithm."""
        client = ImmunefiClient()
        try:
            programs = await client.get_all_programs()

            for program in programs:
                score = program.get_priority_score()

                # Score should be 0-100
                assert 0 <= score <= 100

                # Higher bounties should generally score higher
                if program.max_bounty >= 1_000_000:
                    assert score >= 40  # At least bounty points

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_program_intelligence(self):
        """Test comprehensive program intelligence."""
        client = ImmunefiClient()
        try:
            # Get all programs first to find a valid ID
            programs = await client.get_all_programs()
            assert len(programs) > 0

            # Use first available program
            first_program_id = programs[0].id
            intel = await client.get_program_intelligence(first_program_id)

            assert "program" in intel
            assert "statistics" in intel
            assert "recommended_focus_areas" in intel
            assert "relevant_trends" in intel
            assert "similar_programs" in intel

            # Check program details
            program_data = intel["program"]
            assert program_data["id"] == first_program_id
            assert program_data["max_bounty"] > 0

        finally:
            await client.close()


class TestAdvancedResearchAgent:
    """Test advanced research agent."""

    @pytest.fixture
    def mock_context(self, tmp_path):
        """Create mock run context."""
        from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig

        scope = ScopeConfig(
            in_scope_domains=[],
            in_scope_ips=[],
            out_of_scope_domains=[],
        )

        program = ProgramConfig(
            name="test",
            platform="test",
            focus_areas=[],
            rules=[],
            rewards={},
        )

        return RunContext(
            scope=scope,
            program=program,
            workspace_path=tmp_path,
            dry_run=True,
        )

    @pytest.mark.asyncio
    async def test_research_emerging_patterns(self, mock_context):
        """Test emerging pattern research."""
        agent = AdvancedResearchAgent(
            run_context=mock_context,
            research_client=None,  # Use curated data
        )

        findings = await agent.research_emerging_patterns(timeframe_days=90)

        assert len(findings) > 0
        assert all(isinstance(f, ResearchFinding) for f in findings)

        # Check finding structure
        finding = findings[0]
        assert finding.title
        assert finding.description
        assert finding.severity in ["critical", "high", "medium", "low"]
        assert 0.0 <= finding.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_generate_novel_hypotheses(self, mock_context):
        """Test novel hypothesis generation."""
        agent = AdvancedResearchAgent(
            run_context=mock_context,
            research_client=None,
        )

        hypotheses = await agent.generate_novel_hypotheses(
            target_contracts=["Contract1", "Contract2"],
            context="Test analysis",
        )

        assert len(hypotheses) > 0

        # Check hypothesis structure
        hyp = hypotheses[0]
        assert "title" in hyp or "vulnerability_type" in hyp
        assert "severity" in hyp
        assert "confidence" in hyp

    @pytest.mark.asyncio
    async def test_curated_emerging_patterns(self, mock_context):
        """Test curated emerging patterns are valid."""
        agent = AdvancedResearchAgent(
            run_context=mock_context,
            research_client=None,
        )

        findings = agent._get_curated_emerging_patterns()

        assert len(findings) >= 5  # Should have multiple patterns

        # Verify critical patterns are included
        pattern_names = [f.title for f in findings]

        # Check for key 2024-2025 patterns
        assert any("Intent" in name or "intent" in name for name in pattern_names)
        assert any("Reentrancy" in name or "reentrancy" in name for name in pattern_names)
        assert any("ERC-4337" in name or "Account" in name for name in pattern_names)

        # All should have attack vectors
        for finding in findings:
            assert len(finding.attack_vectors) > 0
            assert finding.mitigation


class TestBountyMetricsTracker:
    """Test bounty metrics tracking."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create metrics tracker."""
        return BountyMetricsTracker(tmp_path / "metrics")

    def test_record_submission(self, tracker):
        """Test recording a submission."""
        submission = BountySubmission(
            id="test-001",
            program="TestProgram",
            platform="immunefi",
            submitted_at="2024-12-25T10:00:00Z",
            vulnerability_type="Reentrancy",
            severity="critical",
            title="Test Finding",
            description="Test description",
            status="accepted",
            bounty_amount=10_000.0,
            confidence_score=0.85,
        )

        tracker.record_submission(submission)

        # Check metrics updated
        metrics = tracker.get_overall_metrics()
        assert metrics["total_submissions"] == 1
        assert metrics["accepted"] == 1
        assert metrics["total_earned"] == 10_000.0

    def test_program_metrics(self, tracker):
        """Test program-specific metrics."""
        # Record multiple submissions
        for i in range(3):
            submission = BountySubmission(
                id=f"test-{i}",
                program="TestProgram",
                platform="immunefi",
                submitted_at=f"2024-12-25T10:{i:02d}:00Z",
                vulnerability_type="Reentrancy",
                severity="high",
                title=f"Finding {i}",
                description="Test",
                status="accepted" if i < 2 else "rejected",
                bounty_amount=5_000.0 if i < 2 else 0.0,
                confidence_score=0.8,
            )
            tracker.record_submission(submission)

        program_metrics = tracker.get_program_metrics("TestProgram", "immunefi")

        assert program_metrics is not None
        assert program_metrics.total_submissions == 3
        assert program_metrics.accepted_submissions == 2
        assert program_metrics.rejected_submissions == 1
        assert program_metrics.acceptance_rate == 2/3
        assert program_metrics.total_earned == 10_000.0

    def test_pattern_learning(self, tracker):
        """Test vulnerability pattern learning."""
        # Record submissions with same pattern
        for i in range(4):
            submission = BountySubmission(
                id=f"test-{i}",
                program="TestProgram",
                platform="immunefi",
                submitted_at=f"2024-12-25T10:{i:02d}:00Z",
                vulnerability_type="Reentrancy",
                severity="high",
                title=f"Finding {i}",
                description="Test",
                status="accepted" if i % 2 == 0 else "rejected",
                bounty_amount=5_000.0 if i % 2 == 0 else 0.0,
                detection_method="static_analysis",
                confidence_score=0.8,
            )
            tracker.record_submission(submission)

        pattern = tracker.get_pattern_learning("Reentrancy")

        assert pattern is not None
        assert pattern.times_submitted == 4
        assert pattern.times_accepted == 2
        assert pattern.detection_effectiveness == 0.5
        assert pattern.avg_bounty == 5_000.0

    def test_should_submit_decision(self, tracker):
        """Test submission decision support."""
        # Record some successful submissions
        for i in range(5):
            submission = BountySubmission(
                id=f"test-{i}",
                program="TestProgram",
                platform="immunefi",
                submitted_at=f"2024-12-25T10:{i:02d}:00Z",
                vulnerability_type="Oracle Manipulation",
                severity="critical",
                title=f"Finding {i}",
                description="Test",
                status="accepted",
                bounty_amount=15_000.0,
                confidence_score=0.8,
            )
            tracker.record_submission(submission)

        # Test decision with high confidence
        decision = tracker.should_submit(
            vulnerability_type="Oracle Manipulation",
            confidence=0.85,
        )
        assert decision["should_submit"] is True

        # Test decision with low confidence
        decision = tracker.should_submit(
            vulnerability_type="Oracle Manipulation",
            confidence=0.5,
        )
        # Might still suggest submission based on pattern success
        assert "reason" in decision
        assert "pattern_stats" in decision

    def test_learning_insights(self, tracker):
        """Test learning insights generation."""
        # Record mixed results
        patterns = [
            ("High Value Pattern", "accepted", 50_000.0, 5, 4),
            ("Low Confidence Pattern", "rejected", 0.0, 5, 1),
        ]

        for pattern_name, _status, bounty, count, accepted_count in patterns:
            for i in range(count):
                submission = BountySubmission(
                    id=f"{pattern_name}-{i}",
                    program="TestProgram",
                    platform="immunefi",
                    submitted_at=f"2024-12-25T{i:02d}:00:00Z",
                    vulnerability_type=pattern_name,
                    severity="high",
                    title=f"Finding {i}",
                    description="Test",
                    status="accepted" if i < accepted_count else "rejected",
                    bounty_amount=bounty if i < accepted_count else 0.0,
                    confidence_score=0.8,
                )
                tracker.record_submission(submission)

        insights = tracker.get_learning_insights()

        assert "high_value_patterns" in insights
        assert "low_confidence_patterns" in insights
        assert "recommended_focus_areas" in insights

        # High value pattern should be recommended
        high_value = insights["high_value_patterns"]
        assert any(p["pattern"] == "High Value Pattern" for p in high_value)

        # Low confidence pattern should be flagged
        low_conf = insights["low_confidence_patterns"]
        assert any(p["pattern"] == "Low Confidence Pattern" for p in low_conf)


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test integration between components."""
    from secbrain.tools.immunefi_client import get_immunefi_intelligence

    # Get intelligence
    intel = await get_immunefi_intelligence(min_bounty=500_000)

    assert "high_value_programs" in intel
    assert "trending_vulnerabilities" in intel

    # Verify we have actionable data
    assert len(intel["high_value_programs"]) > 0
    assert len(intel["trending_vulnerabilities"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
