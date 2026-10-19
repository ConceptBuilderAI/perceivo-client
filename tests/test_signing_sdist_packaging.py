"""Build the sdist and the wheel built from it, as the release does, and check both.

``python -m build`` with no target flag builds the sdist and then builds the wheel
from that sdist, so the sdist file list (``MANIFEST.in``) decides what ships.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

import pytest

DIST_ROOT = pathlib.Path(__file__).resolve().parents[1]
VECTORS_SOURCE = DIST_ROOT / "perceivo_client" / "signing" / "vectors" / "hmac_v1_vectors.json"
SDIST_TEST_SUPPORT = (
    DIST_ROOT / ".gitattributes",
    DIST_ROOT / "docs" / "HMAC_REQUEST_SIGNING.md",
    DIST_ROOT / "openapi" / "openapi-v1.json",
    DIST_ROOT / "openapi" / "spec_provenance.json",
    DIST_ROOT / "openapi" / "regen.py",
    DIST_ROOT / "openapi" / "regen_parts.py",
    DIST_ROOT / "openapi" / "regen_names.py",
    DIST_ROOT / "openapi" / "regen_spec.py",
)

VECTORS_WHEEL_MEMBER = "perceivo_client/signing/vectors/hmac_v1_vectors.json"
VECTORS_SDIST_SUFFIX = "perceivo_client/signing/vectors/hmac_v1_vectors.json"

SIGNING_MODULES = (
    "__init__.py",
    "_constants.py",
    "canonical.py",
    "golden_vectors.py",
    "signer.py",
)

#: Tests that read ``.github/``; ``MANIFEST.in`` excludes them from the sdist.
SDIST_EXCLUDED_TESTS = frozenset(
    {
        "tests/test_ci_dependency_floor_pins.py",
        "tests/test_check_workflow_policy.py",
        "tests/test_regenerate_workflow.py",
        "tests/test_release_workflow_structure.py",
    }
)

_SUBPROCESS_TIMEOUT = 900

#: Build residue left out of the copy this test builds from.
_BUILD_RESIDUE = ("build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv")


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


@pytest.fixture(scope="module")
def release_artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pathlib.Path]:
    """Build from a clean copy with one ``python -m build`` and no target flag."""
    workspace = tmp_path_factory.mktemp("release-source")
    source = workspace / "perceivo-client"
    shutil.copytree(
        DIST_ROOT,
        source,
        ignore=lambda _dir, names: [
            n for n in names if n in _BUILD_RESIDUE or n.endswith(".egg-info")
        ],
    )
    assert (source / "pyproject.toml").is_file(), "the source copy is missing pyproject.toml"
    assert not (source / "build").exists(), "build residue was copied; the build is not pristine"

    outdir = tmp_path_factory.mktemp("release-dist")
    _run([sys.executable, "-m", "build", "--outdir", str(outdir), str(source)])

    sdists = sorted(outdir.glob("perceivo_client-*.tar.gz"))
    wheels = sorted(outdir.glob("perceivo_client-*.whl"))
    assert len(sdists) == 1, f"expected exactly one sdist, got {[p.name for p in sdists]}"
    assert len(wheels) == 1, f"expected exactly one wheel, got {[p.name for p in wheels]}"
    return {"sdist": sdists[0], "wheel": wheels[0]}


@pytest.fixture(scope="module")
def sdist_names(release_artifacts: dict[str, pathlib.Path]) -> list[str]:
    with tarfile.open(release_artifacts["sdist"]) as archive:
        names = archive.getnames()
    assert len(names) > 10, f"sdist has only {len(names)} entries; the scan proves nothing"
    return names


@pytest.fixture(scope="module")
def wheel_names(release_artifacts: dict[str, pathlib.Path]) -> list[str]:
    with zipfile.ZipFile(release_artifacts["wheel"]) as archive:
        names = archive.namelist()
    assert len(names) > 10, f"wheel has only {len(names)} entries; the scan proves nothing"
    return names


def test_the_sdist_carries_the_golden_vector_table(sdist_names: list[str]):
    matches = [n for n in sdist_names if n.endswith(VECTORS_SDIST_SUFFIX)]
    assert matches, f"{VECTORS_SDIST_SUFFIX} is not in the sdist ({len(sdist_names)} entries)."


def test_the_sdist_carries_every_signing_module(sdist_names: list[str]):
    missing = [
        module
        for module in SIGNING_MODULES
        if not any(n.endswith(f"perceivo_client/signing/{module}") for n in sdist_names)
    ]
    assert missing == [], f"the sdist is missing signing modules: {missing}"


def test_the_sdist_carries_its_complete_repo_native_test_inputs(sdist_names: list[str]):
    """Every shipped test and its public repo-native inputs must resolve in the sdist."""
    expected = {
        path.relative_to(DIST_ROOT).as_posix()
        for path in (DIST_ROOT / "tests").rglob("*")
        if path.is_file() and path.suffix in {".py", ".json", ".md"}
    }
    expected.update(
        path.relative_to(DIST_ROOT).as_posix() for path in (DIST_ROOT / "vectors").glob("*.py")
    )
    expected.update(
        path.relative_to(DIST_ROOT).as_posix()
        for path in (DIST_ROOT / "scripts").rglob("*")
        if path.is_file() and path.suffix in {".py", ".md", ".json"}
    )
    expected.update(path.relative_to(DIST_ROOT).as_posix() for path in SDIST_TEST_SUPPORT)
    shipped_excluded = sorted(
        relative
        for relative in SDIST_EXCLUDED_TESTS
        if any(name.endswith(relative) for name in sdist_names)
    )
    assert shipped_excluded == [], (
        "the sdist ships tests whose inputs live in .github/ and are not shipped: "
        f"{shipped_excluded}"
    )
    expected -= SDIST_EXCLUDED_TESTS
    assert len(expected) == 125, f"repo-native test-input roster changed: {sorted(expected)}"
    missing = [
        relative
        for relative in sorted(expected)
        if not any(name.endswith(relative) for name in sdist_names)
    ]
    assert missing == [], (
        "the sdist publishes tests that cannot run from the archive because these "
        f"repo-native inputs are absent: {missing}"
    )


def test_the_sdist_table_is_byte_identical_to_source(
    release_artifacts: dict[str, pathlib.Path], sdist_names: list[str]
):
    source_bytes = VECTORS_SOURCE.read_bytes()
    assert len(source_bytes) > 1000, "source table is implausibly small; the comparison is vacuous"
    member = next(n for n in sdist_names if n.endswith(VECTORS_SDIST_SUFFIX))
    with tarfile.open(release_artifacts["sdist"]) as archive:
        extracted = archive.extractfile(member)
        assert extracted is not None, f"{member} is a directory entry, not a file"
        shipped = extracted.read()
    assert hashlib.sha256(shipped).hexdigest() == hashlib.sha256(source_bytes).hexdigest(), (
        "the table in the sdist differs from the source table. Its bytes define the signature "
        "base for every implementation; they may be moved but never rewritten."
    )


def test_the_wheel_built_from_the_sdist_carries_the_table(wheel_names: list[str]):
    """The wheel built from the sdist contains the golden-vector table."""
    assert VECTORS_WHEEL_MEMBER in wheel_names, (
        f"{VECTORS_WHEEL_MEMBER} is not in the wheel built from the sdist "
        f"({len(wheel_names)} entries)."
    )


def test_the_wheel_built_from_the_sdist_carries_every_signing_module(wheel_names: list[str]):
    missing = [
        module
        for module in SIGNING_MODULES
        if f"perceivo_client/signing/{module}" not in wheel_names
    ]
    assert missing == [], f"the released wheel is missing signing modules: {missing}"


def test_the_wheel_built_from_the_sdist_matches_source_byte_for_byte(
    release_artifacts: dict[str, pathlib.Path], wheel_names: list[str]
):
    source_bytes = VECTORS_SOURCE.read_bytes()
    assert len(source_bytes) > 1000, "source table is implausibly small; the comparison is vacuous"
    assert VECTORS_WHEEL_MEMBER in wheel_names, "the table is absent; the byte check is vacuous"
    with zipfile.ZipFile(release_artifacts["wheel"]) as archive:
        shipped = archive.read(VECTORS_WHEEL_MEMBER)
    assert hashlib.sha256(shipped).hexdigest() == hashlib.sha256(source_bytes).hexdigest(), (
        "the table changed on its way through the sdist. Every implementation signs against "
        "these exact bytes."
    )


def test_both_release_artifacts_declare_the_same_version(
    release_artifacts: dict[str, pathlib.Path],
):
    """The sdist and the wheel carry the same version."""
    sdist_version = (
        release_artifacts["sdist"].name.removeprefix("perceivo_client-").removesuffix(".tar.gz")
    )
    wheel_version = release_artifacts["wheel"].name.split("-")[1]
    assert sdist_version == wheel_version, (
        f"sdist declares {sdist_version} but wheel declares {wheel_version}"
    )


#: Sources the shipped documentation points at by path.
LINKED_SOURCES = ("openapi/regen.py",)

#: Every file each linked source reads or imports, transitively.
LINKED_SOURCE_CLOSURE = {
    "openapi/regen.py": (
        "openapi/regen_parts.py",
        "openapi/regen_names.py",
        "openapi/regen_spec.py",
        "openapi/openapi-v1.json",
        "openapi/spec_provenance.json",
    ),
}

_MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")
_DOCUMENTS_WITH_LINKS = ("README.md", "docs/HMAC_REQUEST_SIGNING.md")


@pytest.fixture(scope="module")
def extracted_sdist(
    release_artifacts: dict[str, pathlib.Path], tmp_path_factory: pytest.TempPathFactory
) -> pathlib.Path:
    """Unpack the sdist and return its single top-level directory."""
    destination = tmp_path_factory.mktemp("extracted-sdist")
    with tarfile.open(release_artifacts["sdist"]) as archive:
        try:
            archive.extractall(destination, filter="data")
        except TypeError:  # pragma: no cover - Python < 3.12
            archive.extractall(destination)
    roots = [path for path in destination.iterdir() if path.is_dir()]
    assert len(roots) == 1, f"expected one top-level sdist directory, got {[p.name for p in roots]}"
    return roots[0]


def test_the_sdist_carries_every_documented_link_target(sdist_names: list[str]):
    """The files the shipped documentation sends the reader to."""
    missing = [
        relative
        for relative in LINKED_SOURCES
        if not any(name.endswith(f"/{relative}") for name in sdist_names)
    ]
    assert missing == [], (
        f"the sdist publishes documentation linking {missing}, which it does not carry "
        f"({len(sdist_names)} entries). The links resolve in the repository and nowhere else."
    )


def test_the_sdist_carries_the_local_input_closure_of_each_linked_source(sdist_names: list[str]):
    gaps = {
        source: [
            dependency
            for dependency in dependencies
            if not any(name.endswith(f"/{dependency}") for name in sdist_names)
        ]
        for source, dependencies in LINKED_SOURCE_CLOSURE.items()
    }
    missing = {source: absent for source, absent in gaps.items() if absent}
    assert missing == {}, f"the sdist ships these sources without their local inputs: {missing}"


def test_every_documented_link_target_resolves_inside_the_extracted_sdist(
    extracted_sdist: pathlib.Path,
):
    """Resolve each relative markdown link from the extracted tree, as a reader would."""
    unresolved: list[str] = []
    checked = 0
    root = extracted_sdist.resolve()
    for relative in _DOCUMENTS_WITH_LINKS:
        document = extracted_sdist / relative
        assert document.is_file(), f"{relative} is not in the extracted sdist"
        for target in _MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            checked += 1
            resolved = (document.parent / target.split("#")[0]).resolve()
            if not resolved.exists() or root not in resolved.parents:
                unresolved.append(f"{relative} -> {target}")
    # The README has no relative links; docs/HMAC_REQUEST_SIGNING.md has two.
    assert checked >= 2, f"only {checked} relative links were examined; the scan proves nothing"
    assert unresolved == [], f"links dangling in the published sdist: {unresolved}"


def test_the_readme_generator_command_resolves_inside_the_extracted_sdist(
    extracted_sdist: pathlib.Path,
):
    readme = (extracted_sdist / "README.md").read_text(encoding="utf-8")
    assert "python openapi/regen.py" in readme, (
        "README.md no longer instructs the reader to run openapi/regen.py; this test is vacuous "
        "and should be retired with the instruction."
    )
    assert (extracted_sdist / "openapi" / "regen.py").is_file(), (
        "README.md tells the reader to run openapi/regen.py, which the sdist does not carry."
    )


def test_the_extracted_generator_reports_its_usage(extracted_sdist: pathlib.Path):
    """The shipped generator's ``--help`` exits 0 from the extracted tree."""
    result = subprocess.run(
        [sys.executable, "openapi/regen.py", "--help"],
        cwd=extracted_sdist,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0, (
        f"the generator shipped in the sdist exited {result.returncode} on --help\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "usage: regen.py" in result.stdout, (
        f"--help succeeded without printing usage; stdout was:\n{result.stdout}"
    )
