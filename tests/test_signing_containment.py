"""Containment guards: the secret does not escape, and a credential is not signed.

Covers ``SigningCredentials`` reflection and copying, the query-credential guard
across decoded spellings, and ``key_id`` header validation.
"""

from __future__ import annotations

import re

import pytest

from perceivo_client.signing import SigningError, sign_request
from perceivo_client.signing.signer import RequestSigner, SigningCredentials

SECRET = "not-a-real-secret-just-a-test-value"
# A UUID: field 3 is the API key id.
KEY_ID = "b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60"
AUDIENCE = "perceivo-api-local"


# ---------------------------------------------------------------------------
# The caller rule on pickling, bound as a rule rather than a word
# ---------------------------------------------------------------------------
#
# The guard requires a prohibition naming both routes to the raw secret; a
# docstring that only mentions pickling does not satisfy it.

_PROHIBITION = re.compile(r"\b(?:do\s+not|don't|never|must\s+not)\b", re.IGNORECASE)


def _sentences(doc: str | None) -> list[str]:
    """A docstring as sentences, with reST/markdown emphasis removed first."""
    flat = " ".join((doc or "").split()).replace("`", "").replace("*", "")
    return re.split(r"(?<=\.)\s+", flat)


def _caller_prohibitions_naming_the_open_routes(doc: str | None) -> list[str]:
    """Sentences forbidding the caller both routes that carry the raw secret."""
    return [
        sentence
        for sentence in _sentences(doc)
        if _PROHIBITION.search(sentence)
        and re.search(r"\bpickle\b", sentence, re.IGNORECASE)
        and re.search(r"\bdeepcopy\b", sentence, re.IGNORECASE)
    ]


def test_the_caller_rule_guard_is_not_satisfied_by_a_bare_mention():
    """A description without a rule, or a rule covering one route, does not bind."""
    # A description of the leak, with no rule in it: not a mitigation.
    assert not _caller_prohibitions_naming_the_open_routes(
        "``creds.__getstate__()`` — and therefore ``pickle.dumps(creds)`` — carries "
        "the secret, and so does ``copy.deepcopy``."
    )
    # A prohibition that closes only one of the two routes: not the rule either.
    assert not _caller_prohibitions_naming_the_open_routes("**Do not pickle a credential.**")
    # The rule, in its own words and in a reworded form, both bind.
    assert _caller_prohibitions_naming_the_open_routes(
        "**Do not pickle, serialise or ``deepcopy``-then-log a ``SigningCredentials``.**"
    )
    assert _caller_prohibitions_naming_the_open_routes(
        "Callers must not pickle a credential, nor deepcopy one into a log record."
    )


# ---------------------------------------------------------------------------
# The secret is unreachable through the instance, not merely unprinted
# ---------------------------------------------------------------------------


def test_credentials_expose_no_instance_dict():
    """``vars()`` must not be a bypass around the redacting ``__repr__``."""
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    with pytest.raises(TypeError):
        vars(creds)
    assert not hasattr(creds, "__dict__")


def test_no_generic_object_dump_reveals_the_secret():
    """The secret is absent from every generic rendering of the instance."""
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    renderings = [repr(creds), str(creds), f"{creds}", format(creds)]
    for rendering in renderings:
        assert SECRET not in rendering, f"secret leaked into {rendering!r}"
    # ...and the key_id, which is not secret, is still there to identify the object.
    assert KEY_ID in repr(creds)


def test_the_secret_literal_is_long_enough_to_be_a_real_search_term():
    """Guard the guard: a short or empty needle would make the leak checks vacuous."""
    assert len(SECRET) >= 16


# ---------------------------------------------------------------------------
# Dataclass reflection
# ---------------------------------------------------------------------------
#
# ``SigningCredentials`` is not a dataclass, so ``dataclasses.asdict`` and
# ``astuple`` cannot extract the secret. Its dataclass-like behaviour is asserted
# below.


def test_the_dataclass_reflection_route_is_closed():
    """``asdict``/``astuple`` must not be able to extract the signing secret."""
    import dataclasses

    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)

    assert not dataclasses.is_dataclass(creds), (
        "still a dataclass: asdict() will walk __dataclass_fields__ and extract the secret"
    )
    for walk in (dataclasses.asdict, dataclasses.astuple, dataclasses.fields):
        with pytest.raises(TypeError):
            walk(creds)
    with pytest.raises(TypeError):
        dataclasses.replace(creds, key_id=KEY_ID)


def test_the_reflection_refusal_does_not_itself_print_the_secret():
    """A TypeError that renders the object would reintroduce the leak it closes."""
    import dataclasses

    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    with pytest.raises(TypeError) as excinfo:
        dataclasses.asdict(creds)
    assert SECRET not in str(excinfo.value)


def test_no_class_level_attribute_enumerates_the_fields():
    """The property, not the mechanism: nothing on the class hands out the field names
    in a form ``getattr`` can be looped over generically."""
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    assert not hasattr(creds, "__dataclass_fields__")
    assert not hasattr(type(creds), "__dataclass_fields__")


def test_the_credential_still_behaves_exactly_as_the_dataclass_did():
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    same = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    other = SigningCredentials(
        key_id="c7a1b2d3-8e4f-4a5b-9c6d-7e8f9a0b1c2d",
        signing_secret=SECRET,
        audience=AUDIENCE,
    )

    # Attribute access, the one route that is supposed to work.
    assert creds.key_id == KEY_ID
    assert creds.signing_secret == SECRET
    assert creds.audience == AUDIENCE

    # Value equality and hashability, as `eq=True`/`frozen=True` gave them.
    assert creds == same
    assert creds != other
    assert creds != object()
    assert hash(creds) == hash(same)
    assert len({creds, same, other}) == 2

    # Frozen.
    with pytest.raises(AttributeError):
        creds.signing_secret = "rotated"
    with pytest.raises(AttributeError):
        del creds.signing_secret

    # ``audience`` is keyword-only.
    with pytest.raises(TypeError):
        SigningCredentials(KEY_ID, SECRET, AUDIENCE)  # type: ignore[misc]


def test_pattern_matching_on_the_credential_still_works():
    """``__match_args__`` supports positional pattern matching."""
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    match creds:
        case SigningCredentials(key_id, secret):
            assert key_id == KEY_ID
            assert secret == SECRET
        case _:  # pragma: no cover - a failure here is the assertion
            pytest.fail("positional pattern match no longer destructures the credential")


def test_the_key_id_normalisation_survived_the_rewrite():
    """``__init__`` validates and normalises ``key_id``."""
    # The spellings `uuid.UUID` itself folds: uppercase and braced. It does not
    # strip surrounding whitespace, so that is not asserted here.
    creds = SigningCredentials(
        key_id=f"{{{KEY_ID.upper()}}}", signing_secret=SECRET, audience=AUDIENCE
    )
    assert creds.key_id == KEY_ID
    with pytest.raises(SigningError):
        SigningCredentials(key_id="not a uuid", signing_secret=SECRET, audience=AUDIENCE)


def test_copying_a_credential_still_works():
    """Copying and pickling work without the dataclass machinery."""
    import copy
    import pickle

    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)

    assert copy.copy(creds) == creds
    assert copy.deepcopy(creds) == creds
    # A deep copy is an independent object.
    assert copy.deepcopy(creds) is not creds
    # Held indirectly, which is how it actually reaches `deepcopy` in real code.
    assert copy.deepcopy({"auth": creds})["auth"] == creds

    restored = pickle.loads(pickle.dumps(creds))
    assert restored == creds
    assert restored.key_id == KEY_ID
    assert restored.signing_secret == SECRET
    assert restored.audience == AUDIENCE


def test_deepcopy_of_a_mutable_secret_is_independent_of_the_callers_buffer():
    """A deep copy does not alias the caller's buffer.

    Rotating the original buffer in place leaves the copy signing with the old key.
    """
    import copy
    import hashlib
    import hmac

    def derived_key(creds) -> str:
        raw = creds.signing_secret
        raw = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
        return hmac.new(raw, b"canonical-request-stand-in", hashlib.sha256).hexdigest()

    buffer = bytearray(b"rotating-buffer-secret-value-0001")
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=buffer, audience=AUDIENCE)
    snapshot = copy.deepcopy(creds)
    before = derived_key(snapshot)

    # The caller rotates its own buffer, in place. The snapshot must not notice.
    buffer[:] = b"rotating-buffer-secret-value-0002"

    assert derived_key(snapshot) == before, (
        "the deep copy aliased the caller's buffer: rotating it in place changed the "
        "key the 'snapshot' signs with"
    )
    # And the rotation really did land, or the assertion above holds vacuously.
    assert derived_key(creds) != before


class TenantCredentials(SigningCredentials):
    """A credential subclass with one extra slot, at module level so ``pickle`` can import it."""

    __slots__ = ("tenant",)

    def __init__(self, *args, tenant: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "tenant", tenant)


def test_a_subclass_survives_a_pickle_round_trip_with_all_of_its_state():
    """A subclass with its own slots round-trips all of its state and still signs."""
    import copy
    import pickle

    creds = TenantCredentials(KEY_ID, SECRET, audience=AUDIENCE, tenant="acme")
    assert set(creds.__getstate__()) == {"key_id", "signing_secret", "audience", "tenant"}

    for restored in (pickle.loads(pickle.dumps(creds)), copy.deepcopy(creds)):
        assert restored.key_id == KEY_ID
        assert restored.signing_secret == SECRET
        assert restored.audience == AUDIENCE
        assert restored.tenant == "acme"
        # The reason the three base slots matter: without them this raises.
        assert (
            RequestSigner(restored)
            .sign("GET", "/x", content_type=None, organization=None)
            .signature.startswith("v1=")
        )


def test_the_residual_serialisation_route_is_recorded_not_discovered_later():
    """Pickling still works, and the class docstring tells callers not to pickle it."""
    import pickle

    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    assert SECRET.encode() in pickle.dumps(creds), (
        "if this now passes containment, update the docstring: it tells callers this route is open"
    )
    assert _caller_prohibitions_naming_the_open_routes(SigningCredentials.__doc__), (
        "the docstring no longer states the caller rule. `__getstate__` is a "
        "deliberately unclosed secret-extraction route and that rule is its entire "
        "mitigation: without it the class documents an open leak and asks nothing "
        "of the caller"
    )


# ---------------------------------------------------------------------------
# The query-credential guard matches what a server decodes, not what was typed
# ---------------------------------------------------------------------------

# Each entry is a query string a permissive server reads as carrying `api_key`.
# Spaces are percent-encoded because the target validator rejects a raw space first.
BYPASSING_QUERIES = [
    pytest.param("API_KEY=abc123", id="uppercase-name"),
    pytest.param("Api_Key=abc123", id="mixed-case-name"),
    pytest.param("api%5Fkey=abc123", id="percent-encoded-underscore"),
    pytest.param("api%5fkey=abc123", id="percent-encoded-underscore-lowercase-hex"),
    pytest.param("%41PI_KEY=abc123", id="percent-encoded-first-letter"),
    pytest.param("%20api_key=abc123", id="encoded-leading-space"),
    pytest.param("limit=10;%20api_key=abc123", id="semicolon-separator-with-encoded-space"),
    pytest.param("limit=10;api_key=abc123", id="semicolon-separator"),
]


@pytest.mark.parametrize("query", BYPASSING_QUERIES)
def test_every_decoded_spelling_of_the_credential_parameter_is_refused(query: str):
    with pytest.raises(SigningError, match="api_key"):
        sign_request(
            method="GET",
            target=f"/v1/orchestrations?{query}",
            key_id=KEY_ID,
            secret=SECRET,
            audience=AUDIENCE,
            content_type=None,
            organization=None,
        )


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("limit=10", id="ordinary"),
        pytest.param("api_keys=3", id="longer-name-must-not-match"),
        pytest.param("my_api_key_name=x", id="substring-must-not-match"),
        pytest.param("filter=api_key", id="name-appearing-as-a-VALUE-is-fine"),
        pytest.param("api+key=abc123", id="plus-decodes-to-SPACE-not-underscore"),
        pytest.param("", id="empty"),
    ],
)
def test_the_guard_does_not_over_reach_into_ordinary_queries(query: str):
    """Names that only resemble ``api_key`` still sign.

    ``filter=api_key`` carries it as a value, and ``api+key`` decodes to ``api key``.
    """
    target = f"/v1/orchestrations?{query}" if query else "/v1/orchestrations"
    signed = sign_request(
        method="GET",
        target=target,
        key_id=KEY_ID,
        secret=SECRET,
        audience=AUDIENCE,
        content_type=None,
        organization=None,
    )
    assert signed.signature.startswith("v1=")
