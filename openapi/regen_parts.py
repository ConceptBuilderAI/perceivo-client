"""Packing the generated flat ``models.py`` into ``_partNN`` modules.

Used by ``regen.py`` (which loads this file by path, so it runs both as a script
and when imported from elsewhere). Standard library only: the package
``__init__`` template, grouping of the generated lines into one block per
top-level class, packing those blocks into parts under a line budget, and the
imports each part needs from earlier parts.
"""

from __future__ import annotations

import re

INIT_TEMPLATE = """{header}
# This package is split into _partNN modules to stay under the file-size ratchet.
# Every model name is re-exported here; forward references that cross part
# boundaries are rebuilt below once all names are visible.
from __future__ import annotations

from enum import Enum as _Enum

from pydantic import BaseModel as _BaseModel

{imports}

_PARTS = ({parts_tuple})

_ns: dict = {{}}
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
"""


def class_blocks(lines: list[str]) -> list[list[str]]:
    """Group the lines after the preamble into one block per top-level class."""
    blocks: list[list[str]] = []
    for line in lines:
        if line.startswith("class ") or not blocks:
            blocks.append([line])
        else:
            blocks[-1].append(line)
    return blocks


def pack(blocks: list[list[str]], budget: int) -> list[list[list[str]]]:
    """Pack blocks, in order, into parts of at most ``budget`` lines each. A
    block longer than the budget gets a part of its own."""
    parts: list[list[list[str]]] = []
    used = 0
    for block in blocks:
        if parts and used + len(block) <= budget:
            parts[-1].append(block)
            used += len(block)
        else:
            parts.append([block])
            used = len(block)
    return parts


IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def class_name(block: list[str]) -> str | None:
    match = re.match(r"class ([A-Za-z_][A-Za-z0-9_]*)", block[0])
    return match.group(1) if match else None


def class_header(block: list[str]) -> str:
    """The ``class Name(<bases>):`` statement, which black may wrap over lines."""
    header: list[str] = []
    for line in block:
        header.append(line)
        if line.rstrip().endswith(":"):
            break
    return "".join(header)


def cross_part_imports(parts: list[list[list[str]]]) -> list[list[str]]:
    """For each part, the names its class statements need from earlier parts.

    Annotations are lazy (``from __future__ import annotations``) and the
    package ``__init__`` rebuilds them across parts, but a base-class expression
    such as ``RootModel[A | B]`` is evaluated when the class is defined. A name
    used there and defined in an earlier part is imported from that part; the
    generator orders classes so that such a name is never defined later.
    """
    defined_in: dict[str, int] = {}
    for index, part in enumerate(parts):
        for block in part:
            name = class_name(block)
            if name is not None:
                defined_in.setdefault(name, index)
    imports: list[list[str]] = []
    for index, part in enumerate(parts):
        needed: dict[int, set[str]] = {}
        for block in part:
            if class_name(block) is None:
                continue
            for token in IDENTIFIER.findall(class_header(block)):
                origin = defined_in.get(token)
                if origin is not None and origin < index:
                    needed.setdefault(origin, set()).add(token)
        imports.append(
            [
                f"from ._part{origin:02d} import {', '.join(sorted(names))}"
                for origin, names in sorted(needed.items())
            ]
        )
    return imports
