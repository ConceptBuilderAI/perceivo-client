"""``client.grants``.

Each row pins the verb, the raw path with every caller path value sent as
``../xN`` (it must arrive as the one encoded segment ``..%2FxN``), the query
string and the JSON body, from the sync client and from its async twin. The
returns are validated into ``GrantRead``, ``ChangeSet`` and
``CascadeApplyResult``.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import uuid

import httpx
import pytest

from perceivo_client import AsyncClient
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import CascadeApplyResult, ChangeSet, GrantRead
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_B = "/v1"
_GRANT_ID = "6f1c2b0e-0d0a-4e47-9d0e-2a43b8f1a001"
_USER_ID = "6f1c2b0e-0d0a-4e47-9d0e-2a43b8f1a002"
_ASSET_ID = "6f1c2b0e-0d0a-4e47-9d0e-2a43b8f1a003"
_ROLE_ID = "6f1c2b0e-0d0a-4e47-9d0e-2a43b8f1a004"
_GRANT = {
    "id": _GRANT_ID,
    "grantee_type": "user",
    "grantee_id": _USER_ID,
    "resource_type": "asset",
    "resource_id": _ASSET_ID,
    "granted_at": "2026-10-03T00:00:00Z",
    "role_id": _ROLE_ID,
}
_FP = "f" * 64
_CHANGE_SET = {
    "operation": "grant",
    "root": {"id": _ASSET_ID},
    "principal": {"type": "user", "id": _USER_ID},
    "requires_confirmation": True,
    "refused": False,
    "fingerprint": _FP,
}
_CREATE = {
    "grantee_type": "user",
    "grantee_id": _USER_ID,
    "resource_type": "asset",
    "resource_id": _ASSET_ID,
    "role_id": _ROLE_ID,
}
_PREVIEW = {
    "operation": "grant",
    "grantee_type": "user",
    "grantee_id": "u-1",
    "resource_id": "a-1",
    "role_id": "r-1",
}

# (call, verb, raw path, query, body or None for a bodiless request)
_ROWS = [
    pytest.param(
        lambda c: c.grants.list(grantee_type="user", grantee_id="u-1", limit=10),
        "GET",
        f"{_B}/grants",
        {"grantee_type": "user", "grantee_id": "u-1", "limit": "10"},
        None,
        id="grants.list",
    ),
    pytest.param(
        lambda c: c.grants.list(
            grantee="me",
            resource_type="asset",
            resource_id="a-1",
            include_revoked=True,
            offset=20,
        ),
        "GET",
        f"{_B}/grants",
        {
            "grantee": "me",
            "resource_type": "asset",
            "resource_id": "a-1",
            "include_revoked": "true",
            "offset": "20",
        },
        None,
        id="grants.list-filters",
    ),
    pytest.param(
        lambda c: c.grants.list(),
        "GET",
        f"{_B}/grants",
        {},
        None,
        id="grants.list-unfiltered",
    ),
    pytest.param(
        lambda c: c.grants.create(_CREATE),
        "POST",
        f"{_B}/grants",
        {},
        _CREATE,
        id="grants.create",
    ),
    pytest.param(
        lambda c: c.grants.update("../x0", {"role_id": "r-2"}),
        "PATCH",
        f"{_B}/grants/..%2Fx0",
        {},
        {"role_id": "r-2"},
        id="grants.update",
    ),
    pytest.param(
        lambda c: c.grants.delete("../x0"),
        "DELETE",
        f"{_B}/grants/..%2Fx0",
        {},
        None,
        id="grants.delete",
    ),
    pytest.param(
        lambda c: c.grants.preview(_PREVIEW),
        "POST",
        f"{_B}/grants/preview",
        {},
        _PREVIEW,
        id="grants.preview",
    ),
    pytest.param(
        lambda c: c.grants.apply({**_PREVIEW, "fingerprint": _FP, "reason": "r"}),
        "POST",
        f"{_B}/grants/apply",
        {},
        {**_PREVIEW, "fingerprint": _FP, "reason": "r"},
        id="grants.apply",
    ),
]


def _ok(request: httpx.Request) -> httpx.Response:
    if request.method == "DELETE":
        return httpx.Response(204)
    return httpx.Response(200, json={})


def _assert_request(rec, verb, raw_path, query, body):
    request = rec.last
    assert request.method == verb
    assert request.url.raw_path.split(b"?")[0] == raw_path.encode()
    assert dict(request.url.params) == query
    if body is None:
        assert request.content == b""
    else:
        assert json.loads(request.content) == body


@pytest.mark.parametrize("call,verb,raw_path,query,body", _ROWS)
def test_each_method_sends_its_verb_path_query_and_body(call, verb, raw_path, query, body):
    client, rec = make_client(_ok)

    call(client)

    assert len(rec.requests) == 1
    _assert_request(rec, verb, raw_path, query, body)


@pytest.mark.parametrize("call,verb,raw_path,query,body", _ROWS)
def test_the_async_client_sends_the_same_request(call, verb, raw_path, query, body):
    sync, rec = make_client(_ok)
    client = _async_from_sync(sync)

    async def run():
        return await call(client)

    asyncio.run(run())

    assert len(rec.requests) == 1
    _assert_request(rec, verb, raw_path, query, body)


def test_the_table_covers_6_methods():
    assert {row.id.split("-")[0] for row in _ROWS} == {
        "grants.list",
        "grants.create",
        "grants.update",
        "grants.delete",
        "grants.preview",
        "grants.apply",
    }


def test_grants_is_mirrored_on_the_async_client():
    assert "grants" in _NAMESPACES
    client = AsyncClient(api_key="k", base_url="https://api.test.perceivo.ai")
    try:
        assert hasattr(client, "grants")
    finally:
        asyncio.run(client.aclose())


# --- returns -----------------------------------------------------------------


def test_grants_list_validates_each_record_into_grant_read():
    client, _ = make_client(json_handler([_GRANT]))

    (grant,) = client.grants.list(grantee="me")

    assert isinstance(grant, GrantRead)
    assert grant.id == uuid.UUID(_GRANT_ID)
    assert grant.role_id == uuid.UUID(_ROLE_ID)
    assert grant.granted_at == datetime.datetime(2026, 10, 3, tzinfo=datetime.UTC)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.grants.create(_CREATE),
        lambda c: c.grants.update(_GRANT_ID, {"role_id": _ROLE_ID}),
    ],
    ids=["create", "update"],
)
def test_grant_writes_return_the_validated_record(call):
    client, _ = make_client(json_handler(_GRANT, status=201))

    grant = call(client)

    assert isinstance(grant, GrantRead)
    assert grant.resource_id == uuid.UUID(_ASSET_ID)


def test_preview_returns_the_change_set_and_apply_the_result():
    client, _ = make_client(json_handler(_CHANGE_SET))
    change_set = client.grants.preview(_PREVIEW)
    assert isinstance(change_set, ChangeSet)
    assert change_set.fingerprint == _FP
    assert change_set.requires_confirmation is True

    result = {"operation": "grant", "applied": True, "change_set": _CHANGE_SET}
    client, _ = make_client(json_handler(result))
    applied = client.grants.apply({**_PREVIEW, "fingerprint": _FP})
    assert isinstance(applied, CascadeApplyResult)
    assert applied.applied is True
    assert applied.change_set.fingerprint == _FP


def test_delete_returns_none_on_204():
    client, _ = make_client(lambda request: httpx.Response(204))

    assert client.grants.delete(_GRANT_ID) is None


def test_a_grants_404_surfaces_as_not_found():
    from perceivo_client.errors import PerceivoNotFoundError

    client, _ = make_client(json_handler({"detail": "Not Found"}, status=404))

    with pytest.raises(PerceivoNotFoundError):
        client.grants.list()
