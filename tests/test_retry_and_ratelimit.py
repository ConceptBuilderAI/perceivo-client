"""429 retry/backoff honoring Retry-After, and rate-limit header parsing."""

from __future__ import annotations

import httpx
import pytest

from perceivo_client.errors import (
    PerceivoExecutionLockedError,
    PerceivoRateLimitError,
    PerceivoServerError,
)
from perceivo_client.ratelimit import RateLimitInfo, parse_retry_after
from tests.conftest import json_handler, make_client, make_transport, sequence_handler


def _resp(status, *, headers=None, json=None):
    return httpx.Response(status, headers=headers or {}, json=json if json is not None else {})


def test_ratelimit_headers_parsed_on_success():
    headers = {
        "X-RateLimit-Limit": "600",
        "X-RateLimit-Remaining": "597",
        "X-RateLimit-Reset": "1720000000",
    }
    client, _ = make_client(json_handler({"ok": True}, headers=headers))
    client.orchestrations.list()
    rl = client.rate_limit
    assert rl is not None
    assert rl.limit == 600
    assert rl.remaining == 597
    assert rl.reset == 1720000000


def test_ratelimit_info_from_headers_case_insensitive():
    rl = RateLimitInfo.from_headers({"x-ratelimit-limit": "60", "RETRY-AFTER": "5"})
    assert rl.limit == 60
    assert rl.retry_after == 5.0


def test_parse_retry_after_seconds_and_http_date():
    assert parse_retry_after("7") == 7.0
    # HTTP-date in the past -> clamped to 0.
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("not-a-date") is None


def test_429_then_200_retries_and_succeeds():
    sleeps: list[float] = []
    responses = [
        _resp(429, headers={"Retry-After": "3"}),
        _resp(200, json={"ok": True}),
    ]
    transport, rec = make_transport(sequence_handler(responses), sleep=sleeps.append, max_retries=3)
    resp = transport.request("GET", "/v1/orchestrations")
    assert resp.status_code == 200
    assert len(rec.requests) == 2  # one retry
    assert sleeps == [3.0]  # honored Retry-After, not exponential backoff


def test_429_exhausts_retries_and_raises_typed_error():
    sleeps: list[float] = []
    headers = {"Retry-After": "1", "X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "0"}
    transport, rec = make_transport(
        json_handler(
            {"error_code": "RATE_LIMITED", "message": "slow down"}, status=429, headers=headers
        ),
        sleep=sleeps.append,
        max_retries=2,
    )
    with pytest.raises(PerceivoRateLimitError) as exc_info:
        transport.request("GET", "/v1/orchestrations")
    err = exc_info.value
    assert err.status_code == 429
    assert err.retry_after == 1.0
    assert err.rate_limit is not None
    assert err.rate_limit.limit == 60
    # initial attempt + 2 retries = 3 requests; 2 sleeps between them.
    assert len(rec.requests) == 3
    assert sleeps == [1.0, 1.0]


def test_backoff_falls_back_to_exponential_without_retry_after():
    sleeps: list[float] = []
    responses = [_resp(503), _resp(503), _resp(200, json={})]
    transport, _ = make_transport(
        sequence_handler(responses),
        sleep=sleeps.append,
        max_retries=3,
        backoff_factor=0.5,
    )
    transport.request("GET", "/v1/orchestrations")
    # 0.5 * 2**0, 0.5 * 2**1
    assert sleeps == [0.5, 1.0]


def test_no_retry_when_max_retries_zero():
    sleeps: list[float] = []
    transport, rec = make_transport(
        json_handler({}, status=429), sleep=sleeps.append, max_retries=0
    )
    with pytest.raises(PerceivoRateLimitError):
        transport.request("GET", "/v1/orchestrations")
    assert len(rec.requests) == 1
    assert sleeps == []


@pytest.mark.parametrize(
    ("status", "error_type"),
    [(429, PerceivoRateLimitError), (503, PerceivoServerError)],
)
def test_real_client_does_not_replay_post_errors(status, error_type):
    """Count requests through a real Client, not by patching its retry loop."""
    requests = 0

    def handler(_request):
        nonlocal requests
        requests += 1
        return _resp(status, headers={"Retry-After": "7"})

    client, _rec = make_client(handler, max_retries=3)
    sleeps: list[float] = []
    client._transport._sleep = sleeps.append
    with pytest.raises(error_type):
        client.orchestrations.create({"name": "must-not-replay"})
    assert requests == 1
    assert sleeps == []


def test_real_client_retries_get_to_budget_and_honors_retry_after():
    """A GET receives its initial attempt plus ``max_retries`` retries."""
    requests = 0

    def handler(_request):
        nonlocal requests
        requests += 1
        if requests <= 2:
            return _resp(429, headers={"Retry-After": "7"})
        return _resp(200, json={"items": [], "total": 0})

    client, _rec = make_client(handler, max_retries=2)
    sleeps: list[float] = []
    client._transport._sleep = sleeps.append
    client.orchestrations.list()
    assert requests == 3  # initial request + max_retries
    assert sleeps == [7.0, 7.0]


@pytest.mark.parametrize(
    ("method", "status", "error_type"),
    [
        (method, 429, PerceivoRateLimitError)
        for method in ("POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
    ]
    + [
        (method, status, PerceivoServerError)
        for method in ("POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
        for status in (502, 503, 504)
    ],
)
def test_non_get_methods_make_one_attempt_for_retry_statuses(method, status, error_type):
    transport, rec = make_transport(
        json_handler({}, status=status), sleep=lambda _seconds: None, max_retries=3
    )
    with pytest.raises(error_type):
        transport.request(method, "/v1/mutations", json={"id": "one-attempt"})
    assert len(rec.requests) == 1


def test_address_limiter_headers_are_parsed_alongside_the_key_budget():
    headers = {
        "X-RateLimit-Limit": "600",
        "X-RateLimit-Remaining": "599",
        "X-RateLimit-Reset": "1720000000",
        "Perceivo-RateLimit-Limit": "1000",
        "Perceivo-RateLimit-Remaining": "998",
        "Perceivo-RateLimit-Reset": "1720000060",
    }
    client, _ = make_client(json_handler({"ok": True}, headers=headers))
    client.orchestrations.list()
    rl = client.rate_limit
    assert (rl.limit, rl.remaining, rl.reset) == (600, 599, 1720000000)
    assert (rl.address_limit, rl.address_remaining, rl.address_reset) == (1000, 998, 1720000060)


def test_address_limiter_fields_are_none_when_that_limiter_did_not_run():
    rl = RateLimitInfo.from_headers({"X-RateLimit-Limit": "600"})
    assert (rl.address_limit, rl.address_remaining, rl.address_reset) == (None, None, None)


@pytest.mark.parametrize(
    "body",
    [
        {"detail": {"code": "execution_locked", "message": "Organization is execution-locked"}},
        {"error_code": "PCV-CORE-RATE-0001", "message": "{'code': 'execution_locked'}"},
    ],
)
def test_get_answering_execution_locked_is_not_retried(body):
    """Waiting cannot clear an execution lock, so a GET makes one attempt."""
    slept: list[float] = []
    transport, rec = make_transport(
        sequence_handler([_resp(429, json=body), _resp(200, json={"ok": True})]),
        sleep=slept.append,
        max_retries=3,
    )
    with pytest.raises(PerceivoExecutionLockedError):
        transport.request("GET", "/v1/orchestrations")
    assert len(rec.requests) == 1
    assert slept == []


def test_get_answering_a_rate_limit_429_is_still_retried():
    """Control for the execution-lock case: a real rate limit retries and succeeds."""
    slept: list[float] = []
    body = {"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}}
    transport, rec = make_transport(
        sequence_handler(
            [_resp(429, json=body, headers={"Retry-After": "2"}), _resp(200, json={"ok": True})]
        ),
        sleep=slept.append,
        max_retries=3,
    )
    assert transport.request("GET", "/v1/orchestrations").status_code == 200
    assert len(rec.requests) == 2
    assert slept == [2.0]
