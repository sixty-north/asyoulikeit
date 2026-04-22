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
