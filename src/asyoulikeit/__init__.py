"""Utilities for enriching CLI tools with structured report output."""

__version__ = "0.2.3"

from asyoulikeit.cli import ALL_REPORTS, tabulated_output
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
    TabularData,
)

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
    "Report",
    "Reports",
    "STYLE_ALIGNMENT",
    "STYLE_BACKGROUND_COLOR",
    "STYLE_BOLD",
    "STYLE_FOREGROUND_COLOR",
    "STYLE_ITALIC",
    "STYLE_WIDTH",
    "TabularData",
    "create_formatter",
    "format_as",
    "formatter_names",
    "tabulated_output",
]
