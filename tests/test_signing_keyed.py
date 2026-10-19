"""Signature, credentials and secret hygiene: the keyed half of signing.

The canonicalization rules are pinned in ``test_signing_canonical.py``.
"""

from __future__ import annotations

import hashlib
import hmac
import inspect

import pytest

from perceivo_client.signing import (
    HEADER_KEY_ID,
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    RequestSigner,
    SigningCredentials,
    SigningError,
    build_canonical_request,
    compute_signature,
    resolve_signing_credentials,
    sign_request,
    verify_signature,
)

SECRET = "unit-test-secret"
TS = 1767225600
NONCE = "sT8kQ2vX7wLpR4nB1mZ6yH0j"
AUDIENCE = "perceivo-api-local"
KEY_ID = "b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60"
OTHER_KEY_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"


def canonical(
    method="GET",
    raw_path="/x",
    query="",
    body=None,
    timestamp=TS,
    nonce=NONCE,
    audience=AUDIENCE,
    key_id=KEY_ID,
    content_type=None,
    organization=None,
):
    return build_canonical_request(
        audience=audience,
        key_id=key_id,
        method=method,
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=content_type,
        organization=organization,
        timestamp=timestamp,
        nonce=nonce,
    )


def credentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE):
    return SigningCredentials(key_id=key_id, signing_secret=signing_secret, audience=audience)


def signed(**overrides):
    kwargs = {
        "method": "GET",
        "target": "/x",
        "key_id": KEY_ID,
        "secret": SECRET,
        "audience": AUDIENCE,
        "content_type": None,
        "organization": None,
        "timestamp": TS,
        "nonce": NONCE,
    }
    kwargs.update(overrides)
    return sign_request(**kwargs)


def same(a: str, b: str) -> bool:
    """Constant-time string comparison for signature material."""
    return hmac.compare_digest(a, b)


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------
def test_signature_carries_the_v1_prefix_and_64_lowercase_hex():
    signature = compute_signature(canonical(), SECRET)
    assert signature.startswith("v1=")
    hexpart = signature[3:]
    assert len(hexpart) == 64
    assert hexpart == hexpart.lower()
    int(hexpart, 16)


def test_hmac_key_is_the_secrets_raw_bytes():
    text = compute_signature(canonical(), SECRET)
    raw = compute_signature(canonical(), SECRET.encode())
    assert same(text, raw)
    assert len(SECRET.encode().hex()) != 64, "64 hex chars are DECODED; SECRET must not be 32B"
    assert not same(text, compute_signature(canonical(), SECRET.encode().hex()))


def test_canonical_string_is_utf8_encoded_before_hmac():
    string = canonical()
    expected = hmac.new(SECRET.encode(), string.encode("utf-8"), hashlib.sha256).hexdigest()
    assert same(compute_signature(string, SECRET), f"v1={expected}")


def test_empty_secret_is_refused():
    string = canonical()
    with pytest.raises(SigningError, match="empty"):
        compute_signature(string, "")


def test_verify_signature_accepts_the_correct_signature():
    string = canonical()
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True


def test_verify_signature_rejects_a_wrong_signature():
    other = canonical(raw_path="/other")
    assert verify_signature(compute_signature(other, SECRET), canonical(), SECRET) is False


def test_verify_signature_requires_the_version_prefix():
    string = canonical()
    signature = compute_signature(string, SECRET)
    assert verify_signature(signature[3:], string, SECRET) is False
    assert verify_signature("v2=" + signature[3:], string, SECRET) is False


def test_verify_signature_does_not_raise_on_garbage():
    assert verify_signature("", canonical(), SECRET) is False
    assert verify_signature(None, canonical(), SECRET) is False


def test_verify_signature_returns_false_for_a_non_ascii_signature():
    """Malformed input, including non-ASCII, is invalid rather than an exception."""
    string = canonical()
    for bad in ("v1=é" * 8, "v1=" + "ÿ" * 64, "v1=" + "🔑" * 16, "v1=café"):
        assert verify_signature(bad, string, SECRET) is False


def test_verify_signature_stays_correct_for_ascii_signatures():
    """The non-ASCII guard must not swallow legitimate verification."""
    string = canonical()
    assert verify_signature(compute_signature(string, SECRET), string, SECRET) is True


# ---------------------------------------------------------------------------
# sign_request / RequestSigner
# ---------------------------------------------------------------------------
def test_sign_request_emits_the_four_headers():
    result = signed()
    assert set(result.headers) == {
        HEADER_KEY_ID,
        HEADER_TIMESTAMP,
        HEADER_NONCE,
        HEADER_SIGNATURE,
    }
    assert result.headers[HEADER_KEY_ID] == KEY_ID
    assert result.headers[HEADER_TIMESTAMP] == str(TS)
    assert result.headers[HEADER_NONCE] == NONCE


def test_the_audience_does_not_travel_in_a_header():
    """The audience is configured, not sent in a header."""
    result = signed()
    assert result.audience == AUDIENCE
    assert not any(AUDIENCE in value for value in result.headers.values())


def test_key_id_header_is_byte_equal_to_the_signed_field():
    """The header names the key; field 3 binds it. If the two could differ, the
    verifier would fetch one secret and check a string naming another."""
    result = signed(key_id=KEY_ID.upper())
    assert result.canonical_request.split("\n")[2] == result.headers[HEADER_KEY_ID]
    assert result.headers[HEADER_KEY_ID] == KEY_ID  # normalised, not as supplied


def test_timestamp_header_is_byte_equal_to_the_signed_field():
    result = signed()
    assert result.canonical_request.split("\n")[9] == result.headers[HEADER_TIMESTAMP]


def test_nonce_header_is_byte_equal_to_the_signed_field():
    result = signed()
    assert result.canonical_request.split("\n")[10] == result.headers[HEADER_NONCE]


def test_sign_request_defaults_the_timestamp_and_nonce():
    result = sign_request(
        method="GET",
        target="/x",
        key_id=KEY_ID,
        secret=SECRET,
        audience=AUDIENCE,
        content_type=None,
        organization=None,
    )
    assert result.timestamp.isdigit()
    assert 8 <= len(result.nonce) <= 128


def test_sign_request_has_no_default_audience():
    """Omitting the audience is a TypeError."""
    with pytest.raises(TypeError):
        sign_request(
            method="GET",
            target="/x",
            key_id=KEY_ID,
            secret=SECRET,
            content_type=None,
            organization=None,
        )


def test_sign_request_has_no_default_content_type():
    """Omitting ``content_type`` is a TypeError."""
    with pytest.raises(TypeError):
        sign_request(method="GET", target="/x", key_id=KEY_ID, secret=SECRET, audience=AUDIENCE)


@pytest.mark.parametrize(
    ("entry_point", "parameter"),
    [
        (build_canonical_request, "audience"),
        (build_canonical_request, "content_type"),
        (build_canonical_request, "organization"),
        (sign_request, "audience"),
        (sign_request, "content_type"),
        (sign_request, "organization"),
        (RequestSigner.sign, "content_type"),
        (RequestSigner.sign, "organization"),
    ],
    ids=lambda x: getattr(x, "__name__", x),
)
def test_the_unforgettable_parameters_stay_unforgettable(entry_point, parameter):
    """Each signer requires ``content_type`` and ``organization`` with no default."""
    found = inspect.signature(entry_point).parameters[parameter]
    assert found.default is inspect.Parameter.empty, (
        f"{entry_point.__name__}({parameter}=...) acquired the default "
        f"{found.default!r}. Omission must stay a TypeError: the symptom of a wrong "
        "value here is a bare 401, or — for `organization` — no symptom at all."
    )
    assert found.kind is inspect.Parameter.KEYWORD_ONLY, (
        f"{entry_point.__name__}({parameter}=...) is {found.kind}; keyword-only is what "
        "stops it being satisfied positionally by the argument next to it."
    )


def test_sign_request_refuses_api_key_in_the_query():
    with pytest.raises(SigningError, match="api_key"):
        signed(target="/x?api_key=abc")


def test_sign_request_allows_a_key_merely_containing_api_key():
    assert signed(target="/x?api_key_hint=1").signature.startswith("v1=")


def test_sign_request_requires_a_key_id():
    with pytest.raises(SigningError, match="key_id"):
        signed(key_id="")


def test_sign_request_rejects_a_key_id_that_is_not_a_uuid():
    """It is the ``api_keys.id``, not the key prefix every key in an org shares."""
    with pytest.raises(SigningError):
        signed(key_id="pk_live_abcdef")


def test_request_signer_generates_fresh_material_each_call():
    signer = RequestSigner(credentials())
    first = signer.sign("GET", "/x", content_type=None, organization=None)
    second = signer.sign("GET", "/x", content_type=None, organization=None)
    assert first.nonce != second.nonce
    assert not same(first.signature, second.signature)


def test_request_signer_signature_verifies_against_its_canonical_request():
    signer = RequestSigner(credentials())
    result = signer.sign(
        "POST", "/x?b=2&a=1", b"body", content_type="application/json", organization=None
    )
    assert verify_signature(result.signature, result.canonical_request, SECRET)
    # Non-alphabetical: the query reaches the canonical request verbatim.
    assert result.canonical_request.split("\n")[5] == "b=2&a=1"
    assert result.canonical_request.split("\n")[7] == "application/json"


def test_request_signer_exposes_the_key_id_and_audience():
    signer = RequestSigner(credentials(key_id=OTHER_KEY_ID))
    assert signer.key_id == OTHER_KEY_ID
    assert signer.audience == AUDIENCE


def test_request_signer_rejects_a_non_credentials_argument():
    with pytest.raises(SigningError):
        RequestSigner("just-a-secret")


def test_request_signer_cannot_be_built_without_an_audience():
    """``RequestSigner`` takes credentials, and credentials require an audience —
    so there is no reachable path from a configured signer to an unaudienced
    signature."""
    with pytest.raises(TypeError):
        SigningCredentials(key_id=KEY_ID, signing_secret=SECRET)


def test_credentials_normalise_the_key_id_once_at_construction():
    creds = credentials(key_id=KEY_ID.upper())
    assert creds.key_id == KEY_ID


def test_credentials_reject_an_illegal_audience():
    with pytest.raises(SigningError):
        credentials(audience="https://api.perceivo.ai")


# ---------------------------------------------------------------------------
# Secret handling — the secret must not escape into any string form
# ---------------------------------------------------------------------------
def test_credentials_repr_redacts_the_secret():
    creds = credentials(signing_secret="super-secret-value")
    assert "super-secret-value" not in repr(creds)
    assert "super-secret-value" not in str(creds)
    assert "<redacted>" in repr(creds)


def test_signer_repr_redacts_the_secret():
    signer = RequestSigner(credentials(signing_secret="super-secret-value"))
    assert "super-secret-value" not in repr(signer)
    assert "super-secret-value" not in str(signer)


def test_signed_request_repr_carries_no_secret():
    assert "super-secret-value" not in repr(signed(secret="super-secret-value"))


def test_signing_errors_never_quote_the_secret():
    secret = "super-secret-value"
    for kwargs in (
        {"method": "get", "target": "/x"},
        {"method": "GET", "target": "http://h/x"},
        {"method": "GET", "target": "/x?"},
        {"method": "GET", "target": "/x?api_key=1"},
        {"method": "GET", "target": "/x", "nonce": "bad"},
        {"method": "GET", "target": "/x", "timestamp": "-5"},
        {"method": "GET", "target": "/x", "audience": "not legal"},
        {"method": "GET", "target": "/x", "key_id": "pk_live_x"},
        {"method": "GET", "target": "/x", "content_type": "a/b\nc"},
    ):
        with pytest.raises(SigningError) as excinfo:
            signed(secret=secret, **kwargs)
        assert secret not in str(excinfo.value)


def test_credentials_reject_an_empty_secret_without_echoing_it():
    with pytest.raises(SigningError, match="empty"):
        credentials(signing_secret="")


def test_credentials_reject_an_empty_key_id():
    with pytest.raises(SigningError, match="key_id"):
        credentials(key_id="")


# ---------------------------------------------------------------------------
# resolve_signing_credentials: opt-in, all or nothing
# ---------------------------------------------------------------------------
@pytest.fixture
def no_signing_env(monkeypatch):
    for name in ("PERCEIVO_KEY_ID", "PERCEIVO_SIGNING_SECRET", "PERCEIVO_HMAC_AUDIENCE"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_no_configuration_means_no_signing(no_signing_env):
    assert resolve_signing_credentials() is None


def test_an_audience_alone_does_not_switch_signing_on(no_signing_env):
    """It is inert without a key: configuring one must not start signing."""
    assert resolve_signing_credentials(audience=AUDIENCE) is None


def test_explicit_arguments_are_used(no_signing_env):
    creds = resolve_signing_credentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    assert creds is not None
    assert creds.key_id == KEY_ID
    assert creds.audience == AUDIENCE


def test_credential_environment_variables_are_the_fallback(no_signing_env):
    """The two *credentials* may come from the environment. Only those two."""
    no_signing_env.setenv("PERCEIVO_KEY_ID", OTHER_KEY_ID)
    no_signing_env.setenv("PERCEIVO_SIGNING_SECRET", SECRET)
    creds = resolve_signing_credentials(audience=AUDIENCE)
    assert creds is not None
    assert creds.key_id == OTHER_KEY_ID
    assert creds.audience == AUDIENCE


def test_the_audience_has_no_environment_fallback(no_signing_env):
    """The audience is not read from the environment."""
    no_signing_env.setenv("PERCEIVO_KEY_ID", OTHER_KEY_ID)
    no_signing_env.setenv("PERCEIVO_SIGNING_SECRET", SECRET)
    no_signing_env.setenv("PERCEIVO_HMAC_AUDIENCE", "perceivo-api-prod")
    with pytest.raises(SigningError, match="without an audience"):
        resolve_signing_credentials()


def test_secret_without_key_id_fails_loudly(no_signing_env):
    with pytest.raises(SigningError, match="without a key id"):
        resolve_signing_credentials(signing_secret=SECRET)


def test_key_id_without_secret_fails_loudly(no_signing_env):
    with pytest.raises(SigningError, match="without a signing secret"):
        resolve_signing_credentials(key_id=KEY_ID)


def test_key_and_secret_without_an_audience_fail_loudly(no_signing_env):
    """A missing audience raises rather than defaulting."""
    with pytest.raises(SigningError, match="without an audience"):
        resolve_signing_credentials(key_id=KEY_ID, signing_secret=SECRET)


def test_resolve_error_does_not_echo_the_secret(no_signing_env):
    with pytest.raises(SigningError) as excinfo:
        resolve_signing_credentials(signing_secret="super-secret-value")
    assert "super-secret-value" not in str(excinfo.value)
