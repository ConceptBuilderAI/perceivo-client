"""Validate raw responses into the generated models."""

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
