"""Shared pieces of the infrastructure namespace's mixins.

The endpoint prefixes, the import-file helpers and the multipart senders the
search-index, vector-store and cache mixins share.

``_MixinBase`` is :class:`~perceivo_client.resources._base.BaseResource` to a type
checker and ``object`` at runtime, so each mixin sees the request helpers without
putting ``BaseResource`` into the method resolution order more than once.
"""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, Any

from perceivo_client._transport import _LONG_TIMEOUT
from perceivo_client.generated.models import CollectionWriteResult, DocumentUploadResponse
from perceivo_client.resources._multipart import file_part

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object

_BASE = "/v1/infrastructure"
_CLUSTER = f"{_BASE}/cluster"
_NODEPOOLS = f"{_CLUSTER}/nodepools"
_MCP = f"{_CLUSTER}/mcp"
_SEARCH = f"{_BASE}/search-index/indices"
_VECTOR = f"{_BASE}/vector-store/collections"
#: The file name an import part carries. The API discards the caller's name
#: and reads only the bytes, so this is a label, not data.
_IMPORT_FILENAME = "import.ndjson"
_IMPORT_CONTENT_TYPE = "application/x-ndjson"

#: What an import accepts: the NDJSON text the matching export returned, or the
#: export file as bytes or a binary file object.
_ImportData = str | bytes | IO[bytes]


def _import_file(data: _ImportData) -> bytes | IO[bytes]:
    """The bytes of an import part.

    The export operations return their newline-delimited JSON as ``str``, and the
    import operations take that file back unchanged, so text is encoded to UTF-8
    as it is. ``bytes`` and binary file objects are the file already and pass
    through.
    """
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


class _MultipartMixin(_MixinBase):
    # -- multipart helpers --------------------------------------------------
    def _ingest(
        self,
        method_name: str,
        path: str,
        filename: str,
        data: bytes | IO[bytes],
        content_type: str | None,
        fields: dict[str, str | int | None],
    ) -> DocumentUploadResponse:
        """Send one document to an ingest operation as ``multipart/form-data``.

        The document is the part named ``files``; every option that is not
        ``None`` is a form field of its own.
        """
        parts: dict[str, Any] = {"files": file_part(filename, data, content_type)}
        for name, value in fields.items():
            if value is not None:
                # A (None, value) part has no filename: a plain form field.
                parts[name] = (None, str(value))
        return self._model(
            DocumentUploadResponse, self._post(path, files=parts, min_timeout=_LONG_TIMEOUT)
        )

    def _import(self, method_name: str, path: str, data: _ImportData) -> CollectionWriteResult:
        """Send an export file to an import operation as ``multipart/form-data``.

        The file is the one part, named ``file``; the API accepts no other
        field and discards the part's file name.
        """
        parts = {"file": (_IMPORT_FILENAME, _import_file(data), _IMPORT_CONTENT_TYPE)}
        return self._model(CollectionWriteResult, self._post(path, files=parts))
