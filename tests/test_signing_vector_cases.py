"""The canonicalization rules each golden vector pins, with mutant controls."""

from __future__ import annotations

import base64
import hashlib
import hmac

import pytest

from perceivo_client.signing import EMPTY_BODY_SHA256, canonical_path
from tests._signing_vectors_support import GENERATOR_PATH, PRIMARY_ID, find, load_table


@pytest.fixture(scope="module")
def table() -> dict:
    return load_table()


# ---------------------------------------------------------------------------
# The specific canonicalization cases the vectors exist to pin
# ---------------------------------------------------------------------------
def test_vector_empty_body_field_is_the_zero_byte_digest(table):
    assert find(table, PRIMARY_ID)["canonical_request"].split("\n")[6] == EMPTY_BODY_SHA256


def test_vector_query_order_is_preserved(table):
    # ?limit=10&cursor=abc&archived=false, non-alphabetical.
    assert (
        find(table, "v03-query-order-is-preserved")["canonical_request"].split("\n")[5]
        == "limit=10&cursor=abc&archived=false"
    )


def test_vector_valueless_key_keeps_its_distinction(table):
    assert find(table, "v04-valueless-key")["canonical_request"].split("\n")[5] == "flag&flag=&a=1"


def test_vector_empty_value_is_not_a_bare_key(table):
    assert find(table, "v05-empty-value")["canonical_request"].split("\n")[5] == "a="


def test_vector_repeated_keys_keep_submission_order(table):
    assert (
        find(table, "v06-repeated-key")["canonical_request"].split("\n")[5]
        == "tag=zeta&tag=alpha&tag=beta"
    )


def test_vector_percent_encoding_case_changes_the_signature(table):
    upper = find(table, "v07-percent-2f-in-path")
    lower = find(table, "v08-percent-encoding-case-preserved")
    assert upper["signature"] != lower["signature"]
    assert upper["canonical_request"].split("\n")[4] == "/v1/files/a%2Fb"
    assert lower["canonical_request"].split("\n")[4] == "/v1/files/a%2fb"


def test_vector_plus_is_not_decoded(table):
    assert find(table, "v09-plus-in-query-value")["canonical_request"].split("\n")[5] == (
        "q=a+b&r=a%20b"
    )


def test_vector_double_slash_is_preserved(table):
    assert find(table, "v10-double-slash-path")["canonical_request"].split("\n")[4] == (
        "/v1//components"
    )


def test_vector_non_ascii_path_is_percent_encoded_utf8(table):
    assert find(table, "v11-non-ascii-path")["canonical_request"].split("\n")[4] == (
        "/v1/files/caf%C3%A9"
    )


def test_vector_non_utf8_body_hashes_as_bytes(table):
    vector = find(table, "v12-non-utf8-body")
    body = base64.b64decode(vector["body_base64"])
    assert body.startswith(b"\xff\xfe\x00\x01")
    with pytest.raises(UnicodeDecodeError):
        body.decode("utf-8")  # not text — proof the body is hashed as bytes
    assert vector["canonical_request"].split("\n")[6] == hashlib.sha256(body).hexdigest()


def test_vector_trailing_slash_is_significant(table):
    assert (
        find(table, "v13-trailing-slash-significant")["signature"]
        != find(table, PRIMARY_ID)["signature"]
    )


def test_vector_empty_query_element_is_retained_in_place(table):
    assert find(table, "v15-empty-query-element")["canonical_request"].split("\n")[5] == "a=1&&b=2"


def test_vector_value_containing_equals(table):
    assert (
        find(table, "v16-value-containing-equals")["canonical_request"].split("\n")[5]
        == "filter=a=b&z=1"
    )


# ---------------------------------------------------------------------------
# The base path rule, and the two controls that make it non-vacuous
# ---------------------------------------------------------------------------
def test_every_vector_path_field_is_the_base_normalised_path(table):
    """Field 5 is ``canonical_path(raw_path)``, not ``raw_path`` as sent."""
    for vector in table["vectors"]:
        assert vector["canonical_path"] == canonical_path(vector["raw_path"]), vector["id"]
        assert vector["canonical_request"].split("\n")[4] == vector["canonical_path"], vector["id"]


def test_vector_unreserved_escape_decodes_in_both_hex_cases(table):
    lower = find(table, "v22-unreserved-escape-lowercase-hex")
    upper = find(table, "v23-unreserved-escape-uppercase-hex")
    literal = find(table, "v24-literal-unreserved-character")
    assert (lower["raw_path"], upper["raw_path"], literal["raw_path"]) == (
        "/v1/files/a%7eb",
        "/v1/files/a%7Eb",
        "/v1/files/a~b",
    )
    for vector in (lower, upper, literal):
        assert vector["canonical_path"] == "/v1/files/a~b", vector["id"]


def test_vector_dot_segments_are_removed(table):
    assert find(table, "v25-dot-segment-removed")["canonical_path"] == "/v1/components"
    assert find(table, "v26-single-dot-segment-removed")["canonical_path"] == "/v1/components"


def test_vector_encoded_dot_segment_proves_decode_runs_before_removal(table):
    """``%2E`` is the one spelling that separates the two possible step orders."""
    vector = find(table, "v27-encoded-dot-segment-decode-then-remove")
    assert vector["raw_path"] == "/v1/x/%2E%2E/components"
    assert vector["canonical_path"] == "/v1/components"
    assert vector["canonical_path"] != _remove_then_decode(vector["raw_path"])


def test_vector_reserved_escape_is_not_decoded_by_the_base_transform(table):
    """``%2F`` is reserved: step 1 must leave it, hex case included."""
    for vector_id, expected in (
        ("v07-percent-2f-in-path", "/v1/files/a%2Fb"),
        ("v08-percent-encoding-case-preserved", "/v1/files/a%2fb"),
        ("v11-non-ascii-path", "/v1/files/caf%C3%A9"),
    ):
        assert find(table, vector_id)["canonical_path"] == expected, vector_id


def test_vector_base_transform_does_not_merge_slashes_or_strip_trailing_slash(table):
    assert find(table, "v10-double-slash-path")["canonical_path"] == "/v1//components"
    assert find(table, "v13-trailing-slash-significant")["canonical_path"] == "/v1/orchestrations/"


def _verbatim_canonical_path(raw_path: str) -> str:
    """The verbatim path rule: the mutant the published table is run against."""
    return raw_path


def _remove_then_decode(raw_path: str) -> str:
    """The step-order mutant: remove dot segments first, then decode unreserved."""
    from perceivo_client.signing._target import _decode_unreserved, _remove_dot_segments

    return _decode_unreserved(_remove_dot_segments(raw_path))


def _mutant_signature(table: dict, vector: dict, path: str) -> str:
    fields = vector["canonical_request"].split("\n")
    fields[4] = path
    return (
        "v1="
        + hmac.new(
            table["secret_utf8"].encode("utf-8"), "\n".join(fields).encode("utf-8"), hashlib.sha256
        ).hexdigest()
    )


def test_the_table_fails_against_the_verbatim_path_canonicaliser(table):
    """The vectors tell the base path transform from verbatim ``raw_path``."""
    disagreements = []
    for vector in table["vectors"]:
        mutated = _verbatim_canonical_path(vector["raw_path"])
        if mutated == vector["canonical_path"]:
            continue
        assert _mutant_signature(table, vector, mutated) != vector["signature"], vector["id"]
        disagreements.append(vector["id"])

    assert set(disagreements) == {
        "v22-unreserved-escape-lowercase-hex",
        "v23-unreserved-escape-uppercase-hex",
        "v25-dot-segment-removed",
        "v26-single-dot-segment-removed",
        "v27-encoded-dot-segment-decode-then-remove",
    }


def test_the_table_fails_against_the_reversed_step_order(table):
    """The vectors pin the two base path steps in order."""
    disagreements = []
    for vector in table["vectors"]:
        mutated = _remove_then_decode(vector["raw_path"])
        if mutated == vector["canonical_path"]:
            continue
        assert _mutant_signature(table, vector, mutated) != vector["signature"], vector["id"]
        disagreements.append(vector["id"])

    assert set(disagreements) == {"v27-encoded-dot-segment-decode-then-remove"}


# ---------------------------------------------------------------------------
# The verbatim query rule
# ---------------------------------------------------------------------------
def test_every_vector_query_field_is_the_query_string_verbatim(table):
    """Field 6 is the query bytes as sent — not split, sorted, or reassembled."""
    for vector in table["vectors"]:
        assert vector["canonical_request"].split("\n")[5] == vector["query_string"], vector["id"]


def test_permutation_pair_has_two_different_signatures(table):
    """v19/v20 are the same two elements in both orders and sign differently."""
    first = find(table, "v19-permutation-pair-a")
    second = find(table, "v20-permutation-pair-b")
    assert first["query_string"] == "org=attacker&org=victim"
    assert second["query_string"] == "org=victim&org=attacker"
    assert sorted(first["query_string"].split("&")) == sorted(second["query_string"].split("&"))
    assert first["canonical_request"] != second["canonical_request"]
    assert first["signature"] != second["signature"]


def _sorting_canonical_query(text: str) -> str:
    """A canonicaliser that sorts the query: the mutant the query vectors reject."""
    if not text:
        return ""
    pairs = []
    for element in text.split("&"):
        key, sep, value = element.partition("=")
        pairs.append((key.encode("ascii"), value.encode("ascii"), 1 if sep else 0, element))
    pairs.sort(key=lambda item: (item[0], item[1], item[2]))
    return "&".join(item[3] for item in pairs)


def test_the_table_fails_against_the_sorting_canonicaliser(table):
    """The vectors tell the verbatim query rule from a sorting mutant."""
    secret = table["secret_utf8"].encode("utf-8")
    disagreements = []
    for vector in table["vectors"]:
        mutated = _sorting_canonical_query(vector["query_string"])
        if mutated == vector["query_string"]:
            continue
        fields = vector["canonical_request"].split("\n")
        fields[5] = mutated
        mutant_signature = (
            "v1=" + hmac.new(secret, "\n".join(fields).encode("utf-8"), hashlib.sha256).hexdigest()
        )
        assert mutant_signature != vector["signature"], vector["id"]
        disagreements.append(vector["id"])

    assert set(disagreements) == {
        "v03-query-order-is-preserved",
        "v04-valueless-key",
        "v06-repeated-key",
        "v15-empty-query-element",
        "v20-permutation-pair-b",
        "v21-bare-key-order-preserved",
    }

    # The permutation pair collapses under the mutant.
    first = find(table, "v19-permutation-pair-a")["query_string"]
    second = find(table, "v20-permutation-pair-b")["query_string"]
    assert _sorting_canonical_query(first) == _sorting_canonical_query(second)


def test_vector_explicitly_empty_body_equals_no_body(table):
    assert find(table, "v18-explicitly-empty-body")["canonical_request"].split("\n")[6] == (
        EMPTY_BODY_SHA256
    )


def test_generator_output_is_stable(table):
    """Regenerating the table must be a no-op unless the rules changed."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_generate_vectors", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    regenerated = module.build()
    assert regenerated["vectors"] == table["vectors"]
    assert regenerated["negative_vectors"] == table["negative_vectors"]


# ---------------------------------------------------------------------------
# Content-Type (field 8)
# ---------------------------------------------------------------------------
def test_every_vector_content_type_field_is_the_header_verbatim(table):
    """Field 8 is the header as sent. Absent means the empty string."""
    for vector in table["vectors"]:
        expected = "" if vector["content_type"] is None else vector["content_type"]
        assert vector["canonical_content_type"] == expected, vector["id"]
        assert vector["canonical_request"].split("\n")[7] == expected, vector["id"]


def test_boundary_pair_signs_the_same_bytes_two_different_ways(table):
    """v30/v31 differ only in the multipart boundary and do not collide."""
    first = find(table, "v30-multipart-boundary-pair-a")
    second = find(table, "v31-multipart-boundary-pair-b")
    assert first["body_base64"] == second["body_base64"]
    assert first["canonical_request"].split("\n")[6] == second["canonical_request"].split("\n")[6]
    assert first["content_type"] != second["content_type"]
    assert first["canonical_request"] != second["canonical_request"]
    assert first["signature"] != second["signature"]


def test_charset_parameter_and_its_case_both_change_the_signature(table):
    """Parameters are not stripped and the value is not case-folded."""
    bare = find(table, "v02-post-json-body")
    lower = find(table, "v32-charset-pair-a")
    upper = find(table, "v33-charset-pair-b")
    assert bare["content_type"] == "application/json"
    assert lower["content_type"] == "application/json; charset=utf-8"
    assert upper["content_type"] == "application/json; charset=UTF-8"
    assert {v["body_base64"] for v in (bare, lower, upper)} == {bare["body_base64"]}
    assert len({v["signature"] for v in (bare, lower, upper)}) == 3


def _media_type_only(content_type: str) -> str:
    """The media-type mutant: lowercase the type and drop every parameter."""
    return content_type.partition(";")[0].strip().lower()


def test_the_table_fails_against_a_media_type_only_canonicaliser(table):
    """The vectors pin field 8 verbatim, not normalised."""
    secret = table["secret_utf8"].encode("utf-8")
    disagreements = []
    for vector in table["vectors"]:
        if vector["content_type"] is None:
            continue
        mutated = _media_type_only(vector["content_type"])
        if mutated == vector["canonical_content_type"]:
            continue
        fields = vector["canonical_request"].split("\n")
        fields[7] = mutated
        mutant_signature = (
            "v1=" + hmac.new(secret, "\n".join(fields).encode("utf-8"), hashlib.sha256).hexdigest()
        )
        assert mutant_signature != vector["signature"], vector["id"]
        disagreements.append(vector["id"])

    assert set(disagreements) == {
        "v17-utf8-body",
        "v30-multipart-boundary-pair-a",
        "v31-multipart-boundary-pair-b",
        "v32-charset-pair-a",
        "v33-charset-pair-b",
    }

    first = find(table, "v30-multipart-boundary-pair-a")
    second = find(table, "v31-multipart-boundary-pair-b")
    assert _media_type_only(first["content_type"]) == _media_type_only(second["content_type"])


# ---------------------------------------------------------------------------
# key_id (field 3): normalisation, and the mutant that skips it
# ---------------------------------------------------------------------------
def test_the_table_fails_against_a_signer_that_does_not_normalise_the_key_id(table):
    """A vector pins key id normalisation: v28 supplies an uppercase uuid."""
    vector = find(table, "v28-key-id-mixed-case-normalised")
    assert vector["key_id_input"] == "0F8FAD5B-D9CB-469F-A165-70867728950E"
    assert vector["key_id"] == "0f8fad5b-d9cb-469f-a165-70867728950e"
    assert vector["canonical_request"].split("\n")[2] == vector["key_id"]

    fields = vector["canonical_request"].split("\n")
    fields[2] = vector["key_id_input"]
    mutant_signature = (
        "v1="
        + hmac.new(
            table["secret_utf8"].encode("utf-8"),
            "\n".join(fields).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )
    assert mutant_signature != vector["signature"]
