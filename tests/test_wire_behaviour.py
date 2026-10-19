"""Requests and response shapes of the reviews, roles, runs, secrets,
service-accounts, support, threads, triggers and webhooks namespaces, held to
the bodies the API actually sends.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

import perceivo_client
from perceivo_client import webhooks
from perceivo_client.generated.models import (
    ReviewRead,
    SecretRead,
    SupportTicketDetail,
    SupportTicketSummary,
    WebhookRead,
)
from perceivo_client.resources.capabilities import (
    EvaluationRun,
    EvaluationRunPage,
    EvaluationRunStatus,
)
from perceivo_client.resources.reviews import ReviewCompletion
from perceivo_client.resources.runs import RunLogPage
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

# --- reviews.complete answers the completion, not a review record -------------

_COMPLETION = {
    "review_request": {"id": "rev-1", "status": "COMPLETED", "review_type": "approval"},
    "ready_to_resume": True,
    "workload_id": "wl-1",
    "workload_user_sub": "api_key:k1",
    "workload_orchestration_id": "orch-1",
}


def test_complete_returns_the_completed_review_and_the_resume_flag():
    client, rec = make_client(json_handler(_COMPLETION))
    got = client.reviews.complete("rev-1", {"response_data": {"approved": True}})
    assert isinstance(got, ReviewCompletion)
    assert isinstance(got.review_request, ReviewRead)
    assert got.review_request.id == "rev-1"
    assert got.review_request.status == "COMPLETED"
    assert got.ready_to_resume is True
    assert got.workload_id == "wl-1"
    assert got.workload_orchestration_id == "orch-1"
    assert json.loads(rec.last.content) == {"response_data": {"approved": True}}


def test_complete_that_released_nothing_reads_ready_to_resume_false():
    body = {**_COMPLETION, "ready_to_resume": False, "workload_id": None}
    client, _ = make_client(json_handler(body))
    got = client.reviews.complete("rev-1", {"response_data": {}})
    assert got.ready_to_resume is False
    assert got.workload_id is None


def test_start_and_complete_claims_then_returns_the_completion():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/start"):
            return httpx.Response(200, json={"id": "rev-1", "status": "IN_PROGRESS"})
        return httpx.Response(200, json=_COMPLETION)

    client, rec = make_client(handler)
    got = client.reviews.start_and_complete("rev-1", {"response_data": {}})
    assert [r.url.path for r in rec.requests] == [
        "/v1/reviews/rev-1/start",
        "/v1/reviews/rev-1/complete",
    ]
    assert got.review_request.id == "rev-1"


def test_complete_from_the_async_client_returns_the_completion():
    sync, _ = make_client(json_handler(_COMPLETION))
    got = asyncio.run(_async_from_sync(sync).reviews.complete("rev-1", {"response_data": {}}))
    assert got.review_request.id == "rev-1"
    assert got.ready_to_resume is True


# --- runs.logs answers the run-log body ---------------------------------------

_RUN_LOGS = {
    "workload_id": "wl-1",
    "entries": [
        {
            "timestamp": "2026-10-03T00:00:00Z",
            "labels": {"log_type": "error"},
            "line": '{"msg": "boom"}',
            "json": {"msg": "boom"},
        }
    ],
    "count": 1,
    "limit": 100,
    "namespace_resolved": True,
}


def test_run_logs_read_the_entries_the_api_sends():
    client, rec = make_client(json_handler(_RUN_LOGS))
    got = client.runs.logs("run-1", channel="error")
    assert isinstance(got, RunLogPage)
    assert got.count == 1
    assert got.entries[0]["line"] == '{"msg": "boom"}'
    assert got.entries[0]["json"] == {"msg": "boom"}
    assert got.workload_id == "wl-1"
    assert got.namespace_resolved is True
    assert sorted(rec.last.url.params.multi_items()) == [
        ("channel", "error"),
        ("scope", "run"),
        ("scope_id", "run-1"),
    ]


def test_run_logs_of_a_run_that_has_not_started_are_empty():
    body = {"workload_id": "wl-1", "run_id": "run-1", "entries": [], "count": 0}
    client, _ = make_client(json_handler(body))
    got = client.runs.logs("run-1")
    assert got.entries == []
    assert got.count == 0
    assert got.run_id == "run-1"


def test_run_logs_from_the_async_client_read_the_entries():
    sync, _ = make_client(json_handler(_RUN_LOGS))
    got = asyncio.run(_async_from_sync(sync).runs.logs("run-1"))
    assert got.entries[0]["labels"] == {"log_type": "error"}


# --- support: raise and amend answer the flat ticket; content is bytes ---------

_TICKET = {"id": "tk-1", "ticket_number": 42, "title": "Import rejected", "status": "open"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.support.create({"title": "Import rejected"}),
        lambda c: c.support.update("tk-1", {"priority": "high"}),
    ],
    ids=["create", "update"],
)
def test_raise_and_amend_return_the_flat_ticket_record(call):
    client, _ = make_client(json_handler(_TICKET))
    got = call(client)
    assert isinstance(got, SupportTicketSummary)
    assert got.id == "tk-1"
    assert got.ticket_number == 42
    assert got.title == "Import rejected"


def test_get_still_returns_the_detail_envelope():
    detail = {"ticket": _TICKET, "comments": [], "links": []}
    client, _ = make_client(json_handler(detail))
    got = client.support.get("tk-1")
    assert isinstance(got, SupportTicketDetail)
    assert got.ticket.id == "tk-1"


# Bytes that are not UTF-8: a decoded-text round trip cannot reproduce them.
_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe\x00\x80"


@pytest.mark.parametrize(
    ("content", "media_type"),
    [
        (_PNG, "image/png"),
        (b'{"a": 1}', "application/json"),
        (b"plain text\n", "text/plain"),
    ],
    ids=["binary", "json", "text"],
)
def test_attachment_content_returns_the_exact_bytes(content, media_type):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=content, headers={"Content-Type": media_type})

    client, rec = make_client(handler)
    got = client.support.get_attachment_content("tk-1", "att-1")
    assert isinstance(got, bytes)
    assert got == content
    assert rec.last.url.path == "/v1/support/tickets/tk-1/attachments/att-1/content"


def test_attachment_content_from_the_async_client_returns_the_exact_bytes():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_PNG, headers={"Content-Type": "image/png"})

    sync, _ = make_client(handler)
    got = asyncio.run(_async_from_sync(sync).support.get_attachment_content("tk-1", "att-1"))
    assert got == _PNG


def test_attachment_content_raises_on_an_error_response():
    client, _ = make_client(json_handler({"error": "not_found"}, status=404))
    with pytest.raises(perceivo_client.PerceivoNotFoundError):
        client.support.get_attachment_content("tk-1", "att-1")


def test_list_comments_sends_only_the_page_parameters_given():
    client, rec = make_client(json_handler([]))
    client.support.list_comments("tk-1")
    assert dict(rec.last.url.params) == {}
    client.support.list_comments("tk-1", page=2, page_size=50)
    assert dict(rec.last.url.params) == {"page": "2", "page_size": "50"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.roles.list(),
        lambda c: c.service_accounts.list(),
        lambda c: c.webhooks.list(),
        lambda c: c.webhooks.list_deliveries("wh-1"),
        lambda c: c.support.list_attachments("tk-1"),
    ],
    ids=["roles", "service_accounts", "webhooks", "deliveries", "attachments"],
)
def test_an_unpaged_list_sends_no_query_and_returns_every_item(call):
    items = [{"id": f"i{n}", "name": f"n{n}", "url": "https://x.invalid"} for n in range(30)]
    client, rec = make_client(json_handler(items))
    got = call(client)
    assert len(rec.requests) == 1
    assert rec.last.url.query == b""
    assert len(got) == 30


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.roles.list(page=2),
        lambda c: c.service_accounts.list(page_size=10),
        lambda c: c.webhooks.list(page=1),
        lambda c: c.webhooks.list_deliveries("wh-1", limit=5),
        lambda c: c.support.list_attachments("tk-1", page=1),
    ],
    ids=["roles", "service_accounts", "webhooks", "deliveries", "attachments"],
)
def test_an_unpaged_list_refuses_a_paging_parameter(call):
    client, rec = make_client(json_handler([]))
    with pytest.raises(TypeError):
        call(client)
    assert rec.requests == []


# --- secrets.list refuses a page or page_size the API would refuse -------------


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"page_size": "50"}, TypeError),
        ({"page_size": True}, TypeError),
        ({"page_size": 50.0}, TypeError),
        ({"page_size": 0}, ValueError),
        ({"page_size": 101}, ValueError),
        ({"page": "2"}, TypeError),
        ({"page": False}, TypeError),
        ({"page": 0}, ValueError),
        ({"page": 1, "page_size": "25"}, TypeError),
    ],
)
def test_secrets_list_refuses_a_bad_page_option_before_any_request(kwargs, error):
    client, rec = make_client(json_handler([]))
    with pytest.raises(error):
        client.secrets.list(**kwargs)
    assert rec.requests == []


def test_secrets_list_refuses_an_unknown_query_parameter():
    client, rec = make_client(json_handler([]))
    with pytest.raises(TypeError):
        client.secrets.list(sort_by="name")  # type: ignore[call-arg]
    assert rec.requests == []


def test_secrets_list_walks_every_page_at_the_page_size_given():
    data = [{"id": f"s{i}", "name": f"n{i}"} for i in range(120)]

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        size = int(request.url.params["page_size"])
        return httpx.Response(200, json=data[(page - 1) * size : page * size])

    client, rec = make_client(handler)
    got = client.secrets.list(page_size=50)
    assert [s.id for s in got] == [f"s{i}" for i in range(120)]
    assert all(isinstance(s, SecretRead) for s in got)
    assert len(rec.requests) == 3


# --- writes that take no body send none; a required body is required ----------


@pytest.mark.parametrize(
    ("call", "path"),
    [
        (lambda c: c.service_accounts.rotate("sa-1"), "/v1/service-accounts/sa-1/rotate"),
        (lambda c: c.service_accounts.unlock("sa-1"), "/v1/service-accounts/sa-1/unlock"),
    ],
    ids=["rotate", "unlock"],
)
def test_a_write_with_no_body_sends_no_body(call, path):
    client, rec = make_client(json_handler({"id": "x"}))
    call(client)
    assert rec.last.method == "POST"
    assert rec.last.url.path == path
    assert rec.last.content == b""
    assert "content-type" not in rec.last.headers


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.service_accounts.rotate("sa-1", {}),
        lambda c: c.service_accounts.unlock("sa-1", {}),
        lambda c: c.secrets.rotate("se-1"),
    ],
    ids=["rotate_body", "unlock_body", "secret_rotate_without_value"],
)
def test_a_body_the_operation_does_not_take_or_requires_is_refused(call):
    client, rec = make_client(json_handler({"id": "x"}))
    with pytest.raises(TypeError):
        call(client)
    assert rec.requests == []


def test_secret_rotate_sends_the_new_value():
    client, rec = make_client(json_handler({"id": "se-1", "name": "n"}))
    client.secrets.rotate("se-1", {"value": "new"})
    assert json.loads(rec.last.content) == {"value": "new"}


def test_thread_acknowledge_returns_none_whatever_the_api_answers():
    client, _ = make_client(json_handler({"unexpected": True}))
    assert client.threads.acknowledge("th-1") is None


# --- webhooks: the record's undeclared fields are readable ---------------------


def test_a_webhook_record_exposes_the_fields_every_read_returns():
    body = {
        "id": "wh-1",
        "name": "n",
        "url": "https://x.invalid",
        "organization_id": "org-1",
        "created_by_user_sub": "api_key:k1",
        "updated_at": "2026-10-03T00:00:00Z",
    }
    client, _ = make_client(json_handler(body))
    got = client.webhooks.get("wh-1")
    assert isinstance(got, WebhookRead)
    assert got.organization_id == "org-1"
    assert got.created_by_user_sub == "api_key:k1"
    assert got.updated_at == "2026-10-03T00:00:00Z"


def test_the_webhook_signature_helper_is_exported_under_its_own_name_only():
    assert perceivo_client.compute_webhook_signature is webhooks.compute_webhook_signature
    assert "compute_webhook_signature" in perceivo_client.__all__
    assert not hasattr(perceivo_client, "compute_signature")
    assert "compute_signature" not in perceivo_client.__all__


@pytest.mark.parametrize(
    "model",
    [ReviewCompletion, RunLogPage, EvaluationRun, EvaluationRunPage, EvaluationRunStatus],
)
def test_the_hand_written_response_models_are_exported_from_the_package_root(model):
    assert getattr(perceivo_client, model.__name__) is model
    assert model.__name__ in perceivo_client.__all__


def test_secrets_list_with_a_page_alone_leaves_the_page_size_to_the_api():
    client, rec = make_client(json_handler([{"id": "s1", "name": "n"}]))
    got = client.secrets.list(page=3)
    assert [s.id for s in got] == ["s1"]
    assert dict(rec.last.url.params) == {"page": "3"}
