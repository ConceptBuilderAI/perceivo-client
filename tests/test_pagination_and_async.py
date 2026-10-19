"""G-19: pagination helper + async client."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from pydantic import BaseModel

from perceivo_client import (
    AsyncClient,
    PerceivoConnectionError,
    PerceivoNotFoundError,
    paginate,
    paginate_pages,
)
from perceivo_client.pagination import page_items
from tests._pagination_helpers import _paged_handler
from tests.conftest import make_client


def test_page_items_extracts_common_keys():
    assert page_items({"items": [1, 2]}) == [1, 2]
    assert page_items({"tickets": [1], "total": 1}) == [1]  # sole list value
    assert page_items({"data": [3]}) == [3]
    assert page_items([9, 8]) == [9, 8]
    assert page_items({"total": 0}) == []
    assert page_items("nope") == []


def test_paginate_walks_all_pages():
    # 3 full pages of 2, then a short page -> stop.
    pages = [
        {"items": [1, 2], "limit": 2, "offset": 0},
        {"items": [3, 4], "limit": 2, "offset": 2},
        {"items": [5], "limit": 2, "offset": 4},
    ]
    client, _ = make_client(_paged_handler(pages))
    got = list(paginate(client.grants.list, limit=2))
    assert got == [1, 2, 3, 4, 5]


def test_paginate_respects_max_items():
    pages = [{"items": [1, 2], "limit": 2, "offset": 0}, {"items": [3, 4], "limit": 2, "offset": 2}]
    client, _ = make_client(_paged_handler(pages))
    got = list(paginate(client.grants.list, limit=2, max_items=3))
    assert got == [1, 2, 3]


def test_paginate_forwards_params_and_offset():
    pages = [{"items": [1], "limit": 100, "offset": 0}]  # short page -> one call
    client, rec = make_client(_paged_handler(pages))
    list(paginate(client.grants.list, grantee_type="user"))
    q = dict(rec.last.url.params)
    assert q.get("grantee_type") == "user"
    assert q.get("limit") == "100"
    assert q.get("offset") == "0"


def test_async_client_mirrors_namespaces_and_awaits():
    pages = [{"items": [{"id": "o1"}], "limit": 100, "offset": 0}]
    sync, _ = make_client(_paged_handler(pages))

    async def _run():
        # Reuse the sync client's mocked transport by wrapping it.
        aclient = AsyncClient.__new__(AsyncClient)
        aclient._sync = sync
        from perceivo_client.async_client import _NAMESPACES, _AsyncNamespace

        for ns in _NAMESPACES:
            setattr(aclient, ns, _AsyncNamespace(getattr(sync, ns)))
        # awaitable method
        result = await aclient.orchestrations.list()
        assert result.items == [{"id": "o1"}]
        # async pagination
        collected = [item async for item in aclient.paginate(aclient.grants.list)]
        assert collected == [{"id": "o1"}]

    asyncio.run(_run())


def test_async_client_exposes_all_namespaces():
    from perceivo_client.async_client import _NAMESPACES

    # Every sync namespace has an async proxy attribute.
    sync, _ = make_client(_paged_handler([{"items": []}]))
    aclient = AsyncClient.__new__(AsyncClient)
    aclient._sync = sync
    from perceivo_client.async_client import _AsyncNamespace

    for ns in _NAMESPACES:
        setattr(aclient, ns, _AsyncNamespace(getattr(sync, ns)))
        assert hasattr(aclient, ns)


def _page_total_handler(total: int):
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        page_size = int(request.url.params["page_size"])
        start = (page - 1) * page_size
        items = list(range(start, min(start + page_size, total)))
        return httpx.Response(200, json={"items": items, "total": total})

    return handler


def _async_from_sync(sync):
    aclient = AsyncClient.__new__(AsyncClient)
    aclient._sync = sync
    from perceivo_client.async_client import _NAMESPACES, _AsyncNamespace

    for namespace in _NAMESPACES:
        setattr(aclient, namespace, _AsyncNamespace(getattr(sync, namespace)))
    return aclient


@pytest.mark.parametrize("namespace", ["orchestrations", "intelligence", "reviews"])
def test_paginate_pages_walks_supported_wrappers_with_exact_query_shape(namespace):
    client, recorder = make_client(_page_total_handler(60))

    got = list(
        paginate_pages(
            getattr(client, namespace).list,
            page_size=25,
        )
    )

    assert got == list(range(60))
    assert [dict(request.url.params) for request in recorder.requests] == [
        {"page": "1", "page_size": "25"},
        {"page": "2", "page_size": "25"},
        {"page": "3", "page_size": "25"},
    ]


@pytest.mark.parametrize("namespace", ["orchestrations", "intelligence", "reviews"])
def test_async_paginate_pages_walks_supported_wrappers(namespace):
    sync, recorder = make_client(_page_total_handler(60))
    client = _async_from_sync(sync)

    async def collect():
        return [
            item
            async for item in client.paginate_pages(
                getattr(client, namespace).list,
                page_size=25,
            )
        ]

    assert asyncio.run(collect()) == list(range(60))
    assert [dict(request.url.params) for request in recorder.requests] == [
        {"page": "1", "page_size": "25"},
        {"page": "2", "page_size": "25"},
        {"page": "3", "page_size": "25"},
    ]


def test_async_paginate_pages_obeys_max_items_and_zero_request_boundary():
    sync, recorder = make_client(_page_total_handler(60))
    client = _async_from_sync(sync)

    async def collect(max_items):
        return [
            item
            async for item in client.paginate_pages(
                client.orchestrations.list,
                page_size=25,
                max_items=max_items,
            )
        ]

    assert asyncio.run(collect(27)) == list(range(27))
    assert len(recorder.requests) == 2

    recorder.requests.clear()
    assert asyncio.run(collect(0)) == []
    assert recorder.requests == []


def test_paginate_pages_has_no_page_100_ceiling():
    calls: list[dict] = []

    def fetch(**params):
        calls.append(params)
        return {"items": [params["page"]], "total": 101}

    assert list(paginate_pages(fetch, page_size=1)) == list(range(1, 102))
    assert calls[-1] == {"page": 101, "page_size": 1}


def test_paginate_pages_truncates_at_max_items_without_reordering():
    client, recorder = make_client(_page_total_handler(60))

    got = list(paginate_pages(client.orchestrations.list, page_size=25, max_items=27))

    assert got == list(range(27))
    assert len(recorder.requests) == 2


def test_paginate_pages_max_items_zero_makes_no_request():
    calls = 0

    def fetch(**_params):
        nonlocal calls
        calls += 1
        return {"items": [], "total": 0}

    assert list(paginate_pages(fetch, max_items=0)) == []
    assert calls == 0


@pytest.mark.parametrize("name", ["page", "limit", "offset"])
def test_paginate_pages_rejects_reserved_caller_params_before_request(name):
    calls = 0

    def fetch(**_params):
        nonlocal calls
        calls += 1
        return {"items": [], "total": 0}

    with pytest.raises(ValueError, match="reserved query parameter"):
        list(paginate_pages(fetch, **{name: 1}))
    assert calls == 0


@pytest.mark.parametrize("value", [True, False, "25", 25.0])
def test_paginate_pages_rejects_non_integer_page_size(value):
    with pytest.raises(TypeError, match="page_size"):
        list(paginate_pages(lambda **_params: {}, page_size=value))


@pytest.mark.parametrize("value", [-1, 0, 101])
def test_paginate_pages_rejects_out_of_range_page_size(value):
    with pytest.raises(ValueError, match="between 1 and 100"):
        list(paginate_pages(lambda **_params: {}, page_size=value))


@pytest.mark.parametrize("value", [True, False, "2", 2.0])
def test_paginate_pages_rejects_non_integer_max_items(value):
    with pytest.raises(TypeError, match="max_items"):
        list(paginate_pages(lambda **_params: {}, max_items=value))


def test_paginate_pages_rejects_negative_max_items():
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        list(paginate_pages(lambda **_params: {}, max_items=-1))


@pytest.mark.parametrize(
    "response, message",
    [
        ([1], "mapping envelope"),
        ({"files": [], "total": 0}, "envelope.items"),
        ({"items": []}, "envelope.total"),
        ({"items": [], "total": True}, "envelope.total"),
        ({"items": [], "total": -1}, "envelope.total"),
        ({"items": "bad", "total": 0}, "envelope.items"),
        ({"items": [1], "total": 3}, "early short"),
        ({"items": [1, 2], "total": 1}, "oversized page"),
    ],
)
def test_paginate_pages_rejects_unsupported_or_malformed_envelopes(response, message):
    with pytest.raises(ValueError, match=message):
        list(paginate_pages(lambda **_params: response, page_size=2))


def test_paginate_pages_normalizes_pydantic_envelope():
    class Envelope(BaseModel):
        items: list[int]
        total: int

    assert list(
        paginate_pages(
            lambda **_params: Envelope(items=[1, 2], total=2),
            page_size=2,
        )
    ) == [1, 2]


def test_paginate_pages_rejects_total_drift():
    pages = iter(
        [
            {"items": [1], "total": 2},
            {"items": [2], "total": 3},
        ]
    )

    with pytest.raises(ValueError, match="stable across pages"):
        list(paginate_pages(lambda **_params: next(pages), page_size=1))


def test_paginate_pages_propagates_transport_errors_unchanged():
    error = PerceivoConnectionError("offline")

    def fetch(**_params):
        raise error

    with pytest.raises(PerceivoConnectionError) as raised:
        list(paginate_pages(fetch))
    assert raised.value is error


def test_paginate_pages_propagates_non_2xx_errors_unchanged():
    client, _recorder = make_client(
        lambda _request: httpx.Response(404, json={"detail": "missing"})
    )

    with pytest.raises(PerceivoNotFoundError):
        list(paginate_pages(client.orchestrations.list))


def test_async_paginate_pages_discloses_thread_backed_cancellation_limit():
    assert "cannot transport-cancel an in-flight worker" in AsyncClient.paginate_pages.__doc__
