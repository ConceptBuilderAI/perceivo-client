"""Storage spaces, entries, content versions and the trash.

Pins each method's exact request and its async twin, plus the dot-segment refusal,
the two-shape entry create, the multipart replacement, default bodies and typed
returns.
"""

from __future__ import annotations

import asyncio
import functools
import io
import json
import pathlib

import httpx
import pytest

from perceivo_client import PerceivoGrantError, paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import (
    BulkOperationResult,
    EmptyTrashResult,
    FileEntryRead,
    PaginatedFileList,
    StorageSpaceRead,
    StorageUsageRead,
    UploadResponse,
    UploadTargetResponse,
)
from perceivo_client.signing import HEADER_SIGNATURE
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_F = "/v1/files"
#: ``../x`` as one encoded segment. Unencoded, ``httpx`` would resolve it and
#: address the parent collection instead.
_ID = "../x"
_ENC = "..%2Fx"
_NO_BODY = object()
_STAMP = "2026-10-03T00:00:00Z"
_E1 = "6f1c2a1e-0d6b-4c55-9a43-1d1f2b3c4d5e"
_S1 = "0b7e9d2c-5a4f-4e3b-8c1d-2e3f4a5b6c7d"
_U1 = "9a8b7c6d-5e4f-4a3b-9c2d-1e0f9a8b7c6d"
_V2 = "3c4d5e6f-7a8b-4c9d-8e0f-1a2b3c4d5e6f"
_ENTRY = {
    "id": _E1,
    "storage_space_id": _S1,
    "name": "a.csv",
    "path": "/a.csv",
    "entry_type": "file",
    "is_starred": False,
    "is_trashed": False,
    "created_by_user_id": _U1,
    "updated_by_user_id": _U1,
    "created_at": _STAMP,
    "updated_at": _STAMP,
}
_VERSION = {
    "id": _V2,
    "file_entry_id": _E1,
    "version_number": 2,
    "size_bytes": 4,
    "is_current": True,
    "created_by_user_id": _U1,
    "created_at": _STAMP,
}

#: (id, call, verb, raw path, query, JSON body or _NO_BODY) for every ``client.files``
#: method that sends JSON or nothing; ``replace_content`` is pinned below.
_ROWS = [
    ("get_space", lambda c: c.files.get_space(_ID), "GET", f"spaces/{_ENC}", {}, _NO_BODY),
    (
        "create_space",
        lambda c: c.files.create_space({"name": "datasets"}),
        "POST",
        "spaces",
        {},
        {"name": "datasets"},
    ),
    (
        "update_space",
        lambda c: c.files.update_space(_ID, {"quota_bytes": 1024}),
        "PATCH",
        f"spaces/{_ENC}",
        {},
        {"quota_bytes": 1024},
    ),
    (
        "delete_space",
        lambda c: c.files.delete_space(_ID, force=True),
        "DELETE",
        f"spaces/{_ENC}",
        {"force": "true"},
        _NO_BODY,
    ),
    (
        "space_usage",
        lambda c: c.files.get_space_usage(_ID),
        "GET",
        f"spaces/{_ENC}/usage",
        {},
        _NO_BODY,
    ),
    (
        "create_entry",
        lambda c: c.files.create_entry(_ID, {"type": "folder", "name": "raw"}),
        "POST",
        f"spaces/{_ENC}/entries",
        {},
        {"type": "folder", "name": "raw"},
    ),
    (
        "update",
        lambda c: c.files.update_entry(_ID, {"is_starred": True}),
        "PATCH",
        f"entries/{_ENC}",
        {},
        {"is_starred": True},
    ),
    (
        "copy",
        lambda c: c.files.copy(_ID, {"dest_parent_id": "f1"}),
        "POST",
        f"entries/{_ENC}/copy",
        {},
        {"dest_parent_id": "f1"},
    ),
    (
        "move",
        lambda c: c.files.move(_ID, {"new_parent_id": "f1"}),
        "POST",
        f"entries/{_ENC}/move",
        {},
        {"new_parent_id": "f1"},
    ),
    (
        "create_upload_url",
        lambda c: c.files.create_upload_url({"space_id": "s1", "file_name": "a", "size_bytes": 1}),
        "POST",
        "upload-url",
        {},
        {"space_id": "s1", "file_name": "a", "size_bytes": 1},
    ),
    (
        "trash",
        lambda c: c.files.list_trash(_ID, page=2, page_size=100),
        "GET",
        f"spaces/{_ENC}/trash",
        {"page": "2", "page_size": "100"},
        _NO_BODY,
    ),
    (
        "empty_trash",
        lambda c: c.files.empty_trash(_ID),
        "DELETE",
        f"spaces/{_ENC}/trash",
        {},
        _NO_BODY,
    ),
    (
        "restore",
        lambda c: c.files.restore_entry(_ID),
        "POST",
        f"trash/{_ENC}/restore",
        {},
        _NO_BODY,
    ),
    (
        "restore_many",
        lambda c: c.files.restore_entries({"entry_ids": ["e1", "e2"]}),
        "POST",
        "trash/restore",
        {},
        {"entry_ids": ["e1", "e2"]},
    ),
]
_PARAMS = [pytest.param(*row[1:], id=row[0]) for row in _ROWS]


def _assert_request(request: httpx.Request, verb, path, query, body) -> None:
    assert request.method == verb
    assert request.url.raw_path.split(b"?")[0] == f"{_F}/{path}".encode()
    assert dict(request.url.params) == query
    if body is _NO_BODY:
        assert request.content == b""
    else:
        assert json.loads(request.content) == body


# --- one test per method: verb, encoded path, query, body ----------------------------


@pytest.mark.parametrize("call,verb,path,query,body", _PARAMS)
def test_each_method_sends_the_exact_request(call, verb, path, query, body):
    client, rec = make_client(json_handler({}))

    call(client)

    _assert_request(rec.last, verb, path, query, body)


@pytest.mark.parametrize("call,verb,path,query,body", _PARAMS)
def test_each_method_sends_the_same_request_from_the_async_client(call, verb, path, query, body):
    sync, rec = make_client(json_handler({}))
    client = _async_from_sync(sync)

    async def run():
        return await call(client)

    asyncio.run(run())

    _assert_request(rec.last, verb, path, query, body)


def test_files_is_mirrored_on_the_async_client():
    assert "files" in _NAMESPACES


# --- dot segments ------------------------------------------------------------------


@pytest.mark.parametrize("value", ["..", ".", ""])
@pytest.mark.parametrize(
    "call",
    [
        lambda c, v: c.files.delete_space(v),
        lambda c, v: c.files.empty_trash(v),
        lambda c, v: c.files.move(v),
        lambda c, v: c.files.restore_entry(v),
        lambda c, v: c.files.replace_content(v, b"x"),
    ],
)
def test_a_dot_segment_id_is_refused_before_anything_is_sent(call, value):
    """Warning: ``.../spaces/..`` would resolve to ``/files``; ``""`` to a different route."""
    client, rec = make_client(json_handler({}))

    with pytest.raises(ValueError, match="one path segment"):
        call(client, value)

    assert rec.requests == []


def test_the_dot_segment_hazard_is_real_for_an_unencoded_path():
    """Positive control: an unencoded ``../x`` leaves the space it names."""
    request = httpx.Request("DELETE", f"https://api.example{_F}/spaces/../x/trash")

    assert request.url.path == f"{_F}/x/trash"


# --- typed returns -----------------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.files.get_space("s1"), StorageSpaceRead),
        (lambda c: c.files.create_space({}), StorageSpaceRead),
        (lambda c: c.files.update_space("s1", {}), StorageSpaceRead),
        (lambda c: c.files.get_space_usage("s1"), StorageUsageRead),
        (lambda c: c.files.update_entry("e1", {}), FileEntryRead),
        (lambda c: c.files.copy("e1"), BulkOperationResult),
        (lambda c: c.files.move("e1"), FileEntryRead),
        (lambda c: c.files.create_upload_url({}), UploadTargetResponse),
        (lambda c: c.files.list_trash("s1"), PaginatedFileList),
        (lambda c: c.files.restore_entry("e1"), FileEntryRead),
        (lambda c: c.files.restore_entries({}), BulkOperationResult),
        (lambda c: c.files.replace_content("e1", b"x"), UploadResponse),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x", "name": "n"}))

    assert isinstance(call(client), model)


def test_delete_space_returns_none_on_no_content():
    client, _ = make_client(lambda request: httpx.Response(204))

    assert client.files.delete_space("s1") is None


@pytest.mark.parametrize(
    "status,body",
    [
        (200, {"deleted_count": 3}),
        (202, {"deleted_count": 120, "message": "Stored content is being removed."}),
    ],
)
def test_empty_trash_returns_the_typed_result(status, body):
    client, _ = make_client(json_handler(body, status=status))

    got = client.files.empty_trash("s1")

    assert isinstance(got, EmptyTrashResult)
    assert got.deleted_count == body["deleted_count"]
    assert got.message == body.get("message")


# --- the entry create answers two shapes ---------------------------------------------


def test_a_folder_create_is_returned_as_the_entry():
    folder = {**_ENTRY, "name": "raw", "path": "/raw", "entry_type": "folder"}
    client, _ = make_client(json_handler(folder, status=201))

    got = client.files.create_entry("s1", {"type": "folder", "name": "raw"})

    assert isinstance(got, FileEntryRead)
    assert got.entry_type.value == "folder"


def test_a_registration_is_returned_as_the_entry_and_its_version():
    body = {"entry": _ENTRY, "version": _VERSION}
    client, _ = make_client(json_handler(body))

    got = client.files.create_entry("s1", {"type": "file", "blob_name": "b"})

    assert isinstance(got, UploadResponse)
    assert str(got.entry.id) == _E1
    assert got.version.version_number == 2


# --- defaults ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "call", [lambda c: c.files.copy("e1"), lambda c: c.files.move("e1")], ids=["copy", "move"]
)
def test_copy_and_move_send_an_empty_object_without_a_body(call):
    """The body is required; ``{}`` means the space root."""
    client, rec = make_client(json_handler({}))

    call(client)

    assert json.loads(rec.last.content) == {}


def test_delete_space_sends_no_force_unless_asked():
    client, rec = make_client(lambda request: httpx.Response(204))

    client.files.delete_space("s1")

    assert dict(rec.last.url.params) == {}


def test_paginate_pages_walks_a_bound_trash_listing():
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        items = [{"id": f"e{page}"}] if page <= 2 else []
        return httpx.Response(200, json={"items": items, "total": 2})

    client, rec = make_client(handler)

    got = list(paginate_pages(functools.partial(client.files.list_trash, "s1"), page_size=1))

    assert [item["id"] for item in got] == ["e1", "e2"]
    assert {r.url.path for r in rec.requests} == {f"{_F}/spaces/s1/trash"}


# --- replace_content: multipart, one part named file -----------------------------------


def test_replace_content_puts_the_bytes_as_the_one_multipart_part():
    client, rec = make_client(json_handler({"entry": {"id": "e1"}, "version": {"id": "v2"}}))

    client.files.replace_content(_ID, b"new,bytes\n", version_comment="fix header")

    body = rec.last.content
    assert rec.last.method == "PUT"
    assert rec.last.url.raw_path.split(b"?")[0] == f"{_F}/entries/{_ENC}/content".encode()
    assert dict(rec.last.url.params) == {"version_comment": "fix header"}
    assert rec.last.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert b'name="file"; filename="content"' in body
    assert body.count(b"Content-Disposition") == 1
    assert b"new,bytes\n" in body


def test_replace_content_sends_the_content_type_and_no_comment_unless_given():
    client, rec = make_client(json_handler({}))

    client.files.replace_content("e1", b"{}", content_type="application/json")

    assert dict(rec.last.url.params) == {}
    assert b"Content-Type: application/json" in rec.last.content


def test_replace_content_declares_a_content_length_for_a_file_object():
    client, rec = make_client(json_handler({}))

    client.files.replace_content("e1", io.BytesIO(b"abc"))

    assert int(rec.last.headers["content-length"]) == len(rec.last.content)
    assert "transfer-encoding" not in rec.last.headers


def test_a_signing_client_sends_replace_content_signed():
    client, rec = make_client(
        json_handler({}),
        key_id="9efa4550-e04e-4624-a6f2-684af0330f23",
        signing_secret="replace-test-signing-secret",
        hmac_audience="perceivo-api-local",
    )

    client.files.replace_content("e1", b"x")

    assert len(rec.requests) == 1
    assert rec.last.method == "PUT"
    assert HEADER_SIGNATURE in rec.last.headers


def test_async_replace_content_sends_the_same_multipart_request():
    sync, rec = make_client(json_handler({}))
    client = _async_from_sync(sync)

    asyncio.run(client.files.replace_content(_ID, b"abc", version_comment="v"))

    assert rec.last.method == "PUT"
    assert rec.last.url.raw_path.split(b"?")[0] == f"{_F}/entries/{_ENC}/content".encode()
    assert dict(rec.last.url.params) == {"version_comment": "v"}
    assert b'name="file"; filename="content"' in rec.last.content


_SPEC = pathlib.Path(__file__).resolve().parents[1] / "openapi" / "openapi-v1.json"
_SPACE_ID = "5b1f6c1e-3a0b-4b56-9d6e-0d2c1c1a7a10"

_GATED = {
    "create_storage_space": "FILE_WRITE",
    "update_storage_space_v1": "FILE_WRITE",
    "delete_storage_space_v1": "FILE_DELETE",
    "create_space_entry": "FILE_WRITE",
    "update_file_entry": "FILE_WRITE",
    "delete_file_entry": "FILE_DELETE",
    "copy_file_entry": "FILE_WRITE",
    "move_file_entry": "FILE_WRITE",
    "replace_file_entry_content": "FILE_WRITE",
    "create_file_upload_url": "FILE_WRITE",
    "empty_space_trash": "FILE_DELETE",
    "upload_files_to_space": "FILE_WRITE",
    "restore_file_entry": "FILE_WRITE",
    "restore_file_entries": "FILE_WRITE",
}


def test_the_vendored_spec_declares_the_file_privileges():
    spec = json.loads(_SPEC.read_text(encoding="utf-8"))
    declared = {
        op["operationId"]: op.get("x-perceivo-privilege")
        for item in spec["paths"].values()
        for op in item.values()
        if isinstance(op, dict) and op.get("operationId") in _GATED
    }

    assert declared == _GATED


@pytest.mark.parametrize(
    ("call", "privilege"),
    [
        (lambda c: c.files.create_space({"name": "x"}), "FILE_WRITE"),
        (lambda c: c.files.delete_space(_SPACE_ID), "FILE_DELETE"),
        (lambda c: c.files.empty_trash(_SPACE_ID), "FILE_DELETE"),
        (lambda c: c.files.restore_entry(_SPACE_ID), "FILE_WRITE"),
    ],
    ids=["create_space", "delete_space", "empty_trash", "restore_entry"],
)
def test_a_missing_file_privilege_raises_grant_error(call, privilege):
    payload = {"code": "insufficient_privilege", "message": f"requires {privilege}"}
    client, _ = make_client(json_handler(payload, status=403))

    with pytest.raises(PerceivoGrantError) as info:
        call(client)

    assert info.value.code == "insufficient_privilege"
