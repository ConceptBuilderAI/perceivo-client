"""Both exported verifiers are total over attacker-supplied input.

A refusal is the ordinary ``False`` rather than an exception, for non-ASCII bound
fields, lone surrogates and wrong argument types.
"""

from __future__ import annotations

import pytest

from perceivo_client.signing import (
    CANONICAL_DOMAIN,
    build_canonical_request,
    compute_signature,
    verify_signature,
    verify_signed_request,
)

SECRET = "unit-test-secret"
TS = 1767225600
NONCE = "sT8kQ2vX7wLpR4nB1mZ6yH0j"
AUDIENCE = "perceivo-api-local"
KEY_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"

#: A lone high surrogate: an ordinary ``str`` UTF-8 refuses to encode, which
#: ``json.loads(r'"\ud800"')`` returns from a request body.
LONE_SURROGATE = "\ud800"


def canonical(**overrides) -> str:
    kwargs = {
        "audience": AUDIENCE,
        "key_id": KEY_ID,
        "method": "GET",
        "raw_path": "/x",
        "query_string": "",
        "body": None,
        "content_type": None,
        "organization": None,
        "timestamp": TS,
        "nonce": NONCE,
    }
    kwargs.update(overrides)
    return build_canonical_request(**kwargs)


def bound(**overrides) -> bool:
    """Call the bound verifier with a correct signature over whatever it is given.

    The default signature is computed lazily so the helper itself does not raise.
    """
    string = overrides.pop("canonical_request")
    if "signature" in overrides:
        signature = overrides.pop("signature")
    else:
        signature = compute_signature(string, SECRET)
    kwargs = {
        "signature": signature,
        "canonical_request": string,
        "secret": SECRET,
        "audience": AUDIENCE,
        "key_id": KEY_ID,
    }
    kwargs.update(overrides)
    return verify_signed_request(**kwargs)


def with_field(index: int, value: str) -> str:
    """Return the primary canonical string with one field replaced verbatim."""
    fields = canonical().split("\n")
    fields[index] = value
    return "\n".join(fields)


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


def test_the_positive_control_verifies():
    """A well-formed request verifies through both verifiers."""
    string = canonical()
    signature = compute_signature(string, SECRET)
    assert verify_signature(signature, string, SECRET) is True
    assert bound(canonical_request=string) is True


def test_the_hostile_inputs_are_genuinely_hostile():
    """The fixtures raise in the stdlib as the cases assume."""
    import hmac as _hmac

    with pytest.raises(TypeError):
        _hmac.compare_digest("café", "cafe")
    with pytest.raises(UnicodeEncodeError):
        LONE_SURROGATE.encode("utf-8")


# ---------------------------------------------------------------------------
# Mechanism 1: non-ASCII in the three bound fields, which reach compare_digest
# ---------------------------------------------------------------------------

NON_ASCII_FIELDS = [
    pytest.param(0, "perceivo-hmac-vé", id="field-1-domain-separator"),
    pytest.param(1, "perceivo-api-locé", id="field-2-audience"),
    pytest.param(2, "0f8fad5b-d9cb-469f-a165-7086772895ée", id="field-3-key-id"),
    pytest.param(0, CANONICAL_DOMAIN + "🔑", id="field-1-astral-plane"),
    pytest.param(1, "ÿ" * 12, id="field-2-latin1-high"),
    pytest.param(2, KEY_ID[:-1] + "ß", id="field-3-sharp-s"),
]


@pytest.mark.parametrize(("index", "value"), NON_ASCII_FIELDS)
def test_bound_verifier_refuses_non_ascii_in_a_bound_field(index: int, value: str):
    """The result is the ordinary ``False`` refusal, not an exception."""
    assert bound(canonical_request=with_field(index, value)) is False


@pytest.mark.parametrize(("index", "value"), NON_ASCII_FIELDS)
def test_the_bare_mac_check_also_survives_non_ascii_fields(index: int, value: str):
    """``verify_signature`` accepts the same strings, since it does not compare fields."""
    string = with_field(index, value)
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True


# ---------------------------------------------------------------------------
# Mechanism 2: a lone surrogate anywhere, which reaches str.encode("utf-8")
# ---------------------------------------------------------------------------

SURROGATE_PLACEMENTS = [
    pytest.param(4, "/x" + LONE_SURROGATE, id="in-the-path-field"),
    pytest.param(5, "limit=" + LONE_SURROGATE, id="in-the-query-field"),
    pytest.param(7, "application/json; x=" + LONE_SURROGATE, id="in-the-content-type-field"),
    pytest.param(9, NONCE + LONE_SURROGATE, id="in-the-nonce-field"),
    pytest.param(1, AUDIENCE + LONE_SURROGATE, id="in-a-bound-field-too"),
]


@pytest.mark.parametrize(("index", "value"), SURROGATE_PLACEMENTS)
def test_both_verifiers_refuse_a_lone_surrogate(index: int, value: str):
    """A lone surrogate yields the ordinary refusal from both verifiers."""
    string = with_field(index, value)
    assert verify_signature("v1=" + "0" * 64, string, SECRET) is False
    assert bound(canonical_request=string, signature="v1=" + "0" * 64) is False


def test_a_surrogate_pair_that_is_encodable_is_not_swallowed():
    """An encodable non-ASCII character such as an emoji reaches the MAC check."""
    string = with_field(7, "application/json; x=🔑")
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True


# ---------------------------------------------------------------------------
# Totality over argument types, on both verifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [None, 12345, b"bytes-are-not-str", [], {"a": 1}])
def test_neither_verifier_raises_on_a_non_str_canonical_request(value):
    """A wrong argument type is refused rather than raising ``SigningError``."""
    assert verify_signature("v1=" + "0" * 64, value, SECRET) is False
    assert bound(canonical_request=value, signature="v1=" + "0" * 64) is False


def test_every_refusal_is_the_same_outcome():
    """Every refusal reason produces the same outcome."""
    outcomes = {
        bound(canonical_request=with_field(0, "perceivo-hmac-v2")),
        bound(canonical_request=with_field(1, "perceivo-api-prod")),
        bound(canonical_request=with_field(2, "3d1c1a7e-6b54-4b0e-9a2d-8c5f0e21b4aa")),
        bound(canonical_request=with_field(0, "perceivo-hmac-vé")),
        bound(canonical_request=with_field(1, "perceivo-api-locé")),
        bound(canonical_request=with_field(2, KEY_ID[:-1] + "ß")),
        bound(canonical_request=with_field(4, "/x" + LONE_SURROGATE), signature="v1=" + "0" * 64),
        bound(canonical_request="\n".join(canonical().split("\n")[:6])),
        bound(canonical_request=canonical(), signature="v1=" + "0" * 64),
        bound(canonical_request=canonical(), audience="not-this-deployment"),
        bound(canonical_request=12345, signature="v1=" + "0" * 64),
    }
    assert outcomes == {False}, f"more than one refusal outcome is an oracle: {outcomes}"


# ---------------------------------------------------------------------------
# The reference verifier documents what it omits
# ---------------------------------------------------------------------------


def test_the_reference_verifier_warns_that_it_is_not_a_complete_verifier():
    """``verify_signed_request`` warns near the top that it omits three server checks."""
    doc = verify_signed_request.__doc__
    assert doc is not None
    # The first 2600 characters hold the warning.
    head = doc[:2600]
    assert "not a complete server verifier" in head.lower()
    assert "three checks" in head.lower()
    assert "timestamp" in head.lower()
    assert "freshness" in head.lower()
    assert "nonce" in head.lower()
    assert "single-use" in head.lower()
    assert "replay" in head.lower()
    assert "organization" in head.lower()
    assert "compare_digest" in head
    assert "field 10" in head
    assert "field 11" in head
    assert "field 9" in head
    assert "field 9|" not in head
    assert "server" in head.lower()


def test_the_bare_mac_check_warns_that_it_binds_nothing():
    """``verify_signature`` warns that it is a MAC check only."""
    doc = verify_signature.__doc__
    assert doc is not None
    assert "MAC check and nothing else" in doc
    assert "replay" in doc.lower()
