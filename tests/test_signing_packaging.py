"""Tests that the golden-vector table ships in the built wheel and works from a clean install.

The table's secret, ``perceivo-test-signing-secret-v1``, is a published test value;
it must appear in no packaged file other than the vector table.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tomllib
import zipfile

import pytest

DIST_ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT = DIST_ROOT / "pyproject.toml"
VECTORS_SOURCE = DIST_ROOT / "perceivo_client" / "signing" / "vectors" / "hmac_v1_vectors.json"

#: The wheel path the table must occupy.
VECTORS_WHEEL_MEMBER = "perceivo_client/signing/vectors/hmac_v1_vectors.json"

#: The published test key, and the only secret material allowed to ship.
PUBLISHED_TEST_SECRET = "perceivo-test-signing-secret-v1"

_SUBPROCESS_TIMEOUT = 900

# Runs in the clean venv and reports where ``perceivo_client`` was imported from.
_PROBE = """
import base64, hashlib, hmac, json, sys
from importlib.metadata import version

import perceivo_client
from perceivo_client.signing import (
    build_canonical_request,
    compute_signature,
    golden_vectors_bytes,
    load_golden_vectors,
    split_target,
    verify_signature,
    verify_signed_request,
)

raw = golden_vectors_bytes()
table = load_golden_vectors()

reproduced, mismatched = [], []
for vector in table["vectors"]:
    raw_path, query = split_target(vector["target"])
    body = None if vector["body_base64"] is None else base64.b64decode(vector["body_base64"])
    canonical = build_canonical_request(
        audience=vector["audience"],
        # The supplied spelling, so the installed code performs the normalisation.
        key_id=vector["key_id_input"],
        method=vector["method"],
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=vector["content_type"], organization=vector["organization"],
        timestamp=vector["timestamp"],
        nonce=vector["nonce"],
    )
    signature = compute_signature(canonical, table["secret_utf8"])
    ok = hmac.compare_digest(canonical, vector["canonical_request"]) and hmac.compare_digest(
        signature, vector["signature"]
    )
    (reproduced if ok else mismatched).append(vector["id"])
    if ok and not verify_signed_request(
        signature=vector["signature"],
        canonical_request=vector["canonical_request"],
        secret=table["secret_utf8"],
        audience=vector["audience"],
        key_id=vector["key_id"],
    ):
        mismatched.append(vector["id"] + " (bound verifier refused a valid vector)")

# Negative vectors carry a correct MAC over a wrongly bound string: a bare MAC check
# accepts them and the bound verifier refuses them. The `metadata_binding` row needs
# the received organization header, so this verifier accepts it; it is counted apart.
mac_accepted, wrongly_verified, accepted_post_mac_rows = [], [], []
for negative in table["negative_vectors"]:
    if verify_signature(negative["signature"], negative["canonical_request"], table["secret_utf8"]):
        mac_accepted.append(negative["id"])
    verified = verify_signed_request(
        signature=negative["signature"],
        canonical_request=negative["canonical_request"],
        secret=table["secret_utf8"],
        audience=negative["verifier_audience"],
        key_id=negative["verifier_key_id"],
    )
    if negative["refused_by"] == "metadata_binding":
        if verified:
            accepted_post_mac_rows.append(negative["id"])
    elif verified:
        wrongly_verified.append(negative["id"])

print(json.dumps({
    "package_file": perceivo_client.__file__,
    "dist_version": version("perceivo-client"),
    "dunder_version": perceivo_client.__version__,
    "sha256": hashlib.sha256(raw).hexdigest(),
    "byte_length": len(raw),
    "count": len(table["vectors"]),
    "field_count": table["field_count"],
    "wire_format_revision": table["wire_format_revision"],
    "negative_count": len(table["negative_vectors"]),
    "accepted_post_mac_rows": accepted_post_mac_rows,
    "post_mac_row_count": sum(
        1 for n in table["negative_vectors"] if n["refused_by"] == "metadata_binding"
    ),
    "negative_shapes": {n["id"]: [n["field_count"], n["refused_by"]] for n in table["negative_vectors"]},
    "secret_utf8": table["secret_utf8"],
    "secret_base64": table["secret_base64"],
    "reproduced": reproduced,
    "mismatched": mismatched,
    "mac_accepted": mac_accepted,
    "wrongly_verified": wrongly_verified,
    "cwd": sys.path[0],
}))
"""


def _run(argv: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT, **kwargs
    )
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


#: Build residue excluded from the copy the wheel is built from, since
#: ``setuptools`` reuses stale files under ``build/lib``.
_BUILD_RESIDUE = ("build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv")


@pytest.fixture(scope="module")
def wheel(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Build a wheel from a clean copy of this distribution."""
    workspace = tmp_path_factory.mktemp("dist-source")
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

    outdir = tmp_path_factory.mktemp("wheelhouse")
    _run([sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir), str(source)])
    built = sorted(outdir.glob("perceivo_client-*.whl"))
    assert len(built) == 1, f"expected exactly one wheel, got {[p.name for p in built]}"
    return built[0]


@pytest.fixture(scope="module")
def clean_install(wheel: pathlib.Path, tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Install that wheel into a fresh venv and probe it from outside the checkout."""
    venv_root = tmp_path_factory.mktemp("clean-venv")
    venv_dir = venv_root / "venv"
    _run([sys.executable, "-m", "venv", str(venv_dir)])

    scripts = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python"
    python = venv_dir / scripts / exe
    assert python.is_file(), f"venv interpreter missing at {python}"

    _run([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)])

    probe = venv_root / "probe.py"
    probe.write_text(_PROBE, encoding="utf-8")
    # Run from the venv root so the source tree is not importable.
    result = _run([str(python), str(probe)], cwd=str(venv_root))
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    payload["_venv_dir"] = str(venv_dir)
    return payload


def test_the_built_wheel_contains_the_golden_vector_table(wheel: pathlib.Path):
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert len(names) > 10, f"wheel has only {len(names)} entries; the scan proves nothing"
    assert VECTORS_WHEEL_MEMBER in names, (
        f"{VECTORS_WHEEL_MEMBER} is not in the wheel ({len(names)} entries). The golden-vector "
        "table is the cross-implementation contract; a consumer that cannot read it from "
        "the dependency graph cannot cross-check anything."
    )


def test_the_wheel_carries_the_table_byte_for_byte(wheel: pathlib.Path):
    source_bytes = VECTORS_SOURCE.read_bytes()
    assert len(source_bytes) > 1000, "source table is implausibly small; the comparison is vacuous"
    with zipfile.ZipFile(wheel) as archive:
        shipped = archive.read(VECTORS_WHEEL_MEMBER)
    assert hashlib.sha256(shipped).hexdigest() == hashlib.sha256(source_bytes).hexdigest(), (
        "the packaged table differs from the source table. Its bytes define the signature "
        "base for every implementation; they may be moved but never rewritten."
    )


def test_the_probe_ran_outside_the_source_tree(clean_install: dict):
    imported = pathlib.Path(clean_install["package_file"]).resolve()
    assert imported.is_relative_to(pathlib.Path(clean_install["_venv_dir"]).resolve()), (
        f"perceivo_client imported from {imported}, which is not the clean venv"
    )
    assert not imported.is_relative_to(DIST_ROOT), (
        f"perceivo_client imported from the source tree ({imported}) — the probe measured the "
        "checkout, not the wheel, which is exactly the defect this file exists to catch"
    )


def test_the_published_artifact_reports_one_version(clean_install: dict):
    """The wheel metadata version and ``__version__`` both match ``pyproject.toml``."""
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert clean_install["dist_version"] == declared, (
        f"wheel metadata says {clean_install['dist_version']}, pyproject says {declared}"
    )
    assert clean_install["dunder_version"] == declared, (
        f"perceivo_client.__version__ is {clean_install['dunder_version']}, "
        f"but the distribution is {declared}. Bump perceivo_client/_version.py."
    )


def test_the_clean_install_loads_the_golden_vectors(clean_install: dict):
    source = json.loads(VECTORS_SOURCE.read_text(encoding="utf-8"))
    expected = len(source["vectors"])
    for name, key in (("positive", "vectors"), ("negative", "negative_vectors")):
        declared = source["vector_counts"][name]
        assert len(source[key]) == declared, (
            f"the source table declares {declared} {name} vectors but carries "
            f"{len(source[key])}; it was truncated or edited by hand"
        )
    assert expected > 0, "the source table carries no vectors at all"
    assert clean_install["count"] == expected, (
        f"expected {expected} vectors from the installed wheel, got {clean_install['count']}"
    )
    assert clean_install["sha256"] == hashlib.sha256(VECTORS_SOURCE.read_bytes()).hexdigest()
    assert clean_install["byte_length"] == VECTORS_SOURCE.stat().st_size


def test_the_installed_table_is_the_eleven_field_revision(clean_install: dict):
    assert clean_install["wire_format_revision"] == 3
    assert clean_install["field_count"] == 11


def test_every_vector_reproduces_from_the_clean_install(clean_install: dict):
    assert clean_install["mismatched"] == [], (
        f"vectors that did not reproduce from the installed wheel: {clean_install['mismatched']}"
    )
    assert len(clean_install["reproduced"]) == clean_install["count"], (
        f"only {len(clean_install['reproduced'])} of {clean_install['count']} vectors were checked"
    )


def test_the_negative_vectors_ship_too(clean_install: dict):
    expected = len(json.loads(VECTORS_SOURCE.read_text(encoding="utf-8"))["negative_vectors"])
    assert expected >= 5, (
        f"the source table declares {expected} negative vectors; five is the floor"
    )
    assert clean_install["negative_count"] == expected


def test_the_installed_negative_vectors_are_not_all_arity_failures(clean_install: dict):
    shapes = clean_install["negative_shapes"]
    grounds = {ground for _count, ground in shapes.values()}
    assert grounds == {"arity", "prelude_binding", "metadata_binding"}, grounds
    prelude = [vid for vid, (count, ground) in shapes.items() if ground == "prelude_binding"]
    assert len(prelude) >= 3, prelude
    for vid in prelude:
        assert shapes[vid][0] == clean_install["field_count"], (
            f"{vid} is a prelude-binding row but carries {shapes[vid][0]} fields; it would be "
            "refused on arity and its binding would go untested"
        )


def test_every_negative_vector_has_a_correct_mac_in_the_clean_install(clean_install: dict):
    assert len(clean_install["mac_accepted"]) == clean_install["negative_count"], (
        "a negative vector's MAC did not verify against the shipped secret; the vectors are "
        f"not testing the binding. accepted={clean_install['mac_accepted']}"
    )


def test_the_installed_bound_verifier_refuses_every_negative_vector(clean_install: dict):
    """Excludes the ``metadata_binding`` rows, which the next test covers."""
    assert clean_install["wrongly_verified"] == [], (
        "the installed bound verifier accepted correctly-signed but wrongly-bound requests: "
        f"{clean_install['wrongly_verified']}"
    )


def test_the_installed_reference_verifier_accepts_the_post_mac_rows(clean_install: dict):
    """The reference verifier accepts metadata-binding rows; the server refuses them."""
    assert clean_install["post_mac_row_count"] >= 1
    assert len(clean_install["accepted_post_mac_rows"]) == clean_install["post_mac_row_count"], (
        clean_install["accepted_post_mac_rows"]
    )


def test_the_shipped_secret_is_the_published_test_constant(clean_install: dict):
    assert clean_install["secret_utf8"] == PUBLISHED_TEST_SECRET, (
        "the shipped vector table's secret is not the published test constant. The table is a "
        "packaged, publicly distributed file — regenerating it with a real signing secret would "
        "publish that secret to every consumer."
    )
    decoded = base64.b64decode(clean_install["secret_base64"]).decode("utf-8")
    assert decoded == PUBLISHED_TEST_SECRET


def test_the_vector_table_is_the_only_packaged_file_carrying_the_secret(wheel: pathlib.Path):
    assert len(PUBLISHED_TEST_SECRET) >= 16, "the search term is too short to be meaningful"
    table = json.loads(VECTORS_SOURCE.read_text(encoding="utf-8"))
    # Each term must also be present in the table, so the scan cannot pass vacuously.
    in_table = [
        PUBLISHED_TEST_SECRET,
        base64.b64encode(PUBLISHED_TEST_SECRET.encode()).decode("ascii"),
        table["secret_transport"]["disclosure_secret_hex"],
        PUBLISHED_TEST_SECRET.encode().hex(),
        table["secret_transport"]["disclosure_secret_hex"].upper(),
    ]
    literals = in_table
    offenders = []
    with zipfile.ZipFile(wheel) as archive:
        table_text = archive.read(VECTORS_WHEEL_MEMBER).decode("utf-8")
        for name in archive.namelist():
            if name == VECTORS_WHEEL_MEMBER:
                continue
            try:
                text = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if any(literal in text for literal in literals):
                offenders.append(name)
    assert offenders == [], (
        f"the golden-vector secret appears in packaged files other than the table: {offenders}. "
        "It belongs in the vector table and nowhere else."
    )
    unfindable = [term for term in in_table if term not in table_text]
    assert unfindable == [], (
        f"{len(unfindable)} search term(s) are absent from the packaged table itself, so the "
        "sweep above proved nothing about them; the scan was measuring an empty set."
    )
