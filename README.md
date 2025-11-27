# Zotero MCP Server

An MCP (Model Context Protocol) server that integrates with Zotero's local API to search, retrieve, and extract full text from PDFs in your Zotero library.

## Prerequisites

- Zotero application with local API enabled
- uv (recommended) or Python 3.12+ with pip

## Enable Zotero Local API

In Zotero's settings (Preferences → Advanced → General), enable:

☑️ **Allow other applications on this computer to communicate with Zotero**

## Configuration

Add the following to your MCP client configuration file (e.g., `mcp_config.json` for Antigravity, `mcp.json` for Claude Desktop or Cursor):

```json
{
  "mcpServers": {
    "zotero": {
      "command": "uvx",
      "args": ["git+https://github.com/yuogawaiic/zotero-mcp.git"]
    }
  }
}
```

## Available Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `zotero_search_items` | `q` (optional) | Search items in your Zotero library by author name or title. Returns up to 30 matching items (excluding attachments). |
| `zotero_get_item` | `itemKey` (required) | Retrieve detailed information about a specific item including title, authors, publication info, abstract, tags, etc. |
| `zotero_read_pdf` | `itemKey` (required) | Extract full text from a PDF attachment associated with a Zotero item. |
| `read_pdf` | `local_path` (required) | Extract full text from a PDF file at a local file path. Can be used with filesystem MCP servers. |




