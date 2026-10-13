"""Multipart helpers shared by the ``client.files`` uploads and ``client.infrastructure`` ingests."""

from __future__ import annotations

from typing import IO

from perceivo_client._transport import Transport
from perceivo_client.signing import SigningError

#: One multipart file part: ``(file name, data)`` or ``(file name, data, content type)``.
FilePart = tuple[str, bytes | IO[bytes]] | tuple[str, bytes | IO[bytes], str]


def refuse_if_signing(transport: Transport, operation: str) -> None:
    """Refuse a multipart request from a signing client instead of sending it unsigned.

    ``httpx`` builds a multipart body as a streaming body, which this client
    cannot HMAC-sign.
    """
    if transport.signing_enabled:
        raise SigningError(
            f"{operation} sends a multipart body, which this client cannot HMAC-sign; "
            "refusing rather than sending an unsigned request from a signing client"
        )


def file_part(file_name: str, data: bytes | IO[bytes], content_type: str | None) -> FilePart:
    """The part for ``data``, carrying ``content_type`` only when one is given."""
    return (file_name, data) if content_type is None else (file_name, data, content_type)
