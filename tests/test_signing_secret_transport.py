"""How a secret *spelling* becomes HMAC *key bytes*.

Every other signing test holds the key fixed and varies the request. This module
inverts that: one request, five spellings of a key, and the published
``secret_transport_vectors`` rows as the reference.

The platform issues the signing secret as 64 hex characters, which decode to a
32-byte key. Encoding that text as UTF-8 instead gives a 64-byte key and a wrong
signature on every request. The positive vectors cannot detect that mistake: they
key on ``secret_utf8``, which is not hex-shaped, so a signer that never decodes hex
still reproduces all of them. These tests fail for it.

The negative row matters most. Reproducing the correct signature shows the code is
right; pinning the signature the wrong encoding produces shows the test can tell
the two apart.
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
    # The published disclosure constant must actually be the shape it declares, or
    # every row below is testing something other than what the block describes.
    disclosure = contract["disclosure_secret_hex"]
    assert len(disclosure) == 64
    assert len(bytes.fromhex(disclosure)) == 32
    assert disclosure != table["secret_utf8"]


def test_the_declared_count_matches_the_rows(table):
    assert table["vector_counts"]["secret_transport"] == len(table["secret_transport_vectors"])
    assert table["vector_counts"]["secret_transport"] == 5


def test_secret_utf8_is_not_the_disclosure_shape(table):
    """The reason every positive vector was blind, pinned so it cannot be forgotten.

    If ``secret_utf8`` were ever regenerated into a 64-hex value, every positive
    vector would silently start exercising the hex path and this module would be the
    only thing still testing the UTF-8 one — so the blindness would move rather than
    close.
    """
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
    """Removing the hex decode makes t01 and t03 fail here."""
    row = rows[row_id]
    assert secret_to_key_bytes(row["secret_input"]).hex() == row["hmac_key_hex"]


@pytest.mark.parametrize("row_id", [HEX_DECODED, HEX_UPPERCASE, NON_HEX_UTF8, SIXTY_FOUR_NOT_HEX])
def test_the_client_reproduces_every_positive_transport_signature(rows, row_id):
    row = rows[row_id]
    assert row["must_verify"] is True
    assert compute_signature(row["canonical_request"], row["secret_input"]) == row["signature"]
    assert verify_signature(row["signature"], row["canonical_request"], row["secret_input"])


# ---------------------------------------------------------------------------
# The negative row: the defect, published so it is identifiable
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
    """The published wrong signature must be the one the defect actually produces.

    Without this the negative row could drift into a value nothing produces, and an
    implementer comparing against it would learn nothing. Reproduced here by keying
    on ``bytes`` — the explicit escape hatch — because that is the only way to ask
    for the wrong key now that the ``str`` path is correct.
    """
    wrong = rows[HEX_AS_UTF8_WRONG]
    keyed_as_text = wrong["secret_input"].encode("utf-8")
    assert compute_signature(wrong["canonical_request"], keyed_as_text) == wrong["signature"]
    assert len(keyed_as_text) == 64


# ---------------------------------------------------------------------------
# The two equalities that make the change additive
# ---------------------------------------------------------------------------
def test_the_non_hex_row_equals_the_primary_vector(table, rows):
    """Additivity control: if this fails, every positive vector is invalid."""
    assert rows[NON_HEX_UTF8]["signature"] == find(table, PRIMARY_ID)["signature"]
    assert rows[NON_HEX_UTF8]["signature"] == PRIMARY_SIGNATURE


def test_uppercase_and_lowercase_disclosures_are_one_key(rows):
    lower, upper = rows[HEX_DECODED], rows[HEX_UPPERCASE]
    assert upper["secret_input"] == lower["secret_input"].upper()
    assert upper["secret_input"] != lower["secret_input"]
    assert upper["signature"] == lower["signature"]
    assert secret_to_key_bytes(upper["secret_input"]) == secret_to_key_bytes(lower["secret_input"])


# ---------------------------------------------------------------------------
# The shape gate: alphabet AND length, not either alone
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
# The copy-paste footguns
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
    """The answer to the residual: a caller who means 'key on this text' passes bytes."""
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
    """The usual deployment path: an operator exports the value they were issued.

    ``PERCEIVO_SIGNING_SECRET`` can only carry text, so the disclosure is what lands
    there. If this path did not decode, every credential resolved from the
    environment — which is the documented way to configure signing — would produce a
    401 with no diagnostic.
    """
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
    """Normalisation happens at signing time, so the credential holds one copy.

    Decoding at construction would leave the caller's ``str`` *and* a derived
    ``bytes`` alive at once — two copies of one secret, and the second one is the
    kind that ends up in a heap dump nobody expected.
    """
    from perceivo_client.signing import SigningCredentials

    row = rows[HEX_DECODED]
    credentials = SigningCredentials(
        key_id="0f8fad5b-d9cb-469f-a165-70867728950e",
        signing_secret=row["secret_input"],
        audience="perceivo-api-local",
    )
    assert credentials.signing_secret == row["secret_input"]
    assert isinstance(credentials.signing_secret, str)
