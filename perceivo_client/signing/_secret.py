"""Conversion of a signing secret to HMAC key bytes.

The platform issues the 32-byte key as 64 lowercase hex characters, which are
decoded rather than encoded as UTF-8.
"""

from __future__ import annotations

import re

from perceivo_client.signing._constants import SecretType
from perceivo_client.signing.canonical import SigningError

__all__ = ["secret_to_key_bytes"]

#: An issued signing secret: 32 bytes rendered as 64 hex characters, either case.
_DISCLOSED_SECRET_HEX_RE = re.compile(r"[0-9a-fA-F]{64}")


def secret_to_key_bytes(secret: SecretType) -> bytes:
    """Return the HMAC key bytes for ``secret``.

    Args:
        secret: The signing secret. A ``str`` of 64 hex characters (surrounding
            whitespace ignored) is decoded from hex; any other ``str`` is encoded
            as UTF-8 with no whitespace stripped; ``bytes``, ``bytearray`` and
            ``memoryview`` are used verbatim. To key on a 64-character hex
            passphrase as text, pass ``passphrase.encode()``.

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
