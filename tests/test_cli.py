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
