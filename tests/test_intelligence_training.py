"""Intelligence training and data.

``client.intelligence`` gains training configurations and groups, feature
views, materialization, ingest, PII and prediction-logging configuration,
service-secret bindings and ingest triggers. Method and path for every row are
pinned by ``test_wrapper_matrix``; this module pins what that matrix cannot see:
the configuration -> group member -> group run id chain, the trigger ->
execution chain, the once-only ``http_token``, the service-secret surface
carrying no secret value, ``PUT`` verbs, untyped ``200`` and ``204`` bodies,
query spellings, the bare arrays ``paginate_pages`` does not walk, typed returns
and async parity.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.generated.models import (
    FeatureViewRead,
    IngestResponse,
    IngestTriggerRead,
    IntelligenceMaterializeAccepted,
    IntelligenceTriggerExecutionRead,
    PiiConfig,
    PredictionLoggingConfig,
    ServiceSecretRead,
    TrainingConfigurationRead,
    TrainingGroupDetail,
    TrainingGroupMemberRead,
    TrainingGroupRead,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_I = "/v1/intelligence"
_CONFIG = {"id": "cfg-1", "intelligence_id": "i1", "name": "baseline", "training_mode": "single"}
_GROUP = {"id": "grp-1", "intelligence_id": "i1", "name": "nightly", "members": []}
_MEMBER = {
    "id": "mem-1",
    "group_id": "grp-1",
    "training_configuration_id": "cfg-1",
    "family_id": "fam-1",
}
_TRIGGER = {
    "id": "trg-1",
    "intelligence_id": "i1",
    "trigger_type": "ingest",
    "http_enabled": True,
    "http_token": "tok-once",
}
_EXECUTION = {
    "id": "exe-1",
    "trigger_id": "trg-1",
    "idempotency_key": "k1",
    "source": "http",
    "status": "completed",
    "created_at": "2026-10-03T00:00:00Z",
}


def _routed(routes: dict[tuple[str, str], tuple[int, object]]):
    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    return handler


_TRAINING_ROUTES = {
    ("POST", f"{_I}/i1/training-configurations"): (201, _CONFIG),
    ("POST", f"{_I}/i1/training-groups"): (201, _GROUP),
    ("PUT", f"{_I}/i1/training-groups/grp-1/members/mem-1"): (201, _MEMBER),
    ("POST", f"{_I}/i1/training-groups/grp-1/run"): (200, {"status": "queued"}),
}


# --- chains --------------------------------------------------------------------


def test_configuration_and_group_ids_round_trip_into_member_and_run():
    client, rec = make_client(_routed(_TRAINING_ROUTES))

    config = client.intelligence.create_training_configuration("i1", {"name": "baseline"})
    group = client.intelligence.create_training_group("i1", {"name": "nightly"})
    member = client.intelligence.replace_training_group_member(
        "i1", group.id, "mem-1", {"training_configuration_id": config.id}
    )
    run = client.intelligence.run_training_group("i1", group.id)

    assert isinstance(config, TrainingConfigurationRead)
    assert isinstance(group, TrainingGroupDetail)
    assert isinstance(member, TrainingGroupMemberRead)
    assert member.training_configuration_id == config.id
    assert json.loads(rec.requests[2].content) == {"training_configuration_id": "cfg-1"}
    assert run == {"status": "queued"}
    assert rec.last.content == b""


def test_trigger_id_round_trips_into_get_trigger_execution():
    client, rec = make_client(
        _routed(
            {
                ("POST", f"{_I}/i1/triggers"): (201, _TRIGGER),
                ("GET", f"{_I}/i1/triggers/trg-1/executions/exe-1"): (200, _EXECUTION),
            }
        )
    )

    trigger = client.intelligence.create_trigger("i1", {"trigger_type": "ingest"})
    execution = client.intelligence.get_trigger_execution("i1", trigger.id, "exe-1")

    assert isinstance(execution, IntelligenceTriggerExecutionRead)
    assert execution.trigger_id == trigger.id
    assert rec.last.url.path == f"{_I}/i1/triggers/trg-1/executions/exe-1"


def test_async_training_chain_awaits_each_step():
    sync, rec = make_client(_routed(_TRAINING_ROUTES))
    client = _async_from_sync(sync)

    async def drive():
        group = await client.intelligence.create_training_group("i1", {"name": "nightly"})
        await client.intelligence.replace_training_group_member("i1", group.id, "mem-1", {})
        return await client.intelligence.run_training_group("i1", group.id)

    run = asyncio.run(drive())

    assert run == {"status": "queued"}
    assert [r.method for r in rec.requests] == ["POST", "PUT", "POST"]


# --- the http_token and the service-secret surface ------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.intelligence.create_trigger("i1", {"http_enabled": True}),
        lambda c: c.intelligence.update_trigger("i1", "trg-1", {"http_enabled": True}),
    ],
)
def test_trigger_writes_surface_the_once_only_http_token(call):
    client, _ = make_client(json_handler(_TRIGGER))

    trigger = call(client)

    assert isinstance(trigger, IngestTriggerRead)
    assert trigger.http_token == "tok-once"


def test_service_secret_read_model_declares_no_value_field():
    fields = set(ServiceSecretRead.model_fields)

    assert fields == {"alias", "id", "intelligence_id", "secret_id", "secret_name", "service_type"}


def test_attach_service_secret_sends_only_the_secret_id():
    body = {"service_type": "training", "secret_id": "sec-1", "alias": "vendor_key"}
    client, rec = make_client(json_handler({**body, "id": "b1"}, status=201))

    got = client.intelligence.attach_service_secret("i1", body)

    assert isinstance(got, ServiceSecretRead)
    assert json.loads(rec.last.content) == body
    assert rec.last.url.path == f"{_I}/i1/service-secrets"


def test_detach_service_secret_addresses_type_and_alias():
    client, rec = make_client(lambda _r: httpx.Response(204))

    got = client.intelligence.detach_service_secret("i1", "training", "vendor_key")

    assert got is None
    assert rec.last.method == "DELETE"
    assert rec.last.url.path == f"{_I}/i1/service-secrets/training/vendor_key"


# --- verbs and bodies ------------------------------------------------------------


@pytest.mark.parametrize(
    "call,path,model",
    [
        (lambda c: c.intelligence.replace_pii_config("i1", {"x": 1}), "/i1/config/pii", PiiConfig),
        (
            lambda c: c.intelligence.replace_prediction_logging_config("i1", {"x": 1}),
            "/i1/config/prediction-logging",
            PredictionLoggingConfig,
        ),
    ],
)
def test_configuration_replacements_use_put(call, path, model):
    client, rec = make_client(json_handler({}))

    got = call(client)

    assert isinstance(got, model)
    assert rec.last.method == "PUT"
    assert rec.last.url.path == f"{_I}{path}"
    assert json.loads(rec.last.content) == {"x": 1}


def test_materialize_forwards_its_request_and_returns_the_acceptance():
    body = {"scope": "full", "feature_views": ["fv1"]}
    client, rec = make_client(json_handler({"status": "accepted", "operation_id": "op-1"}))

    got = client.intelligence.materialize("i1", body)

    assert isinstance(got, IntelligenceMaterializeAccepted)
    assert rec.last.url.path == f"{_I}/i1/materialize"
    assert json.loads(rec.last.content) == body


def test_ingest_posts_to_execute_ingest():
    client, rec = make_client(json_handler({"status": "ok", "records_loaded": 3}))

    got = client.intelligence.ingest("i1", {"config": {}})

    assert isinstance(got, IngestResponse)
    assert rec.last.method == "POST"
    assert rec.last.url.path == f"{_I}/i1/execute/ingest"
    assert json.loads(rec.last.content) == {"config": {}}


# --- query parameters and pagination ------------------------------------------


@pytest.mark.parametrize(
    "call,expected",
    [
        (
            lambda c: c.intelligence.list_training_configurations("i1", family_id="fam-1"),
            {"family_id": "fam-1"},
        ),
        (
            lambda c: c.intelligence.list_training_groups("i1", include_members=True),
            {"include_members": "true"},
        ),
        (lambda c: c.intelligence.sample_feature_view("i1", "fv1", limit=5), {"limit": "5"}),
    ],
)
def test_declared_query_parameters_use_the_contract_spelling(call, expected):
    client, rec = make_client(json_handler([]))

    call(client)

    assert dict(rec.last.url.params) == expected


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.intelligence.list_training_configurations("i1"),
        lambda c: c.intelligence.list_training_groups("i1"),
        lambda c: c.intelligence.sample_feature_view("i1", "fv1"),
        lambda c: c.intelligence.list_feature_views("i1"),
        lambda c: c.intelligence.list_service_secrets("i1"),
        lambda c: c.intelligence.list_triggers("i1"),
    ],
)
def test_unfiltered_reads_send_no_query(call):
    client, rec = make_client(json_handler([]))

    call(client)

    assert dict(rec.last.url.params) == {}


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.intelligence.list_training_configurations("i1"), TrainingConfigurationRead),
        (lambda c: c.intelligence.list_training_groups("i1"), TrainingGroupRead),
        (lambda c: c.intelligence.list_feature_views("i1"), FeatureViewRead),
        (lambda c: c.intelligence.list_service_secrets("i1"), ServiceSecretRead),
        (lambda c: c.intelligence.list_triggers("i1"), IngestTriggerRead),
    ],
)
def test_bare_array_lists_are_typed(call, model):
    client, _ = make_client(json_handler([{"id": "a"}, {"id": "b"}]))

    got = call(client)

    assert len(got) == 2
    assert all(isinstance(item, model) for item in got)


def test_paginate_pages_refuses_a_bare_array_list():
    client, rec = make_client(json_handler([{"id": "a"}]))
    walker = paginate_pages(lambda **kw: client.intelligence.list_predictions("i1", **kw))

    with pytest.raises(ValueError):
        next(walker)
    assert rec.last.url.path == f"{_I}/i1/inference/predictions"


# --- typed returns and untyped bodies -------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (
            lambda c: c.intelligence.get_training_configuration("i1", "c1"),
            TrainingConfigurationRead,
        ),
        (
            lambda c: c.intelligence.update_training_configuration("i1", "c1", {}),
            TrainingConfigurationRead,
        ),
        (lambda c: c.intelligence.get_training_group("i1", "g1"), TrainingGroupDetail),
        (lambda c: c.intelligence.update_training_group("i1", "g1", {}), TrainingGroupDetail),
        (lambda c: c.intelligence.get_feature_view("i1", "fv1"), FeatureViewRead),
        (lambda c: c.intelligence.get_pii_config("i1"), PiiConfig),
        (lambda c: c.intelligence.get_prediction_logging_config("i1"), PredictionLoggingConfig),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x"}))

    assert isinstance(call(client), model)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.intelligence.delete_training_configuration("i1", "c1"),
        lambda c: c.intelligence.delete_training_group("i1", "g1"),
        lambda c: c.intelligence.remove_training_group_member("i1", "g1", "m1"),
    ],
)
def test_untyped_deletes_pass_the_body_through(call):
    client, rec = make_client(json_handler({"deleted": True}))

    assert call(client) == {"deleted": True}
    assert rec.last.method == "DELETE"


def test_delete_trigger_returns_none_on_no_content():
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert client.intelligence.delete_trigger("i1", "trg-1") is None
    assert rec.last.url.path == f"{_I}/i1/triggers/trg-1"


def test_sample_feature_passes_the_records_through():
    client, rec = make_client(json_handler([{"f": 1}, {"f": 2}]))

    got = client.intelligence.sample_feature_view("i1", "fv1", limit=2)

    assert got == [{"f": 1}, {"f": 2}]
    assert rec.last.url.path == f"{_I}/i1/features/fv1/sample"


# --- async parity ------------------------------------------------------------------


def test_async_materialize_awaits_and_hits_the_exact_path():
    sync, rec = make_client(json_handler({"status": "accepted"}))
    client = _async_from_sync(sync)

    got = asyncio.run(client.intelligence.materialize("i1", {"scope": "full"}))

    assert isinstance(got, IntelligenceMaterializeAccepted)
    assert rec.last.url.path == f"{_I}/i1/materialize"


def test_async_detach_service_secret_returns_none():
    sync, rec = make_client(lambda _r: httpx.Response(204))
    client = _async_from_sync(sync)

    got = asyncio.run(client.intelligence.detach_service_secret("i1", "inference", "k"))

    assert got is None
    assert rec.last.url.path == f"{_I}/i1/service-secrets/inference/k"
