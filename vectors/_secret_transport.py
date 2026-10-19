"""The secret-transport rows: how an issued secret becomes the HMAC key.

Every positive vector keys on ``secret_utf8``, a short ASCII string. The platform
issues secrets as 64 hex characters that must be decoded, so these rows hold the
request fixed and vary the secret's spelling.
``perceivo_client/signing/_secret.py`` implements the same rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perceivo_client.signing import compute_signature

# A second published test secret, in the issued shape: 32 bytes written as 64
# lowercase hex characters. The caller holds that text and the server keys on the
# bytes it decodes to. The value is visibly synthetic so it is not mistaken for
# issued key material.
SECRET_HEX = "0f1e2d3c4b5a69788796a5b4c3d2e1f00123456789abcdeffedcba9876543210"

# The same 32 bytes spelled in uppercase. `bytes.fromhex` is case-insensitive, so
# this produces an identical signature.
SECRET_HEX_UPPER = SECRET_HEX.upper()

# 64 characters, one of which is not hex. An issued secret is recognised by its
# alphabet as well as its length, so this value is keyed on its UTF-8 bytes.
# Derived from the constant above by substituting one character.
SECRET_64_NOT_HEX = "z" + SECRET_HEX[1:]


def build_transport_rows(primary: dict, utf8_secret: str) -> list[dict]:
    """Return rows that specify how a secret's spelling becomes the HMAC key.

    Every row signs v01's request, so a consumer that already reproduces v01 has a
    fixed point, and varies only the secret. Row t02 publishes the signature that
    the incorrect encoding (UTF-8 instead of hex decoding) produces, so an
    implementer whose t01 signature matches it can identify the defect.

    Args:
        primary: Vector v01.
        utf8_secret: The ``secret_utf8`` test secret.

    Raises:
        SystemExit: If the generated rows do not have the expected equalities.
    """
    canonical = primary["canonical_request"]
    key_hex = bytes.fromhex(SECRET_HEX)

    cases: list[tuple[str, str, str, str, bytes, bool, str | None]] = [
        (
            "t01-hex-disclosure-decoded",
            "The issued form. The 64-character hex secret decoded to its 32 bytes, "
            "which are the bytes the server keys on. This is the row every "
            "implementation must reproduce.",
            SECRET_HEX,
            "hex-disclosure",
            key_hex,
            True,
            None,
        ),
        (
            "t02-hex-disclosure-utf8-encoded-WRONG",
            "The incorrect encoding, published so it can be recognised. The same "
            "secret encoded as UTF-8 instead of decoded from hex: a 64-byte key "
            "where the server holds a 32-byte one. Must not verify. If your "
            "signature for t01 equals this value, the secret is being encoded "
            "rather than decoded; the canonical request, timestamp and nonce are "
            "not the cause.",
            SECRET_HEX,
            "hex-disclosure-encoded-as-utf8",
            SECRET_HEX.encode("utf-8"),
            False,
            None,
        ),
        (
            "t03-hex-disclosure-uppercase-decoded",
            "The same 32 bytes written in uppercase hex. Hex decoding is "
            "case-insensitive, so this signature is identical to t01's. An "
            "implementation that rejects the uppercase spelling fails here.",
            SECRET_HEX_UPPER,
            "hex-disclosure",
            key_hex,
            True,
            "t01-hex-disclosure-decoded",
        ),
        (
            "t04-non-hex-secret-utf8-encoded",
            "A secret that is not 64 hex characters. `secret_utf8` is keyed on "
            "its UTF-8 bytes, so this signature is identical to v01's.",
            utf8_secret,
            "utf8-text",
            utf8_secret.encode("utf-8"),
            True,
            "v01-get-empty-body-empty-query",
        ),
        (
            "t05-sixty-four-chars-not-hex",
            "64 characters, one of them outside the hex alphabet. Keyed on its "
            "UTF-8 bytes, because an issued secret is recognised by its alphabet "
            "and its length together. An implementation that decodes on length "
            "alone fails here. A 64-character passphrase made only of hex "
            "characters cannot be told apart from an issued secret and is "
            "decoded; to key on such text, pass bytes.",
            SECRET_64_NOT_HEX,
            "utf8-text",
            SECRET_64_NOT_HEX.encode("utf-8"),
            True,
            None,
        ),
    ]

    rows = [
        {
            "id": vector_id,
            "description": description,
            "secret_input": secret_input,
            "secret_input_kind": kind,
            # The key bytes passed to HMAC, as hex, so an implementer can compare
            # key bytes directly. Every secret in the table is a public test
            # constant.
            "hmac_key_hex": key_bytes.hex(),
            "hmac_key_length_bytes": len(key_bytes),
            "canonical_request": canonical,
            "signature": compute_signature(canonical, key_bytes),
            "must_verify": must_verify,
            "signature_equals_vector": same_as,
        }
        for vector_id, description, secret_input, kind, key_bytes, must_verify, same_as in cases
    ]

    by_id = {row["id"]: row for row in rows}
    # Checked at generation time: if any of these fails, the table is not written.
    if (
        by_id["t03-hex-disclosure-uppercase-decoded"]["signature"]
        != by_id["t01-hex-disclosure-decoded"]["signature"]
    ):
        raise SystemExit("t03 must equal t01: hex decoding is case-insensitive")
    if by_id["t04-non-hex-secret-utf8-encoded"]["signature"] != primary["signature"]:
        raise SystemExit(
            "t04 must equal the primary vector's signature; the non-hex path was CHANGED, "
            "which invalidates every positive vector in the table"
        )
    if (
        by_id["t02-hex-disclosure-utf8-encoded-WRONG"]["signature"]
        == by_id["t01-hex-disclosure-decoded"]["signature"]
    ):
        raise SystemExit("t02 must differ from t01 or the row demonstrates nothing")
    return rows


def secret_transport_block() -> dict:
    """Return the ``secret_transport`` block that describes the rows above."""
    # Nested rather than placed beside `secret_utf8` and `secret_base64`, which
    # are two spellings of one secret: this is a different secret.
    return {
        "note": (
            "How an issued secret becomes the HMAC key. The key is 32 random "
            "bytes. The platform issues it once, at enrolment, as 64 lowercase "
            "hex characters, so the caller holds text and the server holds "
            "bytes: an implementation must decode the issued text from hex, "
            "never encode it. Encoding it as UTF-8 produces a 64-byte key that "
            "does not match the server's, and every request fails with a 401. "
            "secret_utf8 is not in the issued form, so the positive vectors do "
            "not exercise this decoding; secret_transport_vectors does, and "
            "includes the signature the incorrect encoding produces."
        ),
        "disclosure_shape": "64 lowercase hex characters, /^[0-9a-f]{64}$/",
        "disclosure_decodes_to_bytes": 32,
        "disclosure_secret_hex": SECRET_HEX,
        "disclosure_secret_note": (
            "A second published test constant, distinct from secret_utf8, that "
            "protects nothing. It is in the issued form so the table can "
            "exercise hex decoding. Never configure it anywhere."
        ),
        "rule": (
            "A str of exactly 64 characters drawn from [0-9a-fA-F] is an issued "
            "secret and is hex-decoded; any other str is keyed on its own UTF-8 "
            "bytes; a bytes value is the key verbatim. Hex decoding is "
            "case-insensitive. Surrounding whitespace is stripped before the "
            "form is tested, because a secret read from a file or a shell often "
            "carries a trailing newline."
        ),
        "residual": (
            "A 64-character passphrase made only of hex characters cannot be "
            "told apart from an issued secret and is decoded, because the "
            "platform issues secrets only in that form. To key on such text, "
            "pass bytes."
        ),
    }
