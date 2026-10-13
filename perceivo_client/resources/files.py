"""Files namespace (``client.files``): storage spaces and the files and folders in them.

A file or folder is an **entry**, addressed by its entry id, and lives in a
**storage space**. This namespace manages spaces and their usage, lists,
reads, changes, copies, moves and deletes entries, uploads and downloads file
content, and works with the trash.
"""

from __future__ import annotations

from typing import IO, Any

from perceivo_client._paths import segment
from perceivo_client._transport import _LONG_TIMEOUT
from perceivo_client.generated.models import (
    BulkOperationResult,
    FileEntryRead,
    FileUploadBatchResult,
    PaginatedFileList,
    StorageSpaceRead,
    StorageUsageRead,
    UploadResponse,
    UploadTargetResponse,
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources._multipart import file_part, refuse_if_signing

_FILES = "/v1/files"
#: The file name a replacement part carries. The API keeps the entry's own name
#: and reads only the bytes, so this is a label, not data.
_REPLACE_FILENAME = "content"


class FilesResource(BaseResource):
    """Storage spaces, files and folders: upload, download, copy, move, trash and restore."""

    # --- storage spaces ---
    def list_spaces(self) -> list[StorageSpaceRead]:
        """Every storage space of the organization (``GET /files/spaces``).

        The route is not paged. ``used_bytes`` is computed when it is read.

        Returns:
            ``list[StorageSpaceRead]``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(StorageSpaceRead, self._get(f"{_FILES}/spaces"))

    def get_space(self, space_id: str) -> StorageSpaceRead:
        """One storage space (``GET /files/spaces/{space_id}``).

        Args:
            space_id: The space to read.

        Returns:
            :class:`StorageSpaceRead`.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            StorageSpaceRead, self._get(f"{_FILES}/spaces/{segment(space_id, 'space_id')}")
        )

    def create_space(self, body: dict[str, Any]) -> StorageSpaceRead:
        """Create a storage space (``POST /files/spaces``, ``201``).

        ``body`` is a ``StorageSpaceCreate``: ``name`` is required;
        ``description``, ``quota_bytes`` and ``is_default`` are optional. The
        organization is the API key's own and cannot be set by the caller.

        Args:
            body: A ``StorageSpaceCreate`` object, sent as the JSON body.

        Returns:
            :class:`StorageSpaceRead`: the new space.

        Raises:
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(StorageSpaceRead, self._post(f"{_FILES}/spaces", json=body))

    def update_space(self, space_id: str, body: dict[str, Any]) -> StorageSpaceRead:
        """Change a space's name, description, quota or default flag.

        Wraps ``PATCH /files/spaces/{space_id}``. ``body`` is a
        ``StorageSpaceUpdate``; omitted fields are left as they are.

        Args:
            space_id: The space to update.
            body: A ``StorageSpaceUpdate`` object, sent as the JSON body.

        Returns:
            :class:`StorageSpaceRead`: the space after the update.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            StorageSpaceRead,
            self._patch(f"{_FILES}/spaces/{segment(space_id, 'space_id')}", json=body),
        )

    def delete_space(self, space_id: str, *, force: bool = False) -> None:
        """Delete a storage space (``DELETE /files/spaces/{space_id}``, ``204``).

        A space that still holds files is refused unless ``force`` is true,
        which deletes it with everything in it. Irreversible.

        Args:
            space_id: The space to delete.
            force: Send ``force=true`` as a query parameter, deleting a space
                that still holds files. Omitted (not sent) when false; the
                route's default is ``false``.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_DELETE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request. A
                non-empty space is refused without ``force``; the contract names no status for that.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_FILES}/spaces/{segment(space_id, 'space_id')}",
            params={"force": True} if force else None,
        )

    def get_space_usage(self, space_id: str) -> StorageUsageRead:
        """Bytes and entry counts of a space, trash included (``GET .../usage``).

        Wraps ``GET /files/spaces/{space_id}/usage``.

        Args:
            space_id: The space to measure.

        Returns:
            :class:`StorageUsageRead`.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            StorageUsageRead,
            self._get(f"{_FILES}/spaces/{segment(space_id, 'space_id')}/usage"),
        )

    # --- entries ---
    def list_entries(
        self,
        space_id: str,
        *,
        query: str | None = None,
        parent_id: str | None = None,
        include_trashed: bool | None = None,
        starred_only: bool | None = None,
        entry_type: str | None = None,
        mime_type: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> PaginatedFileList:
        """One page of a space's entries (``GET /files/spaces/{space_id}/entries``).

        Without ``query`` this browses one folder (``parent_id``; the space
        root when omitted). With ``query`` it searches the whole space by name.
        A parameter of the other mode is ignored, not refused: ``parent_id``
        does not narrow a search. An ``items,total`` page, so
        ``paginate_pages(functools.partial(client.files.list_entries,
        space_id))`` walks it.

        Args:
            space_id: The space to list.
            query: Search term, at least one character; selects search mode.
            parent_id: Browse: the folder to list. Omitted, the root.
            include_trashed: Browse: include trashed entries.
            starred_only: Browse: only starred entries.
            entry_type: Search: ``file`` or ``folder``.
            mime_type: Search: only entries of this media type.
            sort_by: Browse: ``name`` (the default), ``created_at`` or
                ``updated_at``. Folders are always listed before files, each
                group sorted by this key.
            sort_order: Browse: ``asc`` (the default) or ``desc``; any other
                value is refused with ``422``.
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Entries per page, ``1`` to ``100``. Omitted, the API
                uses ``50``.

        Returns:
            :class:`PaginatedFileList`: ``items``, ``total``, ``page``,
            ``page_size`` and ``total_pages``.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a space that does not exist or
                belongs to another organization, and ``422``
                (``PerceivoValidationError``) for a parameter out of range.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "query": query,
            "parent_id": parent_id,
            "include_trashed": include_trashed,
            "starred_only": starred_only,
            "entry_type": entry_type,
            "mime_type": mime_type,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "page": page,
            "page_size": page_size,
        }
        return self._model(
            PaginatedFileList,
            self._get(f"{_FILES}/spaces/{segment(space_id, 'space_id')}/entries", params=params),
        )

    def create_entry(self, space_id: str, body: dict[str, Any]) -> FileEntryRead | UploadResponse:
        """Create a folder, or register a file uploaded through :meth:`create_upload_url`.

        Wraps ``POST /files/spaces/{space_id}/entries``. ``body`` carries
        ``type``. ``{"type": "folder", "name": ...}`` creates a folder and
        answers ``201`` with its :class:`FileEntryRead`. ``{"type": "file",
        "blob_name": ..., "file_name": ..., "file_path": ..., "size_bytes":
        ...}`` registers the blob and answers ``200`` with an
        :class:`UploadResponse` (``entry`` and ``version``); registering the
        same blob twice adds a version to the existing entry rather than
        creating a second one. ``blob_name`` must be the key that this space's
        own upload URL returned.

        The two answers are told apart by their shape: an object carrying
        ``entry`` is an :class:`UploadResponse`.

        Args:
            space_id: The space to create the entry in.
            body: The entry to create, sent as the JSON body: a
                ``CreateFolderEntry`` (``type="folder"``) or a
                ``RegisterFileEntry`` (``type="file"``), told apart by ``type``.

        Returns:
            :class:`FileEntryRead` for a folder, or :class:`UploadResponse`
            (``entry`` and ``version``) for a registered file.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        data = self._post(f"{_FILES}/spaces/{segment(space_id, 'space_id')}/entries", json=body)
        if isinstance(data, dict) and "entry" in data:
            return self._model(UploadResponse, data)
        return self._model(FileEntryRead, data)

    def get_entry(self, entry_id: str) -> FileEntryRead:
        """Metadata of one file or folder (``GET /files/entries/{entry_id}``).

        A trashed entry is returned too, with ``is_trashed`` set.

        Args:
            entry_id: The file or folder to read.

        Returns:
            :class:`FileEntryRead`.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an entry that does not exist or
                belongs to another organization, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            FileEntryRead, self._get(f"{_FILES}/entries/{segment(entry_id, 'entry_id')}")
        )

    def update_entry(self, entry_id: str, body: dict[str, Any]) -> FileEntryRead:
        """Rename, star or unstar a file or folder (``PATCH /files/entries/{entry_id}``).

        ``body`` is a ``FileEntryUpdate`` (``name``, ``is_starred``). To
        relocate an entry use :meth:`move`.

        Args:
            entry_id: The file or folder to update.
            body: A ``FileEntryUpdate`` object, sent as the JSON body.

        Returns:
            :class:`FileEntryRead`: the entry after the update.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown entry, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            FileEntryRead,
            self._patch(f"{_FILES}/entries/{segment(entry_id, 'entry_id')}", json=body),
        )

    def delete_entry(self, entry_id: str, *, permanent: bool = False) -> Any:
        """Delete a file or folder (``DELETE /files/entries/{entry_id}``).

        The entry, with everything under it, goes to the space's trash, from
        which :meth:`restore_entry` brings it back. With ``permanent`` it is
        deleted outright, versions and stored content included, and cannot be
        restored.

        Args:
            entry_id: The file or folder to delete.
            permanent: Send ``permanent=true``, bypassing the trash. Omitted
                (not sent) when false.

        Returns:
            ``None`` when the deletion completed (``204``). A permanent delete
            of a folder holding more than 100 items answers ``202`` while the
            stored content is removed in the background; the decoded body
            (``message``, ``entry_id``, ``blob_count``) is returned unvalidated.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_DELETE`` (``403``).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an entry that does not exist or
                belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``423`` while the organization is under a data hold.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_FILES}/entries/{segment(entry_id, 'entry_id')}",
            params={"permanent": True} if permanent else None,
        )

    def copy(self, entry_id: str, body: dict[str, Any] | None = None) -> BulkOperationResult:
        """Copy a file or folder (``POST /files/entries/{entry_id}/copy``).

        ``body`` is a ``FileEntryCopy``: ``dest_parent_id`` names the
        destination folder. Without it (an empty object is sent when no body is
        given) the copy lands at the root of the same space. A folder is copied
        with everything inside it. Read ``failed_count`` on the result.

        Args:
            entry_id: The file or folder to copy.
            body: An optional ``FileEntryCopy`` object, sent as the JSON body;
                ``None`` sends ``{}``.

        Returns:
            :class:`BulkOperationResult`: what was copied and what failed.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown entry, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BulkOperationResult,
            self._post(
                f"{_FILES}/entries/{segment(entry_id, 'entry_id')}/copy",
                json={} if body is None else body,
            ),
        )

    def move(self, entry_id: str, body: dict[str, Any] | None = None) -> FileEntryRead:
        """Move a file or folder (``POST /files/entries/{entry_id}/move``).

        ``body`` is a ``FileEntryMove``: ``new_parent_id`` names the
        destination folder. Without it (an empty object is sent when no body is
        given) the entry moves to the root of its space.

        Args:
            entry_id: The file or folder to move.
            body: An optional ``FileEntryMove`` object, sent as the JSON body;
                ``None`` sends ``{}``.

        Returns:
            :class:`FileEntryRead`: the entry at its new location.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown entry, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            FileEntryRead,
            self._post(
                f"{_FILES}/entries/{segment(entry_id, 'entry_id')}/move",
                json={} if body is None else body,
            ),
        )

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
                enabled. A multipart body is built by ``httpx`` as a streaming
                body that this client cannot sign, and it refuses to send an
                unsigned request from a signing client.
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
        refuse_if_signing(self._t, "files.upload")
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
            perceivo_client.signing.SigningError: If request signing is enabled,
                for the reason :meth:`upload` gives.
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown entry, ``409`` (``PerceivoConflictError``) for a folder or a trashed file,
                ``413`` (bare ``PerceivoAPIError``) for a request body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        refuse_if_signing(self._t, "files.replace_content")
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

    # --- trash ---
    def list_trash(
        self, space_id: str, *, page: int | None = None, page_size: int | None = None
    ) -> PaginatedFileList:
        """One page of a space's trashed entries (``GET .../spaces/{space_id}/trash``).

        An ``items,total`` page, so
        ``paginate_pages(functools.partial(client.files.list_trash, space_id))``
        walks it.

        Args:
            space_id: The space whose trash to list.
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Entries per page, ``1`` to ``100``. Omitted, the API
                uses ``50``.

        Returns:
            :class:`PaginatedFileList`: one ``items``/``total`` page.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PaginatedFileList,
            self._get(
                f"{_FILES}/spaces/{segment(space_id, 'space_id')}/trash",
                params={"page": page, "page_size": page_size},
            ),
        )

    def empty_trash(self, space_id: str) -> Any:
        """Permanently delete every trashed entry in a space (``DELETE .../trash``).

        Irreversible. The API answers ``200`` with ``deleted_count`` when the
        deletion completed, or ``202`` with ``deleted_count`` and ``message``
        while the stored content of a large trash is removed in the
        background; the contract declares no model for either body, so the
        decoded JSON is returned as is.

        Wraps ``DELETE /files/spaces/{space_id}/trash``.

        Args:
            space_id: The space whose trash to empty.

        Returns:
            The decoded JSON body, unvalidated (``None`` for an empty body).
            The contract's ``200`` schema is empty (untyped). The ``202`` the
            description names is not a declared response.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_DELETE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_FILES}/spaces/{segment(space_id, 'space_id')}/trash")

    def restore_entry(self, entry_id: str) -> FileEntryRead:
        """Restore one trashed file or folder to where it was.

        Wraps ``POST /files/trash/{entry_id}/restore``; needs ``FILE_WRITE``.
        Everything under a folder is restored with it. An entry outside your
        organization answers ``404``; one that is not in the trash, or whose
        folder is still trashed, answers ``400``. The route takes no request
        body.

        Args:
            entry_id: The trashed file or folder to restore.

        Returns:
            :class:`FileEntryRead`: the restored entry.

        Raises:
            ValueError: If ``entry_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response: ``400`` for an entry that
                is not in the trash or whose folder is trashed, ``404``
                (``PerceivoNotFoundError``) for an entry outside your
                organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when ownership could not be
                established, so nothing was restored.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            FileEntryRead,
            self._post(f"{_FILES}/trash/{segment(entry_id, 'entry_id')}/restore"),
        )

    def restore_entries(self, body: dict[str, Any]) -> BulkOperationResult:
        """Restore up to a hundred trashed entries (``POST /files/trash/restore``).

        ``body`` is a ``FileTrashRestore`` (``entry_ids``, one to a hundred);
        needs ``FILE_WRITE``. If any id is not an entry of your organization the
        request answers ``404`` and nothing is restored; otherwise read
        ``failed_count`` and ``failed_ids`` on the result.

        Args:
            body: A ``FileTrashRestore`` object, sent as the JSON body.

        Returns:
            :class:`BulkOperationResult`: what was restored and what failed.

        Raises:
            PerceivoGrantError: For a key without ``FILE_WRITE`` (``403``).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) when any id is not an entry of your
                organization or does not exist (nothing is restored), ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when ownership could not be
                established, so nothing was restored.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(BulkOperationResult, self._post(f"{_FILES}/trash/restore", json=body))
