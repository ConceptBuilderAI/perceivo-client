"""G-19: `paginate` against the served offset routes, and the async client's
rate limit, construction and lifecycle. Split from tests/test_pagination_and_async.py."""

from __future__ import annotations

import asyncio
import json
import pathlib

import httpx
import pytest

from perceivo_client import (
    AsyncClient,
    Client,
    paginate,
)
from tests._pagination_helpers import _paged_handler
from tests.conftest import BASE_URL, make_client

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
    assert len(page_routes) == 29


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
