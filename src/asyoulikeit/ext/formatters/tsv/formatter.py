"""Tab-separated values formatter."""

from asyoulikeit.formatter import Formatter
from asyoulikeit.tabular_data import DetailLevel, Importance, Reports, TableContent
from asyoulikeit.tree_data import Node, TreeContent


# Each level of depth in a tree indents the header column by this many
# spaces. Plain spaces keep the TSV parseable by awk/cut/grep while
# giving a strong visual hint of structure at the terminal.
_TREE_INDENT = "  "


class TsvFormatter(Formatter):
    """Tab-separated values formatter for UNIX-style processing.

    Outputs data as TSV with optional header rows, suitable for
    ``awk``, ``cut``, ``grep`` and friends. Headers are prefixed with
    ``# `` by default so downstream tools can skip the first line as a
    comment.

    Multiple reports are separated by blank lines. Within a single
    tree report, nodes are flattened in pre-order — the header-column
    value of each node is prefixed with two spaces per level of depth,
    giving a readable but still machine-parseable layout.
    """

    def format(self, reports: Reports) -> str:
        """Format reports as TSV with optional header rows.

        Args:
            reports: A Reports object containing one or more named reports.

        Returns:
            TSV string with reports separated by blank lines.
        """
        sections = []
        for _report_name, report in reports.items():
            detail_level = report.detail_level
            header = self._resolve_header(report)
            # TSV defaults to essential-only for machine parseability
            if detail_level == DetailLevel.AUTO:
                detail_level = DetailLevel.ESSENTIAL

            if isinstance(report.data, TableContent):
                sections.append(
                    self._format_table(report.data, detail_level, header)
                )
            elif isinstance(report.data, TreeContent):
                sections.append(
                    self._format_tree(report.data, detail_level, header)
                )
            else:
                raise TypeError(
                    f"TsvFormatter does not know how to render "
                    f"{type(report.data).__name__} content "
                    f"(kind={report.data.kind()!r})"
                )

        return "\n\n".join(sections)

    # -- header resolution --------------------------------------------------

    def _resolve_header(self, report) -> bool:
        """Resolve the effective header flag for ``report``.

        Returns ``report.header`` if the author set it explicitly to
        ``True`` or ``False``; otherwise falls back to this formatter's
        per-content default.
        """
        if report.header is not None:
            return report.header
        return self._default_header(report.data)

    def _default_header(self, content) -> bool:
        """Per-content default for TSV when neither CLI nor Report author asked.

        For tables and trees the default is ``True`` — the ``# Name\\t…``
        header line and the column labels are what make the TSV output
        parseable by downstream tools. Special cases (e.g. a future
        single-value content kind) can be handled here.
        """
        return True

    # -- table --------------------------------------------------------------

    def _format_table(
        self, data: TableContent, detail_level: DetailLevel, header: bool
    ) -> str:
        if data.present_transposed:
            data = data.transpose()

        columns = (
            data.columns if detail_level == DetailLevel.DETAILED
            else data.essential_columns
        )
        rows = data.rows_for_detail_level(detail_level)

        lines = []
        if header:
            labels = [col.label for col in columns]
            if labels:
                labels[0] = f"# {labels[0]}"
            lines.append("\t".join(labels))
        for row in rows:
            lines.append("\t".join(str(row[col.key]) for col in columns))
        return "\n".join(lines)

    # -- tree ---------------------------------------------------------------

    def _format_tree(
        self, data: TreeContent, detail_level: DetailLevel, header: bool
    ) -> str:
        columns = (
            data.columns if detail_level == DetailLevel.DETAILED
            else data.essential_columns
        )
        header_col = data.header_column  # always present — enforced at add_root

        lines = []
        if header:
            labels = [col.label for col in columns]
            if labels:
                labels[0] = f"# {labels[0]}"
            lines.append("\t".join(labels))

        for depth, node in self._walk(data, detail_level):
            cells = []
            for col in columns:
                value = str(node.values[col.key])
                if col.key == header_col.key:
                    value = _TREE_INDENT * depth + value
                cells.append(value)
            lines.append("\t".join(cells))

        return "\n".join(lines)

    # -- shared helpers -----------------------------------------------------

    @classmethod
    def _walk(cls, data: TreeContent, detail_level: DetailLevel):
        """Yield (depth, node) pairs in pre-order, filtered by detail."""
        for root in data.roots:
            yield from cls._walk_node(root, 0, detail_level)

    @classmethod
    def _walk_node(cls, node: Node, depth: int, detail_level: DetailLevel):
        if not cls._node_visible(node, detail_level):
            return
        yield depth, node
        for child in node.children:
            yield from cls._walk_node(child, depth + 1, detail_level)

    @staticmethod
    def _node_visible(node: Node, detail_level: DetailLevel) -> bool:
        if detail_level == DetailLevel.ESSENTIAL and node.importance == Importance.DETAIL:
            return False
        return True
