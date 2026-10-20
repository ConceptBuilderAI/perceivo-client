"""Bearer (Entra) authentication mode on the Client.

These are offline tests: every request is served by an httpx ``MockTransport``,
and the assertions read the headers the client actually produced. The four
properties the mode must hold:

1. **Mode selection.** A bearer token is mutually exclusive with the API-key and
   HMAC inputs; configuring more than one raises at construction, none still
   raises the missing-credential error.
2. **Header shape.** Bearer mode sends ``Authorization: Bearer <token>`` and
   never ``X-API-Key`` or an HMAC signature header.
3. **Per-request refresh.** A callable token source is invoked once per request,
   so a refreshing caller's current token is always the one sent, and the client
   caches nothing.
4. **Error mapping.** A ``401`` is raised as ``PerceivoAuthError``, the same type
   the API-key mode raises.
"""

from __future__ import annotations

import httpx
import pytest

from perceivo_client import (
    AmbiguousCredentialsError,
    AsyncClient,
    BearerCredentials,
    Client,
    MissingCredentialsError,
    PerceivoAuthError,
)
from tests.conftest import BASE_URL, RequestRecorder, json_handler

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "bearer-test-signing-secret"
AUDIENCE = "perceivo-api-local"


def bearer_client(bearer_token, handler=None, **client_kwargs) -> tuple[Client, RequestRecorder]:
    """A Client in bearer mode whose HTTP layer is a mock handler."""
    recorder = RequestRecorder(handler or json_handler({"ok": True}))
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recorder))
    client = Client(
        bearer_token=bearer_token, base_url=BASE_URL, http_client=http_client, **client_kwargs
    )
    return client, recorder


# -- mode selection --------------------------------------------------------


def test_bearer_token_is_mutually_exclusive_with_api_key():
    with pytest.raises(AmbiguousCredentialsError, match="api_key"):
        Client(bearer_token="t", api_key="k", base_url=BASE_URL)


def test_bearer_token_is_mutually_exclusive_with_hmac_pair():
    with pytest.raises(AmbiguousCredentialsError, match="key_id"):
        Client(bearer_token="t", key_id=KEY_ID, signing_secret=SECRET, base_url=BASE_URL)


def test_bearer_token_is_mutually_exclusive_with_hmac_audience_alone():
    with pytest.raises(AmbiguousCredentialsError, match="hmac_audience"):
        Client(bearer_token="t", hmac_audience=AUDIENCE, base_url=BASE_URL)


def test_ambiguous_credentials_error_is_a_perceivo_error():
    from perceivo_client import PerceivoError

    assert issubclass(AmbiguousCredentialsError, PerceivoError)


def test_empty_bearer_token_string_raises_missing_credentials():
    with pytest.raises(MissingCredentialsError):
        Client(bearer_token="", base_url=BASE_URL)


def test_whitespace_only_bearer_token_string_raises_missing_credentials():
    with pytest.raises(MissingCredentialsError):
        Client(bearer_token="   ", base_url=BASE_URL)


def test_non_string_non_callable_bearer_token_raises_type_error():
    with pytest.raises(TypeError):
        Client(bearer_token=123, base_url=BASE_URL)  # type: ignore[arg-type]


def test_callable_returning_empty_token_raises_at_request_time():
    client, _ = bearer_client(lambda: "")
    with pytest.raises(MissingCredentialsError):
        client._transport.request("GET", "/v1/whoami")


def test_callable_returning_whitespace_token_raises_at_request_time():
    client, _ = bearer_client(lambda: "   ")
    with pytest.raises(MissingCredentialsError):
        client._transport.request("GET", "/v1/whoami")


# -- header shape ----------------------------------------------------------


def test_bearer_mode_sends_authorization_bearer_header():
    client, recorder = bearer_client("tok-123")
    client._transport.request("GET", "/v1/whoami")
    assert recorder.last.headers["Authorization"] == "Bearer tok-123"


def test_bearer_mode_sends_no_api_key_header():
    client, recorder = bearer_client("tok-123")
    client._transport.request("GET", "/v1/whoami")
    assert "X-API-Key" not in recorder.last.headers


def test_bearer_mode_sends_no_signature_header():
    client, recorder = bearer_client("tok-123")
    client._transport.request("GET", "/v1/whoami")
    # No HMAC signature headers in bearer mode.
    assert not any(name.lower().startswith("x-perceivo-") for name in recorder.last.headers)


def test_bearer_mode_transport_has_no_signer():
    client, _ = bearer_client("tok-123")
    assert client._transport.signing_enabled is False


# -- per-request refresh ---------------------------------------------------


def test_callable_token_is_invoked_once_per_request():
    tokens = iter(["first", "second", "third"])
    calls = {"n": 0}

    def source() -> str:
        calls["n"] += 1
        return next(tokens)

    client, recorder = bearer_client(source)
    client._transport.request("GET", "/v1/whoami")
    client._transport.request("GET", "/v1/whoami")

    assert calls["n"] == 2
    assert recorder.requests[0].headers["Authorization"] == "Bearer first"
    assert recorder.requests[1].headers["Authorization"] == "Bearer second"


def test_static_token_is_sent_verbatim_on_every_request():
    client, recorder = bearer_client("static-tok")
    client._transport.request("GET", "/v1/whoami")
    client._transport.request("GET", "/v1/whoami")
    assert [r.headers["Authorization"] for r in recorder.requests] == [
        "Bearer static-tok",
        "Bearer static-tok",
    ]


# -- error mapping ---------------------------------------------------------


def test_bearer_mode_401_maps_to_perceivo_auth_error():
    client, _ = bearer_client("tok-123", handler=json_handler({"code": "PCV_AUTH"}, status=401))
    with pytest.raises(PerceivoAuthError):
        client._transport.request("GET", "/v1/whoami")


# -- credential object -----------------------------------------------------


def test_bearer_credentials_repr_redacts_the_token():
    creds = BearerCredentials(base_url=BASE_URL, token_source="super-secret-token")
    text = repr(creds)
    assert "super-secret-token" not in text
    assert "redacted" in text


def test_bearer_credentials_auth_headers_resolve_callable():
    creds = BearerCredentials(base_url=BASE_URL, token_source=lambda: "dynamic")
    assert creds.auth_headers() == {"Authorization": "Bearer dynamic"}


# -- regression: api-key and async parity ----------------------------------


def test_api_key_mode_is_unaffected():
    recorder = RequestRecorder(json_handler({"ok": True}))
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recorder))
    client = Client(api_key="a-key", base_url=BASE_URL, http_client=http_client)
    client._transport.request("GET", "/v1/whoami")
    assert recorder.last.headers["X-API-Key"] == "a-key"
    assert "Authorization" not in recorder.last.headers


def test_async_client_accepts_bearer_token_and_sends_it():
    recorder = RequestRecorder(json_handler({"ok": True}))
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recorder))
    aclient = AsyncClient(bearer_token="async-tok", base_url=BASE_URL, http_client=http_client)
    # The async client wraps a sync Client; drive its transport directly.
    aclient._sync._transport.request("GET", "/v1/whoami")
    assert recorder.last.headers["Authorization"] == "Bearer async-tok"
    assert "X-API-Key" not in recorder.last.headers
