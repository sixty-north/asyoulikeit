"""Utilities for enriching CLI tools with structured report output."""

__version__ = "0.1.0"

from aspects.cli import ALL_REPORTS, tabulated_output
from aspects.exceptions import AspectsError
from aspects.extension import Extension, ExtensionError
from aspects.formatter import (
    Formatter,
    FormatterExtensionError,
    create_formatter,
    format_as,
    formatter_names,
)
from aspects.tabular_data import (
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
    "AspectsError",
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
