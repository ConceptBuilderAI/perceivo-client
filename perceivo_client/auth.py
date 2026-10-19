"""Credential resolution for the Perceivo REST client.

Explicit arguments take precedence over the ``PERCEIVO_API_URL`` and
``PERCEIVO_API_KEY`` environment variables; the base URL defaults to
:data:`DEFAULT_API_URL`.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field

from perceivo_client.errors import PerceivoError

#: Production base URL: scheme and host only, since resource methods supply the
#: whole path. Override it with ``PERCEIVO_API_URL`` or ``base_url``.
DEFAULT_API_URL = "https://api.perceivo.ai"


class MissingCredentialsError(PerceivoError, RuntimeError):
    """Raised when no credential is found in arguments or the environment."""


class AmbiguousCredentialsError(PerceivoError, ValueError):
    """Raised when more than one authentication mode is configured at once.

    The client authenticates with one mode: an API key, an HMAC signing pair, or a
    bearer token. Inputs for more than one mode are rejected at construction.
    """


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


@dataclass(frozen=True)
class BearerCredentials:
    """Resolved bearer (Entra) credentials for a perceivo-client -> API call.

    The token is either a static string or a zero-argument callable. A callable
    is invoked once per request (see :meth:`auth_headers`), so a caller holding
    a short-lived Entra access token can supply a refreshing callable and the
    client always sends the current token. No token caching happens here: the
    caller owns refresh.
    """

    base_url: str
    token_source: str | Callable[[], str] = field(repr=False)

    def __repr__(self) -> str:
        return f"BearerCredentials(base_url={self.base_url!r}, bearer_token=<redacted>)"

    __str__ = __repr__

    def auth_headers(self) -> dict[str, str]:
        """Return the ``Authorization: Bearer`` header, resolving a callable now.

        Raises:
            MissingCredentialsError: If the token source yields an empty or
                non-string value.
        """
        source = self.token_source
        token = source() if callable(source) else source
        if not isinstance(token, str) or not token.strip():
            raise MissingCredentialsError(
                "bearer token source produced an empty, whitespace-only, or non-string token"
            )
        return {"Authorization": f"Bearer {token}"}


#: Any resolved credential the transport can read a base URL and auth headers
#: from. Both members expose ``base_url`` and ``auth_headers()``.
AuthCredentials = APICredentials | BearerCredentials


def resolve_base_url(base_url: str | None = None) -> str:
    """Resolve the API base URL from an explicit arg, the environment, or the default."""
    return (base_url or os.environ.get("PERCEIVO_API_URL") or DEFAULT_API_URL).rstrip("/")


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
    resolved_url = resolve_base_url(base_url)
    resolved_key = api_key or os.environ.get("PERCEIVO_API_KEY")
    if not resolved_key:
        raise MissingCredentialsError(
            "No API key found. Pass api_key=... to Client(...) or set "
            "PERCEIVO_API_KEY in the environment."
        )

    return APICredentials(base_url=resolved_url, api_key=resolved_key)


def resolve_bearer_credentials(
    *,
    base_url: str | None = None,
    bearer_token: str | Callable[[], str],
) -> BearerCredentials:
    """Resolve bearer credentials from an explicit token or token callable.

    The token has no environment fallback, so an environment variable cannot
    change the auth mode.

    Args:
        base_url: Explicit base URL override.
        bearer_token: A non-empty token string, or a zero-argument callable
            returning one.

    Raises:
        MissingCredentialsError: If ``bearer_token`` is an empty or
            whitespace-only string.
        TypeError: If ``bearer_token`` is neither a string nor callable.
    """
    if isinstance(bearer_token, str):
        if not bearer_token.strip():
            raise MissingCredentialsError("bearer_token was an empty or whitespace-only string")
    elif not callable(bearer_token):
        raise TypeError(
            "bearer_token must be a token string or a zero-argument callable returning one"
        )
    return BearerCredentials(base_url=resolve_base_url(base_url), token_source=bearer_token)
