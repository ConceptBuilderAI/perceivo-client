"""File content of ``client.files``: upload, upload URLs, replace and download."""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client._transport import _LONG_TIMEOUT
from perceivo_client.generated.models import (
    FileUploadBatchResult,
    UploadResponse,
    UploadTargetResponse,
)
from perceivo_client.resources._multipart import file_part
from perceivo_client.resources.files._common import _FILES, _REPLACE_FILENAME

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _ContentMixin(_MixinBase):
    """File content of ``client.files``: upload, upload URLs, replace and download."""

    # --- content ---
    def upload(
        self,
        space_id: str,
        file_name: str,
        data: bytes | IO[bytes],
        *,
        content_type: str | None = None,
        folder_id: str | None = None,
    ) -> FileUploadBatchResult:
        """Upload one file into a storage space (``POST /files/spaces/{space_id}/upload``).

        ``data`` is sent as a **multipart** part named ``files``. The API accepts
        a file of at most 10 MiB here and requires a ``Content-Length``, so pass
        bytes or a seekable binary file object. For a larger file use
        :meth:`create_upload_url`. Uploading a file under a name already used
        in the folder adds a version to that file.

        Warning:
            The API answers ``200`` even when storage refuses the file. Read
            ``failed`` and the item's ``status`` on the result; a ``200`` alone
            does not mean the file was stored. The operation is not
            idempotent.

        Waits at least 150 s for the response; raise it with ``client.with_options(timeout=...)``.

        Args:
            space_id: Storage space to upload into.
            file_name: Name to store the file under.
            data: File bytes, or a binary file object opened for reading.
            content_type: MIME type for the part. Omit to let the server infer
                it from ``file_name``.
            folder_id: A folder of the space to upload into (query parameter).
                Omit for the space root.

        Returns:
            :class:`FileUploadBatchResult`: ``items`` (one per file, each with
            its ``status``), ``succeeded`` and ``failed``.

        Raises:
            perceivo_client.signing.SigningError: If request signing is
                enabled and the request cannot be signed. With signing on, the
                multipart body is encoded to bytes in memory once and the
                signature covers exactly those bytes, so the whole file is
                held in memory for the request.
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response. The route declares ``408``
                for an upload that timed out, ``411`` without a
                ``Content-Length``, ``413`` for a file over 10 MiB, ``415`` for
                a body that is not multipart, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            FileUploadBatchResult,
            self._post(
                f"{_FILES}/spaces/{segment(space_id, 'space_id')}/upload",
                params=None if folder_id is None else {"folder_id": folder_id},
                files={"files": file_part(file_name, data, content_type)},
                min_timeout=_LONG_TIMEOUT,
            ),
        )

    def create_upload_url(self, body: dict[str, Any]) -> UploadTargetResponse:
        """A short-lived pre-signed URL for one direct-to-blob upload.

        Wraps ``POST /files/upload-url``. ``body`` is an ``UploadUrlRequest``
        (``space_id``, ``file_name``, ``size_bytes``; optional
        ``relative_path``); the declared size is checked against the space's
        quota first. The bytes never pass through the API: upload them to
        ``upload_url``, then register ``blob_name`` with :meth:`create_entry`.

        Warning:
            ``upload_url`` grants write access to that blob until
            ``expires_at``: do not log it.

        Args:
            body: An ``UploadUrlRequest`` object, sent as the JSON body.

        Returns:
            :class:`UploadTargetResponse`: ``upload_url``, ``blob_name`` and
            ``expires_at``.

        Raises:
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
                The declared size is checked against the space's quota; the contract names no status
                for a size over it.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(UploadTargetResponse, self._post(f"{_FILES}/upload-url", json=body))

    def replace_content(
        self,
        entry_id: str,
        data: bytes | IO[bytes],
        *,
        content_type: str | None = None,
        version_comment: str | None = None,
    ) -> UploadResponse:
        """Upload new content for a file as a new version (``PUT .../content``).

        Wraps ``PUT /files/entries/{entry_id}/content``. ``data`` is sent as
        the one **multipart** part, ``file``; earlier versions stay available
        and the entry keeps its name, location and id (the part's file name is
        ignored). Pass bytes or a seekable binary file object so a
        ``Content-Length`` is sent. The request is limited to 16 MiB (``413``);
        a folder or a trashed file answers ``409``. ``version_comment`` is sent
        as a query parameter when given.

        Waits at least 150 s for the response; raise it with ``client.with_options(timeout=...)``.

        Args:
            entry_id: The file to add a version to.
            data: The new content, as bytes or a binary file object opened for
                reading; sent as the multipart part ``file``.
            content_type: MIME type for the part. Omit to send none.
            version_comment: A note for the new version, sent as the optional
                ``version_comment`` query parameter (no default). Omit to send
                none. The multipart body is the contract's
                ``Body_replace_file_entry_content``.

        Returns:
            :class:`UploadResponse`: the ``entry`` and its new ``version``.

        Raises:
            perceivo_client.signing.SigningError: If request signing is
                enabled and the request cannot be signed. A signing client
                holds the whole encoded body in memory, as :meth:`upload`
                describes.
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown entry, ``409`` (``PerceivoConflictError``) for a folder or a trashed file,
                ``413`` (bare ``PerceivoAPIError``) for a request body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            UploadResponse,
            self._request(
                "PUT",
                f"{_FILES}/entries/{segment(entry_id, 'entry_id')}/content",
                params=None if version_comment is None else {"version_comment": version_comment},
                files={"file": file_part(_REPLACE_FILENAME, data, content_type)},
                min_timeout=_LONG_TIMEOUT,
            ),
        )

    def download(self, entry_id: str) -> bytes:
        """A file's content, as bytes (``GET /files/entries/{entry_id}/content``).

        The content passes through the API, which must finish the transfer
        within 30 seconds, so a very large file can fail with ``502`` or
        ``503``. The public API offers no pre-signed download URL.

        Args:
            entry_id: The file to download.

        Returns:
            ``bytes``: the file's content, exactly as stored.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` for a trashed file,
                ``404`` (``PerceivoNotFoundError``) for a folder or an entry
                that does not exist or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` or ``503`` (``PerceivoServerError``) when the transfer
                does not finish in time.
            PerceivoConnectionError: If the API cannot be reached.
        """
        response = self._t.request(
            "GET", f"{_FILES}/entries/{segment(entry_id, 'entry_id')}/content"
        )
        return response.content
