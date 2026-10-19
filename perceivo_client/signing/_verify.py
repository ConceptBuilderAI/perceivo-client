"""Signature computation and verification.

The verification functions return ``False`` for malformed input rather than
raising, and compare digests with ``hmac.compare_digest``.
"""

from __future__ import annotations

import hashlib
import hmac

from perceivo_client.signing._constants import (
    CANONICAL_DOMAIN,
    CANONICAL_FIELD_COUNT,
    SIGNATURE_PREFIX,
    SecretType,
)
from perceivo_client.signing._secret import secret_to_key_bytes
from perceivo_client.signing.canonical import (
    SigningError,
    canonical_audience,
    canonical_key_id,
)

__all__ = [
    "compute_signature",
    "verify_signature",
    "verify_signed_request",
]


def _is_utf8_encodable(value: object) -> bool:
    """Return ``True`` if ``value`` is a ``str`` that can be encoded as UTF-8.

    A ``str`` containing a lone surrogate such as ``"\\ud800"`` cannot be encoded,
    and a JSON decoder produces one from the escape ``\\ud800``. Checking first
    lets verification return ``False`` for such input instead of raising
    ``UnicodeEncodeError``.
    """
    if not isinstance(value, str):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _digest_equal(received: str, expected: str) -> bool:
    """Compare two strings in constant time, returning ``False`` for non-ASCII input.

    ``hmac.compare_digest`` raises ``TypeError`` when a ``str`` operand contains a
    non-ASCII character. Every ``expected`` value compared here (the canonical
    domain, an audience or a lowercase UUID) is ASCII, so a non-ASCII ``received``
    value can never be equal to it and ``False`` is the correct answer. The ASCII
    check reveals only whether the caller's own input was ASCII.

    ``received`` is untrusted input. ``expected`` is the verifier's own
    configuration; a non-``str`` value there raises, so a misconfiguration is
    reported rather than silently rejecting every request.
    """
    if not received.isascii() or not expected.isascii():
        return False
    return hmac.compare_digest(received, expected)


def compute_signature(canonical_request: str, secret: SecretType) -> str:
    """Return the ``X-Perceivo-Signature`` value for a canonical request.

    Args:
        canonical_request: The canonical request string.
        secret: The signing secret; see
            :func:`~perceivo_client.signing._secret.secret_to_key_bytes`.

    Returns:
        ``v1=`` followed by the 64 lowercase hex characters of the HMAC-SHA256
        digest. The server requires the ``v1=`` prefix.

    Raises:
        SigningError: If ``canonical_request`` is not a ``str`` or the secret is
            invalid.
    """
    if not isinstance(canonical_request, str):
        raise SigningError("canonical_request must be str")
    digest = hmac.new(
        secret_to_key_bytes(secret), canonical_request.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def verify_signature(signature: str, canonical_request: str, secret: SecretType) -> bool:
    """Check a ``v1=`` signature against a canonical request in constant time.

    Use it to check an implementation against the published golden vectors.

    Args:
        signature: The ``X-Perceivo-Signature`` value.
        canonical_request: The canonical request string.
        secret: The signing secret.

    Returns:
        ``True`` if the signature is valid. ``False`` for an invalid signature,
        a signature that is not a ``v1=`` value, or a canonical request that
        cannot be encoded as UTF-8.

    Raises:
        SigningError: If ``secret`` is invalid. The secret is the verifier's own
            configuration, so a misconfiguration is reported rather than
            returned as ``False``.

    Security notes:
        This is a MAC check and nothing else. It does not check the domain,
        audience or key id (see :func:`verify_signed_request`), timestamp
        freshness or nonce reuse, so on its own it accepts a replayed request.
    """
    if not _is_utf8_encodable(canonical_request):
        return False
    if (
        not isinstance(signature, str)
        or not signature.isascii()
        or not signature.startswith(SIGNATURE_PREFIX)
    ):
        return False
    expected = compute_signature(canonical_request, secret)
    return hmac.compare_digest(expected, signature)


def verify_signed_request(
    *,
    signature: str,
    canonical_request: str,
    secret: SecretType,
    audience: str,
    key_id: str,
) -> bool:
    """Verify a signature and the fields a verifier binds to its own values.

    This is not a complete server verifier. A server must add three checks that
    this function does not perform, because it has no clock, nonce store or
    request headers:

    1. Timestamp freshness: reject the request unless field 10 is within
       :data:`MAX_CLOCK_SKEW_SECONDS` of the server clock.
    2. Nonce single-use: reject the request if field 11 has been seen before,
       remembering nonces for at least the clock-skew window.
    3. Organization binding: after ``hmac.compare_digest`` has accepted the
       signature, compare field 9 with the ``Perceivo-Organization`` header the
       server received, and reject any difference.

    Fields are numbered from 1, so field ``n`` is ``fields[n - 1]``. Without the
    first two checks a captured request can be replayed; without the third a
    captured signature can be presented with a different organization. This
    function accepts the ``n07-organization-metadata-unbound`` negative vector for
    that reason.

    The function returns ``True`` only if all of the following hold:

    1. the canonical request has :data:`CANONICAL_FIELD_COUNT` fields;
    2. field 1 equals :data:`CANONICAL_DOMAIN`;
    3. field 2 equals ``audience``, the audience this deployment is configured
       with;
    4. field 3 equals ``key_id``, the id of the key whose secret was looked up;
    5. ``signature`` is a valid MAC of the canonical request under ``secret``.

    Checks 1 to 4 run before the MAC comparison. Every failure returns the same
    ``False``, so a caller cannot tell which check failed. Field 8,
    ``Content-Type``, needs no binding: the server builds it from the header it
    received, and the signature proves the client sent that value.

    Args:
        signature: The ``X-Perceivo-Signature`` value.
        canonical_request: The canonical request string.
        secret: The signing secret for ``key_id``.
        audience: The verifier's configured audience.
        key_id: The key id the verifier resolved for the request. On a server
            this comes from the authenticated credential, not from a request
            header.

    Returns:
        ``True`` if every check passes, otherwise ``False``. Malformed input
        returns ``False`` and never raises.
    """
    if not _is_utf8_encodable(canonical_request):
        return False
    try:
        expected_audience = canonical_audience(audience)
        expected_key_id = canonical_key_id(key_id)
    except SigningError:
        # A misconfigured verifier fails closed and reveals no more to the caller
        # than an invalid signature would.
        return False

    fields = canonical_request.split("\n")
    if len(fields) != CANONICAL_FIELD_COUNT:
        return False
    if not _digest_equal(fields[0], CANONICAL_DOMAIN):
        return False
    if not _digest_equal(fields[1], expected_audience):
        return False
    if not _digest_equal(fields[2], expected_key_id):
        return False
    return verify_signature(signature, canonical_request, secret)
