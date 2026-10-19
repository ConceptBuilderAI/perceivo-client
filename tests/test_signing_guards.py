"""Guards on the shape of the canonical request and on the nonce's entropy source."""

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
    """``/a\\n`` and ``/a?\\n`` are different requests and do not sign alike."""
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
    """Neither target is signable."""
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
    # Field 9 is a caller-supplied header, like Content-Type.
    ("organization", "8c7e2b41-5d93-4a06-bf12-3e9d70a5c684\n"),
    ("timestamp", "1767225600\n"),
    ("nonce", NONCE + "\n"),
]


@pytest.mark.parametrize(("field", "value"), NEWLINE_BEARING_FIELDS)
def test_a_trailing_newline_can_never_add_a_field(field, value):
    """No input makes the canonical request anything other than eleven fields."""
    try:
        canonical = _canonical(**{field: value})
    except SigningError:
        return
    separators = canonical.count("\n")
    assert separators == 10, f"a trailing newline in {field} produced {separators} separators"


@pytest.mark.parametrize(("field", "value"), NEWLINE_BEARING_FIELDS)
def test_every_field_rejects_a_trailing_newline(field, value):
    """A separator is rejected, not escaped."""
    with pytest.raises(SigningError):
        _canonical(**{field: value})


@pytest.mark.parametrize(("field", "value"), NEWLINE_BEARING_FIELDS)
def test_no_field_escapes_a_newline_into_the_canonical_string(field, value):
    """The signer does not emit an escaped separator."""
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
    """A separator inside a field is rejected."""
    with pytest.raises(SigningError):
        canonical_path("/a\nb")
    with pytest.raises(SigningError):
        _canonical(method="G\nET")


# ---------------------------------------------------------------------------
# The nonce comes from a CSPRNG
# ---------------------------------------------------------------------------


def test_generate_nonce_draws_from_the_secrets_module(monkeypatch):
    """``generate_nonce`` draws from ``secrets.token_urlsafe``."""
    calls = []

    def fake_token_urlsafe(n_bytes):
        calls.append(n_bytes)
        return "SENTINEL_from_the_csprng_not_a_real_nonce"

    monkeypatch.setattr(canonical_module.secrets, "token_urlsafe", fake_token_urlsafe)

    assert generate_nonce(24) == "SENTINEL_from_the_csprng_not_a_real_nonce"
    assert calls == [24], "generate_nonce did not route through secrets.token_urlsafe"


def test_the_signing_package_never_imports_a_non_cryptographic_rng():
    """No module under ``signing/`` imports ``random``."""
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
    """The source of ``generate_nonce`` names ``secrets.token_urlsafe``."""
    source = inspect.getsource(canonical_module.generate_nonce)
    assert "secrets.token_urlsafe" in source


# ---------------------------------------------------------------------------
# Field 8 admits ASCII printable 0x20-0x7E and nothing else
# ---------------------------------------------------------------------------
#
# The API refuses every byte outside 0x20-0x7E, so the client refuses the same set
# at signing time.


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
    """Out-of-range bytes are rejected at signing time."""
    with pytest.raises(SigningError):
        canonical_content_type(value)


@pytest.mark.parametrize("value", UNSIGNABLE_CONTENT_TYPES)
def test_the_whole_request_is_unsignable_not_just_the_field(value):
    """The guard holds through ``build_canonical_request`` and ``sign_request``."""
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
    """The whole admitted range survives in field 8 of a real canonical string."""
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
    """An absent Content-Type is the empty string, which is accepted."""
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
    """The guard does not normalise, case-fold or strip parameters."""
    expected = value.decode("ascii") if isinstance(value, bytes) else value
    assert canonical_content_type(value) == expected
