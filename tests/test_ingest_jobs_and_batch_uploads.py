"""The ingest-job wrappers on ``client.infrastructure`` and the
batch upload wrappers on ``client.files``.

The rows are ``tests/_fixtures_wrapper_cases_part5.py``, part of the wrapper matrix; every row gets
the same two checks the matrix rows get --
the method and path the wrapper sends, and that path in the vendored OpenAPI
document -- plus the headers, query and body these operations add.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import AsyncClient
from perceivo_client.generated.models import (
    IngestJob,
    IngestJobFilePage,
    IngestJobPage,
    RegisterFileEntriesResult,
    UploadUrlsResponse,
)
from tests._fixtures_wrapper_cases_part5 import CASES as CASES_INGEST
from tests.conftest import BASE_URL, json_handler, make_client
from tests.test_spec_conformance import _spec_finding

JOB = {
    "id": "op_1",
    "status": "queued",
    "version": 3,
    "store": "milvus",
    "target": "x0",
    "source": {"space_id": "s"},
    "files_succeeded": 0,
    "files_failed": 0,
    "files_pending": 0,
    "chunks_inserted": 0,
    "embedding_tokens": 0,
}


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/upload-urls"):
        return httpx.Response(200, json={"targets": []})
    if path.endswith("/entries/batch"):
        body = {"success_count": 0, "failed_count": 0, "message": "", "results": []}
        return httpx.Response(200, json=body)
    if path.endswith(("/ingest-jobs", "/files")) and request.method == "GET":
        return httpx.Response(200, json={"items": [], "next": None})
    return httpx.Response(202 if request.method == "POST" else 200, json=JOB)


@pytest.mark.parametrize("call,method,path", CASES_INGEST)
def test_each_wrapper_sends_its_operation_and_the_operation_is_published(call, method, path):
    client, rec = make_client(_handler)
    call(client)
    assert (rec.last.method, rec.last.url.path) == (method, path)
    assert _spec_finding(method, path) is None


def test_every_new_operation_has_exactly_one_wrapper():
    """The 14 ingest-job and batch-upload operations, each wrapped once (no duplicate, none left out)."""
    assert len({(m, p) for _c, m, p in CASES_INGEST}) == len(CASES_INGEST) == 14


def test_the_answers_are_typed():
    client, _rec = make_client(_handler)
    infra = client.infrastructure
    assert isinstance(infra.create_vector_store_ingest_job("x0", {}), IngestJob)
    assert isinstance(infra.list_search_index_ingest_jobs("x0"), IngestJobPage)
    assert isinstance(infra.list_vector_store_ingest_job_files("x0", "x1"), IngestJobFilePage)
    assert isinstance(client.files.create_upload_urls({}), UploadUrlsResponse)
    assert isinstance(client.files.register_entries("x0", {}), RegisterFileEntriesResult)


def test_create_sends_the_body_and_an_idempotency_key_only_when_given():
    client, rec = make_client(json_handler(JOB, status=202))
    body = {"source": {"entry_ids": ["e"]}, "embedding_model": "m"}
    client.infrastructure.create_vector_store_ingest_job("x0", body, idempotency_key="k-1")
    assert json.loads(rec.last.content) == body
    assert rec.last.headers["Idempotency-Key"] == "k-1"
    client.infrastructure.create_search_index_ingest_job("x0", body)
    assert "Idempotency-Key" not in rec.last.headers


def test_resume_sends_the_version_as_one_strong_if_match():
    client, rec = make_client(json_handler(JOB, status=202))
    client.infrastructure.resume_vector_store_ingest_job("x0", "x1", version=3, idempotency_key="r")
    assert rec.last.headers["If-Match"] == '"3"'
    assert rec.last.headers["Idempotency-Key"] == "r"
    assert rec.last.content == b""


@pytest.mark.parametrize("version", [-1, True, "3", 3.0, None])
def test_resume_refuses_a_version_that_is_not_a_non_negative_integer(version):
    client, rec = make_client(json_handler(JOB))
    with pytest.raises(ValueError, match="version"):
        client.infrastructure.resume_search_index_ingest_job("x0", "x1", version=version)
    assert rec.requests == []


def test_list_and_files_send_only_the_paging_arguments_given():
    client, rec = make_client(json_handler({"items": [], "next": None}))
    client.infrastructure.list_vector_store_ingest_jobs("x0", limit=5, before="c1")
    assert dict(rec.last.url.params) == {"limit": "5", "before": "c1"}
    client.infrastructure.list_vector_store_ingest_jobs("x0")
    assert dict(rec.last.url.params) == {}
    client.infrastructure.list_search_index_ingest_job_files("x0", "x1", after="f9")
    assert dict(rec.last.url.params) == {"after": "f9"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.infrastructure.get_vector_store_ingest_job("..", "x1"),
        lambda c: c.infrastructure.get_search_index_ingest_job("x0", ".."),
        lambda c: c.infrastructure.cancel_vector_store_ingest_job("x0", ""),
        lambda c: c.files.register_entries("..", {}),
    ],
)
def test_a_name_that_is_not_one_segment_is_refused_before_sending(call):
    client, rec = make_client(json_handler(JOB))
    with pytest.raises(ValueError):
        call(client)
    assert rec.requests == []


def test_batch_bodies_are_sent_unchanged():
    client, rec = make_client(_handler)
    urls = {"space_id": "s", "files": [{"file_name": "a", "size_bytes": 1}]}
    client.files.create_upload_urls(urls)
    assert json.loads(rec.last.content) == urls
    entries = {"files": [{"blob_name": "files/s/a", "file_name": "a", "file_path": "/a"}]}
    client.files.register_entries("s", entries)
    assert json.loads(rec.last.content) == entries


def test_the_async_client_has_the_same_methods():
    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(_handler)),
    )
    job = asyncio.run(client.infrastructure.get_vector_store_ingest_job("x0", "x1"))
    urls = asyncio.run(client.files.create_upload_urls({}))
    assert isinstance(job, IngestJob) and isinstance(urls, UploadUrlsResponse)
