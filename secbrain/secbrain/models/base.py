"""Base model interfaces for SecBrain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    """Response from a model call."""

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if the response was successful."""
        return bool(self.content) and self.finish_reason != "error"


class ModelClient(ABC):
    """Abstract base class for model clients."""

    def __init__(self, model: str, **kwargs: Any):
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response from the model.

        Args:
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            ModelResponse with generated content
        """

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate structured output matching a schema.

        Args:
            prompt: User prompt
            schema: JSON schema for the expected output
            system: System prompt
            **kwargs: Additional parameters

        Returns:
            Parsed structured response
        """

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model


class DryRunModelClient(ModelClient):
    """Mock model client for dry-run mode."""

    def __init__(self, model: str = "dry-run", **kwargs: Any):
        super().__init__(model, **kwargs)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """Return a mock response."""
        return ModelResponse(
            content="[DRY-RUN] Mock response for prompt: " + prompt[:100] + "...",
            model=self.model,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=50,
            total_tokens=len(prompt) // 4 + 50,
            finish_reason="stop",
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return a mock structured response."""
        # Generate a minimal valid response based on schema
        result: dict[str, Any] = {}
        if "properties" in schema:
            for key, prop in schema["properties"].items():
                prop_type = prop.get("type", "string")
                if prop_type == "string":
                    result[key] = f"[DRY-RUN] {key}"
                elif prop_type == "integer":
                    result[key] = 0
                elif prop_type == "number":
                    result[key] = 0.0
                elif prop_type == "boolean":
                    result[key] = False
                elif prop_type == "array":
                    result[key] = []
                elif prop_type == "object":
                    result[key] = {}
        return result
