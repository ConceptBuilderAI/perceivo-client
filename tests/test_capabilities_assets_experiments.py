"""Capabilities, assets and experiments, plus the list parameters of resources A.

Method and path for every row are pinned by ``test_wrapper_matrix``; this
module pins what that matrix cannot see: the ``null`` traffic reads, the
bodiless verbs, empty-body defaults, the untyped bundle round trip, the
experiment delete's ``200`` receipt, the experiment create -> run -> session id
chain, the capability update's two answers, which lists ``paginate_pages``
walks and which it refuses, typed returns, ``204`` bodies, async parity, and
the query parameters each list wrapper sends.
"""

from __future__ import annotations

import asyncio
import functools
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import (
    AssetLineageRead,
    AssetRead,
    CapabilityEvaluationConfigRead,
    CapabilityEvaluationSummaryRead,
    CapabilityRead,
    CapabilityTrafficPlanRead,
    CapabilityTriggerRead,
    CapabilityUpdateResult,
    ComponentRead,
    ComponentUpdateResult,
    ExperimentDeleteResponse,
    ExperimentListResponse,
    ExperimentRead,
    ExperimentRunResponse,
    ExperimentSession,
    ExperimentStopResponse,
    GroupRead,
    LifecycleOperationResponse,
    LineageRestoreResult,
    PaginatedItemsResponse,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync, _page_total_handler

_K = "/v1/capabilities"
_A = "/v1/assets"
_E = "/v1/experiments"
_EXPERIMENT = {
    "id": "exp-1",
    "name": "notebook",
    "organization_id": "org-1",
    "user_id": "u1",
    "status": "DRAFT",
    "created_at": "2026-10-03T00:00:00Z",
}
_TRIGGER = {
    "id": "trg-1",
    "trigger_type": "cron",
    "cron_expression": "0 * * * *",
    "timezone": "UTC",
    "enabled": True,
}
_BUNDLE = {"export_type": "component", "component": {"name": "scorer", "script": "x = 1"}}


def _routed(routes: dict[tuple[str, str], tuple[int, object]]):
    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    return handler


_EXPERIMENT_ROUTES = {
    ("POST", _E): (201, _EXPERIMENT),
    ("POST", f"{_E}/exp-1/run"): (
        202,
        {"experiment_id": "exp-1", "status": "QUEUED", "job_id": "job-1"},
    ),
    ("GET", f"{_E}/exp-1/session"): (200, {"experiment_id": "exp-1", "status": "QUEUED"}),
}


# --- the experiment chain --------------------------------------------------------


def test_experiment_id_round_trips_into_run_and_session():
    client, rec = make_client(_routed(_EXPERIMENT_ROUTES))

    experiment = client.experiments.create({"name": "notebook"})
    queued = client.experiments.run(experiment.id)
    session = client.experiments.get_session(queued.experiment_id)

    assert isinstance(experiment, ExperimentRead)
    assert isinstance(queued, ExperimentRunResponse)
    assert isinstance(session, ExperimentSession)
    assert session.connection_endpoint is None
    assert [r.method for r in rec.requests] == ["POST", "POST", "GET"]
    assert json.loads(rec.requests[0].content) == {"name": "notebook"}


def test_async_experiment_chain_awaits_each_step():
    sync, rec = make_client(_routed(_EXPERIMENT_ROUTES))
    client = _async_from_sync(sync)

    async def drive():
        experiment = await client.experiments.create({"name": "notebook"})
        await client.experiments.run(experiment.id)
        return await client.experiments.get_session(experiment.id)

    session = asyncio.run(drive())

    assert isinstance(session, ExperimentSession)
    assert [r.url.path for r in rec.requests] == [_E, f"{_E}/exp-1/run", f"{_E}/exp-1/session"]


def test_experiment_delete_returns_its_receipt_not_none():
    client, rec = make_client(json_handler({"status": "deleted", "experiment_id": "exp-1"}))

    got = client.experiments.delete("exp-1")

    assert isinstance(got, ExperimentDeleteResponse)
    assert got.experiment_id == "exp-1"
    assert rec.last.method == "DELETE"


# --- bodiless verbs and empty-body defaults ---------------------------------------


@pytest.mark.parametrize(
    "call,method,path",
    [
        (lambda c: c.experiments.run("exp-1"), "POST", f"{_E}/exp-1/run"),
        (lambda c: c.experiments.stop("exp-1"), "POST", f"{_E}/exp-1/stop"),
        (lambda c: c.assets.restore("ast-1"), "POST", f"{_A}/ast-1/restore"),
        (lambda c: c.capabilities.restore("cap-1"), "POST", f"{_K}/cap-1/restore"),
        (
            lambda c: c.capabilities.attach_orchestration("cap-1", "orc-1"),
            "PUT",
            f"{_K}/cap-1/orchestrations/orc-1",
        ),
        (lambda c: c.capabilities.restart("cap-1"), "POST", f"{_K}/cap-1/restart"),
        (lambda c: c.capabilities.evaluate("cap-1"), "POST", f"{_K}/cap-1/evaluate"),
        (
            lambda c: c.capabilities.build_from_config("cap-1", "cfg-1"),
            "POST",
            f"{_K}/cap-1/execution-graphs/configs/cfg-1/build",
        ),
        (lambda c: c.alerts.acknowledge("al-1"), "POST", "/v1/alerts/al-1/acknowledge"),
        (lambda c: c.alerts.resolve("al-1"), "POST", "/v1/alerts/al-1/resolve"),
        (lambda c: c.alert_rules.test("r-1"), "POST", "/v1/alert-rules/r-1/test"),
    ],
)
def test_bodiless_operations_send_no_body(call, method, path):
    client, rec = make_client(json_handler({"id": "x", "status": "active"}))

    call(client)

    assert rec.last.method == method
    assert rec.last.url.path == path
    assert rec.last.content == b""


def test_attach_orchestration_returns_none_on_no_content():
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert client.capabilities.attach_orchestration("cap-1", "orc-1") is None
    assert rec.last.method == "PUT"


@pytest.mark.parametrize(
    "call,path,model",
    [
        (lambda c: c.capabilities.copy("cap-1"), f"{_K}/cap-1/copy", CapabilityRead),
        (lambda c: c.assets.copy("ast-1"), f"{_A}/ast-1/copy", AssetRead),
    ],
)
def test_copy_sends_an_empty_object_without_a_body(call, path, model):
    client, rec = make_client(json_handler({"id": "copy-1"}, status=201))

    got = call(client)

    assert isinstance(got, model)
    assert rec.last.url.path == path
    assert rec.last.content == b"{}"


def test_replace_evaluation_config_is_a_put_of_the_whole_document():
    body = {"enabled": True, "evaluation_window_hours": 24}
    client, rec = make_client(json_handler({"capability_id": "cap-1", "enabled": True}))

    got = client.capabilities.replace_evaluation_config("cap-1", body)

    assert isinstance(got, CapabilityEvaluationConfigRead)
    assert rec.last.method == "PUT"
    assert rec.last.url.path == f"{_K}/cap-1/evaluation-config"
    assert json.loads(rec.last.content) == body


# --- traffic plans -----------------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.capabilities.get_traffic("cap-1"),
        lambda c: c.capabilities.get_traffic_plan("cap-1"),
    ],
)
def test_traffic_reads_return_none_when_there_is_no_live_plan(call):
    client, rec = make_client(json_handler(None))

    assert call(client) is None
    assert rec.last.method == "GET"


_PLAN = {
    "id": "plan-1",
    "capability_id": "cap-1",
    "status": "active",
    "change_source": "user_manual",
    "created_at": "2026-10-03T00:00:00Z",
    "allocations": [
        {
            "id": "al-1",
            "traffic_plan_id": "plan-1",
            "orchestration_id": "orc-1",
            "role": "champion",
            "traffic_percent": 100,
        }
    ],
}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.capabilities.get_traffic("cap-1"),
        lambda c: c.capabilities.get_traffic_plan("cap-1"),
    ],
    ids=["traffic", "traffic-plan"],
)
def test_both_traffic_reads_return_the_plan_with_its_allocations(call):
    """``/traffic-plan`` answers the same plan record as ``/traffic``, not orchestration weights."""
    client, _ = make_client(json_handler(_PLAN))

    plan = call(client)

    assert isinstance(plan, CapabilityTrafficPlanRead)
    assert [(a.orchestration_id, a.traffic_percent) for a in plan.allocations] == [("orc-1", 100)]


def test_replace_traffic_and_get_traffic_share_the_path_not_the_verb():
    client, rec = make_client(json_handler({"capability_id": "cap-1"}))

    client.capabilities.replace_traffic("cap-1", {"allocations": []})
    client.capabilities.get_traffic("cap-1")

    assert [(r.method, r.url.path) for r in rec.requests] == [
        ("PUT", f"{_K}/cap-1/traffic"),
        ("GET", f"{_K}/cap-1/traffic"),
    ]


def test_apply_traffic_plan_forwards_the_plan():
    body = {"traffic_plan": {"orc-1": 100}, "change_reason": "rollout"}
    client, rec = make_client(json_handler({"status": "accepted"}))

    got = client.capabilities.apply_traffic_plan("cap-1", body)

    assert isinstance(got, LifecycleOperationResponse)
    assert rec.last.url.path == f"{_K}/cap-1/traffic-plan"
    assert json.loads(rec.last.content) == body


# --- assets bundles ----------------------------------------------------------------


def test_export_bundle_round_trips_into_import_unchanged():
    routes = {
        ("GET", f"{_A}/ast-1/export"): (200, _BUNDLE),
        ("POST", f"{_A}/import"): (201, {"id": "cmp-9", "name": "scorer"}),
    }
    client, rec = make_client(_routed(routes))

    bundle = client.assets.export_bundle("ast-1")
    created = client.assets.import_bundle({"bundle": bundle})

    assert bundle == _BUNDLE
    assert created == {"id": "cmp-9", "name": "scorer"}
    assert json.loads(rec.last.content) == {"bundle": _BUNDLE}


def test_async_export_bundle_returns_the_json_object():
    sync, rec = make_client(json_handler(_BUNDLE))
    client = _async_from_sync(sync)

    got = asyncio.run(client.assets.export_bundle("ast-1"))

    assert got == _BUNDLE
    assert rec.last.url.path == f"{_A}/ast-1/export"


def test_assets_wraps_no_asset_grant_operation():
    client, _ = make_client(json_handler({}))
    exposed = {name for name in dir(client.assets) if not name.startswith("_")}

    assert exposed == {"copy", "export_bundle", "import_bundle", "restore"}


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
