"""Golden vectors: the cross-implementation contract for HMAC request signing.

``perceivo_client/signing/vectors/hmac_v1_vectors.json`` is the one table that every
implementation of the signing scheme checks itself against, because two copies of a
table cannot check each other.

The table ships as package data and is reachable through
``perceivo_client.signing.load_golden_vectors``. ``test_signing_packaging.py``
proves the shipped artifact carries it, from a wheel installed into a clean virtual
environment. This module is the other half: it checks that the shipped
implementation reproduces the table.

The primary vector's canonical string and signature are additionally pinned as
**literals** in ``_signing_vectors_support.py``. That is deliberate: a bug that
reached both the generator and the implementation would leave the table
self-consistent and still wrong, so the literals are the independent anchor. They
were cross-checked outside Python with::

    printf 'perceivo-hmac-v1\nperceivo-api-local\n0f8fad5b-d9cb-469f-a165-708677\
    28950e\nGET\n/v1/orchestrations\n\ne3b0c44298fc1c149afbf4c8996fb924\
    27ae41e4649b934ca495991b7852b855\n\n1767225600\nsT8kQ2vX7wLpR4nB1mZ6yH0j' \
      | openssl dgst -sha256 -hmac 'perceivo-test-signing-secret-v1'

The table describes the eleven-field canonical request: eleven fields, ten
separators.

This module covers the **table**: the primary vector against its literals, every
vector reproduced end to end, the negative vectors that must be refused, and the
table's shape. The individual canonicalization rules each vector was constructed
to pin (the base path transform, the verbatim query rule, and the two
anti-vacuity mutant controls) live in ``test_signing_vector_cases.py``. Both
modules share one parse of the table and one set of literals via
``_signing_vectors_support.py``.
"""

from __future__ import annotations

import base64
import hmac
import re

import pytest

from perceivo_client.signing import (
    SigningError,
    build_canonical_request,
    canonical_content_type,
    compute_signature,
    split_target,
    verify_signature,
    verify_signed_request,
)
from tests._signing_vectors_support import (
    PRIMARY_AUDIENCE,
    PRIMARY_BODY,
    PRIMARY_CANONICAL,
    PRIMARY_CONTENT_TYPE,
    PRIMARY_ID,
    PRIMARY_KEY_ID,
    PRIMARY_METHOD,
    PRIMARY_NONCE,
    PRIMARY_ORGANIZATION,
    PRIMARY_SECRET,
    PRIMARY_SIGNATURE,
    PRIMARY_TARGET,
    PRIMARY_TIMESTAMP,
    canonical_for,
    find,
    load_table,
)


@pytest.fixture(scope="module")
def table() -> dict:
    return load_table()


# ---------------------------------------------------------------------------
# The primary vector, against hardcoded literals
# ---------------------------------------------------------------------------
def test_primary_vector_canonical_request_matches_the_pinned_literal():
    canonical = build_canonical_request(
        audience=PRIMARY_AUDIENCE,
        key_id=PRIMARY_KEY_ID,
        method=PRIMARY_METHOD,
        raw_path=PRIMARY_TARGET,
        query_string="",
        body=PRIMARY_BODY,
        content_type=PRIMARY_CONTENT_TYPE,
        organization=PRIMARY_ORGANIZATION,
        timestamp=PRIMARY_TIMESTAMP,
        nonce=PRIMARY_NONCE,
    )
    assert hmac.compare_digest(canonical, PRIMARY_CANONICAL)


def test_primary_vector_signature_matches_the_pinned_literal():
    assert hmac.compare_digest(
        compute_signature(PRIMARY_CANONICAL, PRIMARY_SECRET), PRIMARY_SIGNATURE
    )


def test_primary_vector_verifies():
    assert verify_signature(PRIMARY_SIGNATURE, PRIMARY_CANONICAL, PRIMARY_SECRET) is True


def test_published_table_agrees_with_the_pinned_literals(table):
    vector = find(table, PRIMARY_ID)
    assert hmac.compare_digest(table["secret_utf8"], PRIMARY_SECRET)
    assert hmac.compare_digest(vector["canonical_request"], PRIMARY_CANONICAL)
    assert hmac.compare_digest(vector["signature"], PRIMARY_SIGNATURE)


# ---------------------------------------------------------------------------
# Every vector in the table
# ---------------------------------------------------------------------------
def test_every_vector_canonical_request_is_reproduced(table):
    for vector in table["vectors"]:
        assert hmac.compare_digest(canonical_for(vector), vector["canonical_request"]), vector["id"]


def test_every_vector_signature_is_reproduced(table):
    secret = table["secret_utf8"]
    for vector in table["vectors"]:
        signature = compute_signature(vector["canonical_request"], secret)
        assert hmac.compare_digest(signature, vector["signature"]), vector["id"]


def test_every_vector_verifies_and_no_other_vector_does(table):
    secret = table["secret_utf8"]
    vectors = table["vectors"]
    for vector in vectors:
        assert verify_signature(vector["signature"], vector["canonical_request"], secret)
    # Cross-check every ordered pair, not a ring: a signature from one vector may
    # validate another **only** when the two are members of the same path
    # equivalence class, and must fail for every other pair. This is what proves
    # the vectors are distinguishing cases rather than accidentally identical
    # strings — and, since the permitted collisions are enumerated below rather
    # than merely tolerated, that the collisions are the designed ones.
    for vector in vectors:
        for other in vectors:
            if other["id"] == vector["id"]:
                continue
            same_class = _class_of(other["id"]) == _class_of(vector["id"])
            validates = verify_signature(other["signature"], vector["canonical_request"], secret)
            assert validates is same_class, (vector["id"], other["id"])


# The path transform is deliberately not injective: distinct request targets that
# the API normalises to one path are one signed request. These are
# the only collisions the table is allowed to contain, and each is named here so a
# new collision cannot appear by accident.
CANONICAL_PATH_EQUIVALENCE_CLASSES = [
    # `%7e`, `%7E` and a literal `~` are one path: step 1 decodes both hex cases.
    {
        "v22-unreserved-escape-lowercase-hex",
        "v23-unreserved-escape-uppercase-hex",
        "v24-literal-unreserved-character",
    },
    # `..`, `.` and the percent-encoded `%2E%2E` all reduce to the same path:
    # step 1 decodes `%2E` to `.`, then step 2 removes the dot segments.
    {
        "v25-dot-segment-removed",
        "v26-single-dot-segment-removed",
        "v27-encoded-dot-segment-decode-then-remove",
    },
]


# The key-id normalisation class is a collision of a different kind: the requests
# are identical and only the supplied spelling of the uuid differs. v28 hands the
# signer an uppercase uuid and must land on v01's canonical string byte for byte.
# It is listed separately because its members are distinguished by `key_id_input`
# rather than by `raw_path`.
KEY_ID_NORMALISATION_CLASSES = [
    {"v01-get-empty-body-empty-query", "v28-key-id-mixed-case-normalised"},
]

EQUIVALENCE_CLASSES = CANONICAL_PATH_EQUIVALENCE_CLASSES + KEY_ID_NORMALISATION_CLASSES


def _class_of(vector_id: str) -> frozenset[str]:
    for members in EQUIVALENCE_CLASSES:
        if vector_id in members:
            return frozenset(members)
    return frozenset({vector_id})


def test_canonical_requests_collide_exactly_on_the_declared_equivalence_classes(table):
    """Replaces a plain "all distinct" check, which the path transform makes false by design.

    Forbidding all collisions would fail the moment the BASE transform lands;
    tolerating them silently would let a real collision hide. So the exact
    partition is pinned: every declared class must actually collide (in the
    canonical request *and* the signature), and nothing outside a class may.
    """
    by_canonical: dict[str, set[str]] = {}
    for vector in table["vectors"]:
        by_canonical.setdefault(vector["canonical_request"], set()).add(vector["id"])

    observed = {frozenset(ids) for ids in by_canonical.values() if len(ids) > 1}
    assert observed == {frozenset(members) for members in EQUIVALENCE_CLASSES}

    for members in CANONICAL_PATH_EQUIVALENCE_CLASSES:
        signatures = {find(table, vector_id)["signature"] for vector_id in members}
        canonical_paths = {find(table, vector_id)["canonical_path"] for vector_id in members}
        raw_paths = {find(table, vector_id)["raw_path"] for vector_id in members}
        assert len(signatures) == 1, members  # one signed request...
        assert len(canonical_paths) == 1, members
        assert len(raw_paths) == len(members), members  # ...from distinct targets

    for members in KEY_ID_NORMALISATION_CLASSES:
        signatures = {find(table, vector_id)["signature"] for vector_id in members}
        key_ids = {find(table, vector_id)["key_id"] for vector_id in members}
        supplied = {find(table, vector_id)["key_id_input"] for vector_id in members}
        assert len(signatures) == 1, members  # one signed request...
        assert len(key_ids) == 1, members  # ...one normalised key id...
        assert len(supplied) == len(members), members  # ...from distinct spellings


def test_vector_ids_are_unique(table):
    ids = [v["id"] for v in table["vectors"]]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# Table shape — what a server implementer relies on being present
# ---------------------------------------------------------------------------
def test_table_declares_at_least_twelve_vectors(table):
    assert len(table["vectors"]) >= 12


def test_table_declares_version_and_algorithm(table):
    assert table["signature_version"] == "v1"
    assert table["algorithm"] == "HMAC-SHA256"
    assert table["schema"] == "perceivo.hmac-request-signing.golden-vectors/1"


def test_table_declares_the_server_parser_contract(table):
    # A vector is only meaningful relative to a named parser.
    contract = table["server_parser_contract"]
    assert contract["http_parser"] == "httptools"
    assert contract["uvicorn"] == "0.35.0"


def test_table_secret_base64_decodes_to_the_utf8_secret(table):
    assert base64.b64decode(table["secret_base64"]).decode("utf-8") == table["secret_utf8"]


def test_every_vector_has_the_full_field_set(table):
    required = {
        "id",
        "description",
        "audience",
        "key_id",
        "key_id_input",
        "method",
        "target",
        "raw_path",
        "canonical_path",
        "query_string",
        "body_base64",
        "content_type",
        "canonical_content_type",
        "timestamp",
        "nonce",
        "canonical_request",
        "signature",
    }
    for vector in table["vectors"]:
        assert required <= set(vector), vector["id"]
        assert vector["description"].strip(), vector["id"]


def test_every_vector_signature_is_v1_plus_64_lowercase_hex(table):
    for vector in table["vectors"]:
        signature = vector["signature"]
        assert signature.startswith("v1="), vector["id"]
        hexpart = signature[3:]
        assert (len(hexpart), hexpart) == (64, hexpart.lower()), vector["id"]
        int(hexpart, 16)


def test_every_vector_carries_the_tables_audience_and_key_id(table):
    for vector in table["vectors"]:
        assert vector["audience"] == table["audience"], vector["id"]
        assert vector["key_id"] == table["key_id"], vector["id"]
        fields = vector["canonical_request"].split("\n")
        assert fields[0] == "perceivo-hmac-v1", vector["id"]
        assert fields[1] == vector["audience"], vector["id"]
        assert fields[2] == vector["key_id"], vector["id"]
        assert fields[7] == vector["canonical_content_type"], vector["id"]
        assert fields[8] == vector["canonical_organization"], vector["id"]
        assert fields[9] == vector["timestamp"], vector["id"]
        assert fields[10] == vector["nonce"], vector["id"]


def test_an_absent_content_type_signs_as_the_empty_string(table):
    for vector_id in ("v01-get-empty-body-empty-query", "v29-absent-content-type-with-a-body"):
        vector = find(table, vector_id)
        assert vector["content_type"] is None, vector_id
        assert vector["canonical_content_type"] == "", vector_id
        assert vector["canonical_request"].split("\n")[7] == "", vector_id


def test_raw_path_and_query_string_agree_with_the_target(table):
    for vector in table["vectors"]:
        assert split_target(vector["target"]) == (
            vector["raw_path"],
            vector["query_string"],
        ), vector["id"]


# ---------------------------------------------------------------------------
# The negative vectors — correctly signed strings that must still be refused
# ---------------------------------------------------------------------------
# Every one of them carries a valid MAC over its own canonical string, so a
# verifier that only checks the MAC accepts all of them. They fail only against a verifier that binds.
def test_every_negative_vector_has_a_correct_mac(table):
    """The premise. If these macs were wrong the next test would pass vacuously."""
    secret = table["secret_utf8"]
    for vector in table["negative_vectors"]:
        assert vector["mac_is_correct"] is True, vector["id"]
        assert verify_signature(vector["signature"], vector["canonical_request"], secret), vector[
            "id"
        ]


def test_the_bound_verifier_still_accepts_every_positive_vector(table):
    """The other half: binding must not reject what it is supposed to allow."""
    secret = table["secret_utf8"]
    for vector in table["vectors"]:
        assert verify_signed_request(
            signature=vector["signature"],
            canonical_request=vector["canonical_request"],
            secret=secret,
            audience=vector["audience"],
            # The supplied spelling, so v28 exercises the verifier's own
            # normalisation rather than being handed a pre-normalised value.
            key_id=vector["key_id_input"],
        ), vector["id"]


# ---------------------------------------------------------------------------
# The unsignable vectors — inputs that must have no signature at all
# ---------------------------------------------------------------------------
# A third kind of vector. A positive vector says "sign this and you get exactly
# that"; a negative vector says "here is a correct MAC over a wrongly bound string,
# refuse it" (every one carries `mac_is_correct: True`). Neither can say "there is
# no signature for this input, and a signer that produces one is broken."
#
# The API refuses every Content-Type byte outside ASCII printable 0x20-0x7E before
# it verifies anything. A client that signed such a request would leave the caller
# with an opaque `invalid_signature` 401 and nothing local to diagnose. The positive
# vectors cannot show this, because every one of them is pure ASCII.


def test_the_table_ships_the_unsignable_vectors(table):
    assert {v["id"] for v in table["unsignable_vectors"]} == {
        # field 8: the charset rows
        "u01-content-type-non-ascii-text",
        "u02-content-type-latin1-high-byte",
        "u03-content-type-newline",
        "u04-content-type-tab",
        "u05-content-type-del-control",
        # field 9: the organization rows
        "u06-organization-uppercase-uuid",
        "u07-organization-braced-uuid",
        "u08-organization-unhyphenated-uuid",
        "u09-organization-not-a-uuid",
        "u10-organization-newline",
        "u11-organization-duplicate-header",
    }


def test_every_unsignable_vector_carries_no_signature(table):
    """The defining property of the kind. Publishing a signature for an input the
    signer must refuse would be a contradiction another implementation would try to
    reproduce."""
    for vector in table["unsignable_vectors"]:
        assert vector["signable"] is False, vector["id"]
        assert vector["must_sign"] is False, vector["id"]
        assert "canonical_request" not in vector, vector["id"]
        assert "signature" not in vector, vector["id"]
        assert vector["field_number"] in (8, 9), vector["id"]


def test_every_unsignable_vector_is_actually_refused_by_the_signer(table):
    """The assertion a consuming implementation runs, against the shipped table
    rather than the generator's in-memory list."""
    for vector in table["unsignable_vectors"]:
        if vector["field_number"] != 8:
            continue
        raw = base64.b64decode(vector["content_type_base64"])
        with pytest.raises(SigningError):
            canonical_content_type(raw)


def test_the_unsignable_inputs_are_genuinely_outside_the_accepted_set(table):
    """Guard the guard. If a vector's bytes were accidentally all-printable-ASCII the
    test above would be asserting the signer rejects something legal, and the day the
    guard was correct that test would fail. Pin the premise separately."""
    for vector in table["unsignable_vectors"]:
        if vector["field_number"] != 8:
            continue
        raw = base64.b64decode(vector["content_type_base64"])
        assert any(byte < 0x20 or byte > 0x7E for byte in raw), vector["id"]


# ---------------------------------------------------------------------------
# The counts are declared by the table, never by prose
# ---------------------------------------------------------------------------
# A count written into prose or into a test goes stale on the next addition, and a
# stale lower bound lets vectors go missing unnoticed. So every count is read from
# the table.


def test_the_declared_counts_match_the_lists_they_describe(table):
    declared = table["vector_counts"]
    assert len(table["vectors"]) == declared["positive"]
    assert len(table["negative_vectors"]) == declared["negative"]
    assert len(table["unsignable_vectors"]) == declared["unsignable"]
    assert len(table["secret_transport_vectors"]) == declared["secret_transport"]
    # And none of the four is empty, or the equalities above hold vacuously.
    assert all(count > 0 for count in declared.values()), declared


# The guard binds the shape, not one phrasing. A pattern such as
#
#     r"\b(\d+)\s+(?:published\s+|golden\s+)?vectors\b"
#
# misses "33 positive vectors", a count written after the noun, a count attached to
# "table" rather than "vectors", and a hyphenated "golden-vector" compound. A guard a
# writer can escape by choosing a different adjective measures adjectives.
#
# So: a number, in any of the spellings prose uses for one, within a few words of any
# of the nouns this package calls the table's rows, in either order.
#
# Over-matching is the safe direction and is chosen deliberately. A false positive
# costs one prose edit and there is always an escape that is also better writing:
# state the count as `len(table["vectors"])` in code, or do not state it. A false
# negative ships an artefact whose prose contradicts its own table with every control
# passing, which is the failure this exists to prevent.
#: A number as prose writes one. Spelled-out forms below thirteen are deliberately
#: not included: "vector_counts holds one key per list" is about the schema's
#: shape, and house style spells small numbers out, so admitting them would fire on
#: ordinary writing rather than on a count.
_NUMBER = r"""
    (?<!\d-)                       # not the tail of a digit run: the
    \b(?:                          # 8-4-4-4-12 uuid shape is not a count
        \d+
      | (?:thir|four|fif|six|seven|eigh|nine)teen
      | (?:twen|thir|for|fif|six|seven|eigh|nine)ty
        (?:[-\s](?:one|two|three|four|five|six|seven|eight|nine))?
    )\b
    (?!-\d)                        # nor its head
"""
#: Every noun this package uses for the table and its rows, including the
#: ``<kind>_vectors`` list names and the hyphenated "golden-vector" compound.
_ROW_NOUN = r"""\b(?:(?:\w+_)?vectors?|vector_counts|table)\b"""
#: A few intervening words, so any adjective at all is covered, but not so many that
#: the match crosses into an unrelated clause.
_GAP = r"""(?:[\s,:;-]+[A-Za-z][\w'-]*){0,4}?[\s,:;-]+"""

_HARDCODED_COUNT = re.compile(
    rf"""
      (?: {_NUMBER} ) {_GAP} (?: {_ROW_NOUN} )    # "33 positive vectors"
    | (?: {_ROW_NOUN} ) {_GAP} (?: {_NUMBER} )    # "the table shipped 33"
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _hardcoded_counts(text: str) -> list[str]:
    """Every "a count, stated in prose" match in ``text``, whitespace-flattened."""
    return [match.group(0) for match in _HARDCODED_COUNT.finditer(" ".join(text.split()))]


# The positive control. Each entry is a way a writer would naturally state the
# count. The first three are the only ones a naive pattern catches.
COUNT_REWORDINGS = [
    pytest.param("33 vectors", id="bare"),
    pytest.param("33 published vectors", id="published"),
    pytest.param("33 golden vectors", id="golden"),
    pytest.param("33 positive vectors", id="positive-the-new-schemas-own-word"),
    pytest.param("33 negative vectors", id="negative"),
    pytest.param("33 unsignable vectors", id="unsignable"),
    pytest.param("33 positive golden vectors", id="two-adjectives"),
    pytest.param("all 33 of the published vectors", id="words-between-count-and-noun"),
    pytest.param("33 golden-vector cases", id="hyphenated-compound-singular"),
    pytest.param("the table publishes 33 entries", id="count-after-the-noun"),
    pytest.param("vectors: 33", id="colon-form"),
    pytest.param("the table shipped 33 of them", id="anaphora-after-the-noun"),
    pytest.param("thirty-three vectors", id="spelled-out"),
    pytest.param("33 test vectors", id="another-adjective"),
    pytest.param("negative_vectors holds 5", id="list-name-then-count"),
]


@pytest.mark.parametrize("phrase", COUNT_REWORDINGS)
def test_the_count_guard_catches_every_natural_rewording(phrase: str):
    """A guard that only catches the phrasing that produced it has caught nothing."""
    assert _hardcoded_counts(phrase), f"a hardcoded count evaded the guard: {phrase!r}"


# The other half. A pattern that matched everything would satisfy the parametrisation
# above and be worthless — it would fire on every docstring in the package and the
# only available repair would be to delete the guard.
NOT_A_COUNT = [
    pytest.param("the vector table is the cross-implementation contract", id="no-number"),
    pytest.param("read the sizes from table['vector_counts'] instead", id="the-approved-idiom"),
    pytest.param("field 8 admits ASCII printable 0x20-0x7E and nothing else", id="a-field-number"),
    pytest.param("the six- and nine-field downgrade strings", id="field-counts-spelled-small"),
    pytest.param("which is why the vector table pins it (v27)", id="a-vector-ID-not-a-count"),
    pytest.param("field 3 is the lowercase 8-4-4-4-12 form, so this vector", id="a-uuid-shape"),
    pytest.param("vector_counts holds one key per list", id="schema-shape"),
]


@pytest.mark.parametrize("phrase", NOT_A_COUNT)
def test_the_count_guard_does_not_fire_on_ordinary_prose(phrase: str):
    assert not _hardcoded_counts(phrase), f"the guard over-reached into: {phrase!r}"


def test_no_shipped_docstring_hardcodes_a_vector_count():
    """The S-5 defect in the shape that can recur, not the one instance of it."""
    import perceivo_client.signing as signing_pkg

    offenders = []
    for name in ["<module>", *dir(signing_pkg)]:
        target = signing_pkg if name == "<module>" else getattr(signing_pkg, name, None)
        doc = getattr(target, "__doc__", None)
        if not isinstance(doc, str):
            continue
        offenders += [f"{name}: {hit!r}" for hit in _hardcoded_counts(doc)]
    assert not offenders, (
        "a hardcoded vector count in shipped prose will rot the next time a vector is "
        f"added; read it from table['vector_counts'] instead: {offenders}"
    )


def test_no_prose_inside_the_shipped_table_hardcodes_a_vector_count(table):
    """The same rule over the shipped table's own prose.

    The guard above scans docstrings. The table ships its own prose — a
    ``description`` on every vector, plus ``notes`` and ``secret_note`` — generated
    by ``vectors/generate_vectors.py``, and one of those descriptions carried a live
    count of the positive list. Nothing scanned it, so adding a vector would have
    shipped an artefact contradicting its own ``vector_counts`` with every control
    green: the defect this whole section exists to prevent, one file across.
    """

    def strings(node, path=""):
        if isinstance(node, dict):
            for key, value in node.items():
                yield from strings(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from strings(value, f"{path}[{index}]")
        elif isinstance(node, str):
            yield path, node

    offenders = [
        f"{path}: {hit!r}" for path, text in strings(table) for hit in _hardcoded_counts(text)
    ]
    assert not offenders, (
        "the shipped table states one of its own counts in prose; regenerate it from "
        f"a generator that does not, so the artefact cannot contradict itself: {offenders}"
    )
