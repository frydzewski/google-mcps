"""Gmail MCP server exposing email operations via Model Context Protocol."""
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from shared.auth import GoogleAuth, GMAIL_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import (
    GmailClient,
    LABELS,
    VALID_KEYS,
    GMAIL_NAMES,
    normalize_label,
    get_gmail_name,
)

# Get app name from environment (for credential paths)
APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")

# Initialize the MCP server
mcp = FastMCP("gmail-mcp")

# Cached instances
_paths: Optional[MCPPaths] = None
_gmail_client: Optional[GmailClient] = None


def get_paths() -> MCPPaths:
    """Get or create the paths instance."""
    global _paths
    if _paths is None:
        _paths = MCPPaths(APP_NAME)
        ensure_data_dirs(_paths.data_dir)
    return _paths


def get_gmail_client() -> GmailClient:
    """Get or create authenticated Gmail client (cached)."""
    global _gmail_client

    if _gmail_client is not None:
        return _gmail_client

    from googleapiclient.discovery import build

    paths = get_paths()

    if not paths.gmail_token.exists():
        raise RuntimeError(
            f"Gmail not authenticated. Token not found at: {paths.gmail_token}\n"
            "Run 'python -m gmail.auth' to authenticate."
        )

    auth = GoogleAuth(
        credentials_path=paths.gmail_credentials,
        token_path=paths.gmail_token,
        scopes=GMAIL_SCOPES,
    )
    creds = auth.get_credentials()
    service = build("gmail", "v1", credentials=creds)
    client = GmailClient(service=service)

    # Ensure classification labels exist in Gmail
    client.ensure_labels_exist()

    _gmail_client = client
    return _gmail_client


# =============================================================================
# EMAIL OPERATIONS
# =============================================================================


@mcp.tool()
def list_emails(
    labels: list[str] | None = None,
    days: int = 7,
    limit: int = 50,
) -> list[dict]:
    """
    Fetch emails with optional filters.

    Args:
        labels: Filter by Gmail labels (e.g., ["INBOX", "UNREAD"])
        days: Only fetch emails from the last N days
        limit: Maximum number of emails to return

    Returns:
        List of email summaries with id, sender, subject, snippet, timestamp
    """
    gmail = get_gmail_client()
    emails = gmail.fetch_unprocessed_emails(max_results=limit, newer_than_days=days)

    # Filter by labels if specified
    if labels:
        emails = [e for e in emails if any(label in e.labels for label in labels)]

    return [
        {
            "id": e.id,
            "thread_id": e.thread_id,
            "sender": e.sender,
            "subject": e.subject,
            "snippet": e.snippet,
            "timestamp": e.timestamp,
            "labels": e.labels,
        }
        for e in emails
    ]


@mcp.tool()
def get_email(email_id: str) -> dict:
    """
    Get full email content by ID.

    Args:
        email_id: The Gmail message ID

    Returns:
        Full email content including body, thread context
    """
    gmail = get_gmail_client()
    email = gmail.get_email(email_id)

    if not email:
        raise ValueError(f"Email not found: {email_id}")

    return {
        "id": email.id,
        "thread_id": email.thread_id,
        "sender": email.sender,
        "subject": email.subject,
        "body": email.body,
        "snippet": email.snippet,
        "timestamp": email.timestamp,
        "labels": email.labels,
    }


def _apply_label(email_id: str, label_key: str) -> dict:
    """Internal helper to apply a label."""
    if label_key not in LABELS:
        raise ValueError(
            f"Label key '{label_key}' not in LABELS. "
            f"Valid keys: {VALID_KEYS}."
        )

    gmail = get_gmail_client()
    gmail.apply_label(email_id, label_key)
    return {"status": "applied", "email_id": email_id, "label": get_gmail_name(label_key)}


@mcp.tool()
def label_as_fyi(email_id: str) -> dict:
    """
    Mark email as FYI (informational, no response needed).

    Use for: newsletters, notifications, CC'd emails, automated reports.
    """
    return _apply_label(email_id, "fyi")


@mcp.tool()
def label_as_respond(email_id: str) -> dict:
    """
    Mark email as needing a response from the user.

    Use for: direct questions, requests requiring decisions, important contacts.
    """
    return _apply_label(email_id, "respond")


@mcp.tool()
def label_as_draft(email_id: str) -> dict:
    """
    Mark email for auto-draft generation.

    Use for: routine requests, meeting confirmations, standard follow-ups.
    """
    return _apply_label(email_id, "draft")


@mcp.tool()
def label_as_archive(email_id: str) -> dict:
    """
    Mark email for archiving (can be bulk archived).

    Use for: marketing emails, expired promotions, already-handled items.
    """
    return _apply_label(email_id, "archive")


@mcp.tool()
def label_as_needs_review(email_id: str) -> dict:
    """
    Mark email as needing manual review (uncertain classification).

    Use for: new contacts, complex threads, ambiguous requests.
    """
    return _apply_label(email_id, "needs_review")


@mcp.tool()
def apply_label(email_id: str, label: str) -> dict:
    """
    Apply a classification label to an email (generic version).

    Prefer using the specific tools: label_as_fyi, label_as_respond,
    label_as_draft, label_as_archive, label_as_needs_review.

    Args:
        email_id: The Gmail message ID
        label: The classification (fyi, respond, draft, archive, needs_review)
    """
    label_key = normalize_label(label)
    if not label_key:
        raise ValueError(f"Invalid label: {label}. Valid: {VALID_KEYS} or {GMAIL_NAMES}")
    return _apply_label(email_id, label_key)


@mcp.tool()
def remove_label(email_id: str, label: str) -> dict:
    """
    Remove a label from an email.

    Args:
        email_id: The Gmail message ID
        label: The label to remove (internal key or Gmail name)

    Returns:
        Status of the operation
    """
    label_key = normalize_label(label)
    if not label_key:
        raise ValueError(f"Invalid label: {label}. Valid: {VALID_KEYS} or {GMAIL_NAMES}")

    gmail = get_gmail_client()
    gmail.remove_label(email_id, label_key)

    return {"status": "removed", "email_id": email_id, "label": label}


@mcp.tool()
def create_draft(thread_id: str, body: str, to: str, subject: str = "Re: ") -> dict:
    """
    Create a Gmail draft in a thread.

    Args:
        thread_id: The Gmail thread ID to reply to
        body: The draft email body
        to: The recipient email address
        subject: The email subject (default: "Re: ")

    Returns:
        Draft ID and status
    """
    gmail = get_gmail_client()
    draft_id = gmail.create_draft(thread_id=thread_id, body=body, to=to, subject=subject)

    return {"status": "created", "draft_id": draft_id, "thread_id": thread_id}


@mcp.tool()
def list_drafts(limit: int = 20) -> list[dict]:
    """
    List existing Gmail drafts.

    Args:
        limit: Maximum number of drafts to return

    Returns:
        List of draft summaries
    """
    gmail = get_gmail_client()
    drafts = gmail.list_drafts(max_results=limit)

    return [
        {
            "id": d.get("id"),
            "message": d.get("message", {}),
        }
        for d in drafts
    ]


@mcp.tool()
def list_sent_emails(to_address: str, limit: int = 5) -> list[dict]:
    """
    List sent emails to a specific address (for style sampling).

    Args:
        to_address: The recipient email address
        limit: Maximum number of emails to return

    Returns:
        List of sent email summaries with body content
    """
    gmail = get_gmail_client()
    emails = gmail.list_sent_emails(to_address=to_address, max_results=limit)

    return [
        {
            "id": e.id,
            "subject": e.subject,
            "body": e.body,
            "timestamp": e.timestamp,
        }
        for e in emails
    ]


@mcp.tool()
def list_gmail_labels() -> dict:
    """
    List all Gmail labels (for debugging label issues).

    Returns:
        Dict with user labels and their IDs
    """
    gmail = get_gmail_client()
    existing = gmail._get_existing_labels()

    # Separate user labels from system labels
    user_labels = {
        k: v for k, v in existing.items()
        if not v.startswith("CATEGORY_") and not v.isupper()
    }
    system_labels = {
        k: v for k, v in existing.items()
        if v.startswith("CATEGORY_") or v.isupper()
    }

    return {
        "user_labels": user_labels,
        "system_labels": list(system_labels.keys()),
        "configured_labels": gmail.LABELS,
        "cached_label_ids": gmail._label_ids,
    }


# =============================================================================
# ENTRY POINT
# =============================================================================


def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Gmail MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    args = parser.parse_args()

    # Log startup info
    print(f"[gmail-mcp] Using app name: {APP_NAME}", file=sys.stderr)
    print(f"[gmail-mcp] Labels: {VALID_KEYS}", file=sys.stderr)

    if args.transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
