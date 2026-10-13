"""The organization field (canonical field 9), and what each of its rows proves.

Two hazards shape this module, and a reader of any one test cannot see either.

1. **A negative row can be refused for the wrong reason.** If ``n03``, ``n04`` and
   ``n05`` carried ten fields instead of eleven, all three would still be refused,
   on the arity check, which fires before any field is compared. They would pass
   while the domain-separator, audience and key-id bindings they exist to exercise
   went untested. So the shape is asserted per row: ``field_count``, ``refused_by``
   and ``refused_before_mac``.

2. **The field-8 unsignable rows must keep field number 8.** They carry
   ``"field_number": 8`` and publish neither a canonical request nor a signature, so
   they stay true only because field 9 comes after ``content_type``, which therefore
   keeps wire position 8.
"""

from __future__ import annotations

import base64
import hmac

import pytest

from perceivo_client.signing import (
    CANONICAL_FIELD_COUNT,
    SigningError,
    canonical_organization,
    verify_signature,
    verify_signed_request,
)
from tests._signing_vectors_support import (
    PRIMARY_CANONICAL,
    PRIMARY_ID,
    PRIMARY_SIGNATURE,
    PRIMARY_SIX_FIELD_CANONICAL,
    PRIMARY_TEN_FIELD_CANONICAL,
    find,
    load_table,
)


@pytest.fixture(scope="module")
def table() -> dict:
    return load_table()


def test_an_absent_organization_signs_as_the_empty_string(table):
    """Field 9 absent is the empty string, not ``None`` and not a placeholder.

    The arity is still eleven. Empty and absent are the same value and different
    arities; only the field count tells them apart, which is what makes
    ``n06-ten-field-downgrade`` a different string from this one rather than the
    same one spelled differently.
    """
    for vector in table["vectors"]:
        if vector["organization"] is not None:
            continue
        assert vector["canonical_organization"] == "", vector["id"]
        assert vector["canonical_request"].split("\n")[8] == "", vector["id"]
        assert len(vector["canonical_request"].split("\n")) == 11, vector["id"]


def test_two_requests_differing_only_in_the_organization_sign_differently(table):
    """The organization changes the signature.

    Without this pair, field 9 could be dropped in a later refactor and every other
    positive vector would still pass, because they all sign the empty organization. The
    third comparison is against ``v01``, the same request with no header at all: one
    request, three tenancies, three signatures.
    """
    a = find(table, "v35-organization-pair-a")
    b = find(table, "v36-organization-pair-b")
    absent = find(table, PRIMARY_ID)

    assert a["method"] == b["method"]
    assert a["target"] == b["target"]
    assert a["body_base64"] == b["body_base64"]
    assert a["content_type"] == b["content_type"]
    assert a["organization"] != b["organization"]

    fields_a = a["canonical_request"].split("\n")
    fields_b = b["canonical_request"].split("\n")
    differing = [i for i, (x, y) in enumerate(zip(fields_a, fields_b, strict=True)) if x != y]
    assert differing == [8], differing
    assert len({a["signature"], b["signature"], absent["signature"]}) == 3


def test_a_present_organization_is_carried_verbatim_and_lowercase(table):
    """Field 9 is the header verbatim: no normalisation, and only one spelling."""
    for vector_id in (
        "v34-organization-present",
        "v35-organization-pair-a",
        "v36-organization-pair-b",
    ):
        vector = find(table, vector_id)
        organization = vector["organization"]
        assert organization is not None, vector_id
        assert organization == organization.lower(), vector_id
        assert vector["canonical_organization"] == organization, vector_id
        assert vector["canonical_request"].split("\n")[8] == organization, vector_id


def test_the_table_ships_the_negative_vectors(table):
    assert {v["id"] for v in table["negative_vectors"]} == {
        "n01-six-field-downgrade",
        "n02-nine-field-downgrade",
        "n03-wrong-domain-separator",
        "n04-audience-mismatch",
        "n05-key-id-mismatch",
        "n06-ten-field-downgrade",
        "n07-organization-metadata-unbound",
    }


# `test_every_negative_vector_is_refused_by_the_bound_verifier` below would still
# pass if `n03`, `n04` and `n05` carried ten fields: all three would be refused on
# the arity check, which fires before any field is compared, while the
# domain-separator, audience and key-id bindings they exist to exercise went
# untested.
#
# So the shape is asserted, per row, alongside the verdict: what refuses each row,
# and whether it is refused before or after the MAC.
NEGATIVE_SHAPES = {
    # id: (field_count, refused_by, refused_before_mac)
    "n01-six-field-downgrade": (6, "arity", True),
    "n02-nine-field-downgrade": (9, "arity", True),
    "n03-wrong-domain-separator": (11, "prelude_binding", True),
    "n04-audience-mismatch": (11, "prelude_binding", True),
    "n05-key-id-mismatch": (11, "prelude_binding", True),
    "n06-ten-field-downgrade": (10, "arity", True),
    "n07-organization-metadata-unbound": (11, "metadata_binding", False),
}


def test_every_negative_vector_declares_what_actually_refuses_it(table):
    for vector in table["negative_vectors"]:
        field_count, refused_by, before_mac = NEGATIVE_SHAPES[vector["id"]]
        actual = len(vector["canonical_request"].split("\n"))
        assert actual == field_count == vector["field_count"], vector["id"]
        assert vector["refused_by"] == refused_by, vector["id"]
        assert vector["refused_before_mac"] is before_mac, vector["id"]
        # The two halves must agree: a row is refused on arity IF AND ONLY IF its
        # field count is not eleven.
        assert (vector["refused_by"] == "arity") == (actual != 11), vector["id"]


def test_the_three_prelude_vectors_carry_the_full_eleven_fields(table):
    """The control that keeps fields 1-3 tested rather than shadowed by arity."""
    for vector_id in (
        "n03-wrong-domain-separator",
        "n04-audience-mismatch",
        "n05-key-id-mismatch",
    ):
        vector = next(v for v in table["negative_vectors"] if v["id"] == vector_id)
        fields = vector["canonical_request"].split("\n")
        assert len(fields) == CANONICAL_FIELD_COUNT, vector_id
        # ...and exactly ONE of the three bound fields is wrong in each, so the
        # refusal is attributable to that field and to nothing else.
        primary = find(table, PRIMARY_ID)["canonical_request"].split("\n")
        differing = [i for i, (x, y) in enumerate(zip(fields, primary, strict=True)) if x != y]
        assert len(differing) == 1, (vector_id, differing)
        assert differing[0] < 3, (vector_id, differing)


def test_the_ten_field_downgrade_omits_the_organization_field(table):
    """The ten-field downgrade: what a signer that omits field 9 emits.

    It is deliberately not the same string as v01's: v01 signs field 9 as the empty
    string and this omits the field. Same value, different arity.
    """
    vector = next(v for v in table["negative_vectors"] if v["id"] == "n06-ten-field-downgrade")
    assert hmac.compare_digest(vector["canonical_request"], PRIMARY_TEN_FIELD_CANONICAL)
    assert PRIMARY_TEN_FIELD_CANONICAL.count("\n") == 9
    assert vector["canonical_request"] != PRIMARY_CANONICAL
    assert vector["signature"] != PRIMARY_SIGNATURE


def test_the_metadata_unbound_vector_survives_every_check_before_the_mac(table):
    """The row that shows field 9 is bound rather than merely signed.

    Its prelude is correct, its arity is correct and its MAC is correct, so a
    verifier that signs field 9 without re-deriving it accepts this string. Only a
    verifier that compares field 9 against the organization the server received
    (after ``compare_digest``, never before) refuses it.

    The SDK's reference verifier deliberately does not implement that binding
    (it has no request to read a header from), so this row is asserted here on its
    published shape and is exercised end to end by the server implementations.
    """
    vector = next(
        v for v in table["negative_vectors"] if v["id"] == "n07-organization-metadata-unbound"
    )
    fields = vector["canonical_request"].split("\n")
    primary = find(table, PRIMARY_ID)["canonical_request"].split("\n")
    assert len(fields) == CANONICAL_FIELD_COUNT
    assert fields[:3] == primary[:3], "the prelude must be correct or it refuses early"
    assert fields[8] != vector["presented_organization"]
    assert fields[8] != ""
    assert vector["presented_organization"] != ""
    # The mac really is correct — otherwise the row would prove nothing.
    assert verify_signature(vector["signature"], vector["canonical_request"], table["secret_utf8"])


def test_the_field_eight_unsignable_rows_keep_field_number_eight(table):
    """Field 9 comes after ``content_type``, which keeps wire position 8.

    ``u01``-``u05`` carry ``"field_number": 8`` and publish neither a canonical
    request nor a signature. Their labels are true only because ``content_type`` is
    field 8, so these rows pin the position of field 9.
    """
    field_eight = [v for v in table["unsignable_vectors"] if v["field_number"] == 8]
    assert [v["id"] for v in field_eight] == [
        "u01-content-type-non-ascii-text",
        "u02-content-type-latin1-high-byte",
        "u03-content-type-newline",
        "u04-content-type-tab",
        "u05-content-type-del-control",
    ]
    for vector in field_eight:
        assert vector["field"] == "content_type", vector["id"]
        assert vector["reason"] == "content_type_charset", vector["id"]
        assert "content_type_base64" in vector, vector["id"]


def test_the_field_nine_unsignable_rows_are_rejected_never_normalised(table):
    """Field 9 refuses the spellings ``key_id`` normalises.

    ``v28`` supplies an uppercase key id and must produce ``v01``'s signature, because
    ``canonical_key_id`` folds it. ``u06`` supplies an uppercase organization and
    must raise. An implementation that reuses its key-id normaliser for field 9
    passes v28 and fails u06, u07 and u08, which is exactly the discrimination
    these rows exist to make.
    """
    field_nine = [v for v in table["unsignable_vectors"] if v["field_number"] == 9]
    assert len(field_nine) == 6
    for vector in field_nine:
        assert vector["field"] == "organization", vector["id"]
        assert vector["reason"] in {
            "organization_charset",
            "organization_duplicate_header",
        }, vector["id"]
        values = [
            base64.b64decode(value).decode("utf-8")
            for value in vector["organization_values_base64"]
        ]
        with pytest.raises(SigningError):
            canonical_organization(values if len(values) > 1 else values[0])

    # And the premise: v28 proves the opposite rule holds for field 3, so the two
    # are genuinely different rules rather than one rule inconsistently applied.
    assert find(table, "v28-key-id-mixed-case-normalised")["signature"] == PRIMARY_SIGNATURE


def test_every_vector_canonical_request_has_eleven_fields(table):
    assert CANONICAL_FIELD_COUNT == 11
    for vector in table["vectors"]:
        assert vector["canonical_request"].count("\n") == CANONICAL_FIELD_COUNT - 1, vector["id"]
        assert not vector["canonical_request"].endswith("\n"), vector["id"]


def test_the_table_declares_the_eleven_field_revision(table):
    assert table["field_count"] == CANONICAL_FIELD_COUNT
    assert table["wire_format_revision"] == 3
    assert table["canonical_form"].startswith("perceivo-hmac-v1\\n{audience}\\n{key_id}\\n")
    # The tail pins the position, not merely the presence, of field 9: it goes
    # after `content_type` and before `timestamp`, and `nonce` stays terminal.
    # Asserting only that the form mentions `{organization}` would pass on a form
    # that appended it, which is the smaller diff and the wrong one.
    assert table["canonical_form"].endswith(
        "{content_type}\\n{organization}\\n{timestamp}\\n{nonce}"
    )


def test_every_negative_vector_is_refused_by_the_bound_verifier(table):
    """Read this with ``test_every_negative_vector_declares_what_actually_refuses_it``.

    On its own it is satisfied by a row refused for the wrong reason, and it still
    passes if every prelude row is reduced to an arity failure. The companion test
    above makes the verdict attributable.

    ``n07`` is excluded: the reference verifier binds fields 1-3 and checks the MAC,
    and it has no request from which to re-derive the received organization. It
    therefore accepts n07, correctly. The row's point is that a MAC check plus a
    prelude check is not enough, and asserting a refusal here would claim a control
    this function does not implement.
    """
    secret = table["secret_utf8"]
    for vector in table["negative_vectors"]:
        assert vector["must_verify"] is False, vector["id"]
        if vector["refused_by"] == "metadata_binding":
            continue
        assert (
            verify_signed_request(
                signature=vector["signature"],
                canonical_request=vector["canonical_request"],
                secret=secret,
                audience=vector["verifier_audience"],
                key_id=vector["verifier_key_id"],
            )
            is False
        ), vector["id"]


def test_the_reference_verifier_accepts_the_metadata_unbound_vector(table):
    """The exclusion above, asserted rather than assumed.

    A skipped row and an accepted row look identical from a passing suite. This pins
    which one it is: the reference verifier accepts n07, which is exactly the gap a
    server must close in ``bind_metadata`` after the MAC. If this ever starts
    refusing, either the verifier grew the binding (and the exclusion above must
    go) or the row stopped being what it claims.
    """
    vector = next(
        v for v in table["negative_vectors"] if v["id"] == "n07-organization-metadata-unbound"
    )
    assert (
        verify_signed_request(
            signature=vector["signature"],
            canonical_request=vector["canonical_request"],
            secret=table["secret_utf8"],
            audience=vector["verifier_audience"],
            key_id=vector["verifier_key_id"],
        )
        is True
    )


def test_the_six_field_downgrade_is_the_pinned_literal(table):
    """Pinned independently of the generator's slicing of the eleven-field string.

    The timestamp and the nonce are at indices 9 and 10 of the eleven-field string.
    A generator that sliced indices 8 and 9 would emit a six-field string containing
    the content type and the organization where the timestamp and nonce belong:
    still six fields, still refused on arity, and still passing.
    """
    vector = next(v for v in table["negative_vectors"] if v["id"] == "n01-six-field-downgrade")
    assert hmac.compare_digest(vector["canonical_request"], PRIMARY_SIX_FIELD_CANONICAL)
    assert PRIMARY_SIX_FIELD_CANONICAL.count("\n") == 5
    # And it is genuinely a different, prefix-free string from the one we sign.
    assert vector["canonical_request"] != PRIMARY_CANONICAL
    assert vector["signature"] != PRIMARY_SIGNATURE
