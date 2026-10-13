"""G-19: pagination helper + async client."""

from __future__ import annotations

import asyncio
import json
import pathlib

import httpx
import pytest
from pydantic import BaseModel

from perceivo_client import (
    AsyncClient,
    Client,
    PerceivoConnectionError,
    PerceivoNotFoundError,
    paginate,
    paginate_pages,
)
from perceivo_client.pagination import page_items
from tests.conftest import BASE_URL, make_client


def test_page_items_extracts_common_keys():
    assert page_items({"items": [1, 2]}) == [1, 2]
    assert page_items({"tickets": [1], "total": 1}) == [1]  # sole list value
    assert page_items({"data": [3]}) == [3]
    assert page_items([9, 8]) == [9, 8]
    assert page_items({"total": 0}) == []
    assert page_items("nope") == []


def _paged_handler(pages):
    """Return a handler that serves successive JSON pages by request order."""
    state = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        i = state["i"]
        state["i"] = min(i + 1, len(pages) - 1)
        return httpx.Response(200, json=pages[i])

    return handler


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


# --- what `paginate` is actually for -----------------------------
#
# The tests above drive `paginate` with a mock that serves whatever the handler
# was given regardless of the query string, so a helper sending the wrong
# parameters would read green. These cases pin the routes instead of the fixture.


def _async(handler) -> AsyncClient:
    """A real AsyncClient whose HTTP layer is ``handler`` (no network)."""
    return AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)),
    )


_SPEC_PATH = pathlib.Path(__file__).resolve().parents[1] / "openapi" / "openapi-v1.json"
_HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}


def _query_parameter_names() -> dict[tuple[str, str], set[str]]:
    spec = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    out: dict[tuple[str, str], set[str]] = {}
    for template, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(op, dict):
                continue
            out[(method.upper(), template)] = {
                p.get("name")
                for p in op.get("parameters", [])
                if isinstance(p, dict) and p.get("in") == "query"
            }
    return out


def test_the_served_offset_routes_are_exactly_these_six():
    """The measurement behind `paginate`'s narrowed docstring.

    Six routes declare limit/offset; the SDK wraps three of them (cost entries,
    grants and logs), and the three
    billing-diagnostics reads are `unexposed` in the endpoint-suite table. If a
    future spec adds or drops an offset route, the documented scope is wrong
    and this fails, which is the whole point of asserting the exact paths
    rather than a count alone.
    """
    params = _query_parameter_names()
    offset_routes = sorted(route for route, names in params.items() if "offset" in names)
    page_routes = [route for route, names in params.items() if "page" in names]

    assert offset_routes == [
        ("GET", "/v1/billing/diagnostics/cost-ledger"),
        ("GET", "/v1/billing/diagnostics/infra-overhead"),
        ("GET", "/v1/billing/diagnostics/snapshots"),
        ("GET", "/v1/cost-entries/organization"),
        ("GET", "/v1/grants"),
        ("GET", "/v1/logs"),
    ]
    assert len(page_routes) == 30


def test_paginate_is_correct_for_the_one_offset_route_it_documents():
    """`billing.organization_costs` -> CostSummary, whose sole list is `entries`."""
    pages = [
        {"entries": [{"id": "e1"}, {"id": "e2"}], "total_cost_usd": 3.0},
        {"entries": [{"id": "e3"}], "total_cost_usd": 3.0},
    ]
    client, rec = make_client(_paged_handler(pages))

    got = list(paginate(client.billing.organization_costs, limit=2))

    assert got == [{"id": "e1"}, {"id": "e2"}, {"id": "e3"}]
    assert rec.requests[0].url.path == "/v1/cost-entries/organization"
    assert dict(rec.requests[0].url.params) == {"limit": "2", "offset": "0"}
    assert dict(rec.requests[1].url.params) == {"limit": "2", "offset": "2"}


def test_paginate_is_correct_for_the_grants_and_logs_offset_routes():
    """`grants.list` answers a bare array and `query.logs` a `LogPage` whose list is `logs`."""

    def grant(n: int) -> dict:
        return {
            "id": f"00000000-0000-4000-8000-00000000000{n}",
            "grantee_type": "user",
            "grantee_id": "00000000-0000-4000-8000-000000000010",
            "resource_type": "asset",
            "resource_id": "00000000-0000-4000-8000-000000000020",
            "granted_at": "2026-10-03T00:00:00Z",
        }

    grants = [[grant(1), grant(2)], [grant(3)]]
    client, rec = make_client(_paged_handler(grants))

    walked = list(paginate(client.grants.list, limit=2))
    assert [str(g.id)[-1] for g in walked] == ["1", "2", "3"]
    assert rec.requests[0].url.path == "/v1/grants"
    assert dict(rec.requests[1].url.params) == {"limit": "2", "offset": "2"}

    logs = [
        {"scope": "run", "channel": None, "logs": [{"line": "a"}, {"line": "b"}]},
        {"scope": "run", "channel": None, "logs": [{"line": "c"}]},
    ]
    client, rec = make_client(_paged_handler(logs))

    got = list(paginate(client.query.logs, limit=2, scope="run", scope_id="r1"))

    assert got == [{"line": "a"}, {"line": "b"}, {"line": "c"}]
    assert rec.requests[0].url.path == "/v1/logs"
    assert dict(rec.requests[1].url.params) == {
        "limit": "2",
        "offset": "2",
        "scope": "run",
        "scope_id": "r1",
    }


def test_paginate_cannot_send_limit_offset_to_a_page_size_route():
    """Why `paginate_pages` exists: limit/offset are not a page route's parameters.

    The wrapper takes only the parameters the route declares, so `paginate`
    driving it fails on the first call instead of sending a query the route
    ignores. The declared set is read from the vendored spec, not the mock.
    """
    client, rec = make_client(_paged_handler([{"items": [], "limit": 2, "offset": 0}]))

    with pytest.raises(TypeError, match="limit"):
        list(paginate(client.orchestrations.list, limit=2))

    assert rec.requests == []
    declared = _query_parameter_names()[("GET", "/v1/orchestrations")]
    assert not {"limit", "offset"} & declared
    assert {"page", "page_size"} <= declared


def test_async_paginate_carries_the_same_offset_contract():
    client = _async(_paged_handler([{"entries": [{"id": "e1"}], "total_cost_usd": 1.0}]))

    async def drive():
        return [x async for x in client.paginate(client.billing.organization_costs, limit=2)]

    assert asyncio.run(drive()) == [{"id": "e1"}]


# --- AsyncClient.rate_limit --------------------------------------


def test_async_client_exposes_rate_limit_like_the_sync_client():
    headers = {
        "X-RateLimit-Limit": "600",
        "X-RateLimit-Remaining": "597",
        "X-RateLimit-Reset": "1720000000",
    }
    client = _async(lambda _r: httpx.Response(200, json={"items": [], "total": 0}, headers=headers))

    assert client.rate_limit is None, "no request yet -- there is nothing to report"
    asyncio.run(client.orchestrations.list())

    rl = client.rate_limit
    assert rl is not None
    assert (rl.limit, rl.remaining, rl.reset) == (600, 597, 1720000000)


def test_async_rate_limit_matches_the_wrapped_sync_clients_value():
    """The property must read the same transport, not a second one."""
    headers = {"X-RateLimit-Limit": "5", "X-RateLimit-Remaining": "4"}
    client = _async(lambda _r: httpx.Response(200, json={"items": [], "total": 0}, headers=headers))
    asyncio.run(client.orchestrations.list())

    assert client.rate_limit is client._sync.rate_limit
    assert client.rate_limit.limit == 5


def test_async_rate_limit_is_a_property_not_a_coroutine():
    """A namespace proxy wraps callables in `asyncio.to_thread`; this is on the
    client itself and must be readable without awaiting, exactly like `base_url`."""
    client = _async(lambda _r: httpx.Response(200, json={"items": [], "total": 0}))

    assert isinstance(type(client).rate_limit, property)
    assert not asyncio.iscoroutine(client.rate_limit)


# --- AsyncClient construction and lifecycle --------------------------------------


def test_async_client_namespaces_are_exactly_the_sync_clients():
    from perceivo_client.async_client import _NAMESPACES
    from perceivo_client.resources._base import BaseResource

    sync = Client(api_key="k", base_url=BASE_URL)
    sync_namespaces = [n for n, v in vars(sync).items() if isinstance(v, BaseResource)]
    assert list(_NAMESPACES) == sync_namespaces
    aclient = AsyncClient(api_key="k", base_url=BASE_URL)
    for name in sync_namespaces:
        assert getattr(aclient, name) is not None


def test_async_client_takes_the_same_keyword_arguments_as_the_sync_client():
    import inspect

    sync_params = inspect.signature(Client.__init__).parameters
    async_params = inspect.signature(AsyncClient.__init__).parameters
    assert list(async_params) == list(sync_params)
    for name, param in sync_params.items():
        assert async_params[name].default == param.default
        assert async_params[name].kind == param.kind


def test_async_client_rejects_an_unknown_argument():
    with pytest.raises(TypeError):
        AsyncClient(api_key="k", base_url=BASE_URL, max_backof=1.0)


def test_async_client_forwards_its_arguments_to_the_wrapped_client():
    aclient = AsyncClient(api_key="k", base_url=BASE_URL + "/", max_retries=0)
    assert aclient.base_url == BASE_URL
    assert aclient._sync._transport._max_retries == 0


class _ClosingClient(httpx.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        super().close()


def test_async_context_manager_closes_the_pool_it_owns():
    async def scenario():
        async with AsyncClient(api_key="k", base_url=BASE_URL) as aclient:
            pool = aclient._sync._transport._client
            assert not pool.is_closed
        return pool

    assert asyncio.run(scenario()).is_closed


def test_async_and_sync_clients_both_leave_an_injected_pool_open():
    sync_pool = _ClosingClient(base_url=BASE_URL)
    with Client(api_key="k", base_url=BASE_URL, http_client=sync_pool):
        pass
    async_pool = _ClosingClient(base_url=BASE_URL)

    async def scenario():
        async with AsyncClient(api_key="k", base_url=BASE_URL, http_client=async_pool):
            pass

    asyncio.run(scenario())
    assert (sync_pool.close_calls, async_pool.close_calls) == (0, 0)
