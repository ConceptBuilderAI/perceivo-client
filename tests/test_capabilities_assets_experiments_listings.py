"""Capabilities, assets and experiments: listings, typed returns, updates and graphs.

The second half of ``tests/test_capabilities_assets_experiments.py``: which
lists ``paginate_pages`` walks and which it refuses, typed returns, ``204``
bodies, async parity, the capability update's two answers, the execution
graph listings, and the query parameters each list wrapper sends.
"""

from __future__ import annotations

import asyncio
import functools

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import (
    AssetLineageRead,
    AssetRead,
    CapabilityEvaluationSummaryRead,
    CapabilityTriggerRead,
    CapabilityUpdateResult,
    ComponentRead,
    ComponentUpdateResult,
    ExperimentListResponse,
    ExperimentRead,
    ExperimentStopResponse,
    GroupRead,
    LineageRestoreResult,
    PaginatedItemsResponse,
)
from tests._capabilities_fixtures import (
    _K,
    _TRIGGER,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync, _page_total_handler

# --- pagination --------------------------------------------------------------------


def test_paginate_pages_walks_experiments_list():
    client, rec = make_client(_page_total_handler(60))

    got = list(paginate_pages(client.experiments.list, page_size=25))

    assert got == list(range(60))
    assert [r.url.params["page"] for r in rec.requests] == ["1", "2", "3"]


def test_paginate_pages_walks_a_bound_list_orchestrations():
    client, rec = make_client(_page_total_handler(30))
    fetch = functools.partial(client.capabilities.list_orchestrations, "cap-1")

    got = list(paginate_pages(fetch, page_size=20))

    assert got == list(range(30))
    assert {r.url.path for r in rec.requests} == {f"{_K}/cap-1/orchestrations"}


def test_async_paginate_pages_walks_experiments_list():
    sync, rec = make_client(_page_total_handler(30))
    client = _async_from_sync(sync)

    async def walk():
        return [item async for item in client.paginate_pages(client.experiments.list, page_size=20)]

    assert asyncio.run(walk()) == list(range(30))
    assert len(rec.requests) == 2


def test_list_triggers_is_a_typed_bare_array():
    client, rec = make_client(json_handler([_TRIGGER]))

    got = client.capabilities.list_triggers("cap-1")

    assert [t.id for t in got] == ["trg-1"]
    assert isinstance(got[0], CapabilityTriggerRead)
    assert dict(rec.last.url.params) == {}


def test_paginate_pages_refuses_the_bare_trigger_list():
    client, _ = make_client(json_handler([_TRIGGER]))
    walker = paginate_pages(lambda **_kw: client.capabilities.list_triggers("cap-1"))

    with pytest.raises(ValueError):
        next(walker)


# --- typed returns and 204s ---------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.capabilities.get_evaluation_summary("k1"), CapabilityEvaluationSummaryRead),
        (lambda c: c.capabilities.get_lineage("k1"), AssetLineageRead),
        (lambda c: c.capabilities.restore("k1"), LineageRestoreResult),
        (lambda c: c.capabilities.list_orchestrations("k1"), PaginatedItemsResponse),
        (lambda c: c.capabilities.create_trigger("k1", {}), CapabilityTriggerRead),
        (lambda c: c.capabilities.update_trigger("k1", "t1", {}), CapabilityTriggerRead),
        (lambda c: c.assets.restore("a1"), AssetRead),
        (lambda c: c.experiments.list(), ExperimentListResponse),
        (lambda c: c.experiments.get("e1"), ExperimentRead),
        (lambda c: c.experiments.update("e1", {}), ExperimentRead),
        (lambda c: c.experiments.stop("e1"), ExperimentStopResponse),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x"}))

    assert isinstance(call(client), model)


@pytest.mark.parametrize(
    "call,path",
    [
        (lambda c: c.capabilities.delete_traffic("k1"), f"{_K}/k1/traffic"),
        (lambda c: c.capabilities.delete_traffic_plan("k1"), f"{_K}/k1/traffic-plan"),
        (lambda c: c.capabilities.delete_trigger("k1", "t1"), f"{_K}/k1/triggers/t1"),
        (lambda c: c.capabilities.delete_version("k1", "v1"), f"{_K}/k1/versions/v1"),
        (lambda c: c.capabilities.detach_orchestration("k1", "o1"), f"{_K}/k1/orchestrations/o1"),
    ],
)
def test_deletes_return_none_on_no_content(call, path):
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert call(client) is None
    assert rec.last.method == "DELETE"
    assert rec.last.url.path == path


# --- async parity ------------------------------------------------------------------


@pytest.mark.parametrize("namespace", ["assets", "experiments"])
def test_new_namespaces_are_mirrored_on_the_async_client(namespace):
    assert namespace in _NAMESPACES


def test_async_trigger_create_awaits_and_hits_the_exact_path():
    sync, rec = make_client(json_handler(_TRIGGER, status=201))
    client = _async_from_sync(sync)

    got = asyncio.run(client.capabilities.create_trigger("cap-1", {"cron_expression": "0 * * * *"}))

    assert isinstance(got, CapabilityTriggerRead)
    assert rec.last.url.path == f"{_K}/cap-1/triggers"


# --- capability update: in place or a new version ------------------------------------

_CAPABILITY = {"id": "cap-1", "name": "triage", "organization_id": "org-1"}


def test_an_in_place_capability_update_returns_the_capability_with_version_created():
    client, _ = make_client(json_handler({**_CAPABILITY, "version_created": False}))

    got = client.capabilities.update("cap-1", {"name": "triage"})

    assert isinstance(got, CapabilityUpdateResult)
    assert (got.id, got.version_created) == ("cap-1", False)


def test_a_versioning_capability_update_returns_the_new_version_at_the_top_level():
    """The platform answers ``{capability, versioned, propagation_summary}`` with no ``id``."""
    summary = {"total_orchestrations": 2, "orchestrations_ok": [], "orchestrations_with_errors": []}
    body = {
        "capability": {**_CAPABILITY, "id": "cap-2"},
        "versioned": True,
        "propagation_summary": summary,
    }
    client, _ = make_client(json_handler(body))

    got = client.capabilities.update("cap-1", {"end_component_id": "end-2"})

    assert isinstance(got, CapabilityUpdateResult)
    assert got.id == "cap-2"
    assert got.name == "triage"
    assert got.version_created is True
    assert got.propagation_summary == summary


def test_a_versioning_update_with_nothing_propagated_keeps_a_null_summary():
    body = {"capability": {**_CAPABILITY, "id": "cap-2"}, "versioned": True}
    client, _ = make_client(json_handler(body))

    got = client.capabilities.update("cap-1", {"end_component_id": "end-2"})

    assert (got.id, got.version_created, got.propagation_summary) == ("cap-2", True, None)


def test_async_versioning_capability_update_is_lifted_too():
    body = {"capability": {**_CAPABILITY, "id": "cap-2"}, "versioned": True}
    sync, _ = make_client(json_handler(body))
    client = _async_from_sync(sync)

    got = asyncio.run(client.capabilities.update("cap-1", {"end_component_id": "end-2"}))

    assert (got.id, got.version_created) == ("cap-2", True)


# --- execution graphs ------------------------------------------------------------------


@pytest.mark.parametrize(
    "call,path",
    [
        (lambda c: c.capabilities.list_execution_graphs("cap-1"), f"{_K}/cap-1/execution-graphs"),
        (
            lambda c: c.capabilities.list_graph_configs("cap-1"),
            f"{_K}/cap-1/execution-graphs/configs",
        ),
    ],
    ids=["graphs", "configs"],
)
def test_graph_listings_return_the_items_total_object(call, path):
    page = {"items": [{"graph_id": "g-1", "entry_count": 3}], "total": 1}
    client, rec = make_client(json_handler(page))

    got = call(client)

    assert isinstance(got, PaginatedItemsResponse)
    assert (got.items, got.total) == ([{"graph_id": "g-1", "entry_count": 3}], 1)
    assert rec.last.url.path == path


def test_get_execution_graph_returns_the_graph_document_unchanged():
    document = {"graph_id": "g-1", "created_at": "2026-10-03T00:00:00Z", "entries": [{"n": 1}]}
    client, _ = make_client(json_handler(document))

    assert client.capabilities.get_execution_graph("cap-1", "g-1") == document


# --- list parameters: sent exactly as the platform reads them ------------------------


@pytest.mark.parametrize(
    "call,path,query",
    [
        (
            lambda c: c.alerts.list(page=2, page_size=50, severity="critical", status="active"),
            "/v1/alerts",
            {
                "page": "2",
                "page_size": "50",
                "filter[severity]": "critical",
                "filter[status]": "active",
            },
        ),
        (lambda c: c.alerts.list(q="disk"), "/v1/alerts", {"q": "disk"}),
        (
            lambda c: c.capabilities.list(page=3, page_size=100),
            "/v1/capabilities",
            {"page": "3", "page_size": "100"},
        ),
        (
            lambda c: c.capabilities.list_orchestrations("cap-1", page=2),
            "/v1/capabilities/cap-1/orchestrations",
            {"page": "2"},
        ),
        (
            lambda c: c.components.list(page_size=10),
            "/v1/components",
            {"page_size": "10"},
        ),
        (
            lambda c: c.experiments.list(page=4, page_size=5),
            "/v1/experiments",
            {"page": "4", "page_size": "5"},
        ),
    ],
    ids=["alerts", "alerts-q", "capabilities", "members", "components", "experiments"],
)
def test_keyword_arguments_become_their_query_parameters(call, path, query):
    client, rec = make_client(json_handler([]))

    call(client)

    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == query


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.alerts.list(),
        lambda c: c.alerts.get_summary(),
        lambda c: c.capabilities.list(),
        lambda c: c.capabilities.list_evaluations("cap-1"),
        lambda c: c.components.list(),
        lambda c: c.experiments.list(),
        lambda c: c.groups.list(),
        lambda c: c.groups.list_members("grp-1"),
    ],
)
def test_a_call_without_arguments_sends_no_query(call):
    client, rec = make_client(json_handler([]))

    call(client)

    assert rec.last.url.query == b""


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.groups.list(page=2),
        lambda c: c.alerts.get_summary(page=1),
        lambda c: c.capabilities.list(sort_by="name"),
        lambda c: c.components.list(sort_order="asc"),
    ],
)
def test_a_parameter_the_platform_does_not_read_is_refused_before_sending(call):
    client, rec = make_client(json_handler([]))

    with pytest.raises(TypeError):
        call(client)
    assert rec.requests == []


def test_groups_list_returns_every_group_from_one_request():
    """The platform ignores page parameters and answers the full list every time."""
    groups = [{"id": f"g-{n}", "name": f"group {n}", "organization_id": "org-1"} for n in range(30)]
    client, rec = make_client(json_handler(groups))

    got = client.groups.list()

    assert [g.id for g in got] == [f"g-{n}" for n in range(30)]
    assert isinstance(got[0], GroupRead)
    assert len(rec.requests) == 1


def test_components_list_returns_typed_components():
    rows = [{"id": "cmp-1", "name": "scorer", "script": "x = 1"}]
    client, _ = make_client(json_handler(rows))

    got = client.components.list()

    assert isinstance(got[0], ComponentRead)
    assert (got[0].id, got[0].script) == ("cmp-1", "x = 1")


def test_components_update_returns_the_new_version_with_version_created():
    client, _ = make_client(
        json_handler({"id": "cmp-2", "name": "scorer", "version_created": True})
    )

    got = client.components.update("cmp-1", {"tags": ["triage"]})

    assert isinstance(got, ComponentUpdateResult)
    assert (got.id, got.version_created) == ("cmp-2", True)


def test_files_download_returns_the_raw_bytes():
    payload = bytes(range(256))
    client, rec = make_client(lambda _r: httpx.Response(200, content=payload))

    assert client.files.download("ent-1") == payload
    assert rec.last.url.path == "/v1/files/entries/ent-1/content"
