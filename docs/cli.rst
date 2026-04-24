Command-line options
====================

Any tool built with ``asyoulikeit`` gains a standard set of
output-formatting options on every ``@report_output``-decorated
command. If a project documents its CLI as being powered by
``asyoulikeit``, everything on this page applies.


``--as <format>``
-----------------

Selects the output format. Three values ship with ``asyoulikeit``:

``display``
  Human-facing output: bordered tables, colour, bold and italic
  typography. The default when the command is attached to a terminal.

``tsv``
  Tab-separated values, one row per line, with the column headers
  emitted as a comment prefix (``# Name<TAB>Role<TAB>…``) so tools like
  ``awk``, ``cut``, and ``grep`` can skip the header line without a
  special flag. The default when stdout is a pipe.

``json``
  A pretty-printed JSON object. All reports from one invocation are
  collected under a top-level ``"reports"`` key, with per-report
  metadata, column schema, and structured rows. This is the format to
  pick when you're consuming the output from another program, or
  piping it through ``jq``.

Individual projects are free to register additional formats; run any
command with ``--help`` to see the full list available in that tool.

When ``--as`` is not given on the command line, the format is resolved
in this precedence:

1. ``--as`` on the command line (highest).
2. The ``ASYOULIKEIT_FORMAT`` environment variable, if set to a valid
   format name. An invalid value fails fast with a clear error;
   matching is case-insensitive.
3. The TTY-sensing default: ``display`` when stdout is a terminal,
   ``tsv`` when it is a pipe (lowest).

Setting ``ASYOULIKEIT_FORMAT`` in a shell profile is the standard way
to make a tool default to JSON (or anything else) without having to
type ``--as`` every time. Test harnesses — where captured stdout
typically isn't a TTY — use the same lever to force ``display``
without touching every test case; see :ref:`testing` in the usage
guide.


``--report <name>``
-------------------

Names one of the reports the command produces. Pass it multiple times
to request several named reports. When omitted, the command's default
— usually all reports — is shown. Unknown names produce a warning on
stderr listing the reports that were actually available (when the
command declared its reports statically, unknown names fail at parse
with Click's list of valid values instead).

.. code-block:: bash

   mytool status --report users                    # just the users table
   mytool status --report users --report groups    # both, in the order given


``--no-reports``
----------------

Suppresses all report rendering while still running the handler. The
use case is an action command whose reports are useful interactively
but unwanted in other contexts — e.g. an ``import`` command that prints
a summary of what was imported when run by a human, but whose output
is noise in a CI pipeline where the import is logged elsewhere. The
handler's side effects still run; drift detection and the return-type
check still fire. Mutually exclusive with ``--report``: asking for
specific reports and simultaneously suppressing all of them is
incoherent, so the combination fails at parse.

.. code-block:: bash

   mytool import data.yaml --no-reports            # run the import, stay silent


``--header`` / ``--no-header``
------------------------------

Overrides the command's default about whether to emit column headings
and titles. Behaviour varies by format:

- For ``tsv``, ``--no-header`` suppresses the ``# Name<TAB>…`` comment
  line entirely, leaving only data rows — useful when feeding
  fixed-schema output into a downstream tool that already knows the
  columns.
- For ``display``, ``--no-header`` drops both the column headers and
  the title / description above and below the table.
- For ``json``, the flag has no effect: JSON is self-describing and
  always includes the schema metadata.

When the flag is absent, each formatter chooses its own default per
content type. For tables and trees that default is ``--header``
everywhere (column labels and titles are the structural information
a consumer wants). For :class:`~asyoulikeit.ScalarContent`, the TSV
formatter defaults to ``--no-header`` — a single-value report
piped to another tool (``disc title image | pbcopy``) wants the raw
answer, not a commented label. Explicit ``--header`` always wins.


``--detailed`` / ``--essential``
--------------------------------

Controls how much of each report is shown. Tables built with
``asyoulikeit`` can mark some columns and rows as supplementary
("detail") versus core ("essential"). The two flags override the
format-specific default:

- ``--essential`` drops every detail column and detail row. Use it
  when you want the minimum, parse-friendly view.
- ``--detailed`` keeps every detail column and detail row. Use it when
  you want the maximum, human-friendly view.

When neither flag is given, the format decides for itself. ``tsv``
picks *essential* (machine-oriented); ``display`` and ``json`` pick
*detailed* (self-describing or human-facing).


Combining options
-----------------

The options compose freely:

.. code-block:: bash

   # pipe-friendly, minimal view
   mytool status --as tsv --essential --no-header | awk -F'\t' '{print $1}'

   # maximum detail as JSON for a script
   mytool status --as json --detailed | jq '.reports.users.rows'

   # human-readable, one specific report only
   mytool status --report users

   # exactly what you'd get by piping, but without actually piping
   mytool status --as tsv

As a rule of thumb: a command attached to a terminal with no options
gives you the fullest human-readable form. The same command in a
pipeline gives you the most machine-readable form. Everything in
between is explicit.
