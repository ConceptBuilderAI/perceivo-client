"""Fixtures for ``scripts/verify_public_tree.py``."""

from __future__ import annotations

import codecs
import gzip
import hashlib
import io
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Callable

import pytest

from scripts import verify_public_tree
from scripts.canonical_archives import (
    VerificationError,
    canonicalize_sdist,
)
from scripts.canonical_archives import (
    resolve_epoch as _resolve_epoch,
)
from scripts.verify_public_tree import (
    compare_archive_sets,
    main,
    tracked_package,
    tree_findings,
    verify_archives,
)

# A fixed instant after the 1980 zip timestamp floor, used for every
# canonicalization fixture so expected bytes never depend on the clock.
EPOCH = 1_700_000_000


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Public Verification Test",
        "GIT_AUTHOR_EMAIL": "verify@example.invalid",
        "GIT_COMMITTER_NAME": "Public Verification Test",
        "GIT_COMMITTER_EMAIL": "verify@example.invalid",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result.stdout.decode("utf-8").strip()


def _write(root: Path, name: str, data: bytes) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-b", "dev")
    _git(root, "config", "core.autocrlf", "false")
    _write(root, "perceivo_client/__init__.py", b'__version__ = "1.1.1"\n')
    _write(root, "perceivo_client/py.typed", b"")
    _write(root, "LICENSE", b"Apache License\n")
    _write(root, "NOTICE", b"Copyright fixture\n")
    return root


def _commit(root: Path) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "fixture")


def _archives(
    root: Path,
    directory: Path,
    *,
    include_license: bool = True,
    include_notice: bool = True,
    extra: dict[str, bytes] | None = None,
) -> tuple[Path, Path]:
    directory.mkdir()
    wheel = directory / "perceivo_client-1.1.1-py3-none-any.whl"
    wheel_files = {
        "perceivo_client/__init__.py": (root / "perceivo_client/__init__.py").read_bytes(),
        "perceivo_client/py.typed": b"",
    }
    sdist_files = {
        "perceivo_client-1.1.1/perceivo_client/__init__.py": (
            root / "perceivo_client/__init__.py"
        ).read_bytes(),
        "perceivo_client-1.1.1/perceivo_client/py.typed": b"",
    }
    if include_license:
        license_bytes = (root / "LICENSE").read_bytes()
        wheel_files["perceivo_client-1.1.1.dist-info/licenses/LICENSE"] = license_bytes
        sdist_files["perceivo_client-1.1.1/LICENSE"] = license_bytes
    if include_notice:
        notice_bytes = (root / "NOTICE").read_bytes()
        wheel_files["perceivo_client-1.1.1.dist-info/licenses/NOTICE"] = notice_bytes
        sdist_files["perceivo_client-1.1.1/NOTICE"] = notice_bytes
    for name, data in (extra or {}).items():
        wheel_files[name] = data
        sdist_files[f"perceivo_client-1.1.1/{name}"] = data
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in wheel_files.items():
            archive.writestr(name, data)

    sdist = directory / "perceivo_client-1.1.1.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        for name, data in sdist_files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    return wheel, sdist


def test_tracked_package_reads_the_git_index(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    assert set(tracked_package(root)) == {"perceivo_client/__init__.py", "perceivo_client/py.typed"}


def test_rejects_changed_working_bytes(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    _write(root, "perceivo_client/__init__.py", b"changed = True\n")

    with pytest.raises(VerificationError, match="working bytes differ"):
        tracked_package(root)


def test_rejects_symlink_mode_without_platform_symlink_support(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    object_id = _git(root, "hash-object", "-w", "--stdin", input_bytes=b"__init__.py")
    _git(
        root,
        "update-index",
        "--add",
        "--cacheinfo",
        f"120000,{object_id},perceivo_client/link.py",
    )

    with pytest.raises(VerificationError, match="unsupported Git mode"):
        tracked_package(root)


def test_rejects_second_perceivo_package_boundary(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _write(root, "perceivo-extra/__init__.py", b"")
    _commit(root)

    with pytest.raises(VerificationError, match="invalid package boundary"):
        tracked_package(root)


def test_rejects_untyped_package(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "perceivo_client/py.typed").unlink()
    _commit(root)

    with pytest.raises(VerificationError, match="typed-package marker"):
        tracked_package(root)


def test_verifies_archive_members_and_reproducibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = _repository(tmp_path)
    _commit(root)
    first = tmp_path / "first"
    second = tmp_path / "second"
    wheel, sdist = _archives(root, first)
    _archives(root, second)

    verify_archives(root, wheel, sdist)
    compare_archive_sets(first, second)
    assert (
        main(["archives", "--root", str(root), "--wheel", str(wheel), "--sdist", str(sdist)]) == 0
    )


def test_the_cli_refuses_an_archive_outside_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repository(tmp_path)
    _commit(root)
    wheel, sdist = _archives(root, tmp_path / "outside")
    monkeypatch.chdir(root)
    argv = ["archives", "--root", ".", "--wheel", str(wheel), "--sdist", str(sdist)]
    assert main(argv) == 1
    assert "outside the working directory" in capsys.readouterr().err


def test_rejects_archive_without_license(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    wheel, sdist = _archives(root, tmp_path / "archives", include_license=False)

    with pytest.raises(VerificationError, match="LICENSE absent"):
        verify_archives(root, wheel, sdist)


def test_rejects_archive_without_notice(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    wheel, sdist = _archives(root, tmp_path / "archives", include_notice=False)

    with pytest.raises(VerificationError, match="NOTICE absent"):
        verify_archives(root, wheel, sdist)


def test_rejects_archive_whose_package_member_differs(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    wheel, sdist = _archives(root, tmp_path / "archives")
    _write(root, "perceivo_client/__init__.py", b'__version__ = "9.9.9"\n')
    _commit(root)

    with pytest.raises(VerificationError, match="package member missing or changed"):
        verify_archives(root, wheel, sdist)


def test_rejects_a_secret_in_an_archive_member(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _commit(root)
    token = ("gh" + "p_") + "A" * 36
    wheel, sdist = _archives(
        root, tmp_path / "archives", extra={"perceivo_client/leak.txt": token.encode()}
    )

    with pytest.raises(VerificationError, match="GitHub token"):
        verify_archives(root, wheel, sdist)


@pytest.mark.parametrize(
    "member",
    ["perceivo_client/__pycache__/x.cpython-312.pyc", ".env.local", "perceivo" + "_platform/x.py"],
)
def test_rejects_a_denied_archive_path(tmp_path: Path, member: str) -> None:
    root = _repository(tmp_path)
    _commit(root)
    wheel, sdist = _archives(root, tmp_path / "archives", extra={member: b"x\n"})

    with pytest.raises(VerificationError, match="denied"):
        verify_archives(root, wheel, sdist)


@pytest.mark.parametrize(
    ("marker", "label"),
    [(("TI" + "CK-999").encode(), "ticket"), (("claim" + "ed:agent-1").encode(), "claim")],
)
def test_private_ticket_and_claim_markers_are_refused(
    tmp_path: Path, marker: bytes, label: str
) -> None:
    root = _repository(tmp_path)
    _write(root, "perceivo_client/notes.py", b"# " + marker + b"\n")
    _commit(root)
    wheel, sdist = _archives(
        root,
        tmp_path / "archives",
        extra={"perceivo_client/notes.py": (root / "perceivo_client/notes.py").read_bytes()},
    )

    with pytest.raises(VerificationError, match=label):
        verify_archives(root, wheel, sdist)


@pytest.mark.parametrize(
    ("marker", "label"),
    [
        (("perceivo-data" + "-microservice").encode(), "internal repository name"),
        (("perceivo-documen" + "tation").encode(), "internal repository name"),
        (("PERCEIVO-DATA" + "-MICROSERVICE").encode(), "internal repository name"),
        (("ap" + "p/middleware/api_key_auth.py:86").encode(), "file:line pointer"),
    ],
)
def test_internal_repository_names_and_source_pointers_are_refused(
    tmp_path: Path, marker: bytes, label: str
) -> None:
    root = _repository(tmp_path)
    _write(root, "perceivo_client/notes.py", b"# see " + marker + b"\n")
    _commit(root)
    wheel, sdist = _archives(
        root,
        tmp_path / "archives",
        extra={"perceivo_client/notes.py": (root / "perceivo_client/notes.py").read_bytes()},
    )

    with pytest.raises(VerificationError, match=label):
        verify_archives(root, wheel, sdist)


@pytest.mark.parametrize(
    "text",
    [
        b"# Source: perceivo-api" + b"-service committed openapi-public.json\n",
        b"# the ap" + b"p/middleware/api_key_auth.py module, cited without a line\n",
        b"# see perceivo_client/signing/_secret.py:119\n",
    ],
)
def test_the_spec_source_name_and_unnumbered_paths_still_pass(tmp_path: Path, text: bytes) -> None:
    root = _repository(tmp_path)
    _write(root, "perceivo_client/notes.py", text)
    _commit(root)
    wheel, sdist = _archives(
        root,
        tmp_path / "archives",
        extra={"perceivo_client/notes.py": (root / "perceivo_client/notes.py").read_bytes()},
    )

    verify_archives(root, wheel, sdist)


# Every literal below is assembled from pieces so that this file passes the tree
# scan it tests.
PRODUCT = "per" + "ceivo"


def _tree_with(tmp_path: Path, files: dict[str, bytes]) -> Path:
    root = _repository(tmp_path)
    for name, data in files.items():
        _write(root, name, data)
    _commit(root)
    return root


@pytest.mark.parametrize(
    ("text", "label"),
    [
        ("TI" + "CK-1790", "private ticket identifier"),
        ("claim" + "ed:agent-1", "private claim marker"),
        (f"{PRODUCT}-api" + "-service", "internal service or repository name"),
        (f"{PRODUCT}-api" + "-gateway", "internal service or repository name"),
        (f"{PRODUCT}-w" + "eb", "internal service or repository name"),
        (f"{PRODUCT.upper()}-INFRA" + "STRUCTURE", "internal service or repository name"),
        (f"{PRODUCT}-infra" + "structure-manager", "internal service or repository name"),
        (f"_{PRODUCT}" + "-sdk", "internal service or repository name"),
        (
            f"github.com/ConceptBuilderAI/_{PRODUCT}" + "-client",
            "private source repository URL",
        ),
        (
            f"git@github.com:ConceptBuilderAI/_{PRODUCT}" + "-client.git",
            "private source repository URL",
        ),
        (f"{PRODUCT}_api" + "_gateway", "internal service or repository name"),
        (f"{PRODUCT.upper()}_DATA" + "_MICROSERVICE_URL", "internal service or repository name"),
        (f"{PRODUCT}_orchestration" + "_manager", "internal service or repository name"),
        (f"{PRODUCT}-api" + "_service", "internal service or repository name"),
        ("api.d" + f"ev.{PRODUCT}.ai", "internal hostname"),
        ("gate" + f"way.{PRODUCT}.ai", "internal hostname"),
        ("cluster-1.hcp.centralus.azm" + "k8s.io", "internal hostname"),
        ("registry.azure" + "cr.io", "internal hostname"),
        ("api.default.svc.cluster.lo" + "cal", "internal hostname"),
        ("ap" + "p/routes/files.py:42", "internal source file:line pointer"),
        ("docs" + "-site/scripts/run.py:17", "private source file:line pointer"),
        ("he" + "lm/values-prod.yaml:3", "private source file:line pointer"),
        ("Agent " + "Pipeline/RULES.md", "private documentation reference"),
        ("HMAC_SOLUTION" + "_PACKET.md", "private documentation reference"),
        ("S" + "P-1.2", "private documentation reference"),
        ("owner rul" + "ing", "private ruling reference"),
        ("Rul" + "ing 64", "private ruling reference"),
        ("S" + "EC-1", "security finding identifier"),
        (f"{PRODUCT}-8" + "f", "agent session name"),
        ("\u26d4 note", "internal emphasis marker"),
        ("\u2b50 note", "internal emphasis marker"),
        ("\u26a0 note", "internal emphasis marker"),
    ],
)
def test_the_tree_scan_refuses_each_internal_pattern(tmp_path: Path, text: str, label: str) -> None:
    root = _tree_with(tmp_path, {"docs/notes.md": f"see {text} here\n".encode()})

    assert tree_findings(root) == [f"{label} found in docs/notes.md"]


@pytest.mark.parametrize(
    "text",
    [
        f"pip install {PRODUCT}-client",
        f"https://github.com/ConceptBuilderAI/{PRODUCT}-client/issues",
        f"import {PRODUCT}_client",
        f"https://api.{PRODUCT}.ai/v1 and https://{PRODUCT}.ai/docs",
        f'hmac_audience="{PRODUCT}-api-prod"',
        f"the {PRODUCT}-webhook header",
        f"see {PRODUCT}_client/signing/_secret.py:119",
        "the ap" + "p/routes/files.py module, cited without a line",
        "ruling out a retry; the owner of the key",
        "SECRET and SEC" + "TION headers",
        "SP" + "-1 without a minor version",
        f"{PRODUCT}-8" + "fold",
        "plain ASCII warning: read this",
        f"{PRODUCT}_client_api_gateway_timeout",
        f"{PRODUCT}_web" + "hook_secret",
        f"{PRODUCT}_lo" + "calize",
    ],
)
def test_the_tree_scan_passes_public_vocabulary(tmp_path: Path, text: str) -> None:
    root = _tree_with(tmp_path, {"docs/notes.md": f"{text}\n".encode()})

    assert tree_findings(root) == []


def test_the_tree_scan_refuses_a_personal_identifier_by_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planted = "zqxperson"
    monkeypatch.setattr(
        verify_public_tree,
        "PERSONAL_TOKEN_DIGESTS",
        frozenset({hashlib.sha256(planted.encode()).hexdigest()}),
    )
    root = _tree_with(
        tmp_path,
        {
            "docs/leak.md": f"reviewer: {planted.upper()}\n".encode(),
            "docs/clean.md": f"reviewer: {planted}al\n".encode(),
        },
    )

    assert tree_findings(root) == ["personal identifier found in docs/leak.md"]


def test_the_personal_identifier_digests_are_sha256() -> None:
    digests = verify_public_tree.PERSONAL_TOKEN_DIGESTS

    assert digests
    assert all(len(digest) == 64 and int(digest, 16) >= 0 for digest in digests)


def test_the_tree_scan_reports_every_finding(tmp_path: Path) -> None:
    root = _tree_with(
        tmp_path,
        {
            "a.md": ("TI" + "CK-1 and S" + "EC-2\n").encode(),
            "b.md": (f"{PRODUCT}-w" + "eb\n").encode(),
            "c.md": b"clean\n",
        },
    )

    assert tree_findings(root) == [
        "private ticket identifier found in a.md",
        "security finding identifier found in a.md",
        "internal service or repository name found in b.md",
    ]


def test_the_tree_scan_reads_the_index_not_the_working_file(tmp_path: Path) -> None:
    root = _tree_with(tmp_path, {"docs/notes.md": b"clean\n"})
    _write(root, "docs/notes.md", ("TI" + "CK-1\n").encode())

    assert tree_findings(root) == []

    _git(root, "add", "docs/notes.md")

    assert tree_findings(root) == ["private ticket identifier found in docs/notes.md"]


@pytest.mark.parametrize("encoding", ["utf-16", "utf-16-le", "utf-16-be", "utf-32"])
def test_the_tree_scan_reads_bom_marked_wide_text(tmp_path: Path, encoding: str) -> None:
    boms = {"utf-16-le": codecs.BOM_UTF16_LE, "utf-16-be": codecs.BOM_UTF16_BE}
    bom = boms.get(encoding, b"")
    data = bom + ("see " + "TI" + "CK-1 here\n").encode(encoding)
    clean = bom + "clean\n".encode(encoding)
    assert b"\0" in data
    root = _tree_with(tmp_path, {"docs/wide.txt": data, "docs/clean.txt": clean})

    assert tree_findings(root) == ["private ticket identifier found in docs/wide.txt"]


def test_the_tree_scan_still_skips_unmarked_binary_with_a_nul(tmp_path: Path) -> None:
    root = _tree_with(tmp_path, {"assets/blob.bin": b"\x89PNG\0" + ("TI" + "CK-1").encode()})

    assert tree_findings(root) == []


def test_the_tree_scan_refuses_a_denied_path_and_skips_binary_blobs(tmp_path: Path) -> None:
    root = _tree_with(
        tmp_path,
        {".env.local": b"x\n", "assets/logo.bin": b"\0" + ("TI" + "CK-1").encode()},
    )

    assert tree_findings(root) == ["denied path: .env.local"]


def test_the_tree_cli_lists_findings_and_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree_with(tmp_path, {"docs/notes.md": ("S" + "EC-1\n").encode()})
    monkeypatch.chdir(root)

    assert main(["tree", "--root", "."]) == 1
    error = capsys.readouterr().err
    assert "security finding identifier found in docs/notes.md" in error
    assert "1 finding(s) in the git tree" in error


def test_the_tree_cli_passes_a_clean_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree_with(tmp_path, {"docs/notes.md": b"clean\n"})
    monkeypatch.chdir(root)

    assert main(["tree", "--root", "."]) == 0
    assert "public tree verification passed" in capsys.readouterr().out


def _is_git_work_tree_root(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, check=False
    )
    if completed.returncode:
        return False
    top = completed.stdout.decode("utf-8", "replace").strip()
    return bool(top) and Path(top).resolve() == path


def test_the_scanner_and_its_tests_pass_their_own_scan() -> None:
    repository = Path(__file__).resolve().parents[1]
    if not _is_git_work_tree_root(repository):
        pytest.skip(
            "the self-scan reads the git index; this tree is not a git checkout "
            "(for example an unpacked sdist), so there is no index to scan"
        )
    own = {"scripts/verify_public_tree.py", "tests/test_verify_public_tree.py"}
    tracked = set(_git(repository, "ls-files", *sorted(own)).splitlines())

    assert tracked == own
    assert [
        finding for finding in tree_findings(repository) if finding.rsplit(" ", 1)[-1] in own
    ] == []


SDIST_PAYLOADS = {
    "perceivo_client-1.1.1/perceivo_client/__init__.py": b'__version__ = "1.1.1"\n',
    "perceivo_client-1.1.1/LICENSE": b"Apache License\n",
    "perceivo_client-1.1.1/NOTICE": b"Copyright fixture\n",
    "perceivo_client-1.1.1/scripts/release.sh": b"#!/bin/sh\necho release\n",
}
EXECUTABLE_MEMBER = "perceivo_client-1.1.1/scripts/release.sh"
PACKAGE_MEMBER = "perceivo_client-1.1.1/perceivo_client/__init__.py"


def _tar_bytes(build: Callable[[tarfile.TarFile], None]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w|", format=tarfile.PAX_FORMAT) as archive:
        build(archive)
    return buffer.getvalue()


def _gzip_bytes(payload: bytes, *, mtime: int, filename: str) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename=filename, mode="wb", fileobj=buffer, mtime=mtime) as compressed:
        compressed.write(payload)
    return buffer.getvalue()


def _sdist(
    path: Path,
    *,
    mtime: int = 0,
    mode: int = 0o644,
    owner: int = 0,
    owner_name: str = "",
    gzip_mtime: int = 0,
    gzip_filename: str = "",
    reverse: bool = False,
    executable: tuple[str, ...] = (),
) -> Path:
    """Write an sdist whose payloads are fixed and whose metadata varies."""

    def build(archive: tarfile.TarFile) -> None:
        for name in sorted(SDIST_PAYLOADS, reverse=reverse):
            data = SDIST_PAYLOADS[name]
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = mtime
            info.mode = 0o700 if name in executable else mode
            info.uid = info.gid = owner
            info.uname = info.gname = owner_name
            archive.addfile(info, io.BytesIO(data))

    tar = _tar_bytes(build)
    path.write_bytes(_gzip_bytes(tar, mtime=gzip_mtime, filename=gzip_filename))
    return path


def _hostile_sdist(path: Path, build: Callable[[tarfile.TarFile], None]) -> Path:
    """Write an sdist that carries one benign member and one hostile member."""

    def compose(archive: tarfile.TarFile) -> None:
        payload = SDIST_PAYLOADS[PACKAGE_MEMBER]
        good = tarfile.TarInfo(PACKAGE_MEMBER)
        good.size = len(payload)
        archive.addfile(good, io.BytesIO(payload))
        build(archive)

    path.write_bytes(_gzip_bytes(_tar_bytes(compose), mtime=0, filename=""))
    return path


def _members(path: Path) -> dict[str, tuple[bytes, int, int, int, str, str, int]]:
    collected: dict[str, tuple[bytes, int, int, int, str, str, int]] = {}
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            extracted = archive.extractfile(member)
            payload = b"" if extracted is None else extracted.read()
            collected[member.name] = (
                payload,
                member.mode,
                member.uid,
                member.gid,
                member.uname,
                member.gname,
                int(member.mtime),
            )
    return collected


def _reject(path: Path, message: str) -> None:
    """Assert the archive is rejected and left byte-identical on disk."""
    before = path.read_bytes()
    with pytest.raises(VerificationError, match=message):
        canonicalize_sdist(path, EPOCH)
    assert path.read_bytes() == before
    assert not list(path.parent.glob("*.canonical.tmp"))


def test_canonical_sdist_absorbs_metadata_only_differences(tmp_path: Path) -> None:
    left = _sdist(tmp_path / "left.tar.gz")
    right = _sdist(
        tmp_path / "right.tar.gz",
        mtime=1_600_000_000,
        mode=0o666,
        owner=501,
        owner_name="builder",
        gzip_mtime=1_234_567,
        gzip_filename="right.tar",
        reverse=True,
    )
    assert left.read_bytes() != right.read_bytes()

    canonicalize_sdist(left, EPOCH)
    canonicalize_sdist(right, EPOCH)

    assert left.read_bytes() == right.read_bytes()


def test_canonical_sdist_is_deterministic_and_idempotent(tmp_path: Path) -> None:
    source = _sdist(tmp_path / "source.tar.gz", mtime=42, mode=0o666, owner=7, owner_name="ci")
    first = canonicalize_sdist(source, EPOCH, tmp_path / "first.tar.gz").read_bytes()
    second = canonicalize_sdist(source, EPOCH, tmp_path / "second.tar.gz").read_bytes()
    assert first == second

    in_place = tmp_path / "in-place.tar.gz"
    in_place.write_bytes(source.read_bytes())
    canonicalize_sdist(in_place, EPOCH)
    once = in_place.read_bytes()
    canonicalize_sdist(in_place, EPOCH)
    assert in_place.read_bytes() == once == first


def test_canonical_sdist_preserves_payloads_and_legal_files(tmp_path: Path) -> None:
    source = _sdist(tmp_path / "source.tar.gz", mtime=99, mode=0o666, owner=501, owner_name="who")
    canonicalize_sdist(source, EPOCH)

    members = _members(source)
    assert set(members) == set(SDIST_PAYLOADS)
    for name, payload in SDIST_PAYLOADS.items():
        assert members[name][0] == payload
    for legal in ("perceivo_client-1.1.1/LICENSE", "perceivo_client-1.1.1/NOTICE"):
        assert members[legal][1:] == (0o644, 0, 0, "", "", EPOCH)


def test_canonical_sdist_preserves_the_executable_bit(tmp_path: Path) -> None:
    source = _sdist(tmp_path / "source.tar.gz", mode=0o666, executable=(EXECUTABLE_MEMBER,))
    canonicalize_sdist(source, EPOCH)

    members = _members(source)
    assert members[EXECUTABLE_MEMBER][1] == 0o755
    assert members["perceivo_client-1.1.1/LICENSE"][1] == 0o644


def test_canonical_sdist_rejects_an_absolute_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("/etc/shadow")
        info.size = 0
        archive.addfile(info, io.BytesIO(b""))

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "unsafe path")


def test_canonical_sdist_rejects_a_parent_traversal_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("perceivo_client-1.1.1/../../escape.py")
        info.size = 0
        archive.addfile(info, io.BytesIO(b""))

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "unsafe path segments")


def test_canonical_sdist_rejects_a_drive_qualified_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("C:/Windows/system32/evil.py")
        info.size = 0
        archive.addfile(info, io.BytesIO(b""))

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "unsafe drive-qualified path")


def test_canonical_sdist_rejects_a_symlink_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("perceivo_client-1.1.1/link.py")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../../etc/shadow"
        archive.addfile(info)

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "link archive member")


def test_canonical_sdist_rejects_a_hardlink_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("perceivo_client-1.1.1/hard.py")
        info.type = tarfile.LNKTYPE
        info.linkname = PACKAGE_MEMBER
        archive.addfile(info)

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "link archive member")


def test_canonical_sdist_rejects_a_device_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("perceivo_client-1.1.1/console")
        info.type = tarfile.CHRTYPE
        info.devmajor = 5
        info.devminor = 1
        archive.addfile(info)

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "device archive member")


def test_canonical_sdist_rejects_a_fifo_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        info = tarfile.TarInfo("perceivo_client-1.1.1/pipe")
        info.type = tarfile.FIFOTYPE
        archive.addfile(info)

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "device archive member")


def test_canonical_sdist_rejects_a_duplicate_member(tmp_path: Path) -> None:
    def build(archive: tarfile.TarFile) -> None:
        payload = SDIST_PAYLOADS[PACKAGE_MEMBER]
        info = tarfile.TarInfo(PACKAGE_MEMBER)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    _reject(_hostile_sdist(tmp_path / "hostile.tar.gz", build), "duplicate archive member")


def test_canonical_sdist_rejects_a_negative_source_epoch(tmp_path: Path) -> None:
    source = _sdist(tmp_path / "source.tar.gz")
    before = source.read_bytes()

    with pytest.raises(VerificationError, match="negative source epoch"):
        _resolve_epoch(-1)
    assert source.read_bytes() == before


def test_source_epoch_falls_back_to_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))
    assert _resolve_epoch(None) == EPOCH
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "  ")
    with pytest.raises(VerificationError, match="no source epoch"):
        _resolve_epoch(None)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")
    with pytest.raises(VerificationError, match="invalid SOURCE_DATE_EPOCH"):
        _resolve_epoch(None)
