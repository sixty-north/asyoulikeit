"""Human-oriented display formatter.

Where ``json`` is structured output for machines and ``tsv`` is tabular output
for machines, ``display`` is presentation for humans: borders, colors, bold
and italic typography. Both :class:`~asyoulikeit.TableContent` and
:class:`~asyoulikeit.TreeContent` are rendered through Rich; trees get
ASCII-art connectors drawn into the header column of a Rich Table so the
hierarchical shape is visible while other columns still line up as a table.
"""

from io import StringIO
from typing import Optional

from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from asyoulikeit.formatter import Formatter
from asyoulikeit.tabular_data import (
    STYLE_BACKGROUND_COLOR,
    STYLE_BOLD,
    STYLE_FOREGROUND_COLOR,
    STYLE_ITALIC,
    Column,
    DetailLevel,
    Importance,
    Reports,
    TableContent,
)
from asyoulikeit.tree_data import Node, TreeContent


class DisplayFormatter(Formatter):
    """Human-oriented presentation formatter.

    Renders a :class:`~asyoulikeit.TableContent` as a Rich table with
    borders, titles, and optional per-cell styling, and a
    :class:`~asyoulikeit.TreeContent` as the same Rich table with
    ASCII-art tree connectors (``├──``, ``└──``, ``│``) laid into the
    header-column cell of each node.

    Multiple reports are separated by blank lines.
    """

    def format(self, reports: Reports) -> str:
        """Format reports as Rich tables, separated by blank lines."""
        sections = []
        # When only one report is being rendered, certain chrome
        # (bordered box around a single-column tree) stops earning its
        # keep and is dropped. With multiple reports the chrome is what
        # visually separates them, so it's kept.
        solo = len(reports) == 1
        for _report_name, report in reports.items():
            detail_level = report.detail_level
            header = report.header
            # Display defaults to showing all columns.
            if detail_level == DetailLevel.AUTO:
                detail_level = DetailLevel.DETAILED

            if isinstance(report.data, TableContent):
                sections.append(
                    self._format_table(
                        report.data, report.styles, detail_level, header
                    )
                )
            elif isinstance(report.data, TreeContent):
                sections.append(
                    self._format_tree(
                        report.data, detail_level, header, solo=solo
                    )
                )
            else:
                raise TypeError(
                    f"DisplayFormatter does not know how to render "
                    f"{type(report.data).__name__} content "
                    f"(kind={report.data.kind()!r})"
                )

        return "\n\n".join(sections)

    # -- table --------------------------------------------------------------

    def _format_table(
        self,
        data: TableContent,
        styles: Optional[TableContent],
        detail_level: DetailLevel,
        header: bool,
    ) -> str:
        if data.present_transposed:
            data = data.transpose()
            if styles:
                styles = styles.transpose()

        columns = (
            data.columns if detail_level == DetailLevel.DETAILED
            else data.essential_columns
        )
        rows = data.rows_for_detail_level(detail_level)

        table = Table(
            title=data.title if header else None,
            caption=data.description if header else None,
            show_header=header,
        )
        for col in columns:
            if col.header:
                table.add_column(col.label, style="bold")
            else:
                table.add_column(col.label)

        for row in rows:
            if styles:
                original_idx = data.rows.index(row)
                style_row = styles.rows[original_idx]
                rich_cells = []
                for col in columns:
                    cell_value = str(row[col.key])
                    cell_style_dict = style_row.get(col.key)
                    if cell_style_dict and isinstance(cell_style_dict, dict):
                        rich_cells.append(
                            Text(cell_value, style=self._build_rich_style(cell_style_dict))
                        )
                    else:
                        rich_cells.append(cell_value)
                table.add_row(*rich_cells)
            else:
                table.add_row(*[str(row[col.key]) for col in columns])

        return self._render_to_string(table)

    # -- tree ---------------------------------------------------------------

    def _format_tree(
        self,
        data: TreeContent,
        detail_level: DetailLevel,
        header: bool,
        solo: bool = False,
    ) -> str:
        columns = (
            data.columns if detail_level == DetailLevel.DETAILED
            else data.essential_columns
        )
        header_col: Column = data.header_column  # guaranteed by TreeContent

        # Single-column tree with no sibling reports to disambiguate
        # from? The bordered table around the tree adds visual noise
        # without adding information — the ASCII-art connectors
        # already convey hierarchy. Drop the chrome.
        if solo and len(columns) == 1:
            return self._format_tree_bare(data, detail_level, header, header_col)

        non_header_cols = [c for c in columns if not c.header]

        table = Table(
            title=data.title if header else None,
            caption=data.description if header else None,
            show_header=header,
        )
        for col in columns:
            if col.header:
                table.add_column(col.label, style="bold")
            else:
                table.add_column(col.label)

        # Walk the forest and emit (ascii_art, node) pairs.
        rendered = []
        for root in data.roots:
            self._walk_subtree(
                root,
                prefix="",
                is_root=True,
                is_last=True,
                detail_level=detail_level,
                out=rendered,
            )

        for art, node in rendered:
            header_cell = art + str(node.values[header_col.key])
            other_cells = [str(node.values[col.key]) for col in non_header_cols]
            table.add_row(header_cell, *other_cells)

        return self._render_to_string(table)

    def _format_tree_bare(
        self,
        data: TreeContent,
        detail_level: DetailLevel,
        header: bool,
        header_col: Column,
    ) -> str:
        """Emit a single-column tree as bare ASCII art, without table chrome.

        Called only when there's exactly one report and the tree has
        exactly one column, so the bordered table wouldn't add any
        information. Title and description are included as plain lines
        above and below the tree when ``header`` is true.
        """
        rendered: list[tuple[str, Node]] = []
        for root in data.roots:
            self._walk_subtree(
                root,
                prefix="",
                is_root=True,
                is_last=True,
                detail_level=detail_level,
                out=rendered,
            )

        lines = []
        if header and data.title:
            lines.append(data.title)
            lines.append("")
        for art, node in rendered:
            lines.append(art + str(node.values[header_col.key]))
        if header and data.description:
            lines.append("")
            lines.append(data.description)
        # Match the trailing newline that Rich's Console.print adds on
        # the chrome'd path, so callers that concatenate sections with
        # "\n\n" don't see a shape discontinuity between modes.
        return "\n".join(lines) + "\n"

    def _walk_subtree(
        self,
        node: Node,
        prefix: str,
        is_root: bool,
        is_last: bool,
        detail_level: DetailLevel,
        out: list,
    ) -> None:
        """Populate ``out`` with (ascii_art_prefix, node) pairs in pre-order.

        DETAIL nodes (and their descendants) are pruned when
        ``detail_level == ESSENTIAL``.
        """
        if not self._node_visible(node, detail_level):
            return

        if is_root:
            art = ""
            child_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            art = prefix + connector
            child_prefix = prefix + ("    " if is_last else "│   ")

        out.append((art, node))

        visible_children = [
            c for c in node.children if self._node_visible(c, detail_level)
        ]
        for i, child in enumerate(visible_children):
            last = i == len(visible_children) - 1
            self._walk_subtree(
                child,
                child_prefix,
                is_root=False,
                is_last=last,
                detail_level=detail_level,
                out=out,
            )

    @staticmethod
    def _node_visible(node: Node, detail_level: DetailLevel) -> bool:
        if detail_level == DetailLevel.ESSENTIAL and node.importance == Importance.DETAIL:
            return False
        return True

    # -- shared Rich helpers ------------------------------------------------

    def _build_rich_style(self, style_dict: dict) -> Style:
        return Style(
            color=style_dict.get(STYLE_FOREGROUND_COLOR),
            bgcolor=style_dict.get(STYLE_BACKGROUND_COLOR),
            bold=style_dict.get(STYLE_BOLD, False),
            italic=style_dict.get(STYLE_ITALIC, False),
        )

    def _render_to_string(self, table: Table) -> str:
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)
        console.print(table)
        return buffer.getvalue()
