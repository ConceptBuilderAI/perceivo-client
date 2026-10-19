"""The published guide's Python blocks are executed, not just read.

``docs/HMAC_REQUEST_SIGNING.md`` is the copy-pasteable instruction a third-party
server implementer follows. Nothing in this repository had ever run a line of it.

That is not a hypothetical gap. Revision 3 added two negative vectors, and one of
them -- ``n07-organization-metadata-unbound`` -- is the single row the reference
verifier **accepts** by design, because it takes no request and so cannot
re-derive field 9 to compare against what the edge received. The guide's own prose
three paragraphs above the block says exactly that. The block still looped over
*every* negative asserting ``not verify_signed_request(...)``, so the published
snippet failed against the table published in the same commit, with an
``AssertionError`` naming ``n07`` and exit code 1. Every test in the tree stayed
green, because no test ran it.

The reader it misleads is the one the document exists for. Faced with a failing
assertion they either delete it -- losing the ``n01``-``n06`` coverage that is the
point of the section -- or "fix" the verifier by refusing ``n07`` in a prelude,
which is precisely the pre-MAC comparison of two client-asserted values that
section 6 rule 8 forbids. The document would have taught the vulnerability it was
written to close.

Gate 5 states the rule this module enforces: *a document may not carry SQL,
scripts, queries, manifests, or commands that have never been executed.*

**Every** ``python`` block must declare itself, in an HTML comment on the line
above its fence:

``<!-- runnable: ... -->``
    Executed here in a subprocess against the installed ``perceivo_client``.
    A non-zero exit fails this suite.

``<!-- illustrative: <reason> -->``
    Not executed, because it contains something only the reader can supply -- a
    secret, a key id, their own verifier body. It must still *compile*, so a
    syntax error cannot ship, and the reason is required so the exemption is a
    decision on the record rather than an omission.

An unmarked block fails :func:`test_every_python_block_declares_itself`. That is
the part that matters: without it the next block added to this guide is untested
by default, which is how this defect arrived.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

GUIDE = Path(__file__).resolve().parents[1] / "docs" / "HMAC_REQUEST_SIGNING.md"

_FENCE = re.compile(r"^```(\w*)\s*$")
_RUNNABLE = re.compile(r"^<!--\s*runnable\b")
_ILLUSTRATIVE = re.compile(r"^<!--\s*illustrative:\s*(?P<reason>\S.*?)\s*-->\s*$")


class Block:
    """One fenced block, with the marker that governs it."""

    def __init__(self, index: int, language: str, line: int, source: str, marker: str):
        self.index = index
        self.language = language
        self.line = line  # 1-based line of the opening fence
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
        # The marker is the nearest non-blank line above the fence.
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
    """A moved or renamed guide must fail loudly, not silently test nothing.

    Every other assertion here is a loop over ``PYTHON``. An empty list satisfies
    all of them, so a guide this module could not find would report a clean suite
    over zero blocks -- the exact shape of vacuity this module exists to answer.
    """
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
        f"Undeclared: {undeclared}. An unmarked block is untested by default, "
        "which is how the section 7 snippet came to fail against the table "
        "published in the same commit."
    )
    assert len(RUNNABLE) + len(ILLUSTRATIVE) == len(PYTHON)


def test_the_guide_still_carries_executable_content() -> None:
    """Marking every block illustrative must not be a way to switch this off."""
    assert len(RUNNABLE) >= 2, (
        f"only {len(RUNNABLE)} runnable block(s) in {GUIDE.name}. The known-answer "
        "section and the negative-vector section are both executable and must stay "
        "that way; downgrading one to `illustrative` disables the control rather "
        "than satisfying it."
    )


@pytest.mark.parametrize("block", ILLUSTRATIVE, ids=lambda b: b.id)
def test_an_illustrative_block_still_compiles(block: Block) -> None:
    """Not executed is not the same as not checked."""
    match = _ILLUSTRATIVE.match(block.marker)
    assert match is not None
    reason = match.group("reason")
    assert len(reason) >= 12, f"{block.id}: `illustrative` needs a real reason, got {reason!r}"
    compile(block.source, f"{GUIDE.name}:{block.line}", "exec")


@pytest.mark.parametrize("block", RUNNABLE, ids=lambda b: b.id)
def test_a_runnable_block_runs(block: Block, tmp_path: Path) -> None:
    """Verbatim, in a subprocess, against the installed distribution.

    Verbatim matters: a block re-typed into this file is a copy that can agree
    with the code while the published one does not. The bytes executed here are
    the bytes a reader copies.

    A subprocess matters too -- these blocks bind module-level names and call
    ``load_golden_vectors``, and running them in-process would let one block's
    state satisfy another's assertion.
    """
    script = tmp_path / f"{block.id}.py"
    script.write_text(block.source, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"{GUIDE.name} block {block.id} (line {block.line}) exits "
        f"{result.returncode}. This block is published as copy-pasteable "
        f"instruction; a reader running it sees this.\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
