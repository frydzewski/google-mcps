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

    def query_free_busy(
        self,
        calendar_ids: list[str],
        time_min: datetime,
        time_max: datetime,
    ) -> dict[str, list[BusyBlock]]:
        """
        Query busy times for one or more calendars.

        Args:
            calendar_ids: List of calendar IDs to check
            time_min: Start of time range
            time_max: End of time range

        Returns:
            Dict mapping calendar_id -> list of BusyBlock
        """
        body = {
            "timeMin": self._to_rfc3339(time_min),
            "timeMax": self._to_rfc3339(time_max),
            "items": [{"id": cal_id} for cal_id in calendar_ids],
        }

        try:
            result = self.service.freebusy().query(body=body).execute()
        except Exception as e:
            logger.error(f"Failed to query free/busy: {e}")
            raise

        busy_map: dict[str, list[BusyBlock]] = {}
        calendars = result.get("calendars", {})

        for cal_id in calendar_ids:
            cal_data = calendars.get(cal_id, {})
            busy_blocks = []
            for block in cal_data.get("busy", []):
                busy_blocks.append(BusyBlock.from_api_response(block))
            busy_map[cal_id] = busy_blocks

        return busy_map

    def find_free_slots(
        self,
        calendar_ids: list[str],
        time_min: datetime,
        time_max: datetime,
        duration_minutes: int = 30,
        working_hours: tuple[int, int] = (9, 17),
    ) -> list[FreeSlot]:
        """
        Find available time slots across calendars.

        Args:
            calendar_ids: List of calendar IDs to check
            time_min: Start of search range
            time_max: End of search range
            duration_minutes: Minimum slot duration (default 30)
            working_hours: Tuple of (start_hour, end_hour) in 24h format (default 9-17)

        Returns:
            List of FreeSlot objects representing available times
        """
        # 1. Query FreeBusy for all calendars
        busy_map = self.query_free_busy(calendar_ids, time_min, time_max)

        # 2. Merge busy blocks across all calendars
        all_busy: list[BusyBlock] = []
        for blocks in busy_map.values():
            all_busy.extend(blocks)
        merged_busy = self._merge_busy_blocks(all_busy)

        # 3. Find gaps in the busy times
        gaps = self._find_gaps(merged_busy, time_min, time_max)

        # 4. Filter to working hours and minimum duration
        free_slots = []
        for gap_start, gap_end in gaps:
            # Split gap into working hours segments across days
            working_slots = self._filter_to_working_hours(
                gap_start, gap_end, working_hours
            )
            for slot_start, slot_end in working_slots:
                duration = int((slot_end - slot_start).total_seconds() / 60)
                if duration >= duration_minutes:
                    free_slots.append(FreeSlot.create(slot_start, slot_end))

        return free_slots

    @staticmethod
    def _merge_busy_blocks(blocks: list[BusyBlock]) -> list[BusyBlock]:
        """Merge overlapping busy blocks into non-overlapping sorted list."""
        if not blocks:
            return []

        # Sort by start time
        sorted_blocks = sorted(blocks, key=lambda b: b.start)
        merged = [sorted_blocks[0]]

        for block in sorted_blocks[1:]:
            last = merged[-1]
            if block.start <= last.end:
                # Overlapping or adjacent - merge
                merged[-1] = BusyBlock(
                    start=last.start,
                    end=max(last.end, block.end)
                )
            else:
                merged.append(block)

        return merged

    @staticmethod
    def _find_gaps(
        busy_blocks: list[BusyBlock],
        time_min: datetime,
        time_max: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """Find gaps between busy blocks within the time range."""
        gaps = []
        current = time_min

        for block in busy_blocks:
            if block.start > current:
                gaps.append((current, block.start))
            current = max(current, block.end)

        if current < time_max:
            gaps.append((current, time_max))

        return gaps

    @staticmethod
    def _filter_to_working_hours(
        start: datetime,
        end: datetime,
        working_hours: tuple[int, int],
    ) -> list[tuple[datetime, datetime]]:
        """
        Split a time range into segments that fall within working hours.

        Handles multi-day ranges by returning a segment for each day.
        """
        work_start_hour, work_end_hour = working_hours
        slots = []

        current_day = start.date()
        end_day = end.date()

        while current_day <= end_day:
            # Working hours for this day
            day_work_start = datetime(
                current_day.year, current_day.month, current_day.day,
                work_start_hour, 0, 0,
                tzinfo=start.tzinfo or timezone.utc
            )
            day_work_end = datetime(
                current_day.year, current_day.month, current_day.day,
                work_end_hour, 0, 0,
                tzinfo=start.tzinfo or timezone.utc
            )

            # Clamp to the original range
            slot_start = max(start, day_work_start)
            slot_end = min(end, day_work_end)

            # Only add if valid range on a weekday
            if slot_start < slot_end and current_day.weekday() < 5:  # Mon-Fri
                slots.append((slot_start, slot_end))

            current_day += timedelta(days=1)

        return slots

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        send_notifications: bool = True,
    ) -> Event:
        """
        Create a new calendar event.

        Args:
            summary: Event title
            start: Start datetime (will be converted to RFC3339)
            end: End datetime
            calendar_id: Calendar to create event in
            description: Optional event description
            location: Optional location string
            attendees: Optional list of email addresses to invite
            send_notifications: Whether to send invite emails (default True)

        Returns:
            Created Event object with ID and htmlLink
        """
        event_body: dict = {
            "summary": summary,
            "start": {"dateTime": self._to_rfc3339(start)},
            "end": {"dateTime": self._to_rfc3339(end)},
        }

        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        try:
            result = (
                self.service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event_body,
                    sendNotifications=send_notifications,
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

        return Event.from_api_response(result)

    def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Event:
        """
        Update an existing calendar event.

        Only provided fields are updated; None fields are left unchanged.

        Args:
            event_id: The event ID to update
            calendar_id: Calendar ID or "primary"
            summary: New event title (optional)
            start: New start datetime (optional)
            end: New end datetime (optional)
            description: New description (optional)
            location: New location (optional)

        Returns:
            Updated Event object
        """
        # First, get the existing event
        try:
            existing = (
                self.service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to get event for update: {e}")
            raise

        # Update only provided fields
        if summary is not None:
            existing["summary"] = summary
        if start is not None:
            existing["start"] = {"dateTime": self._to_rfc3339(start)}
        if end is not None:
            existing["end"] = {"dateTime": self._to_rfc3339(end)}
        if description is not None:
            existing["description"] = description
        if location is not None:
            existing["location"] = location

        try:
            result = (
                self.service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=existing)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

        return Event.from_api_response(result)

    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        send_notifications: bool = True,
    ) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: The event ID to delete
            calendar_id: Calendar ID or "primary"
            send_notifications: Whether to send cancellation emails (default True)

        Returns:
            True if successful
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendNotifications=send_notifications,
            ).execute()
        except Exception as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

        return True

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
