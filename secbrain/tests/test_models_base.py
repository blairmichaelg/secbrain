"""Tests for base model interfaces."""

import pytest

from secbrain.models.base import DryRunModelClient, ModelClient, ModelResponse


class TestModelResponse:
    """Test ModelResponse dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic ModelResponse initialization."""
        response = ModelResponse(
            content="Test response",
            model="gpt-4",
        )
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0
        assert response.finish_reason == ""
        assert response.raw_response == {}

    def test_full_initialization(self) -> None:
        """Test ModelResponse with all fields."""
        raw = {"usage": {"total_tokens": 100}}
        response = ModelResponse(
            content="Generated text",
            model="gpt-3.5-turbo",
            prompt_tokens=50,
            completion_tokens=40,
            total_tokens=90,
            finish_reason="stop",
            raw_response=raw,
        )
        assert response.content == "Generated text"
        assert response.model == "gpt-3.5-turbo"
        assert response.prompt_tokens == 50
        assert response.completion_tokens == 40
        assert response.total_tokens == 90
        assert response.finish_reason == "stop"
        assert response.raw_response == raw

    def test_success_property_true(self) -> None:
        """Test success property returns True for successful response."""
        response = ModelResponse(
            content="Success",
            model="test",
            finish_reason="stop",
        )
        assert response.success is True

    def test_success_property_false_empty_content(self) -> None:
        """Test success property returns False for empty content."""
        response = ModelResponse(
            content="",
            model="test",
            finish_reason="stop",
        )
        assert response.success is False

    def test_success_property_false_error_finish(self) -> None:
        """Test success property returns False for error finish reason."""
        response = ModelResponse(
            content="Some content",
            model="test",
            finish_reason="error",
        )
        assert response.success is False

    def test_success_property_false_both(self) -> None:
        """Test success property returns False for empty content and error."""
        response = ModelResponse(
            content="",
            model="test",
            finish_reason="error",
        )
        assert response.success is False

    def test_success_property_true_with_content(self) -> None:
        """Test success property returns True with content and no error."""
        response = ModelResponse(
            content="Valid response",
            model="test",
            finish_reason="length",
        )
        assert response.success is True


class TestModelClient:
    """Test ModelClient abstract base class."""

    def test_initialization(self) -> None:
        """Test ModelClient initialization."""
        # Create a concrete implementation for testing
        class ConcreteModelClient(ModelClient):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4096, **kwargs):
                return ModelResponse(content="test", model=self.model)

            async def generate_structured(self, prompt, schema, system=None, **kwargs):
                return {}

        client = ConcreteModelClient(model="test-model", api_key="test-key", timeout=30)
        assert client.model == "test-model"
        assert client.config == {"api_key": "test-key", "timeout": 30}

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that ModelClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ModelClient(model="test")  # type: ignore

    def test_subclass_must_implement_generate(self) -> None:
        """Test that subclass must implement generate method."""
        class IncompleteClient(ModelClient):
            async def generate_structured(self, prompt, schema, system=None, **kwargs):
                return {}

        with pytest.raises(TypeError):
            IncompleteClient(model="test")  # type: ignore

    def test_subclass_must_implement_generate_structured(self) -> None:
        """Test that subclass must implement generate_structured method."""
        class IncompleteClient(ModelClient):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4096, **kwargs):
                return ModelResponse(content="test", model=self.model)

        with pytest.raises(TypeError):
            IncompleteClient(model="test")  # type: ignore

    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self) -> None:
        """Test that a proper concrete implementation works."""
        class WorkingClient(ModelClient):
            async def generate(self, prompt, system=None, temperature=0.7, max_tokens=4096, **kwargs):
                return ModelResponse(
                    content=f"Response to: {prompt}",
                    model=self.model,
                    prompt_tokens=10,
                    completion_tokens=20,
                    total_tokens=30,
                    finish_reason="stop",
                )

            async def generate_structured(self, prompt, schema, system=None, **kwargs):
                return {"result": "structured output"}

        client = WorkingClient(model="test-model")

        # Test generate
        response = await client.generate("Test prompt")
        assert response.content == "Response to: Test prompt"
        assert response.model == "test-model"
        assert response.total_tokens == 30

        # Test generate_structured
        result = await client.generate_structured("Test", {"type": "object"})
        assert result == {"result": "structured output"}


class TestDryRunModelClient:
    """Test DryRunModelClient for dry-run mode."""

    def test_initialization_default(self):
        """Test DryRunModelClient initialization with defaults."""
        client = DryRunModelClient()
        assert client.model == "dry-run"
        assert client.config == {}

    def test_initialization_custom_model(self):
        """Test DryRunModelClient initialization with custom model name."""
        client = DryRunModelClient(model="dry-run-test", api_key="fake")
        assert client.model == "dry-run-test"
        assert client.config == {"api_key": "fake"}

    def test_get_model_name(self):
        """Test getting model name."""
        client = DryRunModelClient(model="test-dry-run")
        assert client.get_model_name() == "test-dry-run"

    @pytest.mark.asyncio
    async def test_generate_basic(self):
        """Test generate method returns mock response."""
        client = DryRunModelClient()
        response = await client.generate("Test prompt")

        assert isinstance(response, ModelResponse)
        assert response.model == "dry-run"
        assert "[DRY-RUN]" in response.content
        assert "Test prompt" in response.content
        assert response.finish_reason == "stop"
        assert response.prompt_tokens > 0
        assert response.completion_tokens == 50
        assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generate with system prompt."""
        client = DryRunModelClient()
        response = await client.generate(
            "User prompt",
            system="System instructions",
            temperature=0.9,
            max_tokens=1000,
        )

        assert isinstance(response, ModelResponse)
        assert "[DRY-RUN]" in response.content
        assert "User prompt" in response.content

    @pytest.mark.asyncio
    async def test_generate_long_prompt(self):
        """Test generate with long prompt (truncated in response)."""
        client = DryRunModelClient()
        long_prompt = "A" * 200
        response = await client.generate(long_prompt)

        assert "[DRY-RUN]" in response.content
        # Content should include truncated prompt
        assert len(response.content) < len(long_prompt) + 50

    @pytest.mark.asyncio
    async def test_generate_structured_string_properties(self):
        """Test generate_structured with string properties."""
        client = DryRunModelClient()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
        }

        result = await client.generate_structured("Test prompt", schema)

        assert isinstance(result, dict)
        assert "name" in result
        assert "description" in result
        assert result["name"] == "[DRY-RUN] name"
        assert result["description"] == "[DRY-RUN] description"

    @pytest.mark.asyncio
    async def test_generate_structured_various_types(self):
        """Test generate_structured with various property types."""
        client = DryRunModelClient()
        schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "count": {"type": "integer"},
                "score": {"type": "number"},
                "active": {"type": "boolean"},
                "items": {"type": "array"},
                "metadata": {"type": "object"},
            },
        }

        result = await client.generate_structured("Test", schema)

        assert result["text"] == "[DRY-RUN] text"
        assert result["count"] == 0
        assert result["score"] == 0.0
        assert result["active"] is False
        assert result["items"] == []
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_generate_structured_no_properties(self):
        """Test generate_structured with schema without properties."""
        client = DryRunModelClient()
        schema = {"type": "object"}

        result = await client.generate_structured("Test", schema)

        assert isinstance(result, dict)
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_structured_with_system(self):
        """Test generate_structured with system prompt."""
        client = DryRunModelClient()
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
            },
        }

        result = await client.generate_structured(
            "Test", schema, system="System instructions"
        )

        assert "status" in result
        assert result["status"] == "[DRY-RUN] status"
