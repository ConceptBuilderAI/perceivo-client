"""Webhook signature verification against deliveries signed as the platform signs them.

The reference signer below is an independent implementation of the platform's
delivery signing: HMAC-SHA256, keyed by the webhook's secret (UTF-8 encoded),
over ``<Perceivo-Timestamp>.<Perceivo-Delivery-Id>.<raw body>``, sent as
``Perceivo-Signature: v1=<hex>``. A verifier that signs the body alone fails
these tests.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time

import pytest

import perceivo_client.webhooks as webhooks_module
from perceivo_client import compute_webhook_signature, verify_webhook

SECRET = "whsec_test_secret_at_least_32_chars_long!!"
BODY = b'{"created_at":"2026-10-03T00:00:00Z","event_type":"run.completed","data":{"run_id":"r1"}}'
DELIVERY_ID = "3f2b8c1e-9a4d-4e6f-8b7a-1c2d3e4f5a6b"
OTHER_DELIVERY_ID = "3f2b8c1e-9a4d-4e6f-8b7a-1c2d3e4f5a6c"
NOW = 1_600_000_000
_REAL_TIME = time.time

# ---- reference signer -------------------------------------------------------
_TIMESTAMP = re.compile(r"[1-9][0-9]{0,11}")
_DELIVERY_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _reference_signing_base(timestamp: str, delivery_id: str, body: bytes) -> bytes:
    if _TIMESTAMP.fullmatch(timestamp) is None:
        raise ValueError("Perceivo-Timestamp must be integer Unix seconds")
    if _DELIVERY_ID.fullmatch(delivery_id) is None:
        raise ValueError("Perceivo-Delivery-Id must be a lowercase canonical UUID")
    return timestamp.encode("ascii") + b"." + delivery_id.encode("ascii") + b"." + body


def _reference_sign_delivery(secret: bytes, timestamp: str, delivery_id: str, body: bytes) -> str:
    digest = hmac.new(secret, _reference_signing_base(timestamp, delivery_id, body), hashlib.sha256)
    return f"v1={digest.hexdigest()}"


def _reference_signed_headers(
    secret: bytes, delivery_id: str, body: bytes, now: int
) -> dict[str, str]:
    timestamp = str(now)
    return {
        "Content-Type": "application/json",
        "Perceivo-Timestamp": timestamp,
        "Perceivo-Delivery-Id": delivery_id,
        "Perceivo-Signature": _reference_sign_delivery(secret, timestamp, delivery_id, body),
    }


# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _frozen_clock(monkeypatch):
    monkeypatch.setattr(webhooks_module.time, "time", lambda: float(NOW))


def _delivery(body: bytes = BODY, secret: str = SECRET, now: int = NOW) -> dict[str, str]:
    return _reference_signed_headers(secret.encode(), DELIVERY_ID, body, now)


def _verify(body: bytes, headers: dict[str, str], secret: str | bytes = SECRET, **kwargs) -> bool:
    return verify_webhook(
        body,
        secret=secret,
        signature=headers["Perceivo-Signature"],
        timestamp=headers["Perceivo-Timestamp"],
        delivery_id=headers["Perceivo-Delivery-Id"],
        **kwargs,
    )


def test_accepts_a_delivery_signed_exactly_as_the_platform_signs_it():
    headers = _delivery()
    assert headers["Perceivo-Signature"].startswith("v1=")
    assert _verify(BODY, headers) is True


def test_accepts_bytes_secret_int_timestamp_and_bytearray_body():
    headers = _delivery()
    assert (
        verify_webhook(
            bytearray(BODY),
            secret=SECRET.encode(),
            signature=headers["Perceivo-Signature"],
            timestamp=NOW,
            delivery_id=DELIVERY_ID,
        )
        is True
    )


def test_rejects_a_signature_over_the_body_alone():
    body_only = "v1=" + hmac.new(SECRET.encode(), BODY, hashlib.sha256).hexdigest()
    headers = {**_delivery(), "Perceivo-Signature": body_only}
    assert _verify(BODY, headers) is False


def test_rejects_a_tampered_body():
    assert _verify(BODY + b" ", _delivery()) is False


def test_rejects_a_wrong_timestamp():
    headers = {**_delivery(), "Perceivo-Timestamp": str(NOW - 1)}
    assert _verify(BODY, headers) is False


def test_rejects_a_wrong_delivery_id():
    headers = {**_delivery(), "Perceivo-Delivery-Id": OTHER_DELIVERY_ID}
    assert _verify(BODY, headers) is False


def test_rejects_a_wrong_secret():
    assert _verify(BODY, _delivery(), secret="the_wrong_secret_value_padded_out_here") is False


def test_rejects_an_expired_timestamp_even_with_a_valid_signature():
    stale = _delivery(now=NOW - 301)
    assert _verify(BODY, stale) is False
    assert _verify(BODY, stale, tolerance=None) is True


def test_rejects_a_timestamp_too_far_in_the_future():
    assert _verify(BODY, _delivery(now=NOW + 301)) is False


def test_tolerance_boundary_and_override():
    edge = _delivery(now=NOW - 300)
    assert _verify(BODY, edge) is True
    assert _verify(BODY, edge, tolerance=299) is False
    assert _verify(BODY, _delivery(now=NOW - 3600), tolerance=3600) is True


def test_the_default_tolerance_reads_the_real_clock(monkeypatch):
    monkeypatch.setattr(webhooks_module.time, "time", _REAL_TIME)
    fresh = _reference_signed_headers(SECRET.encode(), DELIVERY_ID, BODY, int(_REAL_TIME()))
    assert _verify(BODY, fresh) is True
    assert _verify(BODY, _delivery()) is False  # NOW is years before the real clock


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Perceivo-Signature", ""),
        ("Perceivo-Signature", "v1=deadbeef"),
        ("Perceivo-Signature", "sha256=" + "0" * 64),
        ("Perceivo-Timestamp", ""),
        ("Perceivo-Timestamp", "not-a-number"),
        ("Perceivo-Timestamp", f"{NOW}\n"),
        ("Perceivo-Delivery-Id", ""),
        ("Perceivo-Delivery-Id", DELIVERY_ID.upper()),
    ],
)
def test_malformed_headers_are_invalid_and_never_raise(field, value):
    headers = {**_delivery(), field: value}
    assert _verify(BODY, headers) is False


def test_missing_headers_are_invalid():
    headers = _delivery()
    assert (
        verify_webhook(BODY, secret=SECRET, signature=None, timestamp=NOW, delivery_id=DELIVERY_ID)
        is False
    )
    assert (
        verify_webhook(
            BODY,
            secret=SECRET,
            signature=headers["Perceivo-Signature"],
            timestamp=None,
            delivery_id=DELIVERY_ID,
        )
        is False
    )


def test_a_str_body_raises_type_error():
    headers = _delivery()
    text = BODY.decode()
    with pytest.raises(TypeError, match="raw request bytes"):
        _verify(text, headers)


def test_compute_webhook_signature_equals_the_platform_signature():
    expected = _reference_sign_delivery(SECRET.encode(), str(NOW), DELIVERY_ID, BODY)
    assert (
        compute_webhook_signature(BODY, SECRET, timestamp=NOW, delivery_id=DELIVERY_ID) == expected
    )
    assert (
        compute_webhook_signature(
            BODY, SECRET.encode(), timestamp=str(NOW), delivery_id=DELIVERY_ID
        )
        == expected
    )


def test_compute_webhook_signature_refuses_fields_the_platform_would_refuse():
    with pytest.raises(ValueError, match="timestamp"):
        compute_webhook_signature(BODY, SECRET, timestamp="0", delivery_id=DELIVERY_ID)
    with pytest.raises(ValueError, match="delivery_id"):
        compute_webhook_signature(BODY, SECRET, timestamp=NOW, delivery_id="dlv_1")
    text = BODY.decode()
    with pytest.raises(TypeError):
        compute_webhook_signature(text, SECRET, timestamp=NOW, delivery_id=DELIVERY_ID)


# ---- receiver-side configuration is refused, not keyed on --------------------


def test_an_empty_secret_raises_even_for_a_delivery_signed_with_the_empty_key():
    # Anyone can compute an HMAC under the empty key, so a delivery signed with it
    # must not verify against an unset secret: the call refuses the secret first.
    forged = _reference_signed_headers(b"", DELIVERY_ID, BODY, NOW)
    with pytest.raises(ValueError, match="must not be empty"):
        _verify(BODY, forged, secret="")


@pytest.mark.parametrize("secret", ["", b"", bytearray()])
def test_every_empty_secret_spelling_raises_value_error(secret):
    headers = _delivery()
    with pytest.raises(ValueError, match="must not be empty"):
        _verify(BODY, headers, secret=secret)


@pytest.mark.parametrize("secret", [0, 32, None, 1.5, ["k"], memoryview(b"k")])
def test_a_non_text_non_bytes_secret_raises_type_error(secret):
    # ``bytes(32)`` is thirty-two zero bytes: an int secret must not become a key.
    headers = _delivery()
    with pytest.raises(TypeError, match="str or bytes"):
        _verify(BODY, headers, secret=secret)


def test_a_zero_byte_key_signature_is_not_accepted_under_an_int_secret():
    forged = _reference_signed_headers(bytes(32), DELIVERY_ID, BODY, NOW)
    with pytest.raises(TypeError, match="str or bytes"):
        _verify(BODY, forged, secret=32)


def test_the_secret_is_refused_before_any_header_is_read():
    with pytest.raises(ValueError, match="must not be empty"):
        verify_webhook(BODY, secret="", signature=None, timestamp=None, delivery_id=None)


def test_compute_webhook_signature_refuses_an_empty_secret():
    with pytest.raises(ValueError, match="must not be empty"):
        compute_webhook_signature(BODY, b"", timestamp=NOW, delivery_id=DELIVERY_ID)


def test_a_bytearray_secret_is_still_accepted():
    assert _verify(BODY, _delivery(), secret=bytearray(SECRET.encode())) is True


@pytest.mark.parametrize("tolerance", [float("nan"), float("inf"), float("-inf"), -1, -0.5])
def test_a_non_finite_or_negative_tolerance_raises_value_error(tolerance):
    # A NaN window would disable the replay check: ``abs(skew) > nan`` is always False.
    stale = _delivery(now=NOW - 10**6)
    with pytest.raises(ValueError, match="finite, non-negative"):
        _verify(BODY, stale, tolerance=tolerance)


@pytest.mark.parametrize("tolerance", [True, "300", b"300"])
def test_a_non_numeric_tolerance_raises_type_error(tolerance):
    headers = _delivery()
    with pytest.raises(TypeError, match="tolerance"):
        _verify(BODY, headers, tolerance=tolerance)


def test_a_stale_delivery_is_rejected_under_a_float_tolerance():
    assert _verify(BODY, _delivery(now=NOW - 301), tolerance=300.0) is False


def test_a_zero_tolerance_accepts_only_the_current_second():
    assert _verify(BODY, _delivery(), tolerance=0) is True


def test_a_zero_tolerance_rejects_one_second_of_skew():
    assert _verify(BODY, _delivery(now=NOW - 1), tolerance=0) is False


@pytest.mark.parametrize("timestamp", [True, False])
def test_a_bool_timestamp_returns_false_and_never_raises(timestamp):
    headers = _delivery()
    result = verify_webhook(
        BODY,
        secret=SECRET,
        signature=headers["Perceivo-Signature"],
        timestamp=timestamp,
        delivery_id=DELIVERY_ID,
    )
    assert result is False


def test_compute_webhook_signature_still_refuses_a_bool_timestamp():
    with pytest.raises(TypeError, match="timestamp"):
        compute_webhook_signature(BODY, SECRET, timestamp=True, delivery_id=DELIVERY_ID)
