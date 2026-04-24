"""Exception hierarchy for the asyoulikeit package."""


class AsyoulikeitError(Exception):
    """Base class for all exceptions raised by the asyoulikeit package."""
    pass


class ReportDeclarationError(AsyoulikeitError):
    """Raised when a ``@report_output`` command violates its ``reports=`` declaration.

    Thrown at two distinct points:

    * **Decoration time** — when the ``reports=`` mapping is ill-formed
      (non-identifier keys, non-``Ellipsis`` non-string keys, or a
      ``default_reports`` entry naming a report that wasn't declared).
    * **Runtime** — when the handler returns a :class:`~asyoulikeit.Reports`
      containing a name that wasn't declared, and the declaration has no
      ``Ellipsis`` slot to admit dynamic names.
    """
    pass
