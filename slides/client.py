"""Google Slides API client wrapper."""
from typing import Optional
import logging
import uuid

from .models import Presentation, Slide, PageElement

logger = logging.getLogger("google_mcps.slides")

# EMU (English Metric Units) conversion: 1 point = 12700 EMU
EMU_PER_POINT = 12700


class SlidesClient:
    """Wrapper for Google Slides API operations."""

    def __init__(self, service):
        """
        Initialize the Slides client.

        Args:
            service: Google Slides API service object
        """
        self.service = service

    def get_presentation(self, presentation_id: str) -> Presentation:
        """
        Get presentation metadata.

        Args:
            presentation_id: The presentation ID (from the URL)

        Returns:
            Presentation object with title, slide count, etc.
        """
        try:
            result = (
                self.service.presentations()
                .get(presentationId=presentation_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to get presentation {presentation_id}: {e}")
            raise

        return Presentation.from_api_response(result)

    def list_slides(self, presentation_id: str) -> list[Slide]:
        """
        List all slides in a presentation.

        Args:
            presentation_id: The presentation ID

        Returns:
            List of Slide objects with their elements
        """
        try:
            result = (
                self.service.presentations()
                .get(presentationId=presentation_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to list slides for {presentation_id}: {e}")
            raise

        slides = []
        for slide_data in result.get("slides", []):
            slides.append(Slide.from_api_response(slide_data))

        return slides

    def get_slide(self, presentation_id: str, slide_id: str) -> Optional[Slide]:
        """
        Get a specific slide by ID.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide's object ID

        Returns:
            Slide object or None if not found
        """
        slides = self.list_slides(presentation_id)

        for slide in slides:
            if slide.object_id == slide_id:
                return slide

        return None

    def get_slide_by_number(self, presentation_id: str, slide_number: int) -> Optional[Slide]:
        """
        Get a slide by its position (1-indexed).

        Args:
            presentation_id: The presentation ID
            slide_number: Slide number (1 = first slide)

        Returns:
            Slide object or None if out of range
        """
        slides = self.list_slides(presentation_id)

        if 1 <= slide_number <= len(slides):
            return slides[slide_number - 1]

        return None

    def get_slide_text(self, presentation_id: str, slide_id: str) -> str:
        """
        Extract all text content from a specific slide.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide's object ID

        Returns:
            Combined text from all text elements on the slide
        """
        slide = self.get_slide(presentation_id, slide_id)
        if slide:
            return slide.get_text_content()
        return ""

    def get_presentation_text(self, presentation_id: str) -> list[dict]:
        """
        Get text from all slides in a presentation.

        Args:
            presentation_id: The presentation ID

        Returns:
            List of dicts with slide_id, slide_number, and text
        """
        slides = self.list_slides(presentation_id)

        result = []
        for i, slide in enumerate(slides, start=1):
            text = slide.get_text_content()
            result.append({
                "slide_id": slide.object_id,
                "slide_number": i,
                "text": text,
            })

        return result

    def get_all_text(self, presentation_id: str) -> str:
        """
        Get all text from a presentation as a single string.

        Useful for summarization or search.

        Args:
            presentation_id: The presentation ID

        Returns:
            All text content concatenated with slide separators
        """
        slides_text = self.get_presentation_text(presentation_id)

        parts = []
        for slide in slides_text:
            if slide["text"]:
                parts.append(f"--- Slide {slide['slide_number']} ---\n{slide['text']}")

        return "\n\n".join(parts)

    # =========================================================================
    # Write Operations
    # =========================================================================

    def create_presentation(self, title: str) -> Presentation:
        """
        Create a new presentation.

        Args:
            title: Title for the new presentation

        Returns:
            Presentation object with the new presentation's ID
        """
        body = {"title": title}

        try:
            result = self.service.presentations().create(body=body).execute()
        except Exception as e:
            logger.error(f"Failed to create presentation: {e}")
            raise

        return Presentation.from_api_response(result)

    def create_slide(
        self,
        presentation_id: str,
        layout: str = "BLANK",
        insert_at: int = -1,
    ) -> str:
        """
        Create a new slide in a presentation.

        Args:
            presentation_id: The presentation ID
            layout: Predefined layout - BLANK, TITLE, TITLE_AND_BODY, etc.
            insert_at: Position to insert (-1 = append at end)

        Returns:
            The new slide's object ID
        """
        slide_id = f"slide_{uuid.uuid4().hex[:8]}"

        request = {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {
                    "predefinedLayout": layout,
                },
            }
        }

        if insert_at >= 0:
            request["createSlide"]["insertionIndex"] = insert_at

        try:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": [request]},
            ).execute()
        except Exception as e:
            logger.error(f"Failed to create slide: {e}")
            raise

        return slide_id

    def add_text_box(
        self,
        presentation_id: str,
        slide_id: str,
        text: str,
        x: float = 100,
        y: float = 100,
        width: float = 400,
        height: float = 100,
    ) -> str:
        """
        Add a text box to a slide.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide's object ID
            text: Text content for the text box
            x: X position in points from left
            y: Y position in points from top
            width: Width in points
            height: Height in points

        Returns:
            The new text box element's object ID
        """
        element_id = f"textbox_{uuid.uuid4().hex[:8]}"

        requests = [
            # Create the shape
            {
                "createShape": {
                    "objectId": element_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": self._points_to_emu(width), "unit": "EMU"},
                            "height": {"magnitude": self._points_to_emu(height), "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": self._points_to_emu(x),
                            "translateY": self._points_to_emu(y),
                            "unit": "EMU",
                        },
                    },
                }
            },
            # Insert text into the shape
            {
                "insertText": {
                    "objectId": element_id,
                    "insertionIndex": 0,
                    "text": text,
                }
            },
        ]

        try:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()
        except Exception as e:
            logger.error(f"Failed to add text box: {e}")
            raise

        return element_id

    def delete_slide(self, presentation_id: str, slide_id: str) -> bool:
        """
        Delete a slide from a presentation.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide's object ID

        Returns:
            True if successful
        """
        request = {
            "deleteObject": {
                "objectId": slide_id,
            }
        }

        try:
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": [request]},
            ).execute()
        except Exception as e:
            logger.error(f"Failed to delete slide {slide_id}: {e}")
            raise

        return True

    @staticmethod
    def _points_to_emu(points: float) -> int:
        """Convert points to EMU (English Metric Units)."""
        return int(points * EMU_PER_POINT)
