# Sheets MCP

MCP server for Google Sheets. Read-only access to spreadsheet data.

## Tools

| Tool | Args | Description |
|------|------|-------------|
| `get_spreadsheet_info` | `spreadsheet_id` | Get spreadsheet metadata (title, sheets, locale) |
| `list_sheets` | `spreadsheet_id` | List all sheets (tabs) with row/column counts |
| `get_headers` | `spreadsheet_id`, `sheet_name` | Get column headers (first row) |
| `read_sheet` | `spreadsheet_id`, `sheet_name`, `range_notation?`, `limit?` | Read rows as dictionaries |
| `find_rows` | `spreadsheet_id`, `sheet_name`, `column`, `value`, `exact_match?` | Find rows matching a value |

## Setup

### 1. Prerequisites

- Python 3.11+
- Google Cloud project with Sheets API enabled
- OAuth credentials (Desktop app type)

### 2. Credentials

Place `gmail_credentials.json` (same file works for Sheets) in your app's config directory:
```
~/.letter-rip/credentials/gmail_credentials.json
```

### 3. Authentication

Run the auth setup with a test spreadsheet:
```bash
cd /path/to/google-mcps
python -m sheets.auth --test YOUR_SPREADSHEET_ID
```

This opens a browser for OAuth consent and verifies access to your spreadsheet.

### 4. Claude Code Configuration

Add to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "sheets": {
      "command": "python3",
      "args": ["-m", "sheets"],
      "cwd": "/path/to/google-mcps",
      "env": {
        "PYTHONPATH": "/path/to/google-mcps",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GOOGLE_MCP_APP_NAME": "letter-rip-pipeline"
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

## Usage Examples

### List sheets in a spreadsheet
```
"What sheets are in spreadsheet 1ABC...xyz?"
```

### Read data from a sheet
```
"Read the first 20 rows from the Opportunities sheet"
```

### Find specific rows
```
"Find all rows where stage equals 'Discovery' in the Opportunities sheet"
```

### Get column headers
```
"What are the column headers in the Activities sheet?"
```

## Data Format

The `read_sheet` and `find_rows` tools return rows as dictionaries, using the first row as column headers:

```json
[
  {"id": "OPP-001", "name": "Acme Deal", "stage": "Discovery", "amount": "50000"},
  {"id": "OPP-002", "name": "Big Corp", "stage": "Proposal", "amount": "100000"}
]
```

## Read-Only Philosophy

This MCP intentionally has **no write operations**:

- No creating rows
- No updating cells
- No deleting data

Spreadsheet modifications should be done manually or through other tools. This prevents accidental data loss and keeps the MCP safe for automated workflows.

## Spreadsheet ID

Find your spreadsheet ID in the URL:
```
https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
```

For example, in:
```
https://docs.google.com/spreadsheets/d/1ABC_xyz123_example/edit
```

The spreadsheet ID is `1ABC_xyz123_example`.
