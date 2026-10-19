"""``client.queue``: each call pinned by method, path, query and body.

The method/path wrapper cases cannot see query parameters or bodies, and every
queue operation carries its selector there (``kind`` and ``asset_id``), so the
exact request is pinned here.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import AsyncClient
from perceivo_client.generated.models import (
    ActivityResponse,
    BulkCancelResponse,
    CancelInputResponse,
    CapabilityQueueDepthRead,
    CapabilityQueuePurgeResult,
    QueueItem,
)
from tests.conftest import BASE_URL, json_handler, make_client

_CAPABILITY = "0f8fad5b-d9cb-469f-a165-70867728950e"
_ITEM = "c0a8012e-7b1d-4c58-8f43-2f6f5a0c9e77"


def test_list_reads_the_capabilitys_inputs():
    client, rec = make_client(json_handler({}))

    result = client.queue.list(_CAPABILITY)

    assert len(rec.requests) == 1
    assert rec.last.method == "GET"
    assert rec.last.url.path == "/v1/queue"
    assert dict(rec.last.url.params) == {"kind": "input", "asset_id": _CAPABILITY}
    assert rec.last.content == b""
    assert isinstance(result, ActivityResponse)


def test_summary_reads_the_capabilitys_queue_depth():
    client, rec = make_client(json_handler({}))

    result = client.queue.get_summary(_CAPABILITY)

    assert len(rec.requests) == 1
    assert rec.last.method == "GET"
    assert rec.last.url.path == "/v1/queue/summary"
    assert dict(rec.last.url.params) == {"kind": "input", "asset_id": _CAPABILITY}
    assert rec.last.content == b""
    assert isinstance(result, CapabilityQueueDepthRead)


def test_cancel_item_deletes_one_input_and_names_the_kind():
    client, rec = make_client(json_handler({}))

    result = client.queue.cancel_item(_ITEM)

    assert len(rec.requests) == 1
    assert rec.last.method == "DELETE"
    assert rec.last.url.path == f"/v1/queue/{_ITEM}"
    assert dict(rec.last.url.params) == {"kind": "input"}
    assert rec.last.content == b""
    assert isinstance(result, CancelInputResponse)


@pytest.mark.parametrize(
    ("include_running", "served", "model"),
    [
        (
            False,
            {"capability_id": _CAPABILITY, "cancelled_requests": 2, "purged_queue_keys": 1},
            CapabilityQueuePurgeResult,
        ),
        (True, {}, BulkCancelResponse),
    ],
    ids=["waiting_only", "running_too"],
)
def test_cancel_posts_the_selector_as_the_body(include_running, served, model):
    client, rec = make_client(json_handler(served))

    result = client.queue.cancel(_CAPABILITY, include_running=include_running)

    assert len(rec.requests) == 1
    assert rec.last.method == "POST"
    assert rec.last.url.path == "/v1/queue/cancel"
    assert dict(rec.last.url.params) == {}
    assert json.loads(rec.last.content) == {
        "kind": "input",
        "asset_id": _CAPABILITY,
        "include_running": include_running,
    }
    assert isinstance(result, model)


def test_cancel_requires_include_running_and_reaches_no_wire_without_it():
    """The API requires the flag and the operation cannot be undone."""
    client, rec = make_client(json_handler({}))
    call = client.queue.cancel

    with pytest.raises(TypeError, match="include_running"):
        call(_CAPABILITY)

    assert rec.requests == []


def test_the_capability_scoped_queue_methods_are_gone():
    client, _rec = make_client(json_handler({}))

    present = [
        name
        for name in ("activity", "bulk_cancel_activity", "cancel_activity", "queue")
        if hasattr(client.capabilities, name)
    ]

    assert present == []


def test_the_async_client_mirrors_the_queue_namespace():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path, dict(request.url.params)))
        return httpx.Response(200, json={})

    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)),
    )

    result = asyncio.run(client.queue.get_summary(_CAPABILITY))

    assert isinstance(result, CapabilityQueueDepthRead)
    assert seen == [("GET", "/v1/queue/summary", {"kind": "input", "asset_id": _CAPABILITY})]


def test_list_parses_the_projected_items_and_carries_no_input_payload():
    # The API answers a projection; an item has no payload field.
    served = {
        "queued": [{"id": _ITEM, "status": "queued", "capability_id": _CAPABILITY}],
        "running": [],
        "recent": [],
        "counts": {"queued": 1, "running": 0, "completed": 0, "failed": 0, "cancelled": 0},
    }
    client, _ = make_client(json_handler(served))

    result = client.queue.list(_CAPABILITY)

    assert isinstance(result.queued[0], QueueItem)
    assert result.queued[0].id == _ITEM
    assert result.counts is not None and result.counts.queued == 1
    assert not [name for name in QueueItem.model_fields if "payload" in name]
    assert not [name for name in type(result).model_fields if "payload" in name]
