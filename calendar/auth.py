#!/usr/bin/env python3
"""Calendar OAuth setup helper."""
import argparse
import os
import sys
from pathlib import Path

# Add parent to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from shared.auth import GoogleAuth, CALENDAR_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import CalendarClient

APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")


def setup_auth(app_name: str = APP_NAME) -> CalendarClient:
    """
    Run OAuth flow for Calendar API.

    Args:
        app_name: Application name for data directory

    Returns:
        Authenticated CalendarClient
    """
    paths = MCPPaths(app_name)
    ensure_data_dirs(paths.data_dir)

    print(f"Data directory: {paths.data_dir}")
    print(f"Credentials: {paths.calendar_credentials}")
    print(f"Token: {paths.calendar_token}")

    if not paths.calendar_credentials.exists():
        print(f"\nError: Credentials file not found at {paths.calendar_credentials}")
        print("Download OAuth credentials from Google Cloud Console.")
        sys.exit(1)

    print("\nAuthenticating with Google Calendar...")
    auth = GoogleAuth(
        credentials_path=paths.calendar_credentials,
        token_path=paths.calendar_token,
        scopes=CALENDAR_SCOPES,
    )

    creds = auth.get_credentials()
    print("Authentication successful!")

    service = build("calendar", "v3", credentials=creds)
    return CalendarClient(service=service)


def test_connection(client: CalendarClient, calendar_id: str = "primary"):
    """
    Test calendar access by listing calendars and events.

    Args:
        client: Authenticated CalendarClient
        calendar_id: Calendar ID to test with
    """
    print(f"\nTesting connection to calendar: {calendar_id}")

    # List calendars
    print("\nCalendars:")
    calendars = client.list_calendars()
    for cal in calendars[:5]:
        marker = " (primary)" if cal.primary else ""
        print(f"  - {cal.summary}{marker}")
    if len(calendars) > 5:
        print(f"  ... and {len(calendars) - 5} more")

    # List upcoming events
    print(f"\nUpcoming events from '{calendar_id}':")
    events = client.list_events(calendar_id=calendar_id, max_results=5)
    if events:
        for event in events:
            print(f"  - {event.summary} ({event.start.strftime('%Y-%m-%d %H:%M')})")
    else:
        print("  (No upcoming events)")

    print("\nCalendar connection test successful!")


def main():
    parser = argparse.ArgumentParser(description="Calendar OAuth setup")
    parser.add_argument(
        "--app-name",
        default=APP_NAME,
        help=f"Application name for data directory (default: {APP_NAME})",
    )
    parser.add_argument(
        "--test",
        nargs="?",
        const="primary",
        help="Test connection after auth (optionally specify calendar ID)",
    )
    args = parser.parse_args()

    client = setup_auth(args.app_name)

    if args.test:
        test_connection(client, args.test)


if __name__ == "__main__":
    main()
