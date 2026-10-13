"""Regenerate the perceivo-client typed models from an OpenAPI document.

The input is a spec FILE. By default it is the vendored document
``openapi/openapi-v1.json``; ``--spec PATH`` generates from any other file.
Every generated module names its source in its header: the spec's file name,
the ``info.version`` it declares (when it declares one) and the SHA-256 of its
bytes. Nothing else about where the document came from is recorded there.

Usage (from the repository root):

    pip install -e ".[codegen]"
    python openapi/regen.py                          # models from openapi/openapi-v1.json
    python openapi/regen.py --spec PATH              # models from another spec file
    python openapi/regen.py --check                  # committed models equal a fresh generation
    python openapi/regen.py --check --upstream SRC   # ... and the vendored spec is current
    python openapi/regen.py --check --release --upstream SRC   # release pull requests
    python openapi/regen.py --refresh --upstream SRC # re-vendor the spec, then regenerate

``SRC`` is a local copy of the API's published public OpenAPI document,
supplied by the operator as a file name in the current directory. The tool makes
no network requests and knows nothing about where that document is published.

**The vendored spec.** ``openapi-v1.json`` is the upstream public document with
one transform applied (``_to_customer_gateway_spec``): administrative,
marketplace and identity-provider routes are filtered out as defence in depth,
component schemas no remaining path reaches are pruned, and the result is
written as sorted, two-space-indented UTF-8 JSON with LF line endings. Paths
keep the ``/v1/...`` spelling the client calls.
``--refresh`` writes the vendored spec and ``openapi/spec_provenance.json``; it
is the only mode that writes either.

**The check.** ``--check`` regenerates into a temporary directory and
byte-compares the result with ``perceivo_client/generated/models/``, and
compares the spec's SHA-256 with the provenance. With ``--upstream`` it also
re-applies the transform to the supplied document and requires the result to
equal the vendored spec byte for byte. ``--release`` makes that leg mandatory.

Exit codes: 0 clean; 1 a difference was found; 2 the tool could not do what was
asked (bad arguments, an unreadable spec or upstream document, the generator or
one of its formatters -- black, isort -- missing or at a version other than the
recorded one). Nothing is reported as clean when the comparison did not run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent
SPEC_PATH = HERE / "openapi-v1.json"
PROVENANCE_PATH = HERE / "spec_provenance.json"
GENERATED_DIR = PKG_ROOT / "perceivo_client" / "generated"
# The generated models live in a PACKAGE (models/_partNN.py), not a single
# models.py. datamodel-code-generator emits one flat file; it is split into
# <=MAX_MODULE_LINES-line modules so that no generated file is unreviewably
# large. The package __init__ re-exports every model name and rebuilds forward
# references across the parts.
MODELS_PKG = GENERATED_DIR / "models"
MODELS_FLAT = GENERATED_DIR / "models.py"
MAX_MODULE_LINES = 480

EXIT_DIFFERENCE = 1
EXIT_UNUSABLE = 2

_GENERATOR_DIST = "datamodel-code-generator"
# The generator formats its output with these, so their versions decide bytes
# exactly as the generator's does.
_FORMATTER_DISTS = ("black", "isort")
_OPERATION_METHODS = frozenset({"get", "post", "put", "patch", "delete"})

# Inline schemas the generator would otherwise name first, ahead of the component
# schema whose name they take. It names classes in document order and inline
# enums after their title or field, so the grants schemas
# (CascadeApply, ChangeSet, ...) -- which sort before ``Operation`` and
# ``GroupMemberPrivileges`` -- took ``Operation`` from the operation-record model
# that ``client.operations`` returns and ``Privilege`` from the group privilege
# enum, renumbering both as ``Operation4`` and ``Privilege3``. Renaming the
# inline schemas leaves every component its own name. The keys are the
# generator's reference paths (fragment form, datamodel-code-generator 0.83.0);
# a key that stops matching restores the collision, which
# tests/test_generated_model_names.py fails on.
_ENUM = "#-datamodel-code-generator-#-enum-#-special-#"
_ARRAY = "#-datamodel-code-generator-#-array-#-special-#"
_ANY_OF_ARRAY = f"#-datamodel-code-generator-#-anyOf-#-special-#/0{_ARRAY}"
_MODEL_NAME_MAP = {
    f"#/components/schemas/CascadeApply/operation{_ENUM}": "CascadeApplyOperation",
    f"#/components/schemas/CascadeApplyResult/operation{_ENUM}": "CascadeApplyResultOperation",
    f"#/components/schemas/CascadeOperation/operation{_ENUM}": "CascadeOperationOperation",
    f"#/components/schemas/ChangeSet/operation{_ENUM}": "ChangeSetOperation",
    f"#/components/schemas/CascadeApply/privilege{_ANY_OF_ARRAY}": "CascadeApplyPrivilege",
    f"#/components/schemas/CascadeApply/privileges{_ANY_OF_ARRAY}{_ARRAY}/0{_ARRAY}": (
        "CascadeApplyPrivilegesItem"
    ),
    f"#/components/schemas/CascadeOperation/privilege{_ANY_OF_ARRAY}": "CascadeOperationPrivilege",
    # Inline field types the generator would otherwise name after the bare field
    # and then number in document order (``Name``, ``Name1`` ... ``Name11``,
    # ``Role1``). Those names are public through
    # ``perceivo_client.models``, say nothing about what they constrain, and
    # change meaning whenever the document reorders. Each is named after the
    # schema that owns the field instead: the owner's name followed by the
    # field's. Most owners keep their full name. Six drop a suffix that only
    # repeats the schema's role: ``Read`` (``GrantGranteeType``,
    # ``InvitationRole``, ``InvitationStatus``, ``MemberRole``,
    # ``MemberRoleChangeRole``), ``Item`` (``FileUploadStatus``) and ``V1``
    # (``RoleUpdateName``).
    # ``GrantCreateGranteeType`` keeps ``Create`` because ``GrantGranteeType``
    # already names the ``GrantRead`` field.
    f"#/components/schemas/AlertChannelUpdate/name{_ANY_OF_ARRAY}": "AlertChannelUpdateName",
    f"#/components/schemas/AlertRuleUpdate/name{_ANY_OF_ARRAY}": "AlertRuleUpdateName",
    f"#/components/schemas/CapabilityCopyRequest/new_name{_ANY_OF_ARRAY}": (
        "CapabilityCopyRequestNewName"
    ),
    f"#/components/schemas/CascadeOperation/privileges{_ANY_OF_ARRAY}": (
        "CascadeOperationPrivileges"
    ),
    f"#/components/schemas/CascadeOperation/privileges{_ANY_OF_ARRAY}{_ARRAY}/0{_ARRAY}": (
        "CascadeOperationPrivilegesItem"
    ),
    f"#/components/schemas/ComponentDefinitionValidate/manifest_yaml{_ANY_OF_ARRAY}": (
        "ComponentDefinitionValidateManifestYaml"
    ),
    f"#/components/schemas/CreateGraphConfigRequest/description{_ANY_OF_ARRAY}": (
        "CreateGraphConfigRequestDescription"
    ),
    f"#/components/schemas/ExperimentUpdate/name{_ANY_OF_ARRAY}": "ExperimentUpdateName",
    f"#/components/schemas/FileEntryUpdate/name{_ANY_OF_ARRAY}": "FileEntryUpdateName",
    f"#/components/schemas/FileUploadItem/status{_ENUM}": "FileUploadStatus",
    f"#/components/schemas/GrantCreate/grantee_type{_ENUM}": "GrantCreateGranteeType",
    f"#/components/schemas/GrantRead/grantee_type{_ENUM}": "GrantGranteeType",
    f"#/components/schemas/GrantUpdate/direct_privileges{_ANY_OF_ARRAY}": (
        "GrantUpdateDirectPrivileges"
    ),
    f"#/components/schemas/GroupUpdate/name{_ANY_OF_ARRAY}": "GroupUpdateName",
    f"#/components/schemas/InvitationRead/role{_ENUM}": "InvitationRole",
    f"#/components/schemas/InvitationRead/status{_ENUM}": "InvitationStatus",
    f"#/components/schemas/MemberInvite/role{_ENUM}": "MemberInviteRole",
    f"#/components/schemas/MemberRead/role{_ENUM}": "MemberRole",
    f"#/components/schemas/MemberRoleChangeRead/role{_ENUM}": "MemberRoleChangeRole",
    f"#/components/schemas/MemberRoleUpdate/role{_ENUM}": "MemberRoleUpdateRole",
    f"#/components/schemas/ModelRegisterRequest/name{_ANY_OF_ARRAY}": "ModelRegisterRequestName",
    f"#/components/schemas/NodepoolWrite/name{_ANY_OF_ARRAY}": "NodepoolWriteName",
    f"#/components/schemas/OrganizationUpdate/name{_ANY_OF_ARRAY}": "OrganizationUpdateName",
    f"#/components/schemas/RoleUpdateV1/name{_ANY_OF_ARRAY}": "RoleUpdateName",
    f"#/components/schemas/ScheduledTriggerUpdate/name{_ANY_OF_ARRAY}": (
        "ScheduledTriggerUpdateName"
    ),
    f"#/components/schemas/StorageSpaceUpdate/name{_ANY_OF_ARRAY}": "StorageSpaceUpdateName",
    f"#/components/schemas/ThreadCreate/title{_ANY_OF_ARRAY}": "ThreadCreateTitle",
    f"#/components/schemas/ThreadUpdate/title{_ANY_OF_ARRAY}": "ThreadUpdateTitle",
    f"#/components/schemas/TrainingConfigurationUpdate/name{_ANY_OF_ARRAY}": (
        "TrainingConfigurationUpdateName"
    ),
    f"#/components/schemas/TrainingGroupUpdate/name{_ANY_OF_ARRAY}": "TrainingGroupUpdateName",
}


class RegenError(Exception):
    """The tool could not do what was asked. main() turns this into exit 2."""


# Paths excluded from the customer surface, as defence in depth: the public
# document already omits them, and the filter keeps them out of the client even
# if a future document regains them. "/system/" is anchored with slashes so it
# does NOT match the customer "/files/system-zones/..." routes.
_EXCLUDE_PATH_MARKERS = ("/system/", "/marketplace", "microsoft", "service-principal")


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


def _to_customer_gateway_spec(spec: dict) -> dict:
    """Filter to the customer surface and prune orphaned schemas."""
    spec["paths"] = {
        path: item
        for path, item in spec.get("paths", {}).items()
        if not any(marker in path for marker in _EXCLUDE_PATH_MARKERS)
    }
    _prune_orphan_schemas(spec)
    return spec


def _serialise(spec: dict) -> str:
    """The vendored document's on-disk form (sorted keys, 2-space indent)."""
    return json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


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


def _vendored_bytes(upstream: bytes) -> tuple[bytes, dict]:
    """The vendored document, as bytes, that the upstream document transforms to."""
    spec = _to_customer_gateway_spec(_parse_document(upstream, "the upstream document"))
    return _serialise(spec).encode("utf-8"), spec


def _installed_generator() -> str:
    try:
        version = importlib.metadata.version(_GENERATOR_DIST)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RegenError(
            f'{_GENERATOR_DIST} is not installed. Run: pip install -e ".[codegen]"'
        ) from exc
    return f"{_GENERATOR_DIST}=={version}"


def _installed_formatters() -> list[str]:
    found = []
    for dist in _FORMATTER_DISTS:
        try:
            found.append(f"{dist}=={importlib.metadata.version(dist)}")
        except importlib.metadata.PackageNotFoundError as exc:
            raise RegenError(f'{dist} is not installed. Run: pip install -e ".[codegen]"') from exc
    return found


def _load_provenance() -> dict:
    try:
        return json.loads(PROVENANCE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise RegenError(f"cannot read {PROVENANCE_PATH}: {exc}") from exc


def _write_provenance(upstream: bytes, vendored: bytes, spec: dict) -> None:
    """Record what the refresh read and what it wrote. Only --refresh calls this.

    Every recorded value is derived from content, so the same upstream document
    writes the same file on every machine: no date, host, path or URL.
    """
    manifest = _load_provenance()
    manifest.setdefault("upstream", {}).update(
        sha256=hashlib.sha256(upstream).hexdigest(),
        version=_spec_version(spec),
    )
    manifest.setdefault("vendored", {}).update(
        sha256=hashlib.sha256(vendored).hexdigest(),
        paths=len(spec["paths"]),
        operations=_count_operations(spec),
    )
    manifest["generator"] = {
        "code_generator": _installed_generator(),
        "code_formatters": _installed_formatters(),
    }
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    PROVENANCE_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {PROVENANCE_PATH.name}")


def refresh_spec(source: str) -> None:
    """Transform the upstream document into the vendored spec and record the
    provenance of both."""
    upstream = _read_upstream(source)
    vendored, spec = _vendored_bytes(upstream)
    # Fail before writing anything, not after the spec moved.
    _installed_generator()
    _installed_formatters()
    SPEC_PATH.write_bytes(vendored)
    print(
        f"wrote {SPEC_PATH.name} ({len(spec['paths'])} paths, {_count_operations(spec)} operations)"
    )
    _write_provenance(upstream, vendored, spec)


def _file_header(spec_path: Path, spec_bytes: bytes) -> str:
    """The comment block at the top of every generated module.

    It names the spec by file name, declared version and content hash only. It
    is three lines whatever the spec declares: the line count decides where the
    package is split into parts.
    """
    version = _spec_version(_parse_document(spec_bytes, spec_path.name))
    declared = f", version {version}" if version else ""
    return (
        "# GENERATED CODE - DO NOT EDIT BY HAND.\n"
        "# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).\n"
        f"# Source: {spec_path.name}{declared}, sha256 {hashlib.sha256(spec_bytes).hexdigest()}"
    )


_INIT_TEMPLATE = """{header}
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


def _class_blocks(lines: list[str]) -> list[list[str]]:
    """Group the lines after the preamble into one block per top-level class."""
    blocks: list[list[str]] = []
    for line in lines:
        if line.startswith("class ") or not blocks:
            blocks.append([line])
        else:
            blocks[-1].append(line)
    return blocks


def _pack(blocks: list[list[str]], budget: int) -> list[list[list[str]]]:
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


def _split_into_package(text: str, header: str, models_pkg: Path | None = None) -> int:
    """Split datamodel-code-generator's flat models.py into a models/ package of
    <=MAX_MODULE_LINES-line _partNN.py modules. Returns the number of parts.

    ``models_pkg`` is where the package is written. The default is the
    committed package, which is reset first; --check passes a temporary
    directory and the committed tree is not touched."""
    in_place = models_pkg is None
    models_pkg = MODELS_PKG if in_place else models_pkg
    lines = text.splitlines(keepends=True)
    first_class = next(i for i, line in enumerate(lines) if line.startswith("class "))
    preamble = "".join(lines[:first_class]).rstrip("\n")
    preamble_line_count = preamble.count("\n") + 1

    parts = _pack(_class_blocks(lines[first_class:]), MAX_MODULE_LINES - preamble_line_count)

    # Reset the package directory (and remove any stale flat models.py).
    if in_place and MODELS_FLAT.exists():
        MODELS_FLAT.unlink()
    if models_pkg.exists():
        shutil.rmtree(models_pkg)
    models_pkg.mkdir(parents=True)

    names = [f"_part{i:02d}" for i in range(len(parts))]
    for name, part in zip(names, parts, strict=True):
        body = preamble + "\n\n\n" + "".join("".join(b) for b in part)
        body = body.rstrip("\n") + "\n"
        (models_pkg / f"{name}.py").write_text(body, encoding="utf-8", newline="\n")

    init = _INIT_TEMPLATE.format(
        header=header,
        imports="\n".join(f"from . import {n}" for n in names),
        parts_tuple=", ".join(names) + ("," if len(names) == 1 else ""),
    )
    (models_pkg / "__init__.py").write_text(init, encoding="utf-8", newline="\n")
    return len(parts)


def _read_spec(spec_path: Path) -> bytes:
    try:
        return spec_path.read_bytes()
    except OSError as exc:
        raise RegenError(f"cannot read the spec {spec_path}: {exc}") from exc


def generate_models(spec_path: Path | None = None, models_pkg: Path | None = None) -> None:
    """Generate the models package from ``spec_path`` (default: the vendored spec)."""
    spec_path = spec_path or SPEC_PATH
    _installed_generator()
    header = _file_header(spec_path, _read_spec(spec_path))
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    with tempfile.TemporaryDirectory() as tmp:
        flat = Path(tmp) / "models.py"
        cmd = [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            str(spec_path),
            "--input-file-type",
            "openapi",
            "--output",
            str(flat),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.11",
            "--use-standard-collections",
            "--use-union-operator",
            "--use-schema-description",
            "--field-constraints",
            "--snake-case-field",
            "--use-double-quotes",
            "--collapse-root-models",
            "--enum-field-as-literal",
            "one",
            "--disable-timestamp",
            "--model-name-map",
            json.dumps(_MODEL_NAME_MAP, sort_keys=True),
            "--custom-file-header",
            header,
        ]
        try:
            subprocess.run(cmd, check=True, env=env)
        except subprocess.CalledProcessError as exc:
            raise RegenError(f"{_GENERATOR_DIST} exited {exc.returncode}") from exc
        text = flat.read_text(encoding="utf-8")
    parts = _split_into_package(text, header, models_pkg)
    print(f"wrote {models_pkg or MODELS_PKG} ({parts} modules)")


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def _model_findings(regenerated: Path) -> list[str]:
    """Byte differences between a fresh generation and the committed package."""
    fresh, committed = _tree_bytes(regenerated), _tree_bytes(MODELS_PKG)
    if not fresh:
        raise RegenError(f"the generator wrote no files into {regenerated}")
    findings = [
        f"generated/models/{name}: committed, but the generator does not produce it"
        for name in sorted(committed.keys() - fresh.keys())
    ]
    findings += [
        f"generated/models/{name}: produced by the generator, but not committed"
        for name in sorted(fresh.keys() - committed.keys())
    ]
    for name in sorted(fresh.keys() & committed.keys()):
        if fresh[name] == committed[name]:
            continue
        note = ""
        if fresh[name] == committed[name].replace(b"\r\n", b"\n"):
            note = " (line endings only: the working tree holds CRLF, the generator writes LF)"
        findings.append(f"generated/models/{name}: differs from a fresh generation{note}")
    if MODELS_FLAT.exists():
        findings.append("generated/models.py: stale flat module beside the models/ package")
    return findings


def _upstream_findings(source: str, manifest: dict, vendored: bytes) -> list[str]:
    """Re-apply the transform to the supplied upstream document."""
    upstream = _read_upstream(source)
    findings = []
    digest = hashlib.sha256(upstream).hexdigest()
    if digest != manifest["upstream"]["sha256"]:
        findings.append(
            f"the upstream document's sha256 is {digest}; upstream.sha256 records "
            f"{manifest['upstream']['sha256']}"
        )
    if _vendored_bytes(upstream)[0] != vendored:
        findings.append(f"{SPEC_PATH.name} is not the transform of the upstream document")
    return findings


def _recorded(manifest: dict) -> tuple[list[str], str, tuple[int, int]]:
    """The provenance fields --check reads; a missing one is exit 2, not a pass."""
    try:
        generator, vendored = manifest["generator"], manifest["vendored"]
        manifest["upstream"]["sha256"]
        return (
            [generator["code_generator"], *generator["code_formatters"]],
            vendored["sha256"],
            (vendored["paths"], vendored["operations"]),
        )
    except (KeyError, TypeError) as exc:
        raise RegenError(f"spec_provenance.json lacks a field --check reads: {exc}") from exc


def check(spec_path: Path, upstream: str | None, release: bool) -> int:
    """Compare the committed tree with what the tool produces. Writes nothing."""
    if release and upstream is None:
        raise RegenError(
            "--check --release requires --upstream: the upstream leg is release "
            "evidence and is never skipped."
        )
    manifest = _load_provenance()
    recorded_tools, recorded_sha, recorded_counts = _recorded(manifest)
    installed = [_installed_generator(), *_installed_formatters()]
    if installed != recorded_tools:
        raise RegenError(
            f"the installed generator and formatters are {installed}; the provenance records "
            f"{recorded_tools}. A comparison across generator versions proves nothing."
        )
    vendored = _read_spec(spec_path)
    spec = _parse_document(vendored, spec_path.name)

    findings: list[str] = []
    digest = hashlib.sha256(vendored).hexdigest()
    if digest != recorded_sha:
        findings.append(
            f"{spec_path.name} sha256 is {digest}; vendored.sha256 records "
            f"{recorded_sha}. The spec was not written by --refresh."
        )
    counts = (len(spec["paths"]), _count_operations(spec))
    if counts != recorded_counts:
        findings.append(
            f"{spec_path.name} has {counts[0]} paths and {counts[1]} operations; "
            f"the provenance records {recorded_counts[0]} and {recorded_counts[1]}"
        )
    with tempfile.TemporaryDirectory() as tmp:
        regenerated = Path(tmp) / "models"
        generate_models(spec_path, regenerated)
        findings += _model_findings(regenerated)
    if upstream is not None:
        findings += _upstream_findings(upstream, manifest, vendored)

    legs = ["models", "spec_sha256"] + (["upstream"] if upstream is not None else [])
    if findings:
        for finding in findings:
            print(f"DIFFERENCE: {finding}", file=sys.stderr)
        print(f"check FAILED ({len(findings)} difference(s); legs: {', '.join(legs)})")
        return EXIT_DIFFERENCE
    print(
        f"check OK (legs: {', '.join(legs)}; {len(_tree_bytes(MODELS_PKG))} model files, "
        f"spec sha256 {digest})"
    )
    return 0


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--spec",
        default=None,
        help="The spec file to generate from. Default: the vendored openapi/openapi-v1.json.",
    )
    parser.add_argument(
        "--upstream",
        default=None,
        metavar="SRC",
        help=(
            "A local copy of the upstream public OpenAPI document: a file name in the "
            "current directory. "
            "Required with --refresh and --release."
        ),
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-vendor openapi/openapi-v1.json from --upstream, then regenerate.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Write nothing; exit 1 if the committed tree differs from a fresh generation.",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="With --check: require the upstream leg (--upstream).",
    )
    args = parser.parse_args(argv)
    if args.refresh and args.check:
        parser.error("--refresh and --check are mutually exclusive")
    if args.refresh and args.upstream is None:
        parser.error("--refresh requires --upstream <path>")
    if args.refresh and args.spec is not None:
        parser.error("--refresh writes the vendored spec; --spec cannot be combined with it")
    if args.upstream is not None and not (args.refresh or args.check):
        parser.error("--upstream is only meaningful with --refresh or --check")
    if args.release and not args.check:
        parser.error("--release is only meaningful with --check")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)  # argparse exits 2 on a usage error
    spec_path = Path(args.spec).resolve() if args.spec is not None else SPEC_PATH
    try:
        if args.check:
            return check(spec_path, args.upstream, args.release)
        if args.refresh:
            refresh_spec(args.upstream)
        else:
            print(f"using spec {spec_path.name}")
        generate_models(spec_path)
    except RegenError as exc:
        print(f"regen: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    return 0


if __name__ == "__main__":
    sys.exit(main())
