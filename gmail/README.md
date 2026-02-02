# Gmail MCP

MCP server for Gmail operations. Read emails, apply classification labels, and create drafts (never sends automatically).

## Tools

### Reading
| Tool | Args | Description |
|------|------|-------------|
| `list_emails` | `labels?`, `days?`, `limit?` | Fetch emails with optional filters |
| `get_email` | `email_id` | Get full email content by ID |
| `list_sent_emails` | `to_address`, `limit?` | List sent emails to an address |
| `list_drafts` | `limit?` | List existing Gmail drafts |

### Labeling
| Tool | Args | Description |
|------|------|-------------|
| `label_as_fyi` | `email_id` | Mark as FYI (informational, no response needed) |
| `label_as_respond` | `email_id` | Mark as needing a response |
| `label_as_draft` | `email_id` | Mark for auto-draft generation |
| `label_as_archive` | `email_id` | Mark for archiving |
| `label_as_needs_review` | `email_id` | Mark as needing manual review |
| `apply_label` | `email_id`, `label` | Apply label (generic version) |
| `remove_label` | `email_id`, `label` | Remove a label |

### Actions
| Tool | Args | Description |
|------|------|-------------|
| `create_draft` | `thread_id`, `body`, `to`, `subject?` | Create a Gmail draft in a thread |

### Diagnostic
| Tool | Args | Description |
|------|------|-------------|
| `list_gmail_labels` | - | List all Gmail labels (for debugging) |

## Setup

### 1. Prerequisites

- Python 3.11+
- Google Cloud project with Gmail API enabled
- OAuth credentials (Desktop app type)

### 2. Credentials

Place `gmail_credentials.json` in your app's config directory:
```
~/.letter-rip/credentials/gmail_credentials.json
```

### 3. Authentication

Run the auth setup:
```bash
cd /path/to/google-mcps
python -m gmail.auth
```

This opens a browser for OAuth consent. Token is saved for future use.

### 4. Claude Code Configuration

Add to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python3",
      "args": ["-m", "gmail"],
      "cwd": "/path/to/google-mcps",
      "env": {
        "PYTHONPATH": "/path/to/google-mcps",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GOOGLE_MCP_APP_NAME": "letter-rip"
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_MCP_APP_NAME` | `letter-rip` | App name for config directory (`~/.{app_name}/`) |
| `PYTHONDONTWRITEBYTECODE` | - | Set to `1` to avoid bytecode caching issues |

## Label Definitions

| Key | Gmail Name | Use For |
|-----|------------|---------|
| `fyi` | FYI | Newsletters, notifications, CC'd emails |
| `respond` | Respond | Direct questions, requests requiring decisions |
| `draft` | Write-Reply | Routine requests, standard follow-ups |
| `archive` | To-Archive | Marketing emails, expired promotions |
| `needs_review` | Needs-Review | New contacts, complex threads, ambiguous |

## Philosophy

- **Read, don't send**: This MCP creates drafts but never sends emails automatically
- **Label, don't delete**: Emails are labeled for triage, not deleted
- **Safe by default**: No destructive operations
