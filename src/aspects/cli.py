"""Tabulated output decorator for Click commands.

Provides the :func:`tabulated_output` decorator for commands that produce
formatted report output with support for multiple reports, format selection
(display/TSV/JSON), and column filtering.
"""

import functools
import sys
from collections.abc import Container
from dataclasses import replace
from typing import Callable, Iterable

import click
from click_option_group import OptionGroup

from aspects.formatter import formatter_names, format_as
from aspects.tabular_data import DetailLevel, Reports


class _UniversalContainer(Container):
    """A container that contains everything.

    This container responds True to all containment checks (`x in container`).
    Used in @tabulated_output to represent "show all reports by default".

    Implements the collections.abc.Container protocol.
    """
    def __contains__(self, item):
        """Return True for all containment checks."""
        return True

    def __repr__(self):
        return "ALL_REPORTS"

    def __bool__(self):
        """Container is always truthy."""
        return True


# Module-level constant for "show all reports"
ALL_REPORTS = _UniversalContainer()

# Option group for tabulated output formatting options
TABULATED_OUTPUT_GROUP = OptionGroup('Tabulated Output Options')


def _warn(message: str) -> None:
    """Emit a warning to stderr in a distinctive color."""
    click.secho(message, fg="magenta", err=True)


def tabulated_output(
    func: Callable = None,
    /,
    *,
    default_reports: None | Iterable[str] | _UniversalContainer = ALL_REPORTS
) -> Callable:
    """Decorator factory for commands that return tabular output.

    This decorator adds formatting options and handles output display.
    The decorated function should return:
    - Reports: A Reports object containing one or more named reports
    - None: Silent success (nothing displayed)

    Args:
        func: The function to decorate (when used without parentheses)
        default_reports: Which reports to show by default when no --report flags specified:
            - ALL_REPORTS: Show all reports (default, for reporting commands)
            - None: Show no reports (silent by default, for action commands)
            - Iterable[str]: Show only these named reports by default

    Adds these CLI options:
    - --as: Selects the output format (display, tsv, json)
    - --detailed/--essential: Controls which columns are included (overrides report defaults)
    - --header/--no-header: Controls whether headers are emitted (overrides report defaults)
    - --report: Filters which reports to display (can be specified multiple times)

    The --as option defaults intelligently based on TTY detection.
    The detail level defaults to AUTO, allowing each formatter to decide its default behavior.
    Header behavior is format-specific: TSV prefixes first header cell with "#",
    display omits headers/title/caption, JSON ignores the flag.

    Examples:
        @tabulated_output  # Show all reports (reporting command)
        @tabulated_output(default_reports=ALL_REPORTS)  # Explicit, same as above
        @tabulated_output(default_reports=None)  # Silent by default (action command)
        @tabulated_output(default_reports=["outputs"])  # Show only outputs by default
    """
    # Decorator factory pattern: if called with parentheses, func is None
    if func is None:
        return functools.partial(tabulated_output, default_reports=default_reports)

    # Normalize to Container at decoration time for efficient runtime checking
    if default_reports is ALL_REPORTS:
        # Universal container - contains everything
        processed_default_reports = ALL_REPORTS
    elif default_reports is None:
        # Empty container - contains nothing (silent by default)
        processed_default_reports = frozenset()
    else:
        # Specific reports - frozenset of names
        processed_default_reports = frozenset(default_reports)

    def set_smart_default(ctx, param, value):
        """Set default based on TTY detection if user didn't specify --as."""
        if value is None:
            # User didn't specify --as, use smart default based on TTY
            return "display" if sys.stdout.isatty() else "tsv"
        return value

    def map_detail_level(ctx, param, value):
        """Map tri-state boolean to DetailLevel enum."""
        if value is None:
            return DetailLevel.AUTO
        elif value:
            return DetailLevel.DETAILED
        else:
            return DetailLevel.ESSENTIAL

    # Apply option group for tabulated output formatting
    decorated = TABULATED_OUTPUT_GROUP.option(
        "--report",
        multiple=True,
        help="Report name(s) to display (can be specified multiple times). Shows all if omitted."
    )(
        TABULATED_OUTPUT_GROUP.option(
            "--header/--no-header",
            "header",
            default=None,  # None means use report's default
            help="Include column headers in output. Overrides each report's default. "
                 "Format-specific: TSV prefixes first cell with '#', "
                 "display omits headers/title/caption, JSON ignores this flag.",
        )(
            TABULATED_OUTPUT_GROUP.option(
                "--detailed/--essential",
                "detail_level",
                default=None,
                callback=map_detail_level,
                help="Include detailed columns or only essential columns. "
                     "Auto-detects based on output format if not specified."
            )(
                TABULATED_OUTPUT_GROUP.option(
                    "--as",
                    "as_format",
                    type=click.Choice(formatter_names(), case_sensitive=False),
                    default=None,
                    callback=set_smart_default,
                    help="Output format for tabular data. Defaults to 'display' for terminals, 'tsv' for pipes.",
                )(func)
            )
        )
    )

    # Wrap to consume format parameters and handle output
    @functools.wraps(decorated)
    def wrapper(*args, as_format, detail_level, header, report, **kwargs):
        # Call handler without format parameters
        result = func(*args, **kwargs)

        # Format and display if data returned
        if result is not None:
            # Result must be a Reports object
            if not isinstance(result, Reports):
                raise TypeError(
                    f"Command decorated with @tabulated_output must return Reports or None, "
                    f"not {type(result).__name__}"
                )

            # Determine which reports to show using Container protocol
            if report:
                # User explicitly requested specific reports via --report flag(s)
                report_names_to_show = report
            else:
                # Filter by containment check - works for all three cases:
                # - ALL_REPORTS (universal container): all names pass
                # - frozenset(): no names pass (silent)
                # - frozenset({...}): only specified names pass
                report_names_to_show = [
                    name for name in result.keys()
                    if name in processed_default_reports
                ]

            # Early exit if nothing to show
            if not report_names_to_show:
                if report:
                    # User explicitly requested reports that don't exist
                    _warn(
                        f"No reports matched the requested names: {', '.join(report)}. "
                        f"Available: {', '.join(result.keys())}"
                    )
                # Silent exit (no output)
                return

            # Filter to the selected report names (only include names that actually exist)
            filtered_dict = {name: result[name] for name in report_names_to_show if name in result}

            # Check if user requested reports that don't exist
            if report:
                requested_names = set(report)
                available_names = set(result.keys())
                missing_names = requested_names - available_names
                if missing_names:
                    _warn(
                        f"Report{'s' if len(missing_names) > 1 else ''} not available: {', '.join(sorted(missing_names))}. "
                        f"Available: {', '.join(sorted(available_names))}"
                    )

            # If nothing to show after filtering, exit silently
            if not filtered_dict:
                return

            reports_to_format = Reports(filtered_dict)

            # Apply CLI overrides to report preferences if flags were explicitly set
            if detail_level != DetailLevel.AUTO or header is not None:
                # Override each report's preferences with CLI flags
                overridden_dict = {}
                for name, rep in reports_to_format.items():
                    # Build kwargs for replace() based on which flags were set
                    overrides = {}
                    if detail_level != DetailLevel.AUTO:
                        overrides['detail_level'] = detail_level
                    if header is not None:
                        overrides['header'] = header

                    # Use dataclasses.replace to create modified Report
                    overridden_dict[name] = replace(rep, **overrides) if overrides else rep

                reports_to_format = Reports(overridden_dict)

            # Format and output
            output = format_as(reports_to_format, as_format)
            click.echo(output)

    return wrapper
