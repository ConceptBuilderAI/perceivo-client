"""Every TypedDict the client exposes validates under pydantic on Python 3.11.

pydantic refuses ``typing.TypedDict`` before 3.12, so the client uses the
``typing_extensions`` backport.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest
from pydantic import TypeAdapter
from typing_extensions import is_typeddict

import perceivo_client


def _typed_dicts():
    found = []
    for mod in pkgutil.walk_packages(perceivo_client.__path__, "perceivo_client."):
        module = importlib.import_module(mod.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module.__name__ and is_typeddict(obj):
                found.append(obj)
    return found


TYPED_DICTS = _typed_dicts()


def test_typed_dicts_are_discovered():
    names = {cls.__name__ for cls in TYPED_DICTS}
    assert {"BillingUsageEntriesPage", "ExportListResponse"} <= names


@pytest.mark.parametrize("cls", TYPED_DICTS, ids=lambda c: f"{c.__module__}.{c.__name__}")
def test_typed_dict_is_backport_and_builds_a_type_adapter(cls):
    assert type(cls).__module__ != "typing"
    TypeAdapter(cls)
