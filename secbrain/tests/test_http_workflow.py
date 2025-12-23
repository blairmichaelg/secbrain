"""Tests for HTTP workflow module."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from secbrain.workflows.http_workflow import (
    HTTPWorkflowResult,
    HTTPWorkflowStep,
    MultiStepHTTPWorkflow,
)


class TestHTTPWorkflowStep:
    """Test HTTPWorkflowStep dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic HTTPWorkflowStep initialization."""
        step = HTTPWorkflowStep(method="GET", url="https://example.com")
        assert step.method == "GET"
        assert step.url == "https://example.com"
        assert step.headers is None
        assert step.params is None
        assert step.data is None
        assert step.json_data is None
        assert step.identity is None
        assert step.cookies is None
        assert step.label == ""

    def test_full_initialization(self) -> None:
        """Test HTTPWorkflowStep with all fields."""
        headers = {"Content-Type": "application/json"}
        params = {"page": 1}
        json_data = {"key": "value"}
        cookies = {"session": "abc123"}
        
        step = HTTPWorkflowStep(
            method="POST",
            url="https://api.example.com/data",
            headers=headers,
            params=params,
            data="form data",
            json_data=json_data,
            identity="user1",
            cookies=cookies,
            label="Create data",
        )
        
        assert step.method == "POST"
        assert step.url == "https://api.example.com/data"
        assert step.headers == headers
        assert step.params == params
        assert step.data == "form data"
        assert step.json_data == json_data
        assert step.identity == "user1"
        assert step.cookies == cookies
        assert step.label == "Create data"


class TestHTTPWorkflowResult:
    """Test HTTPWorkflowResult dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic HTTPWorkflowResult initialization."""
        result = HTTPWorkflowResult()
        assert result.steps == []
        assert result.responses == []
        assert result.success is True
        assert result.errors == []
        assert result.artifact_path is None

    def test_with_data(self) -> None:
        """Test HTTPWorkflowResult with data."""
        step = HTTPWorkflowStep(method="GET", url="https://test.com")
        response = Mock(status_code=200, success=True)
        
        result = HTTPWorkflowResult(
            steps=[step],
            responses=[response],
            success=True,
            errors=[],
        )
        
        assert len(result.steps) == 1
        assert len(result.responses) == 1
        assert result.success is True

    def test_with_errors(self) -> None:
        """Test HTTPWorkflowResult with errors."""
        result = HTTPWorkflowResult(
            success=False,
            errors=["Error 1", "Error 2"],
        )
        
        assert result.success is False
        assert len(result.errors) == 2

    def test_with_artifact_path(self, tmp_path: Path) -> None:
        """Test HTTPWorkflowResult with artifact path."""
        artifact_path = tmp_path / "workflow.json"
        result = HTTPWorkflowResult(artifact_path=artifact_path)
        assert result.artifact_path == artifact_path


class TestMultiStepHTTPWorkflow:
    """Test MultiStepHTTPWorkflow class."""

    def test_initialization(self) -> None:
        """Test MultiStepHTTPWorkflow initialization."""
        run_context = Mock()
        workflow = MultiStepHTTPWorkflow(run_context)
        assert workflow.run_context == run_context
        assert workflow.client is not None

    @pytest.mark.asyncio
    async def test_run_single_successful_step(self, tmp_path: Path) -> None:
        """Test running a single successful HTTP step."""
        # Setup mocks
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.success = True
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "Response body"
        mock_response.body = b"Response body"
        mock_response.error = None
        mock_response.metadata = {}
        
        workflow.client.request = AsyncMock(return_value=mock_response)
        
        # Create and run step
        step = HTTPWorkflowStep(method="GET", url="https://example.com", label="Test")
        result = await workflow.run([step])
        
        # Verify result
        assert result.success is True
        assert len(result.responses) == 1
        assert len(result.errors) == 0
        assert result.artifact_path is not None
        assert result.artifact_path.exists()
        
        # Verify artifact content
        artifact_content = json.loads(result.artifact_path.read_text())
        assert len(artifact_content) == 1
        assert artifact_content[0]["step"]["method"] == "GET"
        assert artifact_content[0]["step"]["url"] == "https://example.com"
        assert artifact_content[0]["response"]["status"] == 200

    @pytest.mark.asyncio
    async def test_run_multiple_successful_steps(self, tmp_path: Path) -> None:
        """Test running multiple successful HTTP steps."""
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        # Mock successful responses
        mock_response1 = Mock()
        mock_response1.success = True
        mock_response1.status_code = 200
        mock_response1.headers = {}
        mock_response1.text = "Step 1"
        mock_response1.body = b"Step 1"
        mock_response1.error = None
        mock_response1.metadata = {}
        
        mock_response2 = Mock()
        mock_response2.success = True
        mock_response2.status_code = 201
        mock_response2.headers = {}
        mock_response2.text = "Step 2"
        mock_response2.body = b"Step 2"
        mock_response2.error = None
        mock_response2.metadata = {}
        
        workflow.client.request = AsyncMock(side_effect=[mock_response1, mock_response2])
        
        # Create and run steps
        step1 = HTTPWorkflowStep(method="GET", url="https://example.com/1")
        step2 = HTTPWorkflowStep(method="POST", url="https://example.com/2")
        result = await workflow.run([step1, step2])
        
        # Verify result
        assert result.success is True
        assert len(result.responses) == 2
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_run_with_failed_step(self, tmp_path: Path) -> None:
        """Test running workflow with a failed step."""
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        # Mock failed response
        mock_response = Mock()
        mock_response.success = False
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.text = "Not found"
        mock_response.body = b"Not found"
        mock_response.error = "Page not found"
        mock_response.metadata = {}
        
        workflow.client.request = AsyncMock(return_value=mock_response)
        
        # Create and run step
        step = HTTPWorkflowStep(method="GET", url="https://example.com/missing")
        result = await workflow.run([step])
        
        # Verify result
        assert result.success is False
        assert len(result.errors) == 1
        assert "Page not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_run_continues_after_failure(self, tmp_path: Path) -> None:
        """Test that workflow continues after a failed step."""
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        # Mock first failed, second successful
        mock_response1 = Mock()
        mock_response1.success = False
        mock_response1.status_code = 500
        mock_response1.headers = {}
        mock_response1.text = "Error"
        mock_response1.body = b"Error"
        mock_response1.error = "Server error"
        mock_response1.metadata = {}
        
        mock_response2 = Mock()
        mock_response2.success = True
        mock_response2.status_code = 200
        mock_response2.headers = {}
        mock_response2.text = "OK"
        mock_response2.body = b"OK"
        mock_response2.error = None
        mock_response2.metadata = {}
        
        workflow.client.request = AsyncMock(side_effect=[mock_response1, mock_response2])
        
        # Create and run steps
        step1 = HTTPWorkflowStep(method="POST", url="https://example.com/error")
        step2 = HTTPWorkflowStep(method="GET", url="https://example.com/ok")
        result = await workflow.run([step1, step2])
        
        # Verify result
        assert result.success is False  # Overall failure due to one failed step
        assert len(result.responses) == 2  # But both steps were executed
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_run_with_custom_artifact_name(self, tmp_path: Path) -> None:
        """Test running workflow with custom artifact name."""
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "OK"
        mock_response.body = b"OK"
        mock_response.error = None
        mock_response.metadata = {}
        
        workflow.client.request = AsyncMock(return_value=mock_response)
        
        # Run with custom artifact name
        step = HTTPWorkflowStep(method="GET", url="https://example.com")
        result = await workflow.run([step], artifact_name="custom_workflow.json")
        
        # Verify custom artifact name
        assert result.artifact_path is not None
        assert result.artifact_path.name == "custom_workflow.json"
        assert result.artifact_path.exists()

    @pytest.mark.asyncio
    async def test_run_with_all_step_params(self, tmp_path: Path) -> None:
        """Test running workflow with all step parameters."""
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "OK"
        mock_response.body = b"OK"
        mock_response.error = None
        mock_response.metadata = {}
        
        workflow.client.request = AsyncMock(return_value=mock_response)
        
        # Create step with all parameters
        step = HTTPWorkflowStep(
            method="POST",
            url="https://api.example.com/endpoint",
            headers={"Authorization": "Bearer token"},
            params={"filter": "active"},
            data="raw data",
            json_data={"key": "value"},
            identity="user123",
            cookies={"session": "abc"},
            label="API Call",
        )
        
        await workflow.run([step])
        
        # Verify client was called with correct parameters
        workflow.client.request.assert_called_once()
        call_kwargs = workflow.client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["url"] == "https://api.example.com/endpoint"
        assert call_kwargs["headers"] == {"Authorization": "Bearer token"}
        assert call_kwargs["params"] == {"filter": "active"}
        assert call_kwargs["identity_name"] == "user123"
        assert call_kwargs["cookies"] == {"session": "abc"}

    @pytest.mark.asyncio
    async def test_artifact_body_truncation(self, tmp_path: Path) -> None:
        """Test that response body is truncated in artifact."""
        run_context = Mock()
        run_context.logs_path = tmp_path
        
        workflow = MultiStepHTTPWorkflow(run_context)
        
        # Create response with long body
        long_body = "x" * 2000
        mock_response = Mock()
        mock_response.success = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = long_body
        mock_response.body = long_body.encode()
        mock_response.error = None
        mock_response.metadata = {}
        
        workflow.client.request = AsyncMock(return_value=mock_response)
        
        step = HTTPWorkflowStep(method="GET", url="https://example.com")
        result = await workflow.run([step])
        
        # Verify body is truncated to 1024 chars
        artifact_content = json.loads(result.artifact_path.read_text())
        assert len(artifact_content[0]["response"]["body_snippet"]) == 1024
