"""Contract tests for the review self-claim workflow."""

from __future__ import annotations

import inspect
import json

import httpx
import pytest

from perceivo_client import PerceivoConflictError
from perceivo_client.resources.reviews import ReviewsResource
from tests.conftest import json_handler, make_client, sequence_handler


def test_start_posts_to_exact_path_with_no_body():
    client, recorder = make_client(json_handler({}))

    client.reviews.start("r1")

    assert len(recorder.requests) == 1
    request = recorder.last
    assert request.method == "POST"
    assert request.url.path == "/v1/reviews/r1/start"
    assert request.content == b""


def test_start_and_complete_posts_in_order_and_forwards_body_unchanged():
    responses = [httpx.Response(200, json={}), httpx.Response(200, json={})]
    client, recorder = make_client(sequence_handler(responses))
    body = {"response_data": {"decision": "approve", "score": 0}}

    client.reviews.start_and_complete("r1", body)

    assert [(request.method, request.url.path) for request in recorder.requests] == [
        ("POST", "/v1/reviews/r1/start"),
        ("POST", "/v1/reviews/r1/complete"),
    ]
    assert recorder.requests[0].content == b""
    assert json.loads(recorder.requests[1].content) == body


def test_start_and_complete_stops_when_start_fails():
    client, recorder = make_client(json_handler({"detail": "not assigned"}, status=409))

    with pytest.raises(PerceivoConflictError):
        client.reviews.start_and_complete("r1", {"response_data": {"decision": "approve"}})

    assert [(request.method, request.url.path) for request in recorder.requests] == [
        ("POST", "/v1/reviews/r1/start")
    ]


def test_start_and_complete_never_calls_identity_or_assignment_routes():
    responses = [httpx.Response(200, json={}), httpx.Response(200, json={})]
    client, recorder = make_client(sequence_handler(responses))

    client.reviews.start_and_complete("r1", {"response_data": {}})

    paths = [request.url.path for request in recorder.requests]
    assert paths == ["/v1/reviews/r1/start", "/v1/reviews/r1/complete"]
    assert all("whoami" not in path and "assign" not in path for path in paths)


def test_direct_complete_requires_and_forwards_exact_body():
    client, recorder = make_client(json_handler({}))
    body = {"response_data": {"decision": "reject", "reason": "unsafe"}}

    client.reviews.complete("r1", body)

    assert recorder.last.method == "POST"
    assert recorder.last.url.path == "/v1/reviews/r1/complete"
    assert json.loads(recorder.last.content) == body
    assert (
        inspect.signature(ReviewsResource.complete).parameters["body"].default
        is inspect.Parameter.empty
    )
    assert (
        inspect.signature(ReviewsResource.start_and_complete).parameters["body"].default
        is inspect.Parameter.empty
    )
