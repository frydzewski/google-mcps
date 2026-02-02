"""Data models for Google Calendar API."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class CalendarInfo:
    """Information about a calendar."""
    id: str
    summary: str  # Calendar name
    description: Optional[str]
    time_zone: str
    primary: bool = False

    @classmethod
    def from_api_response(cls, data: dict) -> "CalendarInfo":
        """Parse from Google Calendar API response."""
        return cls(
            id=data.get("id", ""),
            summary=data.get("summary", ""),
            description=data.get("description"),
            time_zone=data.get("timeZone", "UTC"),
            primary=data.get("primary", False),
        )


@dataclass
class Event:
    """A calendar event."""
    id: str
    summary: str  # Event title
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: list[str] = field(default_factory=list)
    status: str = "confirmed"  # confirmed, tentative, cancelled
    html_link: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Event":
        """Parse from Google Calendar API response."""
        # Handle both dateTime (with time) and date (all-day) events
        start_data = data.get("start", {})
        end_data = data.get("end", {})

        start = cls._parse_datetime(start_data)
        end = cls._parse_datetime(end_data)

        # Extract attendee emails
        attendees = []
        for attendee in data.get("attendees", []):
            email = attendee.get("email")
            if email:
                attendees.append(email)

        return cls(
            id=data.get("id", ""),
            summary=data.get("summary", "(No title)"),
            start=start,
            end=end,
            description=data.get("description"),
            location=data.get("location"),
            attendees=attendees,
            status=data.get("status", "confirmed"),
            html_link=data.get("htmlLink"),
        )

    @staticmethod
    def _parse_datetime(dt_data: dict) -> datetime:
        """Parse datetime from API response (handles both dateTime and date)."""
        if "dateTime" in dt_data:
            # Full datetime with timezone
            dt_str = dt_data["dateTime"]
            # Handle ISO format with timezone
            if dt_str.endswith("Z"):
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return datetime.fromisoformat(dt_str)
        elif "date" in dt_data:
            # All-day event (date only)
            return datetime.fromisoformat(dt_data["date"])
        else:
            return datetime.now()


@dataclass
class BusyBlock:
    """A block of busy time from FreeBusy API."""
    start: datetime
    end: datetime

    @classmethod
    def from_api_response(cls, data: dict) -> "BusyBlock":
        """Parse from FreeBusy API response."""
        start_str = data.get("start", "")
        end_str = data.get("end", "")

        # Handle Z suffix for UTC
        if start_str.endswith("Z"):
            start_str = start_str.replace("Z", "+00:00")
        if end_str.endswith("Z"):
            end_str = end_str.replace("Z", "+00:00")

        return cls(
            start=datetime.fromisoformat(start_str) if start_str else datetime.now(),
            end=datetime.fromisoformat(end_str) if end_str else datetime.now(),
        )


@dataclass
class FreeSlot:
    """An available time slot."""
    start: datetime
    end: datetime
    duration_minutes: int

    @classmethod
    def create(cls, start: datetime, end: datetime) -> "FreeSlot":
        """Create a FreeSlot with calculated duration."""
        duration = int((end - start).total_seconds() / 60)
        return cls(start=start, end=end, duration_minutes=duration)
