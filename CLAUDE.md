# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package purpose

`aspects` packages up a CLI report-rendering stack extracted from `demonstrable-visning`: a `Report`/`Reports` data model, a stevedore-based `Formatter` plug-in system with three built-in formatters, and a `@tabulated_output` Click decorator that turns a handler returning `Reports` into a command with `--as / --report / --header / --detailed` options. The same stevedore plug-in pattern has been copy-pasted into several sixty-north packages; the long-term intent is for those packages to depend on `aspects` instead. Python 3.11+.

The three built-in formatters form a symmetric mental model — keep this framing in mind when adding new formatters or extending existing ones:

- `json` → structured output for machines
- `tsv`  → tabular output for machines
- `display` → presentation for humans (borders, colors, bold/italic; currently implemented with Rich, but the name is shape-agnostic so it can cover trees or lists when those report kinds are added)

## Commands

```bash
uv sync                             # install runtime + dev deps and build the package in-place
uv run pytest                       # full test suite
uv run pytest tests/test_output.py  # a single file
uv run pytest tests/test_output.py::TestReportSelection::test_report_flag_restricts_output  # a single test
uv run python -c "from aspects.formatter import formatter_names; print(formatter_names())"  # sanity-check entry-point registration
```

After editing entry points in `pyproject.toml` (or adding a new formatter package), **re-run `uv sync`** — stevedore reads entry points from installed package metadata, so the in-place install must be rebuilt before `formatter_names()` reflects the change. Failing to do this is the most common reason a newly-added formatter "isn't found".

## README is generated, not hand-written

`README.md` is produced by `scripts/generate_readme.py` from a Jinja2 template (`scripts/readme_template.md.j2`) and runnable Click examples in `scripts/examples/`. The generator imports each example, invokes it with every built-in format via `CliRunner` (with `COLUMNS=80` and `NO_COLOR=1`, plus a post-hoc ANSI strip so the `display` output fits cleanly in a fenced markdown block), and injects the source + captured output into the template.

```bash
uv run python scripts/generate_readme.py           # regenerate README.md
uv run python scripts/generate_readme.py --check   # verify it's in sync; prints a unified diff + exits 1 on drift
```

A pre-commit hook (`.pre-commit-config.yaml`) runs the `--check` variant whenever `README.md`, the generator script, the template, anything under `scripts/examples/`, or any `src/aspects/*.py` changes. First-time setup in a clone:

```bash
uv run pre-commit install
```

When you change the public API, the example will change (or start failing), the generator will produce a different README, and the hook will block the commit until you regenerate. **Never hand-edit `README.md`** — edit the template or the example instead.

## Versioning and releases

Version is managed manually via `bump-my-version` (configured in `pyproject.toml` under `[tool.bumpversion]`). The single source of truth is `__version__` in `src/aspects/__init__.py`; setuptools reads it via `[tool.setuptools.dynamic]` and exposes it as the wheel's installed version. Do not edit the version by hand in more than one place — let `bump-my-version` update both the module and the `[tool.bumpversion] current_version` config in lock-step.

Release flow (on a clean working tree, from `main` / `master`):

```bash
uv run bump-my-version bump --dry-run --verbose patch   # preview: what changes, commit, tag
uv run bump-my-version bump patch                       # or `minor`, `major` — commits + tags
git push --follow-tags                                   # publish commit and the v<X.Y.Z> tag
```

Each real bump produces one commit (`Bump version: X.Y.Z → X.Y.Z+1`) and one annotated tag (`vX.Y.Z+1`). `bump-my-version` refuses to run with a dirty tree, which is the intended safety net.

## CI and publishing

Three workflows under `.github/workflows/`:

- `test.yml` — reusable (`on: workflow_call`). Resolves the earliest and latest supported Python versions by reading `pyproject.toml` classifiers, then runs the full pytest suite on the 3-OS × 2-Python-version matrix. Critically, tests run **against the installed wheel, not the editable source tree**: `uv sync --no-install-project` → `uv build` → `uv pip install dist/*.whl` → `uv run --no-project pytest`. This catches packaging blunders (missing `package-data`, un-shipped `py.typed`, unregistered entry points) that an editable install would hide.
- `ci.yml` — triggers on push to `master` and pull requests. Calls `test.yml` and additionally runs the README generator's `--check` as a safety net against anyone bypassing the pre-commit hook.
- `publish.yml` — triggers on `v*` tags (the ones `bump-my-version` produces). Re-runs `test.yml`, then `uv publish`es to PyPI. The `needs: test` dependency guarantees publication only happens after a full green matrix on the exact tagged commit. Uses `UV_PUBLISH_TOKEN` (from the `PYPI_TOKEN` repo secret, scoped to the `pypi` environment); trusted publishing via OIDC is also supported if configured.

To release: run `bump-my-version bump <level>` on a clean `master`, then `git push --follow-tags`. The push of the commit triggers `ci.yml`; the push of the tag triggers `publish.yml`.

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
<name>.Formatter (= concrete DisplayFormatter / TsvFormatter / JsonFormatter).format(reports) -> str
   │
   ▼
click.echo(output)
```

Only three nodes hold real logic: the decorator (`src/aspects/cli.py`), the dispatch/ABC layer (`src/aspects/formatter.py`), and each formatter's `format()` method. The rest is data classes.

Client-facing objects (`tabulated_output`, `Report`, `Reports`, `TabularData`, `Column`, `Importance`, `DetailLevel`, `Formatter`, `format_as`, `formatter_names`, `create_formatter`, `ALL_REPORTS`, `AspectsError`, `Extension`, style-key constants, …) are re-exported from the top-level `aspects` package — consumers should `from aspects import ...` rather than reaching into the sub-modules.

### Formatter plug-in packaging (important and non-obvious)

Built-in formatters live under `src/aspects/ext/formatters/<name>/`. Each sub-package has two files:

- `formatter.py` defines a concrete class with a specific name (`DisplayFormatter`, `TsvFormatter`, `JsonFormatter`).
- `__init__.py` does `from .formatter import DisplayFormatter as Formatter` — re-exporting the concrete class under the uniform symbol `Formatter`.

The entry point in `pyproject.toml` then always references `<pkg>:Formatter`:

```toml
[project.entry-points."aspects.formatter"]
display = "aspects.ext.formatters.display:Formatter"
```

This keeps the entry-point target stable while letting the concrete class name stay descriptive. The `ext/` prefix is a cross-project sixty-north convention — keep it; do not flatten. The same layout should be used for any future kinds of extensions beyond formatters.

### Detail-level and header filtering

Three knobs interact and it's easy to get lost:

1. **Per-column `Importance`** (`ESSENTIAL` / `DETAIL`) — set when defining columns on `TabularData`.
2. **Per-row `Importance`** — passed as the reserved `_importance` kwarg on `add_row`.
3. **Per-`Report` `DetailLevel`** (`AUTO` / `DETAILED` / `ESSENTIAL`) — the formatting preference the report *suggests*.

Each formatter resolves `DetailLevel.AUTO` to its own default: `display` and `json` choose `DETAILED`, `tsv` chooses `ESSENTIAL` (since TSV is meant for downstream pipes). `--detailed`/`--essential` on the CLI override the report's preference via `dataclasses.replace` before dispatch.

Header behaviour is format-specific: TSV prefixes the first header cell with `# ` (so downstream `awk`/`cut` can skip it as a comment); display omits title/caption when `header=False`; JSON always includes metadata (self-describing).

### Smart `--as` default and testing it

`tabulated_output` injects `--as` with a callback that reads `sys.stdout.isatty()` at invocation time: `display` when interactive, `tsv` when piped. When writing a test that needs to exercise the TTY branch, note that `click.testing.CliRunner` swaps `sys.stdout` inside `invoke()`, so monkeypatching the real `sys.stdout.isatty` has no effect. Instead, rebind the `sys` name inside the decorator module:

```python
import types
fake_sys = types.SimpleNamespace(stdout=types.SimpleNamespace(isatty=lambda: True))
monkeypatch.setattr("aspects.cli.sys", fake_sys)
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
