# Forms MCP

Google Forms MCP server for Claude Code. Read form structure and analyze responses.

## Features

- **Read form structure** - Get form title, description, and all questions
- **List questions** - See question types, options, and required flags
- **Get responses** - Access all responses with answers
- **Tabular export** - Get responses in spreadsheet-friendly format
- **Response summary** - Get statistics and answer distributions

**Note:** The Google Forms API is read-only for form structure. You cannot create or modify forms programmatically, only read them and their responses.

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud project with Forms API enabled
- OAuth credentials (can share with Gmail MCP)

### Authentication

1. Ensure OAuth credentials are in place:
   ```
   ~/.letter-rip/credentials/gmail_credentials.json
   ```

2. Enable the Google Forms API in your Google Cloud project

3. Run the auth setup:
   ```bash
   cd ~/claude/google-mcps
   python -m forms.auth
   ```

4. Test the connection (requires a form ID):
   ```bash
   python -m forms.auth --test YOUR_FORM_ID
   ```

**Finding Form ID:** The form ID is in the URL: `https://docs.google.com/forms/d/{FORM_ID}/edit`

## Tools

| Tool | Description |
|------|-------------|
| `get_form(form_id)` | Get form metadata and all questions |
| `list_questions(form_id)` | List questions with types and options |
| `get_responses(form_id, limit)` | Get all responses with answers |
| `get_responses_table(form_id, limit)` | Get responses as table (question titles as keys) |
| `get_response(form_id, response_id)` | Get a specific response |
| `get_response_summary(form_id)` | Get statistics and answer distributions |

## Usage Examples

### Understanding form structure

```
"What questions are in this form?"
"Show me the form structure for [form_id]"
"What are the required questions?"
```

### Viewing responses

```
"How many responses does this form have?"
"Show me the latest 10 responses"
"Get all responses as a table for export"
```

### Analyzing responses

```
"Show me the response distribution for question X"
"What's the most common answer to the first question?"
"When was the first and last response submitted?"
```

### Specific response lookup

```
"Show me response [response_id]"
"What did this person answer for each question?"
```

## Configuration

Add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "forms": {
      "command": "python3",
      "args": ["-m", "forms"],
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

This MCP uses two Google Forms API scopes:

- `forms.body.readonly` - Read form structure and questions
- `forms.responses.readonly` - Read form responses

## Question Types

The MCP recognizes these question types:

| Type | Description |
|------|-------------|
| `TEXT` | Short text answer |
| `PARAGRAPH` | Long text answer |
| `CHOICE` | Multiple choice (radio buttons) |
| `CHECKBOX` | Multiple selection (checkboxes) |
| `DROPDOWN` | Dropdown menu |
| `SCALE` | Linear scale (e.g., 1-5) |
| `DATE` | Date picker |
| `TIME` | Time picker |
| `FILE_UPLOAD` | File upload (returns Drive URLs) |
| `GRID` | Grid/matrix question |

## Limitations

- **Read-only for forms:** Cannot create, edit, or delete forms
- **Read-only for responses:** Cannot submit or modify responses
- **No real-time updates:** Responses are fetched at query time
- **File uploads:** Returns Google Drive URLs, not file contents

## Related MCPs

- **Gmail MCP** - Email operations
- **Sheets MCP** - Spreadsheet data (for exporting form data)
- **Calendar MCP** - Scheduling (for forms that book time)
- **Slides MCP** - Presentations
