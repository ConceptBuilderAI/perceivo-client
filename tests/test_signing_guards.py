"""Guards on the *shape* of the canonical request, and on the nonce's entropy source.

These pin two properties that no other test in this suite covers. Both were found
by deliberate mutation:

1. **Trailing control characters.** Python's ``$`` matches at end-of-string *or
   immediately before a trailing newline*, so ``^...$`` validators accept a value
   ending in ``\\n`` — the byte used as the field separator. Changing all four
   validators from ``^...$`` to ``\\A...\\Z`` broke no other test. A field that can carry the separator lets two
   different requests produce one canonical string, and a canonicaliser that maps
   two requests onto one signature is broken by definition.

2. **The nonce's entropy source.** Replacing ``secrets.token_urlsafe`` with
   ``random.choice`` over the same alphabet, at the same length, passes every
   output-based test: no statistical test can tell a CSPRNG from a PRNG from one sample,
   so the requirement has to be pinned at the source rather than inferred from the
   output.

Neither property is exploitable over HTTP, because a bare LF cannot traverse a
request line. They are pinned because this package is the normative reference that
server-side verifiers are written against, and a reference must not be looser than
the server it describes.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

from perceivo_client.signing import (
    SigningError,
    build_canonical_request,
    canonical_content_type,
    canonical_path,
    canonical_query,
    generate_nonce,
    sign_request,
    split_target,
)
from perceivo_client.signing import canonical as canonical_module

TS = 1767225600
NONCE = "sT8kQ2vX7wLpR4nB1mZ6yH0j"
# A uuid, because field 3 is the api_keys.id and nothing else normalises to it.
KEY_ID = "b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60"
AUDIENCE = "perceivo-api-local"
# Local to this module. Not the published golden-vector key, and not a credential.
SECRET = b"guard-tests-only-not-a-credential"


def _canonical(**overrides):
    kwargs = {
        "audience": AUDIENCE,
        "key_id": KEY_ID,
        "method": "GET",
        "raw_path": "/x",
        "query_string": "",
        "body": None,
        "content_type": None,
        "organization": None,
        "timestamp": TS,
        "nonce": NONCE,
    }
    kwargs.update(overrides)
    return build_canonical_request(**kwargs)


# ---------------------------------------------------------------------------
# The collision, stated as the property it violates
# ---------------------------------------------------------------------------


def test_two_different_targets_never_share_one_signature():
    """``/a\\n`` and ``/a?\\n`` are different requests and must not sign alike.

    They are the pair that collides when the target validator accepts a trailing
    newline: ``/a\\n`` parses as path ``/a\\n`` with no query, ``/a?\\n`` as path
    ``/a`` with query ``\\n``, and both render ``"/a" + "\\n" + ""`` in fields 2
    and 3 of the base string.

    Asserted as "no two distinct targets map to one signature" rather than "both
    are rejected", so that the property survives any future decision to accept
    these targets: if they are ever signable again, they must sign *differently*.
    """
    signatures = {}
    for target in ("/a\n", "/a?\n"):
        try:
            signed = sign_request(
                method="GET",
                target=target,
                key_id=KEY_ID,
                secret=SECRET,
                audience=AUDIENCE,
                content_type=None,
                organization=None,
                timestamp=TS,
                nonce=NONCE,
            )
        except SigningError:
            continue
        signatures[target] = signed.signature

    assert len(set(signatures.values())) == len(signatures), (
        f"distinct targets produced one signature: {signatures}"
    )


def test_both_members_of_the_colliding_pair_are_rejected():
    """The resolution actually shipped: neither target is signable."""
    for target in ("/a\n", "/a?\n"):
        with pytest.raises(SigningError):
            sign_request(
                method="GET",
                target=target,
                key_id=KEY_ID,
                secret=SECRET,
                audience=AUDIENCE,
                content_type=None,
                organization=None,
                timestamp=TS,
                nonce=NONCE,
            )


# ---------------------------------------------------------------------------
# Eleven fields, ten separators — whatever the caller hands in
# ---------------------------------------------------------------------------


def test_a_legal_request_has_exactly_eleven_fields():
    canonical = _canonical(raw_path="/v1/x", query_string="limit=10")
    assert canonical.count("\n") == 10
    assert len(canonical.split("\n")) == 11


NEWLINE_BEARING_FIELDS = [
    ("audience", AUDIENCE + "\n"),
    ("key_id", KEY_ID + "\n"),
    ("method", "GET\n"),
    ("raw_path", "/x\n"),
    ("query_string", "limit=10\n"),
    ("content_type", "application/json\n"),
    # Field 9 belongs here for the same reason Content-Type does: it is a
    # header a caller passes through, so a value
    # carrying a separator is reachable from the caller's own input rather than
    # only from a hostile construction.
    ("organization", "8c7e2b41-5d93-4a06-bf12-3e9d70a5c684\n"),
    ("timestamp", "1767225600\n"),
    ("nonce", NONCE + "\n"),
]


@pytest.mark.parametrize(("field", "value"), NEWLINE_BEARING_FIELDS)
def test_a_trailing_newline_can_never_add_a_field(field, value):
    """No input may make the canonical request anything other than eleven fields.

    The separator count is asserted on the *returned* value rather than only
    asserting that the call raises, so the invariant is pinned even if a field is
    ever made permissive: rejecting is one acceptable outcome, emitting a
    twelve-field string is not.

    Revision 2 widened this from five fields to eight — the audience, the key id
    and Content-Type are attacker-influenced in exactly the way the original five
    are, and Content-Type is the one an HTTP client will happily set from a value
    the caller passed through. Revision 3 makes it nine: the organization is a
    caller-supplied header by the same argument.
    """
    try:
        canonical = _canonical(**{field: value})
    except SigningError:
        return
    separators = canonical.count("\n")
    assert separators == 10, f"a trailing newline in {field} produced {separators} separators"


@pytest.mark.parametrize(("field", "value"), NEWLINE_BEARING_FIELDS)
def test_every_field_rejects_a_trailing_newline(field, value):
    """REJECTED, never escaped. Escaping would make two requests one string."""
    with pytest.raises(SigningError):
        _canonical(**{field: value})


@pytest.mark.parametrize(("field", "value"), NEWLINE_BEARING_FIELDS)
def test_no_field_escapes_a_newline_into_the_canonical_string(field, value):
    """The other half of "reject, never escape".

    A signer that emitted ``\\\\n`` or ``%0A`` would keep the field count right and
    still be wrong, because the escaping is not part of the wire format and no
    other implementation would reproduce it.
    """
    try:
        canonical = _canonical(**{field: value})
    except SigningError:
        return
    assert "\\n" not in canonical
    assert "%0A" not in canonical.upper()


@pytest.mark.parametrize("suffix", ["\n", "\r", "\r\n", "\x00", "\x1f", "\x7f", " "])
def test_the_target_validator_rejects_every_trailing_control_character(suffix):
    """``\\n`` is the dangerous one; the rest confirm the class is closed, not the case."""
    with pytest.raises(SigningError):
        canonical_path("/x" + suffix)
    with pytest.raises(SigningError):
        canonical_query("limit=10" + suffix)
    with pytest.raises(SigningError):
        split_target("/x?limit=10" + suffix)


@pytest.mark.parametrize("suffix", ["\n", "\r", "\x00", " "])
def test_the_method_validator_rejects_every_trailing_control_character(suffix):
    with pytest.raises(SigningError):
        _canonical(method="GET" + suffix)


@pytest.mark.parametrize("suffix", ["\n", "\r", "\x00", " "])
def test_the_timestamp_validator_rejects_every_trailing_control_character(suffix):
    with pytest.raises(SigningError):
        _canonical(timestamp="1767225600" + suffix)


@pytest.mark.parametrize("suffix", ["\n", "\r", "\x00", " "])
def test_the_nonce_validator_rejects_every_trailing_control_character(suffix):
    with pytest.raises(SigningError):
        _canonical(nonce=NONCE + suffix)


def test_a_newline_in_the_middle_of_a_field_is_rejected_too():
    """The embedded case already held; asserted so a future rewrite cannot lose it."""
    with pytest.raises(SigningError):
        canonical_path("/a\nb")
    with pytest.raises(SigningError):
        _canonical(method="G\nET")


# ---------------------------------------------------------------------------
# The nonce comes from a CSPRNG (mutant M19)
# ---------------------------------------------------------------------------


def test_generate_nonce_draws_from_the_secrets_module(monkeypatch):
    """The nonce must come from ``secrets``, and this observes that it does.

    A statistical test cannot separate ``secrets`` from ``random`` — so instead of
    inspecting the output, this replaces the CSPRNG and checks the replacement is
    what answered. Any implementation that sources its bytes elsewhere returns
    something other than the sentinel and fails here.
    """
    calls = []

    def fake_token_urlsafe(n_bytes):
        calls.append(n_bytes)
        return "SENTINEL_from_the_csprng_not_a_real_nonce"

    monkeypatch.setattr(canonical_module.secrets, "token_urlsafe", fake_token_urlsafe)

    assert generate_nonce(24) == "SENTINEL_from_the_csprng_not_a_real_nonce"
    assert calls == [24], "generate_nonce did not route through secrets.token_urlsafe"


def test_the_signing_package_never_imports_a_non_cryptographic_rng():
    """No module under ``signing/`` may import ``random``.

    The behavioural test above pins ``generate_nonce``; this pins the package, so a
    second generator added later cannot quietly reach for the wrong source.
    """
    package_dir = pathlib.Path(canonical_module.__file__).parent
    offenders = []
    for module_path in sorted(package_dir.glob("*.py")):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders += [
                    f"{module_path.name}: import {a.name}"
                    for a in node.names
                    if a.name.split(".")[0] == "random"
                ]
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "random":
                offenders.append(f"{module_path.name}: from {node.module} import ...")
    assert offenders == [], f"non-cryptographic RNG imported in the signing package: {offenders}"


def test_generate_nonce_names_secrets_token_urlsafe_in_its_source():
    """Belt and braces for the case where the call is made without going through us."""
    source = inspect.getsource(canonical_module.generate_nonce)
    assert "secrets.token_urlsafe" in source


# ---------------------------------------------------------------------------
# Field 8 admits ASCII printable 0x20-0x7E and nothing else
# ---------------------------------------------------------------------------
#
# A server that decodes the raw Content-Type header bytes as latin-1 and a client
# that decodes them as UTF-8 build different values of field 8 for any non-ASCII
# byte, and no positive golden vector can show it, because every one is pure ASCII.
#
# The API refuses every byte outside 0x20-0x7E, so the client refuses the same set
# at signing time, where the caller still holds the input and can be told why. On
# ASCII printable, latin-1 and UTF-8 decode identically, so the two sides cannot
# disagree.
#
# Without this, the client would sign a request the API always refuses, and the
# caller would see a bare `invalid_signature` 401 with nothing to diagnose it by.


UNSIGNABLE_CONTENT_TYPES = [
    pytest.param("text/plain; x=é", id="str-with-u00e9"),
    pytest.param("text/plain; x=é".encode(), id="bytes-utf8-encoded-u00e9"),
    pytest.param(b"text/plain; x=\xff", id="bytes-not-valid-utf8"),
    pytest.param("application/json\nX-Evil: 1", id="newline-subsumed-by-the-charset-rule"),
    pytest.param("application/json;\tcharset=utf-8", id="tab-0x09"),
    pytest.param("application/json; x=\x7f", id="del-0x7f-one-past-the-top"),
    pytest.param("application/json; x=\x1f", id="us-0x1f-one-below-the-bottom"),
    pytest.param("application/json; x=\r", id="carriage-return"),
    pytest.param("application/json; x=\x00", id="nul"),
    pytest.param("application/json; x=🔑", id="astral-plane"),
]


@pytest.mark.parametrize("value", UNSIGNABLE_CONTENT_TYPES)
def test_a_content_type_outside_ascii_printable_is_unsignable(value):
    """REJECTED at signing time, never signed and left for the edge to refuse."""
    with pytest.raises(SigningError):
        canonical_content_type(value)


@pytest.mark.parametrize("value", UNSIGNABLE_CONTENT_TYPES)
def test_the_whole_request_is_unsignable_not_just_the_field(value):
    """The guard must hold through ``build_canonical_request`` and ``sign_request``.

    A check that only fires when ``canonical_content_type`` is called directly
    would leave every real signing path open.
    """
    with pytest.raises(SigningError):
        _canonical(content_type=value)
    with pytest.raises(SigningError):
        sign_request(
            method="GET",
            target="/x",
            content_type=value,
            organization=None,
            key_id=KEY_ID,
            secret=SECRET,
            audience=AUDIENCE,
        )


def test_every_byte_in_0x20_to_0x7e_is_still_signable():
    """The positive control.

    A guard that refused everything would satisfy every negative case above. This
    asserts the whole admitted range survives, byte for byte, in field 8 of a real
    canonical string.
    """
    every_printable = "".join(chr(code) for code in range(0x20, 0x7F))
    assert canonical_content_type(every_printable) == every_printable
    assert _canonical(content_type=every_printable).split("\n")[7] == every_printable


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="absent-header"),
        pytest.param("", id="empty-string"),
        pytest.param([], id="empty-list"),
    ],
)
def test_the_empty_content_type_stays_legal(value):
    """The rule is ``*``, not ``+``.

    An absent Content-Type is the empty string by the same convention field 6 uses
    for an absent query. A ``+`` here would make every unsigned-body GET
    unsignable — vectors v01 and v29 are exactly that shape.
    """
    assert canonical_content_type(value) == ""
    assert _canonical(content_type=value).count("\n") == 10


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("application/json", id="plain-media-type"),
        pytest.param("application/json; charset=utf-8", id="with-parameter"),
        pytest.param("application/json; charset=UTF-8", id="parameter-case-preserved"),
        pytest.param("multipart/form-data; boundary=----X", id="multipart-boundary"),
        pytest.param(b"application/json", id="bytes-ascii"),
        pytest.param("text/plain; x=~", id="0x7e-the-top-of-the-range"),
        pytest.param("text/plain; x= ", id="0x20-the-bottom-of-the-range"),
    ],
)
def test_ordinary_content_types_are_untouched(value):
    """The guard must not reach further than the charset. Nothing is normalised,
    case-folded, or stripped of parameters — those rulings are what field 8 exists
    for, and a charset check is not a licence to touch them."""
    expected = value.decode("ascii") if isinstance(value, bytes) else value
    assert canonical_content_type(value) == expected
