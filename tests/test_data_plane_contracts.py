"""Request contracts of the infrastructure, intelligence, orchestration,
query, queue, operations, membership and organization namespaces.

Each request case pins the exact query a keyword argument produces, that an
omitted argument is not sent, and that an argument the route does not take is
refused before anything is sent. The response shapes are in
tests/test_data_plane_response_shapes.py.
"""

from __future__ import annotations

import json

import pytest

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
