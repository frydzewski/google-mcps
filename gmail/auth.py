#!/usr/bin/env python3
"""Gmail OAuth setup helper."""
import argparse
import os
import sys
from pathlib import Path

# Add parent to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from shared.auth import GoogleAuth, GMAIL_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import GmailClient

APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")


def main():
    parser = argparse.ArgumentParser(description="Gmail OAuth setup")
    parser.add_argument(
        "--app-name",
        default=APP_NAME,
        help=f"Application name for data directory (default: {APP_NAME})",
    )
    parser.add_argument(
        "--create-labels",
        action="store_true",
        help="Create classification labels after authentication",
    )
    args = parser.parse_args()

    paths = MCPPaths(args.app_name)
    ensure_data_dirs(paths.data_dir)

    print(f"Data directory: {paths.data_dir}")
    print(f"Credentials: {paths.gmail_credentials}")
    print(f"Token: {paths.gmail_token}")

    if not paths.gmail_credentials.exists():
        print(f"\nError: Credentials file not found at {paths.gmail_credentials}")
        print("Download OAuth credentials from Google Cloud Console.")
        sys.exit(1)

    print("\nAuthenticating with Gmail...")
    auth = GoogleAuth(
        credentials_path=paths.gmail_credentials,
        token_path=paths.gmail_token,
        scopes=GMAIL_SCOPES,
    )

    creds = auth.get_credentials()
    print("Authentication successful!")

    if args.create_labels:
        print("\nCreating classification labels...")
        service = build("gmail", "v1", credentials=creds)
        client = GmailClient(service=service)
        client.ensure_labels_exist()
        print("Labels created successfully!")


if __name__ == "__main__":
    main()
