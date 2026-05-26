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
