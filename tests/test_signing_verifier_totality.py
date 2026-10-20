"""Both exported verifiers are total over attacker-supplied input.

``verify_signature`` and ``verify_signed_request`` are exported, documented as total,
and run as the release-gate
verifier in ``.github/workflows/release.yml``. A server written against them inherits
whatever they do, so a raise here would be a 500 on the authentication path of every
server built to this package, reachable by anyone who can send a request.

Two mechanisms can raise:

1. ``hmac.compare_digest`` raises ``TypeError: comparing strings with non-ASCII
   characters is not supported``. ``verify_signed_request`` compares ``fields[0..2]``
   before it delegates to ``verify_signature``, so a guard inside
   ``verify_signature`` alone does not protect those comparisons. Fields 1-3 are
   built by the server from the request it received.
2. ``str.encode("utf-8")`` raises ``UnicodeEncodeError: ... surrogates not
   allowed`` on a lone surrogate, and ``json.loads('"\\ud800"')`` produces one from
   any request body.

**The refusal must be indistinguishable from every other refusal.** The table's own
note says it about the negative vectors: a distinct reason per check is an oracle.
So these tests assert ``is False`` (the ordinary refusal) and never merely "did not
raise". A guard that raised a new ``SigningError`` would satisfy "no TypeError" and
still tell an attacker which of the four checks they failed.
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

#: A lone high surrogate. It is an ordinary ``str`` that UTF-8 refuses to encode,
#: and ``json.loads(r'"\ud800"')`` returns exactly this — so it arrives from a
#: request body, not from a test fixture's imagination.
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

    The default signature is computed lazily. Writing it as
    ``overrides.pop("signature", compute_signature(string, SECRET))`` evaluates
    the default eagerly, so the helper itself would raise on exactly the inputs
    these tests exist to prove do not raise.
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
    """Return the primary canonical string with one field replaced verbatim.

    Built by splitting a REAL canonical string rather than by joining literals, so
    the ten-field shape and every other field stay exactly what the signer emits
    and the only variable is the one under test.
    """
    fields = canonical().split("\n")
    fields[index] = value
    return "\n".join(fields)


# ---------------------------------------------------------------------------
# Guard the guard — if these fail, every assertion below is vacuous
# ---------------------------------------------------------------------------


def test_the_positive_control_verifies():
    """A well-formed request must still verify through BOTH verifiers.

    Without this, a verifier that returned ``False`` unconditionally would pass
    every other test in this file. That is the exact vacuous-gate shape this
    programme has hit repeatedly.
    """
    string = canonical()
    signature = compute_signature(string, SECRET)
    assert verify_signature(signature, string, SECRET) is True
    assert bound(canonical_request=string) is True


def test_the_hostile_inputs_are_genuinely_hostile():
    """The fixtures must actually be the things that raise.

    A test that fed ASCII into a "non-ASCII" case would pass against no fix at
    all, so the raising property is asserted directly against the stdlib rather
    than assumed.
    """
    import hmac as _hmac

    with pytest.raises(TypeError):
        _hmac.compare_digest("café", "cafe")
    with pytest.raises(UnicodeEncodeError):
        LONE_SURROGATE.encode("utf-8")


# ---------------------------------------------------------------------------
# Mechanism 1 — non-ASCII in the three BOUND fields, which reach compare_digest
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
    """``is False`` — the ORDINARY refusal, not an exception and not a new one."""
    assert bound(canonical_request=with_field(index, value)) is False


@pytest.mark.parametrize(("index", "value"), NON_ASCII_FIELDS)
def test_the_bare_mac_check_also_survives_non_ascii_fields(index: int, value: str):
    """The same strings through the OTHER exported verifier.

    ``verify_signature`` does not compare fields, so it must *accept* these: the
    mac over them is correct. What is being pinned is that it returns a bool
    rather than raising — and that it does not quietly become a refuser, which
    would make the bound verifier's ``False`` above prove nothing about binding.
    """
    string = with_field(index, value)
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True


# ---------------------------------------------------------------------------
# Mechanism 2 — a lone surrogate anywhere, which reaches str.encode("utf-8")
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
    """A signature cannot be computed over this string at all, so there is no
    "correct" answer to compare against — the only conforming outcome is the
    ordinary refusal. Both exported verifiers, because both encode.
    """
    string = with_field(index, value)
    assert verify_signature("v1=" + "0" * 64, string, SECRET) is False
    assert bound(canonical_request=string, signature="v1=" + "0" * 64) is False


def test_a_surrogate_pair_that_is_encodable_is_not_swallowed():
    """The guard must refuse only what UTF-8 actually refuses.

    An emoji is two surrogates in UTF-16 and one perfectly encodable character in
    Python, so it must reach the mac check normally. A guard implemented as
    "reject anything outside ASCII" would fail here — and would also make the
    verifier stricter than the signer, which is its own defect.
    """
    string = with_field(7, "application/json; x=🔑")
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True


# ---------------------------------------------------------------------------
# Totality over the argument TYPES, on both verifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [None, 12345, b"bytes-are-not-str", [], {"a": 1}])
def test_neither_verifier_raises_on_a_non_str_canonical_request(value):
    """A ``SigningError`` is an exception on the authentication path, and it is a
    *different* exception from the refusal —
    which is the oracle shape as well as the 500 shape."""
    assert verify_signature("v1=" + "0" * 64, value, SECRET) is False
    assert bound(canonical_request=value, signature="v1=" + "0" * 64) is False


def test_every_refusal_is_the_same_outcome():
    """One outcome for every reason, or the verifier is an oracle.

    Field 2 is server-assigned configuration, so a verifier that distinguished
    "unknown audience" from "bad signature" would tell an attacker which half of
    a guess was right — and would leak the deployment's own audience by the shape
    of the answer. Collecting the outcomes and asserting the set has exactly one
    member is what makes that structural instead of aspirational.
    """
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
# The reference verifier must say that it is incomplete
# ---------------------------------------------------------------------------


def test_the_reference_verifier_warns_that_it_is_not_a_complete_verifier():
    """``verify_signed_request`` omits replay protection, and must say so prominently.

    It binds fields 1-3 and checks the MAC. It does not check field 10 (timestamp
    freshness), field 11 (nonce single use) or field 9 against the organization the
    server received, and it structurally cannot: this package has no trusted clock, no shared nonce store and no
    request headers. A server copying it verbatim therefore *gains*
    domain/audience/key-id binding and *loses* replay protection and tenant
    binding: a captured request replays forever, at whatever organization the
    attacker names.

    The mitigation is documentation, so the documentation is a tested artifact.
    This asserts the warning is present, imperative, names all three missing
    checks, and sits near the top of the docstring where someone copying it sees
    it, not in a footnote.

    The count and the field numbers are asserted, not just the words. Field n is
    ``fields[n - 1]``, so a checklist that named the wrong field numbers would send
    an implementer to ``fields[8]`` (the organization) for freshness, and ``int()``
    would raise on the authentication path.
    """
    doc = verify_signed_request.__doc__
    assert doc is not None
    # 2600 is the top block: the "reference for that verifier" section
    # (the fields 1-3 bindings) begins past 3000, so this window is the warning
    # and nothing else. It is not "most of the docstring".
    head = doc[:2600]
    assert "not a complete server verifier" in head.lower()
    assert "three checks" in head.lower()
    assert "timestamp" in head.lower()
    assert "freshness" in head.lower()
    assert "nonce" in head.lower()
    assert "single-use" in head.lower()
    assert "replay" in head.lower()
    # The third check, and its ordering. Field 9 is client-asserted on both sides
    # of the comparison, so a prelude that refused on it would answer before the
    # mac had proven the string came from the key holder at all.
    assert "organization" in head.lower()
    assert "compare_digest" in head
    assert "field 10" in head
    assert "field 11" in head
    assert "field 9" in head
    # The numbering must be r3. `|now - field 9|` is the revision-2 spelling of
    # the freshness bound and reading it sends the implementer to the uuid.
    assert "field 9|" not in head
    # Arity is NOT the fix: the SDK reference stays at five arguments and the
    # server owns all three checks. If someone "fixes" this by adding a clock, a
    # nonce store or a request object here, this assertion is where the
    # conversation happens.
    assert "server" in head.lower()


def test_the_bare_mac_check_warns_that_it_binds_nothing():
    """``verify_signature`` is the easier one to copy by mistake, being simpler."""
    doc = verify_signature.__doc__
    assert doc is not None
    assert "MAC check and nothing else" in doc
    assert "replay" in doc.lower()
