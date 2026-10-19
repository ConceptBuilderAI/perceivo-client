"""Signing constants and the API-side verifier shared by the transport signing tests."""

from __future__ import annotations

import httpx

from perceivo_client.signing import (
    HEADER_KEY_ID,
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    build_canonical_request,
    split_target,
    verify_signature,
)

KEY_ID = "9efa4550-e04e-4624-a6f2-684af0330f23"
SECRET = "transport-test-signing-secret"
AUDIENCE = "perceivo-api-local"


def recompute(request: httpx.Request) -> str:
    """Rebuild the canonical request the API verifies, from what the mock received.

    Every input except the audience is read back off the *sent* request, so a
    signature computed over anything other than what went out fails here. The
    audience is the one field with no wire
    representation (it is configuration on both ends), so it comes from the
    same constant the signer was built with.

    ``content_type`` is read with ``get_list`` rather than ``get``: httpx joins
    repeated values with ``", "``, which would silently synthesise a single header
    the request never carried and hide the repeated-header rejection.
    """
    raw_path, query = split_target(request.url.raw_path.decode("ascii"))
    return build_canonical_request(
        audience=AUDIENCE,
        key_id=request.headers[HEADER_KEY_ID],
        method=request.method,
        raw_path=raw_path,
        query_string=query,
        body=request.content,
        content_type=request.headers.get_list("content-type") or None,
        organization=request.headers.get_list("perceivo-organization") or None,
        timestamp=request.headers[HEADER_TIMESTAMP],
        nonce=request.headers[HEADER_NONCE],
    )


def assert_api_verifies(request: httpx.Request) -> None:
    """The signature on ``request`` verifies as the API verifies it."""
    assert verify_signature(request.headers[HEADER_SIGNATURE], recompute(request), SECRET)
