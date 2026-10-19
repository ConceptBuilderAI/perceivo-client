"""Wire-format constants for HMAC request signing.

This module holds values only and imports nothing, so every other module in the
package can depend on it without an import cycle. Changing any value here changes
the wire format and invalidates the published golden vectors.
"""

from __future__ import annotations

#: Signature scheme version, sent as the ``v1=`` prefix of the signature header.
SIGNATURE_VERSION = "v1"
SIGNATURE_PREFIX = f"{SIGNATURE_VERSION}="

#: Field 1 of the canonical request; separates this signature domain from any
#: other use of the same secret.
CANONICAL_DOMAIN = "perceivo-hmac-v1"

#: Number of fields in the canonical request. An optional field is present as
#: the empty string, so the count is fixed.
CANONICAL_FIELD_COUNT = 11

#: Grammar of field 2, the audience. It excludes ``/`` and ``\n``.
CANONICAL_AUDIENCE_PATTERN = r"\A[A-Za-z0-9._:-]{1,64}\Z"

#: Grammar of field 9, the organization: a lowercase, hyphenated RFC 4122 UUID, or
#: the empty string when the request carries no ``Perceivo-Organization`` header.
#: Other spellings are rejected rather than normalised.
CANONICAL_ORGANIZATION_PATTERN = (
    r"\A(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?\Z"
)

#: Deployment audiences. They are configuration labels, not hostnames.
AUDIENCE_PRODUCTION = "perceivo-api-prod"
AUDIENCE_LOCAL = "perceivo-api-local"

HEADER_KEY_ID = "X-Perceivo-Key-Id"
HEADER_TIMESTAMP = "X-Perceivo-Timestamp"
HEADER_NONCE = "X-Perceivo-Nonce"
HEADER_SIGNATURE = "X-Perceivo-Signature"

#: Source header of canonical field 9. It is supplied by the caller, not added by
#: the signer.
HEADER_ORGANIZATION = "Perceivo-Organization"

#: SHA-256 of zero bytes: the body field for a request with no or an empty body.
EMPTY_BODY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

#: Maximum difference, in seconds and in either direction, between a signed
#: request's timestamp and the server clock.
MAX_CLOCK_SKEW_SECONDS = 300

ENV_KEY_ID = "PERCEIVO_KEY_ID"
#: Holds the signing secret as issued: 64 lowercase hex characters, decoded to the
#: 32-byte HMAC key. Surrounding whitespace is ignored.
ENV_SIGNING_SECRET = "PERCEIVO_SIGNING_SECRET"

BodyType = bytes | bytearray | memoryview | str | None
#: A signing secret. A ``str`` of 64 hex characters is decoded to its 32 bytes;
#: any other ``str`` is keyed on its UTF-8 bytes; ``bytes`` is used verbatim.
SecretType = str | bytes
#: A ``Content-Type`` header value. ``None`` means the header is absent. A list or
#: tuple represents a repeated header, which cannot be signed.
ContentTypeType = str | bytes | list[str] | tuple[str, ...] | None
#: A ``Perceivo-Organization`` header value. ``None`` means the header is absent.
#: A list or tuple represents a repeated header, which cannot be signed.
OrganizationType = str | bytes | list[str] | tuple[str, ...] | None
