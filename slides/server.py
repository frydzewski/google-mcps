"""Slides MCP Server - Google Slides operations via Model Context Protocol."""
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build

from shared.auth import GoogleAuth, SLIDES_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import SlidesClient

# Initialize the MCP server
mcp = FastMCP("slides")

# App name can be overridden via environment
APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")

# Cached instances
_paths: Optional[MCPPaths] = None
_slides_client: Optional[SlidesClient] = None


def get_paths() -> MCPPaths:
    """Get or create paths instance."""
    global _paths
    if _paths is None:
        _paths = MCPPaths(APP_NAME)
        ensure_data_dirs(_paths.data_dir)
    return _paths


def get_slides_client() -> SlidesClient:
    """Get or create authenticated Slides client."""
    global _slides_client

    if _slides_client is not None:
        return _slides_client

    paths = get_paths()

    if not paths.slides_token.exists():
        raise RuntimeError(
            f"Slides not authenticated. Token not found at: {paths.slides_token}\n"
            "Run: python -m slides.auth"
        )

    auth = GoogleAuth(
        credentials_path=paths.slides_credentials,
        token_path=paths.slides_token,
        scopes=SLIDES_SCOPES,
    )

    creds = auth.get_credentials()
    service = build("slides", "v1", credentials=creds)
    client = SlidesClient(service=service)

    _slides_client = client
    return _slides_client


# =============================================================================
# SLIDES READ OPERATIONS (4 tools)
# =============================================================================


@mcp.tool()
def get_presentation(presentation_id: str) -> dict:
    """
    Get presentation metadata including title and slide count.

    Args:
        presentation_id: The presentation ID (from the Google Slides URL)

    Returns:
        Presentation info with id, title, slide_count, and page_size.
    """
    client = get_slides_client()
    pres = client.get_presentation(presentation_id)

    return {
        "id": pres.id,
        "title": pres.title,
        "locale": pres.locale,
        "slide_count": pres.slide_count,
        "page_size": pres.page_size,
    }


@mcp.tool()
def list_slides(presentation_id: str) -> list[dict]:
    """
    List all slides with their IDs and element summaries.

    Args:
        presentation_id: The presentation ID

    Returns:
        List of slides with slide_number, object_id, element_count, and has_text flag.
    """
    client = get_slides_client()
    slides = client.list_slides(presentation_id)

    return [
        {
            "slide_number": i + 1,
            "object_id": slide.object_id,
            "element_count": len(slide.elements),
            "has_text": bool(slide.get_text_content()),
        }
        for i, slide in enumerate(slides)
    ]


@mcp.tool()
def get_slide_text(presentation_id: str, slide_number: int = 0) -> dict:
    """
    Get text content from a specific slide or all slides.

    Args:
        presentation_id: The presentation ID
        slide_number: Slide number (1-indexed). Use 0 to get text from all slides.

    Returns:
        Dict with slide_number (or "all") and text content.
    """
    client = get_slides_client()

    if slide_number == 0:
        # Get all text
        text = client.get_all_text(presentation_id)
        return {
            "slide_number": "all",
            "text": text,
        }
    else:
        # Get specific slide
        slide = client.get_slide_by_number(presentation_id, slide_number)
        if slide is None:
            return {
                "slide_number": slide_number,
                "error": f"Slide {slide_number} not found",
                "text": "",
            }
        return {
            "slide_number": slide_number,
            "object_id": slide.object_id,
            "text": slide.get_text_content(),
        }


@mcp.tool()
def get_presentation_text(presentation_id: str) -> list[dict]:
    """
    Get all text content from presentation, organized by slide.

    Args:
        presentation_id: The presentation ID

    Returns:
        List of dicts with slide_number, slide_id, and text for each slide.
    """
    client = get_slides_client()
    return client.get_presentation_text(presentation_id)


# =============================================================================
# SLIDES WRITE OPERATIONS (3 tools)
# =============================================================================


@mcp.tool()
def create_presentation(title: str) -> dict:
    """
    Create a new Google Slides presentation.

    Args:
        title: Title for the new presentation

    Returns:
        New presentation info with id, title, and URL.
    """
    client = get_slides_client()
    pres = client.create_presentation(title)

    return {
        "id": pres.id,
        "title": pres.title,
        "url": f"https://docs.google.com/presentation/d/{pres.id}/edit",
    }


@mcp.tool()
def create_slide(
    presentation_id: str,
    layout: str = "BLANK",
) -> dict:
    """
    Add a new slide to a presentation.

    Args:
        presentation_id: The presentation ID
        layout: Predefined layout type. Options:
            - BLANK (default)
            - TITLE
            - TITLE_AND_BODY
            - TITLE_AND_TWO_COLUMNS
            - TITLE_ONLY
            - SECTION_HEADER
            - ONE_COLUMN_TEXT
            - MAIN_POINT
            - BIG_NUMBER

    Returns:
        New slide info with object_id.
    """
    client = get_slides_client()
    slide_id = client.create_slide(presentation_id, layout=layout)

    return {
        "object_id": slide_id,
        "layout": layout,
    }


@mcp.tool()
def add_text_to_slide(
    presentation_id: str,
    slide_number: int,
    text: str,
    x: int = 100,
    y: int = 100,
    width: int = 400,
    height: int = 100,
) -> dict:
    """
    Add a text box to a slide.

    Args:
        presentation_id: The presentation ID
        slide_number: Slide number (1-indexed)
        text: Text content to add
        x: X position in points from left edge (default 100)
        y: Y position in points from top edge (default 100)
        width: Width in points (default 400)
        height: Height in points (default 100)

    Returns:
        New text box info with element_id.
    """
    client = get_slides_client()

    # Get slide ID from number
    slide = client.get_slide_by_number(presentation_id, slide_number)
    if slide is None:
        return {
            "error": f"Slide {slide_number} not found",
        }

    element_id = client.add_text_box(
        presentation_id=presentation_id,
        slide_id=slide.object_id,
        text=text,
        x=float(x),
        y=float(y),
        width=float(width),
        height=float(height),
    )

    return {
        "element_id": element_id,
        "slide_number": slide_number,
        "slide_id": slide.object_id,
    }
