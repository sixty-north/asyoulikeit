"""JSON formatter."""

import json

from asyoulikeit.formatter import Formatter
from asyoulikeit.scalar_data import ScalarContent
from asyoulikeit.tabular_data import DetailLevel, Importance, Reports, TableContent
from asyoulikeit.tree_data import Node, TreeContent


class JsonFormatter(Formatter):
    """JSON formatter for structured data output.

    Outputs data as a JSON object with a top-level ``"reports"`` key
    containing named reports. Each report carries its own ``"metadata"``
    (including a ``"kind"`` discriminator of ``"table"``, ``"tree"``,
    or ``"scalar"``) and a shape-specific payload:

    - table: ``"columns"`` schema + ``"rows"``
    - tree:  ``"columns"`` schema + ``"roots"`` (nested nodes)
    - scalar: just ``"value"``

    Consumers differentiate the shapes via ``metadata.kind`` or
    structurally by which of ``rows`` / ``roots`` / ``value`` is
    present.

    JSON always emits full metadata regardless of the ``header`` flag,
    since the format is self-describing by nature.
    """

    def format(self, reports: Reports) -> str:
        """Format reports as a structured JSON object.

        Args:
            reports: A Reports object containing one or more named reports.

        Returns:
            Pretty-printed JSON string with a top-level ``"reports"`` key.
        """
        rendered = {}
        for report_name, report in reports.items():
            # JSON defaults to showing everything.
            detail_level = report.detail_level
            if detail_level == DetailLevel.AUTO:
                detail_level = DetailLevel.DETAILED

            if isinstance(report.data, TableContent):
                rendered[report_name] = self._format_table(report.data, detail_level)
            elif isinstance(report.data, TreeContent):
                rendered[report_name] = self._format_tree(report.data, detail_level)
            elif isinstance(report.data, ScalarContent):
                rendered[report_name] = self._format_scalar(report.data)
            else:
                raise TypeError(
                    f"JsonFormatter does not know how to render "
                    f"{type(report.data).__name__} content "
                    f"(kind={report.data.kind()!r})"
                )

        return json.dumps({"reports": rendered}, indent=2)

    # -- table --------------------------------------------------------------

    def _format_table(self, data: TableContent, detail_level: DetailLevel) -> dict:
        columns_to_output = (
            data.columns if detail_level == DetailLevel.DETAILED
            else data.essential_columns
        )
        rows_to_output = data.rows_for_detail_level(detail_level)

        return {
            "metadata": {
                "kind": "table",
                "title": data.title,
                "description": data.description,
                "present_transposed": data.present_transposed,
            },
            "columns": [
                {"key": col.key, "label": col.label, "header": col.header}
                for col in columns_to_output
            ],
            "rows": [
                {col.key: row[col.key] for col in columns_to_output}
                for row in rows_to_output
            ],
        }

    # -- tree ---------------------------------------------------------------

    def _format_tree(self, data: TreeContent, detail_level: DetailLevel) -> dict:
        columns_to_output = (
            data.columns if detail_level == DetailLevel.DETAILED
            else data.essential_columns
        )
        visible_roots = [
            self._serialize_node(root, columns_to_output, detail_level)
            for root in data.roots
            if self._node_visible(root, detail_level)
        ]

        return {
            "metadata": {
                "kind": "tree",
                "title": data.title,
                "description": data.description,
            },
            "columns": [
                {"key": col.key, "label": col.label, "header": col.header}
                for col in columns_to_output
            ],
            "roots": visible_roots,
        }

    def _serialize_node(
        self, node: Node, columns, detail_level: DetailLevel
    ) -> dict:
        return {
            "values": {col.key: node.values[col.key] for col in columns},
            "children": [
                self._serialize_node(child, columns, detail_level)
                for child in node.children
                if self._node_visible(child, detail_level)
            ],
        }

    @staticmethod
    def _node_visible(node: Node, detail_level: DetailLevel) -> bool:
        """A node is hidden under --essential iff it's tagged DETAIL."""
        if detail_level == DetailLevel.ESSENTIAL and node.importance == Importance.DETAIL:
            return False
        return True

    # -- scalar -------------------------------------------------------------

    def _format_scalar(self, data: ScalarContent) -> dict:
        return {
            "metadata": {
                "kind": "scalar",
                "title": data.title,
                "description": data.description,
            },
            "value": data.value,
        }
