"""Client and AsyncClient wiring for HMAC signing."""

from __future__ import annotations

import httpx
import pytest

from perceivo_client import AsyncClient, Client
from perceivo_client.signing import (
    HEADER_KEY_ID,
    SigningError,
)
from tests._transport_signing_support import (
    AUDIENCE,
    KEY_ID,
    SECRET,
    assert_api_verifies,
)
from tests.conftest import (
    BASE_URL,
    RequestRecorder,
    json_handler,
    make_client,
)


@pytest.fixture(autouse=True)
def _no_ambient_signing_env(monkeypatch):
    """Signing does not switch on from the developer's shell environment."""
    monkeypatch.delenv("PERCEIVO_KEY_ID", raising=False)
    monkeypatch.delenv("PERCEIVO_SIGNING_SECRET", raising=False)
    # Clear a stale audience variable as well.
    monkeypatch.delenv("PERCEIVO_HMAC_AUDIENCE", raising=False)


# ---------------------------------------------------------------------------
# Client / AsyncClient wiring
# ---------------------------------------------------------------------------
def test_client_kwargs_enable_signing():
    client, recorder = make_client(
        json_handler({"items": []}),
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )
    client.orchestrations.list()
    assert recorder.last.headers[HEADER_KEY_ID] == KEY_ID
    assert_api_verifies(recorder.last)


def test_client_reads_the_two_credentials_from_the_environment(monkeypatch):
    """Key id and secret may be ambient. The audience still may not."""
    monkeypatch.setenv("PERCEIVO_KEY_ID", KEY_ID)
    monkeypatch.setenv("PERCEIVO_SIGNING_SECRET", SECRET)
    client, recorder = make_client(json_handler({"items": []}), hmac_audience=AUDIENCE)
    client.orchestrations.list()
    assert recorder.last.headers[HEADER_KEY_ID] == KEY_ID
    assert_api_verifies(recorder.last)


def test_client_rejects_half_configured_signing():
    with pytest.raises(SigningError, match="without a signing secret"):
        Client(api_key="k", base_url=BASE_URL, key_id=KEY_ID, hmac_audience=AUDIENCE)


def test_client_refuses_to_sign_without_an_explicit_audience(monkeypatch):
    """Environment credentials without an explicit audience do not enable signing."""
    monkeypatch.setenv("PERCEIVO_KEY_ID", KEY_ID)
    monkeypatch.setenv("PERCEIVO_SIGNING_SECRET", SECRET)
    monkeypatch.setenv("PERCEIVO_HMAC_AUDIENCE", AUDIENCE)
    with pytest.raises(SigningError, match="without an audience"):
        Client(api_key="k", base_url=BASE_URL)


def test_the_client_never_derives_the_audience_from_base_url():
    """The audience is not derived from ``base_url``."""
    with pytest.raises(SigningError, match="without an audience"):
        Client(api_key="k", base_url=BASE_URL, key_id=KEY_ID, signing_secret=SECRET)


def test_client_repr_of_the_signer_hides_the_secret():
    client, _recorder = make_client(
        json_handler({"items": []}),
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )
    assert SECRET not in repr(client._transport._signer)


def test_async_client_forwards_signing_kwargs():
    http_client = httpx.Client(
        base_url=BASE_URL, transport=httpx.MockTransport(RequestRecorder(json_handler({})))
    )
    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=http_client,
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )
    assert client._sync._transport._signer is not None
    assert client._sync._transport._signer.key_id == KEY_ID
    assert client._sync._transport._signer.audience == AUDIENCE
