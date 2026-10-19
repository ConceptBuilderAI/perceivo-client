# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d
# This package is split into _partNN modules to stay under the file-size ratchet.
# Every model name is re-exported here; forward references that cross part
# boundaries are rebuilt below once all names are visible.
from __future__ import annotations

from enum import Enum as _Enum

from pydantic import BaseModel as _BaseModel

from . import _part00
from . import _part01
from . import _part02
from . import _part03
from . import _part04
from . import _part05
from . import _part06
from . import _part07
from . import _part08
from . import _part09
from . import _part10
from . import _part11
from . import _part12
from . import _part13
from . import _part14
from . import _part15
from . import _part16
from . import _part17
from . import _part18
from . import _part19
from . import _part20
from . import _part21
from . import _part22

_PARTS = (_part00, _part01, _part02, _part03, _part04, _part05, _part06, _part07, _part08, _part09, _part10, _part11, _part12, _part13, _part14, _part15, _part16, _part17, _part18, _part19, _part20, _part21, _part22)

_ns: dict = {}
for _mod in _PARTS:
    for _k, _v in vars(_mod).items():
        if not _k.startswith("_"):
            _ns[_k] = _v

# Make every model name resolvable from every part module's globals, so
# model_rebuild() (which evaluates string annotations against the model's own
# module namespace) can resolve references that live in a different part.
for _mod in _PARTS:
    _mod.__dict__.update(_ns)

globals().update(_ns)

_PKG = __name__ + "."


def _is_generated(_v: object) -> bool:
    return isinstance(_v, type) and getattr(_v, "__module__", "").startswith(_PKG)


for _obj in list(_ns.values()):
    if _is_generated(_obj) and issubclass(_obj, _BaseModel):
        _obj.model_rebuild(force=True)

__all__ = sorted(
    _k for _k, _v in _ns.items()
    if _is_generated(_v) and issubclass(_v, (_BaseModel, _Enum))
)
