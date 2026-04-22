"""Tests for formatters."""

import json
import re
import pytest

from asyoulikeit.tabular_data import TableContent, Reports, Report
from asyoulikeit.formatter import (
    create_formatter,
    format_as,
    FormatterExtensionError,
)


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace by collapsing multiple spaces and newlines."""
    # First strip ANSI codes
    text = strip_ansi_codes(text)
    # Then collapse all whitespace to single spaces
    return ' '.join(text.split())


class TestTSVFormatter:
    """Tests for TSV (Tab-Separated Values) formatter."""

    def test_empty_table(self):
        """TSV formatter should handle empty tables (headers only)."""
        data = TableContent().add_column("name", "Name")
        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        assert result == "# Name"

    def test_single_column_single_row(self):
        """TSV formatter should handle single column, single row."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Name\nAlice"
        assert result == expected

    def test_multiple_columns_single_row(self):
        """TSV formatter should handle multiple columns."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Name\tAge\nAlice\t30"
        assert result == expected

    def test_multiple_rows(self):
        """TSV formatter should handle multiple rows."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
            .add_row(name="Charlie", age=35)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Name\tAge\nAlice\t30\nBob\t25\nCharlie\t35"
        assert result == expected

    def test_values_converted_to_strings(self):
        """TSV formatter should convert all values to strings."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("active", "Active")
            .add_column("score", "Score")
            .add_row(name="Alice", active=True, score=95.5)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Name\tActive\tScore\nAlice\tTrue\t95.5"
        assert result == expected


class TestJSONFormatter:
    """Tests for JSON formatter."""

    def test_empty_table(self):
        """JSON formatter should handle empty tables."""
        data = TableContent().add_column("name", "Name")
        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [{"key": "name", "label": "Name", "header": False}],
                    "rows": []
                }
            }
        }

    def test_single_column_single_row(self):
        """JSON formatter should handle single column, single row."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [{"key": "name", "label": "Name", "header": False}],
                    "rows": [{"name": "Alice"}]
                }
            }
        }

    def test_multiple_columns_single_row(self):
        """JSON formatter should handle multiple columns."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [
                        {"key": "name", "label": "Name", "header": False},
                        {"key": "age", "label": "Age", "header": False}
                    ],
                    "rows": [{"name": "Alice", "age": 30}]
                }
            }
        }

    def test_multiple_rows(self):
        """JSON formatter should handle multiple rows."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [
                        {"key": "name", "label": "Name", "header": False},
                        {"key": "age", "label": "Age", "header": False}
                    ],
                    "rows": [
                        {"name": "Alice", "age": 30},
                        {"name": "Bob", "age": 25},
                    ]
                }
            }
        }

    def test_json_is_pretty_printed(self):
        """JSON formatter should produce indented output."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        # Pretty-printed JSON should contain newlines and indentation
        assert "\n" in result
        assert "  " in result

    def test_rows_use_column_keys_not_labels(self):
        """JSON formatter rows should use column keys, with labels in column metadata."""
        data = (
            TableContent()
            .add_column("internal_name", "Display Name")
            .add_column("internal_age", "Age in Years")
            .add_row(internal_name="Alice", internal_age=30)
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [
                        {"key": "internal_name", "label": "Display Name", "header": False},
                        {"key": "internal_age", "label": "Age in Years", "header": False}
                    ],
                    "rows": [{"internal_name": "Alice", "internal_age": 30}]
                }
            }
        }


class TestFormatAs:
    """Tests for format_as dispatcher function."""

    def test_format_as_tsv(self):
        """format_as should dispatch to TSV formatter."""
        data = (
            TableContent()
            .add_column("x", "X")
            .add_row(x=1)
        )

        result = format_as(Reports(data=Report(data=data)), "tsv")
        assert result == "# X\n1"

    def test_format_as_json(self):
        """format_as should dispatch to JSON formatter."""
        data = (
            TableContent()
            .add_column("x", "X")
            .add_row(x=1)
        )

        result = format_as(Reports(data=Report(data=data)), "json")
        parsed = json.loads(result)
        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [{"key": "x", "label": "X", "header": False}],
                    "rows": [{"x": 1}]
                }
            }
        }

    def test_format_as_unknown_format(self):
        """format_as should raise FormatterExtensionError for unknown format."""
        data = TableContent().add_column("x", "X")

        with pytest.raises(FormatterExtensionError, match="Unknown format 'xml'"):
            format_as(Reports(data=Report(data=data)), "xml")

    def test_format_as_error_shows_available_formats(self):
        """Error message should list available formats."""
        data = TableContent().add_column("x", "X")

        with pytest.raises(FormatterExtensionError, match="Available: display, json, tsv"):
            format_as(Reports(data=Report(data=data)), "xml")


class TestTSVFormatterTranspose:
    """Tests for TSV formatter transpose functionality."""

    def test_tsv_transpose_with_header_column(self):
        """TSV should transpose output when present_transposed is True with header column."""
        data = (
            TableContent(present_transposed=True)
            .add_column("category", "Category", header=True)
            .add_column("apples", "Apples")
            .add_column("oranges", "Oranges")
            .add_row(category="Count", apples=10, oranges=15)
            .add_row(category="Price", apples=1.50, oranges=2.00)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Category\tCount\tPrice\nApples\t10\t1.5\nOranges\t15\t2.0"
        assert result == expected

    def test_tsv_transpose_without_header_column(self):
        """TSV should transpose output using row indices when no header column."""
        data = (
            TableContent(present_transposed=True)
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# \t0\t1\nName\tAlice\tBob\nAge\t30\t25"
        assert result == expected

    def test_tsv_no_transpose_when_flag_false(self):
        """TSV should not transpose when present_transposed is False."""
        data = (
            TableContent(present_transposed=False)
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Name\tAge\nAlice\t30\nBob\t25"
        assert result == expected

    def test_tsv_transpose_quarterly_metrics(self):
        """TSV transpose works well for quarterly metrics presentation."""
        data = (
            TableContent(present_transposed=True)
            .add_column("metric", "Metric", header=True)
            .add_column("q1", "Q1 2024")
            .add_column("q2", "Q2 2024")
            .add_row(metric="Revenue", q1=100000, q2=120000)
            .add_row(metric="Profit", q1=20000, q2=25000)
        )

        formatter = create_formatter("tsv")
        result = formatter.format(Reports(data=Report(data=data)))

        expected = "# Metric\tRevenue\tProfit\nQ1 2024\t100000\t20000\nQ2 2024\t120000\t25000"
        assert result == expected


class TestJSONFormatterMetadata:
    """Tests for JSON formatter metadata support."""

    def test_json_includes_metadata_with_title_and_description(self):
        """JSON output should include metadata with title and description."""
        data = (
            TableContent(title="User Report", description="Active users in the system")
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed["tables"]["data"]["metadata"]["title"] == "User Report"
        assert parsed["tables"]["data"]["metadata"]["description"] == "Active users in the system"
        assert parsed["tables"]["data"]["metadata"]["present_transposed"] is False

    def test_json_includes_metadata_with_null_values(self):
        """JSON output should include null metadata when not provided."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed["tables"]["data"]["metadata"] == {
            "title": None,
            "description": None,
            "present_transposed": False
        }

    def test_json_includes_present_transposed_flag(self):
        """JSON output should include present_transposed in metadata."""
        data = (
            TableContent(present_transposed=True)
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed["tables"]["data"]["metadata"]["present_transposed"] is True

    def test_json_includes_header_flag_on_columns(self):
        """JSON output should include header flag on each column."""
        data = (
            TableContent()
            .add_column("category", "Category", header=True)
            .add_column("value", "Value")
            .add_row(category="Apples", value=10)
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        assert parsed["tables"]["data"]["columns"][0]["header"] is True
        assert parsed["tables"]["data"]["columns"][1]["header"] is False

    def test_json_does_not_transpose_data(self):
        """JSON output should not transpose data even when present_transposed is True."""
        data = (
            TableContent(present_transposed=True)
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        formatter = create_formatter("json")
        result = formatter.format(Reports(data=Report(data=data)))

        parsed = json.loads(result)
        # Data structure should remain the same, just metadata flag is set
        assert len(parsed["tables"]["data"]["columns"]) == 2
        assert len(parsed["tables"]["data"]["rows"]) == 2
        assert parsed["tables"]["data"]["rows"][0] == {"name": "Alice", "age": 30}
        assert parsed["tables"]["data"]["metadata"]["present_transposed"] is True


class TestDisplayFormatter:
    """Tests for the display (human-presentation) formatter."""

    def test_empty_table(self):
        """Display formatter should handle empty tables."""
        data = TableContent().add_column("name", "Name")
        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))

        # Should return a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain the column name
        assert "Name" in result

    def test_single_column_single_row(self):
        """Display formatter should handle single column, single row."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))

        assert isinstance(result, str)
        assert "Name" in result
        assert "Alice" in result

    def test_multiple_columns_and_rows(self):
        """Display formatter should handle multiple columns and rows."""
        data = (
            TableContent()
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))

        assert isinstance(result, str)
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result
        assert "25" in result

    def test_display_with_title(self):
        """Display formatter should include title."""
        data = (
            TableContent(title="User Report")
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))
        result_normalized = normalize_whitespace(result)

        assert "User Report" in result_normalized

    def test_display_with_description(self):
        """Display formatter should include description as caption."""
        data = (
            TableContent(description="Active users")
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))
        result_normalized = normalize_whitespace(result)

        assert "Active users" in result_normalized

    def test_display_with_title_and_description(self):
        """Display formatter should include both title and description."""
        data = (
            TableContent(title="User Report", description="Active users in the system")
            .add_column("name", "Name")
            .add_row(name="Alice")
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))
        result_normalized = normalize_whitespace(result)

        assert "User Report" in result_normalized
        assert "Active users in the system" in result_normalized

    def test_display_with_header_column(self):
        """Display formatter should style header column."""
        data = (
            TableContent()
            .add_column("category", "Category", header=True)
            .add_column("value", "Value")
            .add_row(category="Apples", value=10)
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))

        assert "Category" in result
        assert "Value" in result
        assert "Apples" in result
        assert "10" in result

    def test_display_transposed_with_header_column(self):
        """Display formatter should transpose with header column values as headers."""
        data = (
            TableContent(present_transposed=True)
            .add_column("category", "Category", header=True)
            .add_column("apples", "Apples")
            .add_column("oranges", "Oranges")
            .add_row(category="Count", apples=10, oranges=15)
            .add_row(category="Price", apples=1.50, oranges=2.00)
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))

        # Header column label and values should be present
        assert "Category" in result
        assert "Count" in result
        assert "Price" in result
        # Data column labels should be in rows
        assert "Apples" in result
        assert "Oranges" in result
        # Values should be present
        assert "10" in result
        assert "15" in result

    def test_display_transposed_without_header_column(self):
        """Display formatter should transpose using row indices when no header column."""
        data = (
            TableContent(present_transposed=True)
            .add_column("name", "Name")
            .add_column("age", "Age")
            .add_row(name="Alice", age=30)
            .add_row(name="Bob", age=25)
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))

        # Row indices should appear as column headers
        assert "0" in result
        assert "1" in result
        # Column labels should be in first column
        assert "Name" in result
        assert "Age" in result
        # Values should be present
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result
        assert "25" in result

    def test_display_quarterly_metrics(self):
        """Display formatter should handle quarterly metrics beautifully."""
        data = (
            TableContent(
                title="Quarterly Metrics",
                description="Financial performance Q1-Q2 2024",
                present_transposed=True
            )
            .add_column("metric", "Metric", header=True)
            .add_column("q1", "Q1 2024")
            .add_column("q2", "Q2 2024")
            .add_row(metric="Revenue", q1=100000, q2=120000)
            .add_row(metric="Profit", q1=20000, q2=25000)
        )

        formatter = create_formatter("display")
        result = formatter.format(Reports(data=Report(data=data)))
        result_normalized = normalize_whitespace(result)

        # Metadata should be present
        assert "Quarterly Metrics" in result_normalized
        assert "Financial performance Q1-Q2 2024" in result_normalized
        # Header column should be present
        assert "Metric" in result
        assert "Revenue" in result
        assert "Profit" in result
        # Column headers from data
        assert "Q1 2024" in result
        assert "Q2 2024" in result
        # Values
        assert "100000" in result
        assert "120000" in result
        assert "20000" in result
        assert "25000" in result


class TestFormatterIntegration:
    """Integration tests for formatters with realistic data."""

    def test_color_table_as_tsv(self):
        """Test formatting color data as TSV."""
        data = (
            TableContent()
            .add_column("color_name", "Color Name")
            .add_column("color_hex", "Color Hex")
            .add_column("complementary_color_name", "Complementary Color Name")
            .add_column("complementary_color_hex", "Complementary Color Hex")
            .add_row(
                color_name="primary",
                color_hex="#FF0000",
                complementary_color_name="secondary",
                complementary_color_hex="#00FF00"
            )
            .add_row(
                color_name="secondary",
                color_hex="#00FF00",
                complementary_color_name="primary",
                complementary_color_hex="#FF0000"
            )
        )

        result = format_as(Reports(data=Report(data=data)), "tsv")
        lines = result.split("\n")

        assert lines[0] == "# Color Name\tColor Hex\tComplementary Color Name\tComplementary Color Hex"
        assert lines[1] == "primary\t#FF0000\tsecondary\t#00FF00"
        assert lines[2] == "secondary\t#00FF00\tprimary\t#FF0000"

    def test_color_table_as_json(self):
        """Test formatting color data as JSON."""
        data = (
            TableContent()
            .add_column("color_name", "Color Name")
            .add_column("color_hex", "Color Hex")
            .add_column("complementary_color_name", "Complementary Color Name")
            .add_column("complementary_color_hex", "Complementary Color Hex")
            .add_row(
                color_name="primary",
                color_hex="#FF0000",
                complementary_color_name="secondary",
                complementary_color_hex="#00FF00"
            )
        )

        result = format_as(Reports(data=Report(data=data)), "json")
        parsed = json.loads(result)

        assert parsed == {
            "tables": {
                "data": {
                    "metadata": {"title": None, "description": None, "present_transposed": False},
                    "columns": [
                        {"key": "color_name", "label": "Color Name", "header": False},
                        {"key": "color_hex", "label": "Color Hex", "header": False},
                        {"key": "complementary_color_name", "label": "Complementary Color Name", "header": False},
                        {"key": "complementary_color_hex", "label": "Complementary Color Hex", "header": False}
                    ],
                    "rows": [
                        {
                            "color_name": "primary",
                            "color_hex": "#FF0000",
                            "complementary_color_name": "secondary",
                            "complementary_color_hex": "#00FF00"
                        }
                    ]
                }
            }
        }
