"""Field 9 exercised end to end through ``Transport``, with a real header.

Warning: **Why this module exists separately from ``test_transport_signing.py``.** That
module's ``recompute`` helper reads the organization back with
``request.headers.get_list("perceivo-organization") or None`` — the same
expression ``_transport`` uses to build it. Both sides therefore agree by
construction, and no test in that module (or anywhere else in this tree) ever
put a ``Perceivo-Organization`` header on a request. Every one of its field-9
assertions was true over ``None``: green, and blind.

The failure that leaves open is total and undiagnosable. A misspelled header
name in ``_transport``, or a regression that reads the ``headers`` *argument*
instead of the built request, signs field 9 as the empty string while the header
goes out on the wire. The revision-3 edge then re-derives field 9 from the signed
string, finds ``""`` against a real organization, and denies **after** a
perfectly valid mac — a coarse ``invalid_signature`` with no reason attached, for
every organization-scoped signed request, with every SDK test still passing.

So the assertions here compare the signed field against a **literal**, never
against a re-evaluation of the expression under test.
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

#: Two organizations, both in §4A.3's canonical form. Literals, on purpose.
ORG_A = "8c7e2b41-5d93-4a06-bf12-3e9d70a5c684"
ORG_B = "1a4f6d20-9e3b-47c8-85af-b62d0c17e995"

#: Canonical field 9 → ``fields[8]`` (§2.2: the conversion is ``n - 1``).
_FIELD_9 = 8


def _sign_with(organization: str | None):
    transport, recorder, _spy = spy_transport(signer=signer())
    headers = {"Perceivo-Organization": organization} if organization is not None else None
    transport.request("GET", "/v1/orchestrations", headers=headers)
    return recorder.last


def test_a_sent_organization_header_is_the_signed_field_9():
    request = _sign_with(ORG_A)
    # The header really did go out — otherwise the assertion below would be
    # comparing two absences and passing for the wrong reason.
    assert request.headers["Perceivo-Organization"] == ORG_A
    assert_api_verifies(request)


def test_the_signed_string_carries_the_organization_at_position_nine():
    request = _sign_with(ORG_A)
    fields = recompute(request).split("\n")
    assert len(fields) == 11
    # Compared against the LITERAL, not against a re-read of the header.
    assert fields[_FIELD_9] == ORG_A
    # And the neighbours did not shift: field 10 is the timestamp, field 11 the
    # nonce. A field-9 insertion at the wrong offset passes the equality above
    # and fails here.
    assert fields[9] == request.headers["X-Perceivo-Timestamp"]
    assert fields[10] == request.headers["X-Perceivo-Nonce"]
    # ...and the signature really is over THIS string, so a transport that read
    # some other header fails here rather than agreeing with `recompute`.
    assert_api_verifies(request)


def test_two_organizations_produce_two_signatures():
    """The pair that makes field 9 undroppable.

    Without it, a refactor that stopped signing the organization entirely would
    leave every other assertion in this tree green: they all sign the empty
    organization, and empty compares equal to empty.
    """
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
    """Warning: Uppercase is a *different byte string*, not a spelling to fix.

    Normalising it here would sign one value and send another, which the edge
    denies on a correct mac. Refusing is the only outcome that leaves the caller
    able to tell what happened.
    """
    for bad in (ORG_A.upper(), "{" + ORG_A + "}", ORG_A.replace("-", ""), "acme-corp"):
        with pytest.raises(SigningError):
            _sign_with(bad)


def test_a_repeated_organization_header_is_refused_not_joined():
    """httpx joins repeated headers with ``", "`` on ``get``; ``_transport`` must
    use ``get_list``. A join would synthesise a single value the request never
    carried, and the verifier and the tenancy decision could resolve the
    duplicate differently."""
    transport, _recorder, _spy = spy_transport(signer=signer())
    repeated = httpx.Headers([("Perceivo-Organization", ORG_A), ("Perceivo-Organization", ORG_B)])
    with pytest.raises(SigningError):
        transport.request("GET", "/v1/orchestrations", headers=repeated)


def test_the_secret_never_reaches_the_wire():
    request = _sign_with(ORG_A)
    assert SECRET not in "".join(f"{k}{v}" for k, v in request.headers.items())
