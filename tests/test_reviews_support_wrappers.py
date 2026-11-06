"""Review assign/draft/cancel, attachment delete.

``client.reviews`` gains ``assign``, ``save_draft`` and ``cancel``;
``client.support`` gains ``delete_attachment``. Method and path for every row
are pinned by ``test_wrapper_matrix``; this module pins, per method, the exact
request (verb, raw path with a ``../x`` id encoded into one segment, query and
body) and its async twin, plus the dot-segment refusal, the ``204`` verbs and
typed returns.
"""

from __future__ import annotations

import asyncio
import json
from functools import partial

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.errors import PerceivoGrantError
from perceivo_client.generated.models import ReviewRead
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


@pytest.mark.parametrize("namespace", ["reviews", "support"])
def test_the_namespace_is_mirrored_on_the_async_client(namespace):
    assert namespace in _NAMESPACES


# --- dot segments ------------------------------------------------------------------


@pytest.mark.parametrize("value", ["..", ".", ""])
@pytest.mark.parametrize(
    "call",
    [
        lambda c, v: c.reviews.cancel(v),
        lambda c, v: c.support.delete_attachment("t1", v),
    ],
    ids=["review", "attachment"],
)
def test_a_dot_segment_id_is_refused_before_anything_is_sent(call, value):
    """Warning: ``.../attachments/..`` would resolve to the ticket's attachment list."""
    client, rec = make_client(json_handler({}))

    with pytest.raises(ValueError, match="one path segment"):
        call(client, value)

    assert rec.requests == []


def test_the_dot_segment_hazard_is_real_for_an_unencoded_path():
    """Positive control: an unencoded ``..`` attachment addresses the ticket."""
    request = httpx.Request("DELETE", f"https://api.example{_B}/support/tickets/t1/attachments/..")

    assert request.url.path == f"{_B}/support/tickets/t1"


# --- returns -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.reviews.assign("r1", {}), ReviewRead),
        (lambda c: c.reviews.save_draft("r1", {}), ReviewRead),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x", "user_id": "u1", "role": "member"}))

    assert isinstance(call(client), model)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.reviews.cancel("r1"),
        lambda c: c.support.delete_attachment("t1", "a1"),
    ],
    ids=["cancel", "delete_attachment"],
)
def test_no_content_verbs_return_none(call):
    client, _ = make_client(lambda request: httpx.Response(204))

    assert call(client) is None


_ORG_READ_REFUSAL = "this operation requires the ORGANIZATION_READ privilege"


@pytest.mark.parametrize(
    "params",
    [{}, {"filter[ticket_number]": 4242}],
    ids=["whole-list", "by-number"],
)
def test_a_list_without_organization_read_raises_grant_error(params):
    """Every form of ``support.list`` answers ``403`` to a key without ``ORGANIZATION_READ``.

    The refusal is the API's own body: the platform error envelope whose
    ``message`` names the privilege. It maps to :class:`PerceivoGrantError`,
    as the method's ``Raises`` section says, with or without a ticket number.
    """
    body = {"error_code": "PCV-APIS-AUTH-0001", "message": _ORG_READ_REFUSAL}
    client, _ = make_client(json_handler(body, status=403))

    with pytest.raises(PerceivoGrantError) as info:
        client.support.list(**params)

    assert info.value.status_code == 403
    assert info.value.message == _ORG_READ_REFUSAL


# --- paging --------------------------------------------------------------------------


def test_paginate_pages_refuses_a_data_next_page():
    """A ``data``/``next`` page has no ``items``: a walk must not guess."""
    client, _ = make_client(json_handler({"data": [{"id": "r1"}], "total": 1, "next": None}))
    walker = paginate_pages(partial(client.intelligence.list_inference_requests, "i1"))

    with pytest.raises(ValueError, match="items"):
        next(walker)
