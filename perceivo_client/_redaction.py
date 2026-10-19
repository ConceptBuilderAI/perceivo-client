"""Keep secret-bearing response fields out of ``repr()`` and ``str()``.

Four generated response models carry a credential that a caller is meant to read
exactly once and store:

* ``UploadTargetResponse.upload_url`` -- a write SAS URL (``files.create_upload_url``)
* ``IngestTriggerRead.http_token`` -- a bearer token (``intelligence.create_trigger``
  and ``intelligence.update_trigger``)
* ``ServiceAccountCreated.key`` -- the plaintext service-account key
  (``service_accounts.create`` and ``service_accounts.rotate``)
* ``SecretValueRead.value`` -- a decrypted secret (``secrets.get_value``)

pydantic's default ``repr`` prints every field, so ``print(result)``, an f-string,
a traceback local or a structured logger would write the credential out in
clear. This module follows the pattern :class:`perceivo_client.auth.APICredentials`
uses for ``api_key``: the value is shown as ``<redacted>`` in ``repr()`` and
``str()`` and is otherwise untouched.

What is NOT changed, deliberately:

* **Attribute access.** ``result.upload_url`` returns the real value.
* **Serialisation.** ``model_dump()`` and ``model_dump_json()`` still carry the
  value, because callers need it -- to PUT to the SAS URL, to configure the
  trigger's caller, to store the key. Do not pass a dump of these models to a
  logger.
* A ``None`` value is shown as ``None``: there is nothing to hide, and an absent
  ``http_token`` (a trigger without ``http_enabled``) stays visible as absent.

Why here and not in the generated models: ``openapi/regen.py`` deletes and
rewrites ``perceivo_client/generated/models/`` on every regeneration, and
``regen.py --check`` byte-compares that tree with the generator's output, so a
hand edit there is both lost and reported as drift. This module lives outside
the regenerated tree and patches the classes when ``perceivo_client`` is
imported (every import path to ``perceivo_client.generated`` imports the
package first). If a regeneration renames or removes one of the fields,
:func:`install` raises at import, so the redaction cannot silently stop
applying.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel

from perceivo_client.generated.models import (
    IngestTriggerRead,
    SecretValueRead,
    ServiceAccountCreated,
    UploadTargetResponse,
)

#: model -> the fields whose values ``repr()``/``str()`` must not show.
REDACTED_FIELDS: dict[type[BaseModel], frozenset[str]] = {
    UploadTargetResponse: frozenset({"upload_url"}),
    IngestTriggerRead: frozenset({"http_token"}),
    ServiceAccountCreated: frozenset({"key"}),
    SecretValueRead: frozenset({"value"}),
}


class _Redacted:
    """Placeholder whose ``repr`` is ``<redacted>`` (so ``field=<redacted>``)."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<redacted>"


_REDACTED = _Redacted()


def _make_repr_args(fields: frozenset[str], original: Any) -> Any:
    def __repr_args__(self: BaseModel) -> Iterator[tuple[str | None, Any]]:
        for name, value in original(self):
            if name in fields and value is not None:
                yield name, _REDACTED
            else:
                yield name, value

    __repr_args__.__doc__ = (
        "Redact secret fields from repr()/str(); attributes and model_dump() are unchanged."
    )
    __repr_args__._perceivo_redacts = fields  # type: ignore[attr-defined]
    return __repr_args__


def install() -> None:
    """Patch ``__repr_args__`` on each model in :data:`REDACTED_FIELDS`.

    pydantic builds ``__repr__``, ``__str__``, ``__rich_repr__`` and
    ``__pretty__`` from ``__repr_args__``, so one override covers all of them.
    Idempotent. Raises ``RuntimeError`` if a field no longer exists on its model.
    """
    for model, fields in REDACTED_FIELDS.items():
        missing = sorted(fields - set(model.model_fields))
        if missing:
            raise RuntimeError(
                f"{model.__name__} no longer has secret field(s) {missing}; "
                "update perceivo_client/_redaction.py after regenerating the models"
            )
        current = model.__dict__.get("__repr_args__")
        if getattr(current, "_perceivo_redacts", None) == fields:
            continue
        model.__repr_args__ = _make_repr_args(fields, model.__repr_args__)  # type: ignore[method-assign]


install()
