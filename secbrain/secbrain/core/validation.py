from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from pathlib import Path

import yaml
from pydantic import ValidationError as PydanticValidationError

from secbrain.core.context import ProgramConfig, ScopeConfig


class ValidationError(Exception):
    """Raised when configuration validation fails."""


def _load_yaml_or_json(path: Path) -> dict:
    if not path.exists():
        raise ValidationError(f"File not found: {path}")
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_scope_file(path: Path) -> ScopeConfig:
    """Validate a scope.yaml file and return the parsed config."""
    data = _load_yaml_or_json(path)
    try:
        config = ScopeConfig(**data)
    except PydanticValidationError as e:
        raise ValidationError(f"Scope schema error: {e}") from e

    if not (config.domains or config.urls or config.ips or config.contracts):
        raise ValidationError("Scope must include at least one of domains, urls, ips, or contracts.")

    if not config.allowed_methods:
        raise ValidationError("Scope allowed_methods must not be empty.")

    return config


def validate_program_file(path: Path) -> ProgramConfig:
    """Validate a program.json file and return the parsed config."""
    data = _load_yaml_or_json(path)
    try:
        config = ProgramConfig(**data)
    except PydanticValidationError as e:
        raise ValidationError(f"Program schema error: {e}") from e

    if not config.name:
        raise ValidationError("Program name is required.")
    return config


def validate_environment(required_env: Iterable[str]) -> list[str]:
    """Validate required environment variables are present."""
    import os

    missing = [key for key in required_env if not os.environ.get(key)]
    if missing:
        raise ValidationError(f"Missing required environment variables: {', '.join(missing)}")
    return list(required_env)


def validate_tools_on_path(tools: Iterable[str]) -> list[str]:
    """Ensure required CLI tools are available on PATH."""
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        raise ValidationError(f"Missing required tools on PATH: {', '.join(missing)}")
    return list(tools)
