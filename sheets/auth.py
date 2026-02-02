#!/usr/bin/env python3
"""Sheets OAuth setup helper."""
import argparse
import os
import sys
from pathlib import Path

# Add parent to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from shared.auth import GoogleAuth, SHEETS_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs

APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")


def main():
    parser = argparse.ArgumentParser(description="Google Sheets OAuth setup")
    parser.add_argument(
        "--app-name",
        default=APP_NAME,
        help=f"Application name for data directory (default: {APP_NAME})",
    )
    parser.add_argument(
        "--test",
        metavar="SPREADSHEET_ID",
        help="Test authentication by reading a spreadsheet",
    )
    args = parser.parse_args()

    paths = MCPPaths(args.app_name)
    ensure_data_dirs(paths.data_dir)

    print(f"Data directory: {paths.data_dir}")
    print(f"Credentials: {paths.sheets_credentials}")
    print(f"Token: {paths.sheets_token}")

    if not paths.sheets_credentials.exists():
        print(f"\nError: Credentials file not found at {paths.sheets_credentials}")
        print("Download OAuth credentials from Google Cloud Console.")
        print("Note: Sheets can share the same credentials file as Gmail.")
        sys.exit(1)

    print("\nAuthenticating with Google Sheets...")
    auth = GoogleAuth(
        credentials_path=paths.sheets_credentials,
        token_path=paths.sheets_token,
        scopes=SHEETS_SCOPES,
    )

    creds = auth.get_credentials()
    print("Authentication successful!")

    if args.test:
        print(f"\nTesting with spreadsheet: {args.test}")
        service = build("sheets", "v4", credentials=creds)

        try:
            result = service.spreadsheets().get(spreadsheetId=args.test).execute()
            title = result.get("properties", {}).get("title", "Unknown")
            sheets = result.get("sheets", [])

            print(f"  Title: {title}")
            print(f"  Sheets: {len(sheets)}")
            for sheet in sheets:
                props = sheet.get("properties", {})
                print(f"    - {props.get('title', 'Unknown')}")
            print("\nTest successful!")
        except Exception as e:
            print(f"Test failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
