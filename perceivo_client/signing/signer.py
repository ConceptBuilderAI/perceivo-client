"""Request signing: :func:`sign_request` and :class:`RequestSigner`.

:func:`sign_request` signs one request and returns its ``X-Perceivo-*`` headers
and canonical request. :class:`RequestSigner` holds a key's credentials and signs
each request attempt with a new timestamp and nonce.

This module also re-exports :class:`SigningCredentials`,
:func:`resolve_signing_credentials`, :func:`compute_signature`,
:func:`verify_signature` and :func:`verify_signed_request`.

The signing secret is never logged, never included in an exception message and
never rendered by ``repr()``.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import unquote as _urllib_unquote

from perceivo_client.signing._constants import (
    HEADER_KEY_ID,
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    BodyType,
    ContentTypeType,
    OrganizationType,
    SecretType,
)
from perceivo_client.signing._credentials import (
    SigningCredentials,
    _validate_key_id,
    resolve_signing_credentials,
)
from perceivo_client.signing._verify import (
    compute_signature,
    verify_signature,
    verify_signed_request,
)
from perceivo_client.signing.canonical import (
    SigningError,
    _canonical_nonce,
    _canonical_timestamp,
    build_canonical_request,
    generate_nonce,
    split_target,
)

__all__ = [
    "RequestSigner",
    "SignedRequest",
    "SigningCredentials",
    "compute_signature",
    "resolve_signing_credentials",
    "sign_request",
    "verify_signature",
    "verify_signed_request",
]


# Separators a server may accept between query elements. `;` is a legacy separator
# that some frameworks still honour.
_QUERY_SEPARATORS = re.compile(r"[&;]")

# Query parameter names that carry a credential. The API reads an API key from the
# `api_key` query parameter. Names are compared after normalisation, so `API_KEY`,
# `api%5Fkey` and a name with surrounding spaces all match.
_CREDENTIAL_PARAM_NAMES = frozenset({"api_key"})


@dataclass(frozen=True)
class SignedRequest:
    """The signature material for one request attempt.

    ``canonical_request`` contains no secret and is safe to log. Comparing it
    with another implementation's is the first step in diagnosing a signature
    mismatch.
    """

    key_id: str
    timestamp: str
    nonce: str
    signature: str
    canonical_request: str
    #: The audience, ``Content-Type`` and organization that were signed, for
    #: diagnostics. None of them is sent in an ``X-Perceivo-*`` header: the
    #: audience is configuration on both ends, and the request already carries
    #: the other two. :attr:`headers` never includes ``Perceivo-Organization``;
    #: the signature commits to the header the caller sends.
    audience: str = ""
    content_type: str = ""
    organization: str = ""

    @property
    def headers(self) -> dict[str, str]:
        """The four ``X-Perceivo-*`` headers to add to the request."""
        return {
            HEADER_KEY_ID: self.key_id,
            HEADER_TIMESTAMP: self.timestamp,
            HEADER_NONCE: self.nonce,
            HEADER_SIGNATURE: self.signature,
        }


def _normalise_query_param_name(raw_name: str) -> str:
    """Normalise a query parameter name to the form a lenient server would read.

    Percent-decoding is lenient: a malformed escape is kept as written rather than
    raising.
    """
    name = raw_name.strip().replace("+", " ")
    if "%" in name:
        # unquote() never raises; an invalid escape is kept verbatim, so the guard
        # errs towards matching.
        name = _urllib_unquote(name)
    return name.strip().lower()


def _reject_api_key_in_query(query: str) -> None:
    """Refuse to sign a request that carries a credential in its query string.

    A credential in a URL is recorded in access logs, proxy logs, browser history
    and ``Referer`` headers. Parameter names are matched the way a lenient server
    parses them, so each of these is refused:

    ==========================  ================================================
    ``API_KEY=...``             names are compared case-insensitively
    ``api%5Fkey=...``           ``%5F`` decodes to ``_``
    ``%20api_key=...``          surrounding spaces are ignored
    ``a=1;api_key=...``         ``;`` is accepted as a separator
    ==========================  ================================================

    Raises:
        SigningError: If any query parameter name normalises to ``api_key``.
    """
    for element in _QUERY_SEPARATORS.split(query):
        name = _normalise_query_param_name(element.partition("=")[0])
        if name in _CREDENTIAL_PARAM_NAMES:
            # Report the normalised name, never the raw element: it is
            # caller-controlled and the message may be logged.
            raise SigningError(
                f"a signed request must not carry '{name}' in the query string "
                "(any spelling a server would decode to it); send the credential "
                "in the X-API-Key header"
            )


def sign_request(
    *,
    method: str,
    target: bytes | str,
    body: BodyType = None,
    content_type: ContentTypeType,
    organization: OrganizationType,
    key_id: str,
    secret: SecretType,
    audience: str,
    timestamp: int | str | None = None,
    nonce: str | None = None,
) -> SignedRequest:
    """Sign one request and return its headers and canonical request.

    Call this after the request is final. ``content_type`` must be the header the
    request will carry; for a multipart body the HTTP client generates the
    boundary, so a signature computed earlier does not match.
    :class:`~perceivo_client._transport.Transport` builds the request with
    ``httpx`` before it signs it.

    Args:
        method: The HTTP method in uppercase, exactly as it will be sent.
        target: The origin-form request target exactly as it will be sent,
            including any query string, for example
            ``/v1/orchestrations?page_size=10``.
        body: The exact bytes that will be sent, or ``None`` for no body.
        content_type: The ``Content-Type`` header, verbatim, or ``None`` if the
            request has none. Required.
        organization: The ``Perceivo-Organization`` header, verbatim, or ``None``
            if the request has none. Required. It must be the lowercase,
            hyphenated UUID the request sends; other spellings are rejected, not
            normalised.
        key_id: The API key id. It is normalised to the lowercase, hyphenated
            UUID form before it is signed and sent.
        secret: The signing secret as issued (64 lowercase hex characters), which
            is decoded to the 32-byte key. Pass ``bytes`` only if you hold the key
            bytes themselves.
        audience: The deployment's configured audience, for example
            ``perceivo-api-prod``. Required. It is never derived from a URL or a
            ``Host`` header.
        timestamp: Unix time in seconds. Defaults to the current time.
        nonce: A single-use nonce. Defaults to a new random nonce; never reuse
            one.

    Returns:
        The signature material. Add :attr:`SignedRequest.headers` to the request.

    Raises:
        SigningError: If any input cannot be signed, including an ``api_key``
            query parameter. The message never contains the secret.
    """
    raw_path, query = split_target(target)
    _reject_api_key_in_query(query)
    resolved_ts = _canonical_timestamp(int(time.time()) if timestamp is None else timestamp)
    resolved_nonce = _canonical_nonce(generate_nonce() if nonce is None else nonce)
    resolved_key_id = _validate_key_id(key_id)
    canonical = build_canonical_request(
        audience=audience,
        key_id=resolved_key_id,
        method=method,
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=content_type,
        organization=organization,
        timestamp=resolved_ts,
        nonce=resolved_nonce,
    )
    fields = canonical.split("\n")
    return SignedRequest(
        key_id=resolved_key_id,
        timestamp=resolved_ts,
        nonce=resolved_nonce,
        signature=compute_signature(canonical, secret),
        canonical_request=canonical,
        audience=fields[1],
        content_type=fields[7],
        organization=fields[8],
    )


class RequestSigner:
    """Signs requests for one key.

    Each call to :meth:`sign` uses a new timestamp and a new nonce, so it is
    correct to call it on every attempt inside a retry loop: the server rejects a
    reused nonce as a replay. Instances are reusable and thread-safe, and the
    secret is redacted from ``repr()``.

    Args:
        credentials: The key id, signing secret and audience to sign with.
        nonce_factory: Returns a new nonce. Defaults to :func:`generate_nonce`.
        clock: Returns the current Unix time. Defaults to :func:`time.time`.

    Raises:
        SigningError: If ``credentials`` is not a :class:`SigningCredentials`.
    """

    __slots__ = ("_clock", "_credentials", "_nonce_factory")

    def __init__(
        self,
        credentials: SigningCredentials,
        *,
        nonce_factory=generate_nonce,
        clock=time.time,
    ) -> None:
        if not isinstance(credentials, SigningCredentials):
            raise SigningError("credentials must be a SigningCredentials instance")
        self._credentials = credentials
        self._nonce_factory = nonce_factory
        self._clock = clock

    @property
    def key_id(self) -> str:
        """The normalised key id this signer signs with."""
        return self._credentials.key_id

    @property
    def audience(self) -> str:
        """The audience this signer signs for."""
        return self._credentials.audience

    def sign(
        self,
        method: str,
        target: bytes | str,
        body: BodyType = None,
        *,
        content_type: ContentTypeType,
        organization: OrganizationType,
    ) -> SignedRequest:
        """Sign one request attempt with a new timestamp and nonce.

        ``content_type`` and ``organization`` are keyword-only and required: pass
        the headers the request will carry, or ``None`` if it carries none. The
        organization can differ between requests, so it is passed per call
        rather than held by the signer. The key id, secret and audience come from
        the credentials.

        See :func:`sign_request` for the arguments and exceptions.
        """
        return sign_request(
            method=method,
            target=target,
            body=body,
            content_type=content_type,
            organization=organization,
            key_id=self._credentials.key_id,
            secret=self._credentials.signing_secret,
            audience=self._credentials.audience,
            timestamp=int(self._clock()),
            nonce=self._nonce_factory(),
        )

    def __repr__(self) -> str:
        return (
            f"RequestSigner(key_id={self._credentials.key_id!r}, signing_secret=<redacted>, "
            f"audience={self._credentials.audience!r})"
        )

    __str__ = __repr__
