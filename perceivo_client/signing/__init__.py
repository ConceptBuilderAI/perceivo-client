"""HMAC-SHA256 request signing for the Perceivo API (signature version ``v1``).

The package uses only the standard library, makes no network calls and does not
import ``httpx``, so it can be used without the client's transport. This
docstring is the full specification of the wire format.

Modules:

* :mod:`~perceivo_client.signing.canonical` builds the canonical request. It
  never handles the signing secret.
* :mod:`~perceivo_client.signing.signer` signs requests and verifies signatures.
* :mod:`~perceivo_client.signing.golden_vectors` provides the published test
  vectors.

The canonical request
=====================
Eleven fields joined by ten ``\\n`` (0x0A) separators, with no trailing newline::

    perceivo-hmac-v1\\n{audience}\\n{key_id}\\n{METHOD}\\n{canonical_path}\\n
    {query}\\n{sha256_hex(body)}\\n{content_type}\\n{organization}\\n{timestamp}\\n{nonce}

The string is encoded as UTF-8 and signed with HMAC-SHA256. The signature header
value is ``v1=`` followed by the lowercase hex digest.

==  ===================  =====================================================
#   Field                Value
==  ===================  =====================================================
1   domain               The constant ``perceivo-hmac-v1``.
2   audience             The deployment's configured audience.
3   key_id               The API key id as a lowercase, hyphenated UUID.
4   METHOD               The HTTP method, uppercase, as sent.
5   canonical_path       The path with unreserved escapes decoded and dot
                         segments removed.
6   query                The query string, verbatim; empty if absent.
7   body hash            Lowercase hex SHA-256 of the exact body bytes.
8   content_type         The ``Content-Type`` header, verbatim; empty if absent.
9   organization         The ``Perceivo-Organization`` header, verbatim; empty
                         if absent.
10  timestamp            Unix time in seconds.
11  nonce                8-128 characters from ``[A-Za-z0-9_-]``.
==  ===================  =====================================================

The signing key
===============
The HMAC key is 32 bytes. The platform issues it once as 64 lowercase hex
characters, and that text must be decoded, not encoded: a ``str`` of 64 hex
characters is decoded with ``bytes.fromhex``, any other ``str`` is encoded as
UTF-8, and ``bytes`` is used verbatim. Encoding the issued hex text as UTF-8
produces a 64-byte key that the server never accepts.

Rules
=====
* No field may contain ``\\n``. A field that would is rejected with
  :class:`SigningError`, never escaped.
* The audience identifies the deployment, for example ``perceivo-api-prod``. It
  is configuration, never derived from a URL or a ``Host`` header, and has no
  default and no environment variable. :func:`build_canonical_request`,
  :func:`sign_request` and :class:`SigningCredentials` all require it.
* Every spelling of the key id that :class:`uuid.UUID` accepts is normalised to
  the lowercase, hyphenated form; anything else is rejected. The
  ``X-Perceivo-Key-Id`` header carries the same normalised value.
* The method must already be uppercase. It is not normalised.
* The request target must be origin-form printable ASCII. Absolute-form targets,
  fragments and a target ending in a bare ``?`` are rejected.
* Sign the target exactly as it is sent: the raw, still-encoded path and
  query. The API canonicalises the path it receives and checks the signature
  over it.
* The path is normalised as the API normalises it before routing: escapes of
  unreserved characters are decoded, then dot segments are removed (RFC 3986
  section 5.2.4). Nothing else changes; ``//``, a trailing ``/`` and reserved
  escapes such as ``%2F`` are kept.
* The query string is signed verbatim, in the order sent. Because element order
  is signed, sign the request after it is final.
* ``Content-Type`` is signed verbatim, including its parameters, and must be
  printable ASCII. HTTP libraries generate multipart boundaries, so sign after
  the request is built.
* The organization must be a lowercase, hyphenated UUID or absent. Other
  spellings are rejected, not normalised. The server compares the signed value
  with the header it received.
* A repeated ``Content-Type`` or ``Perceivo-Organization`` header is rejected.
* An ``api_key`` query parameter is rejected by :func:`sign_request`; send the
  key in a header.
* The body hash covers the exact bytes sent. An absent or empty body hashes to
  :data:`EMPTY_BODY_SHA256`. A ``str`` body is encoded as UTF-8 without Unicode
  normalisation. Streaming bodies cannot be signed.
* The timestamp must be within :data:`MAX_CLOCK_SKEW_SECONDS` of the server
  clock. The nonce must come from a cryptographically secure source
  (:func:`generate_nonce`) and is single-use; :class:`RequestSigner` generates a
  new timestamp and nonce on every call, including retries.

Verification
============
:func:`verify_signature` checks the MAC only. :func:`verify_signed_request` also
checks the field count, the domain, the audience and the key id against values
the verifier holds. Neither checks timestamp freshness, nonce reuse or the
organization header; a server must do so itself.

Golden vectors
==============
:func:`load_golden_vectors` returns the published test vectors, which ship with
the package. Any implementation can check itself against them::

    from perceivo_client.signing import load_golden_vectors

    for vector in load_golden_vectors()["vectors"]:
        ...  # reproduce vector["canonical_request"] and vector["signature"]

``table["vector_counts"]`` gives the size of each list.

Secret handling
===============
The signing secret is never logged, never included in an exception message and
never rendered by ``repr()``. Signatures are compared with
``hmac.compare_digest``.
"""

from __future__ import annotations

from perceivo_client.signing._constants import (
    AUDIENCE_LOCAL,
    AUDIENCE_PRODUCTION,
    CANONICAL_AUDIENCE_PATTERN,
    CANONICAL_DOMAIN,
    CANONICAL_FIELD_COUNT,
    CANONICAL_ORGANIZATION_PATTERN,
    EMPTY_BODY_SHA256,
    HEADER_KEY_ID,
    HEADER_NONCE,
    HEADER_ORGANIZATION,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    MAX_CLOCK_SKEW_SECONDS,
    SIGNATURE_PREFIX,
    SIGNATURE_VERSION,
    BodyType,
    ContentTypeType,
    OrganizationType,
    SecretType,
)
from perceivo_client.signing.canonical import (
    SigningError,
    body_sha256_hex,
    build_canonical_request,
    canonical_audience,
    canonical_content_type,
    canonical_key_id,
    canonical_organization,
    canonical_path,
    canonical_query,
    generate_nonce,
    split_target,
)
from perceivo_client.signing.golden_vectors import (
    golden_vectors_bytes,
    load_golden_vectors,
)
from perceivo_client.signing.signer import (
    RequestSigner,
    SignedRequest,
    SigningCredentials,
    compute_signature,
    resolve_signing_credentials,
    sign_request,
    verify_signature,
    verify_signed_request,
)

__all__ = [
    "AUDIENCE_LOCAL",
    "AUDIENCE_PRODUCTION",
    "CANONICAL_AUDIENCE_PATTERN",
    "CANONICAL_DOMAIN",
    "CANONICAL_FIELD_COUNT",
    "CANONICAL_ORGANIZATION_PATTERN",
    "EMPTY_BODY_SHA256",
    "HEADER_KEY_ID",
    "HEADER_NONCE",
    "HEADER_ORGANIZATION",
    "HEADER_SIGNATURE",
    "HEADER_TIMESTAMP",
    "MAX_CLOCK_SKEW_SECONDS",
    "SIGNATURE_PREFIX",
    "SIGNATURE_VERSION",
    "BodyType",
    "ContentTypeType",
    "OrganizationType",
    "RequestSigner",
    "SecretType",
    "SignedRequest",
    "SigningCredentials",
    "SigningError",
    "body_sha256_hex",
    "build_canonical_request",
    "canonical_audience",
    "canonical_content_type",
    "canonical_key_id",
    "canonical_organization",
    "canonical_path",
    "canonical_query",
    "compute_signature",
    "generate_nonce",
    "golden_vectors_bytes",
    "load_golden_vectors",
    "resolve_signing_credentials",
    "sign_request",
    "split_target",
    "verify_signature",
    "verify_signed_request",
]
