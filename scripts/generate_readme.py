"""Generate README.md from a Jinja2 template + captured example outputs.

Usage:
    python scripts/generate_readme.py            # write README.md
    python scripts/generate_readme.py --check    # verify README.md matches; exit 1 on mismatch

The generator imports each runnable example from ``scripts/examples/``,
invokes it via ``click.testing.CliRunner`` for every built-in format, and
injects the captured source and output into the template. The ``--check``
mode is what the pre-commit hook runs: it regenerates into memory and
exits non-zero with a diff if the on-disk README.md has drifted.
"""

import argparse
import difflib
import importlib.util
import re
import sys
from pathlib import Path

import click
from click.testing import CliRunner
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
EXAMPLES_DIR = SCRIPTS_DIR / "examples"
TEMPLATE_NAME = "readme_template.md.j2"
README_PATH = ROOT / "README.md"

# CSI "m" sequences — colors, bold, italic. Rich emits these when
# force_terminal=True, so we strip them post-hoc to get plain
# unicode-box-drawing output suitable for a fenced markdown block.
ANSI_M_RE = re.compile(r"\x1b\[[0-9;]*m")

# Built-in formats captured for every example. Order matters: it's the
# order they appear in the template.
FORMATS = ("tsv", "json", "display")


def strip_ansi(text: str) -> str:
    return ANSI_M_RE.sub("", text)


def load_example_command(path: Path) -> click.Command:
    """Load a Click command from an example file.

    Convention: each example exposes exactly one module-level ``click.Command``.
    We take the first one we find so the generator doesn't care what it's named.
    """
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, click.Command):
            return attr
    raise RuntimeError(f"No Click command found in {path}")


def capture_example(path: Path) -> dict:
    """Read the example's source and invoke it once per format."""
    command = load_example_command(path)
    source = path.read_text().rstrip()
    runner = CliRunner()
    outputs: dict[str, str] = {}
    for fmt in FORMATS:
        # COLUMNS=80 pins rich's terminal width for stable output. NO_COLOR
        # asks rich to skip color codes; we also strip ANSI post-hoc as
        # belt-and-braces (bold/italic aren't always suppressed by NO_COLOR).
        result = runner.invoke(
            command, ["--as", fmt], env={"COLUMNS": "80", "NO_COLOR": "1"}
        )
        if result.exit_code != 0:
            raise RuntimeError(
                f"Example {path.name} exited {result.exit_code} with --as {fmt}:\n"
                f"stdout:\n{result.output}\n"
                f"exception: {result.exception}"
            )
        outputs[fmt] = strip_ansi(result.output).rstrip()
    return {"name": path.stem, "source": source, "outputs": outputs}


def render() -> str:
    env = Environment(
        loader=FileSystemLoader(SCRIPTS_DIR),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template(TEMPLATE_NAME)

    import asyoulikeit

    quickstart = capture_example(EXAMPLES_DIR / "quickstart.py")

    return template.render(
        version=asyoulikeit.__version__,
        example=quickstart,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify README.md.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify README.md matches generator output; exit 1 (with diff) on mismatch.",
    )
    args = parser.parse_args()

    rendered = render()

    if args.check:
        existing = README_PATH.read_text() if README_PATH.exists() else ""
        if rendered == existing:
            return 0
        sys.stderr.write("README.md is out of sync with the generator.\n")
        sys.stderr.write("Re-run: uv run python scripts/generate_readme.py\n\n")
        sys.stderr.writelines(
            difflib.unified_diff(
                existing.splitlines(keepends=True),
                rendered.splitlines(keepends=True),
                fromfile="README.md (on disk)",
                tofile="README.md (generated)",
            )
        )
        return 1

    README_PATH.write_text(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
