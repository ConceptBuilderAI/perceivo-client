"""Runs the Python blocks in ``docs/HMAC_REQUEST_SIGNING.md``.

Every ``python`` block carries an HTML comment on the line above its fence:
``<!-- runnable: ... -->`` blocks are executed in a subprocess against this
source tree, and ``<!-- illustrative: <reason> -->`` blocks, which need values
only the reader can supply, must compile.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "HMAC_REQUEST_SIGNING.md"

_FENCE = re.compile(r"^```(\w*)\s*$")
_RUNNABLE = re.compile(r"^<!--\s*runnable\b")
_ILLUSTRATIVE = re.compile(r"^<!--\s*illustrative:\s*(?P<reason>\S.*?)\s*-->\s*$")


class Block:
    """One fenced block, with the marker that governs it."""

    def __init__(self, index: int, language: str, line: int, source: str, marker: str):
        self.index = index
        self.language = language
        self.line = line
        self.source = source
        self.marker = marker

    @property
    def id(self) -> str:
        return f"b{self.index:02d}_L{self.line}"

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"<Block {self.id} {self.language}>"


def _blocks() -> list[Block]:
    lines = GUIDE.read_text(encoding="utf-8").split("\n")
    out: list[Block] = []
    index = 0
    cursor = 0
    while cursor < len(lines):
        opening = _FENCE.match(lines[cursor])
        if not opening:
            cursor += 1
            continue
        index += 1
        end = cursor + 1
        while end < len(lines) and not _FENCE.match(lines[end]):
            end += 1
        above = cursor - 1
        while above >= 0 and not lines[above].strip():
            above -= 1
        marker = lines[above].strip() if above >= 0 else ""
        out.append(
            Block(
                index=index,
                language=opening.group(1),
                line=cursor + 1,
                source="\n".join(lines[cursor + 1 : end]),
                marker=marker,
            )
        )
        cursor = end + 1
    return out


BLOCKS = _blocks()
PYTHON = [b for b in BLOCKS if b.language == "python"]
RUNNABLE = [b for b in PYTHON if _RUNNABLE.match(b.marker)]
ILLUSTRATIVE = [b for b in PYTHON if _ILLUSTRATIVE.match(b.marker)]


def test_the_guide_is_where_this_module_thinks_it_is() -> None:
    """The guide exists and has Python blocks."""
    assert GUIDE.is_file(), f"guide not found at {GUIDE}"
    assert PYTHON, f"no python blocks found in {GUIDE.name}; the parser is broken"


def test_every_python_block_declares_itself() -> None:
    """No block may be added without a decision about whether it runs."""
    undeclared = [
        f"{b.id}: marker={b.marker[:70]!r}"
        for b in PYTHON
        if not (_RUNNABLE.match(b.marker) or _ILLUSTRATIVE.match(b.marker))
    ]
    assert not undeclared, (
        f"every python block in {GUIDE.name} must carry a `runnable` or "
        f"`illustrative: <reason>` HTML comment on the line above its fence. "
        f"Undeclared: {undeclared}."
    )
    assert len(RUNNABLE) + len(ILLUSTRATIVE) == len(PYTHON)


def test_the_guide_still_carries_executable_content() -> None:
    """At least the known-answer and negative-vector blocks are runnable."""
    assert len(RUNNABLE) >= 2, (
        f"only {len(RUNNABLE)} runnable block(s) in {GUIDE.name}; the known-answer "
        "and negative-vector sections must stay runnable."
    )


@pytest.mark.parametrize("block", ILLUSTRATIVE, ids=lambda b: b.id)
def test_an_illustrative_block_still_compiles(block: Block) -> None:
    """An illustrative block has a reason and compiles."""
    match = _ILLUSTRATIVE.match(block.marker)
    assert match is not None
    reason = match.group("reason")
    assert len(reason) >= 12, f"{block.id}: `illustrative` needs a real reason, got {reason!r}"
    compile(block.source, f"{GUIDE.name}:{block.line}", "exec")


@pytest.mark.parametrize("block", RUNNABLE, ids=lambda b: b.id)
def test_a_runnable_block_runs(block: Block, tmp_path: Path) -> None:
    """The block runs verbatim in a fresh interpreter."""
    script = tmp_path / f"{block.id}.py"
    script.write_text(block.source, encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT), env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, str(script)],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"{GUIDE.name} block {block.id} (line {block.line}) exits "
        f"{result.returncode}.\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
