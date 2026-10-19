"""Runtime control and query: operations, run controls, ``filter[...]`` spellings,
pagination, typed returns and async parity."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.async_client import _NAMESPACES
from perceivo_client.generated.models import (
    AlertChannelRead,
    AlertRuleCatalog,
    AlertRuleRead,
    AlertRuleTestResult,
    AssetSearchResponse,
    EventPage,
    MetricSeries,
    Operation,
    OperationPage,
    RunControlResult,
    RunEvents,
    RunPage,
    RunSteps,
    WebhookEventTypeRead,
)
from tests.conftest import BASE_URL, json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync, _page_total_handler

_RUNS = "/v1/orchestrations/runs"
_RUNTIME = ("operations", "query", "alert_channels", "alert_rules")

_OPERATION = {
    "id": "op-7f3a",
    "kind": "operation",
    "status": "running",
    "created_at": "2026-10-03T00:00:00Z",
    "poll": "/v1/operations/op-7f3a",
}


def _routed(routes: dict[tuple[str, str], dict]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=routes[(request.method, request.url.path)])

    return handler


# --- operations.get reads one operation by id -----------------------------------


def test_operations_get_reads_the_operation_by_id():
    client, rec = make_client(json_handler(_OPERATION))

    operation = client.operations.get("op-7f3a")

    assert isinstance(operation, Operation)
    assert rec.last.method == "GET"
    assert rec.last.url.path == "/v1/operations/op-7f3a"
    assert operation.id == "op-7f3a"


def test_operations_cancel_posts_no_body_to_the_operation():
    client, rec = make_client(json_handler(_OPERATION))

    got = client.operations.cancel("op-7f3a")

    assert isinstance(got, Operation)
    assert rec.last.method == "POST"
    assert rec.last.url.path == "/v1/operations/op-7f3a/cancel"
    assert rec.last.content == b""


# --- run controls hit the exact paths ----------------------------------------


@pytest.mark.parametrize(
    "verb,call",
    [
        ("pause", lambda c: c.runs.pause("r-42")),
        ("resume", lambda c: c.runs.resume("r-42")),
        ("stop", lambda c: c.runs.stop("r-42")),
    ],
)
def test_run_controls_post_to_their_exact_path_with_no_body(verb, call):
    client, rec = make_client(json_handler({"run_id": "r-42", "action": verb}))

    got = call(client)

    assert isinstance(got, RunControlResult)
    assert len(rec.requests) == 1
    assert rec.last.method == "POST"
    assert str(rec.last.url) == f"{BASE_URL.rstrip('/')}{_RUNS}/r-42/{verb}"
    assert rec.last.content == b""


def test_run_controls_do_not_reach_the_cancel_route():
    client, rec = make_client(json_handler({}))

    client.runs.pause("r1")
    client.runs.resume("r1")
    client.runs.stop("r1")

    paths = [r.url.path for r in rec.requests]
    assert paths == [f"{_RUNS}/r1/pause", f"{_RUNS}/r1/resume", f"{_RUNS}/r1/stop"]


@pytest.mark.parametrize(
    "call,suffix,model",
    [
        (lambda c: c.runs.events("r1"), "/r1/events", RunEvents),
        (lambda c: c.runs.steps("r1"), "/r1/steps", RunSteps),
    ],
)
def test_run_reads_are_typed_gets(call, suffix, model):
    client, rec = make_client(json_handler({"run_id": "r1"}))

    got = call(client)

    assert isinstance(got, model)
    assert rec.last.method == "GET"
    assert rec.last.url.path == f"{_RUNS}{suffix}"


# --- filter[...] spellings and required query parameters --------------------


@pytest.mark.parametrize(
    "call,path,expected",
    [
        (lambda c: c.runs.list(status="RUNNING"), _RUNS, {"filter[status]": "RUNNING"}),
        (
            lambda c: c.operations.list(status="queued"),
            "/v1/operations",
            {"filter[status]": "queued"},
        ),
        (
            lambda c: c.query.events(event_type="org.member.added"),
            "/v1/events",
            {"filter[event_type]": "org.member.added"},
        ),
    ],
)
def test_filter_keywords_are_sent_in_bracket_form(call, path, expected):
    client, rec = make_client(json_handler({}))

    call(client)

    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == expected


@pytest.mark.parametrize(
    "call,path",
    [
        (lambda c: c.runs.list(), _RUNS),
        (lambda c: c.operations.list(), "/v1/operations"),
        (lambda c: c.query.events(), "/v1/events"),
        (lambda c: c.query.search(), "/v1/search"),
    ],
)
def test_unfiltered_lists_send_no_query(call, path):
    client, rec = make_client(json_handler({}))

    call(client)

    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == {}


def test_logs_sends_scope_id_only_when_given():
    client, rec = make_client(json_handler({}))

    client.query.logs("organization")
    bare = dict(rec.last.url.params)
    client.query.logs("run", scope_id="r1", channel="stdout")

    assert bare == {"scope": "organization"}
    assert dict(rec.last.url.params) == {"scope": "run", "scope_id": "r1", "channel": "stdout"}


def test_logs_sends_the_window_as_from_and_to():
    client, rec = make_client(json_handler({}))

    client.query.logs("organization", start="2026-10-01", end="2026-10-02")

    assert rec.last.url.params["from"] == "2026-10-01"
    assert rec.last.url.params["to"] == "2026-10-02"


def test_metrics_sends_subject_and_subject_id():
    client, rec = make_client(json_handler({}))

    client.query.metrics("intelligence", "i1", series="latency_p95")

    assert rec.last.url.path == "/v1/metrics"
    assert dict(rec.last.url.params) == {
        "subject": "intelligence",
        "subject_id": "i1",
        "series": "latency_p95",
    }


# --- pagination ---------------------------------------------------------------


@pytest.mark.parametrize("path", ["query.search"])
def test_paginate_pages_walks_the_items_total_lists(path):
    namespace, method = path.split(".")
    client, rec = make_client(_page_total_handler(60))

    got = list(paginate_pages(getattr(getattr(client, namespace), method), page_size=25))

    assert got == list(range(60))
    assert [dict(r.url.params) for r in rec.requests] == [
        {"page": "1", "page_size": "25"},
        {"page": "2", "page_size": "25"},
        {"page": "3", "page_size": "25"},
    ]


@pytest.mark.parametrize("path", ["query.search"])
def test_async_paginate_pages_walks_the_items_total_lists(path):
    namespace, method = path.split(".")
    sync, rec = make_client(_page_total_handler(30))
    client = _async_from_sync(sync)

    async def collect():
        fetch = getattr(getattr(client, namespace), method)
        return [item async for item in client.paginate_pages(fetch, page_size=20)]

    assert asyncio.run(collect()) == list(range(30))
    assert len(rec.requests) == 2


def _runs_page_handler():
    """In the served ``list_runs`` shape, ``total`` counts the runs in one page."""

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        size = int(request.url.params["page_size"])
        start = (page - 1) * size
        items = [{"run_id": f"r{i}"} for i in range(start, min(start + size, 75))]
        return httpx.Response(200, json={"items": items, "total": len(items)})

    return handler


def test_paginate_pages_refuses_runs_list_instead_of_stopping_after_page_one():
    client, rec = make_client(_runs_page_handler())
    walker = paginate_pages(client.runs.list, page_size=25)

    with pytest.raises(ValueError, match=r"refuses runs\.list"):
        next(walker)

    assert len(rec.requests) == 1


def test_paginate_pages_refuses_runs_list_behind_a_wrapper():
    """The refusal reads the response type, so a lambda around the method is caught."""
    client, _ = make_client(_runs_page_handler())
    walker = paginate_pages(lambda **kw: client.runs.list(status="RUNNING", **kw))

    with pytest.raises(ValueError, match=r"refuses runs\.list"):
        next(walker)


def test_async_paginate_pages_refuses_runs_list():
    sync, rec = make_client(_runs_page_handler())
    client = _async_from_sync(sync)

    async def collect():
        return [item async for item in client.paginate_pages(client.runs.list, page_size=25)]

    with pytest.raises(ValueError, match=r"refuses runs\.list"):
        asyncio.run(collect())
    assert len(rec.requests) == 1


def test_runs_list_pages_by_hand_until_a_short_page():
    """The documented manual walk reaches every run the refusal protects."""
    client, rec = make_client(_runs_page_handler())
    seen, page = [], 1
    while True:
        got = client.runs.list(page=page, page_size=25)
        seen.extend(r.run_id for r in got.items)
        if len(got.items) < 25:
            break
        page += 1

    assert seen == [f"r{i}" for i in range(75)]
    assert len(rec.requests) == 4


def test_operations_list_walks_its_cursor():
    pages = [
        {"items": [_OPERATION], "next": "c2"},
        {"items": [dict(_OPERATION, id="op-2")]},
    ]
    state = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = pages[state["i"]]
        state["i"] += 1
        return httpx.Response(200, json=body)

    client, rec = make_client(handler)

    first = client.operations.list(page_size=1)
    second = client.operations.list(page_size=1, cursor=first.next)

    assert isinstance(first, OperationPage)
    assert [op.id for op in first.items + second.items] == ["op-7f3a", "op-2"]
    assert second.next is None
    assert dict(rec.requests[0].url.params) == {"page_size": "1"}
    assert dict(rec.requests[1].url.params) == {"page_size": "1", "cursor": "c2"}


def test_events_forwards_its_page_parameters():
    client, rec = make_client(json_handler({"events": [], "has_more": False}))

    page = client.query.events(page=2, page_size=50, sort="occurred_at")

    assert isinstance(page, EventPage)
    assert dict(rec.last.url.params) == {"page": "2", "page_size": "50", "sort": "occurred_at"}


@pytest.mark.parametrize(
    "call,path,model",
    [
        (lambda c: c.alert_channels.list(), "/v1/alert-channels", AlertChannelRead),
        (lambda c: c.alert_rules.list(), "/v1/alert-rules", AlertRuleRead),
        (
            lambda c: c.webhooks.list_event_types(),
            "/v1/webhooks/event-types",
            WebhookEventTypeRead,
        ),
    ],
)
def test_unpaged_lists_return_the_whole_typed_array_in_one_request(call, path, model):
    client, rec = make_client(json_handler([{"id": "a"}, {"id": "b"}, {"id": "c"}]))

    got = call(client)

    assert len(rec.requests) == 1
    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == {}
    assert len(got) == 3
    assert all(isinstance(item, model) for item in got)


# --- typed returns and bodies --------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.runs.list(), RunPage),
        (lambda c: c.query.metrics("capability", "c1"), MetricSeries),
        (lambda c: c.query.search(q="x"), AssetSearchResponse),
        (lambda c: c.alert_channels.create({"name": "n"}), AlertChannelRead),
        (lambda c: c.alert_channels.get("ch1"), AlertChannelRead),
        (lambda c: c.alert_channels.update("ch1", {}), AlertChannelRead),
        (lambda c: c.alert_rules.create({"name": "n"}), AlertRuleRead),
        (lambda c: c.alert_rules.get("r1"), AlertRuleRead),
        (lambda c: c.alert_rules.update("r1", {}), AlertRuleRead),
        (lambda c: c.alert_rules.get_catalog(), AlertRuleCatalog),
        (lambda c: c.alert_rules.test("r1"), AlertRuleTestResult),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x"}))

    assert isinstance(call(client), model)


def test_alert_rule_test_without_a_payload_sends_no_body():
    client, rec = make_client(json_handler({}))

    client.alert_rules.test("r1")

    assert rec.last.content == b""


def test_alert_rule_test_with_a_payload_sends_it():
    client, rec = make_client(json_handler({}))

    client.alert_rules.test("r1", {"event_type": "training.job.failed"})

    assert json.loads(rec.last.content) == {"event_type": "training.job.failed"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.alert_channels.delete("ch1"),
        lambda c: c.alert_rules.delete("r1"),
    ],
)
def test_no_content_deletes_return_none(call):
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert call(client) is None
    assert rec.last.method == "DELETE"


def test_usage_report_is_not_wrapped():
    """``GET /usage`` reads billing data and is not wrapped."""
    client, _ = make_client(json_handler({}))

    assert not hasattr(client.query, "usage")


# --- async parity ------------------------------------------------------------


@pytest.mark.parametrize("namespace", _RUNTIME)
def test_runtime_namespaces_are_mirrored_on_the_async_client(namespace):
    assert namespace in _NAMESPACES


def test_async_run_control_awaits_and_hits_the_exact_path():
    sync, rec = make_client(json_handler({"run_id": "r1"}))
    client = _async_from_sync(sync)

    got = asyncio.run(client.runs.pause("r1"))

    assert isinstance(got, RunControlResult)
    assert rec.last.url.path == f"{_RUNS}/r1/pause"


def test_async_operation_get_reads_the_operation_by_id():
    sync, rec = make_client(json_handler(_OPERATION))
    client = _async_from_sync(sync)

    operation = asyncio.run(client.operations.get("op-7f3a"))

    assert operation.id == "op-7f3a"
    assert rec.last.url.path == "/v1/operations/op-7f3a"
