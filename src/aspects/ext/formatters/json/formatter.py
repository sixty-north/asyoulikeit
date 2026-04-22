"""JSON formatter."""

import json

from aspects.formatter import Formatter
from aspects.tabular_data import Reports, DetailLevel


class JsonFormatter(Formatter):
    """JSON formatter for structured data output.

    Outputs data as a JSON object with a top-level "tables" key containing
    named reports. Each report has the same structure as the previous single-table
    JSON output (metadata, columns, rows).

    This format is suitable for consumption by web APIs and data processing tools,
    and leaves room for future top-level additions (e.g., generation metadata).

    Note: JSON format always includes metadata regardless of header flag,
    as JSON is self-describing by nature.
    """

    def format(self, reports: Reports) -> str:
        """Format reports as structured JSON object.

        Args:
            reports: A Reports object containing one or more named reports

        Returns:
            Pretty-printed JSON string with top-level "tables" key containing
            each report with its metadata, columns and rows structure
        """
        tables = {}

        for report_name, report in reports.items():
            # Use report's detail_level preference (may have been overridden by CLI)
            detail_level = report.detail_level

            # JSON defaults to showing all columns (self-describing format)
            if detail_level == DetailLevel.AUTO:
                detail_level = DetailLevel.DETAILED

            # Filter columns based on detail_level
            columns_to_output = (
                report.data.columns if detail_level == DetailLevel.DETAILED
                else report.data.essential_columns
            )

            # Filter rows based on detail_level
            rows_to_output = report.data.rows_for_detail_level(detail_level)

            # Build column metadata including header flag
            columns = [
                {"key": col.key, "label": col.label, "header": col.header}
                for col in columns_to_output
            ]

            # Build rows using column keys (not labels), filtering to selected columns
            rows = [
                {col.key: row[col.key] for col in columns_to_output}
                for row in rows_to_output
            ]

            # Build metadata object
            metadata = {
                "title": report.data.title,
                "description": report.data.description,
                "present_transposed": report.data.present_transposed
            }

            # Each table has the same structure as the old single-table JSON
            tables[report_name] = {
                "metadata": metadata,
                "columns": columns,
                "rows": rows
            }

        # Top-level structure with "tables" key
        output = {
            "tables": tables
        }

        return json.dumps(output, indent=2)
