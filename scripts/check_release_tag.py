#!/usr/bin/env python3
"""Refuse a release tag that does not match the commit being released.

A tag is accepted when it is ``v`` followed by ``X.Y.Z`` or ``X.Y.ZrcN`` in
PEP 440 normal form, the version matches ``pyproject.toml`` and
``perceivo_client/_version.py``, the tag resolves to the release commit, that
commit is an ancestor of the given default-branch reference, and no community
file still carries a contact placeholder such as ``[SECURITY CONTACT EMAIL]``.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Final

#: ``X.Y.Z`` or ``X.Y.ZrcN``; every number is ``0`` or has no leading zero.
_NUMBER: Final = r"(?:0|[1-9][0-9]*)"
RELEASE_VERSION: Final = re.compile(rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}(?:rc{_NUMBER})?")
FULL_SHA: Final = re.compile(r"[0-9a-f]{40}")
#: A branch or remote-tracking reference name for ``--main-ref``.
REF_NAME: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*(?:/[A-Za-z0-9][A-Za-z0-9_.-]*)*")
#: An operand passed to git, optionally with the ``^{commit}`` peel.
GIT_OPERAND: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]*(?:\^\{commit\})?")


#: Files a release publishes whose contact details must be filled in.
CONTACT_FILES: Final = ("SECURITY.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "NOTICE")
#: An unfilled contact placeholder, for example ``[SECURITY CONTACT EMAIL]``.
CONTACT_PLACEHOLDER: Final = re.compile(r"\[[A-Z][A-Z ]* CONTACT[A-Z ]*\]")


class TagRejected(Exception):
    """The tag must not be released."""


def version_from_tag(tag: str) -> str:
    """Return the version a tag names, or raise if the tag is not normal form."""
    if not tag.startswith("v"):
        raise TagRejected(f"tag {tag!r} does not start with 'v'")
    version = tag[1:]
    if not RELEASE_VERSION.fullmatch(version):
        raise TagRejected(f"tag {tag!r} is not v<X.Y.Z> or v<X.Y.Z>rc<N> in PEP 440 normal form")
    return version


#: The module that carries the runtime ``__version__``.
VERSION_MODULE: Final = Path("perceivo_client") / "_version.py"


def module_version(root: Path) -> str:
    """Return the string literal assigned to ``__version__`` in ``VERSION_MODULE``."""
    tree = ast.parse((root / VERSION_MODULE).read_text(encoding="utf-8"))
    values = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(values) != 1:
        raise TagRejected(f"{VERSION_MODULE.as_posix()} has no single literal __version__")
    return values[0]


def declared_versions(root: Path) -> tuple[str, str]:
    """Return ``(pyproject version, _version.py version)`` as written in the tree."""
    with (root / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle).get("project", {})
    pyproject_version = project.get("version")
    if not isinstance(pyproject_version, str):
        raise TagRejected("pyproject.toml has no static [project].version")
    return pyproject_version, module_version(root)


def unfilled_placeholders(root: Path) -> list[str]:
    """Return ``file: placeholder`` for every contact placeholder left in ``CONTACT_FILES``."""
    found: list[str] = []
    for name in CONTACT_FILES:
        path = root / name
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            found.extend(f"{name}: {match}" for match in CONTACT_PLACEHOLDER.findall(text))
    return found


def _git(
    root: Path, subcommand: str, options: tuple[str, ...], operands: tuple[str, ...]
) -> subprocess.CompletedProcess[str]:
    """Run git with fixed options and validated operands after ``--end-of-options``."""
    safe_operands: list[str] = []
    for operand in operands:
        match = GIT_OPERAND.fullmatch(operand)
        if match is None or operand.startswith("-") or ".." in operand:
            raise TagRejected(f"refusing to pass {operand!r} to git")
        safe_operands.append(match.group(0))
    return subprocess.run(
        ["git", subcommand, *options, "--end-of-options", *safe_operands],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def _resolve_commit(root: Path, revision: str) -> str:
    completed = _git(root, "rev-parse", ("--verify", "--quiet"), (f"{revision}^{{commit}}",))
    sha = completed.stdout.strip()
    if completed.returncode or not FULL_SHA.fullmatch(sha):
        raise TagRejected(f"cannot resolve {revision!r} to a commit")
    return sha


def check_release_tag(root: Path, tag: str, commit: str, main_ref: str) -> str:
    """Validate ``tag`` for ``commit``; return the version on success."""
    version = version_from_tag(tag)
    pyproject_version, runtime_version = declared_versions(root)
    if pyproject_version != version:
        raise TagRejected(f"pyproject.toml version is {pyproject_version!r}, tag names {version!r}")
    if runtime_version != version:
        raise TagRejected(
            f"{VERSION_MODULE.as_posix()} version is {runtime_version!r}, tag names {version!r}"
        )
    placeholders = unfilled_placeholders(root)
    if placeholders:
        raise TagRejected(f"unfilled contact placeholders: {', '.join(placeholders)}")
    if not FULL_SHA.fullmatch(commit):
        raise TagRejected(f"commit {commit!r} is not a full 40-hex SHA")
    if not REF_NAME.fullmatch(main_ref) or ".." in main_ref:
        raise TagRejected(f"main ref {main_ref!r} is not a plain reference name")
    head = _resolve_commit(root, "HEAD")
    if head != commit:
        raise TagRejected(f"checked-out HEAD {head} is not the release commit {commit}")
    tagged = _resolve_commit(root, f"refs/tags/{tag}")
    if tagged != commit:
        raise TagRejected(f"tag {tag} points at {tagged}, not the release commit {commit}")
    main = _resolve_commit(root, main_ref)
    if _git(root, "merge-base", ("--is-ancestor",), (commit, main)).returncode != 0:
        raise TagRejected(f"commit {commit} is not an ancestor of {main_ref} ({main})")
    return version


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tag", required=True, help="the tag name, for example v1.0.0rc1")
    parser.add_argument("--commit", required=True, help="the full SHA being released")
    parser.add_argument("--main-ref", default="origin/dev")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        version = check_release_tag(args.root, args.tag, args.commit, args.main_ref)
    except (TagRejected, OSError, UnicodeError, SyntaxError, tomllib.TOMLDecodeError) as exc:
        print(f"release tag rejected: {exc}", file=sys.stderr)
        return 1
    print(f"release tag accepted: {args.tag} -> version {version} at {args.commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
