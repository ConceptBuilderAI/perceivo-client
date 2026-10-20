"""Containment guards: the secret must not escape, and a credential must not be signed.

Each property here appears to hold because of something outside the signing module
(a redacting ``__repr__`` nobody is obliged to call, a well-formed URL nobody is
obliged to write, an HTTP encoder nobody is obliged to use), so each is asserted
directly.

* **``__dict__`` must not route around the redacting ``__repr__``.**
  ``SigningCredentials`` keeps the secret out of ``repr()``; it must not then hand it
  to anything that reaches for ``vars()``: error reporters, structured loggers,
  ``pprint``.
* **The query-credential guard matches every spelling a server decodes.** ``API_KEY=``,
  ``api%5Fkey=`` and a ``;``-separated element must all be refused. ``api%5Fkey`` is
  the important one: a server that percent-decodes parameter names reads it as
  ``api_key``.
* **``key_id`` is validated, not only checked for emptiness.** It is placed in an HTTP
  header, so CR/LF belongs to the encoder's threat model, not the caller's good
  intentions.

None of the three is exploitable over HTTP: h11 rejects a CRLF header before anything
reaches the wire, and the query guard protects the caller's own credential rather than
the platform. They are asserted because this package is the normative reference that
server-side verifiers are written against.
"""

from __future__ import annotations

import re

import pytest

from perceivo_client.signing import SigningError, sign_request
from perceivo_client.signing.signer import RequestSigner, SigningCredentials

SECRET = "not-a-real-secret-just-a-test-value"
# A UUID: field 3 is the API key id, so the accepted key space is narrower than
# "safe as a header value". The tests are written against the real key space,
# because a guard proved over strings the platform never issues proves nothing.
KEY_ID = "b6f0a0d2-7c1e-4f3a-9d55-1c2e3f4a5b60"
AUDIENCE = "perceivo-api-local"


# ---------------------------------------------------------------------------
# Binding the caller rule itself, not merely a word it happens to contain
# ---------------------------------------------------------------------------
#
# A substring check such as ``"pickle" in doc.lower()`` is satisfied by any mention
# of the word, including a purely descriptive one, so it would still pass with the
# caller rule deleted.
#
# ``__getstate__`` is a deliberately unclosed secret-extraction route and the caller
# rule is its entire mitigation, so the guard binds the rule as a rule: a
# prohibition, in one sentence, naming both routes that reach the raw secret. A
# docstring that merely mentions pickling, or that describes the leak without
# asking anything of the caller, does not satisfy it.

_PROHIBITION = re.compile(r"\b(?:do\s+not|don't|never|must\s+not)\b", re.IGNORECASE)


def _sentences(doc: str | None) -> list[str]:
    """A docstring as sentences, with reST/markdown emphasis removed first.

    Backticks and asterisks go before the split so that a rule written
    ``**Do not pickle …**`` ends at its own full stop instead of running into the
    next paragraph, and so the guard binds the prose rather than its formatting.
    """
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
    """Guard the guard, on the two shapes a substring check would accept.

    Without this, "the rule is documented" and "the word appears somewhere" are
    indistinguishable.
    """
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
    """The property that actually matters, stated over the idioms that leak.

    Asserting ``__slots__`` is present would pass the day someone adds
    ``__dict__`` to the slots tuple. This asserts the *secret is absent* from
    every generic rendering instead, so it stays true however the class is built.
    """
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
# Dataclass reflection is a second route to the secret
# ---------------------------------------------------------------------------
#
# Removing `__dict__` is not enough: a `@dataclass` installs a second generic-access
# route on the class, one that does not go through `__dict__` at all:
#
#     dataclasses.asdict(creds)["signing_secret"]
#
# `asdict` walks `__dataclass_fields__` and calls `getattr`, so slots do not touch
# it. Nor do they touch `astuple`, `fields` or `replace`. And unlike `vars()`, this
# is not a hostile idiom: `asdict` is the ordinary, recommended way to render a
# dataclass for a structured log or a JSON error payload, which is precisely the
# code path the redaction exists to protect.
#
# So ``SigningCredentials`` is not a dataclass. Everything a dataclass would provide
# is hand-written and asserted here, so "not a dataclass" cannot silently become
# "not immutable" or "not comparable".


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


# The other half of the trade. Not being a dataclass is only correct if nothing
# legitimate is lost, so every behaviour the decorator would supply is asserted
# here. Without these, "closed the leak" and "broke the credential" look identical.


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

    # `audience` stays keyword-only: a positional third argument was never legal and
    # must not quietly become so.
    with pytest.raises(TypeError):
        SigningCredentials(KEY_ID, SECRET, AUDIENCE)  # type: ignore[misc]


def test_pattern_matching_on_the_credential_still_works():
    """``__match_args__`` is not automatic once the decorator is gone."""
    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)
    match creds:
        case SigningCredentials(key_id, secret):
            assert key_id == KEY_ID
            assert secret == SECRET
        case _:  # pragma: no cover - a failure here is the assertion
            pytest.fail("positional pattern match no longer destructures the credential")


def test_the_key_id_normalisation_survived_the_rewrite():
    """``__post_init__`` validated and normalised. A hand-written ``__init__`` that
    forgot to would accept a key_id ``sign_request`` refuses, and the mismatch would
    only show up as a 401 in production."""
    # The spellings `uuid.UUID` itself folds: uppercase and braced. It does not
    # strip surrounding whitespace, so that is not asserted here.
    creds = SigningCredentials(
        key_id=f"{{{KEY_ID.upper()}}}", signing_secret=SECRET, audience=AUDIENCE
    )
    assert creds.key_id == KEY_ID
    with pytest.raises(SigningError):
        SigningCredentials(key_id="not a uuid", signing_secret=SECRET, audience=AUDIENCE)


def test_copying_a_credential_still_works():
    """Copying and pickling must keep working without the dataclass machinery.

    Without a hand-written ``__getstate__``/``__setstate__`` pair,
    ``copy.deepcopy(creds)`` raises ``AttributeError`` from the frozen
    ``__setattr__``, which breaks any caller holding credentials on a config object
    it deep-copies.
    """
    import copy
    import pickle

    creds = SigningCredentials(key_id=KEY_ID, signing_secret=SECRET, audience=AUDIENCE)

    assert copy.copy(creds) == creds
    assert copy.deepcopy(creds) == creds
    # A deep copy is an independent object, not the original handed back. See
    # `test_deepcopy_of_a_mutable_secret_is_independent_of_the_callers_buffer`
    # below for why that distinction is the whole point rather than pedantry.
    assert copy.deepcopy(creds) is not creds
    # Held indirectly, which is how it actually reaches `deepcopy` in real code.
    assert copy.deepcopy({"auth": creds})["auth"] == creds

    restored = pickle.loads(pickle.dumps(creds))
    assert restored == creds
    assert restored.key_id == KEY_ID
    assert restored.signing_secret == SECRET
    assert restored.audience == AUDIENCE


def test_deepcopy_of_a_mutable_secret_is_independent_of_the_callers_buffer():
    """A deep copy must not alias the caller's buffer; the failure is a wrong signature.

    ``frozen`` binds the *binding*, never the referent, and ``secret_to_key_bytes``
    accepts ``bytearray`` and ``memoryview`` as well as ``str``/``bytes``. So a
    ``__deepcopy__`` that returns ``self`` — which reads as a harmless
    "an immutable value object is its own copy" — hands the caller a snapshot that
    aliases the buffer it was copied from. A caller that takes a deep copy to pin
    the credentials of an in-flight operation and then rotates its own buffer in
    place gets a snapshot that silently starts signing with the new key: every
    request under the old key id 401s, with nothing at the call site to see.

    Asserted over the derived key rather than over ``is`` / ``is not``, so the
    property survives any future re-introduction of a copy hook that happens to
    preserve independence by some other means. The identity assertion in
    ``test_copying_a_credential_still_works`` is the mechanism; this is the
    behaviour, and only this one states a failure.
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
    """A credential subclass carrying one extra slot.

    Module level rather than defined inside the test, because ``pickle`` refuses a
    class it cannot import by qualified name — and the round trip is the point.
    """

    __slots__ = ("tenant",)

    def __init__(self, *args, tenant: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "tenant", tenant)


def test_a_subclass_survives_a_pickle_round_trip_with_all_of_its_state():
    """A subclass with its own slots must round-trip all of its state.

    ``self.__slots__`` is an ordinary attribute lookup.

    On a subclass that declares slots of its own it resolves to the subclass's
    tuple alone, so a ``__getstate__`` written as ``for name in self.__slots__``
    silently omits ``key_id``, ``signing_secret`` and ``audience``. The round trip
    then *succeeds* — no exception, no warning — and returns a credential missing
    everything that makes it one; the failure surfaces later as ``AttributeError``
    out of ``RequestSigner(restored).sign()``, far from the pickle that caused it.

    Subclassing to carry a tenant, a region or an expiry is an ordinary thing for
    a caller to do, so the round trip is asserted on a subclass and on the signing
    call it has to keep working.
    """
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
    """The pickle route is deliberately left open, and this records that decision.

    ``__getstate__`` returns the slot values, so ``pickle.dumps(creds)`` writes the
    secret into the pickle bytes. It is left working because both alternatives are
    worse: a raising ``__getstate__`` breaks ``multiprocessing`` for any config object
    that merely *holds* a credential, and a redacting one round-trips to an object
    that authenticates against nothing and fails as a 401 far from the cause.

    The rule for callers is stated in the class docstring and asserted here: **do not
    pickle, serialise, or ``deepcopy``-then-log a ``SigningCredentials``.**
    """
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
# A guard that compares raw bytes with the literal `api_key` would sign every one.
#
# The spaces are percent-encoded on purpose. A raw leading space is unreachable
# through `sign_request`: the target validator rejects it before the query guard
# runs. `%20` is the form that
# actually arrives, and the one a server strips back to a plain name.
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
    """Over-matching is the safe direction, but it still must not break real calls.

    ``filter=api_key`` is the load-bearing case: the guard inspects parameter
    *names*, so the same text appearing as a value is none of its business.

    ``api+key`` is easy to misread: in form encoding ``+`` is a space, so it decodes to ``api key`` — a different
    parameter, not an obfuscated ``api_key``. Refusing it would be over-reach.
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
