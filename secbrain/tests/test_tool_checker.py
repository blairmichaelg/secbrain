"""Tests for tool checker utilities."""

from unittest.mock import MagicMock, patch

import pytest

from secbrain.utils.tool_checker import ToolChecker, ToolStatus, check_tools_on_startup


class TestToolStatus:
    """Test ToolStatus dataclass."""

    def test_tool_status_creation(self):
        """Test creating a ToolStatus instance."""
        status = ToolStatus(
            name="test_tool",
            available=True,
            path="/usr/bin/test_tool",
            version="1.0.0",
            install_guide="Install via: apt install test_tool",
            required=True,
        )
        assert status.name == "test_tool"
        assert status.available is True
        assert status.path == "/usr/bin/test_tool"
        assert status.version == "1.0.0"
        assert status.install_guide == "Install via: apt install test_tool"
        assert status.required is True

    def test_tool_status_defaults(self):
        """Test ToolStatus with default values."""
        status = ToolStatus(name="tool", available=False)
        assert status.name == "tool"
        assert status.available is False
        assert status.path is None
        assert status.version is None
        assert status.install_guide is None
        assert status.required is False


class TestToolChecker:
    """Test ToolChecker functionality."""

    def test_install_guides_exist(self):
        """Test that install guides are defined for common tools."""
        assert "foundry" in ToolChecker.INSTALL_GUIDES
        assert "nuclei" in ToolChecker.INSTALL_GUIDES
        assert "semgrep" in ToolChecker.INSTALL_GUIDES
        assert "subfinder" in ToolChecker.INSTALL_GUIDES
        assert "amass" in ToolChecker.INSTALL_GUIDES
        assert "httpx" in ToolChecker.INSTALL_GUIDES
        assert "ffuf" in ToolChecker.INSTALL_GUIDES
        assert "nmap" in ToolChecker.INSTALL_GUIDES

    def test_phase_tools_defined(self):
        """Test that phase tools are defined."""
        assert "recon" in ToolChecker.PHASE_TOOLS
        assert "hypothesis" in ToolChecker.PHASE_TOOLS
        assert "exploit" in ToolChecker.PHASE_TOOLS
        assert "static" in ToolChecker.PHASE_TOOLS

    def test_checker_initialization(self):
        """Test ToolChecker initialization."""
        checker = ToolChecker()
        assert isinstance(checker, ToolChecker)
        assert checker._cache == {}

    def test_checker_initialization_with_logger(self):
        """Test ToolChecker initialization with logger."""
        logger = MagicMock()
        checker = ToolChecker(logger=logger)
        assert checker.logger is logger

    def test_check_tool_available(self):
        """Test checking an available tool."""
        checker = ToolChecker()
        with patch("shutil.which", return_value="/usr/bin/python"):
            status = checker.check_tool("python")
            assert status.name == "python"
            assert status.available is True
            assert status.path == "/usr/bin/python"

    def test_check_tool_not_available(self):
        """Test checking an unavailable tool."""
        checker = ToolChecker()
        with patch("shutil.which", return_value=None):
            status = checker.check_tool("nonexistent_tool")
            assert status.name == "nonexistent_tool"
            assert status.available is False
            assert status.path is None

    def test_check_tool_foundry_special_case(self):
        """Test checking foundry uses forge."""
        checker = ToolChecker()
        with patch("shutil.which") as mock_which:
            def which_side_effect(tool):
                return "/usr/bin/forge" if tool == "forge" else None
            mock_which.side_effect = which_side_effect
            
            status = checker.check_tool("foundry")
            assert status.name == "foundry"
            assert status.available is True
            assert status.path == "/usr/bin/forge"

    def test_check_tool_caching(self):
        """Test that tool checks are cached."""
        checker = ToolChecker()
        with patch("shutil.which", return_value="/usr/bin/python") as mock_which:
            # First check
            status1 = checker.check_tool("python")
            # Second check should use cache
            status2 = checker.check_tool("python")
            
            # which should only be called once
            assert mock_which.call_count == 1
            assert status1 is status2

    def test_check_tool_with_logger_missing_required(self):
        """Test logging when required tool is missing."""
        logger = MagicMock()
        checker = ToolChecker(logger=logger)
        with patch("shutil.which", return_value=None):
            checker.check_tool("tool", required=True)
            logger.warning.assert_called_once()

    def test_check_tool_with_logger_missing_optional(self):
        """Test logging when optional tool is missing."""
        logger = MagicMock()
        checker = ToolChecker(logger=logger)
        with patch("shutil.which", return_value=None):
            checker.check_tool("tool", required=False)
            logger.info.assert_called_once()

    def test_check_phase_tools_recon(self):
        """Test checking tools for recon phase."""
        checker = ToolChecker()
        with patch("shutil.which", return_value=None):
            result = checker.check_phase_tools("recon")
            assert "required" in result
            assert "recommended" in result
            assert len(result["required"]) > 0  # foundry
            assert len(result["recommended"]) > 0

    def test_check_phase_tools_unknown_phase(self):
        """Test checking tools for unknown phase."""
        checker = ToolChecker()
        result = checker.check_phase_tools("unknown")
        assert result == {"required": [], "recommended": []}

    def test_validate_required_tools_all_present(self):
        """Test validating required tools when all present."""
        checker = ToolChecker()
        with patch("shutil.which", return_value="/usr/bin/tool"):
            all_available, missing = checker.validate_required_tools("recon")
            assert all_available is True
            assert missing == []

    def test_validate_required_tools_some_missing(self):
        """Test validating required tools with some missing."""
        checker = ToolChecker()
        with patch("shutil.which", return_value=None):
            all_available, missing = checker.validate_required_tools("recon")
            assert all_available is False
            assert len(missing) > 0

    def test_get_missing_tools_report_with_phase(self):
        """Test generating missing tools report for a specific phase."""
        checker = ToolChecker()
        with patch("shutil.which", return_value=None):
            report = checker.get_missing_tools_report("recon")
            assert "REQUIRED TOOLS MISSING" in report or "RECOMMENDED TOOLS MISSING" in report
            assert "foundry" in report.lower()

    def test_get_missing_tools_report_all_phases(self):
        """Test generating missing tools report for all phases."""
        checker = ToolChecker()
        with patch("shutil.which", return_value=None):
            report = checker.get_missing_tools_report()
            assert isinstance(report, str)
            assert len(report) > 0

    def test_get_missing_tools_report_all_available(self):
        """Test report when all tools are available."""
        checker = ToolChecker()
        with patch("shutil.which", return_value="/usr/bin/tool"):
            report = checker.get_missing_tools_report()
            assert "All tools are available!" in report


def test_check_tools_on_startup():
    """Test check_tools_on_startup function."""
    with patch("shutil.which", return_value=None):
        checker = check_tools_on_startup()
        assert isinstance(checker, ToolChecker)
        # Should have checked tools and cached them
        assert len(checker._cache) > 0


def test_check_tools_on_startup_with_logger():
    """Test check_tools_on_startup with logger."""
    logger = MagicMock()
    with patch("shutil.which", return_value=None):
        checker = check_tools_on_startup(logger)
        assert isinstance(checker, ToolChecker)
        # Logger should have been called
        logger.info.assert_called()
