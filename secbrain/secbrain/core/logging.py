"""Structured logging for SecBrain runs.

This module provides structured logging capabilities with:
- Integration with structlog for structured output
- Fallback to stdlib logging when structlog unavailable
- Context-aware logging with bound parameters
- Event tracking and phase transitions
- JSON-formatted log output
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import structlog
    from structlog.typing import EventDict, WrappedLogger
except ModuleNotFoundError:  # pragma: no cover
    structlog = None  # type: ignore[assignment]
    EventDict = dict  # type: ignore[misc,assignment]
    WrappedLogger = Any  # type: ignore[misc,assignment]


class _StdlibBoundLogger:
    def __init__(self, logger: logging.Logger, bound: dict[str, Any] | None = None):
        self._logger = logger
        self._bound = bound or {}

    def bind(self, **kwargs: Any) -> _StdlibBoundLogger:
        merged = dict(self._bound)
        merged.update(kwargs)
        return _StdlibBoundLogger(self._logger, merged)

    def info(self, event: str, **kwargs: Any) -> None:
        payload = {"event": event, **self._bound, **kwargs}
        self._logger.info(json.dumps(payload, default=str))

    def error(self, event: str, **kwargs: Any) -> None:
        payload = {"event": event, **self._bound, **kwargs}
        self._logger.error(json.dumps(payload, default=str))


def add_timestamp(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp to log events."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def setup_logging(
    logs_path: Path | None = None,
    run_id: str | None = None,
    console_output: bool = True,
    log_level: str = "INFO",
    workspace_path: Path | None = None,
):
    """
    Set up structured logging for a SecBrain run.

    Logs are written as JSONL to workspace/logs/run-<timestamp>.jsonl

    Args:
        logs_path: Directory to write log files
        run_id: Unique identifier for this run
        console_output: Whether to also output to console
        log_level: Minimum log level to record
        workspace_path: Workspace directory (if provided, logs go to workspace/logs)

    Returns:
        Configured logger (structlog BoundLogger when available; stdlib fallback otherwise)
    """
    if workspace_path is not None:
        logs_path = workspace_path / "logs"

    if logs_path is None:
        raise ValueError("setup_logging requires logs_path or workspace_path")

    logs_path.mkdir(parents=True, exist_ok=True)

    if run_id is None:
        raise ValueError("setup_logging requires run_id")

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    log_file = logs_path / f"run-{timestamp}-{run_id}.jsonl"

    # Create file handler
    file_handler = log_file.open("a", encoding="utf-8")

    if structlog is None:
        level = getattr(logging, log_level.upper(), logging.INFO)
        logger = logging.getLogger("secbrain")
        logger.setLevel(level)
        logger.handlers.clear()

        formatter = logging.Formatter("%(message)s")

        file_handler_obj = logging.FileHandler(log_file, encoding="utf-8")
        file_handler_obj.setLevel(level)
        file_handler_obj.setFormatter(formatter)
        logger.addHandler(file_handler_obj)

        if console_output:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        return _StdlibBoundLogger(logger).bind(run_id=run_id)

    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        add_timestamp,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Configure output
    if console_output:
        # For console, use pretty printing
        console_processor = structlog.dev.ConsoleRenderer(colors=True)

        def dual_output(
            logger: WrappedLogger, method_name: str, event_dict: EventDict
        ) -> str:
            # Write JSON to file
            json_line = json.dumps(event_dict, default=str)
            file_handler.write(json_line + "\n")
            file_handler.flush()

            # Return formatted string for console
            return console_processor(logger, method_name, event_dict)

        processors.append(dual_output)
    else:
        # JSON only
        def json_output(
            logger: WrappedLogger, method_name: str, event_dict: EventDict
        ) -> str:
            json_line = json.dumps(event_dict, default=str)
            file_handler.write(json_line + "\n")
            file_handler.flush()
            return json_line

        processors.append(json_output)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout if console_output else None),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger()
    return logger.bind(run_id=run_id)


def log_event(
    logger: Any,
    event: str,
    agent: str | None = None,
    phase: str | None = None,
    action: str | None = None,
    model: str | None = None,
    tool: str | None = None,
    result: str | None = None,
    **kwargs: Any,
) -> None:
    context: dict[str, Any] = {}

    if agent:
        context["agent"] = agent
    if phase:
        context["phase"] = phase
    if action:
        context["action"] = action
    if model:
        context["model"] = model
    if tool:
        context["tool"] = tool
    if result:
        context["result"] = result

    context.update(kwargs)

    logger.info(event, **context)


def log_tool_call(
    logger: Any,
    tool: str,
    action: str,
    target: str | None = None,
    success: bool = True,
    duration_ms: float | None = None,
    **kwargs: Any,
) -> None:
    log_event(
        logger,
        event="tool_call",
        tool=tool,
        action=action,
        result="success" if success else "failure",
        target=target,
        duration_ms=duration_ms,
        **kwargs,
    )


def log_model_call(
    logger: Any,
    model: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    duration_ms: float | None = None,
    **kwargs: Any,
) -> None:
    log_event(
        logger,
        event="model_call",
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        duration_ms=duration_ms,
        **kwargs,
    )


def log_phase_transition(
    logger: Any,
    from_phase: str,
    to_phase: str,
    **kwargs: Any,
) -> None:
    log_event(
        logger,
        event="phase_transition",
        phase=to_phase,
        from_phase=from_phase,
        **kwargs,
    )


def log_finding(
    logger: Any,
    severity: str,
    vuln_type: str,
    target: str,
    **kwargs: Any,
) -> None:
    log_event(
        logger,
        event="finding",
        result=severity,
        vuln_type=vuln_type,
        target=target,
        **kwargs,
    )


def log_error(
    logger: Any,
    error: str,
    agent: str | None = None,
    recoverable: bool = True,
    **kwargs: Any,
) -> None:
    logger.error(
        "error",
        agent=agent,
        error=error,
        recoverable=recoverable,
        **kwargs,
    )
