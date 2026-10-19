#!/usr/bin/env python3
"""Verify built perceivo-client archives and make them reproducible.

``archives`` checks a built wheel and sdist against the git index of the tree
they were built from: every tracked ``perceivo_client/`` file is byte-identical
in both archives, ``py.typed``, ``LICENSE`` and ``NOTICE`` are present, and no
archive member is a cache artifact, an ``.env`` file or a recognisable secret.
``canonicalize-sdist``, ``canonicalize-wheel`` and ``compare-archives`` make and
prove a reproducible build.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path, PurePosixPath
from typing import Final

canonical_archives = import_module(
    "scripts.canonical_archives" if __package__ else "canonical_archives"
)
VerificationError = canonical_archives.VerificationError
canonicalize_sdist = canonical_archives.canonicalize_sdist
canonicalize_wheel = canonical_archives.canonicalize_wheel
_resolve_epoch = canonical_archives.resolve_epoch

PACKAGE: Final = "perceivo_client"
REGULAR_MODES: Final = {"100644", "100755"}
DENIED_PARTS: Final = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    "__pycache__",
}


@dataclass(frozen=True)
class IndexEntry:
    path: str
    mode: str
    object_id: str


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> bytes:
    completed = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", "replace").strip()[:500]
        raise VerificationError(f"git {' '.join(args[:4])} failed: {detail}")
    return completed.stdout


def _path(path: str) -> PurePosixPath:
    candidate = PurePosixPath(path)
    if not path or candidate.is_absolute() or "\\" in path:
        raise VerificationError(f"unsafe path: {path!r}")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise VerificationError(f"unsafe path segments: {path!r}")
    return candidate


def _index(root: Path) -> dict[str, IndexEntry]:
    raw = _git(root, "ls-files", "--stage", "-z")
    entries: dict[str, IndexEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, object_id, stage = metadata.decode("ascii").split()
        path = encoded_path.decode("utf-8", "strict")
        _path(path)
        if stage != "0" or path in entries:
            raise VerificationError(f"unmerged or duplicate index entry: {path}")
        if mode not in REGULAR_MODES:
            raise VerificationError(f"unsupported Git mode {mode} for {path}")
        entries[path] = IndexEntry(path, mode, object_id)
    return entries


def _denied_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Secret patterns that no archive member may contain."""
    return (
        ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
        ("storage account key", re.compile(r"\bAccountKey=[A-Za-z0-9+/=]{20,}")),
        ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    )


def _path_violation(path: str) -> str | None:
    candidate = _path(path)
    parts = {part.casefold() for part in candidate.parts}
    if parts.intersection(DENIED_PARTS) or candidate.name.casefold().startswith(".env"):
        return f"denied path: {path}"
    if candidate.suffix.casefold() in {".pyc", ".pyo"}:
        return f"denied cache artifact: {path}"
    return None


def _scan(path: str, data: bytes) -> None:
    violation = _path_violation(path)
    if violation:
        raise VerificationError(violation)
    if b"\0" in data:
        return
    text = data.decode("utf-8", "strict")
    for label, pattern in _denied_patterns():
        if pattern.search(text):
            raise VerificationError(f"{label} found in {path}")


def tracked_package(root: Path) -> dict[str, str]:
    """``{path: sha256}`` of every tracked ``perceivo_client/`` file, from the git index.

    The working bytes of each file must equal its indexed blob, and the tracked
    tree must hold a single top-level ``perceivo*`` package directory.
    """
    root = root.resolve(strict=True)
    index = _index(root)
    top_packages = {
        name.split("/", 1)[0]
        for name in index
        if name.casefold().startswith("perceivo") and "/" in name
    }
    if top_packages != {PACKAGE}:
        raise VerificationError(f"invalid package boundary: {sorted(top_packages)}")
    package: dict[str, str] = {}
    for name, entry in index.items():
        if not name.startswith(f"{PACKAGE}/"):
            continue
        data = root.joinpath(*_path(name).parts).read_bytes()
        if data != _git(root, "cat-file", "blob", entry.object_id):
            raise VerificationError(f"working bytes differ from tracked object: {name}")
        package[name] = _sha(data)
    if f"{PACKAGE}/py.typed" not in package:
        raise VerificationError("typed-package marker is absent")
    return package


def _record(members: dict[str, str], archive_name: str, name: str, data: bytes) -> None:
    if name in members:
        raise VerificationError(f"duplicate archive member in {archive_name}: {name}")
    _scan(name, data)
    members[name] = _sha(data)


def _wheel_members(path: Path) -> dict[str, str]:
    members: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        for zip_info in archive.infolist():
            if not zip_info.is_dir():
                name = _path(zip_info.filename).as_posix()
                _record(members, path.name, name, archive.read(zip_info))
    return members


def _sdist_member_bytes(
    archive: tarfile.TarFile, tar_info: tarfile.TarInfo, path: Path
) -> tuple[str, bytes]:
    if not tar_info.isfile():
        raise VerificationError(f"non-regular archive member in {path.name}: {tar_info.name}")
    parts = _path(tar_info.name).parts
    if len(parts) < 2:
        raise VerificationError(f"sdist member lacks root prefix: {tar_info.name}")
    extracted = archive.extractfile(tar_info)
    if extracted is None:
        raise VerificationError(f"cannot read archive member: {tar_info.name}")
    return PurePosixPath(*parts[1:]).as_posix(), extracted.read()


def _sdist_members(path: Path) -> dict[str, str]:
    members: dict[str, str] = {}
    with tarfile.open(path, "r:gz") as archive:
        for tar_info in archive.getmembers():
            if not tar_info.isdir():
                name, data = _sdist_member_bytes(archive, tar_info, path)
                _record(members, path.name, name, data)
    return members


def _archive_members(path: Path) -> dict[str, str]:
    if path.suffix == ".whl":
        return _wheel_members(path)
    if path.name.endswith(".tar.gz"):
        return _sdist_members(path)
    raise VerificationError(f"unsupported archive: {path}")


def verify_archives(root: Path, wheel: Path, sdist: Path) -> None:
    required_package = tracked_package(root)
    wheel_members = _archive_members(wheel)
    sdist_members = _archive_members(sdist)
    for name, digest in required_package.items():
        if wheel_members.get(name) != digest or sdist_members.get(name) != digest:
            raise VerificationError(f"package member missing or changed in archives: {name}")
    for members, label in ((wheel_members, "wheel"), (sdist_members, "sdist")):
        names = set(members)
        if f"{PACKAGE}/py.typed" not in names:
            raise VerificationError(f"py.typed absent from {label}")
        for legal in ("LICENSE", "NOTICE"):
            if not any(name == legal or name.endswith(f"/{legal}") for name in names):
                raise VerificationError(f"{legal} absent from {label}")
        if any(set(_path(name).parts).intersection(DENIED_PARTS) for name in names):
            raise VerificationError(f"private package path present in {label}")


def compare_archive_sets(first: Path, second: Path) -> None:
    def collect(directory: Path) -> dict[str, dict[str, str]]:
        archives = sorted([*directory.glob("*.whl"), *directory.glob("*.tar.gz")])
        return {path.name: _archive_members(path) for path in archives}

    left, right = collect(first), collect(second)
    if not left or left != right:
        raise VerificationError("archive member paths or hashes are not reproducible")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    subparsers = parser.add_subparsers(dest="command", required=True)
    archives = subparsers.add_parser("archives")
    archives.add_argument("--root", type=Path, default=Path("."))
    archives.add_argument("--wheel", type=Path, required=True)
    archives.add_argument("--sdist", type=Path, required=True)
    compare = subparsers.add_parser("compare-archives")
    compare.add_argument("--first", type=Path, required=True)
    compare.add_argument("--second", type=Path, required=True)
    for command in ("canonicalize-sdist", "canonicalize-wheel"):
        canonicalize = subparsers.add_parser(command)
        canonicalize.add_argument("--source", type=Path, required=True)
        canonicalize.add_argument("--output", type=Path, default=None)
        canonicalize.add_argument(
            "--epoch",
            type=int,
            default=None,
            help="source epoch in seconds; defaults to SOURCE_DATE_EPOCH",
        )
    return parser


def _in_workspace(path: Path) -> Path:
    """Resolve a command-line path and refuse one outside the working directory."""
    workspace = os.path.realpath(os.getcwd())
    resolved = os.path.realpath(path)
    if resolved != workspace and not resolved.startswith(workspace + os.sep):
        raise VerificationError(f"path is outside the working directory: {path}")
    return Path(resolved)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "archives":
            verify_archives(
                _in_workspace(args.root), _in_workspace(args.wheel), _in_workspace(args.sdist)
            )
        elif args.command in {"canonicalize-sdist", "canonicalize-wheel"}:
            rewrite = (
                canonicalize_sdist if args.command == "canonicalize-sdist" else canonicalize_wheel
            )
            output = None if args.output is None else _in_workspace(args.output)
            destination = rewrite(_in_workspace(args.source), _resolve_epoch(args.epoch), output)
            print(f"canonical {destination.name} sha256={_sha(destination.read_bytes())}")
        else:
            compare_archive_sets(_in_workspace(args.first), _in_workspace(args.second))
    except (VerificationError, OSError, UnicodeError) as exc:
        print(f"public tree rejected: {exc}", file=sys.stderr)
        return 1
    print(f"public {args.command} verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
