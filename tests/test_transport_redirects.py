"""Redirect containment for API keys and request-signing headers."""

from __future__ import annotations

import httpx
import pytest

from perceivo_client._transport import Transport
from perceivo_client.auth import APICredentials
from tests.conftest import BASE_URL, RequestRecorder, json_handler


def _credentials() -> APICredentials:
    return APICredentials(base_url=BASE_URL, api_key="redirect-secret")


def test_owned_http_client_explicitly_disables_redirects(monkeypatch):
    constructor_options: dict[str, object] = {}
    real_client = httpx.Client

    def recording_client(**kwargs):
        constructor_options.update(kwargs)
        return real_client(**kwargs)

    monkeypatch.setattr("perceivo_client._transport.httpx.Client", recording_client)
    transport = Transport(_credentials())
    try:
        assert constructor_options["follow_redirects"] is False
        assert transport._client.follow_redirects is False
    finally:
        transport.close()


def test_injected_redirecting_client_is_refused_before_any_request():
    recorder = RequestRecorder(json_handler({"ok": True}))
    credentials = _credentials()
    http_client = httpx.Client(
        base_url=BASE_URL,
        follow_redirects=True,
        transport=httpx.MockTransport(recorder),
    )
    try:
        with pytest.raises(ValueError, match="follow_redirects=False"):
            Transport(credentials, http_client=http_client)
        assert recorder.requests == []
        assert http_client.is_closed is False
    finally:
        http_client.close()
