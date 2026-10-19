"""Canonical target, query, body, timestamp and nonce rules."""

from __future__ import annotations

import hashlib
import unicodedata

import pytest

from perceivo_client.signing import (
    EMPTY_BODY_SHA256,
    MAX_CLOCK_SKEW_SECONDS,
    SigningError,
    body_sha256_hex,
    canonical_query,
    generate_nonce,
    split_target,
)
from tests.test_signing_canonical import TS, canonical


# ---------------------------------------------------------------------------
# split_target — the unsignable-target rules
# ---------------------------------------------------------------------------
def test_split_target_splits_on_the_first_question_mark():
    assert split_target("/x?a=1?b=2") == ("/x", "a=1?b=2")


def test_split_target_no_query():
    assert split_target("/x") == ("/x", "")


def test_split_target_accepts_bytes():
    assert split_target(b"/x?a=1") == ("/x", "a=1")


def test_absolute_form_target_is_rejected():
    with pytest.raises(SigningError, match="origin-form"):
        split_target("http://api.perceivo.ai/x")


def test_options_asterisk_target_is_rejected():
    with pytest.raises(SigningError, match="origin-form"):
        split_target("*")


def test_fragment_target_is_rejected():
    with pytest.raises(SigningError, match="fragment"):
        split_target("/x#frag")


def test_bare_trailing_question_mark_is_rejected():
    with pytest.raises(SigningError, match="bare"):
        split_target("/x?")


# ---------------------------------------------------------------------------
# canonical_query
# ---------------------------------------------------------------------------
def test_empty_and_absent_query_are_the_empty_string():
    assert canonical_query("") == ""
    assert canonical_query(None) == ""
    assert canonical_query(b"") == ""


def test_query_is_emitted_verbatim_and_is_not_sorted():
    # The bytes, in the order sent.
    assert canonical_query("z=1&a=2&m=3") == "z=1&a=2&m=3"


def test_repeated_keys_keep_their_submission_order():
    # The origin resolves a repeated key to its last occurrence, so order is meaning.
    assert canonical_query("tag=zeta&tag=alpha&tag=beta") == "tag=zeta&tag=alpha&tag=beta"


def test_permutations_of_one_query_do_not_collide():
    """Permutations of a repeated key are distinct signed requests."""
    first = canonical_query("org=attacker&org=victim")
    second = canonical_query("org=victim&org=attacker")
    assert first == "org=attacker&org=victim"
    assert second == "org=victim&org=attacker"
    assert first != second


def test_valueless_key_is_distinct_from_empty_value():
    assert canonical_query("flag") == "flag"
    assert canonical_query("flag=") == "flag="
    assert canonical_query("flag") != canonical_query("flag=")


def test_bare_key_and_the_same_key_with_equals_keep_their_order():
    # Both orderings survive as different signed requests.
    assert canonical_query("flag=&flag") == "flag=&flag"
    assert canonical_query("flag&flag=") == "flag&flag="


def test_an_equals_inside_a_value_needs_no_rule():
    # Nothing splits on '='.
    assert canonical_query("z=1&filter=a=b") == "z=1&filter=a=b"
    assert canonical_query("a=n&a=m=z") == "a=n&a=m=z"


def test_empty_elements_are_retained_in_place():
    assert canonical_query("a=1&&b=2") == "a=1&&b=2"


def test_plus_is_not_decoded_as_a_space():
    assert canonical_query("a=b+c") == "a=b+c"


def test_percent_escapes_in_the_query_are_not_decoded():
    assert canonical_query("a=%41") == "a=%41"


def test_query_hex_case_is_preserved():
    assert canonical_query("a=%2f") != canonical_query("a=%2F")


def test_percent_escapes_are_neither_decoded_nor_reordered():
    # Nothing is decoded or reordered.
    assert canonical_query("b=1&%7E=2") == "b=1&%7E=2"


def test_query_accepts_bytes():
    assert canonical_query(b"z=1&a=2") == "z=1&a=2"


def test_non_ascii_query_is_rejected():
    with pytest.raises(SigningError, match="printable ASCII"):
        canonical_query("a=café")


def test_canonical_query_does_not_enforce_the_api_key_rule():
    # Kept a total function of its input so it can reproduce any vector; the
    # api_key refusal belongs to the request-level entry points.
    assert canonical_query("api_key=abc") == "api_key=abc"


# ---------------------------------------------------------------------------
# Body
# ---------------------------------------------------------------------------
def test_empty_body_is_the_sha256_of_zero_bytes():
    assert body_sha256_hex(None) == EMPTY_BODY_SHA256
    assert body_sha256_hex(b"") == EMPTY_BODY_SHA256
    assert hashlib.sha256(b"").hexdigest() == EMPTY_BODY_SHA256


def test_empty_body_is_never_the_digest_of_braces():
    assert body_sha256_hex(None) != hashlib.sha256(b"{}").hexdigest()


def test_body_digest_is_lowercase_hex():
    digest = body_sha256_hex(b"abc")
    assert digest == digest.lower()
    assert len(digest) == 64


def test_str_body_is_utf8_encoded():
    assert body_sha256_hex("café") == hashlib.sha256("café".encode()).hexdigest()


def test_no_unicode_normalization_is_applied_to_a_str_body():
    nfc = unicodedata.normalize("NFC", "café")
    nfd = unicodedata.normalize("NFD", "café")
    assert nfc != nfd
    assert body_sha256_hex(nfc) != body_sha256_hex(nfd)


def test_non_utf8_bytes_body_hashes_fine():
    assert body_sha256_hex(b"\xff\xfe\x00\x01") == hashlib.sha256(b"\xff\xfe\x00\x01").hexdigest()


def test_streaming_body_is_rejected():
    with pytest.raises(SigningError, match="streaming"):
        body_sha256_hex(chunk for chunk in (b"a", b"b"))


# ---------------------------------------------------------------------------
# Timestamp and nonce
# ---------------------------------------------------------------------------
def test_timestamp_int_and_string_agree():
    assert canonical(timestamp=TS) == canonical(timestamp=str(TS))


def test_timestamp_rejects_padding_sign_and_fractions():
    for bad in ["01767225600", "+1767225600", "-1", "1767225600.0", 1767225600.0, "1e9"]:
        with pytest.raises(SigningError):
            canonical(timestamp=bad)


def test_timestamp_zero_is_allowed_but_leading_zeros_are_not():
    assert canonical(timestamp=0).split("\n")[9] == "0"
    with pytest.raises(SigningError):
        canonical(timestamp="00")


def test_nonce_charset_and_length_are_enforced():
    with pytest.raises(SigningError):
        canonical(nonce="short")  # < 8
    with pytest.raises(SigningError):
        canonical(nonce="a" * 129)  # > 128
    with pytest.raises(SigningError):
        canonical(nonce="has spaces!!")
    assert canonical(nonce="a" * 8).split("\n")[10] == "a" * 8
    assert canonical(nonce="a" * 128).split("\n")[10] == "a" * 128


def test_generate_nonce_is_in_the_accepted_charset_and_range():
    for _ in range(50):
        nonce = generate_nonce()
        assert 8 <= len(nonce) <= 128
        assert all(c.isalnum() or c in "_-" for c in nonce)


def test_generate_nonce_does_not_repeat():
    assert len({generate_nonce() for _ in range(200)}) == 200


def test_generate_nonce_rejects_too_little_entropy():
    with pytest.raises(SigningError):
        generate_nonce(4)


def test_skew_window_constant_matches_the_specification():
    assert MAX_CLOCK_SKEW_SECONDS == 300
