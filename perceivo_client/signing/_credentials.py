"""Signing credentials: the credential object and how it is resolved.

:class:`SigningCredentials` holds a key id, its signing secret and the audience it
signs for. :func:`resolve_signing_credentials` builds one from explicit arguments
and the environment. Import both from ``perceivo_client.signing``.

The signing secret is never logged, never included in an exception message and
never rendered by ``repr()``.
"""

from __future__ import annotations

import os
import re
from types import MemberDescriptorType

from perceivo_client.signing._constants import (
    ENV_KEY_ID,
    ENV_SIGNING_SECRET,
    SecretType,
)
from perceivo_client.signing._secret import secret_to_key_bytes
from perceivo_client.signing.canonical import (
    SigningError,
    canonical_audience,
    canonical_key_id,
)

__all__ = [
    "SigningCredentials",
    "resolve_signing_credentials",
]

# The form `canonical_key_id` produces. It is printable ASCII with no space or
# control character, so the key id is always a safe HTTP header value. Checked as
# a postcondition of normalisation.
_KEY_ID_RE = re.compile(r"\A[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def _validate_key_id(key_id: str | object) -> str:
    """Return the normalised key id, the form that is both signed and sent.

    Normalisation is delegated to
    :func:`~perceivo_client.signing.canonical.canonical_key_id`, so the
    ``X-Perceivo-Key-Id`` header is byte-identical to canonical field 3. The
    result is then checked against the expected UUID form, so a header value
    containing CR or LF can never be produced, whichever HTTP library sends it.
    """
    normalised = canonical_key_id(key_id)
    if not _KEY_ID_RE.match(normalised):  # pragma: no cover - unreachable by construction
        raise SigningError(
            "key_id did not normalise to the lowercase hyphenated UUID form; it is "
            "sent as an HTTP header value and signed as canonical field 3"
        )
    return normalised


class SigningCredentials:
    """A key id, its signing secret, and the audience it signs for.

    Instances are immutable, compare by value and are hashable. The secret is
    redacted from ``repr()`` and ``str()``.

    Args:
        key_id: The API key id, in any spelling :class:`uuid.UUID` accepts. It is
            stored in its normalised, lowercase, hyphenated form.
        signing_secret: The signing secret, as issued (64 hex characters) or as
            bytes. It is stored exactly as passed and converted to key bytes when
            a request is signed.
        audience: The deployment audience. Keyword-only and required.

    Raises:
        SigningError: If any argument is invalid.

    Security notes:
        The class is written without ``@dataclass`` so that
        :func:`dataclasses.asdict`, :func:`dataclasses.astuple`,
        :func:`dataclasses.fields` and :func:`dataclasses.replace` raise
        ``TypeError`` rather than copying the secret into a plain ``dict``. It
        uses ``__slots__``, so it has no ``__dict__`` for ``vars()`` or a generic
        object dumper to read.

        Two routes still reach the secret. ``signing_secret`` returns it as
        passed, because the signer reads it. Pickling preserves it, because
        ``__getstate__`` returns every slot so that ``pickle``,
        ``multiprocessing`` and ``copy.deepcopy`` produce a working credential.
        Do not pickle, serialise, or deepcopy and then log a
        ``SigningCredentials``.

        ``copy.deepcopy`` returns an independent credential: a secret held in a
        ``bytearray`` or ``memoryview`` is copied, so changing the original
        buffer does not change the key the copy signs with. ``copy.copy`` returns
        the same object.
    """

    __slots__ = ("audience", "key_id", "signing_secret")

    #: ``audience`` is keyword-only and is therefore not a positional match
    #: argument.
    __match_args__ = ("key_id", "signing_secret")

    def __init__(self, key_id: str, signing_secret: SecretType, *, audience: str) -> None:
        # The class is immutable, so attributes are assigned through
        # object.__setattr__.
        object.__setattr__(self, "key_id", _validate_key_id(key_id))
        object.__setattr__(self, "signing_secret", signing_secret)
        object.__setattr__(self, "audience", canonical_audience(audience))
        # Validates the secret's type and emptiness without retaining the result.
        secret_to_key_bytes(signing_secret)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"SigningCredentials is immutable; cannot set {name!r}")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"SigningCredentials is immutable; cannot delete {name!r}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SigningCredentials):
            return NotImplemented
        return (self.key_id, self.signing_secret, self.audience) == (
            other.key_id,
            other.signing_secret,
            other.audience,
        )

    def __hash__(self) -> int:
        return hash((self.key_id, self.signing_secret, self.audience))

    # Pickle and deepcopy support. An immutable class cannot be restored through
    # setattr, so __setstate__ assigns through object.__setattr__, as __init__
    # does. Validation is not repeated on restore: the state came from an instance
    # that already passed it.
    #
    # Slots are collected across the MRO, so a subclass that declares its own slots
    # still round-trips the base class's attributes. Reading the member descriptors
    # each class installed (rather than its `__slots__` declaration) handles a
    # bare-string `__slots__` and name-mangled private slots, and excludes
    # `__dict__` and `__weakref__`.
    def __getstate__(self) -> dict[str, object]:
        state: dict[str, object] = {}
        for klass in type(self).__mro__:
            for name, member in vars(klass).items():
                if not isinstance(member, MemberDescriptorType) or name in state:
                    continue
                try:
                    state[name] = getattr(self, name)
                except AttributeError:
                    # A slot that was never assigned stays unassigned on restore.
                    continue
        return state

    def __setstate__(self, state: dict[str, object]) -> None:
        for name, value in state.items():
            object.__setattr__(self, name, value)

    # A shallow copy of an immutable object is the object itself, as for `str` and
    # `tuple`. There is intentionally no `__deepcopy__`: deepcopy goes through
    # `__getstate__`/`__setstate__`, which copies a mutable secret buffer rather
    # than sharing it with the original.
    def __copy__(self) -> SigningCredentials:
        return self

    def __repr__(self) -> str:
        return (
            f"SigningCredentials(key_id={self.key_id!r}, signing_secret=<redacted>, "
            f"audience={self.audience!r})"
        )

    __str__ = __repr__


def resolve_signing_credentials(
    *,
    key_id: str | None = None,
    signing_secret: SecretType | None = None,
    audience: str | None = None,
) -> SigningCredentials | None:
    """Resolve signing credentials from arguments and the environment.

    ``key_id`` and ``signing_secret`` fall back to the ``PERCEIVO_KEY_ID`` and
    ``PERCEIVO_SIGNING_SECRET`` environment variables. ``audience`` has no
    environment fallback and no default: it must be passed explicitly, and must
    match the audience the deployment is configured with. A mismatched audience
    makes every signed request fail with a 401.

    Args:
        key_id: The API key id, or ``None`` to read ``PERCEIVO_KEY_ID``.
        signing_secret: The signing secret, or ``None`` to read
            ``PERCEIVO_SIGNING_SECRET``.
        audience: The deployment audience.

    Returns:
        The credentials, or ``None`` when neither a key id nor a signing secret
        is configured. Request signing is opt-in; an audience on its own does not
        enable it.

    Raises:
        SigningError: If the configuration is partial: a key id without a
            secret, a secret without a key id, or either without an audience.
    """
    resolved_id = key_id or os.environ.get(ENV_KEY_ID)
    resolved_secret = signing_secret or os.environ.get(ENV_SIGNING_SECRET)
    resolved_audience = audience
    if not resolved_id and not resolved_secret:
        return None
    if not resolved_id:
        raise SigningError(
            f"a signing secret was configured without a key id; set key_id=... or {ENV_KEY_ID}"
        )
    if not resolved_secret:
        raise SigningError(
            "a key id was configured without a signing secret; set signing_secret=... "
            f"or {ENV_SIGNING_SECRET}"
        )
    if not resolved_audience:
        raise SigningError(
            "signing credentials were configured without an audience; pass audience=..., "
            "for example 'perceivo-api-prod', matching the audience of the deployment you "
            "are calling. The audience has no environment variable and is never derived "
            "from a hostname or base_url."
        )
    return SigningCredentials(
        key_id=resolved_id, signing_secret=resolved_secret, audience=resolved_audience
    )
