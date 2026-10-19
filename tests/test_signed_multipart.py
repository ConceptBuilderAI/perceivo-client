"""HMAC-signed multipart: the signature covers the multipart bytes sent.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import io

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
    build_canonical_request,
    split_target,
)
from perceivo_client.signing._verify import verify_signed_request
from tests.conftest import BASE_URL

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "signed-multipart-test-signing-secret"
AUDIENCE = "perceivo-api-local"

_PAYLOAD = b"a,b\r\n1,2\r\n--not-a-boundary\r\n"


class _Wire:
    """A mock transport handler that records the bytes it is actually sent."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.bodies: list[bytes] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        # Read the stream the transport is handed, not a cached ``request.content``.
        self.bodies.append(b"".join(request.stream))
        self.requests.append(request)
        return httpx.Response(200, json={"id": "x", "name": "n"})

    @property
    def last(self) -> tuple[httpx.Request, bytes]:
        return self.requests[-1], self.bodies[-1]


def _signed_client(**kwargs) -> tuple[Client, _Wire]:
    wire = _Wire()
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(wire))
    client = Client(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=http_client,
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
        **kwargs,
    )
    return client, wire


def _canonical(request: httpx.Request, body: bytes) -> str:
    """The canonical request the API rebuilds from what it received."""
    raw_path, query = split_target(request.url.raw_path.decode("ascii"))
    return build_canonical_request(
        audience=AUDIENCE,
        key_id=request.headers[HEADER_KEY_ID],
        method=request.method,
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=request.headers.get_list("content-type") or None,
        organization=request.headers.get_list("perceivo-organization") or None,
        timestamp=request.headers[HEADER_TIMESTAMP],
        nonce=request.headers[HEADER_NONCE],
    )


def _api_verifies(request: httpx.Request, body: bytes) -> bool:
    return verify_signed_request(
        signature=request.headers[HEADER_SIGNATURE],
        canonical_request=_canonical(request, body),
        secret=SECRET,
        audience=AUDIENCE,
        key_id=KEY_ID,
    )


def _boundary(request: httpx.Request) -> bytes:
    [content_type] = request.headers.get_list("content-type")
    media_type, _, boundary = content_type.partition("; boundary=")
    assert media_type == "multipart/form-data"
    assert boundary
    return boundary.encode("ascii")


def _assert_framed_by(body: bytes, boundary: bytes) -> None:
    """The body opens on, and closes with, the boundary in the header."""
    assert body.startswith(b"--" + boundary + b"\r\n")
    assert body.endswith(b"\r\n--" + boundary + b"--\r\n")


# --- the seven multipart methods ---------------------------------------------

_METHODS = [
    pytest.param(
        lambda c, d: c.files.upload("s1", "rows.csv", d),
        "POST",
        "/v1/files/spaces/s1/upload",
        id="files.upload",
    ),
    pytest.param(
        lambda c, d: c.files.replace_content("e1", d, version_comment="v2"),
        "PUT",
        "/v1/files/entries/e1/content",
        id="files.replace_content",
    ),
    pytest.param(
        lambda c, d: c.infrastructure.import_search_index("i1", d),
        "POST",
        None,
        id="infrastructure.import_search_index",
    ),
    pytest.param(
        lambda c, d: c.infrastructure.import_vector_store_collection("c1", d),
        "POST",
        None,
        id="infrastructure.import_vector_store_collection",
    ),
    pytest.param(
        lambda c, d: c.infrastructure.ingest_cache("k1", "doc.txt", d, ttl=60),
        "POST",
        None,
        id="infrastructure.ingest_cache",
    ),
    pytest.param(
        lambda c, d: c.infrastructure.ingest_search_index("i1", "doc.txt", d),
        "POST",
        None,
        id="infrastructure.ingest_search_index",
    ),
    pytest.param(
        lambda c, d: c.infrastructure.ingest_vector_store_collection("c1", "doc.txt", d),
        "POST",
        None,
        id="infrastructure.ingest_vector_store_collection",
    ),
]


@pytest.mark.parametrize("call,method,path", _METHODS)
@pytest.mark.parametrize(
    "make_data",
    [
        pytest.param(lambda: _PAYLOAD, id="bytes"),
        pytest.param(lambda: io.BytesIO(_PAYLOAD), id="file-object"),
    ],
)
def test_each_multipart_method_sends_one_signed_request_the_api_verifies(
    call, method, path, make_data
):
    client, wire = _signed_client()

    call(client, make_data())

    assert len(wire.requests) == 1
    request, sent = wire.last
    assert request.method == method
    if path is not None:
        assert request.url.path == path
    assert HEADER_SIGNATURE in request.headers
    assert _PAYLOAD in sent
    _assert_framed_by(sent, _boundary(request))
    assert int(request.headers["content-length"]) == len(sent)
    assert "transfer-encoding" not in request.headers
    assert _api_verifies(request, sent)


@pytest.mark.parametrize("call,method,path", _METHODS)
def test_the_async_client_signs_each_multipart_method_too(call, method, path):
    wire = _Wire()
    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(wire)),
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )

    asyncio.run(call(client, _PAYLOAD))

    request, sent = wire.last
    assert _api_verifies(request, sent)


# --- the signature covers the sent bytes ------------------------------------


def test_the_signed_body_digest_is_the_digest_of_the_sent_bytes():
    client, wire = _signed_client()

    client.files.upload("s1", "rows.csv", _PAYLOAD)

    request, sent = wire.last
    canonical = _canonical(request, sent)
    assert canonical.split("\n")[6] == hashlib.sha256(sent).hexdigest()
    assert _api_verifies(request, sent)


def test_one_changed_byte_of_the_sent_body_fails_verification():
    """The negative control: verification depends on the body bytes."""
    client, wire = _signed_client()

    client.files.upload("s1", "rows.csv", _PAYLOAD)

    request, sent = wire.last
    tampered = sent.replace(b"1,2", b"1,3")
    assert tampered != sent
    assert _api_verifies(request, sent)
    assert not _api_verifies(request, tampered)


def test_a_non_seekable_stream_is_read_once_and_sent_with_a_content_length():
    """A stream ``httpx`` cannot size would go out chunked; the routes refuse that (411)."""

    class _OneShot(io.RawIOBase):
        def __init__(self, data: bytes) -> None:
            self._data = io.BytesIO(data)
            self.reads = 0

        def readable(self) -> bool:
            return True

        def read(self, size: int = -1) -> bytes:
            self.reads += 1
            return self._data.read(size)

    client, wire = _signed_client()
    stream = _OneShot(_PAYLOAD)

    client.files.upload("s1", "rows.csv", stream)

    request, sent = wire.last
    assert _PAYLOAD in sent
    assert int(request.headers["content-length"]) == len(sent)
    assert "transfer-encoding" not in request.headers
    assert _api_verifies(request, sent)


# --- the boundary is one value in the signed header and the body ------------


def test_the_signed_content_type_is_the_sent_one_and_its_boundary_frames_the_body():
    client, wire = _signed_client()

    client.infrastructure.ingest_search_index("i1", "doc.txt", _PAYLOAD)

    request, sent = wire.last
    boundary = _boundary(request)
    canonical = _canonical(request, sent)
    assert canonical.split("\n")[7] == request.headers["content-type"]
    _assert_framed_by(sent, boundary)
    # Split on that boundary, the body is one document part.
    parts = sent.split(b"--" + boundary)
    assert parts[0] == b""
    assert parts[-1] == b"--\r\n"
    assert len(parts) == 3
    assert _PAYLOAD in parts[1]


def test_a_body_reframed_with_another_boundary_fails_verification():
    """Re-framing identical bytes under a different boundary changes field 8."""
    client, wire = _signed_client()

    client.files.upload("s1", "rows.csv", _PAYLOAD)

    request, sent = wire.last
    boundary = _boundary(request)
    other = b"x" * len(boundary)
    reframed = httpx.Request(
        request.method,
        request.url,
        headers={
            **request.headers,
            "content-type": f"multipart/form-data; boundary={other.decode()}",
        },
        content=sent.replace(boundary, other),
    )
    assert not _api_verifies(reframed, reframed.content)


# --- golden: fixed boundary, clock and nonce --------------------------------

_GOLDEN_BOUNDARY = "perceivo-golden-boundary-0001"
_GOLDEN_NONCE = "golden-nonce-multipart-000000000001"
_GOLDEN_TIMESTAMP = 1_760_000_000

#: The multipart body, written out by hand: the bytes the API must receive.
_GOLDEN_BODY = (
    b"--perceivo-golden-boundary-0001\r\n"
    b'Content-Disposition: form-data; name="files"; filename="rows.csv"\r\n'
    b"Content-Type: text/x-golden\r\n"
    b"\r\n"
    b"a,b\n1,2\n"
    b"\r\n"
    b"--perceivo-golden-boundary-0001--\r\n"
)


def test_golden_a_fixed_multipart_request_signs_and_verifies_byte_for_byte():
    """Fixed boundary, timestamp and nonce, with the signature computed independently."""
    wire = _Wire()
    http_client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(wire))
    signer = RequestSigner(
        SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE),
        nonce_factory=lambda: _GOLDEN_NONCE,
        clock=lambda: _GOLDEN_TIMESTAMP,
    )
    transport = Transport(
        APICredentials(base_url=BASE_URL, api_key="test-key"),
        http_client=http_client,
        signer=signer,
    )
    content_type = f"multipart/form-data; boundary={_GOLDEN_BOUNDARY}"

    transport.request(
        "POST",
        "/v1/files/spaces/s1/upload",
        params={"folder_id": "f1"},
        headers={"Content-Type": content_type},
        files={"files": ("rows.csv", b"a,b\n1,2\n", "text/x-golden")},
    )

    request, sent = wire.last
    assert sent == _GOLDEN_BODY
    assert request.headers["content-type"] == content_type
    assert request.headers["content-length"] == str(len(_GOLDEN_BODY))

    expected_canonical = "\n".join(
        [
            "perceivo-hmac-v1",
            AUDIENCE,
            KEY_ID,
            "POST",
            "/v1/files/spaces/s1/upload",
            "folder_id=f1",
            hashlib.sha256(_GOLDEN_BODY).hexdigest(),
            content_type,
            "",
            str(_GOLDEN_TIMESTAMP),
            _GOLDEN_NONCE,
        ]
    )
    expected_signature = (
        "v1="
        + hmac.new(
            SECRET.encode("utf-8"), expected_canonical.encode("utf-8"), hashlib.sha256
        ).hexdigest()
    )
    assert _canonical(request, sent) == expected_canonical
    assert request.headers[HEADER_SIGNATURE] == expected_signature
    assert _api_verifies(request, sent)
