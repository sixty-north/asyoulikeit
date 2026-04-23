Using asyoulikeit in your CLI
=============================

``asyoulikeit`` is a small library you apply to a Click-based
command-line tool to give your handlers a single source of truth for
structured output. Instead of printing in one hard-coded format, your
handler returns a :class:`~asyoulikeit.Reports` value and the library
handles rendering it as JSON, TSV, or a rich human-readable display,
according to whatever the user selected with the ``--as`` flag.

This page walks through the typical shape of an integration. See
:doc:`cli` for what your users will see on the command line, and
:doc:`api` for the full API reference.


Installation
------------

.. code-block:: bash

   pip install asyoulikeit

Or with uv:

.. code-block:: bash

   uv add asyoulikeit


The minimal example
-------------------

A Click command decorated with :func:`~asyoulikeit.report_output`
returns a :class:`~asyoulikeit.Reports` value. That's essentially all
there is to it.

.. code-block:: python

   import click
   from asyoulikeit import Report, Reports, TableContent, report_output


   @click.command()
   @report_output
   def list_users():
       """List the users of the system."""
       data = (
           TableContent(title="Users")
           .add_column("name", "Name")
           .add_column("role", "Role")
           .add_row(name="Alice", role="admin")
           .add_row(name="Bob", role="user")
       )
       return Reports(users=Report(data=data))


   if __name__ == "__main__":
       list_users()

Run ``list_users`` attached to a terminal and it renders with the
``display`` formatter — borders, a title, legible rows. Pipe the output
into another program and it renders as TSV (``# Name\tRole`` header
then tab-separated values). Pass ``--as json`` and it emits structured
JSON. The handler is identical across all three modes; the choice of
format is a runtime concern the decorator handles.


The data model
--------------

Three classes carry all the state.

:class:`~asyoulikeit.TableContent` is a schema-validated table builder.
Add columns first, then rows. Every row must supply exactly the columns
that were declared — missing keys and unexpected keys both raise
:exc:`ValueError`, which catches typos early. ``TableContent`` also
holds optional ``title`` and ``description`` metadata that some
formatters display.

:class:`~asyoulikeit.TreeContent` is the hierarchical sibling — a
forest of nodes sharing a single column schema. See :ref:`tree-content`
below.

Both ``TableContent`` and ``TreeContent`` are implementations of
:class:`~asyoulikeit.ReportContent`. Future shapes (heterogeneous
trees, lists, description lists, …) will slot in as further subclasses
without changing the rest of the API.

:class:`~asyoulikeit.Report` is a frozen dataclass wrapping one piece
of ``ReportContent`` plus formatting preferences (``detail_level``,
``header``). These preferences are *suggestions* — the user can
override them from the command line.

:class:`~asyoulikeit.Reports` is a validated mapping of
``name → Report``. A command can return a single named report or
several; both are expressed by the same type. The names become keys in
JSON output and selectors for the user's ``--report`` flag.


Importance and detail level
---------------------------

Not every column is equally important. Some carry core identifying
information ("name", "id", "status"); others are supplementary
("notes", "last modified", "description"). Tag this with
:class:`~asyoulikeit.Importance` on columns, and if needed on
individual rows:

.. code-block:: python

   from asyoulikeit import Importance

   data = (
       TableContent()
       .add_column("name", "Name")                                    # ESSENTIAL (the default)
       .add_column("notes", "Notes", importance=Importance.DETAIL)
       .add_row(name="Alice", notes="Joined 2024-03")                 # essential row (the default)
       .add_row(name="Bob",   notes="Deprecated",
                _importance=Importance.DETAIL)
   )

When the user passes ``--essential``, DETAIL columns and DETAIL rows
drop out. When they pass ``--detailed``, everything stays. The default
is ``AUTO``, which each formatter resolves to whatever makes sense for
itself: TSV picks ``ESSENTIAL`` (pipe-friendly), JSON and display pick
``DETAILED`` (self-describing or human-facing).


Multiple reports
----------------

A single command can return more than one report. All reports are
rendered by default; the user narrows with ``--report <name>``, or
passes ``--report`` multiple times.

.. code-block:: python

   return Reports(
       users=Report(data=users_data),
       roles=Report(data=roles_data),
   )

Use ``@report_output(default_reports=None)`` to make a command
silent by default — useful for action commands that should produce no
visible output unless the user asks for a specific report. Use
``@report_output(default_reports=["users"])`` to show only a
specific subset by default.


.. _tree-content:

Tree content
------------

When your data is hierarchical — a filesystem subtree, an organisation
chart, a syntax tree — return :class:`~asyoulikeit.TreeContent` from
your handler instead of ``TableContent``. The API is deliberately
parallel: you declare a column schema just like for a table, but every
*node* in the tree carries values matching that schema (homogeneous
columns across all nodes) and nodes form a parent/child hierarchy
instead of a flat list.

.. code-block:: python

   from asyoulikeit import (
       Importance, Report, Reports, TreeContent, report_output,
   )

   @click.command()
   @report_output
   def list_usr():
       tree = (
           TreeContent(title="/usr")
           .add_column("name", "Name", header=True)
           .add_column("size", "Size")
           .add_column("kind", "Kind", importance=Importance.DETAIL)
       )
       usr = tree.add_root(name="/usr", size=0, kind="dir")
       bin_dir = usr.add_child(name="bin", size=4096, kind="dir")
       bin_dir.add_child(name="ls", size=150_296, kind="exec")
       bin_dir.add_child(name="cat", size=52_024, kind="exec")
       return Reports(fs=Report(data=tree))

Key differences from ``TableContent``:

* **Exactly one column must be marked** ``header=True``. Trees always
  need a label for each node; that label is what the display formatter
  draws alongside the ASCII-art connectors.
* **``add_root`` is repeatable**. Call it once for a single tree, many
  times to build a forest — useful when listing several independent
  top-level items.
* **``Node.add_child(...)`` returns the new child**, so you descend by
  keeping a reference to each level you need. Siblings come from
  calling ``add_child`` on the shared parent again.
* **Per-node** :class:`~asyoulikeit.Importance` **tagging prunes whole
  subtrees**. A node marked ``DETAIL`` and *all its descendants* drop
  out under ``--essential``, because you cannot show a child while
  hiding its parent.

The three built-in formatters each render trees in the way best suited
to their audience:

* ``display`` lays ASCII-art connectors (``├──``, ``└──``, ``│``) into
  the first column of a Rich table, with the other columns lining up
  as usual.
* ``tsv`` flattens the tree in pre-order and indents the header-column
  value two spaces per level of depth, preserving tab separation so
  downstream tools still parse cleanly.
* ``json`` emits a nested ``{"values": {...}, "children": [...]}``
  structure under a ``"roots"`` list, with ``metadata.kind = "tree"``
  distinguishing it from table-shaped output.


Transposition
-------------

Sometimes a table reads better flipped: columns of values paired with
a label column on the left rather than a header row on top. Set
``present_transposed=True`` on ``TableContent`` and the ``display`` and
``tsv`` formatters will rotate the data at render time. JSON is
unaffected — it's a structural format, not a visual one, and surfaces
the intent via a ``metadata.present_transposed`` flag instead.


Styling
-------

The ``display`` formatter supports per-cell styling (foreground colour,
background colour, bold, italic). Attach a second ``TableContent`` to
your ``Report`` via the ``styles`` argument, with the same shape as the
data table but cell values as dictionaries keyed by
:data:`~asyoulikeit.STYLE_FOREGROUND_COLOR`,
:data:`~asyoulikeit.STYLE_BOLD`, and so on. TSV and JSON ignore styles;
display applies them via Rich.


Custom formatters
-----------------

The built-in ``display``, ``tsv``, and ``json`` formatters are
stevedore-loaded entry points under the ``asyoulikeit.formatter``
namespace. Third-party packages (or your own consumer project) can
register additional formatters the same way:

.. code-block:: toml

   # in the consumer's pyproject.toml
   [project.entry-points."asyoulikeit.formatter"]
   xml = "mypackage.xml_formatter:Formatter"

Subclass :class:`~asyoulikeit.Formatter` and implement the single
``format(reports) -> str`` method. After ``pip install`` / ``uv sync``
of the registering package, the new format name appears automatically
in the ``--as`` choices of every command decorated with
``@report_output``.


.. _testing:

Testing commands that use ``@report_output``
--------------------------------------------

Click's :class:`click.testing.CliRunner` captures stdout into a string
buffer. That buffer's ``isatty()`` returns ``False``, so the smart
default for ``--as`` lands on ``tsv``. If the test has assertions
about TSV output that's fine — you don't need to do anything. But if
your assertions depend on ``display``-mode layout (Rich borders,
titles, colour, wrapped text) or ``json`` structure, the captured
buffer's default doesn't exercise that path.

Two ways to get the format you want in tests:

**Pin the format on each invocation.** Pass ``--as <format>``
explicitly to the command under test:

.. code-block:: python

   def test_my_command_renders_the_title(runner):
       result = runner.invoke(cli, ["my-command", "--as", "display", "input"])
       assert "My Title" in result.output   # only visible in display mode

This is the clearest option when a handful of tests care about format;
the intent is visible at the call site and each test remains self-
contained.

**Set the ``ASYOULIKEIT_FORMAT`` environment variable.** The
decorator consults ``ASYOULIKEIT_FORMAT`` before falling back to the
TTY check, so a session-wide, conftest-wide, or even test-wide
override is one line away:

.. code-block:: python

   # conftest.py — force display mode for every test in the suite
   import os
   os.environ["ASYOULIKEIT_FORMAT"] = "display"

   # or per-test with pytest's monkeypatch fixture
   def test_display_layout(runner, monkeypatch):
       monkeypatch.setenv("ASYOULIKEIT_FORMAT", "display")
       result = runner.invoke(cli, ["my-command", "input"])
       assert "My Title" in result.output

Precedence: an explicit ``--as`` on the command line still wins over
``ASYOULIKEIT_FORMAT``, so individual tests can opt out of a
suite-wide default without interference. An invalid value in the env
var fails fast with a clear error rather than silently falling back,
so typos don't quietly change which rendering path a test exercises.
