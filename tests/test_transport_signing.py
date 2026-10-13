"""Transport wiring for HMAC signing: opt-in, off by default, fresh per attempt.

Two properties matter more than the rest and are asserted structurally rather
than behaviourally:

1. **Off by default is byte-identical.** A behavioural check ("no X-Perceivo-*
   header appeared") passes for a wrapper that is merely quiet today. These tests
   spy on the ``httpx.Client`` and assert the unsigned path still goes through the
   *same* ``Client.request(...)`` call with the *same* arguments — a code-path
   identity assertion, not an output one.
2. **The signature covers the bytes actually sent.** Every signed test recomputes
   the canonical request from the request the mock transport received, so a
   mismatch between what was signed and what was sent fails the test.
"""

from __future__ import annotations

import json
from urllib.parse import parse_qsl

import httpx
import pytest

from perceivo_client import AsyncClient, Client
from perceivo_client._transport import Transport
from perceivo_client.auth import APICredentials
from perceivo_client.signing import (
    HEADER_KEY_ID,
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    RequestSigner,
    SigningCredentials,
    SigningError,
    build_canonical_request,
    split_target,
    verify_signature,
)
from tests.conftest import (
    BASE_URL,
    RequestRecorder,
    json_handler,
    make_client,
)

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "transport-test-signing-secret"
AUDIENCE = "perceivo-api-local"


@pytest.fixture(autouse=True)
def _no_ambient_signing_env(monkeypatch):
    """Signing must never switch on because the developer's shell had it set."""
    monkeypatch.delenv("PERCEIVO_KEY_ID", raising=False)
    monkeypatch.delenv("PERCEIVO_SIGNING_SECRET", raising=False)
    # There is no audience env var to honour, but a stale one in the developer's
    # shell must not become the reason a test passes either.
    monkeypatch.delenv("PERCEIVO_HMAC_AUDIENCE", raising=False)


class SpyClient(httpx.Client):
    """An ``httpx.Client`` that records which entry point the transport used."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.calls: list[tuple[str, tuple, dict]] = []

    def request(self, *args, **kwargs):
        self.calls.append(("request", args, kwargs))
        return super().request(*args, **kwargs)

    def build_request(self, *args, **kwargs):
        self.calls.append(("build_request", args, kwargs))
        return super().build_request(*args, **kwargs)

    def send(self, *args, **kwargs):
        self.calls.append(("send", args, kwargs))
        return super().send(*args, **kwargs)


def spy_transport(handler=None, **transport_kwargs) -> tuple[Transport, RequestRecorder, SpyClient]:
    recorder = RequestRecorder(handler or json_handler({"ok": True}))
    http_client = SpyClient(base_url=BASE_URL, transport=httpx.MockTransport(recorder))
    creds = APICredentials(base_url=BASE_URL, api_key="test-key")
    transport = Transport(creds, http_client=http_client, sleep=lambda _s: None, **transport_kwargs)
    return transport, recorder, http_client


def signer(*, nonce_factory=None, clock=None) -> RequestSigner:
    kwargs = {}
    if nonce_factory is not None:
        kwargs["nonce_factory"] = nonce_factory
    if clock is not None:
        kwargs["clock"] = clock
    return RequestSigner(
        SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE), **kwargs
    )


def recompute(request: httpx.Request) -> str:
    """Rebuild the canonical request the API verifies, from what the mock received.

    Every input except the audience is read back off the *sent* request, so a
    signature computed over anything other than what went out fails here. The
    audience is the one field with no wire
    representation (it is configuration on both ends), so it comes from the
    same constant the signer was built with.

    ``content_type`` is read with ``get_list`` rather than ``get``: httpx joins
    repeated values with ``", "``, which would silently synthesise a single header
    the request never carried and hide the repeated-header rejection.
    """
    raw_path, query = split_target(request.url.raw_path.decode("ascii"))
    return build_canonical_request(
        audience=AUDIENCE,
        key_id=request.headers[HEADER_KEY_ID],
        method=request.method,
        raw_path=raw_path,
        query_string=query,
        body=request.content,
        content_type=request.headers.get_list("content-type") or None,
        organization=request.headers.get_list("perceivo-organization") or None,
        timestamp=request.headers[HEADER_TIMESTAMP],
        nonce=request.headers[HEADER_NONCE],
    )


def assert_api_verifies(request: httpx.Request) -> None:
    """The signature on ``request`` verifies as the API verifies it."""
    assert verify_signature(request.headers[HEADER_SIGNATURE], recompute(request), SECRET)


# ---------------------------------------------------------------------------
# The signed path is the one sent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "call,sent_path",
    [
        (lambda c: c.orchestrations.list(page=2, page_size=5), "/v1/orchestrations"),
        (lambda c: c.auth.whoami(), "/v1/whoami"),
        (lambda c: c.orchestrations.get("a/b c"), "/v1/orchestrations/a%2Fb%20c"),
    ],
    ids=["with-query", "whoami", "encoded-segment"],
)
def test_a_signed_client_request_signs_the_path_it_sends(call, sent_path):
    """The API verifies the path it receives, so the signature covers that path."""
    client, recorder = make_client(
        json_handler({}), key_id=KEY_ID, signing_secret=SECRET, hmac_audience=AUDIENCE
    )
    call(client)
    request = recorder.last
    assert request.url.raw_path.decode("ascii").partition("?")[0] == sent_path
    assert_api_verifies(request)
    # Control: the same signature does not verify over another spelling of the
    # path, so this test would fail against a client that signed a rewritten one.
    request.url = request.url.copy_with(raw_path=b"/api" + request.url.raw_path)
    assert not verify_signature(request.headers[HEADER_SIGNATURE], recompute(request), SECRET)


# ---------------------------------------------------------------------------
# Off by default — code-path identity
# ---------------------------------------------------------------------------
def test_unsigned_transport_uses_the_original_client_request_call():
    transport, _recorder, spy = spy_transport()
    transport.request("GET", "/v1/orchestrations")
    # httpx.Client.request itself calls build_request+send internally, so what
    # distinguishes the paths is which call comes FIRST.
    assert spy.calls[0][0] == "request"


def test_unsigned_transport_passes_the_same_arguments_as_before():
    transport, _recorder, spy = spy_transport()
    transport.request("POST", "/v1/x", params={"a": 1}, json={"b": 2})
    name, args, kwargs = spy.calls[0]
    assert name == "request"
    assert args == ("POST", "/v1/x")
    # `files` joined this set so multipart uploads can reach the
    # wire. It is None for every non-multipart caller, and httpx treats a None
    # `files` exactly as an absent one, so the unsigned request on the wire is
    # unchanged -- which is what the recorder assertions in this module measure.
    assert set(kwargs) == {"params", "json", "content", "files", "headers"}
    assert kwargs["files"] is None
    assert kwargs["params"] == {"a": 1}
    assert kwargs["json"] == {"b": 2}


def test_signed_transport_never_calls_client_request():
    transport, _recorder, spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations")
    assert [name for name, _a, _k in spy.calls] == ["build_request", "send"]
    assert "request" not in [name for name, _a, _k in spy.calls]


def test_unsigned_request_carries_no_signing_headers():
    transport, recorder, _spy = spy_transport()
    transport.request("GET", "/v1/orchestrations", params={"limit": 10})
    sent = recorder.last.headers
    for header in (HEADER_KEY_ID, HEADER_TIMESTAMP, HEADER_NONCE, HEADER_SIGNATURE):
        assert header not in sent


def test_unsigned_request_is_byte_identical_with_and_without_the_new_kwargs():
    """Constructing a Client the pre-change way and the new way must not differ."""
    old_style, old_rec = make_client(json_handler({"ok": True}))
    new_style, new_rec = make_client(json_handler({"ok": True}), key_id=None, signing_secret=None)
    old_style.orchestrations.list(page_size=5)
    new_style.orchestrations.list(page_size=5)

    a, b = old_rec.last, new_rec.last
    assert a.method == b.method
    assert a.url.raw_path == b.url.raw_path
    assert str(a.url) == str(b.url)
    assert a.content == b.content
    # Header list, in order, including values.
    assert list(a.headers.raw) == list(b.headers.raw)


def test_client_without_signing_config_has_no_signer():
    client, _recorder = make_client(json_handler({"ok": True}))
    assert client._transport._signer is None


# ---------------------------------------------------------------------------
# On when configured
# ---------------------------------------------------------------------------
def test_signed_request_carries_all_four_headers():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations")
    sent = recorder.last.headers
    assert sent[HEADER_KEY_ID] == KEY_ID
    assert sent[HEADER_TIMESTAMP].isdigit()
    assert 8 <= len(sent[HEADER_NONCE]) <= 128
    assert sent[HEADER_SIGNATURE].startswith("v1=")


def test_signature_covers_the_request_actually_sent():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations")
    assert_api_verifies(recorder.last)


def test_signature_covers_the_encoded_query_parameters():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations", params={"z": 1, "a": "b c", "s": "a/b"})
    request = recorder.last
    # The request retains the supplied values and order. Its exact serialization
    # is httpx-owned, so MAC verification below binds the actual bytes.
    assert b"?" in request.url.raw_path
    _raw_path, query = split_target(request.url.raw_path.decode("ascii"))
    assert parse_qsl(query, keep_blank_values=True) == [("z", "1"), ("a", "b c"), ("s", "a/b")]
    assert_api_verifies(request)

    canonical = recompute(request)
    mutated = canonical[:-1] + ("0" if canonical[-1] != "0" else "1")
    assert not verify_signature(request.headers[HEADER_SIGNATURE], mutated, SECRET)


def test_signature_covers_the_serialized_json_body():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("POST", "/v1/x", json={"b": 1, "a": 2})
    request = recorder.last
    assert json.loads(request.content) == {"b": 1, "a": 2}
    assert_api_verifies(request)


def test_signature_covers_a_raw_content_body():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("POST", "/v1/x", content=b"\x00\x01raw-bytes")
    assert recorder.last.content == b"\x00\x01raw-bytes"
    assert_api_verifies(recorder.last)


def test_empty_body_signs_as_the_zero_byte_digest():
    from perceivo_client.signing import EMPTY_BODY_SHA256

    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations")
    assert recorder.last.content == b""
    assert recompute(recorder.last).split("\n")[6] == EMPTY_BODY_SHA256


def test_signed_method_matches_the_method_sent():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("delete", "/v1/x/1")
    # httpx uppercases the method; the signature must use the sent form, not the
    # caller's spelling, or every lowercase-method call would 401.
    assert recorder.last.method == "DELETE"
    assert recompute(recorder.last).split("\n")[3] == "DELETE"
    assert_api_verifies(recorder.last)


# ---------------------------------------------------------------------------
# Content-Type (canonical field 8) — the header httpx generated, verbatim
# ---------------------------------------------------------------------------
def test_content_type_field_is_the_header_httpx_generated():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("POST", "/v1/x", json={"a": 1})
    request = recorder.last
    assert recompute(request).split("\n")[7] == request.headers["content-type"]
    assert_api_verifies(request)


def test_a_request_with_no_content_type_signs_the_empty_string():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations")
    request = recorder.last
    assert "content-type" not in request.headers
    assert recompute(request).split("\n")[7] == ""
    assert_api_verifies(request)


def test_the_signed_content_type_is_read_off_the_built_request_not_the_caller():
    """The caller passed no Content-Type at all, so the only way field 8 can be
    non-empty is if it was read back off the request httpx finished building. A
    signer fed the caller's header dict would sign an empty field here and 401."""
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("POST", "/v1/x", json={"a": 1}, headers={"X-Trace": "t"})
    request = recorder.last
    assert recompute(request).split("\n")[7] == "application/json"
    assert_api_verifies(request)


def test_a_generated_multipart_boundary_reaches_the_signed_field():
    """Build-then-sign, on the one body shape where it is unforgiving.

    ``Transport`` has no ``files=`` surface today, so this exercises the pair the
    transport is built from — ``httpx.Client.build_request`` then
    ``RequestSigner.sign`` — in the same order and with the same ``get_list``
    read that ``_build_signed_request`` uses. httpx invents the ``boundary``
    parameter *inside* ``build_request``: a signer invoked any earlier commits to
    a header the request never carries. Whoever adds multipart uploads later needs
    this to already be true.
    """
    http_client = httpx.Client(base_url=BASE_URL)
    request = http_client.build_request("POST", "/v1/files", files={"f": ("a.txt", b"hello")})
    sent = request.headers["content-type"]
    assert sent.startswith("multipart/form-data; boundary=")
    boundary = sent.partition("boundary=")[2]
    # httpx builds multipart as a STREAMING body, so the bytes have to be
    # materialised before they can be hashed. `_build_signed_request` turns the
    # unread case into a loud SigningError rather than signing a placeholder --
    # see test_a_streaming_body_is_refused_rather_than_signed below.
    request.read()
    assert len(boundary) > 0 == request.content.find(f"--{boundary}\r\n".encode("ascii")), boundary

    signed = signer().sign(
        request.method,
        request.url.raw_path.decode("ascii"),
        request.content,
        content_type=request.headers.get_list("content-type") or None,
        organization=request.headers.get_list("perceivo-organization") or None,
    )
    assert signed.canonical_request.split("\n")[7] == sent
    assert boundary in signed.canonical_request


def test_two_multipart_bodies_that_are_byte_identical_sign_differently():
    """Same bytes, two generated boundaries, two signatures. If these collided,
    field 8 would be carrying the media type and dropping the parameter that does
    the work — which is the re-framing attack, still open."""
    http_client = httpx.Client(base_url=BASE_URL)
    first, second = (
        http_client.build_request("POST", "/v1/files", files={"f": ("a.txt", b"hello")})
        for _ in range(2)
    )
    assert first.headers["content-type"] != second.headers["content-type"]

    def sign(request: httpx.Request):
        request.read()
        return signer().sign(
            request.method,
            request.url.raw_path.decode("ascii"),
            request.content,
            content_type=request.headers.get_list("content-type") or None,
            organization=request.headers.get_list("perceivo-organization") or None,
        )

    a, b = sign(first), sign(second)
    assert a.canonical_request.split("\n")[7] != b.canonical_request.split("\n")[7]
    assert a.signature != b.signature


def test_a_caller_supplied_content_type_is_signed_verbatim():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request(
        "POST",
        "/v1/x",
        content=b"{}",
        headers={"Content-Type": "Application/JSON; Charset=UTF-8"},
    )
    request = recorder.last
    # Not lowercased, not reordered, not stripped of its parameter.
    assert recompute(request).split("\n")[7] == "Application/JSON; Charset=UTF-8"
    assert_api_verifies(request)


def test_api_key_header_is_still_sent_alongside_the_signature():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/orchestrations")
    assert recorder.last.headers["X-API-Key"] == "test-key"


def test_caller_headers_survive_signing():
    transport, recorder, _spy = spy_transport(signer=signer())
    transport.request("GET", "/v1/x", headers={"X-Trace": "abc"})
    assert recorder.last.headers["X-Trace"] == "abc"
    assert recorder.last.headers["Accept"] == "application/json"


# ---------------------------------------------------------------------------
# Failure modes — never send an unsigned request when signing was requested
# ---------------------------------------------------------------------------
def test_unsignable_request_raises_and_sends_nothing():
    transport, recorder, _spy = spy_transport(signer=signer())
    with pytest.raises(SigningError, match="api_key"):
        transport.request("GET", "/v1/x", params={"api_key": "leaked"})
    assert recorder.requests == []


def test_a_streaming_body_is_refused_rather_than_signed():
    """A body httpx has not materialised cannot be hashed, and the only safe move
    is to fail loudly. Signing a placeholder digest would produce a signature that
    verifies against bytes the server never receives; sending unsigned would drop
    the protection the caller asked for. This is reachable through the public
    surface — ``content=`` accepts an iterator — and multipart is the shape that
    will meet it first, since httpx streams every multipart body it builds."""
    transport, recorder, _spy = spy_transport(signer=signer())
    with pytest.raises(SigningError, match="streaming request body"):
        transport.request("POST", "/v1/x", content=(c for c in (b"chunk-1", b"chunk-2")))
    assert recorder.requests == []


def test_signing_error_is_not_swallowed_as_a_connection_error():
    transport, _recorder, _spy = spy_transport(signer=signer())
    with pytest.raises(SigningError):
        transport.request("GET", "/v1/x", params={"api_key": "leaked"})


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
    """Environment credentials must not be enough on their own.

    This is the property the whole audience field rests on at the SDK boundary:
    a deployment can put the credentials in the environment and still cannot end
    up signing for an audience nobody named. Note the env var is *set* here — it
    is ignored by design, so the failure is not an accident of an empty shell.
    """
    monkeypatch.setenv("PERCEIVO_KEY_ID", KEY_ID)
    monkeypatch.setenv("PERCEIVO_SIGNING_SECRET", SECRET)
    monkeypatch.setenv("PERCEIVO_HMAC_AUDIENCE", AUDIENCE)
    with pytest.raises(SigningError, match="without an audience"):
        Client(api_key="k", base_url=BASE_URL)


def test_the_client_never_derives_the_audience_from_base_url():
    """``base_url`` is in scope at the very call that resolves the credentials,
    which is precisely why its absence there has to be asserted rather than
    assumed. Deriving it would make every proxy hop a signature break."""
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
