"""Canonical fields 8 and 9: the values taken from request headers.

Field 8 is the ``Content-Type`` header and field 9 is the
``Perceivo-Organization`` header. Both follow the same rules:

* the value is signed verbatim: it is never normalised, case-folded or repaired;
* an absent header is the empty string, as an absent query is for field 6;
* a repeated header is rejected, because a signer that picks one of two values
  may not pick the one the server uses;
* an inadmissible character is rejected, never escaped.

They differ in what they admit. Field 8 admits any printable ASCII character.
Field 9 admits only a lowercase, hyphenated UUID or the empty string.

The server compares field 9 with the ``Perceivo-Organization`` header it
received after verifying the signature, because the organization selects the
tenant the request is authorised against.
"""

from __future__ import annotations

import re

from perceivo_client.signing._constants import (
    CANONICAL_ORGANIZATION_PATTERN,
    ContentTypeType,
    OrganizationType,
)
from perceivo_client.signing._errors import SigningError

__all__ = ["canonical_content_type", "canonical_organization"]

#: Characters admitted in canonical field 8: printable ASCII, 0x20-0x7E. The
#: server accepts exactly this set. On it, latin-1 and UTF-8 decoding agree, so a
#: verifier and a signer that decode header bytes differently still produce the
#: same field. The empty string is admitted, for a request with no
#: ``Content-Type`` header.
_CONTENT_TYPE_CHARSET = re.compile(r"[\x20-\x7e]*")

#: Characters admitted in canonical field 9: a lowercase, hyphenated RFC 4122 UUID,
#: or the empty string. A newline is rejected by this rule, never escaped.
_ORGANIZATION_CHARSET = re.compile(CANONICAL_ORGANIZATION_PATTERN)


def canonical_content_type(content_type: ContentTypeType) -> str:
    """Return canonical field 8: the ``Content-Type`` request header, verbatim.

    An absent header yields the empty string; the field is present either way, so
    the canonical request always has eleven fields.

    The value is not normalised, case-folded or stripped of parameters. On a
    multipart route the body parser, the ``boundary`` and the ``charset`` are all
    selected from this header, so signing a reduced media type would let the same
    body bytes be re-framed without invalidating the signature.

    Sign the request after it is final. HTTP client libraries generate the
    multipart boundary themselves, so a signature computed before the client sets
    ``Content-Type`` commits to a value the request never carries.
    :class:`~perceivo_client._transport.Transport` builds the request before it
    signs it.

    Args:
        content_type: The header value, ``None`` if the header is absent, or a
            list or tuple of the values of a repeated header. Use a
            ``get_list``-style accessor so a repeated header is detected rather
            than joined into one value.

    Returns:
        The header value, or ``""`` if the header is absent.

    Raises:
        SigningError: If the header is repeated, is not decodable text, or
            contains a character outside printable ASCII (0x20-0x7E), including
            ``\\n``. The server rejects the same characters, so such a request
            could never verify.
    """
    if content_type is None:
        return ""
    if isinstance(content_type, (list, tuple)):
        if not content_type:
            return ""
        if len(content_type) > 1:
            raise SigningError(
                "the request carries more than one Content-Type header, which cannot be "
                "signed because the server's body parser might use a different value "
                "from the one signed. Send exactly one."
            )
        content_type = content_type[0]
    if isinstance(content_type, (bytes, bytearray, memoryview)):
        try:
            content_type = bytes(content_type).decode("utf-8")
        except UnicodeDecodeError:
            raise SigningError("Content-Type must be UTF-8 decodable to be signed") from None
    if not isinstance(content_type, str):
        raise SigningError(
            f"Content-Type must be str, bytes or None, got {type(content_type).__name__}"
        )
    if not _CONTENT_TYPE_CHARSET.fullmatch(content_type):
        raise SigningError(
            "Content-Type must be ASCII printable (0x20-0x7E) to be signed; the "
            "byte(s) outside that range cannot be placed in canonical field 8. It "
            "is REJECTED, never escaped or transliterated. This is narrower than "
            "RFC 7231, which admits obs-text in a quoted-string, and the narrowing "
            "is what lets a latin-1 verifier and a UTF-8 signer agree on the field. "
            "A newline is refused by this same rule."
        )
    return content_type


def canonical_organization(organization: OrganizationType) -> str:
    """Return canonical field 9: the ``Perceivo-Organization`` request header, verbatim.

    An absent header yields the empty string; the field is present either way, so
    the canonical request always has
    :data:`~perceivo_client.signing._constants.CANONICAL_FIELD_COUNT` fields.

    The value must be a lowercase, hyphenated RFC 4122 UUID. Unlike
    :func:`~perceivo_client.signing.canonical.canonical_key_id`, this function does
    not normalise: an uppercase, braced or unhyphenated UUID is rejected, so the
    value that is signed and the value the server authorises against are always
    byte-identical.

    Security notes:
        The organization header selects the tenant a request acts on. Including it
        in the signature prevents a captured signature from being replayed against
        another organization. The server compares field 9 with the header it
        received after verifying the signature, so send the same value you sign.

    Args:
        organization: The header value, ``None`` if the header is absent, or a
            list or tuple of the values of a repeated header. Use a
            ``get_list``-style accessor so a repeated header is detected rather
            than joined into one value.

    Returns:
        The header value, or ``""`` if the header is absent.

    Raises:
        SigningError: If the header is repeated, is not decodable text, or is
            neither the empty string nor a lowercase, hyphenated UUID. A value
            containing ``\\n`` is rejected, never escaped.
    """
    if organization is None:
        return ""
    if isinstance(organization, (list, tuple)):
        if not organization:
            return ""
        if len(organization) > 1:
            raise SigningError(
                "the request carries more than one Perceivo-Organization header, which "
                "cannot be signed because the server might authorise the request against "
                "a different value from the one signed. Send exactly one."
            )
        organization = organization[0]
    if isinstance(organization, (bytes, bytearray, memoryview)):
        try:
            organization = bytes(organization).decode("utf-8")
        except UnicodeDecodeError:
            raise SigningError(
                "Perceivo-Organization must be UTF-8 decodable to be signed"
            ) from None
    if not isinstance(organization, str):
        raise SigningError(
            f"Perceivo-Organization must be str, bytes or None, got {type(organization).__name__}"
        )
    if not _ORGANIZATION_CHARSET.fullmatch(organization):
        raise SigningError(
            "Perceivo-Organization must be a lowercase hyphenated 8-4-4-4-12 UUID; "
            "uppercase, braced and unhyphenated spellings are rejected, not normalised, "
            "so the signed value is exactly the value the server receives. Pass "
            "organization=None when the request has no Perceivo-Organization header."
        )
    return organization
