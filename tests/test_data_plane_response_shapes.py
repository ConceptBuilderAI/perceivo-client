"""Response contracts of the infrastructure, intelligence, orchestration, query,
queue, operations, membership and organization namespaces.

Each response fixture is the body the platform actually sends, which in several
places is not the model the published contract names. The request contracts are
in tests/test_data_plane_contracts.py.
"""

from __future__ import annotations

import json

import httpx
import pytest

from perceivo_client.generated.models import (
    BulkCancelResponse,
    CapabilityQueuePurgeResult,
    FeatureViewRead,
    IntelligenceUpdateResult,
    OrchestrationUpdateResult,
)
from tests.conftest import json_handler, make_client

_B = "/v1"


# --- response shapes the platform actually sends -------------------------------------

_MILVUS_RECORD = {"milvus_status": "running", "milvus_size": "basic", "milvus_host": "h"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.infrastructure.get_cluster_service("milvus"),
        lambda c: c.infrastructure.update_cluster_service("milvus", {"size": "basic"}),
    ],
)
def test_a_cluster_service_record_is_returned_with_its_prefixed_keys(call):
    client, _ = make_client(json_handler(_MILVUS_RECORD))
    got = call(client)
    assert got == _MILVUS_RECORD
    assert got["milvus_status"] == "running"


@pytest.mark.parametrize(
    ("verb", "body"),
    [
        (
            "start_cluster_service",
            {"redis_status": "running", "redis_host": "h", "redis_port": 6379},
        ),
        ("stop_cluster_service", {"redis_status": "stopped"}),
    ],
)
def test_a_cluster_lifecycle_answer_is_returned_as_sent(verb, body):
    client, _ = make_client(json_handler(body))
    assert getattr(client.infrastructure, verb)("redis") == body


def test_feature_views_are_read_from_their_envelope():
    body = {"feature_views": [{"name": "customers", "entities": ["id"]}, {"name": "orders"}]}
    client, _ = make_client(json_handler(body))

    got = client.intelligence.list_feature_views("i1")

    assert [type(view) for view in got] == [FeatureViewRead, FeatureViewRead]
    assert [view.name for view in got] == ["customers", "orders"]
    assert got[0].entities == ["id"]


def test_feature_views_of_a_starting_feature_service_are_an_empty_list():
    client, _ = make_client(json_handler({"feature_views": []}))
    assert client.intelligence.list_feature_views("i1") == []


def test_a_feature_view_sample_is_returned_as_sent():
    body = {"feature_view": "customers", "count": 1, "results": [{"id": 1}], "metadata": {}}
    client, _ = make_client(json_handler(body))
    assert client.intelligence.sample_feature_view("i1", "customers", limit=1) == body


@pytest.mark.parametrize(
    ("scope", "body"),
    [
        (
            "run",
            {
                "workload_id": "w1",
                "entries": [{"timestamp": "1", "line": "a"}],
                "count": 1,
                "limit": 100,
                "namespace_resolved": True,
            },
        ),
        (
            "orchestration",
            {"status": "success", "data": {"resultType": "streams", "result": [], "stats": {}}},
        ),
        ("organization", {"items": [{"line": "a"}], "total": 1, "pagination": {"count": 1}}),
    ],
)
def test_logs_returns_each_scope_body_unchanged(scope, body):
    client, _ = make_client(json_handler(body))
    assert client.query.logs(scope, scope_id="x1" if scope != "organization" else None) == body


#: What the gateway answers, as ``200``, when the log read behind it fails or
#: times out: an items body with no ``pagination`` for the intelligence and
#: organization channels, and an empty Loki body for every other scope.
_EMPTY_ITEMS = {"items": [], "total": 0}
_EMPTY_LOKI = {
    "status": "success",
    "data": {
        "resultType": "streams",
        "result": [],
        "stats": {"summary": {"totalEntriesReturned": 0}},
    },
}


@pytest.mark.parametrize(
    ("call", "body"),
    [
        (lambda c: c.query.logs("intelligence", scope_id="i1"), _EMPTY_ITEMS),
        (lambda c: c.query.logs("organization", channel="notification"), _EMPTY_ITEMS),
        (lambda c: c.query.logs("capability", scope_id="c1", channel="system"), _EMPTY_LOKI),
        (lambda c: c.query.logs("orchestration", scope_id="o1"), _EMPTY_LOKI),
        (lambda c: c.query.logs("intelligence", scope_id="i1", channel="error"), _EMPTY_ITEMS),
        (lambda c: c.query.logs("intelligence", scope_id="i1", channel="extension"), _EMPTY_ITEMS),
    ],
    ids=["intelligence", "notification", "capability", "orchestration", "errors", "extension"],
)
def test_a_failed_log_read_returns_the_empty_body_unchanged(call, body):
    client, _ = make_client(json_handler(body))
    assert call(client) == body


def test_update_returns_the_update_result_with_version_created():
    body = {"id": "o2", "name": "n", "organization_id": "org", "version_created": True}
    client, _ = make_client(json_handler(body))

    orchestration = client.orchestrations.update("o1", {"name": "n"})
    client_i, _ = make_client(json_handler(body))
    intelligence = client_i.intelligence.update("i1", {"name": "n"})

    assert isinstance(orchestration, OrchestrationUpdateResult)
    assert isinstance(intelligence, IntelligenceUpdateResult)
    assert orchestration.version_created is True
    assert intelligence.id == "o2"


def test_delete_nodepool_returns_none_for_the_empty_acknowledgement():
    client, rec = make_client(json_handler({}, status=202))
    assert client.infrastructure.delete_nodepool("np1") is None
    assert rec.last.method == "DELETE"


@pytest.mark.parametrize(
    ("include_running", "body", "model"),
    [
        (False, {"cancelled": 2}, CapabilityQueuePurgeResult),
        (True, {"cancelled": 2}, BulkCancelResponse),
    ],
)
def test_queue_cancel_picks_the_model_by_include_running(include_running, body, model):
    client, rec = make_client(json_handler(body))

    got = client.queue.cancel("cap1", include_running=include_running)

    assert type(got) is model
    sent = json.loads(rec.last.content)
    assert sent == {"kind": "input", "asset_id": "cap1", "include_running": include_running}


def test_queue_sends_the_input_kind_on_every_read():
    client, rec = make_client(json_handler({}))
    client.queue.list("cap1")
    client.queue.get_summary("cap1")
    client.queue.cancel_item("item1")
    assert [dict(r.url.params)["kind"] for r in rec.requests] == ["input"] * 3


def test_a_training_group_run_is_returned_as_sent():
    body = {"message": "Started 2 training jobs with 2 runs", "job_ids": ["j1"], "run_count": 2}
    client, _ = make_client(json_handler(body))
    assert client.intelligence.run_training_group("i1", "g1") == body


def test_an_empty_answer_reads_as_none_not_as_an_error():
    client, _ = make_client(lambda _r: httpx.Response(204))
    assert client.orchestrations.delete("o1") is None
    assert client.intelligence.delete("i1") is None
