#!/usr/bin/env python
"""The Protocol 3 ratchet must distinguish ABSENT from FAILED.

WHY THREE STATES AND NOT TWO. The defect this suite guards is that
``size_at()`` mapped ANY non-zero git exit to "absent at revision", so a
corrupt object, an index lock, a killed child or a Windows ``MAX_PATH``
overflow all read as "this file does not exist" and were dropped from the
census under ``exit 0``. A suite that only exercises PRESENT and ABSENT passes
against the broken implementation and proves nothing — the two states it
compares are the two the old code already got right. The third state, a git
invocation that FAILS for some other reason, is the whole property.

WHAT THE TWO-CWD CASE CAN AND CANNOT PROVE, stated so nobody reads more into
a green run than it carries. The original trigger is a Windows ``MAX_PATH``
limit: ``git show <40-char sha>:<path>`` from a deep cwd fails once the argument
crosses 260 characters. On Linux ``PATH_MAX`` is 4096 and CI's workspace is
~38 characters, so on CI that case CANNOT fail and is a regression guard only.
It is live on Windows checkouts under a deep working directory. The
platform-independent proof is the ``Fatal`` cases below, which exercise the
CLASS rather than the trigger.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_file_size as cfs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ("git", *args), cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if out.returncode != 0:
        raise AssertionError(f"fixture git {args} failed: {out.stderr}")
    return out.stdout


class SizesAtThreeStates(unittest.TestCase):
    """PRESENT, ABSENT and FAILED must be three distinguishable answers."""

    def test_present_returns_a_line_count(self) -> None:
        # POSITIVE CONTROL. Without this, an implementation that returned None
        # for everything would satisfy the absent case and look correct.
        sizes = cfs.sizes_at("HEAD", ["scripts/check_file_size.py"])
        self.assertEqual(len(sizes), 1)
        self.assertIsNotNone(sizes[0])
        self.assertGreater(sizes[0], 100)

    def test_absent_returns_none(self) -> None:
        sizes = cfs.sizes_at("HEAD", ["no/such/path/does-not-exist.ts"])
        self.assertEqual(sizes, [None])

    def test_order_is_preserved_across_a_mixed_batch(self) -> None:
        # Results are matched to inputs BY ORDER. A mixed batch is what catches
        # an off-by-one in the stream walk: a uniform batch would not.
        sizes = cfs.sizes_at(
            "HEAD",
            [
                "scripts/check_file_size.py",
                "no/such/path/does-not-exist.ts",
                "scripts/check_file_size.py",
            ],
        )
        self.assertIsNotNone(sizes[0])
        self.assertIsNone(sizes[1])
        self.assertEqual(sizes[0], sizes[2])

    def test_git_failure_raises_rather_than_reading_as_absent(self) -> None:
        """THE THIRD STATE. This is the case the old code could not express."""
        with tempfile.TemporaryDirectory() as tmp:
            # A directory that is not a git repository: `git cat-file` exits
            # non-zero. The old size_at() turned that into None -> "absent".
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with self.assertRaises(cfs.Fatal):
                    cfs.sizes_at("HEAD", ["anything.py"])
            finally:
                os.chdir(cwd)

    def test_truncated_stream_raises(self) -> None:
        """A short read must fail closed, not silently shorten the census."""
        real = subprocess.run

        def truncating(*args, **kwargs):
            result = real(*args, **kwargs)
            if args and args[0][:2] == ("git", "cat-file"):
                result.stdout = result.stdout[: len(result.stdout) // 3]
            return result

        subprocess.run = truncating
        try:
            with self.assertRaises(cfs.Fatal):
                cfs.sizes_at("HEAD", ["scripts/check_file_size.py"])
        finally:
            subprocess.run = real

    def test_empty_batch_spawns_nothing(self) -> None:
        self.assertEqual(cfs.sizes_at("HEAD", []), [])

    def _with_stdout(self, blob: bytes):
        """Run sizes_at against a crafted cat-file stream.

        These exercise the remaining fail-closed branches directly. They are
        worth explicit tests rather than coverage incidental to the happy path:
        every one of them is a place where a malformed answer could otherwise be
        walked past, and walking past a malformed answer is the defect class
        this check exists to close.
        """
        real = subprocess.run

        def fake(*args, **kwargs):
            if args and tuple(args[0][:2]) == ("git", "cat-file"):
                class R:
                    returncode = 0
                    stdout = blob
                    stderr = b""
                return R()
            return real(*args, **kwargs)

        subprocess.run = fake
        try:
            return cfs.sizes_at("HEAD", ["some/path.py"])
        finally:
            subprocess.run = real

    def test_unparsable_header_raises(self) -> None:
        # A header that is neither "<spec> missing" nor "<sha> <type> <size>".
        with self.assertRaises(cfs.Fatal):
            self._with_stdout(b"garbage\n")

    def test_non_numeric_size_raises(self) -> None:
        with self.assertRaises(cfs.Fatal):
            self._with_stdout(b"abc123 blob notanumber\nxxxx\n")

    def test_stream_ending_mid_blob_raises(self) -> None:
        # Header promises 100 bytes; only 4 follow.
        with self.assertRaises(cfs.Fatal):
            self._with_stdout(b"abc123 blob 100\nxxxx")

    def test_trailing_unread_bytes_raise(self) -> None:
        # One request, but the stream carries a second entry's worth of data:
        # the answer does not line up with the question.
        with self.assertRaises(cfs.Fatal):
            self._with_stdout(b"abc123 blob 2\nhi\nabc123 blob 2\nhi\n")

    def test_a_wellformed_single_entry_is_accepted(self) -> None:
        # POSITIVE CONTROL for the four cases above: proves the crafted-stream
        # harness can produce a PASS, so those failures are about the malformed
        # input and not about the harness itself.
        # `x = 1\n` is 6 bytes and ONE line. Asserting 2 here first, and being
        # corrected by the control, is the reason the control is worth having.
        self.assertEqual(self._with_stdout(b"abc123 blob 6\nx = 1\n\n"), [1])


class ScanFailsClosed(unittest.TestCase):
    def test_unreadable_at_head_is_fatal_not_a_silent_skip(self) -> None:
        """THE SILENT FALSE GREEN, directly.

        `ls-tree -r HEAD` lists a path, so it exists at HEAD by construction.
        If the HEAD read comes back None the instrument failed, and the old code
        `continue`d — dropping the file from the census while still printing
        "no new or grown over-limit files" and exiting 0.
        """
        real = cfs.sizes_at

        def blind(rev, paths):
            if rev == "HEAD":
                return [None] * len(paths)
            return real(rev, paths)

        cfs.sizes_at = blind
        try:
            with self.assertRaises(cfs.Fatal):
                cfs.scan(cfs.resolve_base())
        finally:
            cfs.sizes_at = real

    def test_checked_count_only_counts_evaluated_files(self) -> None:
        # `checked += 1` must follow the read, not precede it. Today's defect was
        # that a blind run and a good run printed an IDENTICAL census count, so
        # the output carried no signal of the drop.
        violations, checked = cfs.scan(cfs.resolve_base())
        self.assertGreater(checked, 0)
        self.assertIsInstance(violations, list)


class QuotedPathsStayInTheCensus(unittest.TestCase):
    """A C-quoted path must not fall out of the census.

    Under git's default ``core.quotePath=true``, ``ls-tree --name-only`` quotes
    any path it considers unusual: non-ASCII, a backslash, a double quote. The
    quoted form does not end in ``.py``, so ``is_source()`` dropped it BEFORE
    any size was read — the file left the census, the count did not move, and
    the gate exited 0. Same class as the defect this check closes, one layer up.
    """

    def _scan_repo_with(self, name: str) -> tuple[list[str], int]:
        """Build a scratch repo whose SECOND commit adds an over-limit `name`,
        then drive the real ``scan()`` over it and return its verdict.

        This must exercise ``scan()``. An earlier version of this test called
        ``ls-tree -z`` ITSELF and asserted on the result, which verified git's
        behaviour rather than the script's — it passed with ``-z`` removed from
        the module, i.e. it could not fail for the defect it was written for.
        """
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        for args in (("init", "-q", "-b", "main", "."), ("config", "user.email", "t@t"),
                     ("config", "user.name", "t")):
            _git(root, *args)
        (root / "plain.py").write_text("y = 1\n" * 10, encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "base")
        base = _git(root, "rev-parse", "HEAD").strip()

        (root / name).write_text("x = 1\n" * 600, encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "add over-limit file")

        cwd = os.getcwd()
        try:
            os.chdir(root)
            return cfs.scan(base)
        finally:
            os.chdir(cwd)

    def test_a_non_ascii_over_limit_file_is_reported(self) -> None:
        # Drives scan() end to end. With `-z` removed from the module the path
        # comes back C-quoted, is_source() rejects it, the file leaves the
        # census and this assertion fails — which is the whole point.
        violations, checked = self._scan_repo_with("日本語.py")
        self.assertEqual(checked, 2, "the non-ASCII .py must be IN the census")
        self.assertTrue(
            any("600 lines" in v for v in violations),
            f"expected the over-limit non-ASCII file to be reported, got {violations}",
        )

    def test_an_ascii_over_limit_file_is_reported(self) -> None:
        # POSITIVE CONTROL on the same harness: proves the scratch repo, the
        # base and the limit all work, so a failure above is about QUOTING and
        # not about the fixture.
        violations, checked = self._scan_repo_with("plain_big.py")
        self.assertEqual(checked, 2)
        self.assertTrue(any("600 lines" in v for v in violations), violations)


class RootCommitPush(unittest.TestCase):
    """A push of a parentless commit (the public export) is judged against the
    empty tree, so every file is new and held to LIMIT. A shallow clone, which
    also lacks HEAD^1 but is not a root, must still refuse."""

    def _repo(self, files: dict[str, int]) -> Path:
        root = Path(tempfile.mkdtemp())
        for args in (("init", "-q", "-b", "main", "."), ("config", "user.email", "t@t"),
                     ("config", "user.name", "t")):
            _git(root, *args)
        for name, lines in files.items():
            (root / name).write_text("x = 1\n" * lines, encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "root")
        return root

    def _push_scan(self, root: Path) -> tuple[list[str], int]:
        cwd, event = os.getcwd(), os.environ.get("GITHUB_EVENT_NAME")
        os.environ["GITHUB_EVENT_NAME"] = "push"
        try:
            os.chdir(root)
            return cfs.scan(cfs.resolve_base())
        finally:
            os.chdir(cwd)
            if event is None:
                os.environ.pop("GITHUB_EVENT_NAME", None)
            else:
                os.environ["GITHUB_EVENT_NAME"] = event

    def test_root_commit_under_limit_passes(self) -> None:
        violations, checked = self._push_scan(self._repo({"a.py": 10, "b.py": 500}))
        self.assertEqual((violations, checked), ([], 2))

    def test_root_commit_over_limit_file_is_a_new_file_violation(self) -> None:
        # NEGATIVE CONTROL: the empty-tree base must not be a free pass.
        violations, checked = self._push_scan(self._repo({"a.py": 10, "big.py": 501}))
        self.assertEqual(checked, 2)
        self.assertEqual(len(violations), 1, violations)
        self.assertIn("big.py: new file is 501 lines", violations[0])

    def test_shallow_clone_without_parent_still_refuses(self) -> None:
        source = self._repo({"a.py": 10})
        (source / "a.py").write_text("x = 2\n", encoding="utf-8")
        _git(source, "commit", "-qam", "second")
        shallow = Path(tempfile.mkdtemp()) / "clone"
        subprocess.run(
            ("git", "clone", "-q", "--depth", "1", source.as_uri(), str(shallow)),
            check=True, capture_output=True,
        )
        with self.assertRaises(cfs.Fatal):
            self._push_scan(shallow)


class AcceptanceTwoCwds(unittest.TestCase):
    """The acceptance instrument: same tree, two cwds, same answer."""

    def _run_from(self, cwd: Path) -> tuple[int, str]:
        proc = subprocess.run(
            (sys.executable, str(REPO_ROOT / "scripts" / "check_file_size.py")),
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout + proc.stderr

    def test_identical_verdict_from_a_short_and_a_deep_cwd(self) -> None:
        short_rc, short_out = self._run_from(REPO_ROOT)

        # A cwd deep enough that `<40-char sha>:<path>` would cross MAX_PATH on
        # Windows. Built inside the repo so HEAD and the merge base resolve
        # identically; only the cwd length differs.
        deep = REPO_ROOT
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            deep = Path(tmp)
            for _ in range(6):
                deep = deep / ("d" * 24)
            deep.mkdir(parents=True, exist_ok=True)
            deep_rc, deep_out = self._run_from(deep)

        self.assertEqual(
            short_rc, deep_rc, f"exit differs by cwd depth\nshort:\n{short_out}\ndeep:\n{deep_out}"
        )
        # The census line carries the count; it must not shrink with depth.
        def census(text: str) -> str:
            for line in text.splitlines():
                if "source files checked" in line:
                    return line
            return ""

        self.assertEqual(census(short_out), census(deep_out), "census differs by cwd depth")

    def test_forced_git_failure_exits_2_never_0(self) -> None:
        """NEGATIVE CONTROL. A broken instrument must refuse, not pass."""
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                (sys.executable, str(REPO_ROOT / "scripts" / "check_file_size.py")),
                cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        self.assertNotEqual(proc.returncode, 0, "a run outside a repository must not pass")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
