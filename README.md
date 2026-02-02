# Google MCPs

MCP (Model Context Protocol) servers for Google APIs, designed for use with Claude Code.

## Available MCPs

- **gmail/** - Gmail operations (read, label, draft - never send)
- **sheets/** - Google Sheets operations (read-only)

## Installation

```bash
pip install -e .
```

## Authentication

Each MCP requires Google OAuth credentials. See individual MCP READMEs for setup.

## Usage with Claude Code

Add to your `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["-m", "gmail.server"],
      "cwd": "/path/to/google-mcps"
    }
  }
}
```
