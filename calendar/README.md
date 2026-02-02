# Calendar MCP

Google Calendar MCP server for Claude Code. Read calendars, find free time slots, and manage events.

## Features

- **List calendars** - See all accessible calendars
- **View events** - List upcoming events or get specific event details
- **Find free time** - Query availability across multiple calendars
- **Create events** - Schedule meetings with attendees
- **Update events** - Modify existing events
- **Delete events** - Remove events with optional cancellation notifications

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud project with Calendar API enabled
- OAuth credentials (can share with Gmail MCP)

### Authentication

1. Ensure OAuth credentials are in place:
   ```
   ~/.letter-rip/credentials/gmail_credentials.json
   ```

2. Run the auth setup:
   ```bash
   cd ~/claude/google-mcps
   python -m calendar.auth
   ```

3. Test the connection:
   ```bash
   python -m calendar.auth --test
   ```

## Tools

### Read Tools (4)

| Tool | Description |
|------|-------------|
| `list_calendars()` | List all accessible calendars |
| `list_events(calendar_id, days_ahead, limit)` | List upcoming events |
| `get_event(event_id, calendar_id)` | Get specific event details |
| `find_free_slots(calendar_ids, days_ahead, duration_minutes, working_hours_start, working_hours_end)` | Find available meeting times |

### Write Tools (3)

| Tool | Description |
|------|-------------|
| `create_event(summary, start_time, duration_minutes, ...)` | Create a new event |
| `update_event(event_id, summary, start_time, ...)` | Update an existing event |
| `delete_event(event_id, calendar_id, send_notifications)` | Delete an event |

## Usage Examples

### Finding available time

```
"Find 30-minute slots next week for a meeting"
"When am I free tomorrow between 10am and 4pm?"
"Find a 1-hour slot across my work and personal calendars"
```

### Creating events

```
"Schedule a meeting with alice@example.com tomorrow at 2pm for 1 hour"
"Create a 30-minute sync at 3pm on Friday called 'Weekly Sync'"
"Book a room for the team meeting next Monday at 10am"
```

### Viewing calendar

```
"What's on my calendar for today?"
"Show me my meetings for this week"
"List all my calendars"
```

### Managing events

```
"Move my 3pm meeting to 4pm"
"Cancel the team sync meeting"
"Update the project kickoff description"
```

## Configuration

Add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python3",
      "args": ["-m", "calendar"],
      "cwd": "/path/to/google-mcps",
      "env": {
        "PYTHONPATH": "/path/to/google-mcps",
        "GOOGLE_MCP_APP_NAME": "your-app-name"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_MCP_APP_NAME` | `letter-rip` | App name for data directory (`~/.{app-name}/`) |

## API Scopes

This MCP uses two Google Calendar API scopes:

- `calendar.readonly` - Read calendar and event data
- `calendar.events` - Create, update, and delete events

## Working Hours

The `find_free_slots` tool respects working hours:

- Default: 9am - 5pm
- Weekdays only (Mon-Fri)
- Configurable via `working_hours_start` and `working_hours_end` parameters

## Related MCPs

- **Gmail MCP** - Email operations
- **Sheets MCP** - Spreadsheet data
