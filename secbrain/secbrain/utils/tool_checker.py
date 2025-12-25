"""Tool availability checker and guidance system.

This module provides utilities to check if external tools are available,
provide installation guidance, and gracefully handle missing tools.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import structlog


@dataclass
class ToolStatus:
    """Status of an external tool."""

    name: str
    available: bool
    path: str | None = None
    version: str | None = None
    install_guide: str | None = None
    required: bool = False


class ToolChecker:
    """Check availability of external tools and provide guidance."""

    # Tool installation guides
    INSTALL_GUIDES: ClassVar[dict[str, str]] = {
        "foundry": """
Foundry is required for smart contract testing.

Install via foundryup:
  curl -L https://foundry.paradigm.xyz | bash
  foundryup

Or via package manager:
  brew install foundry     # macOS

Verify installation:
  forge --version
""",
        "nuclei": """
Nuclei is recommended for automated vulnerability scanning.

Install via:
  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

Or via package manager:
  brew install nuclei      # macOS

Update templates:
  nuclei -update-templates

Verify installation:
  nuclei -version
""",
        "semgrep": """
Semgrep is recommended for static code analysis.

Install via pip:
  pip install semgrep

Or via package manager:
  brew install semgrep     # macOS

Verify installation:
  semgrep --version
""",
        "subfinder": """
Subfinder is recommended for subdomain discovery.

Install via:
  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

Or via package manager:
  brew install subfinder   # macOS

Verify installation:
  subfinder -version
""",
        "amass": """
Amass is recommended for comprehensive asset discovery.

Install via:
  go install -v github.com/owasp-amass/amass/v4/...@master

Or via package manager:
  brew install amass       # macOS

Verify installation:
  amass -version
""",
        "httpx": """
httpx is recommended for HTTP probing.

Install via:
  go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

Or via package manager:
  brew install httpx       # macOS

Verify installation:
  httpx -version
""",
        "ffuf": """
ffuf is recommended for fuzzing and content discovery.

Install via:
  go install github.com/ffuf/ffuf/v2@latest

Or via package manager:
  brew install ffuf        # macOS

Verify installation:
  ffuf -V
""",
        "nmap": """
nmap is recommended for port scanning and service detection.

Install via package manager:
  brew install nmap        # macOS
  apt install nmap         # Ubuntu/Debian
  yum install nmap         # CentOS/RHEL

Verify installation:
  nmap --version
""",
    }

    # Tool requirements by phase
    PHASE_TOOLS: ClassVar[dict[str, dict[str, list[str]]]] = {
        "recon": {
            "required": ["foundry"],
            "recommended": ["subfinder", "amass", "httpx", "nuclei"],
        },
        "hypothesis": {
            "required": [],
            "recommended": ["foundry"],
        },
        "exploit": {
            "required": ["foundry"],
            "recommended": [],
        },
        "static": {
            "required": [],
            "recommended": ["semgrep"],
        },
    }

    def __init__(self, logger: structlog.stdlib.BoundLogger | None = None):
        self.logger = logger
        self._cache: dict[str, ToolStatus] = {}

    def check_tool(self, tool_name: str, required: bool = False) -> ToolStatus:
        """
        Check if a tool is available.

        Args:
            tool_name: Name of the tool (e.g., "foundry", "nuclei")
            required: Whether the tool is required for the workflow

        Returns:
            ToolStatus with availability information
        """
        # Check cache first
        if tool_name in self._cache:
            return self._cache[tool_name]

        # Find executable
        path = shutil.which(tool_name)

        # Special handling for certain tools
        if tool_name == "foundry":
            # Foundry is accessed via forge/cast/anvil
            path = shutil.which("forge")

        status = ToolStatus(
            name=tool_name,
            available=path is not None,
            path=path,
            install_guide=self.INSTALL_GUIDES.get(tool_name),
            required=required,
        )

        # Cache result
        self._cache[tool_name] = status

        # Log if tool is missing
        if not status.available and self.logger:
            if required:
                self.logger.warning(
                    "tool_missing",
                    tool=tool_name,
                    required=True,
                )
            else:
                self.logger.info(
                    "tool_unavailable",
                    tool=tool_name,
                    required=False,
                )

        return status

    def check_phase_tools(self, phase: str) -> dict[str, list[ToolStatus]]:
        """
        Check all tools needed for a phase.

        Args:
            phase: Phase name (e.g., "recon", "exploit")

        Returns:
            Dict with "required" and "recommended" tool statuses
        """
        phase_reqs = self.PHASE_TOOLS.get(phase, {"required": [], "recommended": []})

        required = [
            self.check_tool(tool, required=True) for tool in phase_reqs["required"]
        ]

        recommended = [
            self.check_tool(tool, required=False) for tool in phase_reqs["recommended"]
        ]

        return {
            "required": required,
            "recommended": recommended,
        }

    def get_missing_tools_report(self, phase: str | None = None) -> str:
        """
        Generate a report of missing tools.

        Args:
            phase: Optional phase name to check specific phase tools

        Returns:
            Formatted report with installation guidance
        """
        if phase:
            tools_status = self.check_phase_tools(phase)
            missing_required = [t for t in tools_status["required"] if not t.available]
            missing_recommended = [
                t for t in tools_status["recommended"] if not t.available
            ]
        else:
            # Check all tools
            all_tools = set()
            for phase_tools in self.PHASE_TOOLS.values():
                all_tools.update(phase_tools["required"])
                all_tools.update(phase_tools["recommended"])

            missing_required = []
            missing_recommended = []
            for tool in all_tools:
                status = self.check_tool(tool)
                if not status.available:
                    # Determine if required for any phase
                    is_required = any(
                        tool in phase_tools["required"]
                        for phase_tools in self.PHASE_TOOLS.values()
                    )
                    if is_required:
                        missing_required.append(status)
                    else:
                        missing_recommended.append(status)

        # Build report
        report_lines = []

        if missing_required:
            report_lines.append("WARNING: REQUIRED TOOLS MISSING:")
            report_lines.append("")
            for tool in missing_required:
                report_lines.append(f"  - {tool.name}")
                if tool.install_guide:
                    report_lines.append(f"{tool.install_guide}")
                report_lines.append("")

        if missing_recommended:
            report_lines.append("INFO: RECOMMENDED TOOLS MISSING:")
            report_lines.append("")
            for tool in missing_recommended:
                report_lines.append(f"  - {tool.name}")
                if tool.install_guide:
                    # Add indented install guide
                    indent = "    "
                    for line in tool.install_guide.strip().split("\n"):
                        report_lines.append(f"{indent}{line}")
                report_lines.append("")

        if not missing_required and not missing_recommended:
            report_lines.append("All tools are available!")

        return "\n".join(report_lines)

    def validate_required_tools(self, phase: str) -> tuple[bool, list[str]]:
        """
        Validate that all required tools for a phase are available.

        Args:
            phase: Phase name

        Returns:
            Tuple of (all_available, missing_tool_names)
        """
        tools_status = self.check_phase_tools(phase)
        missing = [t.name for t in tools_status["required"] if not t.available]
        return (len(missing) == 0, missing)


def check_tools_on_startup(
    logger: structlog.stdlib.BoundLogger | None = None,
) -> ToolChecker:
    """
    Check tool availability on startup and log results.

    Args:
        logger: Optional logger for reporting

    Returns:
        ToolChecker instance with cached results
    """
    checker = ToolChecker(logger)

    # Check all known tools
    all_tools = set()
    for phase_tools in ToolChecker.PHASE_TOOLS.values():
        all_tools.update(phase_tools["required"])
        all_tools.update(phase_tools["recommended"])

    available = []
    missing = []

    for tool in sorted(all_tools):
        status = checker.check_tool(tool)
        if status.available:
            available.append(tool)
        else:
            missing.append(tool)

    if logger:
        logger.info(
            "tool_check_complete",
            available_count=len(available),
            missing_count=len(missing),
            available=available,
            missing=missing,
        )

    return checker
