"""Infrastructure services, stores, nodepools and databases.

``client.infrastructure`` gains the cluster service list and configuration
``PATCH``, the compute quota, the managed (Azure-hosted) services and their
backups, the dedicated-database read/start/activity verbs, the MCP
configuration read, the nodepool read and scale, and the search-index and
vector-store container and record operations (create, delete, browse, load,
delete one record, export, import). Method and path for every row are pinned by
``test_wrapper_matrix``; this module pins what that matrix cannot see: the
bodiless verbs, the optional backup body, the ``204`` activity record, the
path-segment encoding that keeps a record key from addressing its container,
the multipart import and its signed-mode refusal, the browse pages that
``paginate_pages`` must refuse, the credential-free response models, typed
returns and async parity.
"""

from __future__ import annotations

import asyncio
import io
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import (
    BackupListResponse,
    BackupRead,
    CapacityRead,
    ClusterServiceStatus,
    ClusterServiceStatusList,
    CollectionDataPage,
    CollectionSummary,
    CollectionWriteResult,
    DedicatedDatabaseRead,
    DedicatedDatabaseStartAccepted,
    ManagedServiceListResponse,
    ManagedServiceRead,
    McpConfigDocument,
    NodepoolDetail,
)
from perceivo_client.signing import SigningError
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_I = "/v1/infrastructure"
_S = f"{_I}/search-index/indices"
_V = f"{_I}/vector-store/collections"
_EXPORT = b'{"id": "d1", "body": "x"}\n{"id": "d2", "body": "y"}\n'


def _routed(routes: dict[tuple[str, str], tuple[int, object]]):
    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    return handler


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
        (lambda c: c.infrastructure.create_search_index({}), CollectionSummary),
        (lambda c: c.infrastructure.delete_search_index("i1"), CollectionSummary),
        (lambda c: c.infrastructure.list_search_index_documents("i1"), CollectionDataPage),
        (lambda c: c.infrastructure.add_search_index_document("i1", {}), CollectionWriteResult),
        (
            lambda c: c.infrastructure.delete_search_index_document("i1", "d1"),
            CollectionWriteResult,
        ),
        (lambda c: c.infrastructure.import_search_index("i1", b"x"), CollectionWriteResult),
        (lambda c: c.infrastructure.create_vector_store_collection({}), CollectionSummary),
        (lambda c: c.infrastructure.delete_vector_store_collection("c1"), CollectionSummary),
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


# --- import: multipart, one part named file ----------------------------------------

_IMPORTS = [
    pytest.param(
        lambda c, data: c.infrastructure.import_search_index("i1", data),
        f"{_S}/i1/import",
        id="search_index",
    ),
    pytest.param(
        lambda c, data: c.infrastructure.import_vector_store_collection("c1", data),
        f"{_V}/c1/import",
        id="vector_store",
    ),
]


@pytest.mark.parametrize("call,path", _IMPORTS)
def test_import_posts_the_file_as_the_one_multipart_part(call, path):
    client, rec = make_client(json_handler({"inserted": 2}))

    got = call(client, _EXPORT)

    body = rec.last.content
    assert isinstance(got, CollectionWriteResult)
    assert rec.last.url.path == path
    assert rec.last.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert b'name="file"; filename="import.ndjson"' in body
    assert b"Content-Type: application/x-ndjson" in body
    assert body.count(b"Content-Disposition") == 1
    assert _EXPORT in body


@pytest.mark.parametrize("call,path", _IMPORTS)
def test_import_declares_a_content_length_for_a_file_object(call, path):
    """The import operations refuse a chunked body with 411."""
    client, rec = make_client(json_handler({}))

    call(client, io.BytesIO(_EXPORT))

    assert int(rec.last.headers["content-length"]) == len(rec.last.content)
    assert "transfer-encoding" not in rec.last.headers


@pytest.mark.parametrize("call,path", _IMPORTS)
def test_a_signing_client_refuses_the_import_instead_of_sending_it_unsigned(call, path):
    client, rec = make_client(
        json_handler({}),
        key_id="9efa4550-e04e-4624-a6f2-684af0330f23",
        signing_secret="import-test-signing-secret",
        hmac_audience="perceivo-api-local",
    )

    with pytest.raises(SigningError, match=r"infrastructure\.import_\w+ sends a multipart body"):
        call(client, _EXPORT)

    assert rec.requests == []


# --- export -> import round trip ----------------------------------------------------

_ROUND_TRIPS = [
    pytest.param(
        lambda c: c.infrastructure.export_search_index("i1"),
        lambda c, data: c.infrastructure.import_search_index("i2", data),
        f"{_S}/i1/export",
        f"{_S}/i2/import",
        id="search_index",
    ),
    pytest.param(
        lambda c: c.infrastructure.export_vector_store_collection("c1"),
        lambda c, data: c.infrastructure.import_vector_store_collection("c2", data),
        f"{_V}/c1/export",
        f"{_V}/c2/import",
        id="vector_store",
    ),
]


def _export_then_import(export_path: str, import_path: str, export_body: bytes):
    """Serve the export as the API does (``application/x-ndjson``), accept the import."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == export_path:
            return httpx.Response(
                200, content=export_body, headers={"content-type": "application/x-ndjson"}
            )
        assert request.url.path == import_path
        return httpx.Response(200, json={"inserted": 2})

    return handler


def _file_part(request: httpx.Request) -> bytes:
    """The bytes of the one multipart part, ``file``."""
    boundary = request.headers["content-type"].split("boundary=", 1)[1].encode()
    body = request.content
    part = body.split(b"--" + boundary)[1]
    head, _, rest = part.partition(b"\r\n\r\n")
    assert b'name="file"' in head
    return rest[: -len(b"\r\n")]


@pytest.mark.parametrize("export,load,export_path,import_path", _ROUND_TRIPS)
def test_a_multi_line_export_is_imported_byte_for_byte(export, load, export_path, import_path):
    """The usual export (a metadata line, then a record per line) is NDJSON that does
    not decode as one JSON document, so it comes back as ``str``; the import sends it
    back unchanged."""
    ndjson = b'{"_metadata": {"shape": "s"}}\n{"id": "d1", "v": "\xc3\xa9"}\n{"id": "d2"}\n'
    client, rec = make_client(_export_then_import(export_path, import_path, ndjson))

    exported = export(client)
    got = load(client, exported)

    assert exported == ndjson.decode("utf-8")
    assert isinstance(got, CollectionWriteResult)
    assert [r.url.path for r in rec.requests] == [export_path, import_path]
    assert _file_part(rec.last) == ndjson


@pytest.mark.parametrize("export,load,export_path,import_path", _ROUND_TRIPS)
def test_a_single_line_export_is_still_raw_ndjson_text(export, load, export_path, import_path):
    """A one-line export is a valid JSON document, and must NOT come back decoded:
    the export always returns the NDJSON text, whatever the number of lines."""
    ndjson = b'{"_metadata": {"shape": "s", "count": 0}}\n'
    client, rec = make_client(_export_then_import(export_path, import_path, ndjson))

    exported = export(client)
    load(client, exported)

    assert type(exported) is str
    assert exported == ndjson.decode("utf-8")
    assert _file_part(rec.last) == ndjson
    assert b"Content-Type: application/x-ndjson" in rec.last.content


# --- browse pages ------------------------------------------------------------------


@pytest.mark.parametrize(
    "browse,path",
    [
        (
            lambda c, **kw: c.infrastructure.list_search_index_documents("i1", **kw),
            f"{_S}/i1/documents",
        ),
        (
            lambda c, **kw: c.infrastructure.list_vector_store_entities("c1", **kw),
            f"{_V}/c1/entities",
        ),
    ],
)
def test_browse_forwards_page_and_page_size(browse, path):
    client, rec = make_client(json_handler({"documents": []}))

    browse(client, page=3, page_size=100)

    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == {"page": "3", "page_size": "100"}


@pytest.mark.parametrize(
    "browse,page",
    [
        (
            lambda c, **kw: c.infrastructure.list_search_index_documents("i1", **kw),
            {"documents": [{"id": "d1"}], "total": 40},
        ),
        # Milvus reports total as the size of THIS page: a walk driven by it
        # would stop after page one and report nothing wrong.
        (
            lambda c, **kw: c.infrastructure.list_vector_store_entities("c1", **kw),
            {"entities": [{"id": "e1"}], "total": 1},
        ),
    ],
)
def test_paginate_pages_refuses_a_store_browse_page(browse, page):
    client, _ = make_client(json_handler(page))
    walker = paginate_pages(lambda **kw: browse(client, **kw))

    with pytest.raises(ValueError, match="items"):
        next(walker)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.infrastructure.list_cluster_services(),
        lambda c: c.infrastructure.list_managed_services(),
        lambda c: c.infrastructure.list_managed_service_backups("redis"),
        lambda c: c.infrastructure.get_capacity(),
        lambda c: c.infrastructure.get_mcp_config(),
    ],
)
def test_whole_collection_reads_send_no_page_parameters(call):
    client, rec = make_client(json_handler({"items": [], "total": 0}))

    call(client)

    assert dict(rec.last.url.params) == {}


# --- no credential in a response model ---------------------------------------------

_CREDENTIAL_FIELDS = {
    "admin_password",
    "admin_username",
    "connection_info",
    "connection_secret_name",
    "connection_string",
    "host",
    "password",
    "port",
}


@pytest.mark.parametrize(
    "model",
    [
        BackupRead,
        CapacityRead,
        ClusterServiceStatus,
        DedicatedDatabaseRead,
        DedicatedDatabaseStartAccepted,
        ManagedServiceRead,
        McpConfigDocument,
        NodepoolDetail,
    ],
)
def test_response_models_declare_no_credential_field(model):
    assert _CREDENTIAL_FIELDS.isdisjoint(model.model_fields)


# --- async parity ------------------------------------------------------------------


def test_infrastructure_is_mirrored_on_the_async_client():
    assert "infrastructure" in _NAMESPACES


def test_async_scale_nodepool_awaits_and_hits_the_exact_path():
    sync, rec = make_client(json_handler({"name": "np1", "status": "scaling"}))
    client = _async_from_sync(sync)

    got = asyncio.run(client.infrastructure.scale_nodepool("np1", {"target_nodes": 2}))

    assert isinstance(got, NodepoolDetail)
    assert rec.last.url.path == f"{_I}/cluster/nodepools/np1/scale"


def test_async_import_sends_the_same_multipart_request():
    sync, rec = make_client(json_handler({}))
    client = _async_from_sync(sync)

    asyncio.run(client.infrastructure.import_vector_store_collection("c1", _EXPORT))

    assert rec.last.url.path == f"{_V}/c1/import"
    assert b'name="file"; filename="import.ndjson"' in rec.last.content
