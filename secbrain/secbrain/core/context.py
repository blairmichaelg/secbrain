"""Run context and session management for SecBrain."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import TypedDict

from secbrain.core.approval import ApprovalManager

from .identity import IdentityRegistry

if TYPE_CHECKING:
    from secbrain.models.base import ModelClient


def _default_research_config() -> dict[str, Any]:
    """Default research configuration factory."""
    return {
        "max_concurrent": 3,
        "cache_results": True,
        "priority_threshold": 5,
        "max_queries_per_phase": {
            "hypothesis": 10,
            "exploit": 5,
            "triage": 3,
        },
    }


class SessionErrorDict(TypedDict, total=False):
    """Structure for session error records."""

    phase: str
    error: str
    timestamp: str
    agent: str


class SessionFindingDict(TypedDict, total=False):
    """Structure for session finding records."""

    id: str
    title: str
    severity: str
    phase: str
    discovered_by: str


class ContractConfig(BaseModel):
    """Configuration for a smart contract target.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True)

    address: str = Field(description="Contract address")
    chain_id: int = Field(default=1, description="Chain ID (1=Mainnet, etc.)")
    name: str | None = Field(None, description="Contract name")
    foundry_profile: str | None = Field(None, description="Foundry profile name for compilation")
    source_path: Path | None = Field(None, description="Path to contract source files")
    verified: bool = Field(default=True, description="Whether contract is verified on-chain")

    @field_validator("source_path", mode="before")
    @classmethod
    def _coerce_source_path(cls, value: Any) -> Path | None:
        """Allow string paths in strict mode configs."""
        if value is None or isinstance(value, Path):
            return value
        if isinstance(value, str):
            return Path(value)
        raise TypeError("source_path must be a string or pathlib.Path")


class ScopeConfig(BaseModel):
    """Target scope configuration.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True)

    domains: list[str] = Field(default_factory=list)
    ips: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    contracts: list[ContractConfig] = Field(default_factory=list, description="Smart contracts in scope")
    excluded_paths: list[str] = Field(default_factory=list)
    allowed_methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "HEAD", "OPTIONS"])
    max_depth: int = 3
    notes: str = ""
    foundry_root: Path | None = Field(None, description="Root directory for Foundry project")
    max_requests_per_second: int = Field(default=10, description="Rate limit for web requests")
    respect_robots_txt: bool = Field(default=True, description="Whether to respect robots.txt")
    rpc_urls: list[str] = Field(default_factory=list, description="Fallback RPC URLs to try for forked testing")
    profit_tokens: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "ERC20 tokens to track for profit measurement. "
            "Each item supports: {symbol,address,decimals,eth_equiv_multiplier,eth_equiv_source}."
        ),
    )
    max_parallel_exploits: int = Field(
        default=2,
        description="Maximum concurrent Foundry exploit attempts to run",
    )
    research_config: dict[str, Any] = Field(
        default_factory=_default_research_config,
        description="Research orchestrator configuration",
    )

    @field_validator("foundry_root", mode="before")
    @classmethod
    def _coerce_foundry_root(cls, value: Any) -> Path | None:
        """Allow string paths while keeping strict validation."""
        if value is None or isinstance(value, Path):
            return value
        if isinstance(value, str):
            return Path(value)
        raise TypeError("foundry_root must be a string or pathlib.Path")


class ProgramConfig(BaseModel):
    """Bug bounty program configuration.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True)

    name: str
    platform: str = ""
    bounty_range: str = ""
    url: str = ""
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    rewards: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    contacts: dict[str, Any] = Field(default_factory=dict)


class ToolACL(BaseModel):
    """Access control for a tool.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True)

    allowed: bool = True
    allowed_phases: list[str] = Field(default_factory=list)
    require_approval: bool = False
    max_calls_per_phase: int = 100
    max_calls_per_run: int = 1000


class RateLimitConfig(BaseModel):
    """Rate limiting configuration.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True)

    requests_per_minute: int = 60
    burst: int = 10
    backoff_factor: float = 2.0
    max_backoff: float = 60.0


class ToolsConfig(BaseModel):
    """Tools configuration with ACLs and rate limits.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True)

    acls: dict[str, ToolACL] = Field(default_factory=dict)
    rate_limits: dict[str, RateLimitConfig] = Field(default_factory=dict)
    global_rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter that is event-loop aware."""

    tokens: float
    max_tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = 0.0

    def _loop_time(self) -> float:
        """Return the appropriate monotonic clock for the active loop."""
        try:
            return asyncio.get_running_loop().time()
        except RuntimeError:
            return time.monotonic()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = self._loop_time()
        if self.last_refill == 0.0:
            self.last_refill = now
            return
        elapsed = max(0.0, now - self.last_refill)
        if elapsed <= 0.0:
            return
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Acquire tokens, waiting if necessary."""
        if tokens <= 0:
            return
        while True:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            if self.refill_rate <= 0:
                raise RuntimeError("RateLimiter refill_rate must be positive")
            wait_time = (tokens - self.tokens) / self.refill_rate
            await asyncio.sleep(min(max(wait_time, 0.0), 1.0))


class Session(BaseModel):
    """Session state for a run.

    Uses Pydantic V2 strict mode for enhanced type safety.
    """

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    current_phase: str = "init"
    phases_completed: list[str] = Field(default_factory=list)
    tool_call_counts: dict[str, int] = Field(default_factory=dict)
    research_cache: dict[str, Any] = Field(default_factory=dict)
    llm_cache: dict[str, Any] = Field(default_factory=dict)
    findings: list[SessionFindingDict] = Field(default_factory=list)
    errors: list[SessionErrorDict] = Field(default_factory=list)


class RunContext:
    """
    Central context for a SecBrain run.

    Holds:
    - Program scope info
    - Workspace paths
    - Model clients (worker + advisor)
    - Tool registry / ACLs / rate limits
    - Kill-switch flag and helpers
    """

    def __init__(
        self,
        workspace_path: Path,
        dry_run: bool = False,
        phases: list[str] | None = None,
        kill_switch_file: Path | None = None,
        scope_path: Path | None = None,
        program_path: Path | None = None,
        scope: ScopeConfig | None = None,
        program: ProgramConfig | None = None,
        auto_approve: bool = False,
        local_only_dry_run: bool = True,
        approval_mode: str = "deny",
        approval_audit_log: Path | None = None,
    ):
        self.workspace_path = workspace_path
        self.dry_run = dry_run
        self.phases = phases
        self.kill_switch_file = kill_switch_file
        self._killed = False
        self.auto_approve = auto_approve
        self.local_only_dry_run = local_only_dry_run
        self.approval_mode = approval_mode
        self.identities = IdentityRegistry()

        audit_path = approval_audit_log or (self.workspace_path / "audit.jsonl")
        self.approval_manager = ApprovalManager(mode=approval_mode, audit_log_path=audit_path)

        # Load configurations
        if scope is not None:
            self.scope = scope
        else:
            if scope_path is None:
                raise TypeError("RunContext requires either scope or scope_path")
            self.scope = self._load_scope(scope_path)

        if program is not None:
            self.program = program
        else:
            if program_path is None:
                raise TypeError("RunContext requires either program or program_path")
            self.program = self._load_program(program_path)
        self.tools_config = self._load_tools_config()

        # Initialize session
        self.session = Session()

        # Rate limiters (initialized lazily)
        self._rate_limiters: dict[str, RateLimiter] = {}

        # Model clients (set by orchestrator)
        self._worker_model: ModelClient | None = None
        self._advisor_model: ModelClient | None = None

        # Ensure workspace directories exist
        self._setup_workspace()

    def _load_scope(self, path: Path) -> ScopeConfig:
        """Load scope configuration from YAML."""
        if not path.exists():
            return ScopeConfig(foundry_root=None)
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return ScopeConfig(**data)

    def _load_program(self, path: Path) -> ProgramConfig:
        """Load program configuration from JSON/YAML."""
        if not path.exists():
            return ProgramConfig(name="unknown")
        with open(path) as f:
            if path.suffix == ".json":
                import json
                data = json.load(f)
            else:
                data = yaml.safe_load(f) or {}
        return ProgramConfig(**data)

    def _load_tools_config(self) -> ToolsConfig:
        """Load tools configuration from config directory."""
        config_path = Path(__file__).parent.parent / "config" / "tools.yaml"
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            # Normalize numeric fields that may come through YAML as floats
            rate_limits = data.get("rate_limits") or {}
            if isinstance(rate_limits, dict):
                for _tool_name, cfg in rate_limits.items():
                    if not isinstance(cfg, dict):
                        continue
                    rpm = cfg.get("requests_per_minute")
                    if isinstance(rpm, float):
                        cfg["requests_per_minute"] = int(round(rpm))
                    burst = cfg.get("burst")
                    if isinstance(burst, float):
                        cfg["burst"] = int(round(burst))

            global_rl = data.get("global_rate_limit")
            if isinstance(global_rl, dict):
                rpm = global_rl.get("requests_per_minute")
                if isinstance(rpm, float):
                    global_rl["requests_per_minute"] = int(round(rpm))
                burst = global_rl.get("burst")
                if isinstance(burst, float):
                    global_rl["burst"] = int(round(burst))
            return ToolsConfig(**data)
        return ToolsConfig()

    def _setup_workspace(self) -> None:
        """Create workspace directory structure."""
        dirs = ["logs", "recon", "hypotheses", "findings", "reports"]
        for d in dirs:
            (self.workspace_path / d).mkdir(parents=True, exist_ok=True)

    @property
    def logs_path(self) -> Path:
        """Path to logs directory."""
        return self.workspace_path / "logs"

    @property
    def run_id(self) -> str:
        """Current run ID."""
        return self.session.run_id

    @property
    def requested_phases(self) -> list[str] | None:
        """Return the phases requested for this run (or None for all phases)."""
        return self.phases

    @property
    def worker_model(self) -> ModelClient | None:
        """Worker model client."""
        return self._worker_model

    @worker_model.setter
    def worker_model(self, client: ModelClient) -> None:
        self._worker_model = client

    @property
    def advisor_model(self) -> ModelClient | None:
        """Advisor model client."""
        return self._advisor_model

    @advisor_model.setter
    def advisor_model(self, client: ModelClient) -> None:
        self._advisor_model = client

    def is_killed(self) -> bool:
        """Check if kill-switch has been activated."""
        if self._killed:
            return True
        if self.kill_switch_file and self.kill_switch_file.exists():
            self._killed = True
            return True
        return False

    def kill(self) -> None:
        """Activate the kill-switch."""
        self._killed = True

    def check_scope(self, url: str) -> bool:
        """Check if a URL is within scope."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ""

        # Check if host matches any allowed domain
        for domain in self.scope.domains:
            if domain.startswith("*."):
                if host.endswith(domain[1:]) or host == domain[2:]:
                    return True
            elif host == domain:
                return True

        # Check if host matches any allowed URL pattern
        for allowed_url in self.scope.urls:
            if url.startswith(allowed_url):
                return True

        # Check excluded paths
        for excluded in self.scope.excluded_paths:
            if excluded in url:
                return False

        return len(self.scope.domains) == 0 and len(self.scope.urls) == 0

    def check_tool_acl(self, tool_name: str, phase: str | None = None) -> bool:
        """Check if a tool is allowed in the current context."""
        acl = self.tools_config.acls.get(tool_name, ToolACL())

        if not acl.allowed:
            return False

        if phase is None:
            phase = self.session.current_phase

        if acl.allowed_phases and phase not in acl.allowed_phases:
            return False

        # Check call counts
        current_calls = self.session.tool_call_counts.get(tool_name, 0)
        if current_calls >= acl.max_calls_per_run:
            return False

        return True

    def requires_approval(self, tool_name: str) -> bool:
        """Check if a tool requires human approval."""
        acl = self.tools_config.acls.get(tool_name, ToolACL())
        return acl.require_approval

    async def acquire_rate_limit(self, resource: str = "global") -> None:
        """Acquire a rate limit token for a resource."""
        if resource not in self._rate_limiters:
            config = self.tools_config.rate_limits.get(
                resource, self.tools_config.global_rate_limit
            )
            self._rate_limiters[resource] = RateLimiter(
                tokens=float(config.burst),
                max_tokens=float(config.burst),
                refill_rate=config.requests_per_minute / 60.0,
            )
        await self._rate_limiters[resource].acquire()

    def record_tool_call(self, tool_name: str) -> None:
        """Record a tool call for rate limiting and ACL tracking."""
        self.session.tool_call_counts[tool_name] = (
            self.session.tool_call_counts.get(tool_name, 0) + 1
        )

    def check_rate_limit(self, tool_name: str) -> bool:
        """Check whether a tool is still within its per-run call budget."""
        acl = self.tools_config.acls.get(tool_name, ToolACL())
        current_calls = self.session.tool_call_counts.get(tool_name, 0)
        return current_calls < acl.max_calls_per_run

    def cache_research(self, key: str, value: Any) -> None:
        """Cache a research result."""
        self.session.research_cache[key] = value

    def get_cached_research(self, key: str) -> Any | None:
        """Get a cached research result."""
        return self.session.research_cache.get(key)

    def cache_llm(self, key: str, value: Any, max_items: int = 128) -> None:
        """Cache LLM responses to avoid duplicate expensive calls."""
        self.session.llm_cache[key] = value
        if len(self.session.llm_cache) > max_items:
            first_key = next(iter(self.session.llm_cache.keys()))
            self.session.llm_cache.pop(first_key, None)

    def get_cached_llm(self, key: str) -> Any | None:
        """Retrieve cached LLM response if present."""
        return self.session.llm_cache.get(key)

    def add_finding(self, finding: dict[str, Any]) -> None:
        """Add a finding to the session."""
        finding_dict: SessionFindingDict = {
            "id": finding.get("id", ""),
            "title": finding.get("title", ""),
            "severity": finding.get("severity", ""),
            "phase": finding.get("phase", ""),
            "discovered_by": finding.get("discovered_by", ""),
        }
        self.session.findings.append(finding_dict)

    def add_error(self, error: dict[str, Any]) -> None:
        """Record an error."""
        error_dict: SessionErrorDict = {
            "phase": error.get("phase", ""),
            "error": error.get("error", ""),
            "timestamp": datetime.now(UTC).isoformat(),
            "agent": error.get("agent", ""),
        }
        self.session.errors.append(error_dict)

    def set_phase(self, phase: str) -> None:
        """Set the current phase."""
        if self.session.current_phase != "init":
            self.session.phases_completed.append(self.session.current_phase)
        self.session.current_phase = phase

    def should_run_phase(self, phase: str) -> bool:
        """Check if a phase should be run based on configuration."""
        if self.phases is None:
            return True
        return phase in self.phases
