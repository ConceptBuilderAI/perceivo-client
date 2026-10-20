"""``verify_signed_request``: the fields must be bound, not merely present.

``test_signing_keyed.py`` covers the keyed surface (the signature, the credentials
and secret hygiene). This module covers the reference verifier, which is the half a
MAC check cannot express.

A field that appears in the canonical string but is never compared against a value
the verifier holds itself adds nothing: an attacker writes whatever makes the MAC
verify. Every test here signs correctly and still expects a refusal.

What the reference verifier deliberately does not do is as much a part of the
contract as what it does. It binds fields 1-3 and checks the MAC. It does not check
timestamp freshness, nonce single use, or canonical field 9 against the organization
the server received, because it has no request to read a header from and no store to
record a nonce in. Those checks belong to a real server, and the published vector
``n07-organization-metadata-unbound`` is the row that fails a server which signs
field 9 without re-deriving it.
"""

from __future__ import annotations

from perceivo_client.signing import (
    compute_signature,
    verify_signature,
    verify_signed_request,
)
from tests.test_signing_keyed import AUDIENCE, KEY_ID, OTHER_KEY_ID, SECRET, canonical


# ---------------------------------------------------------------------------
# verify_signed_request — the fields must be BOUND, not merely present
# ---------------------------------------------------------------------------
# A field that appears in the canonical string but is never compared against a
# value the verifier holds itself buys nothing: the attacker writes whatever makes
# the mac verify. Every test below signs CORRECTLY and still expects a refusal.
def test_bound_verifier_accepts_a_correctly_bound_request():
    string = canonical()
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience=AUDIENCE,
            key_id=KEY_ID,
        )
        is True
    )


def test_bound_verifier_refuses_a_correctly_signed_wrong_audience():
    string = canonical(audience="perceivo-api-prod")
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience=AUDIENCE,
            key_id=KEY_ID,
        )
        is False
    )


def test_bound_verifier_refuses_a_correctly_signed_wrong_key_id():
    string = canonical(key_id=OTHER_KEY_ID)
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience=AUDIENCE,
            key_id=KEY_ID,
        )
        is False
    )


def test_bound_verifier_refuses_a_correctly_signed_wrong_domain_separator():
    string = "perceivo-hmac-v2\n" + canonical().split("\n", 1)[1]
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience=AUDIENCE,
            key_id=KEY_ID,
        )
        is False
    )


def test_bound_verifier_refuses_the_six_field_downgrade():
    """What an attacker tries first once the new fields exist."""
    fields = canonical().split("\n")
    six = "\n".join([fields[3], fields[4], fields[5], fields[6], fields[9], fields[10]])
    assert verify_signature(compute_signature(six, SECRET), six, SECRET) is True
    assert (
        verify_signed_request(
            signature=compute_signature(six, SECRET),
            canonical_request=six,
            secret=SECRET,
            audience=AUDIENCE,
            key_id=KEY_ID,
        )
        is False
    )


def test_bound_verifier_normalises_the_key_id_it_is_given():
    string = canonical()
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience=AUDIENCE,
            key_id=KEY_ID.upper(),
        )
        is True
    )


def test_bound_verifier_is_total_on_garbage():
    """It answers 401, never 500. A crash here is a denial of service."""
    for bad in ("", "not-a-canonical-request", "a\nb\nc"):
        assert (
            verify_signed_request(
                signature="v1=" + "0" * 64,
                canonical_request=bad,
                secret=SECRET,
                audience=AUDIENCE,
                key_id=KEY_ID,
            )
            is False
        )
    # An unparsable audience or key id is a configuration error on OUR side and
    # must still not raise into the request path.
    string = canonical()
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience="not a legal audience",
            key_id=KEY_ID,
        )
        is False
    )
    assert (
        verify_signed_request(
            signature=compute_signature(string, SECRET),
            canonical_request=string,
            secret=SECRET,
            audience=AUDIENCE,
            key_id="pk_live_not_a_uuid",
        )
        is False
    )
