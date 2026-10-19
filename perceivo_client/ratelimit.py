"""Rate-limit header parsing for the Perceivo public API.

The API reports the API key's budget as ``X-RateLimit-*`` headers and a
per-client-address limit as ``Perceivo-RateLimit-*`` headers.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return None


def parse_retry_after(value: str | None, *, now: float | None = None) -> float | None:
    """Parse a ``Retry-After`` header into seconds-to-wait.

    Accepts either a delta-seconds integer or an HTTP-date, per RFC 9110.
    Returns ``None`` when the header is absent or unparseable, and never
    returns a negative delay.
    """
    if value is None:
        return None
    value = value.strip()
    seconds = _parse_int(value)
    if seconds is not None:
        return max(0.0, float(seconds))
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    current = now if now is not None else time.time()
    return max(0.0, when.timestamp() - current)


@dataclass(frozen=True)
class RateLimitInfo:
    """Rate-limit state parsed from one response's headers.

    Every field is ``None`` when its header is absent or unparseable.

    Attributes:
        limit: The API key's requests per window (``X-RateLimit-Limit``).
        remaining: Requests left in the key's current window
            (``X-RateLimit-Remaining``).
        reset: Unix time when the key's window frees a slot
            (``X-RateLimit-Reset``).
        retry_after: Seconds to wait before retrying (``Retry-After``).
        address_limit: The per-client-address limit
            (``Perceivo-RateLimit-Limit``).
        address_remaining: Requests left for this client address
            (``Perceivo-RateLimit-Remaining``).
        address_reset: Unix time when the per-address window frees a slot
            (``Perceivo-RateLimit-Reset``).
    """

    limit: int | None = None
    remaining: int | None = None
    reset: int | None = None
    retry_after: float | None = None
    address_limit: int | None = None
    address_remaining: int | None = None
    address_reset: int | None = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str], *, now: float | None = None) -> RateLimitInfo:
        """Build a :class:`RateLimitInfo` from an HTTP response's headers.

        Header lookup is case-insensitive.
        """
        lowered = {str(k).lower(): v for k, v in dict(headers).items()}
        return cls(
            limit=_parse_int(lowered.get("x-ratelimit-limit")),
            remaining=_parse_int(lowered.get("x-ratelimit-remaining")),
            reset=_parse_int(lowered.get("x-ratelimit-reset")),
            retry_after=parse_retry_after(lowered.get("retry-after"), now=now),
            address_limit=_parse_int(lowered.get("perceivo-ratelimit-limit")),
            address_remaining=_parse_int(lowered.get("perceivo-ratelimit-remaining")),
            address_reset=_parse_int(lowered.get("perceivo-ratelimit-reset")),
        )
