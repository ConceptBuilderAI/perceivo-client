"""Entries (files and folders) of ``client.files``: list, read, change, copy, move, delete."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    BulkOperationResult,
    FileEntryRead,
    PaginatedFileList,
    UploadResponse,
)
from perceivo_client.resources.files._common import _FILES

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _EntriesMixin(_MixinBase):
    """Entries (files and folders) of ``client.files``: list, read, change, copy, move, delete."""

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
            PerceivoGrantError: For a key without ``FILE_READ`` (``403``).
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
