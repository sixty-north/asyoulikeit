<p align="center">
  <img src="https://raw.githubusercontent.com/sixty-north/asyoulikeit/master/docs/_static/logo.svg" alt="asyoulikeit" width="600">
</p>

# asyoulikeit

> `--as tsv | json | display` → *as you like it*

Gentle reader, this library doth furnish thy Python terminal tools with reports most manifold: to the machine made glorious by this Son of Jay, to the pipe in honest TSV, and to thine own eye in fair display — every format, verily, **as thou likest it**.

## Prologue — a Quickstart

Take thou a handler that returneth a `Reports` object, and with `@tabulated_output` do thou dress it thus:

```python
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
```

The decorator doth impart these options unto thy command: `--as` (which format thou shalt have), `--report` (which reports shall be shown), `--header` / `--no-header` (shall column headings appear?), and `--detailed` / `--essential` (how copious thy detail?). When `--as` is withheld, the decorator judgeth wisely: to a terminal it giveth `display`; to a pipe, `tsv`.

### Scene I — rendered `--as tsv`, for the machines of UNIX

```
# Name	Year	Paradigm
Python	1991	Multi-paradigm
Haskell	1990	Functional
Go	2009	Imperative
```

### Scene II — rendered `--as json`, for the machines of the web

```json
{
  "tables": {
    "languages": {
      "metadata": {
        "title": "Programming languages",
        "description": "A small sample of notable programming languages.",
        "present_transposed": false
      },
      "columns": [
        {
          "key": "name",
          "label": "Name",
          "header": false
        },
        {
          "key": "year",
          "label": "Year",
          "header": false
        },
        {
          "key": "paradigm",
          "label": "Paradigm",
          "header": false
        },
        {
          "key": "typing",
          "label": "Typing",
          "header": false
        }
      ],
      "rows": [
        {
          "name": "Python",
          "year": 1991,
          "paradigm": "Multi-paradigm",
          "typing": "Dynamic, duck"
        },
        {
          "name": "Haskell",
          "year": 1990,
          "paradigm": "Functional",
          "typing": "Static, inferred"
        },
        {
          "name": "Go",
          "year": 2009,
          "paradigm": "Imperative",
          "typing": "Static, structural"
        }
      ]
    }
  }
}
```

### Scene III — rendered `--as display`, for thine own eye

```
                 Programming languages                  
┏━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Name    ┃ Year ┃ Paradigm       ┃ Typing             ┃
┡━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Python  │ 1991 │ Multi-paradigm │ Dynamic, duck      │
│ Haskell │ 1990 │ Functional     │ Static, inferred   │
│ Go      │ 2009 │ Imperative     │ Static, structural │
└─────────┴──────┴────────────────┴────────────────────┘
    A small sample of notable programming languages.
```

## Of the Licence

Granted under the MIT charter — look thou to [`LICENSE`](LICENSE).

---

*This README is wrought by `scripts/generate_readme.py` from the template `scripts/readme_template.md.j2` and the runnable examples in `scripts/examples/`. Edit it not directly: amend thou the template or the example, then re-run the generator, that thy words may speak true.*
