"""Shared git and archive builders for the ``scripts/verify_public_tree.py`` tests."""

from __future__ import annotations

import io
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path

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
