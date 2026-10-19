"""Async client for the Perceivo API.

``AsyncClient`` runs each call of a synchronous :class:`~perceivo_client.client.Client`
in a worker thread; cancelling a task cannot interrupt a request already
running in its thread.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx

from perceivo_client.client import Client
from perceivo_client.pagination import _PageWalk, _validate_page_options, page_items
from perceivo_client.ratelimit import RateLimitInfo
from perceivo_client.resources._base import BaseResource


class _AsyncNamespace:
    """Awaitable proxy over one synchronous resource namespace.

    Every method of the wrapped namespace is returned as a coroutine function
    with the same name and arguments. Attributes that are not callable are
    returned unchanged.
    """

    def __init__(self, resource: BaseResource) -> None:
        self._resource = resource

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._resource, name)
        if not callable(attr):
            return attr

        async def _call(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.to_thread(attr, *args, **kwargs)

        _call.__name__ = name
        _call.__doc__ = attr.__doc__
        return _call


class AsyncClient:
    """Async mirror of :class:`~perceivo_client.client.Client`.

    Takes the same arguments as :class:`~perceivo_client.client.Client` and
    exposes the same namespaces; every namespace method is awaitable. Use it as
    an async context manager, or call :meth:`aclose`, to release the HTTP
    connection pool.
    """

    auth: _AsyncNamespace
    orchestrations: _AsyncNamespace
    runs: _AsyncNamespace
    intelligence: _AsyncNamespace
    capabilities: _AsyncNamespace
    queue: _AsyncNamespace
    components: _AsyncNamespace
    files: _AsyncNamespace
    webhooks: _AsyncNamespace
    billing: _AsyncNamespace
    reviews: _AsyncNamespace
    alerts: _AsyncNamespace
    support: _AsyncNamespace
    secrets: _AsyncNamespace
    infrastructure: _AsyncNamespace
    roles: _AsyncNamespace
    service_accounts: _AsyncNamespace
    organization: _AsyncNamespace
    members: _AsyncNamespace
    invitations: _AsyncNamespace
    groups: _AsyncNamespace
    grants: _AsyncNamespace
    operations: _AsyncNamespace
    query: _AsyncNamespace
    alert_channels: _AsyncNamespace
    alert_rules: _AsyncNamespace
    assets: _AsyncNamespace
    experiments: _AsyncNamespace
    threads: _AsyncNamespace

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        http_client: httpx.Client | None = None,
        key_id: str | None = None,
        signing_secret: str | bytes | None = None,
        hmac_audience: str | None = None,
        bearer_token: str | Callable[[], str] | None = None,
    ) -> None:
        self._bind(
            Client(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                http_client=http_client,
                key_id=key_id,
                signing_secret=signing_secret,
                hmac_audience=hmac_audience,
                bearer_token=bearer_token,
            )
        )

    def _bind(self, sync: Client) -> None:
        """Wrap ``sync`` and expose each of its namespaces as awaitable."""
        self._sync = sync
        for name in _NAMESPACES:
            setattr(self, name, _AsyncNamespace(getattr(sync, name)))

    @property
    def base_url(self) -> str:
        """The resolved API base URL."""
        return self._sync.base_url

    @property
    def rate_limit(self) -> RateLimitInfo | None:
        """Rate-limit state parsed from the most recent response, if any."""
        return self._sync.rate_limit

    def with_options(self, *, timeout: float | None) -> AsyncClient:
        """An async client for the same API whose requests use a different timeout.

        The async form of :meth:`perceivo_client.client.Client.with_options`,
        with the same argument and sharing rules::

            await client.with_options(timeout=180.0).intelligence.start(intelligence_id)

        Args:
            timeout: Seconds that bound each of the connect, read, write and
                pool waits of every attempt, except that ``files.upload``,
                ``files.replace_content`` and the three infrastructure ingests
                wait at least 150 s to read and write. ``None`` disables the
                limits.

        Returns:
            A new :class:`AsyncClient`.
        """
        derived = AsyncClient.__new__(AsyncClient)
        derived._bind(self._sync.with_options(timeout=timeout))
        return derived

    async def paginate(
        self,
        fetch: Callable[..., Any],
        *,
        limit: int = 100,
        max_items: int | None = None,
        **params: Any,
    ) -> AsyncIterator[Any]:
        """Async iterate an offset/limit list endpoint.

        The async form of :func:`perceivo_client.pagination.paginate`, with the
        same arguments; ``fetch`` is an awaitable namespace method. Most list
        operations page by ``page``/``page_size`` instead: use
        :meth:`paginate_pages` for those.
        """
        offset = 0
        yielded = 0
        while True:
            items = page_items(await fetch(limit=limit, offset=offset, **params))
            for item in items:
                yield item
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return
            if len(items) < limit:
                return
            offset += len(items)

    async def paginate_pages(
        self,
        fetch: Callable[..., Any],
        *,
        page_size: int = 25,
        max_items: int | None = None,
        **params: Any,
    ) -> AsyncIterator[Any]:
        """Async iterate an ``items,total`` page/page-size list endpoint.

        The async form of :func:`perceivo_client.pagination.paginate_pages`, with
        the same arguments, supported wrappers and errors; ``fetch`` is an
        awaitable namespace method.

        Cancelling the task stops it awaiting this helper, but the client
        cannot transport-cancel an in-flight worker request, which may finish in
        its worker thread.
        """
        _validate_page_options(page_size, max_items, params)
        if max_items == 0:
            return

        walk = _PageWalk(page_size)
        while True:
            items, last = walk.accept(await fetch(page=walk.page, page_size=page_size, **params))
            for item in items:
                yield item
                walk.yielded += 1
                if max_items is not None and walk.yielded >= max_items:
                    return
            if last:
                return

    async def aclose(self) -> None:
        """Close the HTTP connection pool.

        A pool passed in as ``http_client`` is left open: whoever created it
        closes it.
        """
        await asyncio.to_thread(self._sync.close)

    async def __aenter__(self) -> AsyncClient:
        """Return this client; :meth:`aclose` runs when the block exits."""
        return self

    async def __aexit__(self, *exc: object) -> None:
        """Close the client."""
        await self.aclose()


#: The namespace attributes declared on :class:`AsyncClient`, in order.
_NAMESPACES: tuple[str, ...] = tuple(
    name
    for name, annotation in AsyncClient.__annotations__.items()
    if annotation == "_AsyncNamespace"
)
