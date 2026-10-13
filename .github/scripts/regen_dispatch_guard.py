"""Refuse a ``regenerate.yml`` target branch that must never receive regenerated models.

``.github/workflows/regenerate.yml`` regenerates ``perceivo_client/generated/models/``
in a runner and commits the result to a branch named by a ``workflow_dispatch``
input. The workflow token can push to any unprotected branch, so the input is the
only thing standing between "regenerate my work branch" and "commit to a shared
one". This guard is that gate. It runs in its own read-only job, and every job
that writes ``needs:`` it.

Refused, compared case-insensitively (a branch spelled ``Dev`` or ``RELEASE/x``
is refused rather than treated as distinct):

* ``dev``, ``main`` and the repository's default branch;
* ``release`` and anything under ``release/``;
* anything under ``refs/`` -- ``refs/heads/dev`` would otherwise reach ``dev``;
* any name that is not a plain branch name: empty, leading ``-`` or ``.``, a
  ``..`` or ``//`` sequence, a trailing ``/``, ``.`` or ``.lock``, or a character
  outside ``[A-Za-z0-9._/-]``.

It also refuses a dispatch whose ref is not ``refs/heads/<branch>``. The
workflow runs on the dispatched ref and checks out that commit, so requiring the
two to agree keeps branch code in the branch's own Actions cache scope; run on
``--ref dev`` it would execute in the default branch's scope, where an entry it
saved would be restored by every other run (CodeQL
``actions/cache-poisoning/poisonable-step``). The comparison is exact and
case-sensitive, because a ref is.

Exit codes: 0 allowed; 1 refused (the reason is printed as a GitHub ``::error::``
annotation). Inputs come from the environment, never from interpolation into a
shell line: ``REGEN_BRANCH``, ``REGEN_DEFAULT_BRANCH`` and ``REGEN_REF``.
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
