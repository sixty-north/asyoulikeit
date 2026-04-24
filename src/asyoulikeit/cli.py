"""Report output decorator for Click commands.

Provides the :func:`report_output` decorator for commands that produce
formatted report output with support for multiple reports, format selection
(display/TSV/JSON), and column filtering.
"""

import functools
import os
import sys
from collections.abc import Container, Mapping
from dataclasses import replace
from types import EllipsisType
from typing import Callable, Iterable, Optional, Union

import click
from click_option_group import OptionGroup

from asyoulikeit.exceptions import ReportDeclarationError
from asyoulikeit.formatter import describe_formatter, formatter_names, format_as
from asyoulikeit.scalar_data import ScalarContent
from asyoulikeit.tabular_data import DetailLevel, Report, Reports, TableContent


# Environment variable consulted when ``--as`` is not given on the
# command line. Takes precedence over the TTY-based default so that
# test harnesses (where stdout is a captured buffer with isatty() ==
# False) can force a chosen format without touching every test, and
# so that users can set a default in their shell rc-file.
FORMAT_ENV_VAR = "ASYOULIKEIT_FORMAT"


class _UniversalContainer(Container):
    """A container that contains everything.

    This container responds True to all containment checks (`x in container`).
    Used in @report_output to represent "show all reports by default".

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
REPORT_OUTPUT_GROUP = OptionGroup('Report Output Options')


def _warn(message: str) -> None:
    """Emit a warning to stderr in a distinctive color."""
    click.secho(message, fg="magenta", err=True)


def _validate_reports_declaration(
    reports: Mapping[Union[str, EllipsisType], str],
) -> None:
    """Validate the shape of a ``reports=`` mapping at decoration time.

    Each key must be either a valid Python identifier (same contract
    :class:`~asyoulikeit.Reports` enforces on construction) or
    ``Ellipsis`` (the "dynamic slot" sentinel). Anything else — a
    non-identifier string, an integer, a tuple — raises
    :exc:`~asyoulikeit.ReportDeclarationError` so the problem surfaces
    at import time, not on first invocation.
    """
    if not isinstance(reports, Mapping):
        raise ReportDeclarationError(
            f"reports= must be a mapping of name → description, not "
            f"{type(reports).__name__}"
        )
    for key, description in reports.items():
        if key is Ellipsis:
            continue
        if not isinstance(key, str):
            raise ReportDeclarationError(
                f"reports= keys must be strings or Ellipsis; got "
                f"{type(key).__name__} ({key!r})"
            )
        if not key.isidentifier():
            raise ReportDeclarationError(
                f"reports= key {key!r} must be a valid Python identifier "
                "(alphanumeric + underscore, not starting with digit). "
                "Use hyphens on the CLI (--report my-report) and identifiers "
                "here (reports={'my_report': ...}); asyoulikeit maps between "
                "the two automatically."
            )
        if not isinstance(description, str):
            raise ReportDeclarationError(
                f"reports={{{key!r}: ...}} description must be a string, "
                f"not {type(description).__name__}"
            )


def _validate_default_reports_against_declaration(
    default_reports, declared_static: frozenset[str]
) -> None:
    """Cross-check ``default_reports`` against the ``reports=`` declaration.

    Only runs when both are given explicitly and ``default_reports`` is
    an iterable of names (not ``ALL_REPORTS`` / ``None``). Catches the
    silent-typo case where ``default_reports=["summaryy"]`` would
    previously have produced an empty default set at runtime with no
    diagnostic.
    """
    if default_reports is ALL_REPORTS or default_reports is None:
        return
    missing = [
        name for name in default_reports if name not in declared_static
    ]
    if missing:
        raise ReportDeclarationError(
            f"default_reports entries not in the reports= declaration: "
            f"{', '.join(repr(n) for n in missing)}. Declared: "
            f"{', '.join(repr(n) for n in sorted(declared_static)) or '(none static)'}."
        )


def _normalise_report_arg(_ctx, _param, value):
    """Rewrite hyphens to underscores on ``--report`` values.

    CLI convention prefers ``--report monthly-sales``; Python identifiers
    forbid hyphens, so :class:`~asyoulikeit.Reports` keys come out as
    ``monthly_sales``. This callback normalises at the flag boundary so
    users get the CLI convention they expect and handlers keep clean
    identifiers. Applies unconditionally — even without a ``reports=``
    declaration — because a user typing a hyphenated name is always
    trying to reach the equivalent identifier.
    """
    if value is None:
        return value
    # ``multiple=True`` gives us a tuple; the option also accepts None.
    return tuple(v.replace("-", "_") for v in value)


def _build_reports_epilog(
    reports: Mapping[Union[str, EllipsisType], str],
) -> str:
    """Render the ``reports=`` declaration as a "Produces reports:" epilog.

    Static names first (sorted), then ``<dynamic>`` at the end if the
    declaration includes an ``Ellipsis`` slot. Column-aligned for
    readability in ``--help`` output.

    The leading ``\\b`` is Click's no-rewrap marker: without it, Click's
    help formatter collapses the multi-line table into a single flowed
    paragraph. Every rendered line in the block needs the marker at the
    start of its paragraph; a single block at the top suffices because
    we only emit one newline between entries (Click treats consecutive
    \\n-separated lines within the same paragraph as the one to preserve).
    """
    static_names = sorted(k for k in reports.keys() if isinstance(k, str))
    has_dynamic = Ellipsis in reports.keys()
    labels = static_names + (["<dynamic>"] if has_dynamic else [])
    name_width = max(len(label) for label in labels) if labels else 0
    # The "\b" tells Click not to rewrap the block when rendering --help.
    lines = ["\b", "Produces reports:"]
    for name in static_names:
        lines.append(f"  {name.ljust(name_width)}  {reports[name]}")
    if has_dynamic:
        lines.append(f"  {'<dynamic>'.ljust(name_width)}  {reports[Ellipsis]}")
    return "\n".join(lines)


class _ReportChoice(click.Choice):
    """``click.Choice`` variant that accepts hyphen-for-underscore aliases.

    Lets users type ``--report monthly-sales`` even when the declared
    name is ``monthly_sales``. Without this, ``click.Choice`` rejects
    the hyphenated form at parse time (before any callback runs).
    Normalising inside :meth:`convert` means the Choice matches either
    form and always returns the canonical identifier.
    """

    def convert(self, value, param, ctx):
        return super().convert(value.replace("-", "_"), param, ctx)


def _check_drift(
    reports_returned: Reports,
    declaration: Mapping[Union[str, EllipsisType], str],
    command_name: str,
) -> None:
    """Hard-fail if the handler returned a name not in the declaration.

    When a ``reports=`` declaration is present, every returned key must
    either match a declared static name or be admitted by the
    ``Ellipsis`` slot. Undeclared names raise — the refactor-renamed-
    a-report-and-nobody-noticed failure mode was the motivating bug
    behind the declaration feature.
    """
    declared_static = {k for k in declaration.keys() if isinstance(k, str)}
    accepts_dynamic = Ellipsis in declaration.keys()
    undeclared = [
        name for name in reports_returned.keys()
        if name not in declared_static
    ]
    if not undeclared:
        return
    if accepts_dynamic:
        return
    raise ReportDeclarationError(
        f"Command {command_name!r} returned undeclared "
        f"report{'s' if len(undeclared) > 1 else ''}: "
        f"{', '.join(repr(n) for n in undeclared)}. "
        f"Declared: {', '.join(repr(n) for n in sorted(declared_static)) or '(none static)'}. "
        "Add the name(s) to reports={...} or declare reports={..., Ellipsis: \"…\"} "
        "to accept dynamic names."
    )


def report_output(
    func: Callable = None,
    /,
    *,
    default_reports: Union[None, Iterable[str], _UniversalContainer] = ALL_REPORTS,
    reports: Optional[Mapping[Union[str, EllipsisType], str]] = None,
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
        reports: Optional mapping of ``{name: description}`` declaring the
            report names this command produces. Keys must be valid Python
            identifiers; use ``Ellipsis`` as a key to declare "this command
            also produces dynamic reports whose names are known only at
            runtime" (e.g. one report per input file). Declaring ``reports=``
            opts a command into:

            - Decoration-time validation (typos in declared names fail fast).
            - A ``Produces reports:`` block appended to ``--help``.
            - ``click.Choice`` on ``--report`` when the declaration is fully
              static (no ``Ellipsis``), so typos fail at parse with a list of
              valid values.
            - Runtime drift detection: a returned :class:`Reports` containing
              a name that isn't declared (and isn't admitted by an
              ``Ellipsis`` slot) raises :exc:`ReportDeclarationError`.

            Omitting ``reports=`` preserves today's free-form behaviour —
            unknown ``--report`` values warn to stderr and exit silently.

    Adds these CLI options:
    - --as: Selects the output format (display, tsv, json)
    - --detailed/--essential: Controls which columns are included (overrides report defaults)
    - --header/--no-header: Controls whether headers are emitted (overrides report defaults)
    - --report: Filters which reports to display (can be specified multiple times).
      Hyphens in values are normalised to underscores (``--report monthly-sales``
      resolves to the ``monthly_sales`` report) regardless of whether
      ``reports=`` is declared.

    The --as option defaults intelligently based on TTY detection.
    The detail level defaults to AUTO, allowing each formatter to decide its default behavior.
    Header behavior is format-specific: TSV prefixes first header cell with "#",
    display omits headers/title/caption, JSON ignores the flag.

    Examples:
        @report_output  # Show all reports (reporting command)
        @report_output(default_reports=ALL_REPORTS)  # Explicit, same as above
        @report_output(default_reports=None)  # Silent by default (action command)
        @report_output(default_reports=["outputs"])  # Show only outputs by default
        @report_output(reports={"summary": "Site-wide totals",
                                "courses": "Per-course breakdown"})
        @report_output(reports={..., "overall": "Global summary",
                                Ellipsis: "One report per input file"})
    """
    # Decorator factory pattern: if called with parentheses, func is None
    if func is None:
        return functools.partial(
            report_output,
            default_reports=default_reports,
            reports=reports,
        )

    # Validate the reports= declaration shape first so typos in the
    # decoration surface before default_reports is checked against it.
    if reports is not None:
        _validate_reports_declaration(reports)
        declared_static = frozenset(
            k for k in reports.keys() if isinstance(k, str)
        )
        _validate_default_reports_against_declaration(
            default_reports, declared_static
        )
        accepts_dynamic_reports = Ellipsis in reports.keys()
    else:
        declared_static = frozenset()
        accepts_dynamic_reports = True  # back-compat: no declaration = permissive

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
        """Resolve ``--as`` with this precedence, highest first:

        1. An explicit ``--as`` value on the command line.
        2. The ``ASYOULIKEIT_FORMAT`` environment variable.
        3. A TTY-sensing default: ``display`` when stdout is a terminal,
           ``tsv`` when it is a pipe.
        """
        if value is not None:
            return value
        env_value = os.environ.get(FORMAT_ENV_VAR)
        if env_value:
            valid = formatter_names()
            # Case-insensitive match, to mirror click.Choice(case_sensitive=False)
            # on the --as option itself.
            for name in valid:
                if name.lower() == env_value.lower():
                    return name
            raise click.BadParameter(
                f"{FORMAT_ENV_VAR}={env_value!r} is not a known format. "
                f"Available: {', '.join(sorted(valid))}.",
                ctx=ctx,
                param=param,
            )
        return "display" if sys.stdout.isatty() else "tsv"

    def map_detail_level(ctx, param, value):
        """Map tri-state boolean to DetailLevel enum."""
        if value is None:
            return DetailLevel.AUTO
        elif value:
            return DetailLevel.DETAILED
        else:
            return DetailLevel.ESSENTIAL

    # Build the --report option type. When the declaration is fully
    # static (no Ellipsis), use click.Choice so typos fail at parse
    # with a clean error listing valid names. Otherwise fall back to
    # plain strings so dynamic names still pass through.
    if reports is not None and not accepts_dynamic_reports and declared_static:
        report_type = _ReportChoice(sorted(declared_static))
        report_help = (
            "Report name(s) to display (can be specified multiple times). "
            "Shows all if omitted. Valid values: "
            f"{', '.join(sorted(declared_static))}."
        )
    else:
        report_type = None
        report_help = (
            "Report name(s) to display (can be specified multiple times). "
            "Shows all if omitted. Hyphens are normalised to underscores."
        )

    # Apply option group for tabulated output formatting
    decorated = REPORT_OUTPUT_GROUP.option(
        "--report",
        multiple=True,
        type=report_type,
        callback=_normalise_report_arg,
        help=report_help,
    )(
        REPORT_OUTPUT_GROUP.option(
            "--header/--no-header",
            "header",
            default=None,  # None means use report's default
            help="Include column headers in output. Overrides each report's default. "
                 "Format-specific: TSV prefixes first cell with '#', "
                 "display omits headers/title/caption, JSON ignores this flag.",
        )(
            REPORT_OUTPUT_GROUP.option(
                "--detailed/--essential",
                "detail_level",
                default=None,
                callback=map_detail_level,
                help="Include detailed columns or only essential columns. "
                     "Auto-detects based on output format if not specified."
            )(
                REPORT_OUTPUT_GROUP.option(
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
                    f"Command decorated with @report_output must return Reports or None, "
                    f"not {type(result).__name__}"
                )

            # Drift detection: when a reports= declaration exists, any
            # returned name that isn't in the declared static set (and
            # isn't admitted by an Ellipsis slot) is a hard failure.
            # Declaration-less commands skip this check entirely.
            if reports is not None:
                _check_drift(
                    result,
                    reports,
                    command_name=(func.__name__ or "<anonymous>").replace("_", "-"),
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

    # Attach the declaration to the wrapper so the introspection
    # factories can read it via a well-known attribute name once Click
    # wraps the function as a Command.
    wrapper._asyoulikeit_reports = reports

    # Extend the docstring with the "Produces reports:" section so it
    # appears in Click's --help output. Click only reads its `epilog`
    # from the @click.command() kwarg, which we can't set from inside
    # this decorator — the docstring is the one surface we can influence
    # that Click actually renders.
    if reports is not None:
        epilog = _build_reports_epilog(reports)
        existing_doc = (wrapper.__doc__ or "").rstrip()
        wrapper.__doc__ = (
            f"{existing_doc}\n\n{epilog}\n" if existing_doc else f"{epilog}\n"
        )

    return wrapper


def list_formatters_command() -> click.Command:
    """Return a Click command that lists the available report-output formatters.

    The returned command is decorated with :func:`report_output` — so it
    inherits ``--as / --report / --header / --detailed`` and renders
    identically to any other asyoulikeit command. Its payload is a
    two-column :class:`~asyoulikeit.TableContent` (``Name``,
    ``Description``) with one row per registered formatter. The
    description is the formatter class's one-line summary (first
    non-empty line of its docstring).

    The host CLI adds it to its group under whatever name it prefers::

        cli.add_command(list_formatters_command(), name="list-formatters")

    Because ``formatter_names()`` is evaluated at factory-call time (not
    at import time), any formatter that was registered via entry point
    before the factory is called will appear in the listing and in
    ``--as``'s choices.
    """
    @click.command()
    @report_output
    def list_formatters():
        """List the available report output formatters."""
        table = (
            TableContent(title="Available formatters")
            .add_column("name", "Name")
            .add_column("description", "Description")
        )
        for name in sorted(formatter_names()):
            table.add_row(
                name=name,
                description=describe_formatter(name, single_line=True),
            )
        return Reports(formatters=Report(data=table))
    return list_formatters


def describe_formatter_command() -> click.Command:
    """Return a Click command that prints one formatter's full description.

    The returned command is decorated with :func:`report_output` and
    takes a single positional ``NAME`` argument restricted (via
    ``click.Choice``) to the set of currently-registered formatters.
    The payload is a :class:`~asyoulikeit.ScalarContent` whose
    ``value`` is the full cleaned docstring and whose ``title`` is the
    formatter name — so ``--as tsv`` yields the bare description
    (pipe-friendly), ``--as json`` yields
    ``{"metadata": {"title": "<name>"}, "value": "<desc>"}``, and
    ``--as display`` yields ``<name>: <desc>``.

    The host adds it under whatever name suits its CLI::

        cli.add_command(describe_formatter_command(), name="describe-formatter")
    """
    @click.command()
    @click.argument(
        "name",
        type=click.Choice(formatter_names(), case_sensitive=False),
    )
    @report_output
    def describe(name: str):
        """Describe a specific report output formatter."""
        return Reports(formatter=Report(data=ScalarContent(
            value=describe_formatter(name),
            title=name,
        )))
    return describe
