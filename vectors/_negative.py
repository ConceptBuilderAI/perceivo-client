"""The negative rows: correctly signed canonical requests a verifier must reject."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _constants import (
    KEY_ID,
    ORGANIZATION_A,
    ORGANIZATION_B,
    OTHER_KEY_ID,
    SECRET,
)

from perceivo_client.signing import AUDIENCE_LOCAL, compute_signature


def negative_vectors_for(primary: str) -> list[dict]:
    """Return canonical requests with a correct MAC that a verifier must reject.

    Each row declares ``refused_by``:

    * ``arity`` (n01, n02, n06): the field count is wrong.
    * ``prelude_binding`` (n03, n04, n05): rejected on the content of fields 1-3.
    * ``metadata_binding`` (n07): rejected after ``compare_digest`` on field 9.

    Every row records ``field_count`` so a consumer can confirm each row is
    rejected for its stated reason.

    Args:
        primary: The canonical request of vector v01.
    """
    fields = primary.split("\n")

    # Zero-based indices: 0 domain, 1 audience, 2 key_id, 3 METHOD, 4 path,
    # 5 query, 6 body digest, 7 content_type, 8 organization, 9 timestamp,
    # 10 nonce.
    six_field = "\n".join([fields[3], fields[4], fields[5], fields[6], fields[9], fields[10]])
    nine_field = "\n".join(fields[:7] + fields[9:])
    ten_field = "\n".join(fields[:8] + fields[9:])
    wrong_domain = "\n".join(["perceivo-hmac-v2", *fields[1:]])
    wrong_audience = "\n".join([fields[0], "perceivo-api-prod", *fields[2:]])
    wrong_key_id = "\n".join([fields[0], fields[1], OTHER_KEY_ID, *fields[3:]])
    # n07: eleven fields, correct fields 1-3, correct MAC, and a field 9 that
    # differs from the organization header the server received.
    signed_other_organization = "\n".join([*fields[:8], ORGANIZATION_B, *fields[9:]])

    # (id, description, canonical, refused_by, presented_organization)
    cases = [
        (
            "n01-six-field-downgrade",
            "Six fields: METHOD, path, query, body digest, timestamp and nonce of "
            "v01's request, correctly signed. A verifier that accepts it leaves "
            "the domain, audience, key id, Content-Type and organization fields "
            "unchecked. Reject on the field count before comparing digests: "
            "eleven fields, ten separators, no trailing newline.",
            six_field,
            "arity",
            "",
        ),
        (
            "n02-nine-field-downgrade",
            "Nine fields: v01's canonical request without the Content-Type and "
            "organization fields, correctly signed. Reject on the field count.",
            nine_field,
            "arity",
            "",
        ),
        (
            "n03-wrong-domain-separator",
            "Field 1 is 'perceivo-hmac-v2'. The field count is correct, so only "
            "the domain comparison rejects this request. The domain is a constant "
            "and is compared for exact equality, so a signature produced for "
            "another scheme with the same secret cannot be replayed here.",
            wrong_domain,
            "prelude_binding",
            "",
        ),
        (
            "n04-audience-mismatch",
            "Field 2 is 'perceivo-api-prod' where this verifier is configured "
            "for '" + AUDIENCE_LOCAL + "'. The field count is correct. Correctly signed "
            "and rejected: a request signed for one deployment must not verify at "
            "another. The verifier compares field 2 with its own configured "
            "audience, never with the request's Host header.",
            wrong_audience,
            "prelude_binding",
            "",
        ),
        (
            "n05-key-id-mismatch",
            "Field 3 is '" + OTHER_KEY_ID + "' while the bearer header names "
            "'" + KEY_ID + "', whose secret was used. The field count is correct. "
            "Correctly signed and rejected: the verifier compares field 3 with "
            "the id of the key whose secret it used, so a signature cannot be "
            "presented under a different key.",
            wrong_key_id,
            "prelude_binding",
            "",
        ),
        (
            "n06-ten-field-downgrade",
            "Ten fields: v01's canonical request with the organization field "
            "omitted rather than empty, correctly signed. Accepting it leaves "
            "field 9 unbound, so a captured signature could be presented with "
            "another organization. It differs from v01, which signs field 9 as "
            "the empty string: the value is the same, the field count is not, "
            "and only the field count check distinguishes them.",
            ten_field,
            "arity",
            "",
        ),
        (
            "n07-organization-metadata-unbound",
            "Field 9 binding. Eleven fields; fields 1, 2 and 3 are correct; the "
            "MAC is correct. Field 9 names '" + ORGANIZATION_B + "' while the "
            "request carried '" + ORGANIZATION_A + "' (see presented_organization). "
            "A verifier must read field 9 from the signed string after "
            "compare_digest and reject a value that differs from the header it "
            "received (signature_metadata_unbound), as it does for the timestamp "
            "and nonce. The comparison must follow the MAC check: before it, "
            "both values are unauthenticated client input. An implementation "
            "that signs field 9 but never compares it passes every other row and "
            "fails only this one.",
            signed_other_organization,
            "metadata_binding",
            ORGANIZATION_A,
        ),
    ]
    return [
        {
            "id": vector_id,
            "description": description,
            "canonical_request": canonical,
            "signature": compute_signature(canonical, SECRET),
            "verifier_audience": AUDIENCE_LOCAL,
            "verifier_key_id": KEY_ID,
            # The organization header the server received with the signed
            # request. For every row except n07 it agrees with field 9.
            "presented_organization": presented_organization,
            "field_count": len(canonical.split("\n")),
            "refused_by": refused_by,
            # `arity` and `prelude_binding` compare with values the server holds,
            # so they run before the MAC check; `metadata_binding` compares two
            # client-supplied values and runs after it.
            "refused_before_mac": refused_by != "metadata_binding",
            "mac_is_correct": True,
            "must_verify": False,
        }
        for vector_id, description, canonical, refused_by, presented_organization in cases
    ]
