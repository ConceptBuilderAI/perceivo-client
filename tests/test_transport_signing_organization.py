"""Field 9 exercised end to end through ``Transport``, with a real header.

The signed field is compared against literals rather than a re-read of the header.
"""

from __future__ import annotations

import httpx
import pytest

from perceivo_client.signing import HEADER_SIGNATURE, SigningError
from tests.test_transport_signing import (
    SECRET,
    assert_api_verifies,
    recompute,
    signer,
    spy_transport,
)

#: Two organizations in canonical form.
ORG_A = "8c7e2b41-5d93-4a06-bf12-3e9d70a5c684"
ORG_B = "1a4f6d20-9e3b-47c8-85af-b62d0c17e995"

#: Canonical field 9 is ``fields[8]``.
_FIELD_9 = 8


def _sign_with(organization: str | None):
    transport, recorder, _spy = spy_transport(signer=signer())
    headers = {"Perceivo-Organization": organization} if organization is not None else None
    transport.request("GET", "/v1/orchestrations", headers=headers)
    return recorder.last


def test_a_sent_organization_header_is_the_signed_field_9():
    request = _sign_with(ORG_A)
    # The header went out.
    assert request.headers["Perceivo-Organization"] == ORG_A
    assert_api_verifies(request)


def test_the_signed_string_carries_the_organization_at_position_nine():
    request = _sign_with(ORG_A)
    fields = recompute(request).split("\n")
    assert len(fields) == 11
    # Compared against the literal, not a re-read of the header.
    assert fields[_FIELD_9] == ORG_A
    # Field 10 is the timestamp and field 11 the nonce.
    assert fields[9] == request.headers["X-Perceivo-Timestamp"]
    assert fields[10] == request.headers["X-Perceivo-Nonce"]
    # The signature is over this string.
    assert_api_verifies(request)


def test_two_organizations_produce_two_signatures():
    """Two organizations give two signatures."""
    a, b = _sign_with(ORG_A), _sign_with(ORG_B)
    assert a.headers[HEADER_SIGNATURE] != b.headers[HEADER_SIGNATURE]
    assert_api_verifies(a)
    assert_api_verifies(b)


def test_absent_header_signs_the_empty_field_and_differs_from_a_present_one():
    absent = _sign_with(None)
    assert "Perceivo-Organization" not in absent.headers
    assert recompute(absent).split("\n")[_FIELD_9] == ""
    assert absent.headers[HEADER_SIGNATURE] != _sign_with(ORG_A).headers[HEADER_SIGNATURE]


def test_the_organization_is_not_re_emitted_as_an_x_perceivo_header():
    request = _sign_with(ORG_A)
    emitted = [v for k, v in request.headers.items() if k.lower().startswith("x-perceivo-")]
    assert ORG_A not in emitted


def test_an_unsignable_organization_is_refused_rather_than_normalised():
    """Uppercase is a different byte string, so it is refused rather than normalised."""
    for bad in (ORG_A.upper(), "{" + ORG_A + "}", ORG_A.replace("-", ""), "acme-corp"):
        with pytest.raises(SigningError):
            _sign_with(bad)


def test_a_repeated_organization_header_is_refused_not_joined():
    """A repeated header is read with ``get_list`` and refused, not joined."""
    transport, _recorder, _spy = spy_transport(signer=signer())
    repeated = httpx.Headers([("Perceivo-Organization", ORG_A), ("Perceivo-Organization", ORG_B)])
    with pytest.raises(SigningError):
        transport.request("GET", "/v1/orchestrations", headers=repeated)


def test_the_secret_never_reaches_the_wire():
    request = _sign_with(ORG_A)
    assert SECRET not in "".join(f"{k}{v}" for k, v in request.headers.items())
