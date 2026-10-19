"""Checks the golden-vector table's ``notes`` against the table itself.

The table's ``notes`` array is normative prose, and it is the first thing an external
implementer reads. This module does not proofread it. It takes the claims that are
mechanically checkable (rosters, counts, memberships), derives each one from the table,
and requires the prose to agree. Everything else is declared free prose, by name, so a
reader can tell which claims carry a guarantee and which do not.

Three properties matter.

**Rosters are checked clause by clause, not as a bag of ids.** A note may legitimately
mention a vector outside the roster it is enumerating -- ``notes[18]`` names v19 in its
collapse clause while v19 is correctly absent from its failure clause. Matching the set
of ids anywhere in the note would accept a roster that names the wrong rows, which is the
defect class this file exists to catch.

**Exhaustiveness is asserted only where the prose claims it.** ``notes[17]`` names two
equivalence classes; a third (v01/v28) also exists. Requiring the named classes to be the
only classes would be a false failure.

**Every note is classified, and every note is pinned.** ``NOTE_CLASSIFICATION`` names
all of them and ``NOTE_DIGESTS`` fixes their contents. Classification alone catches only
a new note: prose appended inside an existing one still matches its anchor. The digest
closes that: any edit to any note fails until its classification is revisited.
"""

from __future__ import annotations

import base64
import hashlib
import re
from collections import defaultdict
from typing import Callable, NamedTuple

import pytest

from perceivo_client.signing import SigningError, canonical_key_id, load_golden_vectors
from tests._notes_digests import NOTE_DIGESTS

# Each row list and the ``vector_counts`` key that declares its size.
ROW_LIST_COUNT_KEY = {
    "vectors": "positive",
    "negative_vectors": "negative",
    "unsignable_vectors": "unsignable",
    "secret_transport_vectors": "secret_transport",
}

# A short vector id: the 'v03'/'n06'/'u11'/'t02' stem, without the descriptive tail.
_ID = re.compile(r"\b([vnut]\d{2})\b")

# An inclusive range as the prose writes it: 'u01-u05', or 'v22-v24'.
_RANGE = re.compile(r"\b([vnut])(\d{2})\s*-\s*(?:[vnut])?(\d{2})\b")

# Numbers as the notes spell them out.
SPELLED_NUMBER = {"ELEVEN": 11, "TEN": 10, "NINE": 9, "SIX": 6, "THREE": 3}

# How many id-groups each multi-group note is written to name. Registered because a scan
# that matches nothing returns an empty list, over which every assertion passes.
COLLAPSE_GROUPS_NAMED = 2
EQUIVALENCE_CLASSES_NAMED = 2


@pytest.fixture(scope="module")
def table() -> dict:
    return load_golden_vectors()


def _short(vector_id: str) -> str:
    return vector_id.split("-", 1)[0]


def _ids_in(text: str) -> set[str]:
    """Every id the span names, with inclusive ranges expanded.

    ``u01-u05`` names five rows, not the two endpoints ``_ID`` would find on its own.
    """
    found = set(_ID.findall(text))
    for prefix, start, end in _RANGE.findall(text):
        for number in range(int(start), int(end) + 1):
            found.add(f"{prefix}{number:02d}")
    return found


def _all_short_ids(table: dict) -> set[str]:
    return {_short(row["id"]) for name in ROW_LIST_COUNT_KEY for row in table[name]}


def _note(table: dict, anchor: str) -> str:
    """The single note containing ``anchor``.

    An anchor that matches zero or several notes is itself a defect: the registry below
    would be pointing at prose that moved, and every claim keyed to it would silently
    stop being checked.
    """
    matches = [note for note in table["notes"] if anchor in note]
    assert len(matches) == 1, f"anchor {anchor!r} matched {len(matches)} notes, expected 1"
    return matches[0]


def _clause(note: str, pattern: str) -> str:
    match = re.search(pattern, note, re.DOTALL)
    assert match, f"clause {pattern!r} did not match the note it is registered against"
    return match.group(1)


def _groups(text: str, pattern: str, expected: int, what: str) -> list[frozenset[str]]:
    """Every id-group ``pattern`` finds, refusing to return the wrong number of them.

    :func:`_note` and :func:`_clause` both fail when their anchor stops matching. A bare
    scan does not: it returns ``[]``, and a loop asserting a property of each element of
    an empty list passes. ``expected`` is what the note is written to name, so a reworded
    note is a red rather than a control that quietly stopped checking anything.
    """
    groups = [frozenset(_ids_in(match)) for match in re.findall(pattern, text)]
    assert len(groups) == expected, (
        f"expected {expected} {what} in this note, found {len(groups)}: "
        f"{[sorted(group) for group in groups]}"
    )
    return groups


# --------------------------------------------------------------------------------------
# Derivations. Each one computes, from the table alone, the set a note claims in prose.
# --------------------------------------------------------------------------------------


def _sorted_query(query: str) -> str:
    return "&".join(sorted(query.split("&")))


def derive_sorting_failures(table: dict) -> set[str]:
    """Positive rows whose canonical query changes when the signer sorts it.

    A row already in sorted order is reproduced correctly by a sorting implementation, so
    it does not fail -- which is exactly why v19 does not belong in that roster.
    """
    return {
        _short(v["id"])
        for v in table["vectors"]
        if v["query_string"] and _sorted_query(v["query_string"]) != v["query_string"]
    }


def derive_sorting_collapses(table: dict) -> set[frozenset[str]]:
    """Groups of distinct rows that a sorting implementation maps to ONE signature."""
    groups: dict[str, set[str]] = defaultdict(set)
    for vector in table["vectors"]:
        if vector["query_string"]:
            groups[_sorted_query(vector["query_string"])].add(_short(vector["id"]))
    return {frozenset(group) for group in groups.values() if len(group) > 1}


def derive_nonempty_organization(table: dict) -> set[str]:
    return {_short(v["id"]) for v in table["vectors"] if v["canonical_organization"]}


def derive_verbatim_path_failures(table: dict) -> set[str]:
    """Rows a signer fails if it emits ``raw_path`` instead of the normalised path."""
    return {_short(v["id"]) for v in table["vectors"] if v["raw_path"] != v["canonical_path"]}


def _unsignable_for_field(table: dict, field_number: int) -> set[str]:
    return {
        _short(u["id"])
        for u in table["unsignable_vectors"]
        if u.get("field_number") == field_number
    }


def derive_key_id_normaliser_folds(table: dict) -> set[str]:
    """Field-9 unsignable rows a signer that reused its ``key_id`` normaliser would accept.

    ``notes[21]`` claims such an implementation "passes v28 and fails u06, u07 and u08".
    That is a claim about which rows the real :func:`canonical_key_id` folds to a valid
    spelling instead of refusing -- so run it. The rows it does NOT fold are safe by a
    different mechanism (u09/u10 raise; u11 carries two header values, so no scalar
    normaliser applies at all) and belong outside the roster.
    """
    folds = set()
    for row in table["unsignable_vectors"]:
        if row.get("field_number") != 9:
            continue
        values = [base64.b64decode(v).decode("utf-8") for v in row["organization_values_base64"]]
        if len(values) != 1:
            continue
        try:
            canonical_key_id(values[0])
        except SigningError:
            continue
        folds.add(_short(row["id"]))
    return folds


class RosterClaim(NamedTuple):
    """A note clause that enumerates a set the table can compute for itself."""

    anchor: str
    clause: str
    derive: Callable[[dict], set[str]]
    what: str


ROSTER_CLAIMS = [
    RosterClaim(
        anchor="canonical_query is field 6",
        clause=r"implementation that sorts fails (.+?),? and collapses",
        derive=derive_sorting_failures,
        what="positive rows a sorting signer fails",
    ),
    RosterClaim(
        anchor="v35 and v36 are the organization pair",
        clause=r"sign a non-empty\s+organization\s*[^\w]{1,3}\s*(.+?);",
        derive=derive_nonempty_organization,
        what="positive rows signing a non-empty organization",
    ),
    RosterClaim(
        anchor="canonical_path is field 5",
        clause=r"emits raw_path verbatim\s+fails (.+?);",
        derive=derive_verbatim_path_failures,
        what="rows a raw_path-verbatim signer fails",
    ),
    RosterClaim(
        anchor="The five unsignable rows",
        clause=r"unsignable rows (.+?) carry",
        derive=lambda table: _unsignable_for_field(table, 8),
        what="unsignable rows carrying field_number 8",
    ),
    RosterClaim(
        anchor="are the field 9 unsignable rows",
        clause=r"^(.+?) are the field 9 unsignable rows",
        derive=lambda table: _unsignable_for_field(table, 9),
        what="unsignable rows carrying field_number 9",
    ),
    RosterClaim(
        anchor="are the field 9 unsignable rows",
        clause=r"passes v28 and fails (.+?)\.",
        derive=derive_key_id_normaliser_folds,
        what="field 9 rows a key_id normaliser folds instead of refusing",
    ),
]


@pytest.mark.parametrize("claim", ROSTER_CLAIMS, ids=lambda c: c.what.replace(" ", "-"))
def test_a_roster_note_names_exactly_the_rows_the_table_derives(claim: RosterClaim, table):
    note = _note(table, claim.anchor)
    named = _ids_in(_clause(note, claim.clause))
    derived = claim.derive(table)
    assert named == derived, (
        f"the note enumerating {claim.what} has drifted from the table.\n"
        f"  names but should not: {sorted(named - derived)}\n"
        f"  omits but should name: {sorted(derived - named)}"
    )


def test_the_collapse_pairs_named_are_exactly_the_groups_that_collapse(table):
    """The other half of ``notes[18]``: which rows a sorting signer merges.

    Checked separately from the failure roster because a row can collapse without
    failing -- v19 is reproduced correctly and still absorbs v20.
    """
    note = _note(table, "canonical_query is field 6")
    clause = _clause(note, r"collapses (.+?)$")
    pattern = r"((?:[vnut]\d{2}\s*/\s*)+[vnut]\d{2})"
    named = set(_groups(clause, pattern, COLLAPSE_GROUPS_NAMED, "collapse groups"))
    derived = derive_sorting_collapses(table)
    assert named == derived, (
        "the collapse clause has drifted from the table.\n"
        f"  names but should not: {sorted(sorted(g) for g in named - derived)}\n"
        f"  omits but should name: {sorted(sorted(g) for g in derived - named)}"
    )


def test_the_named_equivalence_classes_really_share_one_signature(table):
    """``notes[17]``: membership, NOT exhaustiveness -- see the module docstring."""
    by_signature: dict[str, set[str]] = defaultdict(set)
    for vector in table["vectors"]:
        by_signature[vector["signature"]].add(_short(vector["id"]))
    real = {frozenset(members) for members in by_signature.values() if len(members) > 1}
    note = _note(table, "The path transform is not injective")
    pattern = r"(v\d{2}, v\d{2} and v\d{2})"
    for group in _groups(note, pattern, EQUIVALENCE_CLASSES_NAMED, "equivalence classes"):
        assert group in real, (
            f"{sorted(group)} is named as sharing one signature, but the table disagrees"
        )


def test_the_organization_split_counts_what_the_table_holds(table):
    """``notes[19]``: not just which rows sign an organization, but how many, and how
    many do not. The arithmetic is the load-bearing half -- "the other 33 would still
    pass" is the sentence telling an implementer how thin the field-9 coverage is."""
    note = _note(table, "v35 and v36 are the organization pair")
    nonempty = derive_nonempty_organization(table)
    claimed = SPELLED_NUMBER[_clause(note, r"Exactly (\w+) positive\s+rows sign").upper()]
    assert claimed == len(nonempty), f"note claims {claimed}, table has {sorted(nonempty)}"
    residual = int(_clause(note, r"the other (\d+) sign"))
    assert residual == len(table["vectors"]) - len(nonempty), (
        f"note claims {residual} rows sign the empty string; the table has "
        f"{len(table['vectors'])} positives of which {len(nonempty)} are non-empty"
    )


def test_the_negative_taxonomy_note_matches_what_each_row_declares(table):
    """``notes[4]``: the three-way split, and the two per-row facts it hangs on it.

    The note's own warning is that conflating the parts produces a green suite over a
    broken change -- so the rosters are derived from ``refused_by``, and the claims it
    makes about each part ("the FULL ELEVEN FIELDS", "only AFTER the mac") are read off
    ``field_count`` and ``refused_before_mac`` rather than trusted.
    """
    note = _note(table, "The negative vectors fall into three classes")
    rows = {_short(row["id"]): row for row in table["negative_vectors"]}
    named = {}
    for label, pattern in (
        ("arity", r"'arity' rows \(([^)]+)\)"),
        ("prelude_binding", r"'prelude_binding' rows \(([^)]+)\)"),
        ("metadata_binding", r"'metadata_binding' row \(([^)]+)\)"),
    ):
        named[label] = _ids_in(_clause(note, pattern))
        derived = {rid for rid, row in rows.items() if row["refused_by"] == label}
        assert named[label] == derived, (
            f"the {label!r} roster has drifted: note names {sorted(named[label])}, "
            f"the rows declare {sorted(derived)}"
        )
    for rid in named["prelude_binding"] | named["metadata_binding"]:
        assert rows[rid]["field_count"] == table["field_count"], (
            f"{rid} is not an arity refusal, so it must carry all "
            f"{table['field_count']} fields; it carries {rows[rid]['field_count']}"
        )
    assert all(rows[rid]["refused_before_mac"] for rid in named["arity"])
    assert not any(rows[rid]["refused_before_mac"] for rid in named["metadata_binding"])


def test_the_field_and_separator_counts_in_the_first_note_match_the_canonical_form(table):
    """``notes[0]`` states the field and separator counts in words; they must match the
    canonical form and the declared ``field_count``."""
    separator = chr(92) + "n"
    fields = table["canonical_form"].count(separator) + 1
    note = _note(table, "fields,")
    claimed_fields, claimed_separators = re.match(r"^(\w+) fields, (\w+) ", note).groups()
    assert SPELLED_NUMBER[claimed_fields.upper()] == fields == table["field_count"], (
        f"note claims {claimed_fields} fields; canonical_form has {fields}; "
        f"table declares {table['field_count']}"
    )
    assert SPELLED_NUMBER[claimed_separators.upper()] == fields - 1, (
        f"note claims {claimed_separators} separators for {fields} fields"
    )


def test_every_positive_vector_is_ascii_as_the_note_claims(table):
    """``notes[14]`` asserts a universal over the table."""
    not_ascii = [v["id"] for v in table["vectors"] if not v["canonical_request"].isascii()]
    assert not not_ascii, (
        f"the note claims every positive vector is ASCII; these are not: {not_ascii}"
    )


def test_the_permutation_pair_really_has_two_different_signatures(table):
    """``notes[22]``. If these ever matched, the note would be advertising a property the
    table had stopped having, and the pair would prove nothing."""
    pair = {_short(v["id"]): v for v in table["vectors"] if _short(v["id"]) in {"v19", "v20"}}
    assert set(pair) == {"v19", "v20"}, sorted(pair)
    assert pair["v19"]["signature"] != pair["v20"]["signature"]


# --------------------------------------------------------------------------------------
# Structural claims the package docstring makes about the table's own shape.
# --------------------------------------------------------------------------------------


def test_vector_counts_has_exactly_one_key_per_row_list(table):
    """``signing/__init__.py`` says ``vector_counts`` holds 'a key per list'. Nothing
    checked the converse: a fifth row list, or a stale key, would both read as fine."""
    assert set(table["vector_counts"]) == set(ROW_LIST_COUNT_KEY.values())


def test_each_declared_count_equals_the_length_of_the_list_it_describes(table):
    for row_list, count_key in ROW_LIST_COUNT_KEY.items():
        assert len(table[row_list]) == table["vector_counts"][count_key], row_list


def test_every_vector_id_named_in_any_note_exists_in_the_table(table):
    """Prose must not name a row that the table does not carry, or no longer carries
    under that id."""
    real = _all_short_ids(table)
    dangling = {
        (index, named)
        for index, note in enumerate(table["notes"])
        for named in _ids_in(note)
        if named not in real
    }
    assert not dangling, f"notes name ids the table does not carry: {sorted(dangling)}"


# --------------------------------------------------------------------------------------
# The labelling gate. Anything not checked above is declared free prose, by name.
# --------------------------------------------------------------------------------------

CHECKED = "checked against the table"

NOTE_CLASSIFICATION = [
    ("Eleven fields, ten", CHECKED),
    ("Fields 1-3 and 9 must be bound", "free prose: a binding requirement on the verifier"),
    ("Field 9 must be bound even though", "free prose: design rationale"),
    ("The negative_vectors list contains correctly signed", "free prose: describes intent"),
    ("The negative vectors fall into three classes", CHECKED),
    ("The audience is a deployment label", "free prose: deployment guidance"),
    ("key_id is the API key id", "free prose: rule statement"),
    ("content_type is the Content-Type request header verbatim", "free prose: rule statement"),
    ("Sign after the body and headers are final", "free prose: sequencing advice"),
    ("No field may contain", "free prose: rule statement"),
    ("Field 8 admits printable ASCII", "free prose: rule statement"),
    ("The unsignable_vectors list is a third kind", "free prose: taxonomy"),
    ("body_base64 null means no body", "free prose: encoding convention"),
    ("The HMAC key is the secret's raw bytes", "free prose: rule statement"),
    ("The canonical request is UTF-8 encoded before HMAC", CHECKED),
    ("The signature covers no authority", "free prose: rule statement"),
    ("canonical_path is field 5", CHECKED),
    ("The path transform is not injective", CHECKED),
    ("canonical_query is field 6", CHECKED),
    ("v35 and v36 are the organization pair", CHECKED),
    ("The five unsignable rows", CHECKED),
    ("are the field 9 unsignable rows", CHECKED),
    ("v19 and v20 are a permutation pair", CHECKED),
    ("Body-size-cap vectors", "free prose: says what is deliberately absent"),
]


def test_every_note_is_classified(table):
    """New prose must be classified before it can ship.

    A reader must be able to tell which claims carry a guarantee. An unclassified note
    fails rather than passing silently, so the gate cannot be outrun by adding prose.
    """
    unclassified = [
        index
        for index, note in enumerate(table["notes"])
        if not any(anchor in note for anchor, _ in NOTE_CLASSIFICATION)
    ]
    assert not unclassified, (
        f"notes {unclassified} are not classified in NOTE_CLASSIFICATION. Add each one as "
        f"either {CHECKED!r} with a derivation above, or 'free prose: <why it cannot drift>'."
    )


@pytest.mark.parametrize(
    "anchor", [anchor for anchor, _ in NOTE_CLASSIFICATION], ids=lambda a: a[:32]
)
def test_each_classification_anchor_matches_exactly_one_note(anchor: str, table):
    """A stale anchor silently disarms whatever it was keyed to."""
    assert sum(anchor in note for note in table["notes"]) == 1


def test_no_note_changed_without_its_classification_being_revisited(table):
    """The other half of the labelling gate: it covers edits, not just additions.

    An anchor keeps matching while the prose around it changes, so classification alone
    would let an in-place edit through.
    """
    actual = [hashlib.sha256(note.encode("utf-8")).hexdigest()[:8] for note in table["notes"]]
    # Padded rather than zipped so an unpinned note reports as None instead of vanishing.
    pinned = list(NOTE_DIGESTS) + [None] * len(actual)
    drifted = [(i, pinned[i], found) for i, found in enumerate(actual) if pinned[i] != found]
    detail = (
        f"{len(actual)} notes against {len(NOTE_DIGESTS)} pinned; changed (index, pinned,"
        f" found): {drifted}. Re-read each changed note, confirm its NOTE_CLASSIFICATION"
        f" entry still describes it, then repin."
    )
    assert len(actual) == len(NOTE_DIGESTS), detail
    assert not drifted, detail


def test_the_classification_covers_every_note_exactly_once(table):
    """Guards the other direction from :func:`test_every_note_is_classified`: a registry
    that grew entries for notes that no longer exist would still report full coverage."""
    assert len(NOTE_CLASSIFICATION) == len(table["notes"])
