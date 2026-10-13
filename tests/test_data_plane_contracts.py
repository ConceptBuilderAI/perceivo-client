"""Request and response contracts of the infrastructure, intelligence, orchestration,
query, queue, operations, membership and organization namespaces.

Each response fixture is the body the platform actually sends, which in several
places is not the model the published contract names. Each request case pins the
exact query a keyword argument produces, that an omitted argument is not sent,
and that an argument the route does not take is refused before anything is sent.
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

# --- explicit query parameters ----------------------------------------------------

# (call, path, exact query). Every argument is given, so every name is pinned.
_QUERY_CASES = [
    (
        lambda c: c.intelligence.list(page=2, page_size=50),
        f"{_B}/intelligence",
        {"page": "2", "page_size": "50"},
    ),
    (
        lambda c: c.intelligence.list_drift_baselines(
            "i1", include_inactive=True, model_family_id="f1"
        ),
        f"{_B}/intelligence/i1/drift/baselines",
        {"include_inactive": "true", "model_family_id": "f1"},
    ),
    (
        lambda c: c.intelligence.list_inference_requests("i1", status="done", page=2, page_size=10),
        f"{_B}/intelligence/i1/inference/requests",
        {"status": "done", "page": "2", "page_size": "10"},
    ),
    (
        lambda c: c.intelligence.list_predictions(
            "i1",
            model_id="m1",
            served_by="canary",
            start_date="s",
            end_date="e",
            page=1,
            page_size=5,
        ),
        f"{_B}/intelligence/i1/inference/predictions",
        {
            "model_id": "m1",
            "served_by": "canary",
            "start_date": "s",
            "end_date": "e",
            "page": "1",
            "page_size": "5",
        },
    ),
    (
        lambda c: c.intelligence.list_prediction_outcomes("i1", "p1", prediction_time="t"),
        f"{_B}/intelligence/i1/inference/predictions/p1/outcomes",
        {"prediction_time": "t"},
    ),
    (
        lambda c: c.intelligence.list_model_families("i1", active_only=True),
        f"{_B}/intelligence/i1/model-families",
        {"active_only": "true"},
    ),
    (
        lambda c: c.intelligence.list_training_configurations("i1", family_id="f1"),
        f"{_B}/intelligence/i1/training-configurations",
        {"family_id": "f1"},
    ),
    (
        lambda c: c.intelligence.list_training_groups("i1", include_members=False),
        f"{_B}/intelligence/i1/training-groups",
        {"include_members": "false"},
    ),
    (
        lambda c: c.intelligence.sample_feature_view("i1", "customers", limit=20),
        f"{_B}/intelligence/i1/features/customers/sample",
        {"limit": "20"},
    ),
    (
        lambda c: c.orchestrations.list(page=3, page_size=100),
        f"{_B}/orchestrations",
        {"page": "3", "page_size": "100"},
    ),
    (
        lambda c: c.orchestrations.get_compatibility("o1", "cap1"),
        f"{_B}/orchestrations/o1/compatibility",
        {"capability_id": "cap1"},
    ),
    (
        lambda c: c.infrastructure.list_search_index_documents("idx", page=2, page_size=20),
        f"{_B}/infrastructure/search-index/indices/idx/documents",
        {"page": "2", "page_size": "20"},
    ),
    (
        lambda c: c.infrastructure.list_vector_store_entities("col", page=2, page_size=20),
        f"{_B}/infrastructure/vector-store/collections/col/entities",
        {"page": "2", "page_size": "20"},
    ),
    (
        lambda c: c.invitations.list(status="pending"),
        f"{_B}/invitations",
        {"status": "pending"},
    ),
    (
        lambda c: c.members.list(include_removed=True),
        f"{_B}/members",
        {"include_removed": "true"},
    ),
    (
        lambda c: c.operations.list(status="running", cursor="cur", page_size=20),
        f"{_B}/operations",
        {"filter[status]": "running", "cursor": "cur", "page_size": "20"},
    ),
    (
        lambda c: c.query.events(
            event_type="asset.created", start="a", end="b", page=1, page_size=50, sort="-x"
        ),
        f"{_B}/events",
        {
            "filter[event_type]": "asset.created",
            "from": "a",
            "to": "b",
            "page": "1",
            "page_size": "50",
            "sort": "-x",
        },
    ),
    (
        lambda c: c.query.logs(
            "organization",
            channel="notification",
            start="a",
            end="b",
            q="timeout",
            domain="billing",
            severity="high",
            limit=10,
            offset=5,
        ),
        f"{_B}/logs",
        {
            "scope": "organization",
            "channel": "notification",
            "from": "a",
            "to": "b",
            "q": "timeout",
            "domain": "billing",
            "severity": "high",
            "limit": "10",
            "offset": "5",
        },
    ),
    (
        lambda c: c.query.logs(
            "intelligence",
            scope_id="i1",
            channel="extension",
            version="1.0.0",
            service_type="training",
            level="ERROR",
        ),
        f"{_B}/logs",
        {
            "scope": "intelligence",
            "scope_id": "i1",
            "channel": "extension",
            "version": "1.0.0",
            "service_type": "training",
            "level": "ERROR",
        },
    ),
    (
        lambda c: c.query.logs("run", scope_id="r1", order="oldest_first"),
        f"{_B}/logs",
        {"scope": "run", "scope_id": "r1", "order": "oldest_first"},
    ),
    (
        lambda c: c.query.metrics(
            "intelligence",
            "i1",
            series="latency_p95",
            window="24h",
            granularity="1h",
            model_id="m1",
            version="1.0.0",
        ),
        f"{_B}/metrics",
        {
            "subject": "intelligence",
            "subject_id": "i1",
            "series": "latency_p95",
            "window": "24h",
            "granularity": "1h",
            "model_id": "m1",
            "version": "1.0.0",
        },
    ),
    (
        lambda c: c.query.search(
            q="churn",
            asset_type="intelligence",
            category="ml",
            status="active",
            protection="platform",
            deleted=False,
            sort="name",
            page=2,
            page_size=100,
        ),
        f"{_B}/search",
        {
            "q": "churn",
            "type": "intelligence",
            "category": "ml",
            "status": "active",
            "protection": "platform",
            "deleted": "false",
            "sort": "name",
            "page": "2",
            "page_size": "100",
        },
    ),
    (
        lambda c: c.query.logs(
            "intelligence",
            scope_id="i1",
            channel="error",
            start="a",
            end="b",
            q="x",
            version="1.0.0",
            service_type="inference",
            limit=5,
        ),
        f"{_B}/logs",
        {
            "scope": "intelligence",
            "scope_id": "i1",
            "channel": "error",
            "from": "a",
            "to": "b",
            "q": "x",
            "version": "1.0.0",
            "service_type": "inference",
            "limit": "5",
        },
    ),
]


@pytest.mark.parametrize(("call", "path", "query"), _QUERY_CASES)
def test_each_keyword_argument_is_sent_as_its_query_parameter(call, path, query):
    client, rec = make_client(json_handler({}))
    call(client)
    assert rec.last.method == "GET"
    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == query


# (call, path): the same methods with every optional argument omitted.
_BARE_CASES = [
    (lambda c: c.intelligence.list(), f"{_B}/intelligence"),
    (lambda c: c.intelligence.list_drift_baselines("i1"), f"{_B}/intelligence/i1/drift/baselines"),
    (
        lambda c: c.intelligence.list_inference_requests("i1"),
        f"{_B}/intelligence/i1/inference/requests",
    ),
    (
        lambda c: c.intelligence.list_predictions("i1"),
        f"{_B}/intelligence/i1/inference/predictions",
    ),
    (lambda c: c.intelligence.list_models("i1"), f"{_B}/intelligence/i1/models"),
    (lambda c: c.orchestrations.list(), f"{_B}/orchestrations"),
    (lambda c: c.infrastructure.get(), f"{_B}/infrastructure"),
    (lambda c: c.infrastructure.list_search_indices(), f"{_B}/infrastructure/search-index/indices"),
    (lambda c: c.infrastructure.list_cache_keys(), f"{_B}/infrastructure/cache/keys"),
    (lambda c: c.infrastructure.list_mcp_tools(), f"{_B}/infrastructure/cluster/mcp/tools"),
    (lambda c: c.infrastructure.list_nodepools(), f"{_B}/infrastructure/cluster/nodepools"),
    (lambda c: c.invitations.list(), f"{_B}/invitations"),
    (lambda c: c.members.list(), f"{_B}/members"),
    (lambda c: c.operations.list(), f"{_B}/operations"),
    (lambda c: c.grants.list(), f"{_B}/grants"),
    (lambda c: c.query.events(), f"{_B}/events"),
    (lambda c: c.query.search(), f"{_B}/search"),
]


@pytest.mark.parametrize(("call", "path"), _BARE_CASES)
def test_an_omitted_argument_is_not_sent(call, path):
    client, rec = make_client(json_handler({}))
    call(client)
    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == {}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.intelligence.list(sort_by="name"),
        lambda c: c.intelligence.list_models("i1", status="active"),
        lambda c: c.intelligence.list_predictions("i1", sort_order="asc"),
        lambda c: c.orchestrations.list(sort_order="asc"),
        lambda c: c.orchestrations.get_compatibility("o1", "cap1", extra="x"),
        lambda c: c.infrastructure.get(organization_id="o"),
        lambda c: c.infrastructure.list_cache_keys(pattern="a*"),
        lambda c: c.grants.list(principal="me"),
        lambda c: c.query.logs("organization", organization_id="o"),
        lambda c: c.queue.list("cap1", kind="input"),
    ],
)
def test_an_argument_the_route_does_not_take_is_refused_before_sending(call):
    client, rec = make_client(json_handler({}))
    with pytest.raises(TypeError):
        call(client)
    assert rec.requests == []


# --- request bodies ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("call", "path"),
    [
        (
            lambda c: c.infrastructure.start_cluster_service("milvus"),
            f"{_B}/infrastructure/cluster/milvus/start",
        ),
        (
            lambda c: c.infrastructure.stop_cluster_service("milvus"),
            f"{_B}/infrastructure/cluster/milvus/stop",
        ),
        (
            lambda c: c.intelligence.retire_model("i1", "m1"),
            f"{_B}/intelligence/i1/models/m1/retire",
        ),
    ],
)
def test_an_operation_that_takes_no_body_is_sent_none(call, path):
    client, rec = make_client(json_handler({}))
    call(client)
    assert rec.last.method == "POST"
    assert rec.last.url.path == path
    assert rec.last.content == b""
    assert "content-type" not in rec.last.headers


def test_predict_sends_the_features_envelope():
    client, rec = make_client(json_handler({"prediction": 1}))
    client.intelligence.predict("i1", {"features": {"x": 1}})
    assert json.loads(rec.last.content) == {"features": {"x": 1}}


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


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (
            201,
            {"id": "b1", "orchestration_id": "o1", "node_id": "n1", "alias": "k", "secret_id": "s"},
        ),
        (200, {"node_id": "n1", "alias": "k", "secret_id": "s"}),
    ],
)
def test_replace_node_secret_binding_returns_the_body_for_both_answers(status, body):
    client, rec = make_client(json_handler(body, status=status))

    got = client.orchestrations.replace_node_secret_binding("o1", "n1", "k", {"secret_id": "s"})

    assert got == body
    assert rec.last.method == "PUT"
    assert rec.last.url.path == f"{_B}/orchestrations/o1/nodes/n1/secrets/k"


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
