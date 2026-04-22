<p align="center">
  <img src="https://raw.githubusercontent.com/sixty-north/asyoulikeit/master/docs/_static/logo.svg" alt="asyoulikeit" width="600">
</p>

# asyoulikeit

> `--as tsv | json | display` → *as you like it*

Gentle reader, this library doth furnish thy terminal tools with reports most manifold: to the machine made glorious by this Son of Jay, to the pipe in honest tabulations, and to thine own eye in fair display — every format, verily, **as thou likest it**.

## Prologue — a Quickstart

Take thou a handler that returneth a `Reports` object, and with `@tabulated_output` do thou dress it thus:

```python
"""Quickstart example: list the six wives of Henry VIII as a Report.

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
    Report,
    Reports,
    TabularData,
    tabulated_output,
)


@click.command()
@tabulated_output
def list_wives():
    """List the six wives of Henry VIII."""
    data = (
        TabularData(
            title="Wives of Henry VIII",
            description="Divorced, beheaded, died; divorced, beheaded, survived.",
        )
        .add_column("name", "Name")
        .add_column("born", "Born")
        .add_column("fate", "Fate")
        .add_row(name="Catherine of Aragon", born=1485, fate="Divorced")
        .add_row(name="Anne Boleyn", born=1501, fate="Beheaded")
        .add_row(name="Jane Seymour", born=1508, fate="Died")
        .add_row(name="Anne of Cleves", born=1515, fate="Divorced")
        .add_row(name="Catherine Howard", born=1523, fate="Beheaded")
        .add_row(name="Catherine Parr", born=1512, fate="Survived")
    )
    return Reports(wives=Report(data=data))


if __name__ == "__main__":
    list_wives()
```

The decorator doth impart these options unto thy command: `--as` (which format thou shalt have), `--report` (which reports shall be shown), `--header` / `--no-header` (shall column headings appear?), and `--detailed` / `--essential` (how copious thy detail?). When `--as` is withheld, the decorator judgeth wisely: to a terminal it giveth `display`; to a pipe, `tsv`.

### Scene I — rendered `--as tsv`, for the machines of UNIX

```
# Name	Born	Fate
Catherine of Aragon	1485	Divorced
Anne Boleyn	1501	Beheaded
Jane Seymour	1508	Died
Anne of Cleves	1515	Divorced
Catherine Howard	1523	Beheaded
Catherine Parr	1512	Survived
```

### Scene II — rendered `--as json`, for the machines of the web

```json
{
  "tables": {
    "wives": {
      "metadata": {
        "title": "Wives of Henry VIII",
        "description": "Divorced, beheaded, died; divorced, beheaded, survived.",
        "present_transposed": false
      },
      "columns": [
        {
          "key": "name",
          "label": "Name",
          "header": false
        },
        {
          "key": "born",
          "label": "Born",
          "header": false
        },
        {
          "key": "fate",
          "label": "Fate",
          "header": false
        }
      ],
      "rows": [
        {
          "name": "Catherine of Aragon",
          "born": 1485,
          "fate": "Divorced"
        },
        {
          "name": "Anne Boleyn",
          "born": 1501,
          "fate": "Beheaded"
        },
        {
          "name": "Jane Seymour",
          "born": 1508,
          "fate": "Died"
        },
        {
          "name": "Anne of Cleves",
          "born": 1515,
          "fate": "Divorced"
        },
        {
          "name": "Catherine Howard",
          "born": 1523,
          "fate": "Beheaded"
        },
        {
          "name": "Catherine Parr",
          "born": 1512,
          "fate": "Survived"
        }
      ]
    }
  }
}
```

### Scene III — rendered `--as display`, for thine own eye

```
           Wives of Henry VIII           
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━┓
┃ Name                ┃ Born ┃ Fate     ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━┩
│ Catherine of Aragon │ 1485 │ Divorced │
│ Anne Boleyn         │ 1501 │ Beheaded │
│ Jane Seymour        │ 1508 │ Died     │
│ Anne of Cleves      │ 1515 │ Divorced │
│ Catherine Howard    │ 1523 │ Beheaded │
│ Catherine Parr      │ 1512 │ Survived │
└─────────────────────┴──────┴──────────┘
   Divorced, beheaded, died; divorced,   
           beheaded, survived.
```

## Of the Licence

Granted under the MIT charter — look thou to [`LICENSE`](LICENSE).

---

*This README is wrought by `scripts/generate_readme.py` from the template `scripts/readme_template.md.j2` and the runnable examples in `scripts/examples/`. Edit it not directly: amend thou the template or the example, then re-run the generator, that thy words may speak true.*
