"""Human-oriented display formatter.

Where ``json`` is structured output for machines and ``tsv`` is tabular output
for machines, ``display`` is presentation for humans: borders, colors, bold
and italic typography. The current implementation uses the Rich library to
render tabular data; when other report shapes (trees, lists) land, this
formatter's responsibility is to present them for human consumption.
"""

from io import StringIO

from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from asyoulikeit.formatter import Formatter
from asyoulikeit.tabular_data import (
    Reports,
    DetailLevel,
    STYLE_FOREGROUND_COLOR,
    STYLE_BACKGROUND_COLOR,
    STYLE_BOLD,
    STYLE_ITALIC,
)


class DisplayFormatter(Formatter):
    """Human-oriented presentation formatter.

    Outputs data as formatted tables with borders and styling using the Rich
    library. Supports titles, descriptions, header columns, and transposed
    presentation.

    Multiple tables are separated by blank lines. Each table uses its own
    TableContent metadata (title/description).
    """

    def format(self, reports: Reports) -> str:
        """Format reports as Rich tables with optional styling.

        Args:
            reports: A Reports object containing one or more named reports

        Returns:
            Formatted table string(s) with borders and styling, separated by blank lines.
            If present_transposed is True for a report, its rows and columns are swapped.
        """
        table_outputs = []

        for report_name, report in reports.items():
            data = report.data
            styles = report.styles
            detail_level = report.detail_level
            header = report.header

            # Transpose if requested
            if data.present_transposed:
                data = data.transpose()
                # Also transpose styles if provided
                if styles:
                    styles = styles.transpose()

            # Table defaults to showing all columns for human readability
            if detail_level == DetailLevel.AUTO:
                detail_level = DetailLevel.DETAILED

            # Filter columns based on detail_level
            columns = (
                data.columns if detail_level == DetailLevel.DETAILED
                else data.essential_columns
            )

            # Filter rows based on detail_level
            rows = data.rows_for_detail_level(detail_level)

            # Create Rich table with optional metadata
            table = Table(
                title=data.title if header else None,
                caption=data.description if header else None,
                show_header=header,
            )

            # Add columns with appropriate styling
            for col in columns:
                if col.header:
                    # Header column gets bold styling
                    table.add_column(col.label, style="bold")
                else:
                    table.add_column(col.label)

            # Add rows with optional styling
            for row in rows:
                if styles:
                    # Find original row index for styles lookup
                    original_idx = data.rows.index(row)
                    style_row = styles.rows[original_idx]
                    rich_cells = []
                    for col in columns:
                        cell_value = str(row[col.key])
                        cell_style_dict = style_row.get(col.key)
                        if cell_style_dict and isinstance(cell_style_dict, dict):
                            cell_style = self._build_rich_style(cell_style_dict)
                            rich_cells.append(Text(cell_value, style=cell_style))
                        else:
                            rich_cells.append(cell_value)
                    table.add_row(*rich_cells)
                else:
                    values = [str(row[col.key]) for col in columns]
                    table.add_row(*values)

            # Capture this table's output to string
            table_outputs.append(self._render_to_string(table))

        # Join tables with blank line separator
        return "\n\n".join(table_outputs)

    def _build_rich_style(self, style_dict: dict) -> Style:
        """Build a Rich Style object from style property dict.

        Args:
            style_dict: Dict with keys like STYLE_FOREGROUND_COLOR, STYLE_BACKGROUND_COLOR, etc.

        Returns:
            Rich Style object
        """
        fg = style_dict.get(STYLE_FOREGROUND_COLOR)
        bg = style_dict.get(STYLE_BACKGROUND_COLOR)
        bold = style_dict.get(STYLE_BOLD, False)
        italic = style_dict.get(STYLE_ITALIC, False)

        return Style(
            color=fg,
            bgcolor=bg,
            bold=bold,
            italic=italic
        )

    def _render_to_string(self, table: Table) -> str:
        """Render a Rich table to a string.

        Args:
            table: The Rich Table object to render

        Returns:
            String representation of the rendered table
        """
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)
        console.print(table)
        return buffer.getvalue()
