"""Webhook signature verification helper.

Perceivo signs every webhook delivery with three headers:

- ``Perceivo-Timestamp``: integer Unix seconds at the moment of the attempt;
- ``Perceivo-Delivery-Id``: the delivery's lowercase canonical UUID;
- ``Perceivo-Signature``: ``v1=`` followed by 64 lowercase hex digits.

The signature is HMAC-SHA256, keyed by the webhook's secret (UTF-8 encoded),
over the signing string::

    <Perceivo-Timestamp> + "." + <Perceivo-Delivery-Id> + "." + <raw body bytes>

Receivers call :func:`verify_webhook` with the raw request body and the three
header values to confirm a delivery is authentic, and recent, before trusting
it. :func:`compute_webhook_signature` produces the ``Perceivo-Signature`` value,
for example to build a test delivery.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import re
import time

#: Header names the platform sends on every delivery.
TIMESTAMP_HEADER = "Perceivo-Timestamp"
DELIVERY_ID_HEADER = "Perceivo-Delivery-Id"
SIGNATURE_HEADER = "Perceivo-Signature"

#: Default replay window, in seconds, either side of the receiver's clock.
DEFAULT_TOLERANCE_SECONDS = 300

_SIGNATURE_PREFIX = "v1="
# The same shapes the platform checks before it signs.
_TIMESTAMP = re.compile(r"[1-9][0-9]{0,11}")
_DELIVERY_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _body_bytes(body: bytes | bytearray | memoryview) -> bytes:
    if isinstance(body, str):
        raise TypeError(
            "webhook body must be the raw request bytes, not str; "
            "pass the body exactly as received (for example `await request.body()`)"
        )
    if not isinstance(body, (bytes, bytearray, memoryview)):
        raise TypeError(f"webhook body must be bytes, got {type(body).__name__}")
    return bytes(body)


def _secret_bytes(secret: str | bytes) -> bytes:
    # Only text or bytes is a secret. ``bytes(secret)`` on an ``int`` builds that
    # many zero bytes, and an empty key signs with a value anyone can reproduce, so
    # both are refused rather than keyed on.
    if isinstance(secret, str):
        key = secret.encode("utf-8")
    elif isinstance(secret, (bytes, bytearray)):
        key = bytes(secret)
    else:
        raise TypeError(f"webhook secret must be str or bytes, got {type(secret).__name__}")
    if not key:
        raise ValueError("webhook secret must not be empty")
    return key


def _checked_tolerance(tolerance: float | None) -> float | None:
    if tolerance is None:
        return None
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise TypeError(f"tolerance must be a number of seconds, got {type(tolerance).__name__}")
    # NaN compares False against everything, so ``abs(skew) > nan`` would accept
    # every timestamp; a negative window would refuse every delivery.
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a finite, non-negative number of seconds, or None")
    return tolerance


def _timestamp_text(timestamp: str | int) -> str:
    if isinstance(timestamp, bool):
        raise TypeError("timestamp must be the Perceivo-Timestamp header value")
    return str(timestamp) if isinstance(timestamp, int) else timestamp


def _signing_string(timestamp: str, delivery_id: str, body: bytes) -> bytes:
    return timestamp.encode("ascii") + b"." + delivery_id.encode("ascii") + b"." + body


def compute_webhook_signature(
    body: bytes | bytearray | memoryview,
    secret: str | bytes,
    *,
    timestamp: str | int,
    delivery_id: str,
) -> str:
    """Compute the ``Perceivo-Signature`` header value for a delivery.

    The value is HMAC-SHA256, keyed by ``secret``, over
    ``timestamp + "." + delivery_id + "." + body``, exactly as the platform
    signs a delivery.

    Args:
        body: The delivery body bytes.
        secret: The webhook's signing secret (a ``str`` is UTF-8 encoded).
            Must be non-empty ``str`` or ``bytes``.
        timestamp: The ``Perceivo-Timestamp`` value: integer Unix seconds, as
            a string or an ``int``.
        delivery_id: The ``Perceivo-Delivery-Id`` value: a lowercase canonical
            UUID.

    Returns:
        ``v1=`` followed by 64 lowercase hexadecimal digits.

    Raises:
        TypeError: ``body`` is not bytes-like (a ``str`` included), ``secret``
            is not ``str`` or ``bytes``, or ``timestamp`` is a ``bool``.
        ValueError: ``secret`` is empty, or ``timestamp`` or ``delivery_id``
            does not have the shape the platform sends.
    """
    raw = _body_bytes(body)
    ts = _timestamp_text(timestamp)
    if not isinstance(ts, str) or _TIMESTAMP.fullmatch(ts) is None:
        raise ValueError("timestamp must be integer Unix seconds")
    if not isinstance(delivery_id, str) or _DELIVERY_ID.fullmatch(delivery_id) is None:
        raise ValueError("delivery_id must be a lowercase canonical UUID")
    digest = hmac.new(_secret_bytes(secret), _signing_string(ts, delivery_id, raw), hashlib.sha256)
    return _SIGNATURE_PREFIX + digest.hexdigest()


def verify_webhook(
    body: bytes | bytearray | memoryview,
    *,
    secret: str | bytes,
    signature: str | None,
    timestamp: str | int | None,
    delivery_id: str | None,
    tolerance: float | None = DEFAULT_TOLERANCE_SECONDS,
) -> bool:
    """Verify a webhook delivery exactly as the platform signs it.

    Args:
        body: The raw request body bytes exactly as received, before any JSON
            parsing. Re-serializing parsed JSON will not match. A ``str``
            raises :class:`TypeError` rather than being encoded, because a
            decoded-then-re-encoded body is not guaranteed to be the bytes
            that were signed.
        secret: The webhook's signing secret, as given when it was registered
            (a ``str`` is UTF-8 encoded). Must be non-empty ``str`` or
            ``bytes``.
        signature: The ``Perceivo-Signature`` header value, ``v1=<hex>``.
        timestamp: The ``Perceivo-Timestamp`` header value (integer Unix
            seconds, as the header string or an ``int``).
        delivery_id: The ``Perceivo-Delivery-Id`` header value.
        tolerance: Replay window in seconds. The delivery is rejected when
            its timestamp is more than ``tolerance`` seconds from the
            receiver's clock in either direction. Default 300. Must be a
            finite, non-negative number. ``None`` disables the check; the
            signature is still verified.

    Returns:
        ``True`` only if all three headers are well formed, the timestamp is
        inside the tolerance, and the HMAC-SHA256 over
        ``timestamp + "." + delivery_id + "." + body`` matches in constant
        time. ``False`` otherwise; a missing or malformed header is simply an
        invalid delivery and never raises.

    Raises:
        TypeError: ``body`` is not bytes-like, ``secret`` is not ``str`` or
            ``bytes``, or ``tolerance`` is not a number.
        ValueError: ``secret`` is empty, or ``tolerance`` is negative or not
            finite.

    These are configuration errors on the receiver's side and are raised
    before any header is read; nothing a sender controls raises.

    Deduplicate on ``delivery_id``: a delivery may arrive more than once.
    """
    raw = _body_bytes(body)
    key = _secret_bytes(secret)
    window = _checked_tolerance(tolerance)
    if not signature or timestamp is None or not delivery_id:
        return False
    if isinstance(timestamp, bool):
        return False
    ts = _timestamp_text(timestamp)
    if not isinstance(ts, str) or _TIMESTAMP.fullmatch(ts) is None:
        return False
    if not isinstance(delivery_id, str) or _DELIVERY_ID.fullmatch(delivery_id) is None:
        return False
    if window is not None and abs(time.time() - int(ts)) > window:
        return False
    expected = compute_webhook_signature(raw, key, timestamp=ts, delivery_id=delivery_id)
    received = signature.strip() if isinstance(signature, str) else ""
    return hmac.compare_digest(expected.encode("ascii"), received.encode("utf-8"))
