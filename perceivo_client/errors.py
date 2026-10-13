"""Typed exceptions for error responses from the Perceivo API.

The API answers an error with one of several body shapes, depending on which
layer refused the request:

* the platform envelope, ``{"error_code", "message", "details", "correlation_id", ...}``;
* a short slug, ``{"error": "unauthorized"}``, optionally with a ``reason``;
* a nested error object, ``{"error": {"code", "message", "details"}}``;
* a detail string, ``{"detail": "Not Found"}``;
* a detail object, ``{"detail": {"code", "message", ...}}``;
* a validation list, ``{"detail": [{"loc", "msg", "type"}, ...]}``.

:meth:`PerceivoAPIError.from_response` normalizes every one of them onto the
same ``code`` / ``message`` / ``details`` / ``request_id`` attributes.
"""

from __future__ import annotations

from typing import Any

import httpx

from perceivo_client.ratelimit import RateLimitInfo

#: The code the API uses when an organization's cost-incurring work is blocked.
_EXECUTION_LOCKED = "execution_locked"

#: Keys that qualify a ``{"error": "<slug>"}`` refusal, surfaced in ``details``.
_SLUG_QUALIFIERS = ("reason", "limit_bytes")


class PerceivoError(Exception):
    """Base class for every error raised by perceivo-client."""


class PerceivoConnectionError(PerceivoError):
    """A transport-level failure (DNS, connect, read timeout) before any HTTP status."""


class PerceivoAPIError(PerceivoError):
    """An error HTTP response (>= 400) from the Perceivo API.

    Attributes:
        status_code: The HTTP status code.
        code: The machine error code: ``error_code``, ``error.code``,
            ``detail.code`` or the ``error`` slug, whichever the body carries.
        message: Human-readable error message.
        details: Structured context, if any. For a ``{"detail": {...}}`` body it
            is that whole object, so fields such as ``invitation_id`` are kept.
            For a validation failure it holds the field errors under ``errors``.
            For an ``{"error": "<slug>", "reason": ...}`` refusal it holds
            ``reason`` (and ``limit_bytes`` on a ``413``).
        request_id: The id to quote to support: the ``Perceivo-Request-Id``
            response header, else the body's ``request_id`` or
            ``correlation_id``, else another request-id header.
        response: The raw :class:`httpx.Response`.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.request_id = request_id
        self.response = response
        prefix = f"[{status_code}]" if status_code is not None else "[api error]"
        if code:
            prefix += f" {code}"
        rid = f" (request_id={request_id})" if request_id else ""
        super().__init__(f"{prefix} {message}{rid}")

    @classmethod
    def from_response(cls, response: httpx.Response) -> PerceivoAPIError:
        """Build the most specific typed exception for an error response."""
        code, message, details = _extract_envelope(response)
        kwargs: dict[str, Any] = {
            "status_code": response.status_code,
            "code": code,
            "details": details,
            "request_id": _request_id(response),
            "response": response,
        }
        if response.status_code == 429:
            if _names_execution_lock(code, message, details):
                return PerceivoExecutionLockedError(message, **kwargs)
            rate_limit = RateLimitInfo.from_headers(response.headers)
            return PerceivoRateLimitError(
                message, rate_limit=rate_limit, retry_after=rate_limit.retry_after, **kwargs
            )
        exc_cls = _STATUS_TO_EXC.get(response.status_code)
        if exc_cls is None:
            exc_cls = PerceivoServerError if response.status_code >= 500 else PerceivoAPIError
        return exc_cls(message, **kwargs)


class PerceivoAuthError(PerceivoAPIError):
    """401: the API key was missing, invalid, or revoked."""


class PerceivoGrantError(PerceivoAPIError):
    """403: the principal lacks the required privilege or endpoint access.

    When the denial is an endpoint-access rejection, the API reports a list of
    groups in the error ``details``. It is surfaced as :attr:`allowed_groups`
    (a list of group identifiers, or ``None`` when the payload does not carry
    it).
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.allowed_groups: list[str] | None = _extract_allowed_groups(self.details)


class PerceivoNotFoundError(PerceivoAPIError):
    """404: the target resource does not exist or is not visible."""


class PerceivoConflictError(PerceivoAPIError):
    """409: the request conflicts with the current state of the resource."""


class PerceivoValidationError(PerceivoAPIError):
    """422: request validation failed; ``details["errors"]`` lists the field errors."""


class PerceivoRateLimitError(PerceivoAPIError):
    """429: a request-rate limit was exceeded; retrying after ``retry_after`` can succeed.

    Attributes:
        rate_limit: The rate-limit state parsed from the response headers.
        retry_after: Seconds to wait, from ``Retry-After``, or ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        rate_limit: RateLimitInfo | None = None,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        self.rate_limit = rate_limit
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class PerceivoExecutionLockedError(PerceivoAPIError):
    """429 ``execution_locked``: the organization's cost-incurring work is blocked.

    This is not a rate limit, and it is deliberately not a
    :class:`PerceivoRateLimitError`: the lock lasts until the organization's
    budget is restored, so waiting and retrying cannot clear it. The client
    never retries it.
    """


class PerceivoServerError(PerceivoAPIError):
    """5xx: the platform failed to handle the request."""


_STATUS_TO_EXC: dict[int, type[PerceivoAPIError]] = {
    401: PerceivoAuthError,
    403: PerceivoGrantError,
    404: PerceivoNotFoundError,
    409: PerceivoConflictError,
    422: PerceivoValidationError,
}


def _is_execution_locked(response: httpx.Response) -> bool:
    """True when ``response`` is a ``429`` ``execution_locked`` refusal.

    The code arrives as ``detail.code``, as ``details.code`` beside a
    platform ``error_code``, or inside the envelope's ``message``, so all
    three are read.
    """
    if response.status_code != 429:
        return False
    return _names_execution_lock(*_extract_envelope(response))


def _names_execution_lock(code: str | None, message: str, details: dict[str, Any] | None) -> bool:
    return (
        code == _EXECUTION_LOCKED
        or _EXECUTION_LOCKED in message
        or (details is not None and details.get("code") == _EXECUTION_LOCKED)
    )


def _extract_envelope(
    response: httpx.Response,
) -> tuple[str | None, str, dict[str, Any] | None]:
    """Pull ``(code, message, details)`` out of any error body shape."""
    try:
        body: Any = response.json()
    except ValueError:
        body = None

    fallback = f"HTTP {response.status_code}"
    if not isinstance(body, dict):
        text = (response.text or "").strip()
        return None, (text or fallback)[:500], None

    detail = body.get("detail")
    error = body.get("error")
    if isinstance(error, dict):
        # Nested error object; a top-level `detail` string is only a fallback.
        code = _first_str(error, "code", "error_code")
        message = _first_str(error, "message") or _str_or_none(detail)
        details = _dict_or_none(error.get("details"))
    elif isinstance(detail, dict):
        # FastAPI's structured detail: the whole object is the context.
        code = _first_str(detail, "code", "error_code")
        message = _first_str(detail, "message")
        details = detail
    elif isinstance(detail, list):
        # FastAPI's native validation body.
        code = None
        message = "Request validation failed"
        details = {"errors": detail}
    else:
        code = _first_str(body, "error_code", "code") or _str_or_none(error)
        message = _first_str(body, "message", "detail", "error_description")
        details = _dict_or_none(body.get("details"))
        if details is None:
            # A slug refusal's qualifiers, e.g. a signature refusal's `reason`.
            details = {key: body[key] for key in _SLUG_QUALIFIERS if key in body} or None
    return code, message or code or fallback, details


def _request_id(response: httpx.Response) -> str | None:
    """The id to quote to support for ``response``."""
    edge_id = response.headers.get("perceivo-request-id")
    if edge_id:
        return edge_id
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        body_id = _first_str(body, "request_id", "correlation_id", "trace_id")
        if body_id:
            return body_id
    for header in ("x-request-id", "x-correlation-id", "x-trace-id"):
        value = response.headers.get(header)
        if value:
            return value
    return None


def _extract_allowed_groups(details: dict[str, Any] | None) -> list[str] | None:
    """Pull an ``allowed_groups`` hint out of a 403 error's ``details``.

    Accepts either a top-level ``allowed_groups`` list or one nested under an
    ``endpoint_access`` object, and normalizes entries to strings.
    """
    if not isinstance(details, dict):
        return None
    direct = details.get("allowed_groups")
    if isinstance(direct, list):
        return [str(g) for g in direct]
    endpoint_access = details.get("endpoint_access")
    if isinstance(endpoint_access, dict) and isinstance(
        endpoint_access.get("allowed_groups"), list
    ):
        return [str(g) for g in endpoint_access["allowed_groups"]]
    return None


def _first_str(mapping: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _str_or_none(mapping.get(key))
        if value:
            return value
    return None


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None
