"""Request paths: building them from caller data.

Every resource method that puts an id or a name into a URL path passes it
through :func:`segment` first. Nothing else in the client builds a path from
caller data.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

#: Values that no encoding keeps inside one path segment. ``httpx`` resolves
#: ``.`` and ``..`` as dot segments, and an empty value collapses ``a//b`` into
#: a different route, so each is refused rather than sent.
_REFUSED = frozenset({"", ".", ".."})


def segment(value: Any, field: str) -> str:
    """``value`` as exactly one percent-encoded path segment.

    Warning: An id or a name is caller data, and an unencoded ``/`` or a dot segment
    re-targets the request: ``httpx`` resolves
    ``.../indices/idx/documents/..`` to ``.../indices/idx``, which turns a
    one-document delete into a delete of the whole index. Every ``/``, ``?``,
    ``#`` and ``%`` is encoded, and ``""``, ``.`` and ``..``, which no encoding
    keeps inside one segment, are refused before anything is sent.

    A non-string value (a :class:`uuid.UUID`, say) is converted with ``str``
    first, as an f-string would. A UUID, or any other value made only of
    letters, digits and ``-._~``, encodes to itself.

    Raises:
        ValueError: If ``value`` is empty, ``.`` or ``..``.
    """
    text = value if isinstance(value, str) else str(value)
    if text in _REFUSED:
        raise ValueError(f"{field} must be one path segment, got {text!r}")
    return quote(text, safe="")
