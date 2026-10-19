"""The signing-vector table declares its own counts; prose does not restate them."""

from __future__ import annotations

import re

import pytest

from tests._signing_vectors_support import (
    load_table,
)


@pytest.fixture(scope="module")
def table() -> dict:
    return load_table()


# ---------------------------------------------------------------------------
# The counts are declared by the table
# ---------------------------------------------------------------------------


def test_the_declared_counts_match_the_lists_they_describe(table):
    declared = table["vector_counts"]
    assert len(table["vectors"]) == declared["positive"]
    assert len(table["negative_vectors"]) == declared["negative"]
    assert len(table["unsignable_vectors"]) == declared["unsignable"]
    assert len(table["secret_transport_vectors"]) == declared["secret_transport"]
    # And none of the four is empty, or the equalities above hold vacuously.
    assert all(count > 0 for count in declared.values()), declared


# A number, in any spelling prose uses, within a few words of any noun this package
# uses for the table's rows, in either order.
#: A number as prose writes one. Spelled-out forms below thirteen are excluded.
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


# Natural ways a writer states the count.
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
    """Every natural phrasing of a count is caught."""
    assert _hardcoded_counts(phrase), f"a hardcoded count evaded the guard: {phrase!r}"


# Ordinary prose the guard does not match.
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
    """No shipped docstring in the signing package states a vector count."""
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
    """No prose inside the shipped table states a vector count."""

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
