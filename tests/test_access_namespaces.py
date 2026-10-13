"""The access namespaces and the privilege pre-flight repoint.

``client.members``, ``client.invitations``, ``client.groups`` and
``client.organization`` are new. ``client.auth.check_privilege`` (and
``allowed`` over it) calls ``GET /v1/grants/check``, and
``client.service_accounts.delete`` returns the ``ServiceAccountRevoked``
receipt. Method and path for every row are pinned by ``test_wrapper_matrix``;
this module pins what that matrix cannot see.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from perceivo_client import AsyncClient
from perceivo_client.async_client import _NAMESPACES, _AsyncNamespace
from perceivo_client.generated.models import (
    GroupMemberRead,
    GroupRead,
    InvitationRead,
    MemberRead,
    MemberRoleChangeRead,
    OrganizationLimitsRead,
    OrganizationRead,
    PrivilegeCheckResponse,
    ServiceAccountRevoked,
    SubscriptionReadV1,
)
from tests.conftest import json_handler, make_client

_ACCESS = ("organization", "members", "invitations", "groups")


# --- the privilege pre-flight -----------------------------------------------


@pytest.mark.parametrize(
    "call", [lambda c: c.auth.check_privilege("P"), lambda c: c.auth.allowed("P")]
)
def test_the_pre_flight_calls_only_grants_check(call):
    client, rec = make_client(json_handler({"allowed": True}))

    call(client)

    paths = [r.url.path for r in rec.requests]
    assert paths == ["/v1/grants/check"]


def test_check_privilege_returns_the_generated_model():
    client, _ = make_client(json_handler({"allowed": True, "privileges": []}))

    result = client.auth.check_privilege("P")

    assert isinstance(result, PrivilegeCheckResponse)


# --- request shapes the matrix does not pin ----------------------------------


def test_members_remove_sends_the_handoff_only_when_given():
    client, rec = make_client(lambda _r: httpx.Response(204))

    client.members.remove("u1")
    bare = dict(rec.last.url.params)
    client.members.remove("u1", handoff_to_user_id="u2")

    assert bare == {}
    assert dict(rec.last.url.params) == {"handoff_to_user_id": "u2"}


def test_invitations_resend_sends_rotate_token_only_when_given():
    client, rec = make_client(json_handler({}))

    client.invitations.resend("i1")
    bare = dict(rec.last.url.params)
    client.invitations.resend("i1", rotate_token=True)

    assert bare == {}
    assert dict(rec.last.url.params) == {"rotate_token": "true"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.members.restore("u1"),
        lambda c: c.invitations.cancel("i1"),
        lambda c: c.invitations.resend("i1"),
    ],
)
def test_bodyless_posts_send_no_body(call):
    client, rec = make_client(json_handler({}))

    call(client)

    assert rec.last.method == "POST"
    assert rec.last.content == b""


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.members.remove("u1"),
        lambda c: c.groups.delete("g1"),
        lambda c: c.groups.remove_member("g1", "u1"),
    ],
)
def test_no_content_deletes_return_none(call):
    client, _ = make_client(lambda _r: httpx.Response(204))

    assert call(client) is None


# --- typed returns -----------------------------------------------------------

_MEMBER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "email": "a@example.com",
    "name": "A",
    "role": "member",
    "joined_at": "2026-10-01T00:00:00Z",
}


@pytest.mark.parametrize(
    "call,payload,model",
    [
        (lambda c: c.members.restore("u1"), _MEMBER, MemberRead),
        (lambda c: c.members.update_role("u1", {"role": "admin"}), _MEMBER, MemberRoleChangeRead),
        (lambda c: c.members.invite({"email": "a@example.com"}), {"id": "i"}, InvitationRead),
        (lambda c: c.invitations.cancel("i1"), {"id": "i"}, InvitationRead),
        (lambda c: c.invitations.resend("i1"), {"id": "i"}, InvitationRead),
        (lambda c: c.groups.create({"name": "g"}), {"id": "g"}, GroupRead),
        (lambda c: c.groups.get("g1"), {"id": "g"}, GroupRead),
        (lambda c: c.groups.update("g1", {}), {"id": "g"}, GroupRead),
        (
            lambda c: c.groups.update_member("g1", "u1", {"privileges": []}),
            {"user_id": "u"},
            GroupMemberRead,
        ),
        (lambda c: c.organization.get(), {"id": "o"}, OrganizationRead),
        (lambda c: c.organization.get_limits(), {}, OrganizationLimitsRead),
        (lambda c: c.service_accounts.delete("s1"), {"revoked": True}, ServiceAccountRevoked),
    ],
)
def test_object_returns_are_typed(call, payload, model):
    client, _ = make_client(json_handler(payload))

    assert isinstance(call(client), model)


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.members.list(), MemberRead),
        (lambda c: c.invitations.list(), InvitationRead),
        (lambda c: c.groups.list(), GroupRead),
        (lambda c: c.groups.list_members("g1"), GroupMemberRead),
        (lambda c: c.organization.get_subscription(), SubscriptionReadV1),
    ],
)
def test_list_returns_are_typed(call, model):
    client, _ = make_client(json_handler([{"id": "x"}, {"id": "y"}]))

    got = call(client)

    assert len(got) == 2
    assert all(isinstance(item, model) for item in got)


def test_service_account_delete_reads_the_revoke_receipt():
    body = {"revoked": True, "revoked_at": "2026-10-03T00:00:00Z", "revoked_by_user_id": "u1"}
    client, rec = make_client(json_handler(body))

    receipt = client.service_accounts.delete("s1")

    assert rec.last.method == "DELETE"
    assert receipt.revoked is True
    assert receipt.revoked_by_user_id == "u1"


# --- async parity ------------------------------------------------------------


@pytest.mark.parametrize("namespace", _ACCESS)
def test_access_namespaces_are_mirrored_on_the_async_client(namespace):
    assert namespace in _NAMESPACES


def test_async_access_call_awaits_and_returns_the_typed_list():
    sync, rec = make_client(json_handler([_MEMBER]))
    aclient = AsyncClient.__new__(AsyncClient)
    aclient._sync = sync
    for ns in _NAMESPACES:
        setattr(aclient, ns, _AsyncNamespace(getattr(sync, ns)))

    got = asyncio.run(aclient.members.list(include_removed=True))

    assert isinstance(got[0], MemberRead)
    assert rec.last.url.path == "/v1/members"
    assert dict(rec.last.url.params) == {"include_removed": "true"}
