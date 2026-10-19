"""Per-call timeouts with ``with_options``, and ``AsyncClient`` argument forwarding.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

import perceivo_client.async_client as async_client_module
from perceivo_client import AsyncClient, Client
from tests.conftest import BASE_URL, RequestRecorder, json_handler, make_client
from tests.test_transport_signing import AUDIENCE, KEY_ID, SECRET

_POOL_TIMEOUT = 5.0


def _sent_timeouts(request: httpx.Request) -> set:
    """The distinct per-phase timeouts httpx applied to ``request``."""
    return set(request.extensions["timeout"].values())


def test_with_options_sends_each_request_with_the_given_timeout():
    client, rec = make_client(json_handler({"items": [], "total": 0}))
    client.with_options(timeout=180.0).orchestrations.list()
    assert _sent_timeouts(rec.last) == {180.0}


def test_with_options_applies_to_a_signed_request():
    client, rec = make_client(
        json_handler({"items": [], "total": 0}),
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )
    client.with_options(timeout=90.0).orchestrations.list()
    assert _sent_timeouts(rec.last) == {90.0}
    assert "x-perceivo-signature" in rec.last.headers


def test_with_options_none_removes_every_limit():
    client, rec = make_client(json_handler({"items": [], "total": 0}))
    client.with_options(timeout=None).orchestrations.list()
    assert _sent_timeouts(rec.last) == {None}


def test_the_original_client_keeps_its_own_timeout():
    client, rec = make_client(json_handler({"items": [], "total": 0}))
    client.with_options(timeout=180.0)
    client.orchestrations.list()
    assert _sent_timeouts(rec.last) == {_POOL_TIMEOUT}


def test_the_derived_client_tracks_its_own_rate_limit():
    headers = {"X-RateLimit-Limit": "100", "X-RateLimit-Remaining": "99"}
    client, _ = make_client(json_handler({"items": [], "total": 0}, headers=headers))
    derived = client.with_options(timeout=60.0)
    derived.orchestrations.list()
    assert derived.rate_limit is not None
    assert client.rate_limit is None


def test_a_derived_client_starts_with_no_rate_limit_state():
    headers = {"X-RateLimit-Limit": "100", "X-RateLimit-Remaining": "99"}
    client, _ = make_client(json_handler({"items": [], "total": 0}, headers=headers))
    client.orchestrations.list()
    assert client.with_options(timeout=60.0).rate_limit is None


def test_closing_the_derived_client_leaves_the_shared_pool_open():
    client = Client(api_key="test-key", base_url=BASE_URL)
    client.with_options(timeout=60.0).close()
    assert not client._transport._client.is_closed
    client.close()
    assert client._transport._client.is_closed


def _async_client(recorder: RequestRecorder) -> AsyncClient:
    return AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(
            base_url=BASE_URL, timeout=_POOL_TIMEOUT, transport=httpx.MockTransport(recorder)
        ),
    )


def test_async_with_options_sends_each_request_with_the_given_timeout():
    recorder = RequestRecorder(json_handler({"items": [], "total": 0}))
    client = _async_client(recorder)
    asyncio.run(client.with_options(timeout=120.0).orchestrations.list())
    assert _sent_timeouts(recorder.last) == {120.0}
    asyncio.run(client.orchestrations.list())
    assert _sent_timeouts(recorder.last) == {_POOL_TIMEOUT}


def test_async_client_forwards_every_argument_to_client(monkeypatch: pytest.MonkeyPatch):
    received: dict = {}

    class _RecordingClient(Client):
        def __init__(self, **kwargs):
            received.update(kwargs)
            super().__init__(**kwargs)

    monkeypatch.setattr(async_client_module, "Client", _RecordingClient)
    http_client = httpx.Client(base_url=BASE_URL)
    settings = {
        "api_key": "test-key",
        "base_url": BASE_URL,
        "timeout": 7.5,
        "max_retries": 1,
        "backoff_factor": 0.25,
        "http_client": http_client,
        "key_id": KEY_ID,
        "signing_secret": SECRET,
        "hmac_audience": AUDIENCE,
        "bearer_token": None,
    }
    AsyncClient(**settings)
    assert received == settings


def test_async_client_timeout_reaches_the_connection_pool():
    client = AsyncClient(api_key="test-key", base_url=BASE_URL, timeout=7.5)
    assert client._sync._transport._client.timeout == httpx.Timeout(7.5)
