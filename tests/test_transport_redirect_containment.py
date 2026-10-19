"""A driven 3xx does not move the credential to a second origin.

The mock answers the first origin with a 3xx pointing at a second origin, and the
tests assert the second origin received nothing, on both the unsigned and the
signed send paths.
"""

from __future__ import annotations

import httpx
import pytest

from perceivo_client._transport import Transport
from perceivo_client.auth import APICredentials
from perceivo_client.signing import RequestSigner, SigningCredentials
from tests.conftest import BASE_URL

FIRST_ORIGIN = BASE_URL
FIRST_ORIGIN_HOST = httpx.URL(BASE_URL).host
SECOND_ORIGIN = "https://redirect-target.example.net"
SECOND_ORIGIN_HOST = "redirect-target.example.net"

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "redirect-containment-signing-secret"
AUDIENCE = "perceivo-api-local"

# 308 preserves the method and the body, so following it would replay a mutation.
REDIRECT_STATUSES = [301, 302, 303, 307, 308]

CREDENTIAL_HEADERS = ("x-api-key",)
SIGNATURE_HEADER_PREFIX = "x-perceivo-"


class OriginRecorder:
    """Serves a redirect from the first origin and 200 from the second."""

    def __init__(self, *, status: int, location: str) -> None:
        self.requests: list[httpx.Request] = []
        self._status = status
        self._location = location

    def __call__(self, request: httpx.Request) -> httpx.Response:
        _ = request.content
        self.requests.append(request)
        if request.url.host == SECOND_ORIGIN_HOST:
            # Reachable only if the client followed the redirect.
            return httpx.Response(200, json={"followed": True})
        return httpx.Response(self._status, headers={"Location": self._location})

    def hosts(self) -> list[str]:
        return [request.url.host for request in self.requests]

    def second_origin_requests(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.url.host == SECOND_ORIGIN_HOST]


def credential_headers(request: httpx.Request) -> dict[str, str]:
    """Every auth-bearing header on one request, lower-cased."""
    found = {}
    for name, value in request.headers.items():
        lowered = name.lower()
        if lowered in CREDENTIAL_HEADERS or lowered.startswith(SIGNATURE_HEADER_PREFIX):
            found[lowered] = value
    return found


def build_transport(recorder: OriginRecorder, *, signer: RequestSigner | None = None) -> Transport:
    http_client = httpx.Client(
        base_url=FIRST_ORIGIN,
        transport=httpx.MockTransport(recorder),
    )
    credentials = APICredentials(base_url=FIRST_ORIGIN, api_key="redirect-containment-key")
    return Transport(
        credentials,
        http_client=http_client,
        sleep=lambda _seconds: None,
        signer=signer,
    )


def make_signer() -> RequestSigner:
    return RequestSigner(
        SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    )


def assert_contained(recorder: OriginRecorder, *, status: int, response: httpx.Response) -> None:
    """The redirect was surfaced, not followed, and nothing reached origin two."""
    assert recorder.hosts() == [FIRST_ORIGIN_HOST], recorder.hosts()
    assert recorder.second_origin_requests() == []
    assert response.status_code == status
    assert response.headers["Location"].startswith(SECOND_ORIGIN)
    # The credential was sent once, to the configured origin.
    only = recorder.requests[0]
    assert only.url.host == FIRST_ORIGIN_HOST
    assert credential_headers(only)


@pytest.mark.parametrize("status", REDIRECT_STATUSES)
def test_cross_origin_redirect_is_not_followed_unsigned(status: int):
    recorder = OriginRecorder(status=status, location=f"{SECOND_ORIGIN}/v1/orchestrations")
    transport = build_transport(recorder)
    try:
        response = transport.request("GET", "/v1/orchestrations")
    finally:
        transport.close()

    assert_contained(recorder, status=status, response=response)
    assert "x-api-key" in credential_headers(recorder.requests[0])


@pytest.mark.parametrize("status", REDIRECT_STATUSES)
def test_cross_origin_redirect_is_not_followed_when_signing(status: int):
    recorder = OriginRecorder(status=status, location=f"{SECOND_ORIGIN}/v1/orchestrations")
    transport = build_transport(recorder, signer=make_signer())
    try:
        response = transport.request(
            "POST",
            "/v1/orchestrations",
            json={"name": "redirect-containment"},
        )
    finally:
        transport.close()

    assert_contained(recorder, status=status, response=response)
    signed = credential_headers(recorder.requests[0])
    assert "x-api-key" in signed
    assert [name for name in signed if name.startswith(SIGNATURE_HEADER_PREFIX)]


def test_no_signature_or_api_key_header_ever_reaches_the_redirect_target():
    """The census form: over *every* request the transport made, group by host."""
    recorder = OriginRecorder(status=302, location=f"{SECOND_ORIGIN}/v1/runs")
    transport = build_transport(recorder, signer=make_signer())
    try:
        transport.request("GET", "/v1/runs")
        transport.request("POST", "/v1/runs", json={"orchestration_id": "orc-1"})
    finally:
        transport.close()

    assert len(recorder.requests) == 2
    leaked = {
        request.url.host: credential_headers(request)
        for request in recorder.requests
        if request.url.host != FIRST_ORIGIN_HOST and credential_headers(request)
    }
    assert leaked == {}
    # The credential headers are present on the requests that were made.
    assert all(credential_headers(request) for request in recorder.requests)


def test_same_origin_redirect_is_also_surfaced_rather_than_followed():
    """Containment is not host-conditional: no 3xx is followed, same origin included."""
    recorder = OriginRecorder(status=307, location=f"{FIRST_ORIGIN}/v1/orchestrations/moved")
    transport = build_transport(recorder)
    try:
        response = transport.request("GET", "/v1/orchestrations")
    finally:
        transport.close()

    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == "/v1/orchestrations"
    assert response.status_code == 307
    assert response.headers["Location"].endswith("/v1/orchestrations/moved")


def test_redirect_is_not_treated_as_a_retryable_status():
    """A 3xx must not enter the GET retry loop and re-send the credential."""
    recorder = OriginRecorder(status=302, location=f"{SECOND_ORIGIN}/v1/runs")
    slept: list[float] = []
    http_client = httpx.Client(base_url=FIRST_ORIGIN, transport=httpx.MockTransport(recorder))
    credentials = APICredentials(base_url=FIRST_ORIGIN, api_key="redirect-containment-key")
    transport = Transport(
        credentials,
        http_client=http_client,
        sleep=slept.append,
        max_retries=3,
    )
    try:
        response = transport.request("GET", "/v1/runs")
    finally:
        transport.close()

    assert slept == []
    assert len(recorder.requests) == 1
    assert response.status_code == 302
