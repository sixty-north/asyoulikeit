"""Quickstart example: list a handful of programming languages as a Report.

Run this file directly to see the default display format:

    python scripts/examples/quickstart.py

Or force a specific format:

    python scripts/examples/quickstart.py --as tsv
    python scripts/examples/quickstart.py --as json

The ``scripts/generate_readme.py`` generator imports this file, invokes the
command with each built-in format, and injects the source + captured outputs
into the README.
"""

import click

from asyoulikeit import (
    Importance,
    Report,
    Reports,
    TabularData,
    tabulated_output,
)


@click.command()
@tabulated_output
def list_languages():
    """List some well-known programming languages."""
    data = (
        TabularData(
            title="Programming languages",
            description="A small sample of notable programming languages.",
        )
        .add_column("name", "Name")
        .add_column("year", "Year")
        .add_column("paradigm", "Paradigm")
        .add_column("typing", "Typing", importance=Importance.DETAIL)
        .add_row(name="Python", year=1991, paradigm="Multi-paradigm", typing="Dynamic, duck")
        .add_row(name="Haskell", year=1990, paradigm="Functional", typing="Static, inferred")
        .add_row(name="Go", year=2009, paradigm="Imperative", typing="Static, structural")
    )
    return Reports(languages=Report(data=data))


if __name__ == "__main__":
    list_languages()
