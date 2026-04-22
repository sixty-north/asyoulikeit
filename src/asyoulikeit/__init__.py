"""Utilities for enriching CLI tools with structured report output."""

__version__ = "0.2.5"

from asyoulikeit.cli import ALL_REPORTS, report_output
from asyoulikeit.content import ReportContent
from asyoulikeit.exceptions import AsyoulikeitError
from asyoulikeit.extension import Extension, ExtensionError
from asyoulikeit.formatter import (
    Formatter,
    FormatterExtensionError,
    create_formatter,
    format_as,
    formatter_names,
)
from asyoulikeit.tabular_data import (
    STYLE_ALIGNMENT,
    STYLE_BACKGROUND_COLOR,
    STYLE_BOLD,
    STYLE_FOREGROUND_COLOR,
    STYLE_ITALIC,
    STYLE_WIDTH,
    Column,
    DetailLevel,
    Importance,
    Report,
    Reports,
    TableContent,
)
from asyoulikeit.tree_data import Node, TreeContent

__all__ = [
    "ALL_REPORTS",
    "AsyoulikeitError",
    "Column",
    "DetailLevel",
    "Extension",
    "ExtensionError",
    "Formatter",
    "FormatterExtensionError",
    "Importance",
    "Node",
    "Report",
    "ReportContent",
    "Reports",
    "STYLE_ALIGNMENT",
    "STYLE_BACKGROUND_COLOR",
    "STYLE_BOLD",
    "STYLE_FOREGROUND_COLOR",
    "STYLE_ITALIC",
    "STYLE_WIDTH",
    "TableContent",
    "TreeContent",
    "create_formatter",
    "format_as",
    "formatter_names",
    "report_output",
]
