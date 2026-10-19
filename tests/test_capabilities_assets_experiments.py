"""Capabilities, assets and experiments: request shapes the wrapper matrix does not pin.

Listings, typed returns, async parity, updates and execution graphs are in
``tests/test_capabilities_assets_experiments_listings.py``.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client.generated.models import (
    AssetRead,
    CapabilityEvaluationConfigRead,
    CapabilityRead,
    CapabilityTrafficPlanRead,
    ExperimentDeleteResponse,
    ExperimentRead,
    ExperimentRunResponse,
    ExperimentSession,
    LifecycleOperationResponse,
)
from tests._capabilities_fixtures import (
    _A,
    _BUNDLE,
    _E,
    _EXPERIMENT_ROUTES,
    _K,
    _routed,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

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
