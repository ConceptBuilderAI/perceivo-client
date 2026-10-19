"""Intelligence serving: runtimes, inference, models, drift, lineage and traffic plans.

Pins what the wrapper matrix does not: id round trips, raw artifact bytes,
empty-body defaults, page envelopes, typed returns and async parity.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.generated.models import (
    AssetLineageRead,
    BatchPredictionResponse,
    DriftBaselineRead,
    DriftConfig,
    IntelligenceExport,
    IntelligenceImportResult,
    IntelligenceTrafficPlanResult,
    IntelligenceTrainingJobRead,
    LineageRestoreResult,
    ModelFamilyRead,
    ModelRead,
    PredictionLogRead,
    PredictionOutcomes,
    PredictionPage,
    PredictionRecord,
    TrainingJobSubmitResponse,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_I = "/v1/intelligence"
_JOB = "5b0c5f7e-0000-4000-8000-000000000001"
_SUBMITTED = {"id": _JOB, "intelligence_id": "i1", "status": "queued"}
_JOB_READ = {
    "id": _JOB,
    "intelligence_id": "i1",
    "family_id": "5b0c5f7e-0000-4000-8000-000000000002",
    "status": "running",
    "created_at": "2026-10-03T00:00:00Z",
    "hyperparameter_grid": {},
    "training_config": {},
    "runs": [],
}
_BATCH = {
    "batch_id": "b1",
    "status": "completed",
    "total": 2,
    "succeeded": 2,
    "failed": 0,
    "items": [{}, {}],
    "prediction_ids": ["req-a", "req-b"],
}


def _record(request_id: str) -> dict:
    return {
        "id": request_id,
        "intelligence_id": "i1",
        "organization_id": "o1",
        "status": "completed",
    }


def _routed(routes: dict[tuple[str, str], dict]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=routes[(request.method, request.url.path)])

    return handler


def _batch_then_records(request: httpx.Request) -> httpx.Response:
    if request.method == "POST":
        return httpx.Response(200, json=_BATCH)
    return httpx.Response(200, json=_record(request.url.path.rsplit("/", 1)[-1]))


# --- chains --------------------------------------------------------------------


def test_train_job_id_round_trips_into_get_training_job():
    client, rec = make_client(
        _routed(
            {
                ("POST", f"{_I}/i1/train"): _SUBMITTED,
                ("GET", f"{_I}/i1/training-jobs/{_JOB}"): _JOB_READ,
            }
        )
    )

    submitted = client.intelligence.train("i1")
    job = client.intelligence.get_training_job("i1", submitted.id)

    assert isinstance(submitted, TrainingJobSubmitResponse)
    assert isinstance(job, IntelligenceTrainingJobRead)
    assert rec.last.url.path == f"{_I}/i1/training-jobs/{_JOB}"
    assert str(job.id) == submitted.id


def test_predict_batch_prediction_ids_round_trip_into_read_prediction():
    client, rec = make_client(_batch_then_records)

    batch = client.intelligence.predict_batch("i1", {"inputs": [{}, {}]})
    records = [client.intelligence.get_inference_request("i1", pid) for pid in batch.prediction_ids]

    assert isinstance(batch, BatchPredictionResponse)
    assert all(isinstance(r, PredictionRecord) for r in records)
    assert [r.id for r in records] == batch.prediction_ids
    assert [r.url.path for r in rec.requests[1:]] == [
        f"{_I}/i1/inference/requests/req-a",
        f"{_I}/i1/inference/requests/req-b",
    ]


def test_async_train_chain_awaits_get_training_job():
    sync, rec = make_client(
        _routed(
            {
                ("POST", f"{_I}/i1/train"): _SUBMITTED,
                ("GET", f"{_I}/i1/training-jobs/{_JOB}"): _JOB_READ,
            }
        )
    )
    client = _async_from_sync(sync)

    async def drive():
        submitted = await client.intelligence.train("i1")
        return await client.intelligence.get_training_job("i1", submitted.id)

    job = asyncio.run(drive())

    assert isinstance(job, IntelligenceTrainingJobRead)
    assert rec.last.url.path == f"{_I}/i1/training-jobs/{_JOB}"


def test_async_predict_batch_chain_reads_each_prediction():
    sync, rec = make_client(_batch_then_records)
    client = _async_from_sync(sync)

    async def drive():
        batch = await client.intelligence.predict_batch("i1", {"inputs": [{}, {}]})
        return [
            await client.intelligence.get_inference_request("i1", p) for p in batch.prediction_ids
        ]

    records = asyncio.run(drive())

    assert [r.id for r in records] == ["req-a", "req-b"]
    assert len(rec.requests) == 3


# --- artifacts and bodies ------------------------------------------------------


def test_prediction_artifact_is_returned_as_raw_bytes():
    blob = b"\x89PNG\r\n\x1a\n\x00binary"
    client, rec = make_client(
        lambda _r: httpx.Response(
            200, content=blob, headers={"Content-Type": "application/octet-stream"}
        )
    )

    got = client.intelligence.get_inference_request_artifact("i1", "req-a")

    assert got == blob
    assert rec.last.url.path == f"{_I}/i1/inference/requests/req-a/artifact"


# The bodies the platform answers: start acknowledges with the runtime status,
# stop returns the runtime record, and status nests the intelligence record.
_STARTED = {"status": "RUNNING", "message": "Intelligence i1 deployment initiated", "job_ids": []}
_STOPPED = {"id": "rt1", "intelligence_id": "i1", "status": "STOPPED", "stopped_at": "t"}
_STATUS = {
    "intelligence": {"id": "i1", "status": "running"},
    "runtime": {"id": "rt1", "status": "RUNNING"},
    "services": [],
    "models": [],
}


@pytest.mark.parametrize(("verb", "body"), [("start", _STARTED), ("stop", _STOPPED)])
def test_runtime_controls_send_an_empty_object_without_a_body(verb, body):
    client, rec = make_client(json_handler(body))

    got = getattr(client.intelligence, verb)("i1")

    assert got == body
    assert rec.last.method == "POST"
    assert rec.last.url.path == f"{_I}/i1/{verb}"
    assert rec.last.content == b"{}"


def test_get_status_returns_the_nested_record_the_platform_sends():
    client, rec = make_client(json_handler(_STATUS))

    got = client.intelligence.get_status("i1")

    assert got["intelligence"]["status"] == "running"
    assert got["runtime"]["status"] == "RUNNING"
    assert rec.last.method == "GET"
    assert rec.last.url.path == f"{_I}/i1/status"


def test_stop_forwards_its_options():
    client, rec = make_client(json_handler({"id": "i1"}))

    client.intelligence.stop("i1", {"graceful": False, "timeout_seconds": 5})

    assert json.loads(rec.last.content) == {"graceful": False, "timeout_seconds": 5}


@pytest.mark.parametrize(
    "call,path",
    [
        (
            lambda c: c.intelligence.activate_model_family("i1", "f1"),
            "/i1/model-families/f1/activate",
        ),
        (
            lambda c: c.intelligence.activate_drift_baseline("i1", "b1"),
            "/i1/drift/baselines/b1/activate",
        ),
        (lambda c: c.intelligence.restore("i1"), "/i1/restore"),
    ],
)
def test_bodiless_posts_send_no_body(call, path):
    client, rec = make_client(json_handler({}))

    call(client)

    assert rec.last.method == "POST"
    assert rec.last.url.path == f"{_I}{path}"
    assert rec.last.content == b""


def test_drift_config_is_replaced_with_put():
    client, rec = make_client(json_handler({"enabled": True}))

    got = client.intelligence.replace_drift_config("i1", {"enabled": True})

    assert isinstance(got, DriftConfig)
    assert rec.last.method == "PUT"
    assert json.loads(rec.last.content) == {"enabled": True}


def test_import_posts_to_the_collection_not_an_intelligence():
    client, rec = make_client(json_handler({"id": "new"}))

    got = client.intelligence.import_bundle({"intelligence": {}})

    assert isinstance(got, IntelligenceImportResult)
    assert rec.last.url.path == f"{_I}/import"


# --- query parameters and pagination ------------------------------------------


def test_list_predictions_sends_status_unbracketed():
    client, rec = make_client(json_handler({"page": 1, "page_size": 50, "total": 0}))

    client.intelligence.list_inference_requests("i1", status="completed", page=2, page_size=10)

    assert rec.last.url.path == f"{_I}/i1/inference/requests"
    assert dict(rec.last.url.params) == {"status": "completed", "page": "2", "page_size": "10"}


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.intelligence.list_inference_requests("i1"),
        lambda c: c.intelligence.list_predictions("i1"),
        lambda c: c.intelligence.list_prediction_outcomes("i1", "p1"),
        lambda c: c.intelligence.list_model_families("i1"),
    ],
)
def test_unfiltered_reads_send_no_query(call):
    client, rec = make_client(json_handler([]))

    call(client)

    assert dict(rec.last.url.params) == {}


def test_list_predictions_walks_by_page_until_next_is_null():
    pages = {
        "1": {"data": [_record("r1")], "page": 1, "page_size": 1, "total": 2, "next": "/p2"},
        "2": {"data": [_record("r2")], "page": 2, "page_size": 1, "total": 2, "next": None},
    }
    client, rec = make_client(lambda r: httpx.Response(200, json=pages[r.url.params["page"]]))

    seen, page_number = [], 1
    while True:
        page = client.intelligence.list_inference_requests("i1", page=page_number, page_size=1)
        seen.extend(record.id for record in page.data)
        if page.next is None:
            break
        page_number += 1

    assert isinstance(page, PredictionPage)
    assert seen == ["r1", "r2"]
    assert len(rec.requests) == 2


def test_paginate_pages_refuses_the_prediction_page_envelope():
    client, _ = make_client(
        json_handler({"data": [], "page": 1, "page_size": 25, "total": 0, "next": None})
    )
    walker = paginate_pages(lambda **kw: client.intelligence.list_inference_requests("i1", **kw))

    with pytest.raises(ValueError):
        next(walker)


def test_prediction_logs_forward_their_filters_and_return_a_typed_array():
    client, rec = make_client(json_handler([{"id": "a"}, {"id": "b"}]))

    got = client.intelligence.list_predictions("i1", served_by="canary", page=3, page_size=100)

    assert len(got) == 2
    assert all(isinstance(item, PredictionLogRead) for item in got)
    assert dict(rec.last.url.params) == {
        "served_by": "canary",
        "page": "3",
        "page_size": "100",
    }


def test_prediction_outcomes_forward_prediction_time():
    client, rec = make_client(json_handler({"outcomes": []}))

    got = client.intelligence.list_prediction_outcomes(
        "i1", "p1", prediction_time="2026-10-03T00:00:00Z"
    )

    assert isinstance(got, PredictionOutcomes)
    assert rec.last.url.path == f"{_I}/i1/inference/predictions/p1/outcomes"
    assert dict(rec.last.url.params) == {"prediction_time": "2026-10-03T00:00:00Z"}


def test_model_families_forward_active_only():
    client, rec = make_client(json_handler([{"id": "f1"}]))

    got = client.intelligence.list_model_families("i1", active_only=True)

    assert all(isinstance(item, ModelFamilyRead) for item in got)
    assert dict(rec.last.url.params) == {"active_only": "true"}


# --- typed returns ---------------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.intelligence.apply_traffic_plan("i1", {}), IntelligenceTrafficPlanResult),
        (lambda c: c.intelligence.get_inference_request("i1", "r1"), PredictionRecord),
        (lambda c: c.intelligence.register_model("i1", {}), ModelRead),
        (lambda c: c.intelligence.create_model_family("i1", {}), ModelFamilyRead),
        (lambda c: c.intelligence.get_model_family("i1", "f1"), ModelFamilyRead),
        (lambda c: c.intelligence.update_model_family("i1", "f1", {}), ModelFamilyRead),
        (lambda c: c.intelligence.activate_model_family("i1", "f1"), ModelFamilyRead),
        (lambda c: c.intelligence.get_drift_baseline("i1", "b1"), DriftBaselineRead),
        (lambda c: c.intelligence.activate_drift_baseline("i1", "b1"), DriftBaselineRead),
        (lambda c: c.intelligence.get_drift_config("i1"), DriftConfig),
        (lambda c: c.intelligence.export_bundle("i1"), IntelligenceExport),
        (lambda c: c.intelligence.get_lineage("i1"), AssetLineageRead),
        (lambda c: c.intelligence.restore("i1"), LineageRestoreResult),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x"}))

    assert isinstance(call(client), model)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.intelligence.delete_model("i1", "m1"),
        lambda c: c.intelligence.delete_drift_baseline("i1", "b1"),
        lambda c: c.intelligence.delete_version("i1", "v1"),
    ],
)
def test_no_content_deletes_return_none(call):
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert call(client) is None
    assert rec.last.method == "DELETE"


def test_deactivate_model_family_returns_the_untyped_body():
    client, rec = make_client(json_handler({"id": "f1", "is_active": False}))

    got = client.intelligence.deactivate_model_family("i1", "f1")

    assert got == {"id": "f1", "is_active": False}
    assert rec.last.method == "DELETE"
    assert rec.last.url.path == f"{_I}/i1/model-families/f1"


# --- async parity ------------------------------------------------------------------


def test_async_artifact_download_returns_bytes():
    sync, rec = make_client(lambda _r: httpx.Response(200, content=b"\x00\x01"))
    client = _async_from_sync(sync)

    got = asyncio.run(client.intelligence.get_inference_request_artifact("i1", "r1"))

    assert got == b"\x00\x01"
    assert rec.last.url.path == f"{_I}/i1/inference/requests/r1/artifact"


def test_async_start_awaits_and_hits_the_exact_path():
    sync, rec = make_client(json_handler(_STARTED))
    client = _async_from_sync(sync)

    got = asyncio.run(client.intelligence.start("i1", {"force_restart": True}))

    assert got["status"] == "RUNNING"
    assert rec.last.url.path == f"{_I}/i1/start"
    assert json.loads(rec.last.content) == {"force_restart": True}
