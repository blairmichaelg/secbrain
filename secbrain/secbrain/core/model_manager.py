"""Centralized model and API management for SecBrain."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from openai import AsyncOpenAI

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # Dotenv is optional; ignore if missing
    pass

logger = logging.getLogger(__name__)


class ModelManager:
    """Centralized model and API management."""

    def __init__(self) -> None:
        self.config = self._load_config()
        self._validate_keys()
        self.groq_client = self._init_groq()
        rpc_cfg = self.config.get("rpc", {}) if isinstance(self.config, dict) else {}
        self.rpc_url = rpc_cfg.get("primary_url") or os.getenv("RPC_URL")
        self.rpc_fallback = rpc_cfg.get("fallback_url") or os.getenv("RPC_FALLBACK")

    def _config_path(self) -> Path:
        # Prefer repo config/models.yaml relative to this file
        return Path(__file__).parent.parent / "config" / "models.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """Load models.yaml with env var interpolation."""
        cfg_path = self._config_path()
        if not cfg_path.exists():
            return {}
        with open(cfg_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Normalize deprecated models to current supported defaults
        worker_model = (config.get("worker") or {}).get("model", "")
        advisor_model = (config.get("advisor") or {}).get("model", "")
        deprecated = "mixtral-8x7b-32768"
        fallback_model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
        if worker_model == deprecated:
            config.setdefault("worker", {})["model"] = fallback_model
        if advisor_model == deprecated:
            config.setdefault("advisor", {})["model"] = fallback_model

        # Interpolate RPC URL
        rpc_cfg = config.get("rpc", {}) or {}
        if "primary_url" in rpc_cfg:
            rpc_cfg["primary_url"] = os.getenv("RPC_URL", rpc_cfg.get("primary_url"))
        if "fallback_url" in rpc_cfg:
            rpc_cfg["fallback_url"] = os.getenv(
                "RPC_FALLBACK", rpc_cfg.get("fallback_url")
            )
        config["rpc"] = rpc_cfg
        return config

    def _validate_keys(self) -> None:
        """Validate all required API keys are present."""
        required = {
            "GROQ_API_KEY": "Worker and advisor models",
            "RPC_URL": "Smart contract analysis",
            "PERPLEXITY_API_KEY": "Research queries",
        }
        missing: list[str] = []
        for key, desc in required.items():
            if not os.getenv(key):
                missing.append(f"{key} ({desc})")
        if missing:
            raise ValueError("Missing API keys:\n" + "\n".join(f"  - {m}" for m in missing))
        logger.info("All required API keys validated")

    def _init_groq(self) -> AsyncOpenAI:
        """Initialize GROQ async client."""
        return AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=self.config.get("worker", {}).get(
                "base_url", "https://api.groq.com/openai/v1"
            ),
            timeout=30.0,
        )

    async def call_worker(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Call worker model with error handling."""
        model = self.config.get("worker", {}).get("model", "llama-3.3-70b-versatile")
        try:
            response = await self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.config.get("worker", {}).get("temperature", 0.3),
                max_tokens=self.config.get("worker", {}).get("max_tokens", 2000),
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Worker model error: %s", e)
            raise

    async def call_advisor(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Call advisor model with error handling."""
        model = self.config.get("advisor", {}).get("model", "llama-3.1-70b-versatile")
        try:
            response = await self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.config.get("advisor", {}).get("temperature", 0.7),
                max_tokens=self.config.get("advisor", {}).get("max_tokens", 1500),
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Advisor model error: %s", e)
            raise

    @property
    def primary_rpc(self) -> Optional[str]:
        """Get primary RPC URL."""
        return self.rpc_url

    @property
    def fallback_rpc(self) -> Optional[str]:
        """Get fallback RPC URL."""
        return self.rpc_fallback


_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get or create global model manager."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def reset_model_manager() -> None:
    """Reset the global model manager (force reload of config/models.yaml)."""
    global _model_manager
    _model_manager = None
