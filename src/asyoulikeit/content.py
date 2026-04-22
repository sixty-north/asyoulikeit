"""Abstract base for report content.

A :class:`Report` holds one :class:`ReportContent` value (currently always a
:class:`~asyoulikeit.TabularData` — trees and other kinds are planned).
Formatters iterate reports and dispatch on the concrete content type to
render each appropriately.

The protocol is intentionally minimal in this first cut: only :meth:`kind`
is required. Common concerns that might eventually be lifted up (title /
description hooks, detail-level filtering protocol, ...) are deliberately
left to each concrete subclass until a second content kind exists to
triangulate what's genuinely shared.
"""

from abc import ABC, abstractmethod


class ReportContent(ABC):
    """Marker base class for the content carried by a :class:`Report`.

    Every concrete content kind (currently :class:`TabularData`) inherits
    from this class and declares a stable short identifier via
    :meth:`kind`. Formatters use the identifier — or an ``isinstance``
    check — to pick an appropriate rendering path.
    """

    @classmethod
    @abstractmethod
    def kind(cls) -> str:
        """A short, stable identifier for this content kind.

        Returns:
            A token like ``"tabular"`` or (in future) ``"tree"``. Used by
            formatters and tooling to dispatch on content type.
        """
