"""Data models for Google Slides API."""
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class Presentation:
    """Information about a presentation."""
    id: str
    title: str
    locale: Optional[str]
    slide_count: int
    page_size: Optional[dict] = None  # width, height in EMU

    @classmethod
    def from_api_response(cls, data: dict) -> "Presentation":
        """Parse from Google Slides API response."""
        slides = data.get("slides", [])
        page_size = data.get("pageSize", {})

        size_dict = None
        if page_size:
            size_dict = {
                "width": page_size.get("width", {}).get("magnitude"),
                "height": page_size.get("height", {}).get("magnitude"),
                "unit": page_size.get("width", {}).get("unit", "EMU"),
            }

        return cls(
            id=data.get("presentationId", ""),
            title=data.get("title", ""),
            locale=data.get("locale"),
            slide_count=len(slides),
            page_size=size_dict,
        )


@dataclass
class PageElement:
    """An element on a slide (shape, image, table, etc.)."""
    object_id: str
    element_type: str  # SHAPE, IMAGE, TABLE, VIDEO, LINE, etc.
    title: Optional[str] = None
    description: Optional[str] = None
    text_content: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "PageElement":
        """Parse from Slides API pageElement response."""
        object_id = data.get("objectId", "")

        # Determine element type
        element_type = "UNKNOWN"
        text_content = None

        if "shape" in data:
            element_type = "SHAPE"
            text_content = cls._extract_text(data["shape"])
        elif "image" in data:
            element_type = "IMAGE"
        elif "table" in data:
            element_type = "TABLE"
            text_content = cls._extract_table_text(data["table"])
        elif "video" in data:
            element_type = "VIDEO"
        elif "line" in data:
            element_type = "LINE"
        elif "sheetsChart" in data:
            element_type = "SHEETS_CHART"
        elif "wordArt" in data:
            element_type = "WORD_ART"
            text_content = cls._extract_text(data.get("wordArt", {}))

        return cls(
            object_id=object_id,
            element_type=element_type,
            title=data.get("title"),
            description=data.get("description"),
            text_content=text_content,
        )

    @staticmethod
    def _extract_text(shape_data: dict) -> Optional[str]:
        """Extract plain text from a shape's text content."""
        text = shape_data.get("text", {})
        text_elements = text.get("textElements", [])

        parts = []
        for element in text_elements:
            text_run = element.get("textRun", {})
            content = text_run.get("content", "")
            if content:
                parts.append(content)

        result = "".join(parts).strip()
        return result if result else None

    @staticmethod
    def _extract_table_text(table_data: dict) -> Optional[str]:
        """Extract text from all cells in a table."""
        rows = table_data.get("tableRows", [])
        parts = []

        for row in rows:
            cells = row.get("tableCells", [])
            row_texts = []
            for cell in cells:
                text = cell.get("text", {})
                text_elements = text.get("textElements", [])
                cell_text = ""
                for element in text_elements:
                    text_run = element.get("textRun", {})
                    content = text_run.get("content", "")
                    if content:
                        cell_text += content
                row_texts.append(cell_text.strip())
            parts.append(" | ".join(row_texts))

        result = "\n".join(parts).strip()
        return result if result else None


@dataclass
class Slide:
    """A slide in a presentation."""
    object_id: str
    page_type: str  # SLIDE, MASTER, LAYOUT, NOTES
    elements: list[PageElement] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, data: dict) -> "Slide":
        """Parse from Slides API slide response."""
        elements = []
        for element_data in data.get("pageElements", []):
            elements.append(PageElement.from_api_response(element_data))

        return cls(
            object_id=data.get("objectId", ""),
            page_type=data.get("pageType", "SLIDE"),
            elements=elements,
        )

    def get_text_content(self) -> str:
        """Get all text content from this slide."""
        texts = []
        for element in self.elements:
            if element.text_content:
                texts.append(element.text_content)
        return "\n".join(texts)
