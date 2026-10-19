"""The organization field (canonical field 9) and what each of its rows proves."""

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
    """Field 9 absent is the empty string, and the arity is still eleven."""
    for vector in table["vectors"]:
        if vector["organization"] is not None:
            continue
        assert vector["canonical_organization"] == "", vector["id"]
        assert vector["canonical_request"].split("\n")[8] == "", vector["id"]
        assert len(vector["canonical_request"].split("\n")) == 11, vector["id"]


def test_two_requests_differing_only_in_the_organization_sign_differently(table):
    """The organization changes the signature: one request, three tenancies, three signatures."""
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


# Each negative row's shape is asserted with its verdict, so a row refused on arity
# cannot stand in for a field binding.
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
        # A row is refused on arity if and only if its field count is not eleven.
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
        # ...and one of the three bound fields is wrong in each.
        primary = find(table, PRIMARY_ID)["canonical_request"].split("\n")
        differing = [i for i, (x, y) in enumerate(zip(fields, primary, strict=True)) if x != y]
        assert len(differing) == 1, (vector_id, differing)
        assert differing[0] < 3, (vector_id, differing)


def test_the_ten_field_downgrade_omits_the_organization_field(table):
    """The ten-field downgrade omits field 9, unlike v01 which signs it empty."""
    vector = next(v for v in table["negative_vectors"] if v["id"] == "n06-ten-field-downgrade")
    assert hmac.compare_digest(vector["canonical_request"], PRIMARY_TEN_FIELD_CANONICAL)
    assert PRIMARY_TEN_FIELD_CANONICAL.count("\n") == 9
    assert vector["canonical_request"] != PRIMARY_CANONICAL
    assert vector["signature"] != PRIMARY_SIGNATURE


def test_the_metadata_unbound_vector_survives_every_check_before_the_mac(table):
    """n07 shows field 9 is bound: its prelude, arity and MAC are correct.

    The reference verifier does not bind field 9, so the row is asserted on its
    published shape.
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
    # The MAC is correct.
    assert verify_signature(vector["signature"], vector["canonical_request"], table["secret_utf8"])


def test_the_field_eight_unsignable_rows_keep_field_number_eight(table):
    """Field 9 comes after ``content_type``, which keeps wire position 8."""
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
    """Field 9 refuses the spellings ``key_id`` normalises."""
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

    # v28 shows the opposite rule holds for field 3.
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
    # The tail pins the position of field 9: after `content_type`, before `timestamp`,
    # with `nonce` terminal.
    assert table["canonical_form"].endswith(
        "{content_type}\\n{organization}\\n{timestamp}\\n{nonce}"
    )


def test_every_negative_vector_is_refused_by_the_bound_verifier(table):
    """Every negative vector except n07 is refused by the bound verifier.

    The reference verifier cannot re-derive the received organization, so it
    accepts n07.
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
    """The reference verifier accepts n07; a server binds field 9 after the MAC."""
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
    """The six-field downgrade matches the pinned literal."""
    vector = next(v for v in table["negative_vectors"] if v["id"] == "n01-six-field-downgrade")
    assert hmac.compare_digest(vector["canonical_request"], PRIMARY_SIX_FIELD_CANONICAL)
    assert PRIMARY_SIX_FIELD_CANONICAL.count("\n") == 5
    # It differs from the primary canonical string and signature.
    assert vector["canonical_request"] != PRIMARY_CANONICAL
    assert vector["signature"] != PRIMARY_SIGNATURE
