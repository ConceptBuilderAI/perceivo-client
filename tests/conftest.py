"""Shared test helpers: build a Client backed by an httpx MockTransport.

No network and no API key are required — every test drives a mock HTTP layer and
inspects the requests the client produced.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from perceivo_client import Client
from perceivo_client._transport import Transport
from perceivo_client.auth import APICredentials

BASE_URL = "https://api.test.perceivo.ai"


class RequestRecorder:
    """Records every request and serves responses from a handler function."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self.requests: list[httpx.Request] = []
        self._handler = handler

    def __call__(self, request: httpx.Request) -> httpx.Response:
        # Read the body eagerly so assertions can inspect it after the call.
        _ = request.content
        self.requests.append(request)
        return self._handler(request)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


def json_handler(payload, *, status: int = 200, headers: dict | None = None):
    """A handler that always returns the same JSON payload."""

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=payload, headers=headers or {})

    return _handler


def sequence_handler(responses: list[httpx.Response]):
    """A handler that returns queued responses in order (last repeats)."""
    box = {"i": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        i = min(box["i"], len(responses) - 1)
        box["i"] += 1
        return responses[i]

    return _handler


def make_client(
    handler: Callable[[httpx.Request], httpx.Response],
    **client_kwargs,
) -> tuple[Client, RequestRecorder]:
    """Build a Client whose HTTP layer is the given mock handler."""
    recorder = RequestRecorder(handler)
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recorder))
    client = Client(api_key="test-key", base_url=BASE_URL, http_client=http_client, **client_kwargs)
    return client, recorder


def make_transport(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    sleep=None,
    **transport_kwargs,
) -> tuple[Transport, RequestRecorder]:
    """Build a bare Transport with a mock handler and injectable sleep."""
    recorder = RequestRecorder(handler)
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recorder))
    creds = APICredentials(base_url=BASE_URL, api_key="test-key")
    transport = Transport(creds, http_client=http_client, sleep=sleep, **transport_kwargs)
    return transport, recorder


@pytest.fixture
def base_url() -> str:
    return BASE_URL
