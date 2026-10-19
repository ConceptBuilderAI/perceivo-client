"""Keep secret-bearing response fields out of ``repr()`` and ``str()``.

The affected generated models show these values as ``<redacted>``. Attribute
access and ``model_dump()`` still return the real value.
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
    Idempotent. Raises ``RuntimeError`` if a listed field is missing from its model.
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
