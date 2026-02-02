"""Tests for Sheets client."""
import pytest
from unittest.mock import Mock, MagicMock
from sheets.client import SheetsClient, SheetInfo, SpreadsheetInfo


class TestSheetsClient:
    """Test SheetsClient class."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock Sheets API service."""
        return Mock()

    @pytest.fixture
    def client(self, mock_service):
        """Create a SheetsClient with mock service."""
        return SheetsClient(service=mock_service)

    def test_get_spreadsheet_info(self, client, mock_service):
        """Should parse spreadsheet metadata correctly."""
        mock_service.spreadsheets().get().execute.return_value = {
            "spreadsheetId": "test-id",
            "properties": {
                "title": "Test Spreadsheet",
                "locale": "en_US",
                "timeZone": "America/New_York",
            },
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Sheet1",
                        "gridProperties": {
                            "rowCount": 100,
                            "columnCount": 26,
                        },
                    }
                },
                {
                    "properties": {
                        "sheetId": 1,
                        "title": "Sheet2",
                        "gridProperties": {
                            "rowCount": 50,
                            "columnCount": 10,
                        },
                    }
                },
            ],
        }

        info = client.get_spreadsheet_info("test-id")

        assert info.spreadsheet_id == "test-id"
        assert info.title == "Test Spreadsheet"
        assert info.locale == "en_US"
        assert info.time_zone == "America/New_York"
        assert len(info.sheets) == 2
        assert info.sheets[0].title == "Sheet1"
        assert info.sheets[0].row_count == 100
        assert info.sheets[1].title == "Sheet2"

    def test_list_sheets(self, client, mock_service):
        """Should return list of sheet info dicts."""
        mock_service.spreadsheets().get().execute.return_value = {
            "spreadsheetId": "test-id",
            "properties": {"title": "Test"},
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Opportunities",
                        "gridProperties": {"rowCount": 100, "columnCount": 10},
                    }
                },
            ],
        }

        sheets = client.list_sheets("test-id")

        assert len(sheets) == 1
        assert sheets[0]["title"] == "Opportunities"
        assert sheets[0]["sheet_id"] == 0

    def test_get_headers(self, client, mock_service):
        """Should return first row as headers."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Name", "Email", "Amount", "Stage"]]
        }

        headers = client.get_headers("test-id", "Sheet1")

        assert headers == ["Name", "Email", "Amount", "Stage"]

    def test_get_headers_empty(self, client, mock_service):
        """Should return empty list for empty sheet."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": []
        }

        headers = client.get_headers("test-id", "Sheet1")

        assert headers == []

    def test_read_sheet(self, client, mock_service):
        """Should convert rows to dictionaries."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "name", "amount"],
                ["1", "Deal A", "10000"],
                ["2", "Deal B", "25000"],
            ]
        }

        rows = client.read_sheet("test-id", "Opportunities")

        assert len(rows) == 2
        assert rows[0] == {"id": "1", "name": "Deal A", "amount": "10000"}
        assert rows[1] == {"id": "2", "name": "Deal B", "amount": "25000"}

    def test_read_sheet_missing_columns(self, client, mock_service):
        """Should handle rows with fewer columns than headers."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "name", "amount", "stage"],
                ["1", "Deal A"],  # Missing amount and stage
            ]
        }

        rows = client.read_sheet("test-id", "Sheet1")

        assert len(rows) == 1
        assert rows[0] == {"id": "1", "name": "Deal A", "amount": "", "stage": ""}

    def test_read_sheet_empty(self, client, mock_service):
        """Should return empty list for empty sheet."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": []
        }

        rows = client.read_sheet("test-id", "Sheet1")

        assert rows == []

    def test_find_rows_exact_match(self, client, mock_service):
        """Should find rows with exact column match."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "owner", "stage"],
                ["1", "Alice", "Discovery"],
                ["2", "Bob", "Proposal"],
                ["3", "Alice", "Negotiation"],
            ]
        }

        matches = client.find_rows("test-id", "Sheet1", "owner", "Alice")

        assert len(matches) == 2
        assert matches[0]["id"] == "1"
        assert matches[1]["id"] == "3"

    def test_find_rows_contains_match(self, client, mock_service):
        """Should find rows with partial match when exact_match=False."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "subject"],
                ["1", "Important meeting request"],
                ["2", "Quick question"],
                ["3", "Meeting follow-up"],
            ]
        }

        matches = client.find_rows(
            "test-id", "Sheet1", "subject", "meeting", exact_match=False
        )

        assert len(matches) == 2
        assert matches[0]["id"] == "1"
        assert matches[1]["id"] == "3"

    def test_find_rows_no_match(self, client, mock_service):
        """Should return empty list when no matches."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "owner"],
                ["1", "Alice"],
            ]
        }

        matches = client.find_rows("test-id", "Sheet1", "owner", "Charlie")

        assert matches == []

    def test_get_row_by_id(self, client, mock_service):
        """Should return single row by ID."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "name", "amount"],
                ["OPP-001", "Big Deal", "100000"],
                ["OPP-002", "Small Deal", "5000"],
            ]
        }

        row = client.get_row_by_id("test-id", "Sheet1", "id", "OPP-001")

        assert row is not None
        assert row["name"] == "Big Deal"
        assert row["amount"] == "100000"

    def test_get_row_by_id_not_found(self, client, mock_service):
        """Should return None when ID not found."""
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["id", "name"],
                ["OPP-001", "Deal"],
            ]
        }

        row = client.get_row_by_id("test-id", "Sheet1", "id", "OPP-999")

        assert row is None


class TestSheetInfo:
    """Test SheetInfo dataclass."""

    def test_create(self):
        """Should create SheetInfo."""
        info = SheetInfo(
            sheet_id=0,
            title="Test Sheet",
            row_count=100,
            column_count=26,
        )

        assert info.sheet_id == 0
        assert info.title == "Test Sheet"
        assert info.row_count == 100
        assert info.column_count == 26


class TestSpreadsheetInfo:
    """Test SpreadsheetInfo dataclass."""

    def test_create(self):
        """Should create SpreadsheetInfo."""
        sheet = SheetInfo(sheet_id=0, title="Sheet1", row_count=100, column_count=26)
        info = SpreadsheetInfo(
            spreadsheet_id="abc123",
            title="My Spreadsheet",
            sheets=[sheet],
            locale="en_US",
            time_zone="America/New_York",
        )

        assert info.spreadsheet_id == "abc123"
        assert info.title == "My Spreadsheet"
        assert len(info.sheets) == 1
        assert info.locale == "en_US"
        assert info.time_zone == "America/New_York"

    def test_optional_fields(self):
        """Should allow optional locale and timezone."""
        info = SpreadsheetInfo(
            spreadsheet_id="abc123",
            title="My Spreadsheet",
            sheets=[],
        )

        assert info.locale is None
        assert info.time_zone is None
