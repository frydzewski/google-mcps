# Google MCPs

> **⚠️ DEPRECATED**: This repository has been moved to [workspace-tools](https://github.com/frydzewski/workspace-tools).
>
> The code now lives at `packages/mcps/` in the monorepo. Please use the new location for all future work.

---

MCP (Model Context Protocol) servers for Google APIs, designed for use with Claude Code.

## Available MCPs

| MCP | Tools | Description |
|-----|-------|-------------|
| **gmail** | 12 | Read emails, apply labels, create drafts (never sends) |
| **sheets** | 5 | Read spreadsheet data (read-only) |
| **calendar** | 7 | Read calendars, find free time, create/update/delete events |
| **slides** | 7 | Read presentations, extract text, create slides and text boxes |
| **forms** | 6 | Read form structure and analyze responses (read-only) |

## Installation

```bash
pip install -e .
```

## Authentication

Both MCPs use Google OAuth. Download credentials from Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API and/or Sheets API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `gmail_credentials.json`
6. Place in `~/.letter-rip/credentials/`

Run auth setup:
```bash
# Gmail
python -m gmail.auth

# Sheets
python -m sheets.auth --test YOUR_SPREADSHEET_ID

# Calendar
python -m calendar.auth --test

# Slides
python -m slides.auth --test YOUR_PRESENTATION_ID

# Forms
python -m forms.auth --test YOUR_FORM_ID
```

## Gmail MCP

Tools for email operations:

| Tool | Description |
|------|-------------|
| `list_emails` | Fetch emails with optional filters |
| `get_email` | Get full email content by ID |
| `label_as_fyi` | Mark as FYI (informational) |
| `label_as_respond` | Mark as needing response |
| `label_as_draft` | Mark for auto-draft generation |
| `label_as_archive` | Mark for archiving |
| `label_as_needs_review` | Mark as needing review |
| `apply_label` | Apply label (generic) |
| `remove_label` | Remove a label |
| `create_draft` | Create a Gmail draft |
| `list_drafts` | List existing drafts |
| `list_sent_emails` | List sent emails to address |

## Sheets MCP

Read-only tools for spreadsheet data:

| Tool | Description |
|------|-------------|
| `get_spreadsheet_info` | Get spreadsheet metadata |
| `list_sheets` | List all sheets (tabs) |
| `get_headers` | Get column headers |
| `read_sheet` | Read rows as dictionaries |
| `find_rows` | Find rows matching a value |

## Calendar MCP

Tools for calendar and scheduling:

| Tool | Description |
|------|-------------|
| `list_calendars` | List all accessible calendars |
| `list_events` | List upcoming events |
| `get_event` | Get event details |
| `find_free_slots` | Find available meeting times |
| `create_event` | Create a new event |
| `update_event` | Update an existing event |
| `delete_event` | Delete an event |

See [calendar/README.md](calendar/README.md) for details.

## Slides MCP

Tools for presentations:

| Tool | Description |
|------|-------------|
| `get_presentation` | Get presentation metadata |
| `list_slides` | List all slides with summaries |
| `get_slide_text` | Get text from a slide (or all) |
| `get_presentation_text` | Get all text by slide |
| `create_presentation` | Create a new presentation |
| `create_slide` | Add a slide with layout |
| `add_text_to_slide` | Add a text box to a slide |

See [slides/README.md](slides/README.md) for details.

## Forms MCP

Read-only tools for form structure and responses:

| Tool | Description |
|------|-------------|
| `get_form` | Get form metadata and all questions |
| `list_questions` | List questions with types and options |
| `get_responses` | Get all responses with answers |
| `get_responses_table` | Get responses as table format |
| `get_response` | Get a specific response |
| `get_response_summary` | Get statistics and distributions |

See [forms/README.md](forms/README.md) for details.

## Usage with Claude Code

Add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["-m", "gmail.server"],
      "cwd": "/path/to/google-mcps",
      "env": {
        "GOOGLE_MCP_APP_NAME": "my-app"
      }
    },
    "sheets": {
      "command": "python",
      "args": ["-m", "sheets.server"],
      "cwd": "/path/to/google-mcps",
      "env": {
        "GOOGLE_MCP_APP_NAME": "my-app"
      }
    }
  }
}
```

The `GOOGLE_MCP_APP_NAME` environment variable sets the data directory
(defaults to `letter-rip`, creating `~/.letter-rip/`).
