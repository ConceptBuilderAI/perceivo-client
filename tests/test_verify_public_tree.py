"""Fixtures for ``scripts/verify_public_tree.py``."""

from __future__ import annotations

import codecs
import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts import verify_public_tree
from scripts.canonical_archives import (
    VerificationError,
)
from scripts.verify_public_tree import (
    compare_archive_sets,
    main,
    tracked_package,
    tree_findings,
    verify_archives,
)
from tests._verify_public_tree_support import (
    _archives,
    _commit,
    _git,
    _repository,
    _write,
)


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
