# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package purpose

`aspects` packages up a CLI report-rendering stack extracted from `demonstrable-visning`: a `Report`/`Reports` data model, a stevedore-based `Formatter` plug-in system with three built-in formatters (`table`, `tsv`, `json`), and a `@tabulated_output` Click decorator that turns a handler returning `Reports` into a command with `--as / --report / --header / --detailed` options. The same stevedore plug-in pattern has been copy-pasted into several sixty-north packages; the long-term intent is for those packages to depend on `aspects` instead. Python 3.11+.

## Commands

```bash
uv sync                             # install runtime + dev deps and build the package in-place
uv run pytest                       # full test suite
uv run pytest tests/test_output.py  # a single file
uv run pytest tests/test_output.py::TestReportSelection::test_report_flag_restricts_output  # a single test
uv run python -c "from aspects.formatter import formatter_names; print(formatter_names())"  # sanity-check entry-point registration
```

After editing entry points in `pyproject.toml` (or adding a new formatter package), **re-run `uv sync`** — stevedore reads entry points from installed package metadata, so the in-place install must be rebuilt before `formatter_names()` reflects the change. Failing to do this is the most common reason a newly-added formatter "isn't found".

## Architecture

### End-to-end flow

```
Click command (decorated with @tabulated_output)
   │
   ▼  returns Reports (or None)
aspects.cli.output.tabulated_output wrapper
   │
   ▼  filters by --report, applies --header / --detailed overrides via dataclasses.replace
aspects.formatter.format_as(reports, format_name)
   │
   ▼  stevedore lookup in "aspects.formatter" namespace
<name>.Formatter (= concrete TableFormatter / TsvFormatter / JsonFormatter).format(reports) -> str
   │
   ▼
click.echo(output)
```

Only three nodes hold real logic: the decorator (`src/aspects/cli/output.py`), the dispatch/ABC layer (`src/aspects/formatter.py`), and each formatter's `format()` method. The rest is data classes.

### Formatter plug-in packaging (important and non-obvious)

Built-in formatters live under `src/aspects/ext/formatters/<name>/`. Each sub-package has two files:

- `formatter.py` defines a concrete class with a specific name (`TableFormatter`, `TsvFormatter`, `JsonFormatter`).
- `__init__.py` does `from .formatter import TableFormatter as Formatter` — re-exporting the concrete class under the uniform symbol `Formatter`.

The entry point in `pyproject.toml` then always references `<pkg>:Formatter`:

```toml
[project.entry-points."aspects.formatter"]
table = "aspects.ext.formatters.table:Formatter"
```

This keeps the entry-point target stable while letting the concrete class name stay descriptive. The `ext/` prefix is a cross-project sixty-north convention — keep it; do not flatten. The same layout should be used for any future kinds of extensions beyond formatters.

### Detail-level and header filtering

Three knobs interact and it's easy to get lost:

1. **Per-column `Importance`** (`ESSENTIAL` / `DETAIL`) — set when defining columns on `TabularData`.
2. **Per-row `Importance`** — passed as the reserved `_importance` kwarg on `add_row`.
3. **Per-`Report` `DetailLevel`** (`AUTO` / `DETAILED` / `ESSENTIAL`) — the formatting preference the report *suggests*.

Each formatter resolves `DetailLevel.AUTO` to its own default: `table` and `json` choose `DETAILED`, `tsv` chooses `ESSENTIAL` (since TSV is meant for downstream pipes). `--detailed`/`--essential` on the CLI override the report's preference via `dataclasses.replace` before dispatch.

Header behaviour is format-specific: TSV prefixes the first header cell with `# ` (so downstream `awk`/`cut` can skip it as a comment); table omits title/caption when `header=False`; JSON always includes metadata (self-describing).

### Smart `--as` default and testing it

`tabulated_output` injects `--as` with a callback that reads `sys.stdout.isatty()` at invocation time: `table` when interactive, `tsv` when piped. When writing a test that needs to exercise the TTY branch, note that `click.testing.CliRunner` swaps `sys.stdout` inside `invoke()`, so monkeypatching the real `sys.stdout.isatty` has no effect. Instead, rebind the `sys` name inside the decorator module:

```python
import types
fake_sys = types.SimpleNamespace(stdout=types.SimpleNamespace(isatty=lambda: True))
monkeypatch.setattr("aspects.cli.output.sys", fake_sys)
```

Click 8.2+ no longer accepts `mix_stderr=` on `CliRunner`; stderr is always separated — use `result.stderr` directly.

Also note: `--as` choices are computed at **decorator application time** (`click.Choice(formatter_names(), ...)`), not at invocation. A newly-registered formatter is therefore not visible to a decorator that's already imported until the importing module is re-loaded.

### `Extension` ABC and namespace convention

`src/aspects/extension.py` is the shared plug-in machinery. `Extension.entry_point_name()` hardcodes the namespace as `f"aspects.{cls.kind()}"`; any new kind of extension added to aspects should follow that convention (`kind() -> "widget"` ⇒ namespace `"aspects.widget"`). The class exists here, not in a consumer package, because the long-term plan is for other sixty-north packages to adopt aspects instead of duplicating this loader.

The original visning had `Extension.cache_dirpath()` tied to a visning-specific app cache; it was intentionally dropped during extraction. Re-add only if a genuine need appears.

### Handler return contract

The `@tabulated_output` wrapper enforces that the decorated handler returns either a `Reports` instance or `None`. Anything else raises `TypeError` at runtime (caught by `CliRunner` as `result.exception`). `None` is permitted and emits no output — useful for action commands declared with `@tabulated_output(default_reports=None)`.

## Notes on extension

- To add a new built-in formatter: create `src/aspects/ext/formatters/<name>/{formatter.py,__init__.py}` following the alias pattern above, add the `[project.entry-points."aspects.formatter"]` line, then `uv sync`. Add tests in `tests/test_formatters.py`.
- Consumers of aspects register their own formatters the same way from their own package — no code changes in aspects required.
- `src/aspects/_text.py` is internal (underscore-prefixed) — not part of the public API.
