"""Batch direct uploads (part of ``client.files``).

Up to 100 files at a time: :meth:`FilesResource.create_upload_urls` gets one
pre-signed URL per file, you PUT each file's bytes to its URL, and
:meth:`FilesResource.register_entries` registers the uploads as entries. Both
need ``FILE_WRITE`` and are checked exactly as their single-file twins,
``create_upload_url`` and ``create_entry``.

These methods are mixed into :class:`~perceivo_client.resources.files.FilesResource`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import RegisterFileEntriesResult, UploadUrlsResponse
from perceivo_client.resources.files._common import _FILES

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _BatchMixin(_MixinBase):
    """The two batch upload operations."""

    def create_upload_urls(self, body: dict[str, Any]) -> UploadUrlsResponse:
        """Pre-signed URLs for up to 100 direct-to-blob uploads into one space.

        Wraps ``POST /files/upload-urls``. ``body`` is an ``UploadUrlsRequest``:
        ``space_id`` and ``files``, 1 to 100 of ``{file_name, size_bytes,
        relative_path?}``. Their total size is checked against the space's quota
        once, before any URL is issued. Upload each file to its ``upload_url``,
        then register the ``blob_name`` values with :meth:`register_entries`.

        Warning:
            Each ``upload_url`` grants write access to its blob until
            ``expires_at``: do not log it.

        Args:
            body: An ``UploadUrlsRequest`` object, sent as the JSON body.

        Returns:
            :class:`UploadUrlsResponse`: ``targets``, one per file in request order.

        Raises:
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoNotFoundError: For a space that does not exist or is not the
                organization's (``404``).
            PerceivoAPIError: On another error response, ``422``
                (``PerceivoValidationError``) for a malformed body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(UploadUrlsResponse, self._post(f"{_FILES}/upload-urls", json=body))

    def register_entries(self, space_id: str, body: dict[str, Any]) -> RegisterFileEntriesResult:
        """Register up to 100 directly-uploaded files as entries of a space.

        Wraps ``POST /files/spaces/{space_id}/entries/batch``. ``body`` is a
        ``RegisterFileEntries``: ``files``, 1 to 100 of ``{blob_name, file_name,
        file_path, size_bytes, parent_id?, mime_type?, checksum_md5?,
        version_comment?}``, each ``blob_name`` as :meth:`create_upload_urls`
        returned it for this space. If any file's parent folder or ``blob_name``
        is refused, the whole call is refused and nothing is registered;
        otherwise every file gets an outcome in ``results``.

        Args:
            space_id: The space the files were uploaded to.
            body: A ``RegisterFileEntries`` object, sent as the JSON body.

        Returns:
            :class:`RegisterFileEntriesResult`: ``success_count``, ``failed_count``
            and ``results``, one per file in request order.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..``.
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoNotFoundError: For a space or parent folder that does not
                exist or is not the organization's (``404``).
            PerceivoAPIError: ``422`` (``PerceivoValidationError``) for a
                malformed body or a ``blob_name`` not issued for this space.
            PerceivoConnectionError: If the API cannot be reached.
        """
        path = f"{_FILES}/spaces/{segment(space_id, 'space_id')}/entries/batch"
        return self._model(RegisterFileEntriesResult, self._post(path, json=body))
