"""Path management for Google MCPs."""
import os
from pathlib import Path
from typing import Optional


def get_data_dir(app_name: str) -> Path:
    """
    Get the user data directory for an MCP application.

    Priority:
    1. {APP_NAME}_DATA_DIR environment variable (uppercase, underscores)
    2. ~/.{app_name}/ (lowercase, hyphens)

    Args:
        app_name: Application name (e.g., "letter-rip", "letter-rip-pipeline")

    Returns:
        Path to data directory
    """
    # Environment variable: LETTER_RIP_DATA_DIR
    env_var = app_name.upper().replace("-", "_") + "_DATA_DIR"
    env_dir = os.environ.get(env_var)
    if env_dir:
        return Path(env_dir).expanduser()

    # Default: ~/.letter-rip/
    return Path.home() / f".{app_name}"


def ensure_data_dirs(data_dir: Path) -> None:
    """
    Ensure all required subdirectories exist.

    Creates:
    - config/
    - credentials/
    - data/
    - logs/
    - versions/
    """
    subdirs = ["config", "credentials", "data", "logs", "versions"]
    for subdir in subdirs:
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)


class MCPPaths:
    """
    Centralized path access for MCP applications.

    Usage:
        paths = MCPPaths("letter-rip")
        creds = paths.gmail_credentials
        token = paths.gmail_token
    """

    def __init__(self, app_name: str, data_dir: Optional[Path] = None):
        self.app_name = app_name
        self._data_dir = data_dir or get_data_dir(app_name)

    @property
    def data_dir(self) -> Path:
        """Root data directory."""
        return self._data_dir

    @property
    def config_dir(self) -> Path:
        """Configuration files directory."""
        return self._data_dir / "config"

    @property
    def credentials_dir(self) -> Path:
        """Credentials directory."""
        return self._data_dir / "credentials"

    @property
    def data_files_dir(self) -> Path:
        """Data files directory."""
        return self._data_dir / "data"

    @property
    def logs_dir(self) -> Path:
        """Logs directory."""
        return self._data_dir / "logs"

    @property
    def versions_dir(self) -> Path:
        """Backup versions directory."""
        return self._data_dir / "versions"

    # Gmail-specific paths
    @property
    def gmail_credentials(self) -> Path:
        """Gmail OAuth client credentials."""
        return self.credentials_dir / "gmail_credentials.json"

    @property
    def gmail_token(self) -> Path:
        """Gmail OAuth token."""
        return self.credentials_dir / "token.json"

    # Sheets-specific paths
    @property
    def sheets_credentials(self) -> Path:
        """Sheets OAuth client credentials (can share with Gmail)."""
        return self.credentials_dir / "gmail_credentials.json"

    @property
    def sheets_token(self) -> Path:
        """Sheets OAuth token."""
        return self.credentials_dir / "sheets_token.json"

    # Calendar-specific paths
    @property
    def calendar_credentials(self) -> Path:
        """Calendar OAuth client credentials (can share with Gmail)."""
        return self.credentials_dir / "gmail_credentials.json"

    @property
    def calendar_token(self) -> Path:
        """Calendar OAuth token."""
        return self.credentials_dir / "calendar_token.json"
