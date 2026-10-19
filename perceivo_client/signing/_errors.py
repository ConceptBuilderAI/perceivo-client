"""The exception raised by the signing package.

``SigningError`` is defined in a leaf module so that every module that raises it
can import it without importing a canonicaliser. Import it from
``perceivo_client.signing`` or ``perceivo_client``.
"""

from __future__ import annotations

__all__ = ["SigningError"]


class SigningError(ValueError):
    """A request could not be signed, or a signing input was malformed.

    The message never contains the signing secret.
    """
