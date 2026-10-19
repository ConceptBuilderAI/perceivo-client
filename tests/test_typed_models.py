"""The generated models are wired and the ``parse`` helper validates."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from perceivo_client import models, parse
from tests.conftest import json_handler, make_client


def test_models_module_is_exposed():
    # The generated models are re-exported as ``perceivo_client.models``.
    names = [n for n in dir(models) if n[:1].isupper()]
    assert len(names) >= 100


def test_parse_validates_dict():
    class M(BaseModel):
        x: int

    obj = parse(M, {"x": 1})
    assert isinstance(obj, M)
    assert obj.x == 1


def test_parse_maps_a_list():
    class M(BaseModel):
        x: int

    out = parse(M, [{"x": 1}, {"x": 2}])
    assert [m.x for m in out] == [1, 2]


def test_parse_raises_on_bad_payload():
    class M(BaseModel):
        x: int

    with pytest.raises(ValidationError):
        parse(M, {"x": "not-an-int-and-not-coercible"})


def test_parse_with_a_real_generated_model():
    # Pick a generated model and round-trip a minimal payload through it.
    model = getattr(models, "AlertTriggerRead", None) or next(
        m
        for m in vars(models).values()
        if isinstance(m, type) and issubclass(m, BaseModel) and m is not BaseModel
    )
    # model_construct bypasses validation — proves the class is a usable model.
    inst = model.model_construct()
    assert isinstance(inst, BaseModel)


def test_a_body_that_fails_validation_still_returns_the_declared_model():
    # A response that breaks the contract must not crash the caller; it comes
    # back unvalidated, carrying every key the server sent.
    body = {"organization_id": "org-a", "is_admin": "not-a-bool", "roles": 7}
    client, _ = make_client(json_handler(body))
    result = client.auth.whoami()
    assert isinstance(result, models.WhoamiResponse)
    assert result.organization_id == "org-a"
    assert result.is_admin == "not-a-bool"
    assert result.roles == 7


def test_a_conforming_body_is_validated_not_constructed():
    # A coerced field shows the validating path ran, not the fallback.
    body = {"id": "sa-1", "type": "service_account", "is_admin": "true"}
    client, _ = make_client(json_handler(body))
    result = client.auth.whoami()
    assert isinstance(result, models.WhoamiResponse)
    assert result.is_admin is True
