"""Calendar MCP Server - Google Calendar operations via Model Context Protocol."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build

from shared.auth import GoogleAuth, CALENDAR_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import CalendarClient

# Initialize the MCP server
mcp = FastMCP("calendar")

# App name can be overridden via environment
APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")

# Cached instances
_paths: Optional[MCPPaths] = None
_calendar_client: Optional[CalendarClient] = None


def get_paths() -> MCPPaths:
    """Get or create paths instance."""
    global _paths
    if _paths is None:
        _paths = MCPPaths(APP_NAME)
        ensure_data_dirs(_paths.data_dir)
    return _paths


def get_calendar_client() -> CalendarClient:
    """Get or create authenticated Calendar client."""
    global _calendar_client

    if _calendar_client is not None:
        return _calendar_client

    paths = get_paths()

    if not paths.calendar_token.exists():
        raise RuntimeError(
            f"Calendar not authenticated. Token not found at: {paths.calendar_token}\n"
            "Run: python -m calendar.auth"
        )

    auth = GoogleAuth(
        credentials_path=paths.calendar_credentials,
        token_path=paths.calendar_token,
        scopes=CALENDAR_SCOPES,
    )

    creds = auth.get_credentials()
    service = build("calendar", "v3", credentials=creds)
    client = CalendarClient(service=service)

    _calendar_client = client
    return _calendar_client


# =============================================================================
# CALENDAR READ OPERATIONS (4 tools)
# =============================================================================


@mcp.tool()
def list_calendars() -> list[dict]:
    """
    List all calendars the user has access to.

    Returns:
        List of calendars with id, summary (name), description, time_zone, and primary flag.
        The primary calendar is marked with primary=True.
    """
    client = get_calendar_client()
    calendars = client.list_calendars()

    return [
        {
            "id": cal.id,
            "summary": cal.summary,
            "description": cal.description,
            "time_zone": cal.time_zone,
            "primary": cal.primary,
        }
        for cal in calendars
    ]


@mcp.tool()
def list_events(
    calendar_id: str = "primary",
    days_ahead: int = 7,
    limit: int = 50,
) -> list[dict]:
    """
    List upcoming events from a calendar.

    Args:
        calendar_id: Calendar ID or "primary" for the user's main calendar
        days_ahead: Number of days to look ahead (default 7)
        limit: Maximum number of events to return (default 50)

    Returns:
        List of events with id, summary (title), start, end, location, attendees, status.
    """
    client = get_calendar_client()

    time_min = datetime.now(timezone.utc)
    time_max = time_min + timedelta(days=days_ahead)

    events = client.list_events(
        calendar_id=calendar_id,
        time_min=time_min,
        time_max=time_max,
        max_results=limit,
    )

    return [
        {
            "id": event.id,
            "summary": event.summary,
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "location": event.location,
            "attendees": event.attendees,
            "status": event.status,
            "html_link": event.html_link,
        }
        for event in events
    ]


@mcp.tool()
def get_event(event_id: str, calendar_id: str = "primary") -> dict:
    """
    Get details of a specific event.

    Args:
        event_id: The event ID
        calendar_id: Calendar ID or "primary"

    Returns:
        Event details with id, summary, start, end, description, location, attendees, status.
    """
    client = get_calendar_client()
    event = client.get_event(event_id=event_id, calendar_id=calendar_id)

    return {
        "id": event.id,
        "summary": event.summary,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "description": event.description,
        "location": event.location,
        "attendees": event.attendees,
        "status": event.status,
        "html_link": event.html_link,
    }


@mcp.tool()
def find_free_slots(
    calendar_ids: str = "primary",
    days_ahead: int = 7,
    duration_minutes: int = 30,
    working_hours_start: int = 9,
    working_hours_end: int = 17,
) -> list[dict]:
    """
    Find available meeting slots across one or more calendars.

    Queries the FreeBusy API to find times when all specified calendars are free.
    Only returns slots during working hours on weekdays (Mon-Fri).

    Args:
        calendar_ids: Comma-separated calendar IDs (e.g., "primary" or "primary,work@example.com")
        days_ahead: Number of days to search (default 7)
        duration_minutes: Minimum slot duration in minutes (default 30)
        working_hours_start: Start of working day in 24h format (default 9 = 9am)
        working_hours_end: End of working day in 24h format (default 17 = 5pm)

    Returns:
        List of free slots with start, end, and duration_minutes.
        Slots are within working hours and at least duration_minutes long.
    """
    client = get_calendar_client()

    # Parse comma-separated calendar IDs
    cal_ids = [cid.strip() for cid in calendar_ids.split(",")]

    time_min = datetime.now(timezone.utc)
    time_max = time_min + timedelta(days=days_ahead)

    slots = client.find_free_slots(
        calendar_ids=cal_ids,
        time_min=time_min,
        time_max=time_max,
        duration_minutes=duration_minutes,
        working_hours=(working_hours_start, working_hours_end),
    )

    return [
        {
            "start": slot.start.isoformat(),
            "end": slot.end.isoformat(),
            "duration_minutes": slot.duration_minutes,
        }
        for slot in slots
    ]


# =============================================================================
# CALENDAR WRITE OPERATIONS (3 tools)
# =============================================================================


@mcp.tool()
def create_event(
    summary: str,
    start_time: str,
    duration_minutes: int = 60,
    calendar_id: str = "primary",
    description: str = "",
    location: str = "",
    attendees: str = "",
    send_invites: bool = True,
) -> dict:
    """
    Create a new calendar event.

    Args:
        summary: Event title (required)
        start_time: Start time in ISO format, e.g., "2024-01-15T14:00:00" (required)
        duration_minutes: Event duration in minutes (default 60)
        calendar_id: Calendar to create event in (default "primary")
        description: Event description (optional)
        location: Event location (optional)
        attendees: Comma-separated attendee email addresses (optional)
        send_invites: Whether to send email invitations (default True)

    Returns:
        Created event with id, summary, start, end, and html_link.
    """
    client = get_calendar_client()

    # Parse start time
    start = datetime.fromisoformat(start_time)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    # Calculate end time
    end = start + timedelta(minutes=duration_minutes)

    # Parse attendees
    attendee_list = None
    if attendees:
        attendee_list = [email.strip() for email in attendees.split(",") if email.strip()]

    event = client.create_event(
        summary=summary,
        start=start,
        end=end,
        calendar_id=calendar_id,
        description=description if description else None,
        location=location if location else None,
        attendees=attendee_list,
        send_notifications=send_invites,
    )

    return {
        "id": event.id,
        "summary": event.summary,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "html_link": event.html_link,
        "attendees": event.attendees,
    }


@mcp.tool()
def update_event(
    event_id: str,
    calendar_id: str = "primary",
    summary: str = "",
    start_time: str = "",
    duration_minutes: int = 0,
    description: str = "",
    location: str = "",
) -> dict:
    """
    Update an existing calendar event.

    Only non-empty fields are updated. Leave fields empty to keep current values.

    Args:
        event_id: The event ID to update (required)
        calendar_id: Calendar ID (default "primary")
        summary: New event title (optional)
        start_time: New start time in ISO format (optional)
        duration_minutes: New duration in minutes (only used if start_time is provided)
        description: New description (optional)
        location: New location (optional)

    Returns:
        Updated event with id, summary, start, end, and html_link.
    """
    client = get_calendar_client()

    # Parse optional fields
    start = None
    end = None
    if start_time:
        start = datetime.fromisoformat(start_time)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if duration_minutes > 0:
            end = start + timedelta(minutes=duration_minutes)

    event = client.update_event(
        event_id=event_id,
        calendar_id=calendar_id,
        summary=summary if summary else None,
        start=start,
        end=end,
        description=description if description else None,
        location=location if location else None,
    )

    return {
        "id": event.id,
        "summary": event.summary,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "html_link": event.html_link,
    }


@mcp.tool()
def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    send_notifications: bool = True,
) -> dict:
    """
    Delete a calendar event.

    Args:
        event_id: The event ID to delete (required)
        calendar_id: Calendar ID (default "primary")
        send_notifications: Whether to send cancellation emails to attendees (default True)

    Returns:
        Confirmation with deleted event_id and success status.
    """
    client = get_calendar_client()

    success = client.delete_event(
        event_id=event_id,
        calendar_id=calendar_id,
        send_notifications=send_notifications,
    )

    return {
        "event_id": event_id,
        "deleted": success,
    }
