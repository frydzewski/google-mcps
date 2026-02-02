# Google MCPs

MCP (Model Context Protocol) servers for Google APIs, designed for use with Claude Code.

## Available MCPs

| MCP | Tools | Description |
|-----|-------|-------------|
| **gmail** | 12 | Read emails, apply labels, create drafts (never sends) |
| **sheets** | 5 | Read spreadsheet data (read-only) |

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
