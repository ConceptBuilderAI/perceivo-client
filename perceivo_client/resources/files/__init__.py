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
    EmptyTrashResult,
    FileEntryRead,
    FileUploadBatchResult,
    PaginatedFileList,
    StorageSpaceRead,
    StorageUsageRead,
    UploadResponse,
    UploadTargetResponse,
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources._multipart import file_part
from perceivo_client.resources.files._batch import _BatchMixin
from perceivo_client.resources.files._common import _FILES, _REPLACE_FILENAME
from perceivo_client.resources.files._content import _ContentMixin
from perceivo_client.resources.files._entries import _EntriesMixin
from perceivo_client.resources.files._spaces import _SpacesMixin

# ``IO``, ``Any``, ``segment``, ``_LONG_TIMEOUT``, ``file_part``, the models and the
# path constants are re-exported from this module.


class FilesResource(_SpacesMixin, _EntriesMixin, _ContentMixin, _BatchMixin, BaseResource):
    """Storage spaces, files and folders: upload, download, copy, move, trash and restore."""
