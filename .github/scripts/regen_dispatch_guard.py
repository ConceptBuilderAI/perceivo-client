"""Refuse a ``regenerate.yml`` target branch that must not receive regenerated models.

Refuses (case-insensitively) ``dev``, ``main``, the default branch, ``release``
and ``release/*``, ``refs/*`` and any name that is not a plain branch name, and
refuses a dispatch whose ref is not ``refs/heads/<branch>``. Reads
``REGEN_BRANCH``, ``REGEN_DEFAULT_BRANCH`` and ``REGEN_REF``; exits 1 with a
``::error::`` annotation on refusal.
"""

from __future__ import annotations

import os
import re
import sys

PROTECTED_BRANCHES = frozenset({"dev", "main"})
PROTECTED_PREFIXES = ("release/", "refs/")
_BRANCH_CHARS = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")


def refusal(branch: str, default_branch: str) -> str | None:
    """The reason ``branch`` must not be written, or ``None`` when it may be."""
    if not _BRANCH_CHARS.fullmatch(branch):
        return f"not a plain branch name: {branch!r}"
    if ".." in branch or "//" in branch or branch.endswith(("/", ".", ".lock")):
        return f"not a plain branch name: {branch!r}"
    folded = branch.casefold()
    if not default_branch.strip():
        return "the repository default branch is unknown, so it cannot be excluded"
    if folded in PROTECTED_BRANCHES or folded == default_branch.casefold():
        return f"{branch!r} is a shared branch; regenerate on a work branch and open a PR"
    if folded == "release" or folded.startswith(PROTECTED_PREFIXES):
        return f"{branch!r} is a release or fully-qualified ref; this workflow never writes one"
    return None


def ref_refusal(branch: str, ref: str) -> str | None:
    """The reason the dispatch ``ref`` does not match ``branch``, or ``None``."""
    if ref != f"refs/heads/{branch}":
        return (
            f"dispatched on {ref!r}, not 'refs/heads/{branch}'; "
            f"run it with --ref {branch} -f branch={branch}"
        )
    return None


def main() -> int:
    branch = os.environ.get("REGEN_BRANCH", "")
    default_branch = os.environ.get("REGEN_DEFAULT_BRANCH", "")
    ref = os.environ.get("REGEN_REF", "")
    reason = refusal(branch, default_branch) or ref_refusal(branch, ref)
    if reason is not None:
        print(f"::error::regenerate refused: {reason}")
        return 1
    print(f"regenerate target allowed: {branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
