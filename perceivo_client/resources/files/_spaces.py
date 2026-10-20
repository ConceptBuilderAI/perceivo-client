"""Storage spaces and the trash of ``client.files``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    BulkOperationResult,
    EmptyTrashResult,
    FileEntryRead,
    PaginatedFileList,
    StorageSpaceRead,
    StorageUsageRead,
)
from perceivo_client.resources.files._common import _FILES

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _SpacesMixin(_MixinBase):
    """Storage spaces and the trash of ``client.files``."""

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

    def empty_trash(self, space_id: str) -> EmptyTrashResult:
        """Permanently delete every trashed entry in a space (``DELETE .../trash``).

        Irreversible. The API answers ``200`` with ``deleted_count`` when the
        deletion completed, or ``202`` with ``deleted_count`` and ``message``
        while the stored content of a large trash is removed in the
        background.

        Wraps ``DELETE /files/spaces/{space_id}/trash``.

        Args:
            space_id: The space whose trash to empty.

        Returns:
            :class:`EmptyTrashResult` — ``deleted_count``, and ``message`` on a
            ``202``.

        Raises:
            ValueError: If ``space_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``FILE_DELETE`` (``403``).
            PerceivoAPIError: On an error response: ``404`` (``PerceivoNotFoundError``) for an
                unknown space, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            EmptyTrashResult,
            self._delete(f"{_FILES}/spaces/{segment(space_id, 'space_id')}/trash"),
        )

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
