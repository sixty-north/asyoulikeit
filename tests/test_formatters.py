"""Tests for formatters."""

import json
import re
import pytest

from asyoulikeit.tabular_data import TableContent, Reports, Report
from asyoulikeit.tree_data import TreeContent
from asyoulikeit.formatter import (
    create_formatter,
    format_as,
    FormatterExtensionError,
)
from asyoulikeit import Importance


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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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
        assert parsed["reports"]["data"]["metadata"]["title"] == "User Report"
        assert parsed["reports"]["data"]["metadata"]["description"] == "Active users in the system"
        assert parsed["reports"]["data"]["metadata"]["present_transposed"] is False

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
        assert parsed["reports"]["data"]["metadata"] == {
            "kind": "table",
            "title": None,
            "description": None,
            "present_transposed": False,
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
        assert parsed["reports"]["data"]["metadata"]["present_transposed"] is True

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
        assert parsed["reports"]["data"]["columns"][0]["header"] is True
        assert parsed["reports"]["data"]["columns"][1]["header"] is False

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
        assert len(parsed["reports"]["data"]["columns"]) == 2
        assert len(parsed["reports"]["data"]["rows"]) == 2
        assert parsed["reports"]["data"]["rows"][0] == {"name": "Alice", "age": 30}
        assert parsed["reports"]["data"]["metadata"]["present_transposed"] is True


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
            "reports": {
                "data": {
                    "metadata": {"kind": "table", "title": None, "description": None, "present_transposed": False},
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


# -----------------------------------------------------------------------------
# TreeContent rendering
# -----------------------------------------------------------------------------

def _tiny_tree() -> TreeContent:
    """A small filesystem-shaped tree used by multiple tests."""
    tree = (
        TreeContent(title="/usr", description="tiny")
        .add_column("name", "Name", header=True)
        .add_column("size", "Size")
        .add_column("kind", "Kind", importance=Importance.DETAIL)
    )
    usr = tree.add_root(name="/usr", size=0, kind="dir")
    bin_dir = usr.add_child(name="bin", size=4096, kind="dir")
    bin_dir.add_child(name="ls", size=150_296, kind="exec")
    bin_dir.add_child(name="cat", size=52_024, kind="exec")
    lib = usr.add_child(name="lib", size=8192, kind="dir")
    lib.add_child(name="libc.so", size=2_000_000, kind="lib")
    return tree


class TestTsvTreeRendering:
    def test_headers_with_comment_prefix(self):
        result = format_as(Reports(fs=Report(data=_tiny_tree())), "tsv")
        assert result.splitlines()[0] == "# Name\tSize"

    def test_depth_indent_on_header_column(self):
        result = format_as(Reports(fs=Report(data=_tiny_tree())), "tsv")
        lines = result.splitlines()
        # TSV defaults to ESSENTIAL → 'kind' column (DETAIL) is dropped.
        assert lines == [
            "# Name\tSize",
            "/usr\t0",
            "  bin\t4096",
            "    ls\t150296",
            "    cat\t52024",
            "  lib\t8192",
            "    libc.so\t2000000",
        ]

    def test_detailed_includes_detail_column(self):
        tree = _tiny_tree()
        report = Report(data=tree)
        # Override via explicit DetailLevel on the report
        from asyoulikeit import DetailLevel
        report = Report(data=tree, detail_level=DetailLevel.DETAILED)
        result = format_as(Reports(fs=report), "tsv")
        lines = result.splitlines()
        assert lines[0] == "# Name\tSize\tKind"
        assert "/usr\t0\tdir" in lines
        assert "  bin\t4096\tdir" in lines

    def test_detail_node_pruned_under_essential(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        root = tree.add_root(name="keep")
        root.add_child(name="essential-child")
        # A DETAIL node and its descendant should both vanish under --essential
        detail_child = root.add_child(name="detail-child", _importance=Importance.DETAIL)
        detail_child.add_child(name="grandchild")

        from asyoulikeit import DetailLevel
        report = Report(data=tree, detail_level=DetailLevel.ESSENTIAL)
        result = format_as(Reports(t=report), "tsv")
        assert "keep" in result
        assert "essential-child" in result
        assert "detail-child" not in result
        assert "grandchild" not in result

    def test_header_flag_off_suppresses_header_row(self):
        report = Report(data=_tiny_tree(), header=False)
        result = format_as(Reports(fs=report), "tsv")
        assert "# Name" not in result
        assert result.splitlines()[0] == "/usr\t0"

    def test_multiple_roots(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        tree.add_root(name="/usr").add_child(name="bin")
        tree.add_root(name="/home").add_child(name="alice")
        result = format_as(Reports(fs=Report(data=tree)), "tsv")
        assert result.splitlines() == [
            "# Name",
            "/usr",
            "  bin",
            "/home",
            "  alice",
        ]


class TestJsonTreeRendering:
    def test_metadata_kind_is_tree(self):
        result = format_as(Reports(fs=Report(data=_tiny_tree())), "json")
        parsed = json.loads(result)
        assert parsed["reports"]["fs"]["metadata"]["kind"] == "tree"

    def test_has_roots_not_rows(self):
        result = format_as(Reports(fs=Report(data=_tiny_tree())), "json")
        parsed = json.loads(result)
        assert "roots" in parsed["reports"]["fs"]
        assert "rows" not in parsed["reports"]["fs"]

    def test_nested_children_structure(self):
        result = format_as(Reports(fs=Report(data=_tiny_tree())), "json")
        parsed = json.loads(result)
        roots = parsed["reports"]["fs"]["roots"]
        assert len(roots) == 1
        usr = roots[0]
        assert usr["values"]["name"] == "/usr"
        child_names = [c["values"]["name"] for c in usr["children"]]
        assert child_names == ["bin", "lib"]
        # bin → ls, cat
        bin_node = usr["children"][0]
        assert [c["values"]["name"] for c in bin_node["children"]] == ["ls", "cat"]
        # leaves have empty children
        assert bin_node["children"][0]["children"] == []

    def test_detail_column_and_node_pruning(self):
        from asyoulikeit import DetailLevel
        tree = (
            TreeContent()
            .add_column("name", "Name", header=True)
            .add_column("note", "Note", importance=Importance.DETAIL)
        )
        root = tree.add_root(name="keep", note="hi")
        root.add_child(name="essential", note="yes")
        root.add_child(name="gone", note="bye", _importance=Importance.DETAIL)

        essential = format_as(
            Reports(t=Report(data=tree, detail_level=DetailLevel.ESSENTIAL)),
            "json",
        )
        parsed = json.loads(essential)
        cols = [c["key"] for c in parsed["reports"]["t"]["columns"]]
        assert cols == ["name"]  # note dropped
        keep = parsed["reports"]["t"]["roots"][0]
        assert "note" not in keep["values"]
        child_names = [c["values"]["name"] for c in keep["children"]]
        assert child_names == ["essential"]  # "gone" pruned


class TestDisplayTreeRendering:
    def _render(self, tree, detail_level=None, header=True):
        import os
        os.environ.setdefault("COLUMNS", "80")
        os.environ.setdefault("NO_COLOR", "1")
        from asyoulikeit import DetailLevel
        kwargs = {}
        if detail_level is not None:
            kwargs["detail_level"] = detail_level
        kwargs["header"] = header
        report = Report(data=tree, **kwargs)
        return strip_ansi_codes(format_as(Reports(t=report), "display"))

    def test_contains_title_and_caption(self):
        result = self._render(_tiny_tree())
        assert "/usr" in result
        assert "tiny" in result

    def test_ascii_art_connectors_present(self):
        result = self._render(_tiny_tree())
        assert "├── bin" in result
        assert "└── lib" in result
        assert "│   ├── ls" in result or "├── ls" in result  # depending on layout
        assert "    └── libc.so" in result or "└── libc.so" in result

    def test_header_flag_off_hides_title_and_column_labels(self):
        result = self._render(_tiny_tree(), header=False)
        # title suppressed
        normalized = normalize_whitespace(result)
        assert "tiny" not in normalized
        # The header row (column labels like 'Name' | 'Size') is suppressed,
        # but the VALUE '/usr' still appears — it's data, not a header.
        assert "/usr" in result

    def test_detail_node_pruning(self):
        tree = TreeContent().add_column("name", "Name", header=True)
        tree.add_root(name="keep").add_child(
            name="hidden", _importance=Importance.DETAIL
        )
        from asyoulikeit import DetailLevel
        result = self._render(tree, detail_level=DetailLevel.ESSENTIAL)
        assert "keep" in result
        assert "hidden" not in result


class TestDisplayTreeChromeDrop:
    """When a sole tree has only the header column, the table chrome is dropped."""

    @staticmethod
    def _single_col_tree(title=None, description=None):
        tree = TreeContent(title=title, description=description).add_column(
            "name", "Name", header=True
        )
        root = tree.add_root(name="image.dat")
        root.add_child(name="ADFS").add_child(name="$")
        root.add_child(name="AFS").add_child(name="$")
        return tree

    @staticmethod
    def _render(reports):
        import os
        os.environ.setdefault("COLUMNS", "80")
        os.environ.setdefault("NO_COLOR", "1")
        return strip_ansi_codes(format_as(reports, "display"))

    def test_solo_single_column_drops_chrome(self):
        tree = self._single_col_tree()
        result = self._render(Reports(fs=Report(data=tree)))
        # No Rich table box — absence of the top-left and bottom-left
        # corners is the reliable signal. (The continuation guide '│'
        # appears in the tree's own ASCII-art, so it isn't diagnostic.)
        assert "┏" not in result
        assert "┗" not in result
        # The column label 'Name' must not appear as a header row.
        assert "Name" not in result
        # ASCII-art connectors are present.
        assert "├── ADFS" in result
        assert "└── AFS" in result

    def test_solo_single_column_with_title_shows_title_as_plain_line(self):
        tree = self._single_col_tree(title="Archive contents")
        result = self._render(Reports(fs=Report(data=tree)))
        assert "Archive contents" in result
        # No Rich title styling / box
        assert "┏" not in result

    def test_solo_single_column_no_header_hides_title(self):
        tree = self._single_col_tree(
            title="Archive contents", description="A caption"
        )
        result = self._render(
            Reports(fs=Report(data=tree, header=False))
        )
        assert "Archive contents" not in result
        assert "A caption" not in result
        # Tree itself still renders.
        assert "image.dat" in result

    def test_solo_two_column_keeps_chrome(self):
        tree = (
            TreeContent(title="Sized")
            .add_column("name", "Name", header=True)
            .add_column("size", "Size")
        )
        tree.add_root(name="image.dat", size=1024).add_child(
            name="ADFS", size=512
        )
        result = self._render(Reports(fs=Report(data=tree)))
        # Two columns → Rich Table is still used.
        assert "┏" in result

    def test_multiple_reports_keep_chrome_even_if_each_is_single_column(self):
        tree1 = TreeContent(title="one").add_column("name", "Name", header=True)
        tree1.add_root(name="alpha")
        tree2 = TreeContent(title="two").add_column("name", "Name", header=True)
        tree2.add_root(name="beta")
        result = self._render(
            Reports(a=Report(data=tree1), b=Report(data=tree2))
        )
        # With two reports, each gets its bordered box so they're visually
        # separable.
        assert result.count("┏") == 2

    def test_essential_detail_level_can_collapse_to_single_column(self):
        """When --essential drops a DETAIL column, the result is single-column
        and the chrome should also drop, even though the source has 2 columns."""
        from asyoulikeit import DetailLevel
        tree = (
            TreeContent(title="Maybe bare")
            .add_column("name", "Name", header=True)
            .add_column("note", "Note", importance=Importance.DETAIL)
        )
        tree.add_root(name="root", note="hi").add_child(
            name="child", note="there"
        )
        result = self._render(
            Reports(
                fs=Report(data=tree, detail_level=DetailLevel.ESSENTIAL)
            )
        )
        # Only the header column survives under --essential, so the tree has
        # a single column at render time — chrome should drop.
        assert "┏" not in result
        assert "├── child" in result or "└── child" in result


class TestFormatterRejectsUnknownContent:
    """Each formatter should raise a clear TypeError for unknown content."""

    def test_all_formatters_reject_custom_content(self):
        from asyoulikeit import ReportContent

        class WidgetContent(ReportContent):
            @classmethod
            def kind(cls) -> str:
                return "widget"

        report = Report(data=WidgetContent())

        for fmt in ("tsv", "json", "display"):
            with pytest.raises(TypeError, match=r"kind='widget'"):
                format_as(Reports(w=report), fmt)


# -----------------------------------------------------------------------------
# ScalarContent rendering
# -----------------------------------------------------------------------------

from asyoulikeit import ScalarContent


class TestTsvScalarRendering:
    """TSV defaults to 'just the value' for scalars, per-content default."""

    def test_bare_value_no_title_no_flag(self):
        result = format_as(
            Reports(x=Report(data=ScalarContent("00001900"))), "tsv"
        )
        assert result == "00001900"

    def test_bare_value_with_title_but_default_header(self):
        """Title set but no explicit header — TSV default is bare."""
        result = format_as(
            Reports(x=Report(data=ScalarContent("00001900", title="Load"))),
            "tsv",
        )
        assert result == "00001900"

    def test_labelled_form_with_explicit_header_true(self):
        """`header=True` on the Report opts into the `# Title\\nvalue` shape."""
        result = format_as(
            Reports(
                x=Report(
                    data=ScalarContent("00001900", title="Load"),
                    header=True,
                )
            ),
            "tsv",
        )
        assert result == "# Load\n00001900"

    def test_explicit_header_false_is_bare_even_if_title_set(self):
        result = format_as(
            Reports(
                x=Report(
                    data=ScalarContent("00001900", title="Load"),
                    header=False,
                )
            ),
            "tsv",
        )
        assert result == "00001900"

    def test_description_never_emitted(self):
        result = format_as(
            Reports(
                x=Report(
                    data=ScalarContent(
                        "00001900", title="Load", description="An address."
                    ),
                    header=True,
                )
            ),
            "tsv",
        )
        assert "An address." not in result
        assert result == "# Load\n00001900"

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("str", "str"),
            (42, "42"),
            (3.14, "3.14"),
            (True, "True"),
            (False, "False"),
            (None, "None"),
        ],
    )
    def test_various_value_types(self, value, expected):
        result = format_as(
            Reports(x=Report(data=ScalarContent(value))), "tsv"
        )
        assert result == expected


class TestJsonScalarRendering:
    def test_shape(self):
        result = format_as(
            Reports(
                load=Report(
                    data=ScalarContent(
                        "00001900", title="Load", description="An address."
                    )
                )
            ),
            "json",
        )
        parsed = json.loads(result)
        assert parsed == {
            "reports": {
                "load": {
                    "metadata": {
                        "kind": "scalar",
                        "title": "Load",
                        "description": "An address.",
                    },
                    "value": "00001900",
                }
            }
        }

    def test_nulls_for_absent_metadata(self):
        result = format_as(
            Reports(x=Report(data=ScalarContent("v"))), "json"
        )
        parsed = json.loads(result)
        assert parsed["reports"]["x"]["metadata"] == {
            "kind": "scalar",
            "title": None,
            "description": None,
        }
        assert parsed["reports"]["x"]["value"] == "v"

    @pytest.mark.parametrize(
        "value",
        ["str", 42, 3.14, True, False, None],
    )
    def test_value_types_roundtrip(self, value):
        result = format_as(
            Reports(x=Report(data=ScalarContent(value))), "json"
        )
        parsed = json.loads(result)
        assert parsed["reports"]["x"]["value"] == value

    def test_header_flag_does_not_affect_json(self):
        """JSON is always self-describing; header is a no-op."""
        sc = ScalarContent("v", title="T")
        r_true = format_as(Reports(x=Report(data=sc, header=True)), "json")
        r_false = format_as(Reports(x=Report(data=sc, header=False)), "json")
        assert r_true == r_false


class TestDisplayScalarRendering:
    @staticmethod
    def _render(report):
        import os
        os.environ.setdefault("COLUMNS", "80")
        os.environ.setdefault("NO_COLOR", "1")
        return strip_ansi_codes(format_as(Reports(x=report), "display"))

    def test_bare_value_no_title(self):
        result = self._render(Report(data=ScalarContent("00001900")))
        assert result.strip() == "00001900"

    def test_labelled_with_title_default_header(self):
        """Default header is True for display → labelled form when title set."""
        result = self._render(
            Report(data=ScalarContent("00001900", title="Load"))
        )
        assert "Load: 00001900" in result

    def test_description_shown_below_when_header_true(self):
        result = self._render(
            Report(
                data=ScalarContent(
                    "00001900", title="Load", description="An address."
                )
            )
        )
        assert "Load: 00001900" in result
        assert "An address." in result

    def test_header_false_hides_title_and_description(self):
        result = self._render(
            Report(
                data=ScalarContent(
                    "00001900", title="Load", description="An address."
                ),
                header=False,
            )
        )
        assert "Load" not in result
        assert "An address." not in result
        # Value itself still shows.
        assert "00001900" in result

    def test_no_title_value_only_regardless_of_header(self):
        """With no title, there's nothing to label — show just value."""
        for header in (True, False, None):
            result = self._render(
                Report(data=ScalarContent("v"), header=header)
            )
            assert result.strip() == "v"


class TestScalarHeaderResolution:
    """Three-tier resolution: CLI > Report.header > formatter default."""

    def test_report_header_none_uses_formatter_default_tsv(self):
        """No opinion on Report → TSV picks False for scalars → bare value."""
        r = Report(data=ScalarContent("v", title="T"))  # header default is None
        assert r.header is None
        assert format_as(Reports(x=r), "tsv") == "v"

    def test_report_header_none_uses_formatter_default_display(self):
        """No opinion on Report → display picks True → labelled if title."""
        import os
        os.environ.setdefault("COLUMNS", "80")
        os.environ.setdefault("NO_COLOR", "1")
        r = Report(data=ScalarContent("v", title="T"))
        out = strip_ansi_codes(format_as(Reports(x=r), "display"))
        assert "T: v" in out

    def test_report_header_true_wins_over_tsv_default(self):
        r = Report(data=ScalarContent("v", title="T"), header=True)
        assert format_as(Reports(x=r), "tsv") == "# T\nv"

    def test_report_header_false_wins_over_display_default(self):
        import os
        os.environ.setdefault("COLUMNS", "80")
        os.environ.setdefault("NO_COLOR", "1")
        r = Report(data=ScalarContent("v", title="T"), header=False)
        out = strip_ansi_codes(format_as(Reports(x=r), "display"))
        assert "T: v" not in out
        assert "v" in out
