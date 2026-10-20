"""Every component schema keeps its own name among the generated models.

datamodel-code-generator names classes in document order, and an inline schema
named after its title or field can take a component's name first; the
component is then renumbered (``Operation`` -> ``Operation4``) and the name a
caller imports is silently a different type. The grants schemas would do
exactly that to ``Operation`` and ``Privilege``; ``openapi/regen.py`` prevents it
with ``_MODEL_NAME_MAP``. This test fails on any such collision, including one a
future refresh introduces.

The same map names the inline field types the generator would otherwise call
after their bare field and number in document order (``Name1`` ... ``Name11``,
``Role1``, ``Body``). Every generated model is public through
``perceivo_client.models``, so the tests below also fail if a refresh brings a
numbered or bare generic name back, or if a map key stops matching.
"""

from __future__ import annotations

import enum
import importlib.util
import json
import pathlib
import re
import types
import typing

import pytest
from pydantic import BaseModel, RootModel

from perceivo_client.generated import models

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SPEC = _ROOT / "openapi" / "openapi-v1.json"
_SCHEMAS = json.loads(_SPEC.read_text(encoding="utf-8"))["components"]["schemas"]
_OBJECTS = sorted(name for name, schema in _SCHEMAS.items() if schema.get("properties"))


def _class_name(schema_name: str) -> str:
    """The generator's class name: ``Body_replace_x`` becomes ``BodyReplaceX``."""
    return "".join(part[:1].upper() + part[1:] for part in schema_name.split("_"))


def _is_union(annotation: object) -> bool:
    return typing.get_origin(annotation) in (typing.Union, types.UnionType)


def _field_names(model: type[BaseModel]) -> set[str]:
    return {field.alias or name for name, field in model.model_fields.items()}


@pytest.mark.parametrize("name", _OBJECTS)
def test_each_object_component_is_the_model_of_that_name(name):
    model = getattr(models, _class_name(name))

    assert isinstance(model, type)
    assert issubclass(model, BaseModel)
    if issubclass(model, RootModel) and _is_union(model.model_fields["root"].annotation):
        # A component declared as an ``anyOf`` next to its ``properties`` is a
        # root union: every branch must carry the component's whole field set.
        branches = typing.get_args(model.model_fields["root"].annotation)
        assert len(branches) == len(_SCHEMAS[name]["anyOf"])
        for branch in branches:
            assert issubclass(branch, BaseModel)
            assert _field_names(branch) == set(_SCHEMAS[name]["properties"])
    else:
        assert _field_names(model) == set(_SCHEMAS[name]["properties"])


def test_the_two_names_0_175_0_collided_on_are_the_component_types():
    """Pinned directly, because these two are the ones a caller already imports."""
    assert issubclass(models.Operation, BaseModel)
    assert "operation_type" in models.Operation.model_fields
    assert issubclass(models.Privilege, enum.Enum)
    assert models.Privilege("ADMIN_GROUP").value == "ADMIN_GROUP"


def _load_regen():
    spec = importlib.util.spec_from_file_location(
        "client_regen_model_names_test", _ROOT / "openapi" / "regen.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MODEL_NAME_MAP = _load_regen()._MODEL_NAME_MAP
_COMPONENT_CLASSES = frozenset(_class_name(name) for name in _SCHEMAS)
# Names the vendored document declares itself (``RoleReadV1``) are the API
# contract's to choose. Everything else in the namespace was named by the generator.
_INVENTED = sorted(set(models.__all__) - _COMPONENT_CLASSES)
_NUMBERED = re.compile(r"^[A-Za-z]+\d+$")
# A single field word says nothing about which schema's field it constrains.
_GENERIC = frozenset(
    {"Body", "Data", "Item", "Model", "Name", "Payload", "Role", "Status", "Title", "Type", "Value"}
)


@pytest.mark.parametrize("name", _INVENTED)
def test_no_generator_named_model_is_numbered_or_generic(name):
    assert not _NUMBERED.match(name), f"{name}: add a --model-name-map entry in openapi/regen.py"
    assert name not in _GENERIC, f"{name}: add a --model-name-map entry in openapi/regen.py"


def test_the_namespace_check_sees_the_generator_named_models():
    """Must-fail control: the population is non-empty and the patterns bite."""
    assert len(_INVENTED) > 50
    assert _NUMBERED.match("Name1")
    assert _NUMBERED.match("Privileges1")
    assert not _NUMBERED.match("Privileges1Item")
    assert "Body" in _GENERIC


@pytest.mark.parametrize("path", sorted(_MODEL_NAME_MAP))
def test_every_model_name_map_entry_names_an_exported_model(path):
    """A key that stops matching leaves its mapped name ungenerated."""
    name = _MODEL_NAME_MAP[path]

    assert name in models.__all__
    assert name not in _COMPONENT_CLASSES


@pytest.mark.parametrize(
    ("owner", "field", "name"),
    [
        ("AlertRuleUpdate", "name", "AlertRuleUpdateName"),
        ("TrainingGroupUpdate", "name", "TrainingGroupUpdateName"),
        ("MemberInvite", "role", "MemberInviteRole"),
        ("MemberRead", "role", "MemberRole"),
        ("InvitationRead", "status", "InvitationStatus"),
        ("GrantRead", "grantee_type", "GrantGranteeType"),
        ("CascadeOperation", "privileges", "CascadeOperationPrivileges"),
        ("CreateGraphConfigRequest", "description", "CreateGraphConfigRequestDescription"),
    ],
)
def test_a_mapped_name_is_the_type_of_the_field_it_was_mapped_from(owner, field, name):
    annotation = getattr(models, owner).model_fields[field].annotation

    assert getattr(models, name) in getattr(annotation, "__args__", (annotation,))
