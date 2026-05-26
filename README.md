<p align="center">
  <img src="https://raw.githubusercontent.com/sixty-north/asyoulikeit/master/docs/_static/logo.svg" alt="asyoulikeit" width="600">
</p>

# asyoulikeit

> `$ your-cli [--as tsv | json | display]` → *as you like it*

Gentle reader, this library doth furnish thy terminal tools with reports most manifold: to the device made glorious by this Son of Jay, to the pipe in honest tabulations, and to thine own eye in fair display — every format, verily, **as thou likest it**.

<p align="center">
  <a href="https://pypi.org/project/asyoulikeit/"><img src="https://img.shields.io/pypi/v/asyoulikeit.svg" alt="PyPI"></a>
  <a href="https://github.com/sixty-north/asyoulikeit/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/sixty-north/asyoulikeit/release.yml?label=release" alt="Release"></a>
  <a href="https://github.com/sixty-north/asyoulikeit/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sixty-north/asyoulikeit/ci.yml?branch=master&label=CI" alt="CI"></a>
  <a href="https://pypi.org/project/asyoulikeit/"><img src="https://img.shields.io/pypi/pyversions/asyoulikeit.svg" alt="Python versions"></a>
</p>

<p align="center">
  <strong>Hark! the fuller folio awaiteth thee at <a href="https://sixty-north.github.io/asyoulikeit/">Documentation As You Like It</a>.</strong>
</p>

## Prologue

Take thou a handler that returneth `Reports`, and with `@report_output` do thou dress it. Thus decorated are options imparted unto thy command: `--as` (which format thou shalt have), `--report` (which reports shall be shown), `--header` / `--no-header` (shall columns have their heads?), and `--detailed` / `--essential` (how copious thy detail?). When `--as` is withheld, judgement is passed wisely: to a terminal is given `display`; to a pipe, `tsv`.

## Act Ⅰ   a table, of the wives of Henry VIII

Mark well the column of **Marriage**, a thing of double aspect: each entry therein weareth two faces, and `ByAudience` holdeth both at once. To the engines of pipe and web it speaketh a bare numeral, fit for reck'ning and for sorting; but unto thine own eye it telleth the selfsame rank as a word writ fair. Thou needst not choose betwixt them at the cell's making — the format thou electest with `--as` doth choose the face, and so the machine readeth `1` where the reader beholdeth *first*.

*Enter* **`henry-wives.py`**:

```python
"""List the six wives of Henry VIII as a Report.

Run this file directly to see the default display format:

    python scripts/examples/henry-wives.py

Or force a specific format:

    python scripts/examples/henry-wives.py --as tsv
    python scripts/examples/henry-wives.py --as json
"""

import click

from asyoulikeit import (
    ByAudience,
    Importance,
    Report,
    Reports,
    TableContent,
    report_output,
)


@click.command()
@report_output(reports={"wives": "The six wives of Henry VIII."})
def list_wives():
    """List the six wives of Henry VIII."""
    # The "Marriage" cells carry two faces via ByAudience: the raw ordinal
    # number for machines (so JSON emits 1, not "first", and a pipe can sort
    # on it) and the word for the human eye. The dispatcher picks the face
    # matching the chosen formatter's audience.
    data = (
        TableContent(
            title="Wives of Henry VIII",
            description="Divorced, beheaded, died; divorced, beheaded, survived.",
        )
        .add_column("name", "Name")
        .add_column("marriage", "Marriage")
        .add_column("born", "Born")
        .add_column("fate", "Fate")
        .add_column("queenship", "Queenship", importance=Importance.DETAIL)
        .add_row(name="Catherine of Aragon", marriage=ByAudience(machine=1, human="first"), born=1485, fate="Divorced", queenship="1509-1533")
        .add_row(name="Anne Boleyn", marriage=ByAudience(machine=2, human="second"), born=1501, fate="Beheaded", queenship="1533-1536")
        .add_row(name="Jane Seymour", marriage=ByAudience(machine=3, human="third"), born=1508, fate="Died", queenship="1536-1537")
        .add_row(name="Anne of Cleves", marriage=ByAudience(machine=4, human="fourth"), born=1515, fate="Divorced", queenship="1540")
        .add_row(name="Catherine Howard", marriage=ByAudience(machine=5, human="fifth"), born=1523, fate="Beheaded", queenship="1540-1542")
        .add_row(name="Catherine Parr", marriage=ByAudience(machine=6, human="sixth"), born=1512, fate="Survived", queenship="1543-1547")
    )
    return Reports(wives=Report(data=data))


if __name__ == "__main__":
    list_wives()
```

### Scene ⅰ   `--as tsv`,   for the devices of UNIX

```console
$ python henry-wives.py --as tsv
```

```
# Name                 Marriage    Born    Fate
Catherine of Aragon    1           1485    Divorced
Anne Boleyn            2           1501    Beheaded
Jane Seymour           3           1508    Died
Anne of Cleves         4           1515    Divorced
Catherine Howard       5           1523    Beheaded
Catherine Parr         6           1512    Survived
```

### Scene ⅱ   `--as json`,   for the contrivances of the web

```console
$ python henry-wives.py --as json
```

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
          "key": "marriage",
          "label": "Marriage",
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
          "marriage": 1,
          "born": 1485,
          "fate": "Divorced",
          "queenship": "1509-1533"
        },
        {
          "name": "Anne Boleyn",
          "marriage": 2,
          "born": 1501,
          "fate": "Beheaded",
          "queenship": "1533-1536"
        },
        {
          "name": "Jane Seymour",
          "marriage": 3,
          "born": 1508,
          "fate": "Died",
          "queenship": "1536-1537"
        },
        {
          "name": "Anne of Cleves",
          "marriage": 4,
          "born": 1515,
          "fate": "Divorced",
          "queenship": "1540"
        },
        {
          "name": "Catherine Howard",
          "marriage": 5,
          "born": 1523,
          "fate": "Beheaded",
          "queenship": "1540-1542"
        },
        {
          "name": "Catherine Parr",
          "marriage": 6,
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

```console
$ python henry-wives.py --as display
```

```
                      Wives of Henry VIII                       
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Name                ┃ Marriage ┃ Born ┃ Fate     ┃ Queenship ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ Catherine of Aragon │ first    │ 1485 │ Divorced │ 1509-1533 │
│ Anne Boleyn         │ second   │ 1501 │ Beheaded │ 1533-1536 │
│ Jane Seymour        │ third    │ 1508 │ Died     │ 1536-1537 │
│ Anne of Cleves      │ fourth   │ 1515 │ Divorced │ 1540      │
│ Catherine Howard    │ fifth    │ 1523 │ Beheaded │ 1540-1542 │
│ Catherine Parr      │ sixth    │ 1512 │ Survived │ 1543-1547 │
└─────────────────────┴──────────┴──────┴──────────┴───────────┘
    Divorced, beheaded, died; divorced, beheaded, survived.
```

## Act Ⅱ   two trees, in the forest of Arden

Behold: the play that lent this library its name doth turn upon two brothers of the ducal stamp — one banish'd to the forest of Arden, the other an usurper at court — and upon the daughters each begat. Fitting, surely, that for houses which grow not together but apart, a `TreeContent` here taketh two roots: a forest in both shape and sense.

*Enter* **`arden-dukes.py`**:

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
@report_output(reports={
    "dukes": "The two ducal lines of Shakespeare's As You Like It.",
})
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

```console
$ python arden-dukes.py --as tsv
```

```
# Name            Path1             Path2       Role
Duke Senior       Duke Senior                   Exiled duke
Rosalind          Duke Senior       Rosalind    Heroine
Duke Frederick    Duke Frederick                Usurper
Celia             Duke Frederick    Celia       Heroine's cousin
```

### Scene ⅱ   `--as json`,   for the contrivances of the web

```console
$ python arden-dukes.py --as json
```

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

```console
$ python arden-dukes.py --as display
```

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
