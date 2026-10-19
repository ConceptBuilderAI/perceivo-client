"""Typed-response helpers (G-12).

The resource methods return raw parsed JSON (``Any``). Threading a typed model
onto *every* operation's return is capped by the served contract: ~46% of
operations have no typed response schema in ``openapi-v1.json`` (API-side,
tracked as gap **G-14**), so a per-method typed return can only be as complete
as the contract. Until then, the 119 generated models are wired here and any
response can be validated into one on demand::

    from perceivo_client import models, parse

    orch = parse(models.OrchestrationRead, client.orchestrations.get(oid))
    items = parse(models.OrchestrationRead, client.orchestrations.list()["items"])
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


def parse(model: type[M], data: Any) -> M | list[M]:
    """Validate a raw response into a generated model (or list of them).

    Passes a ``dict`` through ``model.model_validate``; maps a top-level
    ``list`` element-wise. Raises ``pydantic.ValidationError`` if the payload
    does not match the model.
    """
    if isinstance(data, list):
        return [model.model_validate(item) for item in data]
    return model.model_validate(data)
