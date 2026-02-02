"""Tests for Gmail client."""
import pytest
from gmail.client import (
    normalize_label,
    get_gmail_name,
    get_exclude_query,
    LABELS,
    VALID_KEYS,
    GMAIL_NAMES,
)


class TestLabelNormalization:
    """Test label normalization functions."""

    def test_normalize_internal_key(self):
        """Internal keys should pass through."""
        assert normalize_label("fyi") == "fyi"
        assert normalize_label("respond") == "respond"
        assert normalize_label("draft") == "draft"
        assert normalize_label("archive") == "archive"
        assert normalize_label("needs_review") == "needs_review"

    def test_normalize_gmail_name(self):
        """Gmail names should convert to internal keys."""
        assert normalize_label("FYI") == "fyi"
        assert normalize_label("Respond") == "respond"
        assert normalize_label("Write-Reply") == "draft"
        assert normalize_label("To-Archive") == "archive"
        assert normalize_label("Needs-Review") == "needs_review"

    def test_normalize_case_insensitive(self):
        """Should handle case variations."""
        assert normalize_label("FYI") == "fyi"
        assert normalize_label("fyi") == "fyi"
        assert normalize_label("Fyi") == "fyi"

    def test_normalize_hyphen_underscore(self):
        """Should handle hyphen/underscore variations."""
        assert normalize_label("needs-review") == "needs_review"
        assert normalize_label("needs_review") == "needs_review"

    def test_normalize_invalid(self):
        """Invalid labels should return None."""
        assert normalize_label("invalid") is None
        assert normalize_label("") is None
        assert normalize_label("random") is None


class TestGetGmailName:
    """Test get_gmail_name function."""

    def test_valid_keys(self):
        """Should return Gmail names for valid keys."""
        assert get_gmail_name("fyi") == "FYI"
        assert get_gmail_name("respond") == "Respond"
        assert get_gmail_name("draft") == "Write-Reply"
        assert get_gmail_name("archive") == "To-Archive"
        assert get_gmail_name("needs_review") == "Needs-Review"

    def test_invalid_key(self):
        """Should return None for invalid keys."""
        assert get_gmail_name("invalid") is None


class TestExcludeQuery:
    """Test exclude query generation."""

    def test_exclude_query_format(self):
        """Query should exclude all classification labels."""
        query = get_exclude_query()

        # Should exclude all labels
        assert "-label:FYI" in query
        assert "-label:Respond" in query
        assert '-label:"Write-Reply"' in query  # Has hyphen, needs quotes
        assert '-label:"To-Archive"' in query
        assert '-label:"Needs-Review"' in query


class TestLabelConstants:
    """Test label constant definitions."""

    def test_label_count(self):
        """Should have exactly 5 labels."""
        assert len(LABELS) == 5
        assert len(VALID_KEYS) == 5
        assert len(GMAIL_NAMES) == 5

    def test_label_consistency(self):
        """Keys and names should be consistent."""
        for key in VALID_KEYS:
            assert key in LABELS
            assert LABELS[key] in GMAIL_NAMES
