"""Reading OpenAPI documents and file trees, for ``regen.py``."""

from __future__ import annotations

import json
import os
from pathlib import Path

_OPERATION_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


class RegenError(Exception):
    """The tool could not do what was asked. main() turns this into exit 2."""


def _collect_refs(obj: object) -> set[str]:
    """Every ``#/components/schemas/<name>`` referenced anywhere in ``obj``."""
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if (
                key == "$ref"
                and isinstance(value, str)
                and value.startswith("#/components/schemas/")
            ):
                found.add(value.rsplit("/", 1)[1])
            else:
                found |= _collect_refs(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _collect_refs(item)
    return found


def _prune_orphan_schemas(spec: dict) -> None:
    """Drop component schemas no path reaches (transitively), so the vendored
    document and the generated models carry no types for filtered routes."""
    schemas: dict = spec.get("components", {}).get("schemas", {})
    if not schemas:
        return
    reachable = _collect_refs(spec.get("paths", {}))
    frontier = list(reachable)
    while frontier:
        name = frontier.pop()
        for ref in _collect_refs(schemas.get(name, {})):
            if ref not in reachable:
                reachable.add(ref)
                frontier.append(ref)
    for name in [n for n in schemas if n not in reachable]:
        del schemas[name]


def _count_operations(spec: dict) -> int:
    return sum(
        1
        for methods in spec["paths"].values()
        for method in methods
        if method.lower() in _OPERATION_METHODS
    )


def _parse_document(raw: bytes, label: str) -> dict:
    try:
        document = json.loads(raw.decode("utf-8"))
    except ValueError as exc:  # UnicodeDecodeError and JSONDecodeError are both ValueError
        raise RegenError(f"{label} is not UTF-8 JSON: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("paths"), dict):
        raise RegenError(f"{label} is not an OpenAPI document (no 'paths' object)")
    return document


def _spec_version(document: dict) -> str | None:
    """``info.version`` when the document declares one as a string."""
    info = document.get("info")
    version = info.get("version") if isinstance(info, dict) else None
    return version if isinstance(version, str) and version else None


def _read_upstream(source: str) -> bytes:
    """The bytes of the upstream document, a file in the current directory.

    The tool makes no network requests: download a published document first.
    ``source`` is a bare file name. A URL, a path with a directory part, or a
    name that resolves outside the current directory (a symbolic link) is refused.
    """
    if "://" in source:
        raise RegenError(
            f"the upstream document must be a local file, got {source!r}; download it first"
        )
    name = os.path.basename(source)
    if name != source or name in {"", ".", ".."}:
        raise RegenError(
            f"the upstream document must be a file name in the current directory, got {source!r}"
        )
    base = os.path.realpath(os.getcwd())
    target = os.path.realpath(os.path.join(base, name))
    if not target.startswith(base + os.sep):
        raise RegenError(f"the upstream document {source!r} resolves outside {base}")
    try:
        with open(target, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise RegenError(f"cannot read the upstream document {source}: {exc}") from exc


def _read_spec(spec_path: Path) -> bytes:
    try:
        return spec_path.read_bytes()
    except OSError as exc:
        raise RegenError(f"cannot read the spec {spec_path}: {exc}") from exc


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
