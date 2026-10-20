"""Checks the generator runs before it writes the table.

Each check guards a property that the table's own tests could not detect if it
were violated: the table would still be self-consistent while encoding something
false. Running them at generation time means such a table is never written.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def assert_table_invariants(
    vectors: list[dict], negative_vectors: list[dict], unsignable_vectors: list[dict]
) -> None:
    """Refuse to write a table whose rows would pass their own tests while being wrong.

    Raises:
        SystemExit: If any invariant does not hold.
    """
    by_id = {vector["id"]: vector for vector in vectors}

    # (1) Field positions. Check the count and the position of fields 8 to 11
    # together: a field inserted in the wrong place still gives the right count.
    for vector in vectors:
        fields = vector["canonical_request"].split("\n")
        if len(fields) != 11:
            raise SystemExit(f"{vector['id']}: {len(fields)} fields, expected eleven")
        if fields[7] != vector["canonical_content_type"]:
            raise SystemExit(f"{vector['id']}: field 8 is not content_type")
        if fields[8] != vector["canonical_organization"]:
            raise SystemExit(f"{vector['id']}: field 9 is not organization")
        if fields[9] != vector["timestamp"] or fields[10] != vector["nonce"]:
            raise SystemExit(f"{vector['id']}: timestamp/nonce are not fields 10 and 11")

    # (2) The organization is signed. Two requests differing only in the
    # organization must have different signatures, and both must differ from the
    # same request with no header. Most positive rows sign the empty organization,
    # so without this check field 9 could be dropped and they would still pass.
    pair_a = by_id["v35-organization-pair-a"]
    pair_b = by_id["v36-organization-pair-b"]
    absent = by_id["v01-get-empty-body-empty-query"]
    if pair_a["signature"] == pair_b["signature"]:
        raise SystemExit("v35 and v36 must differ: field 9 is not in the signature")
    differing = [
        i
        for i, (x, y) in enumerate(
            # strict=True: two strings with different field counts must not be
            # truncated to the shorter one and reported as differing in field 9.
            zip(
                pair_a["canonical_request"].split("\n"),
                pair_b["canonical_request"].split("\n"),
                strict=True,
            )
        )
        if x != y
    ]
    if differing != [8]:
        raise SystemExit(f"v35/v36 must differ in field 9 ALONE, differ in {differing}")
    if absent["signature"] in (pair_a["signature"], pair_b["signature"]):
        raise SystemExit("an absent organization must not sign as a present one")

    # (3) Each negative row has the field count for its class. A prelude_binding
    # row with the wrong count would be rejected on arity, leaving the domain,
    # audience and key id checks it exists for untested.
    expected_field_counts = {
        "n01-six-field-downgrade": 6,
        "n02-nine-field-downgrade": 9,
        "n03-wrong-domain-separator": 11,
        "n04-audience-mismatch": 11,
        "n05-key-id-mismatch": 11,
        "n06-ten-field-downgrade": 10,
        "n07-organization-metadata-unbound": 11,
    }
    for negative in negative_vectors:
        expected = expected_field_counts.get(negative["id"])
        if expected is None:
            raise SystemExit(f"{negative['id']}: no declared field count; add one")
        if negative["field_count"] != expected:
            raise SystemExit(
                f"{negative['id']}: {negative['field_count']} fields, expected {expected} "
                "-- a row refused on the wrong ground is a passing test over an "
                "untested control"
            )
        if (negative["refused_by"] == "arity") != (expected != 11):
            raise SystemExit(f"{negative['id']}: refused_by disagrees with field_count")

    # (4) n07 can be rejected only after the MAC check. If any of fields 1-3
    # differed it would be rejected earlier and would not test field 9 binding.
    unbound = next(n for n in negative_vectors if n["id"] == "n07-organization-metadata-unbound")
    unbound_fields = unbound["canonical_request"].split("\n")
    primary_fields = absent["canonical_request"].split("\n")
    if unbound_fields[:3] != primary_fields[:3]:
        raise SystemExit("n07's prelude must be CORRECT or it is refused before the mac")
    if unbound_fields[8] == unbound["presented_organization"]:
        raise SystemExit("n07's signed and presented organizations must disagree")

    # (5) The field 8 unsignable rows are exactly u01-u05.
    field_eight = [u for u in unsignable_vectors if u["field_number"] == 8]
    if len(field_eight) != 5 or [u["id"] for u in field_eight] != [
        "u01-content-type-non-ascii-text",
        "u02-content-type-latin1-high-byte",
        "u03-content-type-newline",
        "u04-content-type-tab",
        "u05-content-type-del-control",
    ]:
        raise SystemExit("the field 8 unsignable rows must be exactly u01-u05")
