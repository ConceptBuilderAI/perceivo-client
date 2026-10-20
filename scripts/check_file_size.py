#!/usr/bin/env python
"""Protocol 3 ratchet — reject new over-limit source files and growth of existing ones.

Source files are capped at 500 lines. Before this check existed the cap was
enforced by nothing: a local pre-commit hook is configured but not installed in
any clone, is bypassable with ``--no-verify``, and covers Python only.

WHY THERE IS NO BASELINE FILE
-----------------------------
The obvious design is a checked-in list of grandfathered sizes. It is defeated by
regenerating that list from the PR branch: the entry becomes the grown value, it is
not above the file's real size and not under the limit, so every plausible tamper
check passes and the gate exits 0 while a file grew 595 -> 927 lines.

So the previous size is read from git instead. Restating it means rewriting the
merge base, which branch protection forbids and which is visible platform-wide.
There is nothing here to regenerate, nothing to date, and nothing to go stale.

Do NOT reintroduce a baseline file "for visibility". It recreates that defeat.

THE RULE
--------
    absent at base              -> must be <= LIMIT                  (new file)
    over LIMIT at base          -> must be <= its own size at base   (no growth; shrink fine)
    at or under LIMIT at base   -> must be <= LIMIT

CHOOSING THE BASE
-----------------
On a pull request the base is ``merge-base(<base ref>, HEAD)``, so a PR is judged
against its own starting point and never against growth someone else committed.

On a push to the default branch the base is ``HEAD^1``, the FIRST PARENT -- the
previous tip. Using ``merge-base`` there is degenerate: it resolves to HEAD itself,
every file satisfies ``now == then``, and the post-merge run exits 0 unconditionally
forever. That is worse than no gate, because it is believed. First parent also
catches the one failure a per-PR check structurally cannot see: a 450-line file
taken to 490 by two independently green PRs merges to 530.

``github.event.before`` is deliberately not used -- a force push rewrites it.

COUNTING
--------
Lines are counted as ``wc -l`` / ``git grep -c '^'`` do. PowerShell's
``Get-Content | Measure-Object -Line`` SILENTLY SKIPS BLANK LINES and under-reports
(measured: 4552 against a true 5446 -- 894 blank lines dropped). Any line-count
check built on it passes files well over the limit.

DRIFT
-----
``CANONICAL_SHA256`` detects LOCAL MODIFICATION of a vendored copy -- someone
editing this file in place to pass their PR. It is NOT a drift detector: a copy
that is never updated hashes to its own stale constant and self-checks green while
diverging from the canonical copy. Cross-copy drift is detected out-of-band.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

CHECKER_VERSION = "1.0.0"
# sha256 of this file with the CANONICAL_SHA256 assignment line excluded.
# Regenerate with: python scripts/check_file_size.py --print-hash
CANONICAL_SHA256 = "308c080602d9d7c7778c09cbd7c6d77c3ec4a940cf2598cc6a1589acf019e0d3"

LIMIT = 500
EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx")

# Generated, vendored, build and migration trees. These are not authored source.
# Stated here rather than in a glob so the census stays reproducible and auditable.
EXCLUDED_PREFIXES = ("alembic/versions/", "alembic/baseline/", "alembic_archive/")
EXCLUDED_SEGMENTS = (
    "node_modules/", "dist/", "build/", ".venv/", "venv/",
    "site-packages/", "__pycache__/", ".mypy_cache/",
)

_HASH_LINE = re.compile(r"^CANONICAL_SHA256\s*=.*$", re.MULTILINE)
_UNSTAMPED = "0" * 64


class Fatal(RuntimeError):
    """A condition under which the gate must refuse to run rather than pass."""


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        raise Fatal(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def git_ok(*args: str) -> bool:
    return subprocess.run(("git", *args), capture_output=True).returncode == 0


def self_hash(path: Path) -> str:
    body = _HASH_LINE.sub("CANONICAL_SHA256 = <redacted>", path.read_text(encoding="utf-8"), count=1)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def count_lines(blob: str) -> int:
    """Number of lines, matching ``wc -l`` / ``git grep -c '^'``."""
    if not blob:
        return 0
    return blob.count("\n") + (0 if blob.endswith("\n") else 1)


def is_source(path: str) -> bool:
    if not path.endswith(EXTENSIONS):
        return False
    if any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    padded = "/" + path
    return not any(f"/{segment}" in padded for segment in EXCLUDED_SEGMENTS)


def _merge_base(ref: str) -> str | None:
    for candidate in (f"origin/{ref}", ref):
        if git_ok("rev-parse", "--verify", candidate):
            base = git("merge-base", candidate, "HEAD").strip()
            if base:
                return base
    return None


def resolve_base() -> str:
    """The commit the working tree is judged against. Fails closed."""
    event = os.environ.get("GITHUB_EVENT_NAME", "")

    if event == "push":
        if not git_ok("rev-parse", "--verify", "HEAD^1"):
            # A ROOT COMMIT (the public export is one parentless commit) has no
            # previous tip, so judge it against the empty tree: every file is new
            # and must be <= LIMIT. That is stricter than any parent, not a pass.
            # A shallow clone also lacks HEAD^1 but is NOT a root, so it still fails.
            if git("rev-parse", "--is-shallow-repository").strip() == "false" and git(
                "rev-list", "--parents", "-n", "1", "HEAD"
            ).split() == [git("rev-parse", "HEAD").strip()]:
                empty = subprocess.run(
                    ("git", "hash-object", "-t", "tree", "--stdin"),
                    input=b"", capture_output=True,
                )
                if empty.returncode != 0:
                    raise Fatal(f"git hash-object of the empty tree failed: {empty.stderr!r}")
                return empty.stdout.decode("ascii").strip()
            raise Fatal(
                "HEAD has no first parent, so there is no previous tip to compare "
                "against. Refusing to report success on an unevaluated tree."
            )
        return git("rev-parse", "HEAD^1").strip()

    ref = os.environ.get("GITHUB_BASE_REF") or "dev" if event == "pull_request" else "dev"
    base = _merge_base(ref)
    if base:
        return base
    raise Fatal(
        f"cannot resolve the merge base against {ref!r}. A shallow clone breaks this; "
        "the job running this check must use actions/checkout with fetch-depth: 0."
    )


def rename_map(base: str) -> dict[str, str]:
    """new path -> path at ``base``, so a rename inherits its predecessor's size.

    Without this, renaming an over-limit file makes it "new" and forces the author
    to decompose it inside a rename PR. A large repository can hold hundreds of
    over-limit test files, so reorganising such a tree would demand hundreds of
    unrelated decompositions. Nothing is
    laundered: the growth rule still applies at the new path.
    """
    out = git("diff", "--find-renames", "--name-status", "--diff-filter=R", base, "HEAD")
    mapping: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].startswith("R"):
            mapping[parts[2]] = parts[1]
    return mapping


def sizes_at(rev: str, paths: list[str]) -> list[int | None]:
    """Line counts for many paths at one revision, in ONE git process.

    Returns one entry per input path, in order. ``None`` means git reported the
    blob GENUINELY ABSENT at that revision. Every other failure raises ``Fatal``.

    WHY THIS REPLACED ``git show`` PER PATH.
    The old helper was ``return None if result.returncode != 0``, which mapped
    ANY non-zero exit to "absent at revision". That is fail-OPEN on every
    platform: a corrupt object, an index lock, a killed child or an OOM each
    read as "this file does not exist", and the caller dropped the file from the
    census under exit 0. The census count did not move, because it was
    incremented before the read, so the output carried no signal of the drop.

    Windows ``MAX_PATH`` was only the TRIGGER that exposed it. ``git show
    <40-char sha>:<path>`` from a deep cwd fails with rc=128 ``Filename too
    long`` once the argument crosses 260 characters, which a deeply nested
    checkout reaches with an ordinary repository path. Passing paths
    on STDIN removes the command-line exposure entirely rather than mitigating
    it (``core.longpaths=true`` closes the trigger and leaves the class intact),
    and it drops one process spawn per source file — ~9,900 in the web client repository.

    ``git cat-file --batch`` answers a genuine miss with ``<spec> missing`` and
    anything else with a non-zero exit or a malformed stream, which is exactly
    the three-way distinction the old code could not make: PRESENT, ABSENT, and
    FAILED. Results are matched to inputs BY ORDER, never by parsing the spec
    back out of the header — a path may contain spaces, and re-parsing it would
    reintroduce a guess where git has given us a guarantee.
    """
    if not paths:
        return []

    # NUL-TERMINATED INPUT, not newline. A git path may legally contain a
    # newline, which would split one spec into two and desynchronise every
    # result after it — silently, because the walk would still produce one entry
    # per header it read. `--batch -z` removes that class outright.
    stdin = b"".join(f"{rev}:{path}".encode("utf-8") + b"\0" for path in paths)
    proc = subprocess.run(
        ("git", "cat-file", "--batch", "-z"), input=stdin, capture_output=True
    )
    if proc.returncode != 0:
        raise Fatal(
            f"git cat-file --batch failed at {rev} (rc={proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )

    out = proc.stdout
    sizes: list[int | None] = []
    pos = 0
    for path in paths:
        end = out.find(b"\n", pos)
        if end < 0:
            raise Fatal(
                f"git cat-file --batch produced a truncated stream at {rev}:{path}. "
                "Refusing to report a census that was not fully evaluated."
            )
        header = out[pos:end]
        pos = end + 1
        if header.endswith(b" missing"):
            sizes.append(None)
            continue
        fields = header.rsplit(b" ", 2)
        if len(fields) != 3:
            raise Fatal(f"unparsable cat-file header at {rev}:{path}: {header!r}")
        try:
            size = int(fields[2])
        except ValueError as exc:
            raise Fatal(f"unparsable cat-file size at {rev}:{path}: {header!r}") from exc
        blob = out[pos : pos + size]
        if len(blob) != size:
            raise Fatal(
                f"git cat-file --batch stream ended mid-blob at {rev}:{path}. "
                "Refusing to report a census that was not fully evaluated."
            )
        pos += size + 1  # blob, then git's trailing newline
        sizes.append(count_lines(blob.decode("utf-8", "replace")))

    if pos != len(out):
        raise Fatal(
            f"git cat-file --batch left {len(out) - pos} unread bytes at {rev}. "
            "The answer does not line up with the question; refusing to report it."
        )
    return sizes


def violation_for(path: str, now: int, then: int | None) -> str | None:
    """The whole rule, in one place, so it can be read without tracing the loop."""
    if then is None:
        if now > LIMIT:
            return f"{path}: new file is {now} lines, over the {LIMIT}-line limit"
    elif then > LIMIT:
        if now > then:
            return (
                f"{path}: grew {then} -> {now} lines. It is over the {LIMIT}-line limit "
                "already; it may shrink but must not grow."
            )
    elif now > LIMIT:
        return f"{path}: {then} -> {now} lines, crossing the {LIMIT}-line limit"
    return None


def scan(base: str) -> tuple[list[str], int]:
    renames = rename_map(base)
    # `--full-tree` IS LOAD-BEARING, and its absence was a second silent false
    # GREEN of the same class (caught by the two-cwd acceptance test). Without
    # it `ls-tree` is CWD-RELATIVE: run from `scripts/` the census
    # is 7 files instead of 5014, and from an empty subdirectory it is 0 — and in
    # every case the gate prints its census line and exits 0. CI happens to run
    # from the repository root, so the defect was invisible there. `git diff` is
    # NOT cwd-relative, so `rename_map` needs no equivalent.
    # `-z` IS LOAD-BEARING, and its absence was a THIRD silent false green of
    # the same class. Without it `ls-tree`
    # C-QUOTES any path git considers unusual under the default
    # `core.quotePath=true` — a non-ASCII name, a backslash, a double quote. A
    # 600-line `日本語.py` comes back as `"\346\227\245\346\234\254\350\252\236.py"`,
    # which does NOT end in `.py`, so `is_source()` filtered it out of the
    # candidate list BEFORE any size was read. The file left the census, the
    # count did not move, and the gate exited 0 — reproduced end to end.
    # `-z` emits raw NUL-separated paths, which also removes the newline-in-a-
    # filename case that `.splitlines()` would have mis-split.
    raw = git("ls-tree", "-r", "-z", "--full-tree", "--name-only", "HEAD")
    paths = [p for p in raw.split("\0") if p and is_source(p)]

    # Two batched reads rather than two process spawns per file.
    now_sizes = sizes_at("HEAD", paths)
    then_sizes = sizes_at(base, [renames.get(p, p) for p in paths])

    violations: list[str] = []
    checked = 0
    for path, now, then in zip(paths, now_sizes, then_sizes):
        # `ls-tree -r HEAD` JUST LISTED this path, so it exists at HEAD by
        # construction. `None` here cannot mean "absent" — it can only mean the
        # instrument failed — so it is Fatal rather than a `continue`. That is
        # the silent false GREEN this check exists to close: the old code
        # dropped such a file from the census and still printed
        # "no new or grown over-limit files" with exit 0.
        if now is None:
            raise Fatal(
                f"{path} is listed at HEAD but unreadable there. Refusing to report a "
                "census that skipped it."
            )
        # `then is None` IS legitimate: the file is new since base.
        checked += 1
        found = violation_for(path, now, then)
        if found:
            violations.append(found)
    return violations, checked


def verify_self(here: Path) -> bool:
    """False when this copy has been edited in place. Not a drift detector."""
    if CANONICAL_SHA256 == _UNSTAMPED:
        return True
    actual = self_hash(here)
    if actual == CANONICAL_SHA256:
        return True
    sys.stderr.write(
        "check_file_size.py has been modified locally.\n"
        f"  expected {CANONICAL_SHA256}\n  actual   {actual}\n"
        "This check refuses to run against an edited copy. If the change is intended, "
        "update CANONICAL_SHA256 (--print-hash) in the canonical copy and roll it out; "
        "do not edit one repository's copy in place.\n"
    )
    return False


def report(violations: list[str]) -> int:
    sys.stderr.write(f"\nProtocol 3: {len(violations)} violation(s).\n\n")
    for line in violations:
        sys.stderr.write(f"  {line}\n")
    sys.stderr.write(
        f"\nProtocol 3 caps source files at {LIMIT} lines. Existing over-limit files are "
        "grandfathered and may shrink; they may not grow, and no new file may cross the "
        "limit. Decompose the file rather than raising the limit.\n"
    )
    return 1


def main() -> int:
    here = Path(__file__).resolve()

    if "--print-hash" in sys.argv:
        sys.stdout.write(self_hash(here) + "\n")
        return 0

    if not verify_self(here):
        return 2

    try:
        base = resolve_base()
        violations, checked = scan(base)
    except Fatal as exc:
        sys.stderr.write(f"file-size ratchet could not run: {exc}\n")
        return 2

    sys.stdout.write(
        f"Protocol 3 ratchet v{CHECKER_VERSION}: {checked} source files "
        f"checked against {base[:12]}\n"
    )
    if violations:
        return report(violations)
    sys.stdout.write("Protocol 3: no new or grown over-limit files.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
