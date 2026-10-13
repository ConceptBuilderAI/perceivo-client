"""Wire-format constants for HMAC request signing.

This module holds values only and imports nothing, so every other module in the
package can depend on it without an import cycle. Changing any value here changes
the wire format and invalidates the published golden vectors.
"""

from __future__ import annotations

#: Signature scheme version, sent as the ``v1=`` prefix of the signature header.
#: The prefix lets a future scheme be introduced alongside this one, so the
#: canonical request needs no additional field for forward compatibility.
SIGNATURE_VERSION = "v1"
SIGNATURE_PREFIX = f"{SIGNATURE_VERSION}="

#: Field 1 of the canonical request. A constant that is never configurable: it
#: separates this signature domain from any other use of the same secret.
CANONICAL_DOMAIN = "perceivo-hmac-v1"

#: Number of fields in the canonical request, joined by ``CANONICAL_FIELD_COUNT - 1``
#: newline separators with no trailing newline. The count is fixed: an optional
#: field is present as the empty string, never omitted. A verifier that splits on
#: ``\n`` and checks this count rejects both a newline smuggled into a field and
#: a canonical request with fields missing.
CANONICAL_FIELD_COUNT = 11

#: Grammar of field 2, the audience. It excludes ``/`` and ``\n``.
CANONICAL_AUDIENCE_PATTERN = r"\A[A-Za-z0-9._:-]{1,64}\Z"

#: Grammar of field 9, the organization: a lowercase, hyphenated RFC 4122 UUID, or
#: the empty string when the request carries no ``Perceivo-Organization`` header.
#:
#: Unlike the key id, the organization is not normalised. Any other spelling is
#: rejected, so the value that is signed and the value the server authorises
#: against are always byte-identical.
CANONICAL_ORGANIZATION_PATTERN = (
    r"\A(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?\Z"
)

#: Deployment audiences. They are configuration labels, not hostnames, and are
#: never derived from a URL or a ``Host`` header.
AUDIENCE_PRODUCTION = "perceivo-api-prod"
AUDIENCE_LOCAL = "perceivo-api-local"

HEADER_KEY_ID = "X-Perceivo-Key-Id"
HEADER_TIMESTAMP = "X-Perceivo-Timestamp"
HEADER_NONCE = "X-Perceivo-Nonce"
HEADER_SIGNATURE = "X-Perceivo-Signature"

#: Source header of canonical field 9.
#:
#: The signer never adds this header to
#: :attr:`~perceivo_client.signing.signer.SignedRequest.headers`. The four headers
#: above are produced by the signer; this one is supplied by the caller, and the
#: signature commits to the value the request already carries.
HEADER_ORGANIZATION = "Perceivo-Organization"

#: SHA-256 of zero bytes: the body field for a request with no body or an empty
#: body.
EMPTY_BODY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

#: Maximum difference, in seconds and in either direction, between a signed
#: request's timestamp and the server clock.
MAX_CLOCK_SKEW_SECONDS = 300

ENV_KEY_ID = "PERCEIVO_KEY_ID"
#: Holds the signing secret as it was issued: 64 lowercase hex characters. The HMAC
#: key is the 32 bytes those characters decode to, and
#: :func:`perceivo_client.signing._secret.secret_to_key_bytes` performs the decode,
#: so the issued value can be exported unchanged. Surrounding whitespace, such as
#: the trailing newline from ``$(cat secret.txt)``, is ignored.
ENV_SIGNING_SECRET = "PERCEIVO_SIGNING_SECRET"
#: There is no environment variable for the audience. The audience is explicit
#: configuration supplied at the call site, and is never taken from a base URL, a
#: ``Host`` header or the environment.

BodyType = bytes | bytearray | memoryview | str | None
#: A signing secret. A ``str`` of exactly 64 hex characters is the issued secret
#: and is decoded to its 32 bytes; any other ``str`` is keyed on its UTF-8 bytes;
#: ``bytes`` is used verbatim. To key on a 64-character passphrase made only of hex
#: characters, pass it as ``bytes``.
SecretType = str | bytes
#: A ``Content-Type`` header value. ``None`` means the header is absent. A list or
#: tuple represents a repeated header, which cannot be signed.
ContentTypeType = str | bytes | list[str] | tuple[str, ...] | None
#: A ``Perceivo-Organization`` header value. ``None`` means the header is absent.
#: A list or tuple represents a repeated header, which cannot be signed.
OrganizationType = str | bytes | list[str] | tuple[str, ...] | None
