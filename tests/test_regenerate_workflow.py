"""Controls over ``.github/workflows/regenerate.yml`` and its branch guard.

The workflow regenerates models on a branch named by a ``workflow_dispatch``
input and hands the result back as a patch artifact. These tests pin the two
things that keep it safe: the guard refuses ``dev``, ``main``, the default
branch and ``release/*``; and no job holds ``contents: write`` or pushes, as the
workflow policy (``scripts/check_workflow_policy.py``) requires.

Like ``test_release_workflow_structure.py`` this module reads ``.github/``, which
the source distribution does not ship, so it is excluded in ``MANIFEST.in`` and
named in ``tests/test_signing_sdist_packaging.py::SDIST_EXCLUDED_TESTS``. It
imports no YAML parser for the same reason that module gives.
"""

from __future__ import annotations

import importlib.util
import re
import tomllib
from pathlib import Path

import pytest

from tests.test_release_workflow_structure import _jobs

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "regenerate.yml"
GUARD_PATH = ROOT / ".github" / "scripts" / "regen_dispatch_guard.py"
REQUIREMENTS_CODEGEN = ROOT / ".github" / "requirements-codegen.txt"

SPEC = importlib.util.spec_from_file_location("regen_dispatch_guard", GUARD_PATH)
assert SPEC is not None
assert SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

_RUN_BLOCK = re.compile(r"^(?P<indent>\s*)(?:- )?run:\s*(?P<rest>.*)$")


def workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def run_blocks(text: str) -> list[str]:
    """Every ``run:`` body: a one-line value or the indented block under ``|``/``>``."""
    lines = text.splitlines()
    blocks = []
    for index, line in enumerate(lines):
        match = _RUN_BLOCK.match(line)
        if match is None:
            continue
        rest = match.group("rest")
        if rest and rest[0] not in "|>":
            blocks.append(rest)
            continue
        indent = len(match.group("indent"))
        body = []
        for following in lines[index + 1 :]:
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            body.append(following)
        blocks.append("\n".join(body))
    return blocks


# --- the guard ---------------------------------------------------------------

REFUSED = [
    "dev",
    "Dev",
    "DEV",
    "main",
    "MAIN",
    "trunk",  # the default branch in these cases
    "release",
    "release/0.28.0",
    "Release/client-0.28.0",
    "refs/heads/dev",
    "Refs/heads/feature",
    "",
    "-dev",
    ".hidden",
    "a..b",
    "a//b",
    "trailing/",
    "trailing.",
    "branch.lock",
    "has space",
    "semi;colon",
    "dollar$(id)",
]

ALLOWED = [
    "team/client/issue-123/models",
    "feature/regen",
    "developer",  # starts with "dev" but is not dev
    "maintenance",
    "releases-notes",
    "prerelease/x",
]


@pytest.mark.parametrize("branch", REFUSED)
def test_the_guard_refuses_protected_and_malformed_branches(branch: str):
    assert guard.refusal(branch, "trunk") is not None


@pytest.mark.parametrize("branch", ALLOWED)
def test_the_guard_allows_a_work_branch(branch: str):
    assert guard.refusal(branch, "trunk") is None


def test_the_guard_refuses_dev_when_dev_is_also_the_default_branch():
    assert guard.refusal("dev", "dev") is not None


def test_the_guard_fails_closed_without_a_default_branch():
    assert guard.refusal("feature/regen", "") is not None
    assert guard.refusal("feature/regen", "  ") is not None


def test_the_guard_cli_exits_1_on_refusal_and_0_on_a_work_branch(monkeypatch, capsys):
    monkeypatch.setenv("REGEN_DEFAULT_BRANCH", "dev")
    monkeypatch.setenv("REGEN_BRANCH", "release/0.28.0")
    monkeypatch.setenv("REGEN_REF", "refs/heads/release/0.28.0")
    assert guard.main() == 1
    assert "::error::regenerate refused" in capsys.readouterr().out
    monkeypatch.setenv("REGEN_BRANCH", "team/client/issue-123/models")
    monkeypatch.setenv("REGEN_REF", "refs/heads/team/client/issue-123/models")
    assert guard.main() == 0


MISMATCHED_REFS = [
    "refs/heads/dev",
    "refs/heads/main",
    "refs/heads/Feature/regen",  # a ref is case-sensitive
    "refs/heads/feature/regen2",
    "refs/tags/feature/regen",
    "feature/regen",  # not fully qualified
    "",
]


@pytest.mark.parametrize("ref", MISMATCHED_REFS)
def test_the_guard_refuses_a_dispatch_ref_that_is_not_the_branch(ref: str):
    assert guard.ref_refusal("feature/regen", ref) is not None


def test_the_guard_allows_a_dispatch_on_the_branch_itself():
    assert guard.ref_refusal("feature/regen", "refs/heads/feature/regen") is None


def test_the_guard_cli_refuses_a_work_branch_dispatched_on_dev(monkeypatch, capsys):
    """Must fail: a valid work branch, dispatched with ``--ref dev``."""
    monkeypatch.setenv("REGEN_DEFAULT_BRANCH", "dev")
    monkeypatch.setenv("REGEN_BRANCH", "feature/regen")
    monkeypatch.setenv("REGEN_REF", "refs/heads/dev")
    assert guard.main() == 1
    assert "not 'refs/heads/feature/regen'" in capsys.readouterr().out
    monkeypatch.delenv("REGEN_REF")
    assert guard.main() == 1


def test_the_guard_cli_refuses_when_the_inputs_are_absent(monkeypatch):
    monkeypatch.delenv("REGEN_BRANCH", raising=False)
    monkeypatch.delenv("REGEN_DEFAULT_BRANCH", raising=False)
    assert guard.main() == 1


# --- the workflow ------------------------------------------------------------


def test_the_run_block_reader_sees_inline_and_block_values():
    """The reader's own control: a planted ``${{`` in each form must be seen."""
    planted = (
        "jobs:\n"
        "  a:\n"
        "    steps:\n"
        "      - run: echo ${{ inputs.x }}\n"
        "      - name: b\n"
        "        run: |\n"
        "          echo ok\n"
        "          echo ${{ inputs.y }}\n"
        "      - name: c\n"
        "        env:\n"
        "          X: ${{ inputs.z }}\n"
    )
    blocks = run_blocks(planted)
    assert len(blocks) == 2
    assert "inputs.x" in blocks[0]
    assert "inputs.y" in blocks[1]
    assert not any("inputs.z" in block for block in blocks)


def test_the_workflow_is_dispatch_only():
    on_block = workflow_text().split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
    assert "workflow_dispatch:" in on_block
    for trigger in ("push:", "pull_request", "schedule:", "workflow_run:", "repository_dispatch:"):
        assert trigger not in on_block


def test_no_expression_is_interpolated_into_a_shell_line():
    blocks = run_blocks(workflow_text())
    assert len(blocks) >= 4
    offending = [block for block in blocks if "${{" in block]
    assert offending == []


def test_permissions_are_empty_by_default_and_no_job_can_write():
    text = workflow_text()
    assert "\npermissions: {}\n" in text
    jobs = _jobs(text)
    assert set(jobs) == {"guard", "regenerate"}
    for name in ("guard", "regenerate"):
        assert "permissions:\n      contents: read\n" in jobs[name]
        assert "write" not in jobs[name]
    assert not re.search(r"^\s+\w[\w-]*: write$", text, re.M)


def test_regenerate_depends_on_the_guard():
    jobs = _jobs(workflow_text())
    assert "needs: guard\n" in jobs["regenerate"]
    assert "python3 .github/scripts/regen_dispatch_guard.py" in jobs["guard"]
    assert "REGEN_BRANCH: ${{ inputs.branch }}" in jobs["guard"]
    assert "REGEN_DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}" in jobs["guard"]
    assert "REGEN_REF: ${{ github.ref }}" in jobs["guard"]


def test_branch_code_runs_in_the_dispatched_refs_cache_scope():
    """regenerate checks out the dispatched commit, never a ref named by the input."""
    text = workflow_text()
    regenerate = _jobs(text)["regenerate"]
    assert "inputs.branch" not in regenerate
    assert not re.search(r"^\s+ref:", regenerate, re.M)
    assert "--ref dev" not in text
    assert (
        "gh workflow run regenerate.yml --ref <your work branch> -f branch=<your work branch>"
        in text
    )


def test_branch_code_runs_without_credentials_and_hash_locked_tools():
    jobs = _jobs(workflow_text())
    assert "persist-credentials: false" in jobs["regenerate"]
    install = [block for block in run_blocks(jobs["regenerate"]) if "pip install" in block]
    assert len(install) == 1
    assert " ".join(install[0].split()) == (
        "python -m pip install --only-binary :all: --require-hashes"
        " -r .github/requirements-codegen.txt"
    )
    assert "python openapi/regen.py\n" in jobs["regenerate"]
    assert "python openapi/regen.py --check" in jobs["regenerate"]


def test_no_shell_line_commits_or_pushes():
    shell = "\n".join(run_blocks(workflow_text()))
    for verb in ("git push", "git commit", "gh api", "gh pr"):
        assert verb not in shell, verb


def test_the_patch_is_handed_back_as_an_artifact():
    regenerate = _jobs(workflow_text())["regenerate"]
    assert "actions/upload-artifact@" in regenerate
    assert "name: regenerated-models" in regenerate
    assert "if: steps.diff.outputs.changed == 'true'" in regenerate


def test_every_action_is_pinned_by_full_sha():
    uses = re.findall(r"uses:\s*(\S+)", workflow_text())
    assert len(uses) == 4
    for ref in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", ref), ref


def _requirements(text: str) -> list[str]:
    """Each requirement in a pip requirements file, continuation lines joined."""
    joined = re.sub(r"\\\n", " ", text)
    return [
        line.strip()
        for line in joined.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_the_codegen_requirements_are_exact_and_every_one_is_hashed():
    requirements = _requirements(REQUIREMENTS_CODEGEN.read_text(encoding="utf-8"))
    assert len(requirements) >= 3
    for requirement in requirements:
        assert re.match(r"^[A-Za-z0-9._-]+(\[[a-z,]+\])?==\S+ ", requirement), requirement
        assert re.search(r"--hash=sha256:[0-9a-f]{64}", requirement), requirement


def test_the_codegen_requirements_pin_the_codegen_extra():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extra = set(pyproject["project"]["optional-dependencies"]["codegen"])
    pinned = {
        requirement.split()[0]
        for requirement in _requirements(REQUIREMENTS_CODEGEN.read_text(encoding="utf-8"))
    }
    assert extra <= pinned, extra - pinned
