"""Infrastructure services, stores, nodepools and databases.

Pins what the wrapper matrix does not: bodiless verbs, the optional backup body,
the ``204`` activity record, path-segment encoding and typed returns. Stores are
in ``tests/test_infrastructure_services_stores.py``.
"""

from __future__ import annotations

import json

import httpx
import pytest

from perceivo_client.generated.models import (
    BackupListResponse,
    BackupRead,
    CapacityRead,
    ClusterServiceStatusList,
    CollectionDataPage,
    CollectionWriteResult,
    DedicatedDatabaseRead,
    DedicatedDatabaseStartAccepted,
    ManagedServiceListResponse,
    ManagedServiceRead,
    McpConfigDocument,
    NodepoolDetail,
)
from tests._infrastructure_fixtures import (
    _I,
    _S,
    _V,
    _routed,
)
from tests.conftest import json_handler, make_client

# --- typed returns -------------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.infrastructure.get_capacity(), CapacityRead),
        (lambda c: c.infrastructure.list_cluster_services(), ClusterServiceStatusList),
        (lambda c: c.infrastructure.get_mcp_config(), McpConfigDocument),
        (lambda c: c.infrastructure.get_nodepool("np1"), NodepoolDetail),
        (lambda c: c.infrastructure.scale_nodepool("np1", {}), NodepoolDetail),
        (lambda c: c.infrastructure.list_managed_services(), ManagedServiceListResponse),
        (lambda c: c.infrastructure.get_managed_service("postgres"), ManagedServiceRead),
        (lambda c: c.infrastructure.update_managed_service("redis", {}), ManagedServiceRead),
        (lambda c: c.infrastructure.start_managed_service("redis"), ManagedServiceRead),
        (lambda c: c.infrastructure.stop_managed_service("redis"), ManagedServiceRead),
        (lambda c: c.infrastructure.list_managed_service_backups("redis"), BackupListResponse),
        (lambda c: c.infrastructure.get_managed_service_backup("redis", "b1"), BackupRead),
        (lambda c: c.infrastructure.create_managed_service_backup("redis"), BackupRead),
        (lambda c: c.infrastructure.get_database("db1"), DedicatedDatabaseRead),
        (lambda c: c.infrastructure.start_database("db1"), DedicatedDatabaseStartAccepted),
        (lambda c: c.infrastructure.list_search_index_documents("i1"), CollectionDataPage),
        (lambda c: c.infrastructure.add_search_index_document("i1", {}), CollectionWriteResult),
        (
            lambda c: c.infrastructure.delete_search_index_document("i1", "d1"),
            CollectionWriteResult,
        ),
        (lambda c: c.infrastructure.import_search_index("i1", b"x"), CollectionWriteResult),
        (lambda c: c.infrastructure.list_vector_store_entities("c1"), CollectionDataPage),
        (lambda c: c.infrastructure.add_vector_store_entities("c1", {}), CollectionWriteResult),
        (
            lambda c: c.infrastructure.delete_vector_store_entity("c1", "e1"),
            CollectionWriteResult,
        ),
        (
            lambda c: c.infrastructure.import_vector_store_collection("c1", b"x"),
            CollectionWriteResult,
        ),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x", "service": "redis", "status": "running"}))

    assert isinstance(call(client), model)


def test_managed_service_list_items_are_typed():
    page = {"items": [{"service": "postgres", "status": "running"}], "total": 1}
    client, rec = make_client(json_handler(page))

    got = client.infrastructure.list_managed_services()

    assert isinstance(got.items[0], ManagedServiceRead)
    assert got.items[0].service == "postgres"
    assert dict(rec.last.url.params) == {}


# --- bodiless verbs, the optional backup body and the 204 ------------------------


@pytest.mark.parametrize(
    "call,path",
    [
        (lambda c: c.infrastructure.start_managed_service("redis"), f"{_I}/managed/redis/start"),
        (lambda c: c.infrastructure.stop_managed_service("redis"), f"{_I}/managed/redis/stop"),
        (lambda c: c.infrastructure.start_database("db1"), f"{_I}/databases/db1/start"),
        (
            lambda c: c.infrastructure.record_database_activity("db1"),
            f"{_I}/databases/db1/activity",
        ),
        (
            lambda c: c.infrastructure.create_managed_service_backup("redis"),
            f"{_I}/managed/redis/backups",
        ),
        (lambda c: c.infrastructure.export_search_index("i1"), f"{_S}/i1/export"),
        (lambda c: c.infrastructure.export_vector_store_collection("c1"), f"{_V}/c1/export"),
    ],
)
def test_bodiless_posts_send_no_body(call, path):
    client, rec = make_client(json_handler({"id": "x", "service": "redis", "status": "x"}))

    call(client)

    assert rec.last.method == "POST"
    assert rec.last.url.path == path
    assert rec.last.content == b""


def test_a_backup_type_is_sent_when_given():
    client, rec = make_client(json_handler({"id": "b1", "service": "redis"}, status=202))

    got = client.infrastructure.create_managed_service_backup("redis", {"backup_type": "manual"})

    assert got.id == "b1"
    assert json.loads(rec.last.content) == {"backup_type": "manual"}


def test_record_database_activity_returns_none_on_no_content():
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert client.infrastructure.record_database_activity("db1") is None
    assert rec.last.method == "POST"


def test_scale_nodepool_forwards_the_target():
    client, rec = make_client(json_handler({"name": "np1", "status": "scaling"}))

    got = client.infrastructure.scale_nodepool("np1", {"target_nodes": 3})

    assert got.status == "scaling"
    assert json.loads(rec.last.content) == {"target_nodes": 3}


def test_update_service_and_service_status_share_the_path_not_the_verb():
    client, rec = make_client(json_handler({"service": "redis", "status": "running"}))

    client.infrastructure.update_cluster_service("redis", {"memory_mb": 512})
    client.infrastructure.get_cluster_service("redis")

    assert [(r.method, r.url.path) for r in rec.requests] == [
        ("PATCH", f"{_I}/cluster/redis"),
        ("GET", f"{_I}/cluster/redis"),
    ]


def test_mcp_config_and_mcp_update_config_share_the_path_not_the_verb():
    doc = {"auto_shutdown": True, "idle_timeout_minutes": 30}
    client, rec = make_client(json_handler(doc))

    client.infrastructure.replace_mcp_config(doc)
    got = client.infrastructure.get_mcp_config()

    assert got.idle_timeout_minutes == 30
    assert [r.method for r in rec.requests] == ["PUT", "GET"]
    assert {r.url.path for r in rec.requests} == {f"{_I}/cluster/mcp/config"}


def test_start_database_id_round_trips_into_the_status_poll():
    routes = {
        ("POST", f"{_I}/databases/db1/start"): (
            202,
            {"database_id": "db1", "status": "accepted"},
        ),
        ("GET", f"{_I}/databases/db1"): (
            200,
            {"id": "db1", "organization_id": "org-1", "status": "starting"},
        ),
    }
    client, rec = make_client(_routed(routes))

    accepted = client.infrastructure.start_database("db1")
    status = client.infrastructure.get_database(accepted.database_id)

    assert status.status == "starting"
    assert [r.method for r in rec.requests] == ["POST", "GET"]


# --- one path segment per name and key ---------------------------------------------


@pytest.mark.parametrize(
    "call,raw_path",
    [
        (
            lambda c: c.infrastructure.delete_search_index_document("i1", "a/b?c#d"),
            b"/v1/infrastructure/search-index/indices/i1/documents/a%2Fb%3Fc%23d",
        ),
        (
            lambda c: c.infrastructure.delete_vector_store_entity("c 1", "50%"),
            b"/v1/infrastructure/vector-store/collections/c%201/entities/50%25",
        ),
        (
            lambda c: c.infrastructure.get_managed_service_backup("redis", "b/1"),
            b"/v1/infrastructure/managed/redis/backups/b%2F1",
        ),
    ],
)
def test_names_and_keys_are_encoded_into_one_segment(call, raw_path):
    client, rec = make_client(json_handler({"id": "x", "service": "redis"}))

    call(client)

    assert rec.last.url.raw_path == raw_path


@pytest.mark.parametrize("key", ["..", ".", ""])
@pytest.mark.parametrize(
    "delete",
    [
        lambda c, k: c.infrastructure.delete_search_index_document("i1", k),
        lambda c, k: c.infrastructure.delete_vector_store_entity("c1", k),
    ],
)
def test_a_dot_segment_key_is_refused_before_it_can_address_the_container(delete, key):
    """Warning: ``httpx`` resolves ``.../documents/..`` to the index itself."""
    client, rec = make_client(json_handler({}))

    with pytest.raises(ValueError, match="one path segment"):
        delete(client, key)

    assert rec.requests == []


def test_the_dot_segment_hazard_is_real_for_an_unencoded_path():
    """Positive control: without the refusal, ``..`` would reach the container."""
    request = httpx.Request("DELETE", f"https://api.example{_S}/i1/documents/..")

    assert request.url.path == f"{_S}/i1"
