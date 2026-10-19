"""HTTP transport: authentication header, retry of ``GET`` requests, error mapping
and optional HMAC request signing.
"""

from __future__ import annotations

import copy
import time
from collections.abc import Callable
from typing import Any

import httpx

from perceivo_client._version import __version__
from perceivo_client.auth import AuthCredentials
from perceivo_client.errors import PerceivoAPIError, PerceivoConnectionError, _is_execution_locked
from perceivo_client.ratelimit import RateLimitInfo
from perceivo_client.signing import RequestSigner, SigningError

_RETRY_STATUS = frozenset({429, 502, 503, 504})
_DEFAULT_TIMEOUT = 30.0
_LONG_TIMEOUT = 150.0


class Transport:
    """Synchronous HTTP transport for the Perceivo public API."""

    def __init__(
        self,
        credentials: AuthCredentials,
        *,
        timeout: float | None = _DEFAULT_TIMEOUT,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        max_backoff: float = 60.0,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
        signer: RequestSigner | None = None,
    ) -> None:
        self._credentials = credentials
        self._signer = signer
        self._max_retries = max(0, max_retries)
        self._backoff_factor = backoff_factor
        self._max_backoff = max_backoff
        self._sleep = sleep or time.sleep
        self._owns_client = http_client is None
        if http_client is not None and http_client.follow_redirects:
            raise ValueError("injected http_client must set follow_redirects=False")
        self._client = http_client or httpx.Client(
            base_url=credentials.base_url,
            timeout=timeout,
            follow_redirects=False,
        )
        # Per-request options; set by :meth:`with_timeout`.
        self._request_options: dict[str, Any] = {}
        self.last_rate_limit: RateLimitInfo | None = None

    def with_timeout(self, timeout: float | None) -> Transport:
        """A transport that shares this one's pool but sends with ``timeout``.

        The timeout is attached to each request, so it also applies to an
        injected ``http_client``. The derived transport never closes the shared
        pool, and records its own :attr:`last_rate_limit`.
        """
        derived = copy.copy(self)
        derived._owns_client = False
        derived._request_options = {"timeout": timeout}
        derived.last_rate_limit = None
        return derived

    def _options(self, min_timeout: float | None) -> dict[str, Any]:
        """Per-request options, with read and write raised to ``min_timeout``.

        Connect and pool keep their value: a slow upload or ingest is spent
        sending the body and waiting for the answer, not connecting. A bound of
        ``None`` (no timeout) is never lowered to one.
        """
        if min_timeout is None:
            return self._request_options
        current = httpx.Timeout(self._request_options.get("timeout", self._client.timeout))

        def floor(value: float | None) -> float | None:
            return None if value is None else max(value, min_timeout)

        return {
            "timeout": httpx.Timeout(
                connect=current.connect,
                read=floor(current.read),
                write=floor(current.write),
                pool=current.pool,
            )
        }

    def close(self) -> None:
        """Close the connection pool, unless the caller injected ``http_client``."""
        if self._owns_client:
            self._client.close()

    @property
    def signing_enabled(self) -> bool:
        """True when this transport HMAC-signs every request it issues."""
        return self._signer is not None

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        files: Any = None,
        min_timeout: float | None = None,
    ) -> httpx.Response:
        """Issue a request, retrying eligible GET rate-limit/transient responses.

        Returns the successful :class:`httpx.Response`. Raises a
        :class:`perceivo_client.errors.PerceivoAPIError` subclass on a 4xx/5xx
        that is not retried, or :class:`PerceivoConnectionError` on transport
        failure. ``min_timeout`` raises this request's read and write timeouts
        to at least that many seconds.
        """
        options = self._options(min_timeout)
        merged = {
            "Accept": "application/json",
            "User-Agent": f"perceivo-client/{__version__}",
            **self._credentials.auth_headers(),
            **(headers or {}),
        }
        if params is not None:
            params = {k: v for k, v in params.items() if v is not None}

        attempt = 0
        while True:
            try:
                if self._signer is None:
                    response = self._client.request(
                        method,
                        path,
                        params=params,
                        json=json,
                        content=content,
                        files=files,
                        headers=merged,
                        **options,
                    )
                else:
                    # Signed per attempt: a retry needs a fresh nonce.
                    response = self._client.send(
                        self._build_signed_request(
                            method,
                            path,
                            params=params,
                            json=json,
                            content=content,
                            files=files,
                            headers=merged,
                            options=options,
                        )
                    )
            except httpx.HTTPError as exc:
                raise PerceivoConnectionError(
                    f"HTTP transport error calling {method} {path}: {exc}"
                ) from exc

            self.last_rate_limit = RateLimitInfo.from_headers(response.headers)

            # Only GET is retried: a 429/5xx can follow a completed side effect.
            # A 429 execution_locked does not clear by waiting.
            if (
                method.upper() == "GET"
                and response.status_code in _RETRY_STATUS
                and attempt < self._max_retries
                and not _is_execution_locked(response)
            ):
                self._sleep(self._retry_delay(attempt, self.last_rate_limit))
                attempt += 1
                continue

            if response.status_code >= 400:
                raise PerceivoAPIError.from_response(response)

            return response

    def _build_signed_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        json: Any,
        content: bytes | None,
        files: Any,
        headers: dict[str, str],
        options: dict[str, Any],
    ) -> httpx.Request:
        """Build one request and attach its ``X-Perceivo-*`` signature headers.

        The request is built before it is signed, so the signature covers the path,
        query, body bytes, ``Content-Type`` and ``Perceivo-Organization`` that
        ``httpx`` sends. ``get_list`` is used for headers so a repeated value is
        rejected rather than joined. A multipart body is read into bytes first and
        sent with ``Content-Length``.
        """
        request = self._client.build_request(
            method,
            path,
            params=params,
            json=json,
            content=content,
            files=files,
            headers=headers,
            **options,
        )
        if files is not None:
            _read_multipart_body(request)
        try:
            body = request.content
        # Only a `content=` iterator reaches here; multipart bodies were read above.
        except httpx.RequestNotRead as exc:
            raise SigningError(
                "a streaming request body cannot be signed; read it into bytes first"
            ) from exc
        signed = self._signer.sign(
            request.method,
            request.url.raw_path.decode("ascii"),
            body,
            content_type=request.headers.get_list("content-type") or None,
            organization=request.headers.get_list("perceivo-organization") or None,
        )
        request.headers.update(signed.headers)
        return request

    def _retry_delay(self, attempt: int, rate_limit: RateLimitInfo | None) -> float:
        """Seconds to wait before the next attempt (Retry-After wins)."""
        if rate_limit and rate_limit.retry_after is not None:
            return min(rate_limit.retry_after, self._max_backoff)
        backoff = self._backoff_factor * (2**attempt)
        return min(backoff, self._max_backoff)


def _read_multipart_body(request: httpx.Request) -> None:
    """Read a built multipart request's body into bytes, framed by ``Content-Length``."""
    body = request.read()
    if "transfer-encoding" in request.headers:
        del request.headers["transfer-encoding"]
    request.headers["Content-Length"] = str(len(body))
