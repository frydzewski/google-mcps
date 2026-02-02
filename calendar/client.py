"""Google Calendar API client wrapper."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from .models import CalendarInfo, Event, BusyBlock, FreeSlot

logger = logging.getLogger("google_mcps.calendar")


class CalendarClient:
    """Wrapper for Google Calendar API operations."""

    def __init__(self, service):
        """
        Initialize the Calendar client.

        Args:
            service: Google Calendar API service object
        """
        self.service = service

    def list_calendars(self) -> list[CalendarInfo]:
        """
        List all calendars the user has access to.

        Returns:
            List of CalendarInfo objects
        """
        try:
            result = self.service.calendarList().list().execute()
        except Exception as e:
            logger.error(f"Failed to list calendars: {e}")
            raise

        calendars = []
        for item in result.get("items", []):
            calendars.append(CalendarInfo.from_api_response(item))

        return calendars

    def get_calendar(self, calendar_id: str = "primary") -> CalendarInfo:
        """
        Get info about a specific calendar.

        Args:
            calendar_id: Calendar ID or "primary" for the user's primary calendar

        Returns:
            CalendarInfo object
        """
        try:
            result = self.service.calendarList().get(calendarId=calendar_id).execute()
        except Exception as e:
            logger.error(f"Failed to get calendar {calendar_id}: {e}")
            raise

        return CalendarInfo.from_api_response(result)

    def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
    ) -> list[Event]:
        """
        List events in a time range.

        Args:
            calendar_id: Calendar ID or "primary"
            time_min: Start of time range (defaults to now)
            time_max: End of time range (defaults to 7 days from now)
            max_results: Maximum number of events to return

        Returns:
            List of Event objects, ordered by start time
        """
        # Default time range: now to 7 days from now
        if time_min is None:
            time_min = datetime.now(timezone.utc)
        if time_max is None:
            time_max = time_min + timedelta(days=7)

        # Convert to RFC3339 format
        time_min_str = self._to_rfc3339(time_min)
        time_max_str = self._to_rfc3339(time_max)

        try:
            result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min_str,
                    timeMax=time_max_str,
                    maxResults=max_results,
                    singleEvents=True,  # Expand recurring events
                    orderBy="startTime",
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            raise

        events = []
        for item in result.get("items", []):
            events.append(Event.from_api_response(item))

        return events

    def get_event(self, event_id: str, calendar_id: str = "primary") -> Event:
        """
        Get a specific event by ID.

        Args:
            event_id: The event ID
            calendar_id: Calendar ID or "primary"

        Returns:
            Event object
        """
        try:
            result = (
                self.service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            raise

        return Event.from_api_response(result)

    @staticmethod
    def _to_rfc3339(dt: datetime) -> str:
        """
        Convert datetime to RFC3339 format for Google API.

        Args:
            dt: datetime object (timezone-aware or naive)

        Returns:
            RFC3339 formatted string
        """
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
