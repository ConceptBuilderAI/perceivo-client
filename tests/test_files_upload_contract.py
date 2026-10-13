"""``files.upload`` request/response contract.

``POST /v1/files/spaces/{space_id}/upload`` takes the file as a
**multipart** part named ``files`` and an optional ``folder_id`` **query**
parameter, and answers a per-file batch result: ``items``, ``succeeded`` and
``failed``. The vendored snapshot (``openapi/openapi-v1.json``) declares exactly
that, so ``tests/test_spec_conformance.py`` pins the path and the verb and
these tests pin the parts it cannot see: the part name, the query and the
response type.

Warning: The route answers ``200`` even when storage refuses the file. A caller that
reads only the status code reads a failed upload as a stored one; the
``failed`` count is the control, and it is asserted here.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio
import io

import httpx
import pytest

from perceivo_client import AsyncClient, PerceivoGrantError
from perceivo_client.generated.models import FileUploadBatchResult
from perceivo_client.signing import SigningError
from tests.conftest import BASE_URL, json_handler, make_client

_SPACE = "5b1f6c1e-3a0b-4b56-9d6e-0d2c1c1a7a10"
_FOLDER = "c0a8012e-7b1d-4c58-8f43-2f6f5a0c9e77"
_PATH = f"/v1/files/spaces/{_SPACE}/upload"

# A batch of one stored file, in the shape the route answers.
_UPLOADED = {
    "items": [{"filename": "rows.csv", "status": "completed"}],
    "succeeded": 1,
    "failed": 0,
}
_REFUSED = {
    "items": [{"filename": "rows.csv", "status": "error"}],
    "succeeded": 0,
    "failed": 1,
}

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "files-upload-test-signing-secret"
AUDIENCE = "perceivo-api-local"


def _signed_client(handler=None):
    return make_client(
        handler or json_handler(_UPLOADED),
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )


def _async_client(payload=None) -> AsyncClient:
    body = _UPLOADED if payload is None else payload
    return AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(
            base_url=BASE_URL,
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=body)),
        ),
    )


# --- request shape ----------------------------------------------------------


def test_upload_posts_to_the_space_and_sends_no_query_by_default():
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", b"a,b\n1,2\n")

    assert rec.last.method == "POST"
    assert rec.last.url.path == _PATH
    assert dict(rec.last.url.params) == {}


def test_upload_sends_the_folder_as_a_query_parameter():
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", b"x", folder_id=_FOLDER)

    assert rec.last.url.path == _PATH
    assert dict(rec.last.url.params) == {"folder_id": _FOLDER}


def test_upload_sends_the_payload_as_a_multipart_part_named_files():
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", b"a,b\n1,2\n")

    content_type = rec.last.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")
    body = rec.last.content
    assert b'name="files"' in body
    assert b'name="file"' not in body
    assert b'filename="rows.csv"' in body
    assert b"a,b\n1,2\n" in body


def test_upload_declares_a_content_length():
    """The route refuses a chunked body with 411."""
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", io.BytesIO(b"from-a-stream"))

    assert int(rec.last.headers["content-length"]) == len(rec.last.content)
    assert "transfer-encoding" not in rec.last.headers


def test_upload_does_not_send_a_json_body():
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", b"payload")

    assert "application/json" not in rec.last.headers["content-type"]


def test_upload_accepts_a_binary_file_object():
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", io.BytesIO(b"from-a-stream"))

    assert b"from-a-stream" in rec.last.content


def test_an_explicit_content_type_reaches_the_part_and_is_not_invented():
    """Warning: The asserted type must be one no guesser can produce.

    Asserting `text/csv` both ways reads
    green on Windows and red on Linux: `mimetypes` resolves `.csv` from the
    platform's own tables, so the "omitted" half would measure the runner's
    mimetype database, not the wrapper. A token that exists nowhere but here
    can only have come from the `content_type` argument.
    """
    marker = b"Content-Type: application/x-perceivo-upload-test"

    client, rec = make_client(json_handler(_UPLOADED))
    client.files.upload(_SPACE, "rows.csv", b"x", content_type="application/x-perceivo-upload-test")
    assert marker in rec.last.content

    client, rec = make_client(json_handler(_UPLOADED))
    client.files.upload(_SPACE, "rows.csv", b"x")
    assert marker not in rec.last.content


# --- response shape ---------------------------------------------------------


def test_upload_returns_the_batch_result():
    client, _rec = make_client(json_handler(_UPLOADED))

    result = client.files.upload(_SPACE, "rows.csv", b"x")

    assert isinstance(result, FileUploadBatchResult)
    assert result.succeeded == 1
    assert result.failed == 0
    assert len(result.items) == 1


def test_a_refused_file_is_visible_on_a_200_response():
    """The route answers 200 for a batch whose only file was refused."""
    client, _rec = make_client(json_handler(_REFUSED))

    result = client.files.upload(_SPACE, "rows.csv", b"x")

    assert isinstance(result, FileUploadBatchResult)
    assert result.succeeded == 0
    assert result.failed == 1


# --- signed mode ------------------------------------------------------------


def test_a_signing_client_refuses_the_upload_instead_of_sending_it_unsigned():
    """Warning: The control that matters: refuse, do not downgrade.

    A multipart body is built by ``httpx`` as a streaming body, and this client
    will not sign a body it has not read. The alternative failure -- sending the
    upload unsigned from a client the caller configured for signing -- would
    drop the control silently, which is why the assertion on ``rec.requests``
    is here and not only the ``raises``.
    """
    client, rec = _signed_client()
    call = client.files.upload

    with pytest.raises(SigningError, match="multipart"):
        call(_SPACE, "rows.csv", b"x")

    assert rec.requests == []


def test_an_unsigned_client_is_not_refused():
    """The negative control: the refusal is keyed to signing, not to uploads."""
    client, rec = make_client(json_handler(_UPLOADED))

    client.files.upload(_SPACE, "rows.csv", b"x")

    assert len(rec.requests) == 1


def test_signing_enabled_reports_the_transports_configuration():
    signed, _rec = _signed_client()
    plain, _rec2 = make_client(json_handler({}))

    assert signed._transport.signing_enabled is True
    assert plain._transport.signing_enabled is False


def test_the_transport_backstop_still_refuses_an_unread_streaming_body():
    """Defence in depth: the call-site guard is not the only one.

    ``files.upload`` refuses first, so this drives the transport directly with a
    streaming ``content=`` iterator -- the other way a signed request can carry
    a body that cannot be hashed.
    """
    client, rec = _signed_client()
    transport = client._transport

    with pytest.raises(SigningError, match="streaming request body"):
        transport.request("POST", "/v1/anything", content=iter([b"a", b"b"]))

    assert rec.requests == []


# --- async mirror -----------------------------------------------------------


def test_async_upload_mirrors_the_sync_contract():
    result = asyncio.run(_async_client().files.upload(_SPACE, "rows.csv", b"x"))

    assert isinstance(result, FileUploadBatchResult)
    assert result.succeeded == 1


def test_async_upload_refuses_under_signing_too():
    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(
            base_url=BASE_URL,
            transport=httpx.MockTransport(lambda _r: httpx.Response(200, json=_UPLOADED)),
        ),
        key_id=KEY_ID,
        signing_secret=SECRET,
        hmac_audience=AUDIENCE,
    )
    pending = client.files.upload(_SPACE, "rows.csv", b"x")

    with pytest.raises(SigningError, match="multipart"):
        asyncio.run(pending)


def test_an_upload_url_without_file_write_raises_grant_error():
    # POST /files/upload-url needs FILE_WRITE.
    payload = {"code": "insufficient_privilege", "message": "requires FILE_WRITE"}
    client, _ = make_client(json_handler(payload, status=403))

    with pytest.raises(PerceivoGrantError) as info:
        client.files.create_upload_url({"space_id": _SPACE, "file_name": "a", "size_bytes": 1})

    assert info.value.code == "insufficient_privilege"
