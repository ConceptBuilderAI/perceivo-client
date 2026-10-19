"""Uploads and ingests wait longer than the client's default timeout.

The default bounds each read at 30 s, which a 10 MiB upload or an ingest that
chunks and embeds a document can exceed while the API is still working. These
five calls raise read and write to at least 150 s, keep a longer timeout the
caller asked for, and never bound a call the caller left unbounded.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import httpx
import pytest

from perceivo_client import Client
from tests.conftest import BASE_URL

_ID = "5b1f6c1e-3a0b-4b56-9d6e-0d2c1c1a7a10"

_CALLS = [
    lambda c: c.files.upload(_ID, "rows.csv", b"a,b\n"),
    lambda c: c.files.replace_content(_ID, b"a,b\n"),
    lambda c: c.infrastructure.ingest_search_index("docs", "a.txt", b"text"),
    lambda c: c.infrastructure.ingest_vector_store_collection("docs", "a.txt", b"text"),
    lambda c: c.infrastructure.ingest_cache("docs", "a.txt", b"text"),
]
_IDS = ["upload", "replace_content", "ingest_search_index", "ingest_vector_store", "ingest_cache"]


class _Sent(Exception):
    """Raised by the handler once the request is captured; nothing is answered."""


def _client(timeout: float | None) -> tuple[Client, list[dict]]:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.extensions["timeout"])
        raise _Sent

    # The pool timeout is the one Client() builds its own pool with.
    http_client = httpx.Client(
        base_url=BASE_URL, transport=httpx.MockTransport(handler), timeout=timeout
    )
    return Client(api_key="test-key", base_url=BASE_URL, http_client=http_client), seen


@pytest.mark.parametrize("call", _CALLS, ids=_IDS)
def test_a_long_call_on_a_default_client_waits_at_least_150_s(call):
    client, seen = _client(30.0)
    with pytest.raises(_Sent):
        call(client)
    assert seen[0]["read"] == 150.0
    assert seen[0]["write"] == 150.0
    assert seen[0]["connect"] == 30.0


@pytest.mark.parametrize("call", _CALLS, ids=_IDS)
def test_a_longer_timeout_the_caller_set_is_kept(call):
    client, seen = _client(30.0)
    with pytest.raises(_Sent):
        call(client.with_options(timeout=300.0))
    assert seen[0]["read"] == 300.0
    assert seen[0]["write"] == 300.0


@pytest.mark.parametrize("call", _CALLS, ids=_IDS)
def test_an_unbounded_client_stays_unbounded(call):
    client, seen = _client(None)
    with pytest.raises(_Sent):
        call(client)
    assert seen[0]["read"] is None
    assert seen[0]["write"] is None


def test_an_ordinary_call_keeps_the_default():
    client, seen = _client(30.0)
    with pytest.raises(_Sent):
        client.files.get_space(_ID)
    assert seen[0]["read"] == 30.0
