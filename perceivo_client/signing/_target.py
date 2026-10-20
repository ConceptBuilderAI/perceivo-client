"""Request-target handling: splitting a target and canonicalising its path and query.

These functions operate on the origin-form request target an HTTP client writes
on the request line. They are pure functions of their input and never see the
signing secret.
"""

from __future__ import annotations

import re

from perceivo_client.signing._errors import SigningError

__all__ = [
    "canonical_path",
    "canonical_query",
    "split_target",
]

# Printable ASCII, no space and no control characters: what may appear in an
# origin-form request target.
_TARGET_RE = re.compile(r"\A[\x21-\x7e]*\Z")
# RFC 3986 section 2.3 `unreserved` characters. These are the only escapes the
# path transform decodes; every other escape is kept as written, including its
# hex case.
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
# A well-formed percent escape. A stray '%' or '%zz' does not match and is kept
# as written.
_PCT_ESCAPE_RE = re.compile(r"%([0-9A-Fa-f]{2})")


def _as_ascii(value: bytes | str, what: str) -> str:
    """Return ``value`` as a printable-ASCII ``str`` or raise :class:`SigningError`."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        try:
            value = bytes(value).decode("ascii")
        except UnicodeDecodeError:
            raise SigningError(
                f"{what} must be ASCII; percent-encode non-ASCII bytes before signing"
            ) from None
    if not isinstance(value, str):
        raise SigningError(f"{what} must be str or bytes, got {type(value).__name__}")
    if not _TARGET_RE.match(value):
        raise SigningError(
            f"{what} must be printable ASCII with no spaces or control characters; "
            "percent-encode it exactly as your HTTP client will send it"
        )
    return value


def split_target(target: bytes | str) -> tuple[str, str]:
    """Split an origin-form request target into ``(raw_path, query_string)``.

    ``target`` is what an HTTP client writes on the request line, for example
    ``/v1/orchestrations?limit=10``. The split is on the first ``?``, which
    belongs to neither part.

    Raises:
        SigningError: If the target is not origin-form (does not start with
            ``/``), carries a fragment, ends in a bare ``?``, or is not
            printable ASCII.
    """
    text = _as_ascii(target, "request target")
    if not text.startswith("/"):
        raise SigningError(
            "request target must be origin-form and start with '/'; absolute-form "
            "URLs and 'OPTIONS *' cannot be signed because the origin never sees them"
        )
    if "#" in text:
        raise SigningError(
            "request target must not contain a fragment; '#...' is discarded before "
            "the origin sees the request and therefore cannot be signed"
        )
    raw_path, sep, query = text.partition("?")
    if sep and not query:
        raise SigningError(
            "request target must not end in a bare '?'; an empty query is "
            "indistinguishable from no query — send the path without the '?'"
        )
    return raw_path, query


def _decode_unreserved(path: str) -> str:
    """Percent-decode escapes of unreserved characters only.

    ``%7e`` and ``%7E`` both become ``~``. Every other escape is kept as written,
    including its hex case: ``%2F`` stays ``%2F`` and ``%2f`` stays ``%2f``.
    Decoding a reserved escape would make ``/a%2Fb`` and ``/a/b`` sign alike,
    although they address different resources.
    """

    def replace(match: re.Match[str]) -> str:
        char = chr(int(match.group(1), 16))
        return char if char in _UNRESERVED else match.group(0)

    return _PCT_ESCAPE_RE.sub(replace, path)


def _remove_dot_segments(path: str) -> str:
    """Remove dot segments as specified by RFC 3986 section 5.2.4.

    The algorithm follows the RFC step by step, including branches an origin-form
    path cannot reach. ``output`` holds whole segments, each with its leading
    ``/``, so removing the last element removes the last segment and its
    preceding ``/``.
    """
    remaining = path
    output: list[str] = []
    while remaining:
        remaining = _dot_segment_step(remaining, output)
    return "".join(output)


def _dot_segment_step(remaining: str, output: list[str]) -> str:
    """Run one iteration of the RFC 3986 section 5.2.4 loop.

    Each branch is one lettered step of the RFC, tried in order. ``output`` is the
    RFC's output buffer and is updated in place.

    Returns:
        The remaining input buffer.
    """
    if remaining.startswith("../"):  # 2A
        return remaining[3:]
    if remaining.startswith("./"):  # 2A
        return remaining[2:]
    if remaining.startswith("/./"):  # 2B
        return "/" + remaining[3:]
    if remaining == "/.":  # 2B
        return "/"
    if remaining.startswith("/../") or remaining == "/..":  # 2C
        if output:
            output.pop()
        # For "/.." the slice is empty, leaving "/" as the RFC requires.
        return "/" + remaining[4:]
    if remaining in (".", ".."):  # 2D
        return ""
    # 2E: move one segment to the output buffer.
    end = remaining.find("/", 1)
    if end == -1:
        output.append(remaining)
        return ""
    output.append(remaining[:end])
    return remaining[end:]


def canonical_path(raw_path: bytes | str) -> str:
    """Return canonical field 5: the normalised request path.

    Two operations are applied, in this order:

    1. Percent-decode escapes of unreserved characters (``A-Z a-z 0-9 - . _ ~``),
       in either hex case. Every other escape is kept as written.
    2. Remove dot segments as specified by RFC 3986 section 5.2.4.

    Nothing else changes: ``//`` is not merged, a trailing ``/`` is kept, and a
    reserved escape is neither decoded nor case-normalised. The order matters:
    ``%2E`` decodes to ``.`` in step 1 and is then removed as a dot segment, so
    ``/a/%2E%2E/b`` becomes ``/b``.

    The API applies the same normalisation to the path before routing a request,
    so the signature covers the path the server acts on. Targets that normalise
    to the same path, such as ``/a/%7eb`` and ``/a/~b``, therefore share a
    signature.

    Args:
        raw_path: The request path, without its query string.

    Returns:
        The normalised path.

    Raises:
        SigningError: If the path is not origin-form, contains ``?`` or ``#``, or
            is not printable ASCII.
    """
    path = _as_ascii(raw_path, "raw_path")
    if not path.startswith("/"):
        raise SigningError(
            "raw_path must be origin-form and start with '/'; absolute-form URLs "
            "and 'OPTIONS *' cannot be signed because the origin never sees them"
        )
    if "?" in path or "#" in path:
        raise SigningError(
            "raw_path must not contain '?' or '#'; pass the query separately "
            "(use split_target() to split a combined target)"
        )
    return _remove_dot_segments(_decode_unreserved(path))


def canonical_query(query_string: bytes | str | None) -> str:
    """Return canonical field 6: the raw query string, verbatim.

    The field is every byte after the first ``?`` of the request target, in the
    order sent. Nothing is split, sorted, decoded, re-encoded or deduplicated. An
    empty or absent query yields ``""``. The only check is that the query is
    printable ASCII, as an HTTP client writes it on the request line.

    Args:
        query_string: The query string without the leading ``?``, or ``None``.

    Returns:
        The query string, unchanged.

    Raises:
        SigningError: If the query string is not printable ASCII.
    """
    if query_string is None:
        return ""
    return _as_ascii(query_string, "query string")
