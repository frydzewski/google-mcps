#!/usr/bin/env python3
"""Slides OAuth setup helper."""
import argparse
import os
import sys
from pathlib import Path

# Add parent to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from shared.auth import GoogleAuth, SLIDES_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import SlidesClient

APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")


def setup_auth(app_name: str = APP_NAME) -> SlidesClient:
    """
    Run OAuth flow for Slides API.

    Args:
        app_name: Application name for data directory

    Returns:
        Authenticated SlidesClient
    """
    paths = MCPPaths(app_name)
    ensure_data_dirs(paths.data_dir)

    print(f"Data directory: {paths.data_dir}")
    print(f"Credentials: {paths.slides_credentials}")
    print(f"Token: {paths.slides_token}")

    if not paths.slides_credentials.exists():
        print(f"\nError: Credentials file not found at {paths.slides_credentials}")
        print("Download OAuth credentials from Google Cloud Console.")
        sys.exit(1)

    print("\nAuthenticating with Google Slides...")
    auth = GoogleAuth(
        credentials_path=paths.slides_credentials,
        token_path=paths.slides_token,
        scopes=SLIDES_SCOPES,
    )

    creds = auth.get_credentials()
    print("Authentication successful!")

    service = build("slides", "v1", credentials=creds)
    return SlidesClient(service=service)


def test_connection(client: SlidesClient, presentation_id: str):
    """
    Test slides access by getting presentation info.

    Args:
        client: Authenticated SlidesClient
        presentation_id: Presentation ID to test with
    """
    print(f"\nTesting connection with presentation: {presentation_id}")

    pres = client.get_presentation(presentation_id)
    print(f"\nPresentation: {pres.title}")
    print(f"Slides: {pres.slide_count}")

    # Show slide summary
    slides = client.list_slides(presentation_id)
    print("\nSlide summary:")
    for i, slide in enumerate(slides[:5], start=1):
        text = slide.get_text_content()
        preview = text[:50] + "..." if len(text) > 50 else text
        preview = preview.replace("\n", " ")
        print(f"  {i}. {preview if preview else '(no text)'}")

    if len(slides) > 5:
        print(f"  ... and {len(slides) - 5} more slides")

    print("\nSlides connection test successful!")


def main():
    parser = argparse.ArgumentParser(description="Slides OAuth setup")
    parser.add_argument(
        "--app-name",
        default=APP_NAME,
        help=f"Application name for data directory (default: {APP_NAME})",
    )
    parser.add_argument(
        "--test",
        metavar="PRESENTATION_ID",
        help="Test connection with a presentation ID",
    )
    args = parser.parse_args()

    client = setup_auth(args.app_name)

    if args.test:
        test_connection(client, args.test)


if __name__ == "__main__":
    main()
