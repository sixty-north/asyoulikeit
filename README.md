<p align="center">
  <img src="https://raw.githubusercontent.com/sixty-north/asyoulikeit/master/docs/_static/logo.svg" alt="asyoulikeit" width="600">
</p>

# asyoulikeit

> `--as tsv | json | display` → *as you like it*

Gentle reader, this library doth furnish thy terminal tools with reports most manifold: to the device made glorious by this Son of Jay, to the pipe in honest tabulations, and to thine own eye in fair display — every format, verily, **as thou likest it**.

<p align="center">
  <a href="https://pypi.org/project/asyoulikeit/"><img src="https://img.shields.io/pypi/v/asyoulikeit.svg" alt="PyPI"></a>
  <a href="https://sixty-north.github.io/asyoulikeit/"><img src="https://img.shields.io/github/actions/workflow/status/sixty-north/asyoulikeit/docs.yml?branch=master&label=docs" alt="Docs"></a>
  <a href="https://github.com/sixty-north/asyoulikeit/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sixty-north/asyoulikeit/ci.yml?branch=master&label=CI" alt="CI"></a>
  <a href="https://pypi.org/project/asyoulikeit/"><img src="https://img.shields.io/pypi/pyversions/asyoulikeit.svg" alt="Python versions"></a>
</p>

<p align="center">
  <strong>Hark! the fuller folio awaiteth thee at <a href="https://sixty-north.github.io/asyoulikeit/">Documentation As You Like It</a>.</strong>
</p>

## Prologue

Take thou a handler that returneth `Reports`, and with `@report_output` do thou dress it. Thus decorated are options imparted unto thy command: `--as` (which format thou shalt have), `--report` (which reports shall be shown), `--header` / `--no-header` (shall columns have their heads?), and `--detailed` / `--essential` (how copious thy detail?). When `--as` is withheld, judgement is passed wisely: to a terminal is given `display`; to a pipe, `tsv`.

## Act Ⅰ   a table, of the wives of Henry VIII

```python
"""List the six wives of Henry VIII as a Report.

Run this file directly to see the default display format:

    python scripts/examples/quickstart.py

Or force a specific format:

    python scripts/examples/quickstart.py --as tsv
    python scripts/examples/quickstart.py --as json
"""

import click

from asyoulikeit import (
    Importance,
    Report,
    Reports,
    TableContent,
    report_output,
)


@click.command()
@report_output
def list_wives():
    """List the six wives of Henry VIII."""
    data = (
        TableContent(
            title="Wives of Henry VIII",
            description="Divorced, beheaded, died; divorced, beheaded, survived.",
        )
        .add_column("name", "Name")
        .add_column("born", "Born")
        .add_column("fate", "Fate")
        .add_column("queenship", "Queenship", importance=Importance.DETAIL)
        .add_row(name="Catherine of Aragon", born=1485, fate="Divorced", queenship="1509-1533")
        .add_row(name="Anne Boleyn", born=1501, fate="Beheaded", queenship="1533-1536")
        .add_row(name="Jane Seymour", born=1508, fate="Died", queenship="1536-1537")
        .add_row(name="Anne of Cleves", born=1515, fate="Divorced", queenship="1540")
        .add_row(name="Catherine Howard", born=1523, fate="Beheaded", queenship="1540-1542")
        .add_row(name="Catherine Parr", born=1512, fate="Survived", queenship="1543-1547")
    )
    return Reports(wives=Report(data=data))


if __name__ == "__main__":
    list_wives()
```

### Scene ⅰ   `--as tsv`,   for the devices of UNIX

```
# Name	Born	Fate
Catherine of Aragon	1485	Divorced
Anne Boleyn	1501	Beheaded
Jane Seymour	1508	Died
Anne of Cleves	1515	Divorced
Catherine Howard	1523	Beheaded
Catherine Parr	1512	Survived
```

### Scene ⅱ   `--as json`,   for the contrivances of the web

```json
{
  "reports": {
    "wives": {
      "metadata": {
        "kind": "table",
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
        },
        {
          "key": "queenship",
          "label": "Queenship",
          "header": false
        }
      ],
      "rows": [
        {
          "name": "Catherine of Aragon",
          "born": 1485,
          "fate": "Divorced",
          "queenship": "1509-1533"
        },
        {
          "name": "Anne Boleyn",
          "born": 1501,
          "fate": "Beheaded",
          "queenship": "1533-1536"
        },
        {
          "name": "Jane Seymour",
          "born": 1508,
          "fate": "Died",
          "queenship": "1536-1537"
        },
        {
          "name": "Anne of Cleves",
          "born": 1515,
          "fate": "Divorced",
          "queenship": "1540"
        },
        {
          "name": "Catherine Howard",
          "born": 1523,
          "fate": "Beheaded",
          "queenship": "1540-1542"
        },
        {
          "name": "Catherine Parr",
          "born": 1512,
          "fate": "Survived",
          "queenship": "1543-1547"
        }
      ]
    }
  }
}
```

### Scene ⅲ   `--as display`,   for thine own eye

```
                 Wives of Henry VIII                 
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Name                ┃ Born ┃ Fate     ┃ Queenship ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ Catherine of Aragon │ 1485 │ Divorced │ 1509-1533 │
│ Anne Boleyn         │ 1501 │ Beheaded │ 1533-1536 │
│ Jane Seymour        │ 1508 │ Died     │ 1536-1537 │
│ Anne of Cleves      │ 1515 │ Divorced │ 1540      │
│ Catherine Howard    │ 1523 │ Beheaded │ 1540-1542 │
│ Catherine Parr      │ 1512 │ Survived │ 1543-1547 │
└─────────────────────┴──────┴──────────┴───────────┘
    Divorced, beheaded, died; divorced, beheaded,    
                      survived.
```

## Act Ⅱ   two trees, in the forest of Arden

Behold: the play that lent this library its name doth turn upon two brothers of the ducal stamp — one banish'd to the forest of Arden, the other an usurper at court — and upon the daughters each begat. Fitting, surely, that for houses which grow not together but apart, a `TreeContent` here taketh two roots: a forest in both shape and sense.

```python
"""Families of Shakespeare's *As You Like It* as a Report.

The play from which this library takes its name turns on two ducal
brothers — one exiled to the Forest of Arden, the other a usurper —
and the daughters of each. Two trees, one forest.
"""

import click

from asyoulikeit import (
    Importance,
    Report,
    Reports,
    TreeContent,
    report_output,
)


@click.command()
@report_output
def list_dukes():
    """List the ducal families from 'As You Like It'."""
    tree = (
        TreeContent(
            title="Ducal families of 'As You Like It'",
            description="The two lines around which the play turns.",
        )
        .add_column("name", "Name", header=True)
        .add_column("role", "Role")
        .add_column("setting", "Setting", importance=Importance.DETAIL)
    )
    senior = tree.add_root(
        name="Duke Senior", role="Exiled duke", setting="Forest of Arden"
    )
    senior.add_child(
        name="Rosalind", role="Heroine", setting="Court and Arden"
    )
    frederick = tree.add_root(
        name="Duke Frederick", role="Usurper", setting="At court"
    )
    frederick.add_child(
        name="Celia", role="Heroine's cousin", setting="Court and Arden"
    )
    return Reports(dukes=Report(data=tree))


if __name__ == "__main__":
    list_dukes()
```

### Scene ⅰ   `--as tsv`,   for the devices of UNIX

```
# Name	Role
Duke Senior	Exiled duke
  Rosalind	Heroine
Duke Frederick	Usurper
  Celia	Heroine's cousin
```

### Scene ⅱ   `--as json`,   for the contrivances of the web

```json
{
  "reports": {
    "dukes": {
      "metadata": {
        "kind": "tree",
        "title": "Ducal families of 'As You Like It'",
        "description": "The two lines around which the play turns."
      },
      "columns": [
        {
          "key": "name",
          "label": "Name",
          "header": true
        },
        {
          "key": "role",
          "label": "Role",
          "header": false
        },
        {
          "key": "setting",
          "label": "Setting",
          "header": false
        }
      ],
      "roots": [
        {
          "values": {
            "name": "Duke Senior",
            "role": "Exiled duke",
            "setting": "Forest of Arden"
          },
          "children": [
            {
              "values": {
                "name": "Rosalind",
                "role": "Heroine",
                "setting": "Court and Arden"
              },
              "children": []
            }
          ]
        },
        {
          "values": {
            "name": "Duke Frederick",
            "role": "Usurper",
            "setting": "At court"
          },
          "children": [
            {
              "values": {
                "name": "Celia",
                "role": "Heroine's cousin",
                "setting": "Court and Arden"
              },
              "children": []
            }
          ]
        }
      ]
    }
  }
}
```

### Scene ⅲ   `--as display`,   for thine own eye

```
          Ducal families of 'As You Like It'           
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Name           ┃ Role             ┃ Setting         ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Duke Senior    │ Exiled duke      │ Forest of Arden │
│ └── Rosalind   │ Heroine          │ Court and Arden │
│ Duke Frederick │ Usurper          │ At court        │
│ └── Celia      │ Heroine's cousin │ Court and Arden │
└────────────────┴──────────────────┴─────────────────┘
      The two lines around which the play turns.
```

## Of the Licence

Granted under the MIT charter — look thou to [`LICENSE`](LICENSE).

---

*This README is wrought by `scripts/generate_readme.py` from the template `scripts/readme_template.md.j2` and the runnable examples in `scripts/examples/`. Edit it not directly: amend thou the template or the example, then re-run the generator, that thy words may speak true.*
