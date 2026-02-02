#!/usr/bin/env python3
"""Forms OAuth setup helper."""
import argparse
import os
import sys
from pathlib import Path

# Add parent to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from shared.auth import GoogleAuth, FORMS_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import FormsClient


APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")


def setup_auth(app_name: str = APP_NAME) -> FormsClient:
    """
    Run OAuth flow for Forms API.

    Args:
        app_name: Application name for data directory

    Returns:
        Authenticated FormsClient
    """
    paths = MCPPaths(app_name)
    ensure_data_dirs(paths.data_dir)

    print(f"Data directory: {paths.data_dir}")
    print(f"Credentials: {paths.forms_credentials}")
    print(f"Token: {paths.forms_token}")

    if not paths.forms_credentials.exists():
        print(f"\nError: Credentials file not found at {paths.forms_credentials}")
        print("Download OAuth credentials from Google Cloud Console.")
        sys.exit(1)

    print("\nAuthenticating with Google Forms...")
    auth = GoogleAuth(
        credentials_path=paths.forms_credentials,
        token_path=paths.forms_token,
        scopes=FORMS_SCOPES,
    )

    creds = auth.get_credentials()
    print("Authentication successful!")

    service = build("forms", "v1", credentials=creds)
    return FormsClient(service=service)


def test_connection(client: FormsClient, form_id: str):
    """
    Test forms access by getting form info.

    Args:
        client: Authenticated FormsClient
        form_id: Form ID to test with
    """
    print(f"\nTesting connection with form: {form_id}")

    try:
        form = client.get_form(form_id)
        print(f"\nForm: {form.title}")
        if form.description:
            print(f"Description: {form.description}")

        print(f"\nQuestions ({len(form.questions)}):")
        for q in form.questions[:5]:
            required = " *" if q.required else ""
            print(f"  - {q.title}{required} [{q.question_type}]")
        if len(form.questions) > 5:
            print(f"  ... and {len(form.questions) - 5} more")

        # Try to list responses
        print("\nResponses:")
        summary = client.list_responses(form_id, page_size=5)
        print(f"  Total: {summary.total_responses}")
        if summary.responses:
            for r in summary.responses[:3]:
                print(f"  - {r.response_id} ({r.last_submitted_time.strftime('%Y-%m-%d %H:%M')})")

        print("\nForms connection test successful!")

    except Exception as e:
        print(f"\nError accessing form: {e}")
        print("Make sure you have access to this form.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Forms OAuth setup")
    parser.add_argument(
        "--app-name",
        default=APP_NAME,
        help=f"Application name for data directory (default: {APP_NAME})",
    )
    parser.add_argument(
        "--test",
        metavar="FORM_ID",
        help="Test connection with a specific form ID",
    )
    args = parser.parse_args()

    client = setup_auth(args.app_name)

    if args.test:
        test_connection(client, args.test)


if __name__ == "__main__":
    main()
