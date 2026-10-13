"""HTTP transport: auth header injection, rate-limit-aware retry, error mapping.

A thin wrapper over an ``httpx.Client`` that:

* attaches the ``X-API-Key`` header to every request,
* records the rate-limit state of each response (:attr:`last_rate_limit`),
* retries only ``GET`` requests on ``429``/``502``/``503``/``504``, up to
  ``max_retries``, honoring ``Retry-After`` and falling back to exponential
  backoff; a ``429`` ``execution_locked`` is never retried, because waiting
  does not clear it,
* raises the typed exceptions in :mod:`perceivo_client.errors` for any 4xx/5xx,
* **optionally** HMAC-signs each request (:mod:`perceivo_client.signing`).

The ``sleep`` callable is injectable so tests can assert backoff timing without
real waits, and ``http_client`` is injectable so tests can supply a mock
transport.

Request signing is **opt-in and off by default**. With no ``signer`` a request
is issued with one ``httpx.Client.request`` call. With a signer the transport
builds the request first and then sends it, so it can sign the URL and body
bytes it is about to put on the wire.
"""

from __future__ import annotations

import copy
import time
from collections.abc import Callable
from typing import Any

import httpx

from perceivo_client._version import __version__
from perceivo_client.auth import APICredentials
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
        credentials: APICredentials,
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
        # Empty: each request uses the pool's own timeout. Set by
        # :meth:`with_timeout` to override it per request.
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

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        """Close the connection pool, unless the caller injected ``http_client``."""
        if self._owns_client:
            self._client.close()

    @property
    def signing_enabled(self) -> bool:
        """True when this transport HMAC-signs every request it issues.

        Read-only, and deliberately a boolean rather than the signer itself: a
        caller needs to know *whether* a request will be signed (a multipart
        upload cannot be, see :meth:`_build_signed_request`) without being handed
        the object that holds the key material.
        """
        return self._signer is not None

    # -- request -----------------------------------------------------------
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
        # Drop params whose value is None so callers can pass optional arguments
        # uniformly without polluting the query string.
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
                    # Sign INSIDE the retry loop. Every attempt gets a fresh
                    # timestamp and nonce: a retry that replayed the previous
                    # nonce would be rejected as a replay once the server's nonce
                    # store recovered, converting a transient outage into a
                    # permanent failure.
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

            # A status alone cannot prove a mutation did not reach its handler:
            # an upstream 429/5xx can follow a completed side effect. Retry only
            # GET, whose contract is read-only. HEAD and OPTIONS are not retried
            # because their retry safety is not established. A 429
            # execution_locked lasts until the organization's budget is
            # restored, so waiting cannot clear it.
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

        The request is built first so the signature covers the **exact** query,
        body bytes and ``Content-Type`` ``httpx`` will send: the URL after
        ``httpx`` has resolved it against ``base_url`` and encoded ``params``, the
        serialized body rather than a re-serialization of it, and the header
        ``httpx`` chose rather than the one the caller expected it to choose.

        **Build-then-sign is required for field 8.** ``Content-Type`` is signed
        verbatim, and for a multipart body ``httpx`` generates the ``boundary``
        parameter itself. A signer invoked before the client sets the header
        commits to a value the request never carries.

        **Field 9 is read from the built request for the same reason.**
        ``Perceivo-Organization`` is a caller header, but only the built request
        knows what will be sent after ``httpx`` has merged per-request headers
        over the client's defaults. Reading it here means the signed organization
        is the sent one by construction.

        **The signed path is the one sent.** The target is read off the built
        request, so the signature covers the raw, still-encoded path ``httpx``
        writes on the request line, which is the path the API verifies.

        ``get_list`` rather than ``get`` for both headers: ``httpx.Headers.get``
        joins repeated values with ``", "``, which would turn an unsignable
        ambiguity into a plausible-looking single value. The signer rejects the
        list. For the organization this matters more than for the content type,
        because a joined value would let the signature and the organization the
        API acts for disagree.
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
        try:
            body = request.content
        # Reachable: httpx builds every multipart body as a streaming one, and
        # `content=` accepts an iterator. Signing a placeholder digest would
        # verify against bytes the server never receives, so this fails loudly.
        #
        # This is the backstop, not the primary guard: a signed multipart upload
        # is refused at the call site (`files.upload`) with a message that names
        # the operation. Reaching here means some other caller supplied a
        # streaming body directly.
        except httpx.RequestNotRead as exc:
            raise SigningError(
                "a streaming request body (for example a multipart upload) cannot be signed; "
                "read it into bytes first"
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
