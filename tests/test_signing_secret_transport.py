"""How a secret spelling becomes HMAC key bytes, checked against the published
``secret_transport_vectors`` rows.
"""

from __future__ import annotations

import pytest

from perceivo_client.signing import (
    SigningError,
    compute_signature,
    load_golden_vectors,
    resolve_signing_credentials,
    verify_signature,
)
from perceivo_client.signing._secret import secret_to_key_bytes
from tests._signing_vectors_support import PRIMARY_ID, PRIMARY_SIGNATURE, find

HEX_DECODED = "t01-hex-disclosure-decoded"
HEX_AS_UTF8_WRONG = "t02-hex-disclosure-utf8-encoded-WRONG"
HEX_UPPERCASE = "t03-hex-disclosure-uppercase-decoded"
NON_HEX_UTF8 = "t04-non-hex-secret-utf8-encoded"
SIXTY_FOUR_NOT_HEX = "t05-sixty-four-chars-not-hex"


@pytest.fixture(scope="module")
def table() -> dict:
    return load_golden_vectors()


@pytest.fixture(scope="module")
def rows(table) -> dict[str, dict]:
    return {row["id"]: row for row in table["secret_transport_vectors"]}


# ---------------------------------------------------------------------------
# The table carries the axis at all
# ---------------------------------------------------------------------------
def test_the_table_publishes_the_secret_transport_contract(table):
    """The table expresses the platform's secret encoding."""
    contract = table["secret_transport"]
    assert contract["disclosure_decodes_to_bytes"] == 32
    assert contract["disclosure_shape"] == "64 lowercase hex characters, /^[0-9a-f]{64}$/"
    # The disclosure constant has the shape it declares.
    disclosure = contract["disclosure_secret_hex"]
    assert len(disclosure) == 64
    assert len(bytes.fromhex(disclosure)) == 32
    assert disclosure != table["secret_utf8"]


def test_the_declared_count_matches_the_rows(table):
    assert table["vector_counts"]["secret_transport"] == len(table["secret_transport_vectors"])
    assert table["vector_counts"]["secret_transport"] == 5


def test_secret_utf8_is_not_the_disclosure_shape(table):
    """``secret_utf8`` is not hex-shaped, so the positive vectors key on UTF-8 text."""
    secret = table["secret_utf8"]
    assert len(secret) != 64
    assert len(secret_to_key_bytes(secret)) == len(secret.encode("utf-8"))


# ---------------------------------------------------------------------------
# Key derivation, row by row
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "row_id",
    [HEX_DECODED, HEX_AS_UTF8_WRONG, HEX_UPPERCASE, NON_HEX_UTF8, SIXTY_FOUR_NOT_HEX],
)
def test_every_row_publishes_the_key_bytes_it_was_signed_with(rows, row_id):
    """``hmac_key_hex`` is the debugging field; it must be true, not decorative."""
    row = rows[row_id]
    assert len(bytes.fromhex(row["hmac_key_hex"])) == row["hmac_key_length_bytes"]


@pytest.mark.parametrize("row_id", [HEX_DECODED, HEX_UPPERCASE, NON_HEX_UTF8, SIXTY_FOUR_NOT_HEX])
def test_the_client_derives_the_published_key_bytes(rows, row_id):
    """Each row's secret derives the published key bytes."""
    row = rows[row_id]
    assert secret_to_key_bytes(row["secret_input"]).hex() == row["hmac_key_hex"]


@pytest.mark.parametrize("row_id", [HEX_DECODED, HEX_UPPERCASE, NON_HEX_UTF8, SIXTY_FOUR_NOT_HEX])
def test_the_client_reproduces_every_positive_transport_signature(rows, row_id):
    row = rows[row_id]
    assert row["must_verify"] is True
    assert compute_signature(row["canonical_request"], row["secret_input"]) == row["signature"]
    assert verify_signature(row["signature"], row["canonical_request"], row["secret_input"])


# ---------------------------------------------------------------------------
# The negative row
# ---------------------------------------------------------------------------
def test_the_wrong_encoding_row_is_marked_as_a_refusal(rows):
    assert rows[HEX_AS_UTF8_WRONG]["must_verify"] is False


def test_the_client_does_not_produce_the_wrong_encoding_signature(rows):
    """The client signs the hex disclosure with the decoded key, not the UTF-8 text."""
    wrong = rows[HEX_AS_UTF8_WRONG]
    produced = compute_signature(wrong["canonical_request"], wrong["secret_input"])
    assert produced != wrong["signature"], (
        "the client UTF-8-encoded the hex disclosure instead of decoding it. That is the "
        "signing-key encoding defect: a 64-byte key against the server's 32-byte one, mismatching on "
        "every production request and surfacing only as an ordinary 401."
    )
    assert produced == rows[HEX_DECODED]["signature"]


def test_the_wrong_encoding_row_is_reproducible_on_purpose(rows):
    """The published negative signature is the one UTF-8 keying produces."""
    wrong = rows[HEX_AS_UTF8_WRONG]
    keyed_as_text = wrong["secret_input"].encode("utf-8")
    assert compute_signature(wrong["canonical_request"], keyed_as_text) == wrong["signature"]
    assert len(keyed_as_text) == 64


# ---------------------------------------------------------------------------
# Agreement with the primary vector and across hex case
# ---------------------------------------------------------------------------
def test_the_non_hex_row_equals_the_primary_vector(table, rows):
    """The non-hex row signs like the primary vector."""
    assert rows[NON_HEX_UTF8]["signature"] == find(table, PRIMARY_ID)["signature"]
    assert rows[NON_HEX_UTF8]["signature"] == PRIMARY_SIGNATURE


def test_uppercase_and_lowercase_disclosures_are_one_key(rows):
    lower, upper = rows[HEX_DECODED], rows[HEX_UPPERCASE]
    assert upper["secret_input"] == lower["secret_input"].upper()
    assert upper["secret_input"] != lower["secret_input"]
    assert upper["signature"] == lower["signature"]
    assert secret_to_key_bytes(upper["secret_input"]) == secret_to_key_bytes(lower["secret_input"])


# ---------------------------------------------------------------------------
# The shape gate: alphabet and length, not either alone
# ---------------------------------------------------------------------------
def test_sixty_four_characters_outside_the_hex_alphabet_are_text(rows):
    """A length-only gate would raise here instead of signing."""
    row = rows[SIXTY_FOUR_NOT_HEX]
    assert len(row["secret_input"]) == 64
    assert row["hmac_key_length_bytes"] == 64
    assert secret_to_key_bytes(row["secret_input"]) == row["secret_input"].encode("utf-8")


@pytest.mark.parametrize("length", [62, 63, 65, 66])
def test_hex_alphabet_at_the_wrong_length_is_text(length):
    """An alphabet-only gate would decode these — and raise on the odd lengths."""
    secret = "ab" * 40
    secret = secret[:length]
    assert secret_to_key_bytes(secret) == secret.encode("utf-8")


def test_the_disclosure_length_boundary_is_exact(rows):
    disclosure = rows[HEX_DECODED]["secret_input"]
    assert len(secret_to_key_bytes(disclosure)) == 32
    assert len(secret_to_key_bytes(disclosure[:-1])) == 63
    assert len(secret_to_key_bytes(disclosure + "a")) == 65


# ---------------------------------------------------------------------------
# Copy-paste whitespace
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("wrapper", ["{}\n", "  {}", "{}  ", "\n\t{}\r\n"])
def test_whitespace_around_a_disclosure_is_stripped(rows, wrapper):
    """``$(cat secret.txt)`` carries a newline, and a newline is not key material."""
    disclosure = rows[HEX_DECODED]["secret_input"]
    padded = wrapper.format(disclosure)
    assert secret_to_key_bytes(padded) == secret_to_key_bytes(disclosure)
    assert (
        compute_signature(rows[HEX_DECODED]["canonical_request"], padded)
        == (rows[HEX_DECODED]["signature"])
    )


def test_whitespace_inside_a_text_secret_is_key_material(table):
    """Stripping is on the hex path only; a text secret keeps every byte it was given."""
    secret = table["secret_utf8"]
    assert secret_to_key_bytes(secret + "\n") != secret_to_key_bytes(secret)


def test_bytes_are_the_explicit_escape_hatch(rows):
    """A caller who means to key on the text passes bytes."""
    disclosure = rows[HEX_DECODED]["secret_input"]
    assert secret_to_key_bytes(disclosure.encode("utf-8")) == disclosure.encode("utf-8")
    assert len(secret_to_key_bytes(disclosure.encode("utf-8"))) == 64
    assert secret_to_key_bytes(bytearray(b"raw-key")) == b"raw-key"
    assert secret_to_key_bytes(memoryview(b"raw-key")) == b"raw-key"


def test_an_empty_secret_is_still_refused_on_both_paths():
    with pytest.raises(SigningError, match="empty"):
        secret_to_key_bytes("")
    with pytest.raises(SigningError, match="empty"):
        secret_to_key_bytes(b"")


def test_a_non_secret_type_is_still_refused():
    with pytest.raises(SigningError, match="must be str or bytes"):
        secret_to_key_bytes(1234)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The environment boundary — where the disclosure actually arrives
# ---------------------------------------------------------------------------
def test_a_disclosure_from_the_environment_signs_correctly(monkeypatch, rows):
    """A secret resolved from ``PERCEIVO_SIGNING_SECRET`` is hex-decoded."""
    row = rows[HEX_DECODED]
    monkeypatch.setenv("PERCEIVO_KEY_ID", "0f8fad5b-d9cb-469f-a165-70867728950e")
    monkeypatch.setenv("PERCEIVO_SIGNING_SECRET", row["secret_input"])
    credentials = resolve_signing_credentials(audience="perceivo-api-local")
    assert credentials is not None
    assert (
        compute_signature(row["canonical_request"], credentials.signing_secret)
        == (row["signature"])
    )


def test_the_credential_keeps_the_spelling_it_was_given(rows):
    """Normalisation happens at signing time, so the credential holds one copy."""
    from perceivo_client.signing import SigningCredentials

    row = rows[HEX_DECODED]
    credentials = SigningCredentials(
        key_id="0f8fad5b-d9cb-469f-a165-70867728950e",
        signing_secret=row["secret_input"],
        audience="perceivo-api-local",
    )
    assert credentials.signing_secret == row["secret_input"]
    assert isinstance(credentials.signing_secret, str)
