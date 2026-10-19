"""Percent-encoding for caller data placed in request paths."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

#: Values that no encoding keeps inside one path segment. ``httpx`` resolves
#: ``.`` and ``..`` as dot segments, and an empty value collapses ``a//b`` into
#: a different route, so each is refused rather than sent.
_REFUSED = frozenset({"", ".", ".."})


def segment(value: Any, field: str) -> str:
    """``value`` as one percent-encoded path segment.

    Every ``/``, ``?``, ``#`` and ``%`` is encoded, so an id or a name cannot
    re-target the request. A non-string value (a :class:`uuid.UUID`, say) is
    converted with ``str`` first.

    Raises:
        ValueError: If ``value`` is empty, ``.`` or ``..``, which no encoding
            keeps inside one segment.
    """
    text = value if isinstance(value, str) else str(value)
    if text in _REFUSED:
        raise ValueError(f"{field} must be one path segment, got {text!r}")
    return quote(text, safe="")
