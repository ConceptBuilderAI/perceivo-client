"""Credential resolution for the Perceivo REST client.

Resolution order for the base URL and the API key:
    1. Explicit arguments passed to :class:`~perceivo_client.Client`.
    2. ``PERCEIVO_API_URL`` / ``PERCEIVO_API_KEY`` environment variables.
    3. For the base URL only, the production default (:data:`DEFAULT_API_URL`).

The key is sent as the ``X-API-Key`` header. To target a deployment other than
production, set ``PERCEIVO_API_URL`` or pass ``base_url``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from perceivo_client.errors import PerceivoError

#: Production base URL: scheme and host only, since resource methods supply the
#: whole path. Override it with ``PERCEIVO_API_URL`` or ``base_url``.
DEFAULT_API_URL = "https://api.perceivo.ai"


class MissingCredentialsError(PerceivoError, RuntimeError):
    """Raised when no API key is found in arguments or the environment."""


@dataclass(frozen=True)
class APICredentials:
    """Resolved credentials for a perceivo-client -> Perceivo API call."""

    base_url: str
    api_key: str = field(repr=False)

    def __repr__(self) -> str:
        return f"APICredentials(base_url={self.base_url!r}, api_key=<redacted>)"

    __str__ = __repr__

    def auth_headers(self) -> dict[str, str]:
        """Return the auth header the Perceivo public API requires."""
        return {"X-API-Key": self.api_key}


def resolve_credentials(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
) -> APICredentials:
    """Resolve API credentials from explicit args then the environment.

    Args:
        base_url: Explicit base URL override.
        api_key: Explicit API key override.

    Returns:
        An :class:`APICredentials` with both fields populated.

    Raises:
        MissingCredentialsError: If no API key can be found anywhere.
    """
    resolved_url = (base_url or os.environ.get("PERCEIVO_API_URL") or DEFAULT_API_URL).rstrip("/")
    resolved_key = api_key or os.environ.get("PERCEIVO_API_KEY")
    if not resolved_key:
        raise MissingCredentialsError(
            "No API key found. Pass api_key=... to Client(...) or set "
            "PERCEIVO_API_KEY in the environment."
        )

    return APICredentials(base_url=resolved_url, api_key=resolved_key)
