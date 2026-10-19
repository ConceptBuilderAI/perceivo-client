"""The golden-vector table must reach a consumer through the built artifact.

The golden-vector table is the cross-check between this client's signer and any
other implementation, so there is exactly one table and every implementation reads
it from the installed package. A test that reads the table from the source tree, or
from an editable install that exposes the source tree, passes even when the wheel
does not carry it. So every assertion below runs against a wheel built from this
tree and installed into a clean virtual environment, and the probe runs with its
working directory outside the checkout so the source tree cannot be on ``sys.path``.

The published test secret
=========================
``perceivo-test-signing-secret-v1`` is published on purpose and protects nothing. A
vector table maps ``(audience, key_id, method, path, query, body, content_type,
timestamp, nonce, secret)`` to a signature, so the key has to be in the file or the
signature column cannot be recomputed by anyone.

What must never happen is the reverse: a real secret being generated into the table
and shipped, or the test secret being pasted into some other packaged file. So the
shipped secret is pinned to that exact published literal, and the set of packaged
files containing it must be exactly the one vector table.

Each test guards itself against passing vacuously.
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

#: The wheel path the table must occupy. Hardcoded rather than derived, so a
#: refactor that relocates the resource has to state the move here.
VECTORS_WHEEL_MEMBER = "perceivo_client/signing/vectors/hmac_v1_vectors.json"

#: The published test key, and the only secret material allowed to ship.
PUBLISHED_TEST_SECRET = "perceivo-test-signing-secret-v1"

_SUBPROCESS_TIMEOUT = 900

# Runs in the clean venv, never in this interpreter. It resolves the table only
# through the public accessor, reproduces every vector end to end, and reports
# where `perceivo_client` was actually imported from so the caller can prove the
# checkout was not the source.
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
        # The supplied spelling, not the normalised one. Handing the installed
        # code the answer would make the key-id normalisation vector vacuous.
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

# The negative vectors carry a correct MAC over a wrongly bound string. Both
# halves are measured: a bare mac check must accept every one of them, and the
# bound verifier must refuse every one of them. Without the first half the
# second proves only that a bad digest fails, which is not the claim.
#
# The `metadata_binding` row is counted separately and asserted in the other
# direction. It is refused only by comparing canonical field 9 against the
# organization header the EDGE received, which this reference verifier has no
# request to read -- so it accepts, correctly, and folding it into
# `wrongly_verified` would claim a control this function does not implement.
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
    # Fixed argv, no shell. Failures raise with both streams attached: a packaging
    # test that dies on an unexplained non-zero exit teaches nothing.
    result = subprocess.run(
        argv, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT, **kwargs
    )
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result


#: Build residue that must never reach the copy this test builds from.
#: ``setuptools`` does not clean ``build/lib`` between builds, so a wheel built in
#: place can be assembled from a previous build's staged files: with the
#: ``package-data`` entry deleted, a stale ``build/lib/.../vectors/`` would still
#: put the vector table in the wheel.
_BUILD_RESIDUE = ("build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv")


@pytest.fixture(scope="module")
def wheel(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Build a real wheel from a pristine copy of this distribution.

    Copied rather than built in place for two reasons: the build cannot inherit
    stale staged files (see ``_BUILD_RESIDUE``), and running the suite does not
    litter the working tree with ``build/`` and ``*.egg-info/``.
    """
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
    # cwd is the venv root, NOT the checkout: nothing from the source tree may be
    # importable, or the probe would measure the editable install all over again.
    result = _run([str(python), str(probe)], cwd=str(venv_root))
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    payload["_venv_dir"] = str(venv_dir)
    return payload


# ---------------------------------------------------------------------------
# The artifact itself
# ---------------------------------------------------------------------------
def test_the_built_wheel_contains_the_golden_vector_table(wheel: pathlib.Path):
    """The contract is in the shipped artifact."""
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert len(names) > 10, f"wheel has only {len(names)} entries; the scan proves nothing"
    assert VECTORS_WHEEL_MEMBER in names, (
        f"{VECTORS_WHEEL_MEMBER} is not in the wheel ({len(names)} entries). The golden-vector "
        "table is the cross-implementation contract; a consumer that cannot read it from "
        "the dependency graph cannot cross-check anything."
    )


def test_the_wheel_carries_the_table_byte_for_byte(wheel: pathlib.Path):
    """The bytes are the wire format; packaging must not reformat or re-encode them."""
    source_bytes = VECTORS_SOURCE.read_bytes()
    assert len(source_bytes) > 1000, "source table is implausibly small; the comparison is vacuous"
    with zipfile.ZipFile(wheel) as archive:
        shipped = archive.read(VECTORS_WHEEL_MEMBER)
    assert hashlib.sha256(shipped).hexdigest() == hashlib.sha256(source_bytes).hexdigest(), (
        "the packaged table differs from the source table. Its bytes define the signature "
        "base for every implementation; they may be moved but never rewritten."
    )


# ---------------------------------------------------------------------------
# The clean install — the only evidence that survives `pip install -e`
# ---------------------------------------------------------------------------
def test_the_probe_ran_outside_the_source_tree(clean_install: dict):
    """Guard the guard: if this resolved to the checkout, every result below is void."""
    imported = pathlib.Path(clean_install["package_file"]).resolve()
    assert imported.is_relative_to(pathlib.Path(clean_install["_venv_dir"]).resolve()), (
        f"perceivo_client imported from {imported}, which is not the clean venv"
    )
    assert not imported.is_relative_to(DIST_ROOT), (
        f"perceivo_client imported from the source tree ({imported}) — the probe measured the "
        "checkout, not the wheel, which is exactly the defect this file exists to catch"
    )


def test_the_published_artifact_reports_one_version(clean_install: dict):
    """``_version.py`` and the distribution metadata are two hand-maintained copies.

    They were free to drift while nothing published this distribution. Now that the
    release workflow does, the number in the wheel's metadata is what a consumer
    pins and the number in ``_version.py`` is what the User-Agent advertises — a
    disagreement makes a published artifact lie about which build it is.
    """
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert clean_install["dist_version"] == declared, (
        f"wheel metadata says {clean_install['dist_version']}, pyproject says {declared}"
    )
    assert clean_install["dunder_version"] == declared, (
        f"perceivo_client.__version__ is {clean_install['dunder_version']}, "
        f"but the distribution is {declared}. Bump perceivo_client/_version.py."
    )


def test_the_clean_install_loads_the_golden_vectors(clean_install: dict):
    """``load_golden_vectors()`` works from a wheel, with no path and no source tree."""
    source = json.loads(VECTORS_SOURCE.read_text(encoding="utf-8"))
    expected = len(source["vectors"])
    # Derived, not hardcoded: the table declares its own sizes, so the anti-shrink
    # check compares each list with that declaration and there is no number in this
    # file to go stale.
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
    """The shipped table must match the shipped signer. A wheel carrying ten-field
    expectations next to an eleven-field canonicaliser reads as a signer bug at every
    consumer."""
    assert clean_install["wire_format_revision"] == 3
    assert clean_install["field_count"] == 11


def test_every_vector_reproduces_from_the_clean_install(clean_install: dict):
    """Every canonical request and signature, recomputed by the installed code."""
    assert clean_install["mismatched"] == [], (
        f"vectors that did not reproduce from the installed wheel: {clean_install['mismatched']}"
    )
    assert len(clean_install["reproduced"]) == clean_install["count"], (
        f"only {len(clean_install['reproduced'])} of {clean_install['count']} vectors were checked"
    )


# ---------------------------------------------------------------------------
# The negative vectors — the half of the contract a MAC check cannot express
# ---------------------------------------------------------------------------
def test_the_negative_vectors_ship_too(clean_install: dict):
    """They are as much of the contract as the positive ones: a verifier that
    reproduces every positive signature and still accepts the six-field downgrade
    has implemented the canonicaliser and none of the binding. The count is
    derived from the source table, so it does not go stale when rows are added."""
    expected = len(json.loads(VECTORS_SOURCE.read_text(encoding="utf-8"))["negative_vectors"])
    assert expected >= 5, (
        f"the source table declares {expected} negative vectors; five is the floor"
    )
    assert clean_install["negative_count"] == expected


def test_the_installed_negative_vectors_are_not_all_arity_failures(clean_install: dict):
    """Checked in the artifact a consumer installs: a table whose every negative row
    is refused on the field count tests the arity check repeatedly and the domain,
    audience and key-id bindings not at all, while every test above still passes."""
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
    """The premise. Each negative vector is *correctly signed* — it fails on the
    binding, not on the digest — so this must hold or the next test is vacuous."""
    assert len(clean_install["mac_accepted"]) == clean_install["negative_count"], (
        "a negative vector's MAC did not verify against the shipped secret; the vectors are "
        f"not testing the binding. accepted={clean_install['mac_accepted']}"
    )


def test_the_installed_bound_verifier_refuses_every_negative_vector(clean_install: dict):
    """The negative vectors, run against the code a consumer installs. Excludes
    the `metadata_binding` rows; the next test asserts that half."""
    assert clean_install["wrongly_verified"] == [], (
        "the installed bound verifier accepted correctly-signed but wrongly-bound requests: "
        f"{clean_install['wrongly_verified']}"
    )


def test_the_installed_reference_verifier_accepts_the_post_mac_rows(clean_install: dict):
    """The exclusion above, asserted rather than assumed: a skipped row and an
    accepted row are indistinguishable from a passing suite. The reference verifier
    accepts the field 9 metadata-unbound row, precisely the gap a server closes
    after ``compare_digest``; if this starts refusing, either the verifier grew the
    binding or the row is no longer what it claims."""
    assert clean_install["post_mac_row_count"] >= 1
    assert len(clean_install["accepted_post_mac_rows"]) == clean_install["post_mac_row_count"], (
        clean_install["accepted_post_mac_rows"]
    )


# ---------------------------------------------------------------------------
# The published-secret control
# ---------------------------------------------------------------------------
def test_the_shipped_secret_is_the_published_test_constant(clean_install: dict):
    """A real secret must never be generated into the table and shipped."""
    assert clean_install["secret_utf8"] == PUBLISHED_TEST_SECRET, (
        "the shipped vector table's secret is not the published test constant. The table is a "
        "packaged, publicly distributed file — regenerating it with a real signing secret would "
        "publish that secret to every consumer."
    )
    decoded = base64.b64decode(clean_install["secret_base64"]).decode("utf-8")
    assert decoded == PUBLISHED_TEST_SECRET


def test_the_vector_table_is_the_only_packaged_file_carrying_the_secret(wheel: pathlib.Path):
    """The secret may live in the contract. It may not leak into anything else shipped."""
    assert len(PUBLISHED_TEST_SECRET) >= 16, "the search term is too short to be meaningful"
    # The table publishes a second secret, the 64-hex disclosure the
    # secret-transport rows key on — and hex is a supported transport, so a scan that
    # knew only the UTF-8 spelling would pass while a disclosure sat in a shipped file.
    table = json.loads(VECTORS_SOURCE.read_text(encoding="utf-8"))
    # Allowed in the table, forbidden everywhere else. Each is asserted present there
    # after the sweep: an empty result must mean "found nowhere else", never "searched
    # for a string that exists nowhere", which is how a leak scan passes vacuously.
    in_table = [
        PUBLISHED_TEST_SECRET,
        base64.b64encode(PUBLISHED_TEST_SECRET.encode()).decode("ascii"),
        table["secret_transport"]["disclosure_secret_hex"],
        # The published secret rendered AS HEX. It is a legitimate spelling now, the
        # table itself carries it as one transport row's key, and a docstring that
        # "helpfully" showed it this way would be a leak the two terms above miss.
        PUBLISHED_TEST_SECRET.encode().hex(),
        # ``t03`` proves upper- and lower-case disclosures are ONE key, so the
        # uppercase spelling is as real as the lowercase one and a docstring could
        # leak it while every term above still reported clean.
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


# ---------------------------------------------------------------------------
