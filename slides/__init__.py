"""Google Slides MCP server."""
from .client import SlidesClient
from .models import Presentation, Slide, PageElement

__all__ = ["SlidesClient", "Presentation", "Slide", "PageElement"]
