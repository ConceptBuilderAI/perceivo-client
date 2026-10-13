"""Messaging threads, review assign/draft/cancel, attachment delete.

``client.threads`` is new and wraps the twelve ``/threads`` operations;
``client.reviews`` gains ``assign``, ``save_draft`` and ``cancel``;
``client.support`` gains ``delete_attachment``. Method and path for every row
are pinned by ``test_wrapper_matrix``; this module pins, per method, the exact
request (verb, raw path with a ``../x`` id encoded into one segment, query and
body) and its async twin, plus the dot-segment refusal, the ``204`` verbs, the
``data``/``next`` thread page that ``paginate_pages`` must refuse, the required
search query and typed returns.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.errors import PerceivoConflictError, PerceivoNotFoundError
from perceivo_client.generated.models import (
    ReviewRead,
    ThreadListResponse,
    ThreadMessage,
    ThreadMessagesPage,
    ThreadParticipant,
    ThreadRead,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_B = "/v1"
#: ``../x`` and ``../y`` as one encoded segment each. Unencoded, ``httpx``
#: would resolve them and address the parent collection instead.
_ID = "../x"
_ENC = "..%2Fx"
_ID2 = "../y"
_ENC2 = "..%2Fy"
_NO_BODY = object()

#: (id, call, verb, raw path, query, JSON body or _NO_BODY). Every new method.
_ROWS = [
    # --- threads ---
    (
        "threads.list",
        lambda c: c.threads.list(page=2, page_size=50),
        "GET",
        "threads",
        {"page": "2", "page_size": "50"},
        _NO_BODY,
    ),
    (
        "threads.search",
        lambda c: c.threads.search("invoice", page=1),
        "GET",
        "threads/search",
        {"q": "invoice", "page": "1"},
        _NO_BODY,
    ),
    (
        "threads.create",
        lambda c: c.threads.create({"participant_user_ids": ["u2"], "title": "t"}),
        "POST",
        "threads",
        {},
        {"participant_user_ids": ["u2"], "title": "t"},
    ),
    ("threads.get", lambda c: c.threads.get(_ID), "GET", f"threads/{_ENC}", {}, _NO_BODY),
    (
        "threads.update",
        lambda c: c.threads.update(_ID, {"title": "renamed"}),
        "PATCH",
        f"threads/{_ENC}",
        {},
        {"title": "renamed"},
    ),
    ("threads.delete", lambda c: c.threads.delete(_ID), "DELETE", f"threads/{_ENC}", {}, _NO_BODY),
    (
        "threads.acknowledge",
        lambda c: c.threads.acknowledge(_ID),
        "POST",
        f"threads/{_ENC}/acknowledge",
        {},
        _NO_BODY,
    ),
    (
        "threads.list_messages",
        lambda c: c.threads.list_messages(_ID, limit=10, before="2026-10-01T00:00:00Z"),
        "GET",
        f"threads/{_ENC}/messages",
        {"limit": "10", "before": "2026-10-01T00:00:00Z"},
        _NO_BODY,
    ),
    (
        "threads.create_message",
        lambda c: c.threads.create_message(_ID, {"body": "hello"}),
        "POST",
        f"threads/{_ENC}/messages",
        {},
        {"body": "hello"},
    ),
    (
        "threads.list_participants",
        lambda c: c.threads.list_participants(_ID),
        "GET",
        f"threads/{_ENC}/participants",
        {},
        _NO_BODY,
    ),
    (
        "threads.add_participant",
        lambda c: c.threads.add_participant(_ID, {"user_id": "u3"}),
        "POST",
        f"threads/{_ENC}/participants",
        {},
        {"user_id": "u3"},
    ),
    (
        "threads.remove_participant",
        lambda c: c.threads.remove_participant(_ID, _ID2),
        "DELETE",
        f"threads/{_ENC}/participants/{_ENC2}",
        {},
        _NO_BODY,
    ),
    # --- reviews ---
    (
        "reviews.assign",
        lambda c: c.reviews.assign(_ID, {"assignment_type": "group", "assignee_group_id": "g1"}),
        "POST",
        f"reviews/{_ENC}/assign",
        {},
        {"assignment_type": "group", "assignee_group_id": "g1"},
    ),
    (
        "reviews.save_draft",
        lambda c: c.reviews.save_draft(_ID, {"draft_data": {"q1": "yes"}}),
        "PUT",
        f"reviews/{_ENC}/draft",
        {},
        {"draft_data": {"q1": "yes"}},
    ),
    ("reviews.cancel", lambda c: c.reviews.cancel(_ID), "DELETE", f"reviews/{_ENC}", {}, _NO_BODY),
    # --- support ---
    (
        "support.delete_attachment",
        lambda c: c.support.delete_attachment(_ID, _ID2),
        "DELETE",
        f"support/tickets/{_ENC}/attachments/{_ENC2}",
        {},
        _NO_BODY,
    ),
]
_PARAMS = [pytest.param(*row[1:], id=row[0]) for row in _ROWS]


def _assert_request(request: httpx.Request, verb, path, query, body) -> None:
    assert request.method == verb
    assert request.url.raw_path.split(b"?")[0] == f"{_B}/{path}".encode()
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


@pytest.mark.parametrize("namespace", ["threads", "reviews", "support"])
def test_the_namespace_is_mirrored_on_the_async_client(namespace):
    assert namespace in _NAMESPACES


# --- dot segments ------------------------------------------------------------------


@pytest.mark.parametrize("value", ["..", ".", ""])
@pytest.mark.parametrize(
    "call",
    [
        lambda c, v: c.threads.delete(v),
        lambda c, v: c.threads.remove_participant("t1", v),
        lambda c, v: c.reviews.cancel(v),
        lambda c, v: c.support.delete_attachment("t1", v),
    ],
    ids=["thread", "participant", "review", "attachment"],
)
def test_a_dot_segment_id_is_refused_before_anything_is_sent(call, value):
    """Warning: ``.../participants/..`` would resolve to the thread itself: a thread delete."""
    client, rec = make_client(json_handler({}))

    with pytest.raises(ValueError, match="one path segment"):
        call(client, value)

    assert rec.requests == []


def test_the_dot_segment_hazard_is_real_for_an_unencoded_path():
    """Positive control: an unencoded ``..`` participant addresses the thread."""
    request = httpx.Request("DELETE", f"https://api.example{_B}/threads/t1/participants/..")

    assert request.url.path == f"{_B}/threads/t1"


# --- returns -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.threads.list(), ThreadListResponse),
        (lambda c: c.threads.search("q"), ThreadListResponse),
        (lambda c: c.threads.create({}), ThreadRead),
        (lambda c: c.threads.get("t1"), ThreadRead),
        (lambda c: c.threads.update("t1", {}), ThreadRead),
        (lambda c: c.threads.list_messages("t1"), ThreadMessagesPage),
        (lambda c: c.threads.create_message("t1", {}), ThreadMessage),
        (lambda c: c.threads.add_participant("t1", {}), ThreadParticipant),
        (lambda c: c.reviews.assign("r1", {}), ReviewRead),
        (lambda c: c.reviews.save_draft("r1", {}), ReviewRead),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x", "user_id": "u1", "role": "member"}))

    assert isinstance(call(client), model)


def test_participants_is_a_typed_bare_array():
    client, _ = make_client(json_handler([{"user_id": "u1", "role": "owner"}]))

    got = client.threads.list_participants("t1")

    assert isinstance(got[0], ThreadParticipant)
    assert got[0].role == "owner"


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.threads.delete("t1"),
        lambda c: c.threads.acknowledge("t1"),
        lambda c: c.threads.remove_participant("t1", "u1"),
        lambda c: c.reviews.cancel("r1"),
        lambda c: c.support.delete_attachment("t1", "a1"),
    ],
    ids=["delete", "acknowledge", "remove_participant", "cancel", "delete_attachment"],
)
def test_no_content_verbs_return_none(call):
    client, _ = make_client(lambda request: httpx.Response(204))

    assert call(client) is None


def test_the_owner_leaving_raises_conflict():
    """The owner removing themselves is a ``409``, relayed unchanged."""
    detail = "The owner cannot leave the conversation; delete it instead"
    client, _ = make_client(json_handler({"detail": detail}, status=409))

    with pytest.raises(PerceivoConflictError) as info:
        client.threads.remove_participant("t1", "u1")

    assert info.value.message == detail


def test_a_member_removing_somebody_else_raises_not_found():
    """A member who names somebody else gets the shared ``404``."""
    client, _ = make_client(json_handler({"error": "not_found"}, status=404))

    with pytest.raises(PerceivoNotFoundError):
        client.threads.remove_participant("t1", "u2")


def test_a_message_page_carries_has_more_for_backward_paging():
    message = {
        "id": "m1",
        "conversation_id": "t1",
        "sender_type": "user",
        "body": "hi",
        "created_at": "2026-10-03T00:00:00Z",
    }
    page = {"messages": [message], "has_more": True}
    client, _ = make_client(json_handler(page))

    got = client.threads.list_messages("t1")

    assert got.has_more is True
    assert isinstance(got.messages[0], ThreadMessage)


# --- paging and the required search query ---------------------------------------------


def test_paginate_pages_refuses_the_data_next_thread_page():
    """The thread page is ``data``/``next``, not ``items``: a walk must not guess."""
    client, _ = make_client(json_handler({"data": [{"id": "t1"}], "total": 1, "next": None}))
    walker = paginate_pages(client.threads.list)

    with pytest.raises(ValueError, match="items"):
        next(walker)


def test_a_keyword_q_cannot_be_passed_beside_the_positional_query():
    """``q`` is positional and required; a keyword ``q`` cannot shadow it silently."""
    client, rec = make_client(json_handler({}))

    with pytest.raises(TypeError):
        client.threads.search("a", q="b")

    assert rec.requests == []


def test_async_search_awaits_and_sends_the_query():
    sync, rec = make_client(json_handler({"data": [], "page": 1, "page_size": 25, "total": 0}))
    client = _async_from_sync(sync)

    got = asyncio.run(client.threads.search("invoice"))

    assert isinstance(got, ThreadListResponse)
    assert dict(rec.last.url.params) == {"q": "invoice"}
