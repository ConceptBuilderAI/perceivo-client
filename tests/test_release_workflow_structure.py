"""Structural tests for ``release.yml`` and ``build-distributions.yml``.

Uses only the standard library, since the ``dependency-floor`` job runs it
without ``yaml`` or ``packaging``.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

WORKFLOWS = ROOT / ".github" / "workflows"
RELEASE_WORKFLOW = WORKFLOWS / "release.yml"
BUILD_WORKFLOW = WORKFLOWS / "build-distributions.yml"
CI_WORKFLOW = WORKFLOWS / "ci.yml"
REQUIREMENTS_BUILD = ROOT / ".github" / "requirements-build.txt"
REQUIREMENTS_TWINE = ROOT / ".github" / "requirements-twine.txt"
RELEASE_FLOOR = ROOT / ".github" / "release-floor.toml"
PYPROJECT = ROOT / "pyproject.toml"
VERSION_MODULE = ROOT / "perceivo_client" / "_version.py"

RELEASE_JOBS = (
    "verify",
    "build",
    "install-matrix",
    "testpypi",
    "testpypi-smoke",
    "pypi",
    "pypi-verify",
    "github-release",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _jobs(workflow: str) -> dict[str, str]:
    """Map each job id to its block in a two-space-indented ``jobs:`` mapping (LF only)."""
    body = workflow.split("\njobs:\n", 1)[1]
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"^  ([A-Za-z0-9_-]+):$", body, re.M)]
    bounds = [s for s, _ in starts] + [len(body)]
    return {name: body[bounds[i] : bounds[i + 1]] for i, (_, name) in enumerate(starts)}


def _code(block: str) -> str:
    """Return a block with its comment lines removed."""
    return "\n".join(line for line in block.splitlines() if not line.strip().startswith("#"))


def _needs(block: str) -> set[str]:
    match = re.search(r"^    needs: (?:\[(?P<many>[^\]]*)\]|(?P<one>\S+))$", block, re.M)
    if match is None:
        return set()
    if match.group("one"):
        return {match.group("one")}
    return {item.strip() for item in match.group("many").split(",")}


def test_the_job_splitter_attributes_lines_to_the_right_job():
    workflow = _text(RELEASE_WORKFLOW)
    jobs = _jobs(workflow)

    assert tuple(jobs) == RELEASE_JOBS
    assert all(block.strip() for block in jobs.values())

    for host, other in (("testpypi", "pypi"), ("pypi", "testpypi")):
        planted = workflow.replace(f"\n  {host}:\n", f"\n  {host}:\n    # PLANTED-MARKER\n", 1)
        blocks = _jobs(planted)
        assert "PLANTED-MARKER" in blocks[host]
        assert "PLANTED-MARKER" not in blocks[other]


def test_a_release_runs_only_from_a_normal_form_v_tag_or_a_dry_run_dispatch():
    head = _text(RELEASE_WORKFLOW).split("\njobs:\n", 1)[0]
    on = head.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]

    assert _code(on).strip().splitlines() == [
        "push:",
        "    tags:",
        '      - "v[0-9]+.[0-9]+.[0-9]+"',
        '      - "v[0-9]+.[0-9]+.[0-9]+rc[0-9]+"',
        "  workflow_dispatch:",
    ]
    assert "\npermissions: {}\n" in head


def test_the_job_graph_is_the_perceivo_release_sequence():
    jobs = _jobs(_text(RELEASE_WORKFLOW))
    assert _needs(jobs["build"]) == {"verify"}
    assert _needs(jobs["install-matrix"]) == {"verify", "build"}
    assert _needs(jobs["testpypi"]) == {"verify", "build", "install-matrix"}
    assert _needs(jobs["testpypi-smoke"]) == {"verify", "build", "testpypi"}
    assert _needs(jobs["pypi"]) == {"verify", "build", "testpypi-smoke"}
    assert _needs(jobs["pypi-verify"]) == {"verify", "build", "pypi"}
    assert _needs(jobs["github-release"]) == {"verify", "build", "pypi-verify"}
    assert "uses: ./.github/workflows/build-distributions.yml" in jobs["build"]


@pytest.mark.parametrize(("job", "environment"), [("testpypi", "testpypi"), ("pypi", "pypi")])
def test_each_upload_job_is_a_dry_run_skip_and_runs_in_its_own_environment(
    job: str, environment: str
) -> None:
    block = _jobs(_text(RELEASE_WORKFLOW))[job]
    assert "    if: needs.verify.outputs.upload == 'true'\n" in block
    assert f"    environment:\n      name: {environment}\n" in block
    assert "    permissions:\n      id-token: write\n    steps:" in block
    assert "pypa/gh-action-pypi-publish@" in block
    project = "https://test.pypi.org" if job == "testpypi" else "https://pypi.org"
    assert f"url: {project}/project/perceivo-client/" in block


def test_only_the_two_upload_jobs_name_an_environment():
    jobs = _jobs(_text(RELEASE_WORKFLOW))
    named = {job for job, block in jobs.items() if "    environment:" in _code(block)}
    assert named == {"testpypi", "pypi"}


def test_the_dry_run_derives_its_tag_from_pyproject_and_checks_ancestry_against_default_branch():
    block = _code(_jobs(_text(RELEASE_WORKFLOW))["verify"])
    assert 'tomllib.load(open("pyproject.toml", "rb"))["project"]["version"]' in block
    assert "MAIN_REF: origin/${{ github.event.repository.default_branch }}" in block
    assert '--main-ref "$MAIN_REF"' in block
    assert "--main-ref origin/" not in block
    assert "fetch-depth: 0" in block


def test_ci_runs_on_both_possible_default_branches():
    head = _text(CI_WORKFLOW).split("\njobs:\n", 1)[0]
    on = _code(head.split("\non:\n", 1)[1].split("\npermissions:", 1)[0])
    assert on.count("branches: [dev, main]") == 2, on


def test_every_smoke_imports_the_installed_client_at_the_released_version():
    jobs = _jobs(_text(RELEASE_WORKFLOW))
    for job in ("install-matrix", "testpypi-smoke", "pypi-verify"):
        block = _code(jobs[job])
        assert "m.version('perceivo-client') == os.environ['EXPECTED_VERSION']" in block, job
        assert "perceivo_client.__version__" in block, job
        assert "working-directory: ${{ runner.temp }}" in block, job
    assert '"perceivo-client==$VERSION"' in jobs["pypi-verify"]


# The release version must be above the one recorded in .github/release-floor.toml.

_RELEASE_VERSION = re.compile(r"(?P<release>[0-9]+\.[0-9]+\.[0-9]+)(?:rc[0-9]+)?")


def _declared_version() -> str:
    return tomllib.loads(_text(PYPROJECT))["project"]["version"]


def test_the_declared_version_is_above_the_cross_publisher_floor():
    floor = tomllib.loads(_text(RELEASE_FLOOR))
    assert floor["schema_version"] == 1
    highest = floor["highest_client_version"]
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", highest), highest

    match = _RELEASE_VERSION.fullmatch(_declared_version())
    assert match, _declared_version()
    declared = tuple(int(part) for part in match.group("release").split("."))
    assert declared > tuple(int(part) for part in highest.split(".")), (
        f"pyproject version {_declared_version()} is not above the floor {highest}"
    )


def test_the_floor_assertion_refuses_a_version_at_the_floor():
    highest = tomllib.loads(_text(RELEASE_FLOOR))["highest_client_version"]
    at_floor = tuple(int(part) for part in highest.split("."))
    assert not at_floor > tuple(int(part) for part in highest.split("."))


def test_the_version_module_matches_pyproject():
    module = re.search(r'^__version__ = "([^"]+)"$', _text(VERSION_MODULE), re.M)
    assert module, "perceivo_client/_version.py has no literal __version__"
    assert module.group(1) == _declared_version()


def _logical_commands(block: str) -> list[str]:
    """Shell commands with backslash continuations joined and comments skipped."""
    joined, commands = "", []
    for raw in block.splitlines():
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue
        joined += " " + stripped.rstrip("\\")
        if not stripped.endswith("\\"):
            commands.append(joined.strip())
            joined = ""
    if joined:
        commands.append(joined.strip())
    return commands


@pytest.mark.parametrize("requirements", ["requirements-build.txt", "requirements-twine.txt"])
def test_the_build_toolchain_installs_without_executing_setup_scripts(requirements: str):
    block = _jobs(_text(BUILD_WORKFLOW))["build"]

    installs = [c for c in _logical_commands(block) if "pip install" in c and requirements in c]
    assert len(installs) == 1, installs
    assert "--require-hashes" in installs[0]
    assert "--only-binary :all:" in installs[0], installs[0]


def test_the_twine_closure_never_shares_the_build_interpreter():
    commands = _logical_commands(_jobs(_text(BUILD_WORKFLOW))["build"])
    twine_install = [c for c in commands if "requirements-twine.txt" in c]
    assert twine_install
    assert all(c.startswith('"$RUNNER_TEMP/twine/bin/python"') for c in twine_install)
    checks = [c for c in commands if "twine check" in c]
    assert checks == ['"$RUNNER_TEMP/twine/bin/python" -m twine check --strict dist-one/*']


# The build runs with ``--no-isolation``, so the pinned backend must satisfy
# ``[build-system].requires``. Versions are compared as zero-padded int tuples.

_PIN = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[0-9][0-9A-Za-z.]*)\s*(?:;|\\|$)")
_SPECIFIER = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)\s*(?:(?P<op>>=|==)\s*(?P<version>\S+))?$")


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _release(version: str) -> tuple[int, ...]:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
        raise AssertionError(f"unsupported version form for a stdlib compare: {version!r}")
    return tuple(int(part) for part in version.split("."))


def _at_least(pinned: str, required: str) -> bool:
    left, right = _release(pinned), _release(required)
    width = max(len(left), len(right))
    return left + (0,) * (width - len(left)) >= right + (0,) * (width - len(right))


def build_pins() -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in REQUIREMENTS_BUILD.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "--hash")):
            continue
        match = _PIN.match(stripped)
        assert match, f"unparsable requirement line: {stripped!r}"
        pins[_normalise(match.group("name"))] = match.group("version")
    return pins


def test_the_pinned_build_toolchain_satisfies_the_declared_build_system():
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["build-system"]["requires"]
    pins = build_pins()

    for requirement in declared:
        match = _SPECIFIER.match(requirement.strip())
        assert match, f"unsupported requirement form: {requirement!r}"
        name = _normalise(match.group("name"))
        assert name in pins, f"{requirement!r} has no pin in {REQUIREMENTS_BUILD.name}"
        if match.group("op") == ">=":
            assert _at_least(pins[name], match.group("version")), (
                f"{name}=={pins[name]} does not satisfy {requirement!r}"
            )
        elif match.group("op") == "==":
            assert pins[name] == match.group("version"), requirement


def _pin_blocks() -> dict[str, list[str]]:
    """Map each normalised requirement name to its own ``--hash`` lines."""
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for raw in REQUIREMENTS_BUILD.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            current = None
            continue
        if stripped.startswith("--hash"):
            assert current is not None, f"orphaned hash line: {stripped!r}"
            blocks[current].append(stripped)
            continue
        match = _PIN.match(stripped)
        assert match, f"unparsable requirement line: {stripped!r}"
        current = _normalise(match.group("name"))
        blocks[current] = []
    return blocks


def test_every_pinned_build_requirement_carries_its_own_hashes():
    blocks = _pin_blocks()
    pins = build_pins()

    assert blocks, "no pins parsed"
    assert set(blocks) == set(pins), set(blocks) ^ set(pins)
    for name, hashes in blocks.items():
        assert hashes, f"{name} carries no --hash line"
        assert all(h.startswith("--hash=sha256:") for h in hashes), (name, hashes)


def _required_dev_checks() -> list[str]:
    text = (ROOT / "RELEASING.md").read_text(encoding="utf-8")
    section = text.split("### Required checks on `dev`", 1)[1]
    block = section.split("```", 2)[1]
    return re.findall(r'"([^"]+)"', block)


def _check_name_patterns() -> list[re.Pattern[str]]:
    """Every check name ``ci.yml`` can produce, matrix expressions as wildcards."""
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    called = re.search(
        r"^    name: (.+)$",
        (WORKFLOWS / "build-distributions.yml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert called is not None
    names = re.findall(r"^    name: (.+)$", ci, re.MULTILINE)
    patterns = []
    for name in names:
        parts = re.split(r"\$\{\{.*?\}\}", name.strip())
        patterns.append(re.compile(".+".join(re.escape(part) for part in parts) + "$"))
    patterns.append(re.compile(re.escape(f"Build / {called.group(1).strip()}") + "$"))
    return patterns


def test_releasing_names_every_release_job_as_a_required_dev_check() -> None:
    required = _required_dev_checks()
    assert len(required) == len(set(required))
    for release_job in (
        "Workflow policy",
        "Release tag self-test",
        "Build / Build and reproduce distributions",
        "Install smoke (wheel)",
        "Install smoke (sdist)",
    ):
        assert release_job in required


def test_every_required_dev_check_is_a_real_check_name() -> None:
    external = {"Analyze (python)", "Analyze (actions)"}
    patterns = _check_name_patterns()
    for name in _required_dev_checks():
        if name in external:
            continue
        assert any(pattern.match(name) for pattern in patterns), name
