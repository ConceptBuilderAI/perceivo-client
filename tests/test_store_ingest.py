"""The three store ingest methods: request and response contract.

``ingest_search_index``, ``ingest_vector_store_collection`` and ``ingest_cache`` post
``multipart/form-data``: the document is the part named ``files`` and every
option is a form field of its own. The API refuses any other body type with
``415``, so the body type is asserted here, not only the path.

Warning: The ingest operations answer ``200`` even when the document is refused. The
per-document outcome is in the result's ``files`` list, and that is asserted
for each method: a caller reading only the status code reads a refused
document as a stored one.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio
import io

import httpx
import pytest

from perceivo_client import AsyncClient
from perceivo_client.generated.models import DocumentUploadResponse
from perceivo_client.signing import SigningError
from tests.conftest import BASE_URL, json_handler, make_client

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "store-ingest-test-signing-secret"
AUDIENCE = "perceivo-api-local"

_STORED = {
    "files": [{"filename": "rows.csv", "status": "completed", "inserted": 3, "chunks": 3}],
    "embedding_model": "text-embedding-3-small",
    "total_inserted": 3,
    "total_chunks": 3,
}
_REFUSED = {
    "files": [{"filename": "rows.csv", "status": "error", "error": "Unsupported file"}],
    "embedding_model": "text-embedding-3-small",
    "total_inserted": 0,
    "total_chunks": 0,
}

# (case id, call, path, the form fields the call must send, fields it must not)
CASES = [
    (
        "search_index",
        lambda c, data=b"a,b\n1,2\n": c.infrastructure.ingest_search_index(
            "logs", "rows.csv", data, text_field="body", chunk_size=200
        ),
        "/v1/infrastructure/search-index/indices/logs/ingest",
        {"text_field": b"body", "chunk_size": b"200"},
        ("vector_field", "embedding_model", "chunk_overlap", "key_prefix", "ttl"),
    ),
    (
        "vector_store",
        lambda c, data=b"a,b\n1,2\n": c.infrastructure.ingest_vector_store_collection(
            "docs", "rows.csv", data, vector_field="embedding", embedding_model="m-1"
        ),
        "/v1/infrastructure/vector-store/collections/docs/ingest",
        {"vector_field": b"embedding", "embedding_model": b"m-1"},
        ("text_field", "chunk_size", "chunk_overlap", "key_prefix", "ttl"),
    ),
    (
        "cache",
        lambda c, data=b"a,b\n1,2\n": c.infrastructure.ingest_cache(
            "kb:", "rows.csv", data, ttl=60, chunk_overlap=10
        ),
        "/v1/infrastructure/cache/ingest",
        {"key_prefix": b"kb:", "ttl": b"60", "chunk_overlap": b"10"},
        ("text_field", "vector_field", "embedding_model", "chunk_size"),
    ),
]
_IDS = [case[0] for case in CASES]


def _field(name: str, value: bytes) -> bytes:
    """A plain form field as httpx writes it: no filename, then the value."""
    return (
        b'Content-Disposition: form-data; name="' + name.encode() + b'"\r\n\r\n' + value + b"\r\n"
    )


def _signed_client():
    return make_client(
        json_handler(_STORED), key_id=KEY_ID, signing_secret=SECRET, hmac_audience=AUDIENCE
    )


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_ingest_posts_one_multipart_request_to_the_ingest_path(_id, call, path, fields, absent):
    client, rec = make_client(json_handler(_STORED))

    call(client)

    assert len(rec.requests) == 1
    assert rec.last.method == "POST"
    assert rec.last.url.path == path
    assert dict(rec.last.url.params) == {}
    assert rec.last.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert "application/json" not in rec.last.headers["content-type"]


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_the_document_is_the_part_named_files(_id, call, path, fields, absent):
    client, rec = make_client(json_handler(_STORED))

    call(client)

    body = rec.last.content
    assert b'name="files"; filename="rows.csv"' in body
    assert b'name="file"' not in body
    assert b"a,b\n1,2\n" in body


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_options_are_form_fields_and_omitted_options_are_not_sent(_id, call, path, fields, absent):
    client, rec = make_client(json_handler(_STORED))

    call(client)

    body = rec.last.content
    missing = [name for name, value in fields.items() if _field(name, value) not in body]
    assert missing == []
    leaked = [name for name in absent if f'name="{name}"'.encode() in body]
    assert leaked == []


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_ingest_declares_a_content_length(_id, call, path, fields, absent):
    """The ingest operations refuse a chunked body with 411."""
    client, rec = make_client(json_handler(_STORED))

    call(client, io.BytesIO(b"a,b\n1,2\n"))

    assert int(rec.last.headers["content-length"]) == len(rec.last.content)
    assert "transfer-encoding" not in rec.last.headers
    assert b"a,b\n1,2\n" in rec.last.content


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_a_stored_document_is_reported_per_file(_id, call, path, fields, absent):
    client, _rec = make_client(json_handler(_STORED))

    result = call(client)

    assert isinstance(result, DocumentUploadResponse)
    assert result.total_inserted == 3
    assert [entry["status"] for entry in result.files] == ["completed"]


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_a_refused_document_is_visible_on_a_200_response(_id, call, path, fields, absent):
    """The route answers 200 for a batch whose only document was refused."""
    client, _rec = make_client(json_handler(_REFUSED))

    result = call(client)

    assert isinstance(result, DocumentUploadResponse)
    assert result.total_inserted == 0
    assert [entry["status"] for entry in result.files] == ["error"]
    assert result.files[0]["error"] == "Unsupported file"


def test_an_explicit_content_type_reaches_the_document_part_and_is_not_invented():
    """The asserted type is one no guesser can produce (see the files upload test)."""
    marker = b"Content-Type: application/x-perceivo-ingest-test"

    client, rec = make_client(json_handler(_STORED))
    client.infrastructure.ingest_cache(
        "kb:", "rows.csv", b"x", content_type="application/x-perceivo-ingest-test"
    )
    assert marker in rec.last.content

    client, rec = make_client(json_handler(_STORED))
    client.infrastructure.ingest_cache("kb:", "rows.csv", b"x")
    assert marker not in rec.last.content


def test_the_json_body_form_cannot_be_called_and_reaches_no_wire():
    client, rec = make_client(json_handler(_STORED))
    call = client.infrastructure.ingest_search_index

    with pytest.raises(TypeError, match=r"missing 1 required positional argument"):
        call("logs", {"documents": []})

    assert rec.requests == []


# --- signed mode ------------------------------------------------------------


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_a_signing_client_refuses_the_ingest_instead_of_sending_it_unsigned(
    _id, call, path, fields, absent
):
    """Warning: Refuse, do not downgrade: nothing may reach the wire unsigned."""
    client, rec = _signed_client()

    with pytest.raises(SigningError, match="multipart"):
        call(client)

    assert rec.requests == []


@pytest.mark.parametrize("_id,call,path,fields,absent", CASES, ids=_IDS)
def test_an_unsigned_client_is_not_refused(_id, call, path, fields, absent):
    """The negative control: the refusal is keyed to signing, not to ingest."""
    client, rec = make_client(json_handler(_STORED))

    call(client)

    assert len(rec.requests) == 1


def test_the_refusal_names_the_method_that_was_called():
    client, _rec = _signed_client()
    call = client.infrastructure.ingest_vector_store_collection

    with pytest.raises(SigningError, match=r"infrastructure\.ingest_vector_store_collection"):
        call("docs", "rows.csv", b"x")


# --- async mirror -----------------------------------------------------------


def test_async_ingest_mirrors_the_sync_contract():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json=_REFUSED)

    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)),
    )

    result = asyncio.run(client.infrastructure.ingest_cache("kb:", "rows.csv", b"x"))

    assert seen == [("POST", "/v1/infrastructure/cache/ingest")]
    assert isinstance(result, DocumentUploadResponse)
    assert [entry["status"] for entry in result.files] == ["error"]
