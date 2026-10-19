"""Infrastructure stores: import, export round trip, browse pages, models, async parity."""

from __future__ import annotations

import asyncio
import io

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import (
    BackupRead,
    CapacityRead,
    ClusterServiceStatus,
    CollectionWriteResult,
    DedicatedDatabaseRead,
    DedicatedDatabaseStartAccepted,
    ManagedServiceRead,
    McpConfigDocument,
    NodepoolDetail,
)
from perceivo_client.signing import HEADER_SIGNATURE
from tests._infrastructure_fixtures import (
    _EXPORT,
    _I,
    _S,
    _V,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

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
def test_a_signing_client_sends_the_import_signed(call, path):
    client, rec = make_client(
        json_handler({}),
        key_id="9efa4550-e04e-4624-a6f2-684af0330f23",
        signing_secret="import-test-signing-secret",
        hmac_audience="perceivo-api-local",
    )

    call(client, _EXPORT)

    assert len(rec.requests) == 1
    assert rec.last.url.path == path
    assert HEADER_SIGNATURE in rec.last.headers
    assert _EXPORT in rec.last.content


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
    """A one-line export is returned as NDJSON text, not decoded."""
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
        # Milvus reports total as the size of this page, not of the collection.
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
