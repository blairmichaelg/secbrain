"""Open/cheap worker model implementations for SecBrain."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from secbrain.models.base import ModelClient, ModelResponse


class OpenWorkerClient(ModelClient):
    """
    Client for open/cheap worker models via OpenAI-compatible APIs.

    Supports:
    - Together AI (Qwen, DeepSeek, etc.)
    - OpenRouter
    - Local models via Ollama/vLLM
    - Any OpenAI-compatible endpoint
    """

    def __init__(
        self,
        model: str = "qwen/qwen-2.5-72b-instruct",
        base_url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)

        # Determine provider and set defaults
        self.base_url = base_url or os.environ.get(
            "OPENAI_BASE_URL", "https://api.groq.com/openai/v1"
        )
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get(
            "OPENAI_API_KEY", ""
        )

        if not self.api_key:
            raise ValueError("OpenWorkerClient missing API key. Set GROQ_API_KEY.")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a response using OpenAI-compatible API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        try:
            # Use relative path to preserve any base_url path (e.g., /v1)
            response = await self.client.post("chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data.get("choices", [{}])[0]
            usage = data.get("usage", {})

            return ModelResponse(
                content=choice.get("message", {}).get("content", ""),
                model=data.get("model", self.model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", ""),
                raw_response=data,
            )
        except httpx.HTTPError as e:
            return ModelResponse(
                content="",
                model=self.model,
                finish_reason="error",
                raw_response={"error": str(e)},
            )

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate structured output using JSON mode."""
        # Add JSON instruction to prompt
        json_prompt = f"""{prompt}

Respond with a JSON object matching this schema:
{json.dumps(schema, indent=2)}

Output ONLY valid JSON, no other text."""

        enhanced_system = system or ""
        if enhanced_system:
            enhanced_system += "\n\n"
        enhanced_system += "You must respond with valid JSON only. No explanations or markdown."

        response = await self.generate(
            prompt=json_prompt,
            system=enhanced_system,
            **kwargs,
        )

        if not response.success:
            return {}

        # Parse JSON from response
        try:
            # Handle potential markdown code blocks
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


class OllamaClient(ModelClient):
    """Client for local Ollama models."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=300.0)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate using Ollama API."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

            return ModelResponse(
                content=data.get("response", ""),
                model=data.get("model", self.model),
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                finish_reason="stop" if data.get("done") else "length",
                raw_response=data,
            )
        except httpx.HTTPError as e:
            return ModelResponse(
                content="",
                model=self.model,
                finish_reason="error",
                raw_response={"error": str(e)},
            )

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate structured output."""
        json_prompt = f"""{prompt}

Respond with a JSON object matching this schema:
{json.dumps(schema, indent=2)}

Output ONLY valid JSON."""

        response = await self.generate(prompt=json_prompt, system=system, **kwargs)

        if not response.success:
            return {}

        try:
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
