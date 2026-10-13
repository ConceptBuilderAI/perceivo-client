"""The *released* wheel is built from the sdist — so the sdist must carry the table.

**This file exists because ``test_signing_packaging.py`` measures a different
artifact than the one the release publishes.** That file builds with
``python -m build --wheel``, which assembles a wheel *directly from the source
tree*. The release does not:

    .github/workflows/release.yml, "Build distributions"
        python -m build --outdir dist-client perceivo-client

``python -m build`` with no target flag builds the **sdist first and then builds
the wheel from that sdist**. The two paths select files through different
machinery — the wheel path through ``[tool.setuptools.package-data]``, the sdist
path through the sdist file list (``MANIFEST.in`` directives, and setuptools'
defaults) — so they can disagree, and only the sdist path decides what ships.

Measured, with a single ``exclude perceivo_client/signing/vectors/*.json`` line in
a ``MANIFEST.in``:

======================================  ===================
build path                              vector table
======================================  ===================
``build --wheel`` (what the other file  **present** — green
tests)
sdist                                   **missing**
wheel built from that sdist             **missing** — this
                                        is the published
                                        artifact
======================================  ===================

That is a control reporting green while the released wheel is broken. The whole
point of the golden-vector table is that a consumer reaches it *through the
dependency graph*; a wheel without it 401s every consumer that tries to
cross-check its canonicaliser, and the sdist is itself a published release asset
(``gh release create ... dist-client/*``), so a ``--no-binary`` install or any
downstream repackager consumes it directly.

So this file builds **the way the release builds** and asserts on **both**
artifacts it produces.
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
)

#: Path of the table inside each artifact. Hardcoded, not derived: a refactor that
#: relocates the resource has to state the move here, in both spellings.
#: The live public-API suite needs a deployed API and operator keys: never shipped.
SDIST_PRUNED_DIR = "tests/integration/public_api/"
VECTORS_WHEEL_MEMBER = "perceivo_client/signing/vectors/hmac_v1_vectors.json"
VECTORS_SDIST_SUFFIX = "perceivo_client/signing/vectors/hmac_v1_vectors.json"

#: Every module of the signing subpackage. A wheel that ships the table but drops
#: ``canonical.py`` is just as unusable, and the release verifies imports only for
#: the names it happens to list.
SIGNING_MODULES = (
    "__init__.py",
    "_constants.py",
    "canonical.py",
    "golden_vectors.py",
    "signer.py",
)

#: Tests excluded from the sdist by ``MANIFEST.in`` because their inputs are
#: repository infrastructure under ``.github/``, which a source distribution does
#: not carry. Named here, not derived: adding a test that reads ``.github/``
#: without listing it in both places breaks the unpacked-sdist suite.
SDIST_EXCLUDED_TESTS = frozenset(
    {
        "tests/test_ci_dependency_floor_pins.py",
        "tests/test_check_workflow_policy.py",
        "tests/test_regenerate_workflow.py",
        "tests/test_release_workflow_structure.py",
    }
)

#: Repository tooling ``MANIFEST.in`` excludes: each reads the git checkout (see MANIFEST.in).
SDIST_EXCLUDED_REPO_TOOLING = frozenset(
    {
        "scripts/_export_manifest.json",
        "scripts/check_file_size.py",
        "scripts/grant_terminology_allowlist.json",
        "scripts/grant_terminology_scan.py",
        "scripts/legacy_code_scan.py",
        "scripts/tests/test_check_file_size.py",
        "tests/_gitrepo.py",
        "tests/test_grant_terminology_scan.py",
        "tests/test_legacy_code_scan.py",
        "tests/test_legacy_repo_scan.py",
    }
)

_SUBPROCESS_TIMEOUT = 900

#: Build residue that must never reach the copy this test builds from.
#: ``setuptools`` does not clean ``build/lib`` between builds, so a build run in
#: place can be assembled from a PREVIOUS build's staged files. Measured while
#: writing this file: with the table excluded from the sdist, a wheel built in a
#: tree that had already produced a wheel still contained the table, because a
#: stale ``build/lib/.../vectors/`` was left over — the mutation looked survivable
#: when it was not. Mirrors ``test_signing_packaging.py``.
_BUILD_RESIDUE = ("build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv")


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    # Fixed argv, no shell. Failures raise with both streams attached: a packaging
    # test that dies on an unexplained non-zero exit teaches nothing.
    result = subprocess.run(argv, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


@pytest.fixture(scope="module")
def release_artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pathlib.Path]:
    """Build exactly as the release does: one ``python -m build``, no target flag.

    A single invocation produces the sdist *and* the wheel-built-from-that-sdist,
    sharing one isolated build environment — the same two files the release
    workflow uploads. Built from a pristine copy so no residue can supply a file
    the configuration no longer selects.
    """
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
    # No --wheel and no --sdist. That is the whole point of this file.
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


# ---------------------------------------------------------------------------
# The sdist — a published release asset in its own right
# ---------------------------------------------------------------------------
def test_the_sdist_carries_the_golden_vector_table(sdist_names: list[str]):
    """If the table is not here, the wheel built from this sdist cannot have it."""
    matches = [n for n in sdist_names if n.endswith(VECTORS_SDIST_SUFFIX)]
    assert matches, (
        f"{VECTORS_SDIST_SUFFIX} is not in the sdist ({len(sdist_names)} entries). The release "
        "builds the published wheel FROM this sdist, so the table cannot reach the wheel either, "
        "and the sdist is itself published as a release asset."
    )


def test_the_sdist_carries_every_signing_module(sdist_names: list[str]):
    """The table is useless without the code that reads it."""
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
    # The release-tooling tests import their scripts out of ``scripts/`` by path,
    # so an sdist without that tree publishes tests that cannot run.
    expected.update(
        path.relative_to(DIST_ROOT).as_posix()
        for path in (DIST_ROOT / "scripts").rglob("*")
        if path.is_file() and path.suffix in {".py", ".md", ".json"}
    )
    expected.update(path.relative_to(DIST_ROOT).as_posix() for path in SDIST_TEST_SUPPORT)
    # The ``.github/``-reading tests are deliberately NOT shipped, so they
    # are not part of the roster either. Their absence is asserted positively
    # below: an sdist that shipped them would publish a test whose inputs it does
    # not carry, and the unpacked archive would fail collection.
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
    shipped_tooling = sorted(
        relative
        for relative in SDIST_EXCLUDED_REPO_TOOLING
        if any(name.endswith(relative) for name in sdist_names)
    )
    assert shipped_tooling == [], f"the sdist ships repository-only tooling: {shipped_tooling}"
    expected -= SDIST_EXCLUDED_REPO_TOOLING
    expected = {r for r in expected if not r.startswith(SDIST_PRUNED_DIR)}
    # The roster is every shipped test module, test fixture and README under
    # tests/, vectors/*.py, scripts/*.py and the shared
    # support modules, less the .github/-reading tests above. A change that adds
    # or removes one of those files restates this count.
    assert len(expected) == 98, f"repo-native test-input roster changed: {sorted(expected)}"
    missing = [
        relative
        for relative in sorted(expected)
        if not any(name.endswith(relative) for name in sdist_names)
    ]
    assert missing == [], (
        "the sdist publishes tests that cannot run from the archive because these "
        f"repo-native inputs are absent: {missing}"
    )


def _is_live_public_api_suite(name: str) -> bool:
    return f"/{SDIST_PRUNED_DIR}" in f"/{name}"


def test_the_sdist_ships_no_live_public_api_suite(sdist_names: list[str]):
    """The live public-API suite stays in the repository; MANIFEST.in prunes it."""
    # Controls that hold in a checkout AND in an unpacked sdist (which has no
    # suite to look at): the matcher recognises an archive member path, and
    # the archive does carry the other tests, so a clean scan is not an
    # empty population.
    assert _is_live_public_api_suite(f"perceivo_client-0.0.0/{SDIST_PRUNED_DIR}README.md")
    assert not _is_live_public_api_suite("perceivo_client-0.0.0/tests/integration/__init__.py")
    siblings = [n for n in sdist_names if "/tests/" in f"/{n}"]
    assert len(siblings) > 10, f"only {len(siblings)} tests/ members; the scan proves nothing"
    shipped = sorted(name for name in sdist_names if _is_live_public_api_suite(name))
    assert shipped == [], f"the sdist ships the live public-API suite: {shipped}"


def test_the_sdist_table_is_byte_identical_to_source(
    release_artifacts: dict[str, pathlib.Path], sdist_names: list[str]
):
    """The bytes ARE the wire format — the sdist must not reformat or re-encode."""
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


# ---------------------------------------------------------------------------
# The wheel built FROM that sdist — the artifact a consumer actually installs
# ---------------------------------------------------------------------------
def test_the_wheel_built_from_the_sdist_carries_the_table(wheel_names: list[str]):
    """The load-bearing assertion: the *published* wheel contains the contract.

    ``test_signing_packaging.py`` asserts this of a wheel built straight from the
    source tree. This asserts it of the wheel the release actually ships.
    """
    assert VECTORS_WHEEL_MEMBER in wheel_names, (
        f"{VECTORS_WHEEL_MEMBER} is not in the wheel built from the sdist "
        f"({len(wheel_names)} entries). This is the artifact `gh release create` publishes, so a "
        "consumer installing perceivo-client cannot reach the golden-vector table at all."
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
    """A round trip through the sdist must not perturb a single byte."""
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
    """The release names the wheel by ``CLIENT_VERSION`` and would not find a mismatch.

    ``release.yml`` locates the wheel at a hardcoded
    ``dist-client/perceivo_client-${CLIENT_VERSION}-py3-none-any.whl``. If the two
    artifacts ever carried different versions the release would fail late, after
    publishing had already begun.
    """
    sdist_version = (
        release_artifacts["sdist"].name.removeprefix("perceivo_client-").removesuffix(".tar.gz")
    )
    wheel_version = release_artifacts["wheel"].name.split("-")[1]
    assert sdist_version == wheel_version, (
        f"sdist declares {sdist_version} but wheel declares {wheel_version}"
    )


# ---------------------------------------------------------------------------
# Documentation links that point OUT of the shipped tree
# ---------------------------------------------------------------------------
# A published document that links a file the archive does not carry is a
# dangling link in the *release artifact*, not in the repository: the repository
# resolves it, so every repo-side check reads green. These assertions are made
# against the extracted sdist for that reason.
#: Sources the shipped documentation points at by path: ``README.md`` instructs
#: the reader to run ``openapi/regen.py``. Hardcoded, not derived from a parse of
#: the documents: a doc edit that *drops* the instruction would otherwise shrink
#: the derived roster to nothing and the test would still pass.
LINKED_SOURCES = ("openapi/regen.py",)

#: The local input closure of each linked source — every file in this tree it
#: imports, requires or reads, transitively. Shipping only the entrypoint leaves
#: the link resolving to a file that cannot run.
LINKED_SOURCE_CLOSURE = {
    # regen.py imports only the standard library. Without a flag it reads the
    # vendored spec; `--check` also reads the provenance beside it.
    "openapi/regen.py": ("openapi/openapi-v1.json", "openapi/spec_provenance.json"),
}

_MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")
_DOCUMENTS_WITH_LINKS = ("README.md", "docs/HMAC_REQUEST_SIGNING.md")


@pytest.fixture(scope="module")
def extracted_sdist(
    release_artifacts: dict[str, pathlib.Path], tmp_path_factory: pytest.TempPathFactory
) -> pathlib.Path:
    """Unpack the sdist and return its single top-level directory.

    This is what a ``pip download --no-binary`` consumer, or any downstream
    repackager, actually has on disk.
    """
    destination = tmp_path_factory.mktemp("extracted-sdist")
    with tarfile.open(release_artifacts["sdist"]) as archive:
        # Our own freshly built artifact. ``filter`` mirrors the guard in
        # ``tests/unit/fixtures_seed_corpus.py`` so 3.12+ does not warn.
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
    """An entrypoint whose own inputs are absent is a link to a file that cannot run."""
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
    # 2: the README carries no relative links (it is the PyPI description, where
    # none resolve; tests/test_readme_quickstart.py enforces that), so every
    # relative link examined here is one of docs/HMAC_REQUEST_SIGNING.md's two.
    assert checked >= 2, f"only {checked} relative links were examined; the scan proves nothing"
    assert unresolved == [], f"links dangling in the published sdist: {unresolved}"


def test_the_readme_generator_command_resolves_inside_the_extracted_sdist(
    extracted_sdist: pathlib.Path,
):
    """``python openapi/regen.py`` is an instruction, not a link — same obligation."""
    readme = (extracted_sdist / "README.md").read_text(encoding="utf-8")
    assert "python openapi/regen.py" in readme, (
        "README.md no longer instructs the reader to run openapi/regen.py; this test is vacuous "
        "and should be retired with the instruction."
    )
    assert (extracted_sdist / "openapi" / "regen.py").is_file(), (
        "README.md tells the reader to run openapi/regen.py, which the sdist does not carry."
    )


def test_the_extracted_generator_reports_its_usage(extracted_sdist: pathlib.Path):
    """Run the shipped generator's ``--help`` from the extracted tree and assert exit 0.

    ``--help`` is argparse's own path: it prints usage and exits before the
    generator reads the spec, writes a model or contacts anything. It proves the
    shipped file is the runnable entrypoint the README names; it does not prove a
    regeneration would succeed, and nothing here regenerates anything.
    """
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
