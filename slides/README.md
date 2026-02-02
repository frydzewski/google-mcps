# Slides MCP

Google Slides MCP server for Claude Code. Read presentation content and create/modify slides.

## Features

- **Read presentations** - Get metadata, slide counts, and content
- **Extract text** - Pull text from individual slides or entire presentations
- **Create presentations** - Start new slide decks
- **Add slides** - Insert slides with various layouts
- **Add text boxes** - Place text content on slides

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud project with Slides API enabled
- OAuth credentials (can share with Gmail MCP)

### Authentication

1. Ensure OAuth credentials are in place:
   ```
   ~/.letter-rip/credentials/gmail_credentials.json
   ```

2. Run the auth setup:
   ```bash
   cd ~/claude/google-mcps
   python -m slides.auth
   ```

3. Test with a presentation:
   ```bash
   python -m slides.auth --test YOUR_PRESENTATION_ID
   ```

## Tools

### Read Tools (4)

| Tool | Description |
|------|-------------|
| `get_presentation(id)` | Get presentation metadata (title, slide count) |
| `list_slides(id)` | List all slides with element summaries |
| `get_slide_text(id, slide_number)` | Get text from one slide (or all with 0) |
| `get_presentation_text(id)` | Get all text organized by slide |

### Write Tools (3)

| Tool | Description |
|------|-------------|
| `create_presentation(title)` | Create a new presentation |
| `create_slide(id, layout)` | Add a slide with specified layout |
| `add_text_to_slide(id, slide_num, text, x, y, width, height)` | Add a text box |

### Available Layouts

For `create_slide`, use one of these layout options:
- `BLANK` (default)
- `TITLE`
- `TITLE_AND_BODY`
- `TITLE_AND_TWO_COLUMNS`
- `TITLE_ONLY`
- `SECTION_HEADER`
- `ONE_COLUMN_TEXT`
- `MAIN_POINT`
- `BIG_NUMBER`

## Usage Examples

### Reading presentations

```
"What's in this presentation?" (with presentation ID)
"Summarize slide 3"
"Extract all text from the deck"
```

### Creating presentations

```
"Create a new presentation called 'Q1 Report'"
"Add a title slide to my presentation"
"Add a text box at position 100,200 with 'Hello World'"
```

## Configuration

Add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "slides": {
      "command": "python3",
      "args": ["-m", "slides"],
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

This MCP uses two Google Slides API scopes:

- `presentations.readonly` - Read presentation content
- `presentations` - Create and modify presentations

## Coordinate System

When adding text boxes:
- `x`, `y` are in **points** (1/72 inch) from top-left
- Default position: (100, 100)
- Default size: 400 x 100 points

## Related MCPs

- **Gmail MCP** - Email operations
- **Sheets MCP** - Spreadsheet data
- **Calendar MCP** - Calendar and scheduling
- **Forms MCP** - Form responses
