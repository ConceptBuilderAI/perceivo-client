"""Canonicalisation: build the string that is signed.

The signing secret does not pass through this module, so a canonical request is
safe to log.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid

from perceivo_client.signing._constants import (
    CANONICAL_AUDIENCE_PATTERN,
    CANONICAL_DOMAIN,
    EMPTY_BODY_SHA256,
    BodyType,
    ContentTypeType,
    OrganizationType,
)
from perceivo_client.signing._errors import SigningError
from perceivo_client.signing._header_fields import (
    canonical_content_type,
    canonical_organization,
)
from perceivo_client.signing._target import (
    canonical_path,
    canonical_query,
    split_target,
)

__all__ = [
    "SigningError",
    "body_sha256_hex",
    "build_canonical_request",
    "canonical_audience",
    "canonical_content_type",
    "canonical_key_id",
    "canonical_organization",
    "canonical_path",
    "canonical_query",
    "generate_nonce",
    "split_target",
]

# ``\A``/``\Z`` anchors: ``$`` would also match before a trailing newline.
_AUDIENCE_RE = re.compile(CANONICAL_AUDIENCE_PATTERN)
_METHOD_RE = re.compile(r"\A[A-Z]+\Z")
_NONCE_RE = re.compile(r"\A[A-Za-z0-9_-]{8,128}\Z")
_TIMESTAMP_RE = re.compile(r"\A(0|[1-9][0-9]*)\Z")


def body_sha256_hex(body: BodyType) -> str:
    """Return canonical field 7: the lowercase hex SHA-256 of the request body.

    ``None`` and an empty body both yield :data:`EMPTY_BODY_SHA256`, the digest of
    zero bytes. A ``str`` is encoded as UTF-8 with no Unicode normalisation.

    Raises:
        SigningError: If ``body`` is a stream, iterator, or any other type whose
            bytes are not available up front. Such a body cannot be signed.
    """
    if body is None:
        return EMPTY_BODY_SHA256
    if isinstance(body, str):
        payload = body.encode("utf-8")
    elif isinstance(body, (bytes, bytearray, memoryview)):
        payload = bytes(body)
    else:
        raise SigningError(
            "request body must be bytes, str, or None; a streaming or non-seekable "
            f"body cannot be signed (got {type(body).__name__}). Read it into bytes "
            "first and send those same bytes."
        )
    return hashlib.sha256(payload).hexdigest()


def canonical_audience(audience: str) -> str:
    """Return canonical field 2: the deployment's configured audience, validated.

    The audience is a configured label that identifies the deployment, such as
    ``perceivo-api-prod``. It must match :data:`CANONICAL_AUDIENCE_PATTERN`
    (1-64 characters from ``[A-Za-z0-9._:-]``) and is not normalised, so case is
    significant.

    Security notes:
        The audience is not a hostname and is never derived from a URL or a
        ``Host`` header, which proxies can rewrite. Nothing in this package
        accepts an absolute URL, so there is no authority to derive it from.

    Raises:
        SigningError: If the audience is ``None``, not a string, or does not
            match the pattern. A newline is rejected, never escaped.
    """
    if audience is None:
        raise SigningError(
            "audience is required and has no default; it is the deployment constant "
            "the verifier binds against (e.g. 'perceivo-api-prod'). It must never be "
            "derived from a URL or a Host header."
        )
    if not isinstance(audience, str):
        raise SigningError(f"audience must be str, got {type(audience).__name__}")
    if not _AUDIENCE_RE.match(audience):
        raise SigningError(
            "audience must be 1-64 characters from [A-Za-z0-9._:-]; it is an opaque "
            "configured label such as 'perceivo-api-prod', never a hostname or a URL"
        )
    return audience


def canonical_key_id(key_id: str | uuid.UUID) -> str:
    """Return canonical field 3: the API key id as a lowercase, hyphenated UUID.

    The key id is the UUID that identifies the API key, for example
    ``0f8fad5b-d9cb-469f-a165-70867728950e``. It is not the key prefix, which
    every key in an organization shares.

    The value is parsed with :class:`uuid.UUID` and rendered with ``str()``, so
    every spelling :class:`uuid.UUID` accepts (uppercase, braced, unhyphenated)
    produces the same field and the same signature.

    Raises:
        SigningError: If ``key_id`` is empty or is not a UUID.
    """
    if isinstance(key_id, uuid.UUID):
        return str(key_id)
    if not isinstance(key_id, str) or not key_id:
        raise SigningError("key_id must be a non-empty string")
    try:
        parsed = uuid.UUID(key_id)
    except (ValueError, AttributeError, TypeError):
        raise SigningError(
            "key_id must be the UUID, in any spelling uuid.UUID() accepts; "
            "it is normalised to the lowercase hyphenated 8-4-4-4-12 form before it is "
            "signed. It is NOT the key prefix, which every key in an organization shares."
        ) from None
    return str(parsed)


def _canonical_method(method: str) -> str:
    if not isinstance(method, str):
        raise SigningError(f"method must be str, got {type(method).__name__}")
    if not _METHOD_RE.match(method):
        raise SigningError(
            f"method must be uppercase ASCII letters, got {method!r}. It is signed "
            "exactly as it appears on the request line and is never normalized — "
            "uppercase it before calling, so what you sign is what you send."
        )
    return method


def _canonical_timestamp(timestamp: int | str) -> str:
    if isinstance(timestamp, (bool, float)):
        raise SigningError("timestamp must be Unix seconds as an int or a digit string")
    text = str(timestamp) if isinstance(timestamp, int) else timestamp
    if not isinstance(text, str) or not _TIMESTAMP_RE.match(text):
        raise SigningError(
            "timestamp must be base-10 Unix seconds with no sign, fractional part, "
            f"or leading zero, got {timestamp!r}"
        )
    return text


def _canonical_nonce(nonce: str) -> str:
    if not isinstance(nonce, str) or not _NONCE_RE.match(nonce):
        raise SigningError(
            "nonce must be 8-128 characters from [A-Za-z0-9_-]; generate it with "
            "generate_nonce() so it comes from a CSPRNG"
        )
    return nonce


def generate_nonce(n_bytes: int = 24) -> str:
    """Return a new nonce from a cryptographically secure random source.

    The nonce uses the characters ``[A-Za-z0-9_-]``. The default of 24 bytes of
    entropy produces 32 characters, within the 8-128 characters the server
    accepts. A nonce is single-use: generate a new one for every attempt,
    including retries.

    Raises:
        SigningError: If ``n_bytes`` is less than 6.
    """
    if n_bytes < 6:
        raise SigningError("nonce needs at least 6 bytes of entropy")
    return secrets.token_urlsafe(n_bytes)


def build_canonical_request(
    *,
    audience: str,
    key_id: str | uuid.UUID,
    method: str,
    raw_path: bytes | str,
    query_string: bytes | str | None,
    body: BodyType,
    content_type: ContentTypeType,
    organization: OrganizationType,
    timestamp: int | str,
    nonce: str,
) -> str:
    """Build the canonical request string::

        perceivo-hmac-v1\\n{audience}\\n{key_id}\\n{METHOD}\\n{canonical_path}\\n
        {query}\\n{body_sha256_hex}\\n{content_type}\\n{organization}\\n{timestamp}\\n
        {nonce}

    Eleven fields joined by ten ``\\n`` separators, with no trailing newline. The
    string is encoded as UTF-8 once before it is passed to HMAC-SHA256.

    Every argument is keyword-only and required. Pass ``content_type=None`` or
    ``organization=None`` when the request does not carry that header.

    Args:
        audience: The deployment audience (field 2).
        key_id: The API key id (field 3).
        method: The HTTP method in uppercase, as sent on the request line.
        raw_path: The request path without its query string; use
            :func:`split_target` to split a combined target. Field 5 is the
            normalised path returned by :func:`canonical_path`.
        query_string: The query string without the leading ``?``, or ``None``.
        body: The exact request body bytes, a ``str`` to be encoded as UTF-8,
            or ``None``.
        content_type: The ``Content-Type`` header value, or ``None``.
        organization: The ``Perceivo-Organization`` header value, or ``None``.
        timestamp: Unix time in seconds.
        nonce: A single-use nonce from :func:`generate_nonce`.

    Returns:
        The canonical request string.

    Raises:
        SigningError: If any field is invalid.
    """
    return "\n".join(
        (
            CANONICAL_DOMAIN,
            canonical_audience(audience),
            canonical_key_id(key_id),
            _canonical_method(method),
            canonical_path(raw_path),
            canonical_query(query_string),
            body_sha256_hex(body),
            canonical_content_type(content_type),
            canonical_organization(organization),
            _canonical_timestamp(timestamp),
            _canonical_nonce(nonce),
        )
    )
