"""Google Sheets API client wrapper."""
from dataclasses import dataclass
from typing import Optional, Any
import logging

logger = logging.getLogger("google_mcps.sheets")


@dataclass
class SheetInfo:
    """Information about a sheet (tab) in a spreadsheet."""
    sheet_id: int
    title: str
    row_count: int
    column_count: int


@dataclass
class SpreadsheetInfo:
    """Information about a spreadsheet."""
    spreadsheet_id: str
    title: str
    sheets: list[SheetInfo]
    locale: Optional[str] = None
    time_zone: Optional[str] = None


class SheetsClient:
    """Wrapper for Google Sheets API operations (read-only)."""

    def __init__(self, service):
        """
        Initialize the Sheets client.

        Args:
            service: Google Sheets API service object
        """
        self.service = service

    def get_spreadsheet_info(self, spreadsheet_id: str) -> SpreadsheetInfo:
        """
        Get metadata about a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID

        Returns:
            SpreadsheetInfo with title, sheets list, locale, timezone
        """
        try:
            result = (
                self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to get spreadsheet info: {e}")
            raise

        sheets = []
        for sheet in result.get("sheets", []):
            props = sheet.get("properties", {})
            grid_props = props.get("gridProperties", {})
            sheets.append(SheetInfo(
                sheet_id=props.get("sheetId", 0),
                title=props.get("title", ""),
                row_count=grid_props.get("rowCount", 0),
                column_count=grid_props.get("columnCount", 0),
            ))

        props = result.get("properties", {})
        return SpreadsheetInfo(
            spreadsheet_id=result.get("spreadsheetId", spreadsheet_id),
            title=props.get("title", ""),
            sheets=sheets,
            locale=props.get("locale"),
            time_zone=props.get("timeZone"),
        )

    def list_sheets(self, spreadsheet_id: str) -> list[dict]:
        """
        List all sheets (tabs) in a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID

        Returns:
            List of sheet info dicts with title, sheet_id, row_count, column_count
        """
        info = self.get_spreadsheet_info(spreadsheet_id)
        return [
            {
                "title": sheet.title,
                "sheet_id": sheet.sheet_id,
                "row_count": sheet.row_count,
                "column_count": sheet.column_count,
            }
            for sheet in info.sheets
        ]

    def get_headers(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> list[str]:
        """
        Get column headers (first row) from a sheet.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet (tab)

        Returns:
            List of header column names
        """
        range_notation = f"'{sheet_name}'!1:1"

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_notation)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to get headers: {e}")
            raise

        values = result.get("values", [[]])
        return values[0] if values else []

    def read_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_notation: Optional[str] = None,
        include_headers: bool = True,
    ) -> list[dict]:
        """
        Read rows from a sheet as dictionaries.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet (tab)
            range_notation: Optional A1 notation (e.g., "A2:E100"). If not provided,
                           reads all data.
            include_headers: If True, first row is treated as headers.
                           If False, generates column_0, column_1, etc.

        Returns:
            List of row dictionaries with column names as keys
        """
        if range_notation:
            full_range = f"'{sheet_name}'!{range_notation}"
        else:
            full_range = f"'{sheet_name}'"

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=full_range)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to read sheet: {e}")
            raise

        values = result.get("values", [])
        if not values:
            return []

        if include_headers:
            headers = values[0]
            data_rows = values[1:]
        else:
            # Generate column names
            max_cols = max(len(row) for row in values) if values else 0
            headers = [f"column_{i}" for i in range(max_cols)]
            data_rows = values

        rows = []
        for row in data_rows:
            row_dict = {}
            for i, header in enumerate(headers):
                # Handle rows with fewer columns than headers
                value = row[i] if i < len(row) else ""
                row_dict[header] = value
            rows.append(row_dict)

        return rows

    def find_rows(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        column: str,
        value: str,
        exact_match: bool = True,
    ) -> list[dict]:
        """
        Find rows where a column matches a value.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet (tab)
            column: Column name to search
            value: Value to search for
            exact_match: If True, exact match. If False, contains match.

        Returns:
            List of matching row dictionaries
        """
        all_rows = self.read_sheet(spreadsheet_id, sheet_name)

        matching = []
        for row in all_rows:
            cell_value = row.get(column, "")
            if exact_match:
                if cell_value == value:
                    matching.append(row)
            else:
                if value.lower() in cell_value.lower():
                    matching.append(row)

        return matching

    def get_row_by_id(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        id_column: str,
        id_value: str,
    ) -> Optional[dict]:
        """
        Get a single row by ID column value.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet (tab)
            id_column: Name of the ID column
            id_value: The ID value to find

        Returns:
            Row dictionary or None if not found
        """
        matches = self.find_rows(
            spreadsheet_id, sheet_name, id_column, id_value, exact_match=True
        )
        return matches[0] if matches else None
