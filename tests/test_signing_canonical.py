"""Canonicalization rules, one test per rule (the secret-free half).

The keyed half is in ``test_signing_keyed.py``.
"""

from __future__ import annotations

import hashlib

import pytest

from perceivo_client.signing import (
    AUDIENCE_LOCAL,
    AUDIENCE_PRODUCTION,
    CANONICAL_DOMAIN,
    CANONICAL_FIELD_COUNT,
    SigningError,
    build_canonical_request,
    canonical_audience,
    canonical_content_type,
    canonical_key_id,
    canonical_path,
)

TS = 1767225600
NONCE = "sT8kQ2vX7wLpR4nB1mZ6yH0j"
AUDIENCE = AUDIENCE_LOCAL
KEY_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"


def canonical(
    method="GET",
    raw_path="/x",
    query="",
    body=None,
    timestamp=TS,
    nonce=NONCE,
    audience=AUDIENCE,
    key_id=KEY_ID,
    content_type=None,
    organization=None,
):
    return build_canonical_request(
        audience=audience,
        key_id=key_id,
        method=method,
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=content_type,
        organization=organization,
        timestamp=timestamp,
        nonce=nonce,
    )


# ---------------------------------------------------------------------------
# Shape of the canonical string
# ---------------------------------------------------------------------------
def test_canonical_request_has_ten_fields_and_nine_separators():
    result = canonical(method="POST", raw_path="/a", query="b=1", body=b"x")
    assert result.count("\n") == 10
    assert len(result.split("\n")) == CANONICAL_FIELD_COUNT == 11
    assert not result.endswith("\n")


def test_canonical_request_field_order_is_the_v1r2_order():
    fields = canonical(
        method="PUT",
        raw_path="/a/b",
        query="z=1",
        body=b"hi",
        content_type="text/plain",
        organization=None,
    ).split("\n")
    assert fields[0] == "perceivo-hmac-v1"
    assert fields[1] == AUDIENCE
    assert fields[2] == KEY_ID
    assert fields[3] == "PUT"
    assert fields[4] == "/a/b"
    assert fields[5] == "z=1"
    assert fields[6] == hashlib.sha256(b"hi").hexdigest()
    assert fields[7] == "text/plain"
    assert fields[9] == str(TS)
    assert fields[10] == NONCE


def test_the_nonce_is_still_the_last_field():
    """The nonce is the last field of the canonical string."""
    fields = canonical(content_type="application/json").split("\n")
    assert fields[-1] == NONCE
    assert fields[-2] == str(TS)


def test_field_one_is_a_constant_and_is_not_configurable():
    """It is a domain separator: the same secret under another scheme must not
    produce a string this verifier will accept."""
    assert CANONICAL_DOMAIN == "perceivo-hmac-v1"
    assert canonical().split("\n")[0] == CANONICAL_DOMAIN
    assert "audience" not in CANONICAL_DOMAIN
    # No argument sets field 1.
    assert canonical(audience=AUDIENCE_PRODUCTION).split("\n")[0] == CANONICAL_DOMAIN


def test_empty_query_keeps_the_separators():
    # The field is empty but the nine \n remain, so the string still has 10 fields.
    assert canonical(query="").split("\n")[5] == ""
    assert canonical(query="").count("\n") == 10


def test_host_is_not_a_canonical_field():
    """The signature covers no host; the configured audience binds the deployment."""
    result = canonical(raw_path="/v1/x")
    assert "api.perceivo.ai" not in result
    assert len(result.split("\n")) == 11


def test_canonical_string_carries_no_scheme_or_absolute_url():
    assert "http://" not in canonical()
    assert "https://" not in canonical()


# ---------------------------------------------------------------------------
# audience — field 2
# ---------------------------------------------------------------------------
def test_audience_is_signed_verbatim_and_is_case_significant():
    assert canonical(audience="perceivo-api-prod").split("\n")[1] == "perceivo-api-prod"
    assert canonical(audience="Perceivo-API-Prod").split("\n")[1] == "Perceivo-API-Prod"


def test_audience_is_required():
    with pytest.raises(SigningError):
        canonical(audience=None)
    with pytest.raises(SigningError):
        canonical(audience="")


@pytest.mark.parametrize(
    "value",
    [
        "has space",
        "has/slash",
        "has\nnewline",
        "café",
        "a" * 65,
        "api.perceivo.ai:443/path",
    ],
)
def test_audience_outside_the_grammar_is_rejected(value):
    with pytest.raises(SigningError):
        canonical(audience=value)


@pytest.mark.parametrize(
    "value",
    ["perceivo-api-prod", "perceivo-api-local", "a", "a.b_c:d-e", "A" * 64],
)
def test_audience_inside_the_grammar_is_accepted(value):
    assert canonical_audience(value) == value


def test_the_two_published_audiences_are_legal():
    assert canonical_audience(AUDIENCE_PRODUCTION) == "perceivo-api-prod"
    assert canonical_audience(AUDIENCE_LOCAL) == "perceivo-api-local"


# ---------------------------------------------------------------------------
# key_id: field 3, and its normalisation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "supplied",
    [
        "0f8fad5b-d9cb-469f-a165-70867728950e",
        "0F8FAD5B-D9CB-469F-A165-70867728950E",
        "0f8fad5bd9cb469fa16570867728950e",
        "{0f8fad5b-d9cb-469f-a165-70867728950e}",
        "urn:uuid:0f8fad5b-d9cb-469f-a165-70867728950e",
    ],
)
def test_every_uuid_spelling_normalises_to_one_field_three(supplied):
    """Each spelling yields the same signature or a rejection."""
    assert canonical_key_id(supplied) == KEY_ID
    assert canonical(key_id=supplied).split("\n")[2] == KEY_ID


def test_key_id_is_rejected_when_it_is_not_a_uuid():
    """It is the api_keys.id, not the key prefix every key in an org shares."""
    for value in ("pk_live_abc", "", "not-a-uuid", "0f8fad5b-d9cb-469f-a165"):
        with pytest.raises(SigningError):
            canonical_key_id(value)


def test_key_id_error_names_the_prefix_confusion():
    with pytest.raises(SigningError, match="prefix"):
        canonical_key_id("pk_live_abc")


# ---------------------------------------------------------------------------
# content_type — field 8, verbatim
# ---------------------------------------------------------------------------
def test_content_type_is_signed_verbatim():
    for value in (
        "application/json",
        "application/json; charset=utf-8",
        "application/JSON; Charset=UTF-8",
        "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxk",
        "  application/json  ",
    ):
        assert canonical(content_type=value).split("\n")[7] == value


def test_absent_content_type_is_the_empty_string():
    assert canonical(content_type=None).split("\n")[7] == ""
    assert canonical_content_type(None) == ""


def test_content_type_with_a_newline_is_rejected_never_escaped():
    with pytest.raises(SigningError):
        canonical(content_type="application/json\nX-Evil: 1")


def test_a_repeated_content_type_header_is_unsignable():
    """Joining or picking one would sign something the request does not carry."""
    with pytest.raises(SigningError):
        canonical_content_type(["application/json", "text/plain"])
    assert canonical_content_type(["application/json"]) == "application/json"
    assert canonical_content_type([]) == ""


def test_the_boundary_parameter_is_part_of_what_is_signed():
    """Field 8 is verbatim, so the multipart boundary is signed."""
    first = canonical(body=b"same", content_type="multipart/form-data; boundary=A")
    second = canonical(body=b"same", content_type="multipart/form-data; boundary=B")
    assert first.split("\n")[6] == second.split("\n")[6]  # identical body bytes
    assert first != second


# ---------------------------------------------------------------------------
# METHOD
# ---------------------------------------------------------------------------
def test_method_is_signed_verbatim():
    assert canonical(method="DELETE").split("\n")[3] == "DELETE"


def test_lowercase_method_is_rejected_never_normalized():
    with pytest.raises(SigningError, match="uppercase"):
        canonical(method="get")


def test_non_alpha_method_is_rejected():
    with pytest.raises(SigningError):
        canonical(method="GET ")


# ---------------------------------------------------------------------------
# canonical_path: the base path transform
#
# Field 5 is raw_path put through RFC 3986 §6.2.2 normalisation: percent-decode
# unreserved escapes only, then remove dot segments. The API applies the same
# transform before routing.
# ---------------------------------------------------------------------------
def test_canonical_path_is_field_five_of_the_canonical_request():
    assert canonical(raw_path="/a/../b").split("\n")[4] == canonical_path("/a/../b") == "/b"


def test_ordinary_path_passes_through_unchanged():
    assert canonical_path("/v1/orchestrations") == "/v1/orchestrations"


def test_trailing_slash_is_significant():
    # BASE does not strip it, so /x and /x/ remain different requests.
    assert canonical_path("/x/") == "/x/"
    assert canonical(raw_path="/x") != canonical(raw_path="/x/")


def test_double_slash_is_preserved():
    # BASE removes dot segments; it does not merge adjacent slashes.
    assert canonical_path("/a//b") == "/a//b"
    assert canonical(raw_path="/a//b").split("\n")[4] == "/a//b"


# --- step 1: percent-decode unreserved only --------------------------------
def test_unreserved_escapes_decode_in_both_hex_cases():
    assert canonical_path("/a/%7eb") == "/a/~b"
    assert canonical_path("/a/%7Eb") == "/a/~b"


def test_every_unreserved_class_decodes():
    # A-Z a-z 0-9 - . _ ~  (RFC 3986 §2.3): %2D %5F %2E %7E, a letter of each case
    # and a digit.
    assert canonical_path("/%41%7a%39%2D%5F%7E") == "/Az9-_~"


def test_reserved_escapes_are_not_decoded():
    # /a%2Fb must not collapse into /a/b — that decode is structural and lossy.
    assert canonical_path("/a%2Fb") == "/a%2Fb"
    assert canonical(raw_path="/a%2Fb") != canonical(raw_path="/a/b")


def test_hex_case_of_an_undecoded_escape_is_not_normalised():
    upper = canonical(raw_path="/a%2Fb")
    lower = canonical(raw_path="/a%2fb")
    assert canonical_path("/a%2Fb") == "/a%2Fb"
    assert canonical_path("/a%2fb") == "/a%2fb"
    assert upper != lower


def test_percent_encoded_utf8_path_is_accepted_and_left_encoded():
    # %C3 and %A9 are not unreserved, so café stays percent-encoded.
    assert canonical_path("/caf%C3%A9") == "/caf%C3%A9"
    assert canonical(raw_path="/caf%C3%A9").split("\n")[4] == "/caf%C3%A9"


def test_a_malformed_escape_is_left_exactly_as_written():
    # Not a well-formed escape, so there is nothing to decode and nothing to fix.
    assert canonical_path("/a%zz") == "/a%zz"
    assert canonical_path("/a%2") == "/a%2"
    assert canonical_path("/a%") == "/a%"


# --- step 2: remove dot segments (RFC 3986 §5.2.4) -------------------------
def test_dot_segments_are_removed_not_preserved():
    assert canonical_path("/a/../b") == "/b"
    assert canonical_path("/a/./b") == "/a/b"
    assert canonical_path("/./y") == "/y"
    assert canonical_path("/a/b/../../c") == "/c"


def test_dot_segment_removal_keeps_a_trailing_slash_it_produced():
    assert canonical_path("/a/./b/../c/") == "/a/c/"


def test_a_dot_segment_that_would_escape_the_root_is_clamped():
    # RFC 3986 §5.2.4 pops nothing when the output buffer is empty; the path
    # cannot be walked above /.
    assert canonical_path("/..") == "/"
    assert canonical_path("/../x") == "/x"
    assert canonical_path("/a/..") == "/"


# --- step order ------------------------------------------------------------
def test_encoded_dot_segments_decode_first_and_are_then_removed():
    """``%2E`` is unreserved, so step 1 turns it into a dot segment for step 2."""
    assert canonical_path("/a/%2E%2E/b") == "/b"
    assert canonical_path("/a/%2e%2e/b") == "/b"
    assert canonical_path("/a/%2e/b") == "/a/b"


# --- non-injectivity ------------------------------------------------------
def test_the_transform_is_not_injective_by_design():
    """Distinct targets the API cannot distinguish are one signed request."""
    assert canonical(raw_path="/a/%7eb") == canonical(raw_path="/a/~b")
    assert canonical(raw_path="/v1/x/../c") == canonical(raw_path="/v1/c")


# --- rejected inputs -------------------------------------------------------
def test_raw_path_must_be_origin_form():
    with pytest.raises(SigningError, match="origin-form"):
        canonical(raw_path="x")
    with pytest.raises(SigningError, match="origin-form"):
        canonical_path("http://host/a")


def test_raw_path_rejects_embedded_query_or_fragment():
    with pytest.raises(SigningError, match="separately"):
        canonical(raw_path="/x?a=1")
    with pytest.raises(SigningError, match="separately"):
        canonical(raw_path="/x#f")


def test_non_ascii_path_is_rejected_not_encoded_for_the_caller():
    with pytest.raises(SigningError, match="printable ASCII"):
        canonical(raw_path="/café")


def test_canonical_path_accepts_bytes():
    assert canonical_path(b"/a/%7eb") == "/a/~b"


def test_non_ascii_bytes_path_is_rejected_not_silently_decoded():
    with pytest.raises(SigningError, match="ASCII"):
        canonical_path(b"/caf\xc3\xa9")


def test_a_path_of_the_wrong_type_is_rejected():
    with pytest.raises(SigningError, match="str or bytes"):
        canonical_path(17)


def test_a_method_of_the_wrong_type_is_rejected():
    with pytest.raises(SigningError, match="must be str"):
        canonical(method=b"GET")


def test_remove_dot_segments_implements_the_rfc_branches_a_path_cannot_reach():
    """RFC 3986 §5.2.4 branches 2A and 2D, which ``canonical_path`` cannot reach."""
    from perceivo_client.signing._target import _remove_dot_segments

    assert _remove_dot_segments("../a") == "a"  # 2A
    assert _remove_dot_segments("./a") == "a"  # 2A
    assert _remove_dot_segments(".") == ""  # 2D
    assert _remove_dot_segments("..") == ""  # 2D
    # 2B's `remaining == "/."` form is reachable from an origin-form path.
    assert canonical_path("/a/.") == "/a/"
    # RFC 3986 §5.2.4's own worked example, start to finish.
    assert _remove_dot_segments("/a/b/c/./../../g") == "/a/g"


# ---------------------------------------------------------------------------
