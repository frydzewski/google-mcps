"""Gmail API client wrapper."""
import base64
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("gmail_mcp.client")

# Map: internal key -> Gmail label name
LABELS = {
    "fyi": "FYI",
    "respond": "Respond",
    "draft": "Write-Reply",
    "archive": "To-Archive",
    "needs_review": "Needs-Review",
}

# Reverse map: Gmail label name -> internal key
LABEL_KEYS = {v: k for k, v in LABELS.items()}

# All valid keys
VALID_KEYS = list(LABELS.keys())

# All Gmail label names
GMAIL_NAMES = list(LABELS.values())


def normalize_label(label: str) -> str | None:
    """
    Convert any label format to the internal key.

    Accepts:
      - Internal key: "archive" -> "archive"
      - Gmail name: "To-Archive" -> "archive"
      - Variations: "needs-review", "NEEDS_REVIEW" -> "needs_review"

    Returns None if not recognized.
    """
    # Already a valid key?
    if label in LABELS:
        return label

    # Is it a Gmail label name?
    if label in LABEL_KEYS:
        return LABEL_KEYS[label]

    # Try case-insensitive match on keys
    label_lower = label.lower().replace("-", "_")
    if label_lower in LABELS:
        return label_lower

    # Try case-insensitive match on Gmail names
    for gmail_name, key in LABEL_KEYS.items():
        if gmail_name.lower() == label.lower():
            return key

    return None


def get_gmail_name(key: str) -> str | None:
    """Get the Gmail label name for an internal key."""
    return LABELS.get(key)


def get_exclude_query() -> str:
    """Get Gmail query string to exclude all labeled emails."""
    parts = []
    for name in GMAIL_NAMES:
        if "-" in name:
            parts.append(f'-label:"{name}"')
        else:
            parts.append(f"-label:{name}")
    return " ".join(parts)


@dataclass
class Email:
    """Represents a Gmail message."""
    id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str
    body: str
    labels: list[str]
    timestamp: Optional[str] = None


class GmailClient:
    """Wrapper for Gmail API operations."""

    # Expose label constants for external use
    LABELS = LABELS

    def __init__(self, service):
        """
        Initialize with a Gmail API service instance.

        Args:
            service: A googleapiclient.discovery.Resource for Gmail API v1
        """
        self.service = service
        self._label_ids: dict[str, str] = {}

    def fetch_unprocessed_emails(
        self,
        max_results: int = 50,
        newer_than_days: Optional[int] = None,
        domain: Optional[str] = None,
        sender: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> list[Email]:
        """Fetch emails that don't have any classification labels.

        Args:
            max_results: Maximum number of emails to fetch
            newer_than_days: Only fetch emails from the last N days (None = no limit)
            domain: Filter to emails from a specific domain (e.g., "validic.com")
            sender: Filter to emails from a specific sender email address
            after: Only emails after this date (YYYY-MM-DD format)
            before: Only emails before this date (YYYY-MM-DD format)
        """
        # Build query to exclude already-classified emails
        query = get_exclude_query()

        if newer_than_days is not None:
            query += f" newer_than:{newer_than_days}d"

        if domain is not None:
            query += f" from:@{domain}"

        if sender is not None:
            query += f" from:{sender}"

        if after is not None:
            # Gmail uses YYYY/MM/DD format
            query += f" after:{after.replace('-', '/')}"

        if before is not None:
            query += f" before:{before.replace('-', '/')}"

        try:
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["INBOX"],
                    q=query,
                    maxResults=max_results,
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to list messages: {e}")
            return []

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            try:
                full_msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                email = self._parse_message(full_msg)
                emails.append(email)
            except Exception as e:
                logger.warning(f"Failed to fetch message {msg['id']}: {e}")

        return emails

    def get_email(self, email_id: str) -> Optional[Email]:
        """Fetch a single email by ID."""
        try:
            full_msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )
            return self._parse_message(full_msg)
        except Exception as e:
            logger.warning(f"Failed to fetch email {email_id}: {e}")
            return None

    def apply_label(self, message_id: str, label_key: str) -> None:
        """Apply a classification label to a message.

        Removes any existing classification labels first to prevent duplicates.
        Always preserves the INBOX label.
        """
        label_id = self._get_or_create_label_id(label_key)
        if not label_id:
            raise ValueError(f"Unknown label key: {label_key}")

        # Get all classification label IDs to remove (except the one we're adding)
        all_classification_ids = self._get_all_classification_label_ids()
        labels_to_remove = [lid for lid in all_classification_ids if lid != label_id]

        # Single API call: remove old labels and add new one
        body = {"addLabelIds": [label_id]}
        if labels_to_remove:
            body["removeLabelIds"] = labels_to_remove

        self.service.users().messages().modify(
            userId="me",
            id=message_id,
            body=body,
        ).execute()
        logger.debug(f"Applied label {label_key} to message {message_id}")

    def remove_label(self, message_id: str, label_key: str) -> None:
        """Remove a classification label from a message."""
        label_id = self._get_or_create_label_id(label_key)
        if not label_id:
            raise ValueError(f"Unknown label key: {label_key}")

        self.service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": [label_id]},
        ).execute()
        logger.debug(f"Removed label {label_key} from message {message_id}")

    def create_draft(
        self,
        thread_id: str,
        body: str,
        to: str,
        subject: str,
        in_reply_to: Optional[str] = None,
    ) -> str:
        """Create a draft reply in a thread."""
        import email.mime.text

        message = email.mime.text.MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        draft_body = {
            "message": {
                "raw": raw,
                "threadId": thread_id,
            }
        }

        result = (
            self.service.users()
            .drafts()
            .create(userId="me", body=draft_body)
            .execute()
        )
        logger.info(f"Created draft {result['id']} in thread {thread_id}")
        return result["id"]

    def list_drafts(self, max_results: int = 20) -> list[dict]:
        """List Gmail drafts.

        Returns:
            List of draft objects with id and message summary
        """
        try:
            results = (
                self.service.users()
                .drafts()
                .list(userId="me", maxResults=max_results)
                .execute()
            )
            return results.get("drafts", [])
        except Exception as e:
            logger.warning(f"Failed to list drafts: {e}")
            return []

    def ensure_labels_exist(self) -> None:
        """Create classification labels if they don't exist."""
        existing = self._get_existing_labels()

        for key, name in self.LABELS.items():
            label_id = self._find_existing_label(name, existing)

            if label_id:
                self._label_ids[key] = label_id
            else:
                # Try to create it
                created_id = self._create_label(name, key)
                if created_id:
                    logger.info(f"Created label: {name}")
                else:
                    logger.warning(f"Could not create label: {name}")

    def list_sent_emails(self, to_address: str, max_results: int = 5) -> list[Email]:
        """Fetch sent emails to a specific address (for style sampling).

        Args:
            to_address: Recipient email address
            max_results: Maximum number of emails to return

        Returns:
            List of sent emails to this address
        """
        query = f"to:{to_address}"

        try:
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["SENT"],
                    q=query,
                    maxResults=max_results,
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to search sent emails: {e}")
            return []

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            try:
                full_msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                email = self._parse_message(full_msg)
                emails.append(email)
            except Exception as e:
                logger.warning(f"Failed to fetch message {msg['id']}: {e}")

        return emails

    def _parse_message(self, msg: dict) -> Email:
        """Parse Gmail API message into Email dataclass."""
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

        body = self._extract_body(msg["payload"])

        return Email(
            id=msg["id"],
            thread_id=msg.get("threadId", msg["id"]),
            sender=headers.get("From", ""),
            subject=headers.get("Subject", ""),
            snippet=msg.get("snippet", ""),
            body=body,
            labels=msg.get("labelIds", []),
            timestamp=headers.get("Date"),
        )

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from message payload (recursive)."""
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if part["body"].get("data"):
                        return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                elif "parts" in part:
                    # Nested multipart
                    body = self._extract_body(part)
                    if body:
                        return body

        return ""

    def _get_or_create_label_id(self, label_key: str) -> str | None:
        """Get label ID from cache, or find/create it."""
        # Check cache first
        if label_key in self._label_ids:
            return self._label_ids[label_key]

        # Get expected label name
        label_name = self.LABELS.get(label_key)
        if not label_name:
            return None

        # Look in existing labels
        existing = self._get_existing_labels()
        label_id = self._find_existing_label(label_name, existing)

        if label_id:
            self._label_ids[label_key] = label_id
            return label_id

        # Not found - create it
        return self._create_label(label_name, label_key)

    def _get_label_id(self, label_name: str) -> str | None:
        """Get label ID by Gmail label name."""
        existing = self._get_existing_labels()
        return existing.get(label_name)

    def _get_existing_labels(self) -> dict[str, str]:
        """Get map of label name -> label ID."""
        results = self.service.users().labels().list(userId="me").execute()
        return {label["name"]: label["id"] for label in results.get("labels", [])}

    def _find_existing_label(self, target_name: str, existing: dict[str, str]) -> str | None:
        """Find an existing label that matches target_name (exact or normalized).

        Gmail treats "Needs-Review" and "Needs Review" as the same label,
        so we defer to whatever already exists in the user's Gmail.
        """
        # Exact match first
        if target_name in existing:
            return existing[target_name]

        # Normalized match (spaces/hyphens/underscores treated as equivalent)
        target_normalized = self._normalize_for_match(target_name)
        for existing_name, existing_id in existing.items():
            if self._normalize_for_match(existing_name) == target_normalized:
                logger.info(f"Using existing label '{existing_name}' for '{target_name}'")
                return existing_id

        return None

    def _normalize_for_match(self, name: str) -> str:
        """Normalize label name for matching (Gmail treats spaces/hyphens as equivalent)."""
        return name.lower().replace("-", " ").replace("_", " ")

    def _create_label(self, name: str, key: str) -> str | None:
        """Create a Gmail label and return its ID."""
        from googleapiclient.errors import HttpError

        label_body = {
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        try:
            result = (
                self.service.users().labels().create(userId="me", body=label_body).execute()
            )
            label_id = result["id"]
        except HttpError as e:
            if e.resp.status == 409:
                # Label already exists or conflicts - find its ID using normalized matching
                existing = self._get_existing_labels()
                logger.info(f"Label {name} got 409, searching existing labels")

                label_id = self._find_existing_label(name, existing)
                if not label_id:
                    logger.error(f"Label {name} conflicts but no match found in: {list(existing.keys())}")
                    return None
            else:
                raise

        # Cache the ID
        self._label_ids[key] = label_id

        return label_id

    def _get_all_classification_label_ids(self) -> list[str]:
        """Get all classification label IDs (for removing prior labels)."""
        label_ids = []
        for key in self.LABELS.keys():
            label_id = self._get_or_create_label_id(key)
            if label_id:
                label_ids.append(label_id)
        return label_ids
