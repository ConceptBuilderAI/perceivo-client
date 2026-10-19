"""Multipart helpers shared by the ``client.files`` uploads and ``client.infrastructure`` ingests."""

from __future__ import annotations

from typing import IO

#: One multipart file part: ``(file name, data)`` or ``(file name, data, content type)``.
#:
#: On a signing client the transport reads the whole encoded multipart body
#: into memory once, signs those bytes and sends them (see
#: ``Transport._build_signed_request``).
FilePart = tuple[str, bytes | IO[bytes]] | tuple[str, bytes | IO[bytes], str]


def file_part(file_name: str, data: bytes | IO[bytes], content_type: str | None) -> FilePart:
    """The part for ``data``, carrying ``content_type`` only when one is given."""
    return (file_name, data) if content_type is None else (file_name, data, content_type)
