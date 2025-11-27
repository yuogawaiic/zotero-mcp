from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import PyPDF2
import urllib.parse
import os

__version__ = "0.1.0"

# Initialize FastMCP server
mcp = FastMCP("zotero")

ZOTERO_API_BASE = "http://localhost:23119/api/users/0/"
USER_AGENT = "zotero-mcp/1.0"  # <--- ここを変更

async def make_zotero_request(endpoint: str) -> Any:
    """Make a request to the Zotero API."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    url = f"{ZOTERO_API_BASE}{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@mcp.tool()
async def zotero_search_items(q: str = "") -> str:
    """Search items in the Zotero library by author and title (excluding attachments, up to 30 results)."""
    # Build query parameters
    params = [
        "itemType=-attachment",
        "limit=30"
    ]
    if q:
        params.append(f"q={q}")
    param_str = "&".join(params)
    data = await make_zotero_request(f"items?{param_str}")
    if "error" in data:
        return f"Zotero API error: {data['error']}"
    if not data:
        return "No items found."

    # Format items as readable text
    result_lines = [f"Found {len(data)} items:\n"]
    for idx, item in enumerate(data, 1):
        item_data = item.get("data", {})
        meta = item.get("meta", {})

        # Extract key information
        item_key = item_data.get("key", "N/A")
        title = item_data.get("title", "No title")
        item_type = item_data.get("itemType", "N/A")
        date = item_data.get("date", "N/A")

        # Format authors
        creators = item_data.get("creators", [])
        if creators:
            author_names = [f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators]
            authors = ", ".join(author_names)
        else:
            authors = meta.get("creatorSummary", "N/A")

        # Additional fields
        publication = item_data.get("publicationTitle", item_data.get("bookTitle", ""))
        doi = item_data.get("DOI", "")

        # Format item
        result_lines.append(f"[{idx}] Item Key: {item_key}")
        result_lines.append(f"    Title: {title}")
        result_lines.append(f"    Authors: {authors}")
        result_lines.append(f"    Date: {date}")
        result_lines.append(f"    Type: {item_type}")
        if publication:
            result_lines.append(f"    Publication: {publication}")
        if doi:
            result_lines.append(f"    DOI: {doi}")
        result_lines.append("")

    return "\n".join(result_lines)

@mcp.tool()
async def zotero_get_item(itemKey: str) -> str:
    """Retrieve the details of a specified item in the Zotero library by itemKey."""
    data = await make_zotero_request(f"items/{itemKey}")
    if "error" in data:
        return f"Zotero API error: {data['error']}"

    item_data = data.get("data", {})
    meta = data.get("meta", {})
    result_lines = []

    result_lines.append(f"Item Key: {item_data.get('key', 'N/A')}")
    result_lines.append(f"Type: {item_data.get('itemType', 'N/A')}")
    result_lines.append(f"Title: {item_data.get('title', 'No title')}")

    creators = item_data.get("creators", [])
    if creators:
        author_names = [f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators]
        result_lines.append(f"Authors: {', '.join(author_names)}")
    elif meta.get("creatorSummary"):
        result_lines.append(f"Authors: {meta['creatorSummary']}")

    if item_data.get("date"): result_lines.append(f"Date: {item_data['date']}")
    if item_data.get("publicationTitle"): result_lines.append(f"Publication: {item_data['publicationTitle']}")
    
    if item_data.get("abstractNote"):
        result_lines.append(f"\nAbstract:")
        result_lines.append(item_data['abstractNote'])

    tags = item_data.get("tags", [])
    if tags:
        tag_names = [tag.get("tag", "") for tag in tags]
        result_lines.append(f"\nTags: {', '.join(tag_names)}")

    return "\n".join(result_lines)

@mcp.tool()
async def zotero_read_pdf(itemKey: str) -> str:
    """From the children of the item specified by itemKey in the Zotero library, find the first PDF attachment, read it from the local file system, and return its full text."""
    children = await make_zotero_request(f"items/{itemKey}/children")
    if "error" in children:
        return f"Zotero API error: {children['error']}"
    
    pdf_path = None
    for child in children:
        if child['data'].get('itemType') == 'attachment' and child['data'].get('contentType') == 'application/pdf':
            enclosure = child.get('links', {}).get('enclosure', {})
            href = enclosure.get('href')
            if href and href.startswith('file:///'):
                if os.name == 'nt':
                    pdf_path = urllib.parse.unquote(href[8:])
                else:
                    pdf_path = urllib.parse.unquote(href[7:])
                break
    
    if not pdf_path:
        return "No PDF attachment found."
    
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)} (Path: {pdf_path})"

@mcp.tool()
async def read_pdf(local_path: str) -> str:
    """Read a PDF file from the local file path and return its full text."""
    try:
        with open(local_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)} (Path: {local_path})"

def main():
    mcp.run(transport='stdio')