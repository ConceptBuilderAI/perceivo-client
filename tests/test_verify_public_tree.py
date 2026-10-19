"""Fixtures for ``scripts/verify_public_tree.py``."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.canonical_archives import (
    VerificationError,
)
from scripts.verify_public_tree import (
    compare_archive_sets,
    main,
    tracked_package,
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
    ["perceivo_client/__pycache__/x.cpython-312.pyc", ".env.local"],
)
def test_rejects_a_denied_archive_path(tmp_path: Path, member: str) -> None:
    root = _repository(tmp_path)
    _commit(root)
    wheel, sdist = _archives(root, tmp_path / "archives", extra={member: b"x\n"})

    with pytest.raises(VerificationError, match="denied"):
        verify_archives(root, wheel, sdist)
