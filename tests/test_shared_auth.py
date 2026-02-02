"""Tests for shared auth utilities."""
import pytest
from pathlib import Path
from shared.paths import get_data_dir, MCPPaths


class TestGetDataDir:
    """Test data directory resolution."""

    def test_default_path(self, monkeypatch):
        """Should use ~/.app-name by default."""
        monkeypatch.delenv("TEST_APP_DATA_DIR", raising=False)
        path = get_data_dir("test-app")
        assert path == Path.home() / ".test-app"

    def test_env_override(self, monkeypatch):
        """Should respect environment variable."""
        monkeypatch.setenv("TEST_APP_DATA_DIR", "/custom/path")
        path = get_data_dir("test-app")
        assert path == Path("/custom/path")


class TestMCPPaths:
    """Test MCPPaths class."""

    def test_gmail_paths(self, tmp_path):
        """Should provide correct Gmail credential paths."""
        paths = MCPPaths("test-app", data_dir=tmp_path)

        assert paths.gmail_credentials == tmp_path / "credentials" / "gmail_credentials.json"
        assert paths.gmail_token == tmp_path / "credentials" / "token.json"

    def test_sheets_paths(self, tmp_path):
        """Should provide correct Sheets credential paths."""
        paths = MCPPaths("test-app", data_dir=tmp_path)

        # Sheets shares credentials file with Gmail
        assert paths.sheets_credentials == tmp_path / "credentials" / "gmail_credentials.json"
        assert paths.sheets_token == tmp_path / "credentials" / "sheets_token.json"

    def test_directory_paths(self, tmp_path):
        """Should provide correct directory paths."""
        paths = MCPPaths("test-app", data_dir=tmp_path)

        assert paths.config_dir == tmp_path / "config"
        assert paths.credentials_dir == tmp_path / "credentials"
        assert paths.data_files_dir == tmp_path / "data"
        assert paths.logs_dir == tmp_path / "logs"
        assert paths.versions_dir == tmp_path / "versions"
