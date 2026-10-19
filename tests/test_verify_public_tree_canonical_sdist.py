"""Fixtures for ``scripts/canonical_archives.py`` as ``scripts/verify_public_tree.py`` uses it."""

from __future__ import annotations

import gzip
import io
import tarfile
from pathlib import Path
from typing import Callable

import pytest

from scripts.canonical_archives import (
    VerificationError,
    canonicalize_sdist,
)
from scripts.canonical_archives import (
    resolve_epoch as _resolve_epoch,
)
from tests._verify_public_tree_support import (
    EPOCH,
)

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
