"""Bootstrap tests for AI Visibility package."""

import json
import subprocess
from pathlib import Path

import pytest

from ai_visibility import __version__
from ai_visibility.config import Settings, get_settings
from ai_visibility.cli import doctor


class TestPackageImport:
    """Test that the package imports correctly."""

    def test_package_version_exists(self) -> None:
        """Test that package version is defined."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert __version__ == "0.1.0"

    def test_package_metadata(self) -> None:
        """Test that package metadata is available."""
        from ai_visibility import __author__, __description__

        assert __author__ == "Solara AI"
        assert "LLM provider" in __description__


class TestSettingsLoading:
    """Test configuration loading from environment."""

    def test_settings_defaults(self) -> None:
        """Test that settings load with defaults."""
        settings = get_settings()
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_providers_default(self) -> None:
        """Test that providers default includes core providers."""
        settings = get_settings()
        assert "openai" in settings.providers
        assert "anthropic" in settings.providers

    def test_settings_db_path_default(self) -> None:
        """Test that db_path default is set."""
        settings = get_settings()
        assert settings.db_path == "./data/ai_visibility.db"

    def test_settings_log_level_default(self) -> None:
        """Test that log_level default is set."""
        settings = get_settings()
        assert settings.log_level == "INFO"

    def test_settings_llm_framework(self) -> None:
        """Test that llm_framework is set to solaraai-llm."""
        settings = get_settings()
        assert settings.llm_framework == "solaraai-llm"

    def test_settings_providers_list_parsing(self) -> None:
        """Test that providers are parsed into a list."""
        settings = get_settings()
        providers = settings.providers_list
        assert isinstance(providers, list)
        assert len(providers) > 0
        assert "openai" in providers
        assert "anthropic" in providers


class TestCliDoctor:
    """Test the CLI doctor command."""

    def test_doctor_returns_dict(self) -> None:
        """Test that doctor command returns a dictionary."""
        result = doctor(format="json")
        assert isinstance(result, dict)

    def test_doctor_has_status(self) -> None:
        """Test that doctor result includes status."""
        result = doctor(format="json")
        assert "status" in result
        assert result["status"] == "healthy"

    def test_doctor_has_llm_framework(self) -> None:
        """Test that doctor result includes llm_framework."""
        result = doctor(format="json")
        assert "llm_framework" in result
        assert result["llm_framework"] == "solaraai-llm"

    def test_doctor_has_db_path(self) -> None:
        """Test that doctor result includes db_path."""
        result = doctor(format="json")
        assert "db_path" in result
        assert result["db_path"] == "./data/ai_visibility.db"

    def test_doctor_has_providers(self) -> None:
        """Test that doctor result includes providers."""
        result = doctor(format="json")
        assert "providers" in result
        assert "available" in result["providers"]
        assert isinstance(result["providers"]["available"], list)
        assert len(result["providers"]["available"]) > 0

    def test_doctor_has_provider_count(self) -> None:
        """Test that doctor result includes provider count."""
        result = doctor(format="json")
        assert "count" in result["providers"]
        assert result["providers"]["count"] == len(result["providers"]["available"])


class TestCliExecution:
    """Test CLI execution via subprocess."""

    def test_cli_doctor_command_exits_zero(self) -> None:
        """Test that CLI doctor command exits with code 0."""
        result = subprocess.run(
            ["python", "-m", "ai_visibility.cli", "doctor", "--format", "json"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_cli_doctor_output_is_valid_json(self) -> None:
        """Test that CLI doctor output is valid JSON."""
        result = subprocess.run(
            ["python", "-m", "ai_visibility.cli", "doctor", "--format", "json"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert "status" in output
        assert output["status"] == "healthy"

    def test_cli_doctor_output_contains_required_fields(self) -> None:
        """Test that CLI doctor output contains all required fields."""
        result = subprocess.run(
            ["python", "-m", "ai_visibility.cli", "doctor", "--format", "json"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "status" in output
        assert "llm_framework" in output
        assert "db_path" in output
        assert "providers" in output
        assert "available" in output["providers"]
