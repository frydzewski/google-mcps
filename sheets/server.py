"""Sheets MCP Server - Google Sheets operations via Model Context Protocol.

This is a READ-ONLY MCP. It does not modify spreadsheet data.
"""
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build

from shared.auth import GoogleAuth, SHEETS_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import SheetsClient

# Initialize the MCP server
mcp = FastMCP("sheets")

# App name can be overridden via environment
APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")

# Cached instances
_paths: Optional[MCPPaths] = None
_sheets_client: Optional[SheetsClient] = None


def get_paths() -> MCPPaths:
    """Get or create paths instance."""
    global _paths
    if _paths is None:
        _paths = MCPPaths(APP_NAME)
        ensure_data_dirs(_paths.data_dir)
    return _paths


def get_sheets_client() -> SheetsClient:
    """Get or create authenticated Sheets client."""
    global _sheets_client

    if _sheets_client is not None:
        return _sheets_client

    paths = get_paths()

    if not paths.sheets_token.exists():
        raise RuntimeError(
            f"Sheets not authenticated. Token not found at: {paths.sheets_token}\n"
            "Run: python -m sheets.auth"
        )

    auth = GoogleAuth(
        credentials_path=paths.sheets_credentials,
        token_path=paths.sheets_token,
        scopes=SHEETS_SCOPES,
    )

    creds = auth.get_credentials()
    service = build("sheets", "v4", credentials=creds)
    client = SheetsClient(service=service)

    _sheets_client = client
    return _sheets_client


# =============================================================================
# SHEETS OPERATIONS (5 read-only tools)
# =============================================================================


@mcp.tool()
def get_spreadsheet_info(spreadsheet_id: str) -> dict:
    """
    Get metadata about a spreadsheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID (from the URL)

    Returns:
        Spreadsheet info including title, locale, timezone, and list of sheets
    """
    client = get_sheets_client()
    info = client.get_spreadsheet_info(spreadsheet_id)

    return {
        "spreadsheet_id": info.spreadsheet_id,
        "title": info.title,
        "locale": info.locale,
        "time_zone": info.time_zone,
        "sheets": [
            {
                "title": s.title,
                "sheet_id": s.sheet_id,
                "row_count": s.row_count,
                "column_count": s.column_count,
            }
            for s in info.sheets
        ],
    }


@mcp.tool()
def list_sheets(spreadsheet_id: str) -> list[dict]:
    """
    List all sheets (tabs) in a spreadsheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID

    Returns:
        List of sheets with title, sheet_id, row_count, column_count
    """
    client = get_sheets_client()
    return client.list_sheets(spreadsheet_id)


@mcp.tool()
def get_headers(spreadsheet_id: str, sheet_name: str) -> list[str]:
    """
    Get column headers (first row) from a sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID
        sheet_name: Name of the sheet (tab) to read headers from

    Returns:
        List of column header names
    """
    client = get_sheets_client()
    return client.get_headers(spreadsheet_id, sheet_name)


@mcp.tool()
def read_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    range_notation: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    """
    Read rows from a sheet as dictionaries.

    The first row is treated as column headers. Each subsequent row
    becomes a dictionary with header names as keys.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID
        sheet_name: Name of the sheet (tab) to read
        range_notation: Optional A1 notation to limit the range (e.g., "A2:E100").
                       If not provided, reads all data.
        limit: Maximum number of rows to return (default 1000)

    Returns:
        List of row dictionaries
    """
    client = get_sheets_client()
    rows = client.read_sheet(
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name,
        range_notation=range_notation,
        include_headers=True,
    )
    return rows[:limit]


@mcp.tool()
def find_rows(
    spreadsheet_id: str,
    sheet_name: str,
    column: str,
    value: str,
    exact_match: bool = True,
) -> list[dict]:
    """
    Find rows where a column matches a value.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID
        sheet_name: Name of the sheet (tab) to search
        column: Column name to search in
        value: Value to search for
        exact_match: If True, requires exact match. If False, searches for
                    rows where the column contains the value (case-insensitive).

    Returns:
        List of matching row dictionaries
    """
    client = get_sheets_client()
    return client.find_rows(
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name,
        column=column,
        value=value,
        exact_match=exact_match,
    )
