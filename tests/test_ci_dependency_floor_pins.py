"""The dependency-floor CI job must test the floors ``pyproject.toml`` declares.

``.github/workflows/ci.yml`` installs exact versions before force-reinstalling the
wheel with ``--no-deps``. Those exact versions are the *claim* that the declared
floors work. Nothing in the workflow binds them to ``pyproject.toml``: lowering a
declared floor (``httpx>=0.27.0`` to ``httpx>=0.26.0``) leaves the job pinning
``0.27.0``, so CI stays green while the floor it advertises is never exercised,
and the first person to install at the advertised floor is the one who finds out.

This test parses both sides and asserts equality. It reads ``.github/``, which a
source distribution does not ship, so it is excluded from the sdist by
``MANIFEST.in`` and from the roster in ``test_signing_sdist_packaging.py``.
"""

from __future__ import annotations

import pathlib
import re
import tomllib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

#: ``name>=version`` with nothing else: an extras marker, an environment marker or
#: an upper bound would change what "the floor" means, so this pattern refuses
#: them rather than guessing.
_REQUIREMENT = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)>=(?P<floor>[0-9][0-9A-Za-z.]*)$")

#: The line in the workflow that pins the floors, e.g.
#: ``'pydantic==2.10.0' 'httpx==0.27.0' \``.
_PIN = re.compile(r"'(?P<name>[A-Za-z0-9._-]+)==(?P<version>[0-9][0-9A-Za-z.]*)'")


def declared_floors(pyproject_text: str) -> dict[str, str]:
    """Runtime dependency floors as ``pyproject.toml`` declares them."""
    metadata = tomllib.loads(pyproject_text)
    dependencies = metadata["project"]["dependencies"]
    assert dependencies, "pyproject declares no runtime dependencies; the check is vacuous"
    floors: dict[str, str] = {}
    for requirement in dependencies:
        match = _REQUIREMENT.fullmatch(requirement.strip())
        assert match is not None, (
            f"runtime requirement {requirement!r} is not a bare `name>=floor`. The "
            "dependency-floor job installs one exact version per dependency, so a "
            "marker or an upper bound has to be reflected there deliberately."
        )
        floors[match["name"].lower().replace("_", "-")] = match["floor"]
    return floors


def workflow_floor_pins(workflow_text: str) -> dict[str, str]:
    """Exact versions the ``dependency-floor`` job installs before the wheel."""
    lines = [line for line in workflow_text.splitlines() if _PIN.search(line)]
    assert len(lines) == 1, (
        "expected exactly one quoted `name==version` pin line in ci.yml, found "
        f"{len(lines)}: {lines}. The parser, not the workflow, is what is wrong "
        "if the pins legitimately moved."
    )
    return {
        match["name"].lower().replace("_", "-"): match["version"]
        for match in _PIN.finditer(lines[0])
    }


def test_the_floor_job_installs_exactly_the_declared_floors():
    floors = declared_floors(PYPROJECT.read_text(encoding="utf-8"))
    pins = workflow_floor_pins(WORKFLOW.read_text(encoding="utf-8"))

    assert pins == floors, (
        "the dependency-floor CI job does not install the floors pyproject "
        f"declares. pyproject: {floors}; ci.yml: {pins}. Whichever side moved, "
        "the job is no longer testing the floor the package advertises."
    )


@pytest.mark.parametrize(
    ("side", "before", "after"),
    [
        ("pyproject", '"httpx>=0.27.0"', '"httpx>=0.26.0"'),
        ("workflow", "'httpx==0.27.0'", "'httpx==0.26.9'"),
    ],
)
def test_the_check_fails_when_either_side_moves_alone(side: str, before: str, after: str):
    """Mutation control: a check that cannot fail is not a check.

    Both mutations are applied in memory, never on disk.
    """
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    if side == "pyproject":
        assert before in pyproject_text, before
        pyproject_text = pyproject_text.replace(before, after, 1)
    else:
        assert before in workflow_text, before
        workflow_text = workflow_text.replace(before, after, 1)

    assert declared_floors(pyproject_text) != workflow_floor_pins(workflow_text)


def test_every_declared_dependency_is_pinned_somewhere_in_the_job():
    """A dependency dropped from the pin line must not pass as agreement."""
    floors = declared_floors(PYPROJECT.read_text(encoding="utf-8"))
    pins = workflow_floor_pins(WORKFLOW.read_text(encoding="utf-8"))

    assert set(pins) == set(floors), (
        f"dependency-floor job pins {sorted(pins)} but pyproject declares {sorted(floors)}"
    )
