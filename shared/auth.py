"""Google OAuth authentication utilities."""
import sys
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for different Google APIs
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.compose",  # For drafts
    "https://www.googleapis.com/auth/gmail.modify",   # For applying labels
]

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


class GoogleAuth:
    """Handle Google OAuth authentication."""

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        scopes: list[str],
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes

    def get_credentials(self) -> Credentials:
        """Get valid credentials, refreshing or re-authenticating as needed."""
        creds = None

        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_path),
                self.scopes
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"OAuth credentials not found at: {self.credentials_path}\n"
                        "Download from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save refreshed/new credentials
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json())

        return creds

    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        if not self.token_path.exists():
            return False
        try:
            creds = Credentials.from_authorized_user_file(
                str(self.token_path),
                self.scopes
            )
            return creds.valid or (creds.expired and creds.refresh_token)
        except Exception:
            return False
