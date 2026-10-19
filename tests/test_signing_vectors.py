"""Golden vectors: the cross-implementation contract for HMAC request signing.

The shipped table is reproduced end to end, and the primary vector is checked
against literals in ``_signing_vectors_support.py``.
"""

from __future__ import annotations

import base64
import hmac

import pytest

from perceivo_client.signing import (
    SigningError,
    build_canonical_request,
    canonical_content_type,
    compute_signature,
    split_target,
    verify_signature,
    verify_signed_request,
)
from tests._signing_vectors_support import (
    PRIMARY_AUDIENCE,
    PRIMARY_BODY,
    PRIMARY_CANONICAL,
    PRIMARY_CONTENT_TYPE,
    PRIMARY_ID,
    PRIMARY_KEY_ID,
    PRIMARY_METHOD,
    PRIMARY_NONCE,
    PRIMARY_ORGANIZATION,
    PRIMARY_SECRET,
    PRIMARY_SIGNATURE,
    PRIMARY_TARGET,
    PRIMARY_TIMESTAMP,
    canonical_for,
    find,
    load_table,
)


@pytest.fixture(scope="module")
def table() -> dict:
    return load_table()


# ---------------------------------------------------------------------------
# The primary vector, against hardcoded literals
# ---------------------------------------------------------------------------
def test_primary_vector_canonical_request_matches_the_pinned_literal():
    canonical = build_canonical_request(
        audience=PRIMARY_AUDIENCE,
        key_id=PRIMARY_KEY_ID,
        method=PRIMARY_METHOD,
        raw_path=PRIMARY_TARGET,
        query_string="",
        body=PRIMARY_BODY,
        content_type=PRIMARY_CONTENT_TYPE,
        organization=PRIMARY_ORGANIZATION,
        timestamp=PRIMARY_TIMESTAMP,
        nonce=PRIMARY_NONCE,
    )
    assert hmac.compare_digest(canonical, PRIMARY_CANONICAL)


def test_primary_vector_signature_matches_the_pinned_literal():
    assert hmac.compare_digest(
        compute_signature(PRIMARY_CANONICAL, PRIMARY_SECRET), PRIMARY_SIGNATURE
    )


def test_primary_vector_verifies():
    assert verify_signature(PRIMARY_SIGNATURE, PRIMARY_CANONICAL, PRIMARY_SECRET) is True


def test_published_table_agrees_with_the_pinned_literals(table):
    vector = find(table, PRIMARY_ID)
    assert hmac.compare_digest(table["secret_utf8"], PRIMARY_SECRET)
    assert hmac.compare_digest(vector["canonical_request"], PRIMARY_CANONICAL)
    assert hmac.compare_digest(vector["signature"], PRIMARY_SIGNATURE)


# ---------------------------------------------------------------------------
# Every vector in the table
# ---------------------------------------------------------------------------
def test_every_vector_canonical_request_is_reproduced(table):
    for vector in table["vectors"]:
        assert hmac.compare_digest(canonical_for(vector), vector["canonical_request"]), vector["id"]


def test_every_vector_signature_is_reproduced(table):
    secret = table["secret_utf8"]
    for vector in table["vectors"]:
        signature = compute_signature(vector["canonical_request"], secret)
        assert hmac.compare_digest(signature, vector["signature"]), vector["id"]


def test_every_vector_verifies_and_no_other_vector_does(table):
    secret = table["secret_utf8"]
    vectors = table["vectors"]
    for vector in vectors:
        assert verify_signature(vector["signature"], vector["canonical_request"], secret)
    # Cross-check every ordered pair: a signature validates another vector only
    # within a declared path equivalence class.
    for vector in vectors:
        for other in vectors:
            if other["id"] == vector["id"]:
                continue
            same_class = _class_of(other["id"]) == _class_of(vector["id"])
            validates = verify_signature(other["signature"], vector["canonical_request"], secret)
            assert validates is same_class, (vector["id"], other["id"])


# Distinct targets the API normalises to one path are one signed request. These
# are the only collisions the table may contain.
CANONICAL_PATH_EQUIVALENCE_CLASSES = [
    # `%7e`, `%7E` and a literal `~` are one path: step 1 decodes both hex cases.
    {
        "v22-unreserved-escape-lowercase-hex",
        "v23-unreserved-escape-uppercase-hex",
        "v24-literal-unreserved-character",
    },
    # `..`, `.` and the percent-encoded `%2E%2E` all reduce to the same path:
    # step 1 decodes `%2E` to `.`, then step 2 removes the dot segments.
    {
        "v25-dot-segment-removed",
        "v26-single-dot-segment-removed",
        "v27-encoded-dot-segment-decode-then-remove",
    },
]


# Key-id normalisation: v28 supplies an uppercase uuid and lands on v01's
# canonical string.
KEY_ID_NORMALISATION_CLASSES = [
    {"v01-get-empty-body-empty-query", "v28-key-id-mixed-case-normalised"},
]

EQUIVALENCE_CLASSES = CANONICAL_PATH_EQUIVALENCE_CLASSES + KEY_ID_NORMALISATION_CLASSES


def _class_of(vector_id: str) -> frozenset[str]:
    for members in EQUIVALENCE_CLASSES:
        if vector_id in members:
            return frozenset(members)
    return frozenset({vector_id})


def test_canonical_requests_collide_exactly_on_the_declared_equivalence_classes(table):
    """Every declared collision class collides, and nothing outside a class does."""
    by_canonical: dict[str, set[str]] = {}
    for vector in table["vectors"]:
        by_canonical.setdefault(vector["canonical_request"], set()).add(vector["id"])

    observed = {frozenset(ids) for ids in by_canonical.values() if len(ids) > 1}
    assert observed == {frozenset(members) for members in EQUIVALENCE_CLASSES}

    for members in CANONICAL_PATH_EQUIVALENCE_CLASSES:
        signatures = {find(table, vector_id)["signature"] for vector_id in members}
        canonical_paths = {find(table, vector_id)["canonical_path"] for vector_id in members}
        raw_paths = {find(table, vector_id)["raw_path"] for vector_id in members}
        assert len(signatures) == 1, members  # one signed request...
        assert len(canonical_paths) == 1, members
        assert len(raw_paths) == len(members), members  # ...from distinct targets

    for members in KEY_ID_NORMALISATION_CLASSES:
        signatures = {find(table, vector_id)["signature"] for vector_id in members}
        key_ids = {find(table, vector_id)["key_id"] for vector_id in members}
        supplied = {find(table, vector_id)["key_id_input"] for vector_id in members}
        assert len(signatures) == 1, members  # one signed request...
        assert len(key_ids) == 1, members  # ...one normalised key id...
        assert len(supplied) == len(members), members  # ...from distinct spellings


def test_vector_ids_are_unique(table):
    ids = [v["id"] for v in table["vectors"]]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# Table shape
# ---------------------------------------------------------------------------
def test_table_declares_at_least_twelve_vectors(table):
    assert len(table["vectors"]) >= 12


def test_table_declares_version_and_algorithm(table):
    assert table["signature_version"] == "v1"
    assert table["algorithm"] == "HMAC-SHA256"
    assert table["schema"] == "perceivo.hmac-request-signing.golden-vectors/1"


def test_table_declares_the_server_parser_contract(table):
    # A vector is only meaningful relative to a named parser.
    contract = table["server_parser_contract"]
    assert contract["http_parser"] == "httptools"
    assert contract["uvicorn"] == "0.35.0"


def test_table_secret_base64_decodes_to_the_utf8_secret(table):
    assert base64.b64decode(table["secret_base64"]).decode("utf-8") == table["secret_utf8"]


def test_every_vector_has_the_full_field_set(table):
    required = {
        "id",
        "description",
        "audience",
        "key_id",
        "key_id_input",
        "method",
        "target",
        "raw_path",
        "canonical_path",
        "query_string",
        "body_base64",
        "content_type",
        "canonical_content_type",
        "timestamp",
        "nonce",
        "canonical_request",
        "signature",
    }
    for vector in table["vectors"]:
        assert required <= set(vector), vector["id"]
        assert vector["description"].strip(), vector["id"]


def test_every_vector_signature_is_v1_plus_64_lowercase_hex(table):
    for vector in table["vectors"]:
        signature = vector["signature"]
        assert signature.startswith("v1="), vector["id"]
        hexpart = signature[3:]
        assert (len(hexpart), hexpart) == (64, hexpart.lower()), vector["id"]
        int(hexpart, 16)


def test_every_vector_carries_the_tables_audience_and_key_id(table):
    for vector in table["vectors"]:
        assert vector["audience"] == table["audience"], vector["id"]
        assert vector["key_id"] == table["key_id"], vector["id"]
        fields = vector["canonical_request"].split("\n")
        assert fields[0] == "perceivo-hmac-v1", vector["id"]
        assert fields[1] == vector["audience"], vector["id"]
        assert fields[2] == vector["key_id"], vector["id"]
        assert fields[7] == vector["canonical_content_type"], vector["id"]
        assert fields[8] == vector["canonical_organization"], vector["id"]
        assert fields[9] == vector["timestamp"], vector["id"]
        assert fields[10] == vector["nonce"], vector["id"]


def test_an_absent_content_type_signs_as_the_empty_string(table):
    for vector_id in ("v01-get-empty-body-empty-query", "v29-absent-content-type-with-a-body"):
        vector = find(table, vector_id)
        assert vector["content_type"] is None, vector_id
        assert vector["canonical_content_type"] == "", vector_id
        assert vector["canonical_request"].split("\n")[7] == "", vector_id


def test_raw_path_and_query_string_agree_with_the_target(table):
    for vector in table["vectors"]:
        assert split_target(vector["target"]) == (
            vector["raw_path"],
            vector["query_string"],
        ), vector["id"]


# ---------------------------------------------------------------------------
# The negative vectors
# ---------------------------------------------------------------------------
# Each carries a valid MAC over its own canonical string; only a binding verifier
# refuses them.
def test_every_negative_vector_has_a_correct_mac(table):
    """Every negative vector carries a correct MAC."""
    secret = table["secret_utf8"]
    for vector in table["negative_vectors"]:
        assert vector["mac_is_correct"] is True, vector["id"]
        assert verify_signature(vector["signature"], vector["canonical_request"], secret), vector[
            "id"
        ]


def test_the_bound_verifier_still_accepts_every_positive_vector(table):
    """The bound verifier accepts every positive vector."""
    secret = table["secret_utf8"]
    for vector in table["vectors"]:
        assert verify_signed_request(
            signature=vector["signature"],
            canonical_request=vector["canonical_request"],
            secret=secret,
            audience=vector["audience"],
            # The supplied spelling, so v28 exercises the verifier's own
            # normalisation rather than being handed a pre-normalised value.
            key_id=vector["key_id_input"],
        ), vector["id"]


# ---------------------------------------------------------------------------
# The unsignable vectors
# ---------------------------------------------------------------------------
# Inputs that have no signature. The API refuses every Content-Type byte outside
# ASCII printable 0x20-0x7E before it verifies anything.


def test_the_table_ships_the_unsignable_vectors(table):
    assert {v["id"] for v in table["unsignable_vectors"]} == {
        # field 8: the charset rows
        "u01-content-type-non-ascii-text",
        "u02-content-type-latin1-high-byte",
        "u03-content-type-newline",
        "u04-content-type-tab",
        "u05-content-type-del-control",
        # field 9: the organization rows
        "u06-organization-uppercase-uuid",
        "u07-organization-braced-uuid",
        "u08-organization-unhyphenated-uuid",
        "u09-organization-not-a-uuid",
        "u10-organization-newline",
        "u11-organization-duplicate-header",
    }


def test_every_unsignable_vector_carries_no_signature(table):
    """An unsignable vector publishes no canonical request or signature."""
    for vector in table["unsignable_vectors"]:
        assert vector["signable"] is False, vector["id"]
        assert vector["must_sign"] is False, vector["id"]
        assert "canonical_request" not in vector, vector["id"]
        assert "signature" not in vector, vector["id"]
        assert vector["field_number"] in (8, 9), vector["id"]


def test_every_unsignable_vector_is_actually_refused_by_the_signer(table):
    """The signer refuses every field-8 unsignable vector in the shipped table."""
    for vector in table["unsignable_vectors"]:
        if vector["field_number"] != 8:
            continue
        raw = base64.b64decode(vector["content_type_base64"])
        with pytest.raises(SigningError):
            canonical_content_type(raw)


def test_the_unsignable_inputs_are_genuinely_outside_the_accepted_set(table):
    """Each field-8 unsignable vector carries a byte outside printable ASCII."""
    for vector in table["unsignable_vectors"]:
        if vector["field_number"] != 8:
            continue
        raw = base64.b64decode(vector["content_type_base64"])
        assert any(byte < 0x20 or byte > 0x7E for byte in raw), vector["id"]
