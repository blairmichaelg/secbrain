"""Gemini advisor model implementation for SecBrain."""

from __future__ import annotations

import json
import os
from typing import Any

from secbrain.models.base import ModelClient, ModelResponse


class GeminiAdvisorClient(ModelClient):
    """
    Client for Google Gemini as the advisor model.

    Used for:
    - Critical decision checkpoints
    - Plan review and approval
    - High-stakes vulnerability validation
    - Report quality assessment
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",  # Changed to Flash for faster responses
        api_key: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self._client = None

    def _get_client(self) -> Any:
        """Lazily initialize the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)  # type: ignore[attr-defined]
                self._client = genai.GenerativeModel(self.model)  # type: ignore[attr-defined, assignment]
            except ImportError:
                raise ImportError(
                    "google-generativeai is required for Gemini. "
                    "Install it with: pip install google-generativeai"
                )
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a response using Gemini."""
        try:
            client = self._get_client()

            # Combine system and user prompts for Gemini
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n---\n\n{prompt}"

            # Gemini uses sync API, wrap for async compatibility
            import asyncio

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                ),
            )

            # Extract content and usage
            content = ""
            if response.candidates:
                content = response.candidates[0].content.parts[0].text

            # Gemini doesn't always provide token counts
            prompt_tokens = getattr(response, "prompt_token_count", 0) or 0
            completion_tokens = getattr(response, "candidates_token_count", 0) or 0

            return ModelResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason="stop",
                raw_response={"text": content},
            )
        except Exception as e:
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
        """Generate structured output using Gemini."""
        json_prompt = f"""{prompt}

You must respond with a JSON object matching this exact schema:
{json.dumps(schema, indent=2)}

Rules:
1. Output ONLY valid JSON
2. No markdown code blocks
3. No explanations before or after
4. Ensure all required fields are present"""

        response = await self.generate(
            prompt=json_prompt,
            system=system,
            **kwargs,
        )

        if not response.success:
            return {}

        try:
            content = response.content.strip()
            # Handle potential markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first and last lines (```json and ```)
                content = "\n".join(lines[1:-1])
            result: dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {}

    async def review_plan(
        self,
        plan: dict[str, Any],
        context: str,
    ) -> dict[str, Any]:
        """
        Review an agent's plan for safety and effectiveness.

        Returns:
            {
                "approved": bool,
                "concerns": list[str],
                "suggestions": list[str],
                "risk_level": "low" | "medium" | "high"
            }
        """
        prompt = f"""Review this security testing plan for a bug bounty program.

Context:
{context}

Plan:
{json.dumps(plan, indent=2)}

Evaluate:
1. Is this plan within ethical and legal bounds?
2. Could any actions cause harm or service disruption?
3. Are there scope violations or risky edge cases?
4. Is the approach likely to be effective?

Provide your assessment."""

        schema = {
            "type": "object",
            "properties": {
                "approved": {"type": "boolean"},
                "concerns": {"type": "array", "items": {"type": "string"}},
                "suggestions": {"type": "array", "items": {"type": "string"}},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["approved", "concerns", "suggestions", "risk_level"],
        }

        return await self.generate_structured(prompt=prompt, schema=schema)

    async def validate_finding(
        self,
        finding: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Validate a vulnerability finding.

        Returns:
            {
                "valid": bool,
                "confidence": float (0-1),
                "severity_assessment": str,
                "missing_evidence": list[str],
                "recommendations": list[str]
            }
        """
        prompt = f"""Validate this security finding for a bug bounty submission.

Finding:
{json.dumps(finding, indent=2)}

Evidence:
{json.dumps(evidence, indent=2)}

Assess:
1. Is the vulnerability real and exploitable?
2. Is the evidence sufficient to prove the issue?
3. Is the severity assessment accurate?
4. What additional evidence would strengthen the report?"""

        schema = {
            "type": "object",
            "properties": {
                "valid": {"type": "boolean"},
                "confidence": {"type": "number"},
                "severity_assessment": {"type": "string"},
                "missing_evidence": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["valid", "confidence", "severity_assessment"],
        }

        return await self.generate_structured(prompt=prompt, schema=schema)
