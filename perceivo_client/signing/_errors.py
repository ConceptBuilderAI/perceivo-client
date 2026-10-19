"""The exception raised by the signing package."""

from __future__ import annotations

__all__ = ["SigningError"]


class SigningError(ValueError):
    """A request could not be signed, or a signing input was malformed.

    The message never contains the signing secret.
    """
