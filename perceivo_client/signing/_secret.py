"""Conversion of a signing secret to HMAC key bytes.

The HMAC key is 32 random bytes. The platform issues it once, at enrolment, as 64
lowercase hex characters (``key.hex()``), so the value a caller holds is text and
the value the server keys on is the bytes that text decodes to.

:func:`secret_to_key_bytes` maps one to the other:

* a ``str`` of exactly 64 hex characters, after surrounding whitespace is
  stripped, is decoded with ``bytes.fromhex``;
* any other ``str`` is keyed on its UTF-8 bytes;
* ``bytes``, ``bytearray`` and ``memoryview`` are used verbatim.

Security notes:
    Encoding the issued hex string as UTF-8 instead of decoding it produces a
    64-byte key that does not match the server's 32-byte key. Every request then
    fails with a 401 that does not name the cause. The ``secret_transport_vectors``
    list in the golden vectors covers this case, including the signature the
    incorrect encoding produces.

    A 64-character passphrase made only of hex characters cannot be told apart
    from an issued secret and is decoded. To key on such a passphrase as text,
    pass ``passphrase.encode()``.
"""

from __future__ import annotations

import re

from perceivo_client.signing._constants import SecretType
from perceivo_client.signing.canonical import SigningError

__all__ = ["secret_to_key_bytes"]

#: The shape of an issued signing secret: 32 bytes rendered as 64 hex characters.
#: Matched case-insensitively, because ``bytes.fromhex`` decodes both cases to the
#: same bytes. A hex string of any other length is keyed as text.
_DISCLOSED_SECRET_HEX_RE = re.compile(r"[0-9a-fA-F]{64}")


def secret_to_key_bytes(secret: SecretType) -> bytes:
    """Return the HMAC key bytes for ``secret``.

    Args:
        secret: The signing secret. A ``str`` of 64 hex characters (surrounding
            whitespace ignored) is decoded from hex; any other ``str`` is encoded
            as UTF-8 with no whitespace stripped; ``bytes``, ``bytearray`` and
            ``memoryview`` are used verbatim.

    Returns:
        The key bytes passed to HMAC-SHA256.

    Raises:
        SigningError: If ``secret`` is not ``str`` or bytes-like, or is empty.
    """
    if isinstance(secret, str):
        candidate = secret.strip()
        if _DISCLOSED_SECRET_HEX_RE.fullmatch(candidate):
            raw = bytes.fromhex(candidate)
        else:
            raw = secret.encode("utf-8")
    elif isinstance(secret, (bytes, bytearray, memoryview)):
        raw = bytes(secret)
    else:
        raise SigningError(f"signing secret must be str or bytes, got {type(secret).__name__}")
    if not raw:
        raise SigningError("signing secret is empty")
    return raw
