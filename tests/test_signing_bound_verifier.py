"""``verify_signed_request`` binds fields 1-3 to values the verifier holds.

Every test signs correctly and still expects a refusal. Timestamp freshness, nonce
reuse and field 9 are server-side checks outside this verifier.
"""

from __future__ import annotations

from perceivo_client.signing import (
    compute_signature,
    verify_signature,
    verify_signed_request,
)
from tests.test_signing_keyed import AUDIENCE, KEY_ID, OTHER_KEY_ID, SECRET, canonical


# ---------------------------------------------------------------------------
# verify_signed_request: bound fields
# ---------------------------------------------------------------------------
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
    """A six-field canonical string signed with the right secret is refused."""
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
    """Malformed input answers 401 rather than raising."""
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
    # A malformed audience or key id on the verifier side still does not raise.
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
