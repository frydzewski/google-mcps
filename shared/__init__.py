"""Shared utilities for Google MCPs."""
from .auth import GoogleAuth, GMAIL_SCOPES, SHEETS_SCOPES
from .paths import MCPPaths, get_data_dir, ensure_data_dirs

__all__ = [
    "GoogleAuth",
    "GMAIL_SCOPES",
    "SHEETS_SCOPES",
    "MCPPaths",
    "get_data_dir",
    "ensure_data_dirs",
]
