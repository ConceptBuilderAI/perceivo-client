"""Log reads call ``GET /v1/logs`` with the id in the query; ``secrets.list`` walks pages.

An intelligence's error and extension logs are ``client.query.logs`` with
``scope="intelligence"`` and the channel; ``client.runs.logs`` is bound to one
run.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from perceivo_client import AsyncClient
from perceivo_client.generated.models import SecretRead
from tests.conftest import json_handler, make_client

_LOG_BODY = {"scope": "intelligence", "channel": "error", "logs": [{"line": "x"}]}
#: What ``GET /v1/logs`` answers for ``scope=intelligence``: an items page, not
#: the published ``LogPage``.
_INTELLIGENCE_BODY = {"items": [{"line": "x"}], "total": 1, "pagination": {"count": 1}}


# (call, exact query pairs). Path is always /v1/logs and the method GET.
LOG_CASES = [
    (
        lambda c: c.query.logs("intelligence", scope_id="intel-1", channel="error"),
        [("channel", "error"), ("scope", "intelligence"), ("scope_id", "intel-1")],
    ),
    (
        lambda c: c.query.logs("intelligence", scope_id="intel-1", channel="extension"),
        [("channel", "extension"), ("scope", "intelligence"), ("scope_id", "intel-1")],
    ),
    (
        lambda c: c.query.logs(
            "intelligence",
            scope_id="intel-1",
            channel="extension",
            level="ERROR",
            start="2026-10-01",
        ),
        [
            ("channel", "extension"),
            ("from", "2026-10-01"),
            ("level", "ERROR"),
            ("scope", "intelligence"),
            ("scope_id", "intel-1"),
        ],
    ),
]
_IDS = [
    "intelligence-error-channel",
    "intelligence-extension-channel",
    "intelligence-extension-filters",
]


def _assert_log_request(request: httpx.Request, expected: list[tuple[str, str]]) -> None:
    assert request.method == "GET"
    assert request.url.path == "/v1/logs"
    assert sorted(request.url.params.multi_items()) == expected
    assert request.content == b""


@pytest.mark.parametrize(("call", "expected"), LOG_CASES, ids=_IDS)
def test_log_wrapper_sends_exact_request_sync(call, expected):
    client, rec = make_client(json_handler(_INTELLIGENCE_BODY))
    result = call(client)
    assert len(rec.requests) == 1
    _assert_log_request(rec.last, expected)
    assert result == _INTELLIGENCE_BODY


def _async_from_sync(sync):
    from perceivo_client.async_client import _NAMESPACES, _AsyncNamespace

    aclient = AsyncClient.__new__(AsyncClient)
    aclient._sync = sync
    for namespace in _NAMESPACES:
        setattr(aclient, namespace, _AsyncNamespace(getattr(sync, namespace)))
    return aclient


@pytest.mark.parametrize(("call", "expected"), LOG_CASES, ids=_IDS)
def test_log_wrapper_sends_exact_request_async(call, expected):
    sync, rec = make_client(json_handler(_INTELLIGENCE_BODY))
    aclient = _async_from_sync(sync)
    result = asyncio.run(call(aclient))
    assert len(rec.requests) == 1
    _assert_log_request(rec.last, expected)
    assert result == _INTELLIGENCE_BODY


@pytest.mark.parametrize(
    ("call", "owned"),
    [
        (lambda c: c.runs.logs("r", scope="intelligence"), "scope"),
        (lambda c: c.runs.logs("r", scope_id="other"), "scope_id"),
    ],
)
def test_log_wrapper_refuses_to_override_its_own_selectors(call, owned):
    client, rec = make_client(json_handler(_LOG_BODY))
    with pytest.raises(TypeError, match=owned):
        call(client)
    assert rec.requests == []


def test_log_wrapper_sends_a_slash_id_as_a_query_value_not_a_path():
    client, rec = make_client(json_handler(_LOG_BODY))
    client.runs.logs("a/../b")
    assert rec.last.url.path == "/v1/logs"
    assert rec.last.url.params["scope_id"] == "a/../b"


def test_log_wrapper_refuses_an_empty_id():
    client, rec = make_client(json_handler(_LOG_BODY))
    with pytest.raises(ValueError, match="must not be empty"):
        client.runs.logs("")
    assert rec.requests == []


# --- secrets.list ---------------------------------------------------------------


def _secrets(n: int) -> list[dict]:
    return [{"id": f"s{i}", "name": f"n{i}"} for i in range(n)]


def _paged_secrets_handler(total: int):
    """Page/page_size honoured, plain array, default 25."""
    data = _secrets(total)

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        size = int(request.url.params.get("page_size", "25"))
        if size > 100:
            return httpx.Response(422, json={"detail": "page_size"})
        start = (page - 1) * size
        return httpx.Response(200, json=data[start : start + size])

    return handler


def _unpaged_secrets_handler(total: int):
    """Page/page_size ignored, every page is the whole list."""
    return json_handler(_secrets(total))


@pytest.mark.parametrize("total", [0, 26, 99, 100, 101, 237])
def test_secrets_list_returns_every_secret_across_pages(total):
    client, rec = make_client(_paged_secrets_handler(total))
    got = client.secrets.list()
    assert [s.id for s in got] == [f"s{i}" for i in range(total)]
    assert all(isinstance(s, SecretRead) for s in got)
    # page_size 100 on every request; one request past the last full page.
    assert [dict(r.url.params) for r in rec.requests] == [
        {"page": str(p), "page_size": "100"} for p in range(1, total // 100 + 2)
    ]


def test_secrets_list_walks_more_than_25_at_a_small_page_size():
    client, rec = make_client(_paged_secrets_handler(60))
    got = client.secrets.list(page_size=25)
    assert [s.id for s in got] == [f"s{i}" for i in range(60)]
    assert [r.url.params["page"] for r in rec.requests] == ["1", "2", "3"]
    assert {r.url.params["page_size"] for r in rec.requests} == {"25"}


def test_secrets_list_async_walks_pages():
    sync, rec = make_client(_paged_secrets_handler(130))
    aclient = _async_from_sync(sync)
    got = asyncio.run(aclient.secrets.list())
    assert len(got) == 130
    assert len(rec.requests) == 2


@pytest.mark.parametrize("total", [3, 100, 250])
def test_secrets_list_on_an_unpaged_server_returns_the_list_once(total):
    client, rec = make_client(_unpaged_secrets_handler(total))
    got = client.secrets.list()
    assert [s.id for s in got] == [f"s{i}" for i in range(total)]
    # 100 exactly: page 2 repeats page 1, adds no new id, and ends the walk.
    assert len(rec.requests) == (2 if total == 100 else 1)


def test_secrets_list_with_page_returns_that_page_only():
    client, rec = make_client(_paged_secrets_handler(60))
    got = client.secrets.list(page=2, page_size=25)
    assert [s.id for s in got] == [f"s{i}" for i in range(25, 50)]
    assert len(rec.requests) == 1
    assert dict(rec.last.url.params) == {"page": "2", "page_size": "25"}
