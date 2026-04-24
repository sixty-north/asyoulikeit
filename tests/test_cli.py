"""Tests for the ``report_output`` decorator.

These tests define synthetic Click commands inside each test function so that
every assertion exercises the full path: decorator → handler → Reports →
dispatcher → formatter → stdout.
"""

import json

import click
import pytest
from click.testing import CliRunner

from asyoulikeit.cli import ALL_REPORTS, report_output
from asyoulikeit.tabular_data import (
    DetailLevel,
    Importance,
    Report,
    Reports,
    TableContent,
)


def _make_people_reports() -> Reports:
    """A Reports with two named reports and a mix of importance tags."""
    people = (
        TableContent()
        .add_column("name", "Name")
        .add_column("age", "Age")
        .add_column("notes", "Notes", importance=Importance.DETAIL)
        .add_row(name="Alice", age=30, notes="essential row")
        .add_row(name="Bob", age=25, notes="detail row", _importance=Importance.DETAIL)
    )
    colors = (
        TableContent()
        .add_column("color", "Color")
        .add_row(color="red")
        .add_row(color="green")
    )
    return Reports(
        people=Report(data=people),
        colors=Report(data=colors),
    )


class TestFormatSelection:
    """Tests for the --as option dispatching to the correct formatter."""

    def test_as_tsv_output_shape(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0
        # Two tables separated by a blank line; TSV defaults to ESSENTIAL,
        # so the 'notes' DETAIL column and Bob's DETAIL row are both filtered out.
        assert "# Name\tAge" in result.output
        assert "Alice\t30" in result.output
        assert "Bob" not in result.output
        assert "notes" not in result.output.lower()
        # The colors table is also present.
        assert "# Color" in result.output
        assert "red" in result.output
        assert "green" in result.output

    def test_as_json_output_shape(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert set(parsed["reports"].keys()) == {"people", "colors"}
        # JSON defaults to DETAILED, so 'notes' column and Bob's DETAIL row appear.
        people_cols = [c["key"] for c in parsed["reports"]["people"]["columns"]]
        assert people_cols == ["name", "age", "notes"]
        people_rows = parsed["reports"]["people"]["rows"]
        assert {r["name"] for r in people_rows} == {"Alice", "Bob"}

    def test_as_display_renders(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "display"])
        assert result.exit_code == 0
        assert "Alice" in result.output
        assert "red" in result.output


class TestSmartDefaultFormat:
    """Tests for the TTY-sensitive default for --as."""

    def test_default_is_tsv_when_not_a_tty(self):
        """CliRunner's captured stdout reports isatty() == False, so default is tsv."""
        @click.command()
        @report_output
        def cmd():
            data = TableContent().add_column("x", "X").add_row(x=1)
            return Reports(only=Report(data=data))

        result = CliRunner().invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.startswith("# X\n1")

    def test_default_is_display_when_a_tty(self, monkeypatch):
        """Forcing isatty() True should flip the default to 'display'."""
        import types

        # CliRunner swaps sys.stdout during invoke, so monkeypatching the real
        # sys.stdout has no effect inside the command. Instead, rebind the
        # `sys` name inside asyoulikeit.cli to a fake whose stdout.isatty()
        # returns True — the smart-default callback reads that reference.
        fake_sys = types.SimpleNamespace(
            stdout=types.SimpleNamespace(isatty=lambda: True)
        )
        monkeypatch.setattr("asyoulikeit.cli.sys", fake_sys)

        @click.command()
        @report_output
        def cmd():
            data = TableContent().add_column("x", "X").add_row(x=1)
            return Reports(only=Report(data=data))

        result = CliRunner().invoke(cmd, [])
        assert result.exit_code == 0
        assert "X" in result.output
        # A leading "# X" is the TSV signature; display output never produces it.
        assert not result.output.startswith("# X")


class TestFormatEnvVarOverride:
    """Tests for the ASYOULIKEIT_FORMAT env-var override.

    Precedence: explicit --as > ASYOULIKEIT_FORMAT > TTY-based default.
    """

    @staticmethod
    def _cmd():
        @click.command()
        @report_output
        def cmd():
            data = TableContent().add_column("x", "X").add_row(x=1)
            return Reports(only=Report(data=data))
        return cmd

    def test_env_var_beats_tty_default(self, monkeypatch):
        """Env var forces display even though CliRunner reports isatty=False."""
        monkeypatch.setenv("ASYOULIKEIT_FORMAT", "display")
        result = CliRunner().invoke(self._cmd(), [])
        assert result.exit_code == 0
        # Display output never starts with the TSV '# X' signature.
        assert not result.output.startswith("# X")
        assert "X" in result.output

    def test_env_var_forces_tsv(self, monkeypatch):
        """Env var forces tsv explicitly (equivalent to the default here, but
        proves the mechanism picks up non-default values too)."""
        monkeypatch.setenv("ASYOULIKEIT_FORMAT", "json")
        result = CliRunner().invoke(self._cmd(), [])
        assert result.exit_code == 0
        # JSON output starts with '{'; TSV would start with '# X'.
        assert result.output.lstrip().startswith("{")

    def test_explicit_cli_as_beats_env_var(self, monkeypatch):
        """--as on the command line takes precedence over ASYOULIKEIT_FORMAT."""
        monkeypatch.setenv("ASYOULIKEIT_FORMAT", "json")
        result = CliRunner().invoke(self._cmd(), ["--as", "tsv"])
        assert result.exit_code == 0
        assert result.output.startswith("# X\n1")

    def test_case_insensitive_match(self, monkeypatch):
        """Env var value is matched case-insensitively, mirroring click.Choice."""
        monkeypatch.setenv("ASYOULIKEIT_FORMAT", "DISPLAY")
        result = CliRunner().invoke(self._cmd(), [])
        assert result.exit_code == 0
        assert not result.output.startswith("# X")

    def test_empty_env_var_falls_through_to_tty_default(self, monkeypatch):
        """An empty string in the env var should be treated as 'not set'."""
        monkeypatch.setenv("ASYOULIKEIT_FORMAT", "")
        result = CliRunner().invoke(self._cmd(), [])
        assert result.exit_code == 0
        # Falls through to TTY default — CliRunner's buffer isn't a tty, so tsv.
        assert result.output.startswith("# X\n1")

    def test_invalid_env_var_raises_clear_error(self, monkeypatch):
        """An unknown format in ASYOULIKEIT_FORMAT fails with a helpful message."""
        monkeypatch.setenv("ASYOULIKEIT_FORMAT", "xml")
        result = CliRunner().invoke(self._cmd(), [])
        assert result.exit_code != 0
        # Click renders BadParameter into stderr with the message; check the
        # exception carries the right context.
        assert "ASYOULIKEIT_FORMAT" in str(result.output) + str(result.stderr)
        assert "xml" in str(result.output) + str(result.stderr)


class TestHeaderToggle:
    """Tests for --header / --no-header."""

    def test_header_on_by_default(self):
        @click.command()
        @report_output
        def cmd():
            data = TableContent().add_column("x", "X").add_row(x=1)
            return Reports(only=Report(data=data))

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert "# X" in result.output

    def test_no_header_suppresses_tsv_header_row(self):
        @click.command()
        @report_output
        def cmd():
            data = TableContent().add_column("x", "X").add_row(x=1)
            return Reports(only=Report(data=data))

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--no-header"])
        assert "# X" not in result.output
        assert result.output.strip() == "1"

    def test_scalar_tsv_defaults_to_bare_value(self):
        """A ScalarContent in TSV mode renders just the value by default,
        even with a title set — the format's per-content default wins."""
        from asyoulikeit import ScalarContent

        @click.command()
        @report_output
        def cmd():
            return Reports(
                load=Report(data=ScalarContent("00001900", title="Load"))
            )

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0
        assert result.output.strip() == "00001900"
        assert "Load" not in result.output

    def test_scalar_tsv_with_explicit_header_shows_label(self):
        """`--header` on the CLI opts into the `# Title\\nvalue` form."""
        from asyoulikeit import ScalarContent

        @click.command()
        @report_output
        def cmd():
            return Reports(
                load=Report(data=ScalarContent("00001900", title="Load"))
            )

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--header"])
        assert result.exit_code == 0
        assert "# Load" in result.output
        assert "00001900" in result.output


class TestDetailLevelFiltering:
    """Tests for --detailed / --essential overriding the default."""

    def test_detailed_includes_detail_columns_and_rows_in_tsv(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--detailed"])
        assert result.exit_code == 0
        # With --detailed, TSV now shows the DETAIL column and DETAIL row.
        assert "Notes" in result.output
        assert "Bob" in result.output
        assert "detail row" in result.output

    def test_essential_excludes_detail_columns_and_rows_in_json(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "json", "--essential"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        people_cols = [c["key"] for c in parsed["reports"]["people"]["columns"]]
        # 'notes' is DETAIL, so it's filtered out when --essential forces the level.
        assert people_cols == ["name", "age"]
        people_rows = parsed["reports"]["people"]["rows"]
        assert {r["name"] for r in people_rows} == {"Alice"}


class TestReportSelection:
    """Tests for --report restricting which reports are emitted."""

    def test_report_flag_restricts_output(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--report", "colors"])
        assert result.exit_code == 0
        assert "# Color" in result.output
        assert "red" in result.output
        assert "# Name" not in result.output
        assert "Alice" not in result.output

    def test_unknown_report_emits_warning_and_exits(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--report", "nope"])
        assert result.exit_code == 0
        # No report data rendered.
        assert "Alice" not in result.output
        assert "red" not in result.output
        # Warning goes to stderr (Click 8.2+ always separates streams).
        assert "nope" in result.stderr
        assert "Available" in result.stderr

    def test_report_flag_can_be_specified_multiple_times(self):
        @click.command()
        @report_output
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(
            cmd, ["--as", "tsv", "--report", "people", "--report", "colors"]
        )
        assert result.exit_code == 0
        assert "# Name" in result.output
        assert "# Color" in result.output


class TestDefaultReportsOption:
    """Tests for the decorator's default_reports argument."""

    def test_silent_by_default_when_none(self):
        """@report_output(default_reports=None) produces no output by default."""
        @click.command()
        @report_output(default_reports=None)
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0
        assert result.output == ""

    def test_silent_mode_still_honors_report_flag(self):
        @click.command()
        @report_output(default_reports=None)
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--report", "colors"])
        assert result.exit_code == 0
        assert "# Color" in result.output
        assert "# Name" not in result.output

    def test_named_default_reports_limits_output(self):
        @click.command()
        @report_output(default_reports=["colors"])
        def cmd():
            return _make_people_reports()

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0
        assert "# Color" in result.output
        assert "# Name" not in result.output

    def test_all_reports_sentinel_is_default(self):
        """@report_output and @report_output(default_reports=ALL_REPORTS)
        produce the same output."""
        @click.command()
        @report_output
        def bare():
            return _make_people_reports()

        @click.command()
        @report_output(default_reports=ALL_REPORTS)
        def explicit():
            return _make_people_reports()

        r1 = CliRunner().invoke(bare, ["--as", "tsv"])
        r2 = CliRunner().invoke(explicit, ["--as", "tsv"])
        assert r1.exit_code == 0
        assert r2.exit_code == 0
        assert r1.output == r2.output


class TestReturnContract:
    """Tests for the handler's return-value contract."""

    def test_none_return_produces_no_output(self):
        @click.command()
        @report_output
        def cmd():
            return None

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0
        assert result.output == ""

    def test_non_reports_return_raises_type_error(self):
        @click.command()
        @report_output
        def cmd():
            return "not a Reports"

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code != 0
        assert isinstance(result.exception, TypeError)
        assert "must return Reports or None" in str(result.exception)


class TestReportOverrides:
    """Tests that CLI flags override per-report preferences."""

    def test_header_flag_overrides_report_header_preference(self):
        """A report with header=True is overridden by --no-header."""
        @click.command()
        @report_output
        def cmd():
            data = TableContent().add_column("x", "X").add_row(x=1)
            return Reports(only=Report(data=data, header=True))

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--no-header"])
        assert "# X" not in result.output
        assert result.output.strip() == "1"

    def test_detail_level_flag_overrides_report_detail_preference(self):
        """A report asking for ESSENTIAL is overridden by --detailed."""
        @click.command()
        @report_output
        def cmd():
            data = (
                TableContent()
                .add_column("name", "Name")
                .add_column("note", "Note", importance=Importance.DETAIL)
                .add_row(name="Alice", note="hello")
            )
            return Reports(only=Report(data=data, detail_level=DetailLevel.ESSENTIAL))

        result = CliRunner().invoke(cmd, ["--as", "tsv", "--detailed"])
        assert "Note" in result.output
        assert "hello" in result.output


class TestReportsDeclarationValidation:
    """Decoration-time validation of the reports= declaration."""

    def test_non_identifier_key_rejected(self):
        from asyoulikeit import ReportDeclarationError
        with pytest.raises(ReportDeclarationError) as excinfo:
            @report_output(reports={"bad-name": "no"})
            def cmd(): ...
        assert "bad-name" in str(excinfo.value)
        assert "identifier" in str(excinfo.value)

    def test_starting_digit_rejected(self):
        from asyoulikeit import ReportDeclarationError
        with pytest.raises(ReportDeclarationError):
            @report_output(reports={"1st": "no"})
            def cmd(): ...

    def test_non_string_non_ellipsis_key_rejected(self):
        from asyoulikeit import ReportDeclarationError
        with pytest.raises(ReportDeclarationError) as excinfo:
            @report_output(reports={42: "no"})
            def cmd(): ...
        assert "int" in str(excinfo.value) or "42" in str(excinfo.value)

    def test_non_string_description_rejected(self):
        from asyoulikeit import ReportDeclarationError
        with pytest.raises(ReportDeclarationError):
            @report_output(reports={"summary": 42})
            def cmd(): ...

    def test_non_mapping_rejected(self):
        from asyoulikeit import ReportDeclarationError
        with pytest.raises(ReportDeclarationError):
            @report_output(reports=["summary", "courses"])
            def cmd(): ...

    def test_ellipsis_key_accepted(self):
        # Should not raise.
        @report_output(reports={Ellipsis: "Dynamic names"})
        def cmd(): ...

    def test_mixed_static_and_ellipsis_accepted(self):
        @report_output(reports={"overall": "Fixed", Ellipsis: "Dynamic"})
        def cmd(): ...

    def test_default_reports_must_be_in_declaration(self):
        from asyoulikeit import ReportDeclarationError
        with pytest.raises(ReportDeclarationError) as excinfo:
            @report_output(
                reports={"summary": "Totals", "courses": "Courses"},
                default_reports=["summaryy"],  # typo
            )
            def cmd(): ...
        assert "summaryy" in str(excinfo.value)

    def test_default_reports_subset_of_declaration_accepted(self):
        @report_output(
            reports={"summary": "Totals", "courses": "Courses"},
            default_reports=["summary"],
        )
        def cmd(): ...


class TestReportsDeclarationHelp:
    """The "Produces reports:" block appended to --help."""

    def test_static_declaration_appears_in_help(self):
        @click.command()
        @report_output(reports={
            "summary": "Site-wide totals",
            "courses": "Per-course breakdown",
        })
        def cmd():
            """Run the thing."""

        result = CliRunner().invoke(cmd, ["--help"])
        # Click's formatter preserves our \b-marked block, so the header
        # and each row appear on their own lines.
        assert "Produces reports:" in result.output
        assert "summary" in result.output
        assert "Site-wide totals" in result.output
        assert "courses" in result.output
        assert "Per-course breakdown" in result.output

    def test_ellipsis_slot_renders_as_dynamic(self):
        @click.command()
        @report_output(reports={"fixed": "Fixed part", Ellipsis: "Per-input dynamic"})
        def cmd(): ...

        result = CliRunner().invoke(cmd, ["--help"])
        assert "<dynamic>" in result.output
        assert "Per-input dynamic" in result.output

    def test_declaration_less_command_has_no_produces_block(self):
        @click.command()
        @report_output
        def cmd():
            """A plain command."""

        result = CliRunner().invoke(cmd, ["--help"])
        assert "Produces reports:" not in result.output


class TestReportChoiceValidation:
    """--report option type is click.Choice when the declaration is fully static."""

    def _static_cmd(self):
        @click.command()
        @report_output(reports={"summary": "s", "courses": "c"})
        def cmd():
            return Reports(
                summary=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
                courses=Report(data=TableContent().add_column("k", "k").add_row(k="y")),
            )
        return cmd

    def _dynamic_cmd(self):
        @click.command()
        @report_output(reports={"fixed": "f", Ellipsis: "dyn"})
        def cmd():
            return Reports(
                fixed=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
                one=Report(data=TableContent().add_column("k", "k").add_row(k="y")),
            )
        return cmd

    def test_static_declaration_rejects_unknown_name_at_parse(self):
        cmd = self._static_cmd()
        result = CliRunner().invoke(cmd, ["--report", "nope"])
        assert result.exit_code != 0
        assert "nope" in result.output
        assert "summary" in result.output  # shown as valid
        assert "courses" in result.output

    def test_static_declaration_accepts_declared_name(self):
        cmd = self._static_cmd()
        result = CliRunner().invoke(cmd, ["--report", "summary", "--as", "tsv"])
        assert result.exit_code == 0

    def test_dynamic_declaration_does_not_use_click_choice(self):
        cmd = self._dynamic_cmd()
        # Dynamic commands allow any name through — the handler gets to decide.
        result = CliRunner().invoke(cmd, ["--report", "any_name", "--as", "tsv"])
        # Unknown name at runtime → current behaviour: warn to stderr, exit 0.
        assert result.exit_code == 0

    def test_declaration_less_command_keeps_free_form_behaviour(self):
        @click.command()
        @report_output
        def cmd():
            return Reports(a=Report(data=TableContent().add_column("k", "k").add_row(k="x")))

        result = CliRunner().invoke(cmd, ["--report", "b"])
        # Legacy: unknown --report warns, exits 0.
        assert result.exit_code == 0


class TestReportHyphenNormalisation:
    """--report monthly-sales must resolve to the declared monthly_sales."""

    def test_static_declaration_accepts_hyphen_form(self):
        @click.command()
        @report_output(reports={"monthly_sales": "Monthly"})
        def cmd():
            return Reports(
                monthly_sales=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
            )

        result = CliRunner().invoke(cmd, ["--report", "monthly-sales", "--as", "tsv"])
        assert result.exit_code == 0
        assert "x" in result.output

    def test_declaration_less_command_also_normalises(self):
        @click.command()
        @report_output
        def cmd():
            return Reports(
                monthly_sales=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
            )

        result = CliRunner().invoke(cmd, ["--report", "monthly-sales", "--as", "tsv"])
        assert result.exit_code == 0
        assert "x" in result.output


class TestReportsDriftDetection:
    """Handlers returning names outside the declaration fail loudly."""

    def test_undeclared_report_raises_with_static_declaration(self):
        from asyoulikeit import ReportDeclarationError

        @click.command()
        @report_output(reports={"summary": "s"})
        def cmd():
            return Reports(
                summary=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
                extra=Report(data=TableContent().add_column("k", "k").add_row(k="y")),
            )

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code != 0
        assert isinstance(result.exception, ReportDeclarationError)
        assert "extra" in str(result.exception)

    def test_declared_report_returned_does_not_raise(self):
        @click.command()
        @report_output(reports={"summary": "s"})
        def cmd():
            return Reports(
                summary=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
            )

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0

    def test_ellipsis_slot_admits_any_name(self):
        @click.command()
        @report_output(reports={"fixed": "f", Ellipsis: "dyn"})
        def cmd():
            return Reports(
                fixed=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
                whatever=Report(data=TableContent().add_column("k", "k").add_row(k="y")),
            )

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0

    def test_declaration_less_command_does_not_drift_check(self):
        # Back-compat: no declaration → no drift detection, silent warn on --report.
        @click.command()
        @report_output
        def cmd():
            return Reports(
                anything=Report(data=TableContent().add_column("k", "k").add_row(k="x")),
                at_all=Report(data=TableContent().add_column("k", "k").add_row(k="y")),
            )

        result = CliRunner().invoke(cmd, ["--as", "tsv"])
        assert result.exit_code == 0

    def test_declaration_metadata_attached_to_wrapper(self):
        # The introspection factories (see #7 Commit B) read this attr.
        @report_output(reports={"summary": "s"})
        def cmd():
            return Reports()

        declaration = cmd._asyoulikeit_reports
        assert declaration == {"summary": "s"}


class TestListFormattersCommand:
    """Factory that returns a 'list registered formatters' Click command."""

    def _make_cli(self):
        from asyoulikeit import list_formatters_command

        @click.group()
        def cli():
            pass

        cli.add_command(list_formatters_command(), name="list-formatters")
        return cli

    def test_factory_returns_click_command(self):
        from asyoulikeit import list_formatters_command
        cmd = list_formatters_command()
        assert isinstance(cmd, click.Command)

    def test_tsv_output_has_one_row_per_registered_formatter(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["list-formatters", "--as", "tsv"])
        assert result.exit_code == 0, result.output
        lines = result.output.strip().splitlines()
        # Header + one row per built-in (display, json, tsv)
        assert lines[0] == "# Name\tDescription"
        data_lines = lines[1:]
        assert len(data_lines) == 3
        names = sorted(line.split("\t")[0] for line in data_lines)
        assert names == ["display", "json", "tsv"]

    def test_tsv_description_is_single_line(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["list-formatters", "--as", "tsv"])
        # Each row must have exactly 2 cells; multi-line docstrings must have
        # collapsed to their first line.
        for line in result.output.strip().splitlines()[1:]:
            assert line.count("\t") == 1

    def test_json_output_shape(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["list-formatters", "--as", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        report = parsed["reports"]["formatters"]
        assert report["metadata"]["kind"] == "table"
        names = sorted(row["name"] for row in report["rows"])
        assert names == ["display", "json", "tsv"]

    def test_display_output_contains_each_formatter_name(self):
        cli = self._make_cli()
        result = CliRunner().invoke(
            cli,
            ["list-formatters", "--as", "display"],
            env={"COLUMNS": "80", "NO_COLOR": "1"},
        )
        assert result.exit_code == 0
        for name in ("display", "json", "tsv"):
            assert name in result.output

    def test_host_can_pick_any_command_name(self):
        """The factory doesn't dictate the command name — add_command does."""
        from asyoulikeit import list_formatters_command

        @click.group()
        def cli():
            pass

        cli.add_command(list_formatters_command(), name="show-output-formats")
        result = CliRunner().invoke(cli, ["show-output-formats", "--as", "tsv"])
        assert result.exit_code == 0
        assert "tsv" in result.output


class TestDescribeFormatterCommand:
    """Factory that returns a 'describe one formatter' Click command."""

    def _make_cli(self):
        from asyoulikeit import describe_formatter_command

        @click.group()
        def cli():
            pass

        cli.add_command(describe_formatter_command(), name="describe-formatter")
        return cli

    def test_factory_returns_click_command(self):
        from asyoulikeit import describe_formatter_command
        assert isinstance(describe_formatter_command(), click.Command)

    def test_tsv_default_emits_bare_description(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["describe-formatter", "tsv", "--as", "tsv"])
        assert result.exit_code == 0, result.output
        # Scalar TSV default is headerless: no leading "# tsv" line.
        assert not result.output.startswith("#")
        # And the captured content is the TsvFormatter docstring — 'awk' is a reliable anchor.
        assert "awk" in result.output

    def test_tsv_with_header_flag_emits_labelled_form(self):
        cli = self._make_cli()
        result = CliRunner().invoke(
            cli, ["describe-formatter", "tsv", "--as", "tsv", "--header"]
        )
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines[0] == "# tsv"

    def test_json_output_is_scalar_shape(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["describe-formatter", "tsv", "--as", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        report = parsed["reports"]["formatter"]
        assert report["metadata"]["kind"] == "scalar"
        assert report["metadata"]["title"] == "tsv"
        assert "awk" in report["value"]

    def test_display_output_labels_value_with_name(self):
        cli = self._make_cli()
        result = CliRunner().invoke(
            cli,
            ["describe-formatter", "tsv", "--as", "display"],
            env={"COLUMNS": "80", "NO_COLOR": "1"},
        )
        assert result.exit_code == 0
        # Scalar display default renders "title: value" when a title is set.
        assert result.output.startswith("tsv:")

    def test_missing_argument_fails_with_usage_error(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["describe-formatter"])
        assert result.exit_code != 0
        assert "Usage" in result.output or "Missing argument" in result.output

    def test_unknown_formatter_name_fails_at_parse(self):
        cli = self._make_cli()
        result = CliRunner().invoke(cli, ["describe-formatter", "nope"])
        # click.Choice rejects at parse time with a listing of valid values.
        assert result.exit_code != 0
        assert "nope" in result.output
        assert "tsv" in result.output  # the valid set is shown in the error
