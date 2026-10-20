"""Retry behavior for HMAC-signed transport requests.

Kept separate from the core transport-signing tests so retry semantics remain a
focused subject.
"""

from __future__ import annotations

import hmac

import httpx
import pytest

from perceivo_client.errors import PerceivoRateLimitError
from perceivo_client.signing import (
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    verify_signature,
)
from tests.conftest import json_handler, sequence_handler
from tests.test_transport_signing import (
    SECRET,
    assert_api_verifies,
    recompute,
    signer,
    spy_transport,
)


def _retry_handler():
    return sequence_handler(
        [
            httpx.Response(503, json={"detail": "unavailable"}),
            httpx.Response(503, json={"detail": "unavailable"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )


def test_signed_post_429_is_one_exactly_signed_body_attempt():
    """A signed mutation cannot be replayed after a rate-limit response."""
    transport, recorder, _spy = spy_transport(
        json_handler({"detail": "slow down"}, status=429), signer=signer(), max_retries=3
    )
    with pytest.raises(PerceivoRateLimitError):
        transport.request("POST", "/v1/x", content=b"\x00retry-body\xff")
    assert len(recorder.requests) == 1
    request = recorder.last
    assert request.content == b"\x00retry-body\xff"
    assert_api_verifies(request)


def test_each_retry_attempt_gets_a_fresh_nonce():
    transport, recorder, _spy = spy_transport(_retry_handler(), signer=signer(), max_retries=2)
    transport.request("GET", "/v1/orchestrations")
    nonces = [r.headers[HEADER_NONCE] for r in recorder.requests]
    assert len(nonces) == 3
    assert len(set(nonces)) == 3


def test_each_retry_attempt_gets_a_fresh_timestamp():
    ticks = iter([1767225600, 1767225601, 1767225602])
    transport, recorder, _spy = spy_transport(
        _retry_handler(), signer=signer(clock=lambda: next(ticks)), max_retries=2
    )
    transport.request("GET", "/v1/orchestrations")
    stamps = [r.headers[HEADER_TIMESTAMP] for r in recorder.requests]
    assert stamps == ["1767225600", "1767225601", "1767225602"]


def test_every_retry_attempt_is_independently_valid():
    transport, recorder, _spy = spy_transport(_retry_handler(), signer=signer(), max_retries=2)
    transport.request("GET", "/v1/orchestrations")
    for request in recorder.requests:
        assert_api_verifies(request)


def test_retry_signatures_are_not_reused():
    transport, recorder, _spy = spy_transport(_retry_handler(), signer=signer(), max_retries=2)
    transport.request("GET", "/v1/orchestrations")
    signatures = [r.headers[HEADER_SIGNATURE] for r in recorder.requests]
    assert len(set(signatures)) == 3
    first, second = signatures[0], signatures[1]
    assert not hmac.compare_digest(first, second)


def test_a_retry_signature_does_not_validate_a_different_attempt():
    transport, recorder, _spy = spy_transport(_retry_handler(), signer=signer(), max_retries=2)
    transport.request("GET", "/v1/orchestrations")
    first, second = recorder.requests[0], recorder.requests[1]
    assert not verify_signature(second.headers[HEADER_SIGNATURE], recompute(first), SECRET)
