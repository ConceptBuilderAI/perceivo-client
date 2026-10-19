"""The cases for header values a signer must refuse to sign.

An unsignable row has no ``canonical_request`` and no ``signature``; a consumer
checks it by canonicalising the input and requiring an error.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _constants import ORGANIZATION_A, ORGANIZATION_B

# Field 8 values a signer must refuse: a Content-Type with a byte outside
# printable ASCII. (id, description, content-type)
UNSIGNABLE_CASES: list[tuple[str, str, bytes]] = [
    (
        "u01-content-type-non-ascii-text",
        "A Content-Type whose parameter contains U+00E9, sent as UTF-8 bytes. "
        "Field 8 admits printable ASCII, 0x20-0x7E, only, so the signer must "
        "refuse it. A latin-1 decoder and a UTF-8 decoder read these bytes as "
        "different text ('Ã©' and 'é') and would sign different values; on "
        "printable ASCII the two agree.",
        "text/plain; x=é".encode(),
    ),
    (
        "u02-content-type-latin1-high-byte",
        "A single 0xFF byte, which is not valid UTF-8. A UTF-8 decoder refuses "
        "it before the character check; a latin-1 decoder reaches the "
        "character check and refuses it there. The vector specifies the "
        "outcome, not which check produces it.",
        b"text/plain; x=\xff",
    ),
    (
        "u03-content-type-newline",
        "A newline in Content-Type. 0x0A is outside 0x20-0x7E, so the "
        "character rule also covers the rule that no field may contain a "
        "newline. Rejected, never escaped: escaping would produce a string no "
        "other implementation would reproduce.",
        b"application/json\nX-Evil: 1",
    ),
    (
        "u04-content-type-tab",
        "A horizontal tab (0x09) between parameters. RFC 7230 admits it as "
        "optional whitespace inside a header value; this format does not.",
        b"application/json;\tcharset=utf-8",
    ),
    (
        "u05-content-type-del-control",
        "0x7F (DEL), one past the top of the admitted range. The boundary is "
        "closed at 0x7E, so this pins the upper edge; 0x7E itself ('~') is "
        "signable and appears in the positive controls.",
        b"application/json; x=\x7f",
    ),
]

# Field 9 values a signer must refuse. u06, u07 and u08 are spellings that
# `canonical_key_id` would normalise.
# (id, description, raw-value-or-list-of-values, reason)
UNSIGNABLE_ORGANIZATION_CASES: list[tuple[str, str, object, str]] = [
    (
        "u06-organization-uppercase-uuid",
        "The same UUID as v35's, in uppercase. Field 9 is rejected rather than "
        "converted to lowercase, unlike the key id in v28, which normalises to "
        "the canonical spelling and produces v01's signature. The key id is a "
        "UUID the server has already resolved; field 9 is client text that the "
        "signer, the verifier and the server's authorisation must all read "
        "identically.",
        ORGANIZATION_A.upper(),
        "organization_charset",
    ),
    (
        "u07-organization-braced-uuid",
        "The UUID in braces. Refused for u06's reason: field 9 has one admissible spelling.",
        "{" + ORGANIZATION_A + "}",
        "organization_charset",
    ),
    (
        "u08-organization-unhyphenated-uuid",
        "The 32-character unhyphenated form. Refused for u06's reason. "
        "`uuid.UUID()` accepts this spelling, so an implementation that "
        "validates by parsing rather than by matching the pattern accepts it.",
        ORGANIZATION_A.replace("-", ""),
        "organization_charset",
    ),
    (
        "u09-organization-not-a-uuid",
        "An organization slug rather than a UUID. Field 9 is a UUID or the "
        "empty string; a signer must refuse anything else rather than sign a "
        "request the server will reject.",
        "acme-corporation",
        "organization_charset",
    ),
    (
        "u10-organization-newline",
        "A newline inside the organization value. Rejected, never escaped: a "
        "newline in a field adds a field, which the verifier's field count "
        "check rejects. Escaping would produce a string no other "
        "implementation would reproduce.",
        ORGANIZATION_A + "\n" + ORGANIZATION_B,
        "organization_charset",
    ),
    (
        "u11-organization-duplicate-header",
        "Two Perceivo-Organization headers. Rejected rather than resolved: if "
        "the signer picked one value, the server's verifier and its "
        "authorisation could pick differently. Read the header as a list of "
        "values; a mapping built from the headers collapses duplicates and "
        "hides this case.",
        [ORGANIZATION_A, ORGANIZATION_B],
        "organization_duplicate_header",
    ),
]
