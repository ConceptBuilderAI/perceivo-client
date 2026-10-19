"""Credential-query refusal and signed-header containment guards."""

from __future__ import annotations

import pytest

from perceivo_client.signing import SigningError, sign_request
from perceivo_client.signing.signer import SigningCredentials
from tests.test_signing_containment import AUDIENCE, KEY_ID, SECRET


def test_the_refusal_message_never_echoes_the_callers_raw_spelling():
    """The message reaches logs, so it reports the normalised name, not raw input."""
    injected = "api%5Fkey"
    with pytest.raises(SigningError) as excinfo:
        sign_request(
            method="GET",
            target=f"/x?{injected}=abc123",
            key_id=KEY_ID,
            secret=SECRET,
            audience=AUDIENCE,
            content_type=None,
            organization=None,
        )
    message = str(excinfo.value)
    assert "api_key" in message
    assert injected not in message
    assert "abc123" not in message, "the credential VALUE must never reach the message"


# ---------------------------------------------------------------------------
# key_id is a header value, so it is validated as one
# ---------------------------------------------------------------------------

UNSAFE_KEY_IDS = [
    pytest.param("ak_test\r\nX-Injected: 1", id="crlf-header-injection"),
    pytest.param("ak_test\nX-Injected: 1", id="lf-only"),
    pytest.param("ak_test\r", id="trailing-cr"),
    pytest.param("ak_test\n", id="trailing-lf"),
    pytest.param("ak test", id="embedded-space"),
    pytest.param("ak_test\x00", id="nul"),
    pytest.param("ak_test\x7f", id="del"),
    pytest.param("ak_tést", id="non-ascii"),
    pytest.param("a" * 257, id="over-length"),
    pytest.param("", id="empty"),
    # The same injections wearing a uuid, so the refusal cannot be an accident of
    # the prefix-shaped strings above.
    pytest.param(KEY_ID + "\r\nX-Injected: 1", id="uuid-with-crlf-injection"),
    pytest.param(KEY_ID + "\n", id="uuid-with-trailing-lf"),
    pytest.param(KEY_ID + " ", id="uuid-with-trailing-space"),
    pytest.param(" " + KEY_ID, id="uuid-with-leading-space"),
]


@pytest.mark.parametrize("key_id", UNSAFE_KEY_IDS)
def test_sign_request_refuses_a_key_id_that_is_unsafe_as_a_header(key_id: str):
    with pytest.raises(SigningError, match="key_id"):
        sign_request(
            method="GET",
            target="/x",
            key_id=key_id,
            secret=SECRET,
            audience=AUDIENCE,
            content_type=None,
            organization=None,
        )


@pytest.mark.parametrize("key_id", UNSAFE_KEY_IDS)
def test_credentials_refuse_the_same_key_ids(key_id: str):
    """Both construction paths validate ``key_id``."""
    with pytest.raises(SigningError, match="key_id"):
        SigningCredentials(key_id=key_id, signing_secret=SECRET, audience=AUDIENCE)


@pytest.mark.parametrize(
    "supplied",
    [
        pytest.param("b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60", id="canonical-form"),
        pytest.param("B6F0A0D2-7C1E-4F3A-9D55-1C2E3F4A5B60", id="uppercase"),
        pytest.param("b6f0a0d27c1e4f3a9d551c2e3f4a5b60", id="unhyphenated"),
        pytest.param("{b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60}", id="braced"),
        pytest.param("urn:uuid:b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60", id="urn"),
    ],
)
def test_legitimate_key_ids_still_sign(supplied: str):
    """Every spelling of the same UUID signs to the same normalised header value."""
    signed = sign_request(
        method="GET",
        target="/x",
        key_id=supplied,
        secret=SECRET,
        audience=AUDIENCE,
        content_type=None,
        organization=None,
    )
    assert signed.headers["X-Perceivo-Key-Id"] == KEY_ID
    assert signed.canonical_request.split("\n")[2] == KEY_ID


def test_no_signed_header_value_can_contain_a_line_break():
    """No header value ``sign_request`` returns contains a line break."""
    signed = sign_request(
        method="GET",
        target="/x?limit=10",
        key_id=KEY_ID,
        secret=SECRET,
        audience=AUDIENCE,
        content_type="application/json",
        organization=None,
    )
    for name, value in signed.headers.items():
        assert not {"\r", "\n"} & set(value), f"{name} carries a line break"
        assert value.isascii(), f"{name} carries non-ASCII"
