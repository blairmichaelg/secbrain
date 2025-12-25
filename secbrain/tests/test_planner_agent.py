"""Tests for PlannerAgent."""

from __future__ import annotations

import json

import pytest

from secbrain.agents.planner_agent import PlannerAgent


class MockRunContext:
    """Mock RunContext for testing."""

    def __init__(self, run_id: str = "test-run-001", killed: bool = False):
        self.run_id = run_id
        self._killed = killed

    def is_killed(self):
        return self._killed


class MockWorkerModel:
    """Mock worker model for testing."""

    def __init__(self, response: str | None = None):
        self.response = response or json.dumps({
            "phases": [
                {
                    "phase": "recon",
                    "objectives": ["Discover assets"],
                    "tools": ["nmap", "subfinder"],
                    "time_estimate": "2 hours",
                    "success_criteria": ["Find all domains"],
                },
                {
                    "phase": "hypothesis",
                    "objectives": ["Identify vulnerabilities"],
                    "tools": ["static analysis"],
                    "time_estimate": "4 hours",
                    "success_criteria": ["Generate hypotheses"],
                },
            ],
            "priority_areas": ["authentication", "authorization"],
        })

    async def generate(self, prompt: str, system: str | None = None, **kwargs):
        """Mock worker model generate method."""
        class Response:
            def __init__(self, content: str):
                self.content = content

        return Response(self.response)


class MockAdvisorModel:
    """Mock advisor model for testing."""

    def __init__(self, review: dict | None = None):
        self.review = review or {
            "approved": True,
            "concerns": [],
            "suggestions": ["Consider adding API testing"],
        }

    async def generate(self, prompt: str, system: str | None = None, **kwargs):
        """Mock advisor model generate method."""
        class Response:
            def __init__(self, content: str):
                self.content = content

        return Response(json.dumps(self.review))


class MockResearchClient:
    """Mock research client for testing."""

    def __init__(self, research_response: dict | None = None):
        self.research_response = research_response or {
            "answer": "Focus on OWASP Top 10 vulnerabilities",
            "confidence": 0.8,
            "sources": ["owasp.org"],
        }

    async def ask_research(self, question: str, context: str = "", **kwargs) -> dict:
        """Mock ask_research method."""
        return self.research_response


class MockStorage:
    """Mock storage for testing."""

    def __init__(self):
        self.saved_assets = []

    async def save_asset(self, asset: dict):
        """Mock save_asset method."""
        self.saved_assets.append(asset)


@pytest.mark.asyncio
async def test_planner_agent_initialization():
    """Test PlannerAgent initialization."""
    run_context = MockRunContext()
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
    )

    assert agent.name == "planner"
    assert agent.phase == "plan"
    assert agent.run_context == run_context


@pytest.mark.asyncio
async def test_planner_agent_run_basic():
    """Test basic planner agent execution."""
    run_context = MockRunContext()
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()
    storage = MockStorage()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
        storage=storage,
    )

    result = await agent.run(
        ingest_data={
            "domains": ["example.com"],
            "focus_areas": ["authentication"],
            "rules": ["Test only in scope"],
        }
    )

    assert result.success is True
    assert "plan" in result.data
    assert "review" in result.data
    assert "phases" in result.data
    assert len(result.data["phases"]) > 0


@pytest.mark.asyncio
async def test_planner_agent_run_with_research():
    """Test planner agent with research enhancement."""
    run_context = MockRunContext()
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()
    research_client = MockResearchClient()
    storage = MockStorage()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
        research_client=research_client,
        storage=storage,
    )

    result = await agent.run(
        ingest_data={
            "domains": ["example.com"],
            "focus_areas": ["api_security"],
        }
    )

    assert result.success is True
    assert result.data.get("plan") is not None


@pytest.mark.asyncio
async def test_planner_agent_kill_switch():
    """Test planner agent respects kill switch."""
    run_context = MockRunContext(killed=True)
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
    )

    result = await agent.run(ingest_data={})

    assert result.success is False
    assert "Kill-switch" in result.message


@pytest.mark.asyncio
async def test_planner_agent_with_concerns():
    """Test planner agent adjusts plan when advisor has concerns."""
    run_context = MockRunContext()
    worker_model = MockWorkerModel()

    # Advisor with concerns
    advisor_review = {
        "approved": False,
        "concerns": ["Missing input validation testing"],
        "suggestions": ["Add validation phase"],
    }
    advisor_model = MockAdvisorModel(review=advisor_review)
    storage = MockStorage()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
        storage=storage,
    )

    result = await agent.run(ingest_data={"domains": ["example.com"]})

    # Should still succeed but plan is adjusted
    assert result.success is True
    assert result.data.get("review", {}).get("concerns") is not None


@pytest.mark.asyncio
async def test_planner_agent_storage_integration():
    """Test planner agent saves plan to storage."""
    run_context = MockRunContext(run_id="test-123")
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()
    storage = MockStorage()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
        storage=storage,
    )

    await agent.run(ingest_data={"domains": ["example.com"]})

    # Verify plan was saved
    assert len(storage.saved_assets) == 1
    saved_plan = storage.saved_assets[0]
    assert saved_plan["id"] == "plan-test-123"
    assert saved_plan["type"] == "plan"
    assert "value" in saved_plan


@pytest.mark.asyncio
async def test_planner_agent_empty_ingest_data():
    """Test planner agent handles empty ingest data."""
    run_context = MockRunContext()
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
    )

    result = await agent.run(ingest_data={})

    # Should still create a plan even with empty data
    assert result.success is True
    assert "plan" in result.data


@pytest.mark.asyncio
async def test_planner_agent_next_actions():
    """Test planner agent returns appropriate next actions."""
    run_context = MockRunContext()
    worker_model = MockWorkerModel()
    advisor_model = MockAdvisorModel()

    agent = PlannerAgent(
        run_context=run_context,
        worker_model=worker_model,
        advisor_model=advisor_model,
    )

    result = await agent.run(ingest_data={"domains": ["example.com"]})

    assert result.success is True
    assert result.next_actions is not None
    assert "recon" in result.next_actions
