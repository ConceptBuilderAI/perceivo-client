"""Every ``client.files`` call, pinned by the request it actually sends.

The method/path wrapper cases cannot see query parameters or bodies, so each
wrapper is pinned here by method, path, query and body. ``files.upload`` is
pinned in ``tests/test_files_upload_contract.py`` and the ``files.list_entries``
envelope in ``tests/test_files_envelope.py``.
"""

from __future__ import annotations

import httpx
import pytest

from perceivo_client import PerceivoGrantError
from perceivo_client.generated.models import FileEntryRead, StorageSpaceRead
from tests.conftest import json_handler, make_client

_SPACE = "5b1f6c1e-3a0b-4b56-9d6e-0d2c1c1a7a10"
_ENTRY = "c0a8012e-7b1d-4c58-8f43-2f6f5a0c9e77"
_USER = "0f8fad5b-d9cb-469f-a165-70867728950e"


@pytest.mark.parametrize(
    ("call", "payload", "method", "path", "params"),
    [
        (lambda c: c.files.list_spaces(), [], "GET", "/v1/files/spaces", {}),
        (
            lambda c: c.files.list_entries(_SPACE),
            {"items": []},
            "GET",
            f"/v1/files/spaces/{_SPACE}/entries",
            {},
        ),
        (
            lambda c: c.files.list_entries(_SPACE, query="rows", page=2),
            {"items": []},
            "GET",
            f"/v1/files/spaces/{_SPACE}/entries",
            {"query": "rows", "page": "2"},
        ),
        (lambda c: c.files.get_entry(_ENTRY), {}, "GET", f"/v1/files/entries/{_ENTRY}", {}),
        (
            lambda c: c.files.delete_entry(_ENTRY),
            {},
            "DELETE",
            f"/v1/files/entries/{_ENTRY}",
            {},
        ),
        (
            lambda c: c.files.delete_entry(_ENTRY, permanent=True),
            {},
            "DELETE",
            f"/v1/files/entries/{_ENTRY}",
            {"permanent": "true"},
        ),
    ],
)
def test_file_calls_send_the_expected_request(call, payload, method, path, params):
    client, recorder = make_client(json_handler(payload))

    call(client)

    assert len(recorder.requests) == 1
    assert recorder.last.method == method
    assert recorder.last.url.path == path
    assert dict(recorder.last.url.params) == params
    assert recorder.last.content == b""


def test_download_reads_the_entry_content_and_returns_the_bytes():
    client, recorder = make_client(lambda _request: httpx.Response(200, content=b"a,b\n"))

    assert client.files.download(_ENTRY) == b"a,b\n"
    assert recorder.last.method == "GET"
    assert recorder.last.url.path == f"/v1/files/entries/{_ENTRY}/content"
    assert dict(recorder.last.url.params) == {}


def test_spaces_returns_typed_storage_spaces():
    space = {
        "id": _SPACE,
        "name": "Default",
        "used_bytes": 0,
        "is_default": True,
        "is_personal": False,
        "created_by_user_id": _USER,
        "created_at": "2026-10-02T00:00:00Z",
        "updated_at": "2026-10-02T00:00:00Z",
    }
    client, _recorder = make_client(json_handler([space]))

    spaces = client.files.list_spaces()

    assert len(spaces) == 1
    assert isinstance(spaces[0], StorageSpaceRead)
    assert str(spaces[0].id) == _SPACE


def test_get_returns_a_typed_entry():
    client, _recorder = make_client(json_handler({"id": _ENTRY, "name": "rows.csv"}))

    entry = client.files.get_entry(_ENTRY)

    assert isinstance(entry, FileEntryRead)
    assert entry.name == "rows.csv"


@pytest.mark.parametrize(
    ("call", "privilege"),
    [
        (lambda c: c.files.update_entry(_ENTRY, {"name": "x"}), "FILE_WRITE"),
        (lambda c: c.files.delete_entry(_ENTRY), "FILE_DELETE"),
    ],
    ids=["update_entry", "delete_entry"],
)
def test_a_missing_file_privilege_raises_grant_error(call, privilege):
    payload = {"code": "insufficient_privilege", "message": f"requires {privilege}"}
    client, _ = make_client(json_handler(payload, status=403))

    with pytest.raises(PerceivoGrantError) as info:
        call(client)

    assert info.value.code == "insufficient_privilege"
