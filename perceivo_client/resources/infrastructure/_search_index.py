"""The search index (Elasticsearch): indices, documents, query, export, import and ingest.

One of the mixins that make up
:class:`~perceivo_client.resources.infrastructure.InfrastructureResource`.
"""

from __future__ import annotations

from typing import IO, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    CollectionDataPage,
    CollectionDetail,
    CollectionList,
    CollectionQueryResult,
    CollectionWriteResult,
    DocumentUploadResponse,
    SearchIndexCreated,
    SearchIndexDeleted,
)
from perceivo_client.resources.infrastructure._common import (
    _SEARCH,
    _ImportData,
    _MultipartMixin,
)


class _SearchIndexMixin(_MultipartMixin):
    # -- search index (Elasticsearch) ---------------------------------------
    def list_search_indices(self) -> CollectionList:
        """List the search indices (``GET /infrastructure/search-index/indices``).

        Returns:
            :class:`CollectionList` — the indices under ``indices``, read from
            ``model_extra``.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(CollectionList, self._get(_SEARCH))

    def get_search_index(self, index_name: str) -> CollectionDetail:
        """Describe one search index (``GET .../search-index/indices/{name}``).

        Args:
            index_name: The index to describe.

        Returns:
            :class:`CollectionDetail` — the index's mapping and statistics, in
            Elasticsearch's own terms.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For an unknown index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionDetail, self._get(f"{_SEARCH}/{segment(index_name, 'index_name')}")
        )

    def create_search_index(self, body: dict[str, Any]) -> SearchIndexCreated:
        """Create a search index (``POST /infrastructure/search-index/indices``).

        Args:
            body: A ``CollectionCreate`` object in the platform's own create
                shape, not Elasticsearch's create-index API: ``name`` (1 to
                255 characters, required), ``mappings`` (an Elasticsearch
                mappings object) and ``settings`` (an Elasticsearch index
                settings object). Any other key is dropped without an error,
                and the index is still created (``201``).

        Returns:
            :class:`SearchIndexCreated` — ``created`` and the ``index`` name (``201``).

        Raises:
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response, including ``400`` for an
                invalid name or definition, or a name already in use.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(SearchIndexCreated, self._post(_SEARCH, json=body))

    def delete_search_index(self, index_name: str) -> SearchIndexDeleted:
        """Delete a search index and everything in it (``DELETE .../indices/{name}``).

        Irreversible: :meth:`export_search_index` it first if its contents
        matter.

        Args:
            index_name: The index to delete.

        Returns:
            :class:`SearchIndexDeleted` — ``deleted`` and the ``index`` name.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``INFRA_DEPROVISION``
                (``403``).
            PerceivoNotFoundError: For an unknown index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SearchIndexDeleted, self._delete(f"{_SEARCH}/{segment(index_name, 'index_name')}")
        )

    def list_search_index_documents(
        self, index_name: str, *, page: int | None = None, page_size: int | None = None
    ) -> CollectionDataPage:
        """Read one page of a search index's documents (``GET .../indices/{name}/documents``).

        The page is Elasticsearch's own body, and its ``total`` may count only
        this page, so neither pagination helper walks it: request the next page
        until a short or empty one comes back.

        Args:
            index_name: The index to read.
            page: Page number, 1 or more; the server default is ``1``.
            page_size: Documents per page, 1 to 100; the server default is
                ``20``. A larger value is refused, not reduced.

        Returns:
            :class:`CollectionDataPage` — one page, in Elasticsearch's terms.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For an unknown index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoValidationError: For an out-of-range ``page`` or
                ``page_size`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionDataPage,
            self._get(
                f"{_SEARCH}/{segment(index_name, 'index_name')}/documents",
                params={"page": page, "page_size": page_size},
            ),
        )

    def add_search_index_document(
        self, index_name: str, body: dict[str, Any]
    ) -> CollectionWriteResult:
        """Add one document to a search index (``POST .../indices/{name}/documents``).

        Nothing is embedded: the document is stored as sent.

        Args:
            index_name: The index to add to.
            body: A ``CollectionDataWrite`` object in Elasticsearch's record
                format: a ``document`` and an optional ``doc_id``.

        Returns:
            :class:`CollectionWriteResult` — what the write stored (``201``).

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoNotFoundError: For an unknown index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response, including ``400``
                for a document the store refuses.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionWriteResult,
            self._post(f"{_SEARCH}/{segment(index_name, 'index_name')}/documents", json=body),
        )

    def delete_search_index_document(
        self, index_name: str, document_id: str
    ) -> CollectionWriteResult:
        """Delete one document (``DELETE .../indices/{name}/documents/{document_id}``).

        Args:
            index_name: The index holding the document.
            document_id: The document's id, encoded as one path segment.

        Returns:
            :class:`CollectionWriteResult` — what the delete removed.

        Raises:
            ValueError: If ``index_name`` or ``document_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown document or index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionWriteResult,
            self._delete(
                f"{_SEARCH}/{segment(index_name, 'index_name')}/documents/{segment(document_id, 'document_id')}"
            ),
        )

    def query_search_index(self, index_name: str, body: dict[str, Any]) -> CollectionQueryResult:
        """Search one index (``POST .../search-index/indices/{name}/search``).

        Args:
            index_name: The index to search.
            body: A ``CollectionQuery`` object in the platform's own search
                shape, not Elasticsearch Query DSL: ``query`` (a query-string
                expression, required), ``fields`` (the fields to search),
                ``from`` (offset, default 0), ``size`` (1 to 1000, default
                20), ``sort`` (one field, sorted descending) and
                ``highlight`` (default true). The platform builds a
                ``query_string`` query from them. A Query DSL body such as
                ``{"query": {"match": ...}}`` is refused with ``422``.

        Returns:
            :class:`CollectionQueryResult` — ``hits`` (each with ``_id``,
            ``_score``, ``_source`` and ``highlight``), ``total``,
            ``took_ms`` and ``max_score``.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For an unknown index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoValidationError: For a body that is not the platform's
                search shape, including Query DSL (``422``).
            PerceivoAPIError: On any other error response, including ``400``
                for a query string the store refuses.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionQueryResult,
            self._post(f"{_SEARCH}/{segment(index_name, 'index_name')}/search", json=body),
        )

    def export_search_index(self, index_name: str) -> str:
        """Export a search index's documents as NDJSON (``POST .../indices/{name}/export``).

        At most the first 10,000 documents are exported, and a failure part
        way, or an unknown index, can answer a truncated or empty export rather
        than an error: compare the line count with the index's document count.
        A large export can outlast the client's default 30 s timeout. Sent
        once, not retried.

        Args:
            index_name: The index to export.

        Returns:
            ``str`` — the export file exactly as the API sent it:
            newline-delimited JSON, one object per line. Pass it unchanged to
            :meth:`import_search_index`.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached, or the
                transfer outlasts the client's timeout.
        """
        # Read as text, not decoded as JSON: the body is NDJSON, and a JSON
        # decode would turn a one-line export into an object.
        return self._t.request("POST", f"{_SEARCH}/{segment(index_name, 'index_name')}/export").text

    def import_search_index(self, index_name: str, data: _ImportData) -> CollectionWriteResult:
        """Load an export file into a search index (``POST .../indices/{name}/import``).

        Importing into an index that already holds the rows adds them again.

        Args:
            index_name: The index to load into.
            data: The NDJSON text :meth:`export_search_index` returned, or the
                export file as bytes or a seekable binary file object. Sent as
                the multipart part ``file``; text is encoded to UTF-8.

        Returns:
            :class:`CollectionWriteResult` — what the import stored.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            perceivo_client.signing.SigningError: If request signing is on and
                the request cannot be signed. A signed multipart body is held in memory.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response, including ``411``
                without a ``Content-Length`` and ``413`` for a request over
                16 MiB.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._import(
            "import_search_index", f"{_SEARCH}/{segment(index_name, 'index_name')}/import", data
        )

    def ingest_search_index(
        self,
        index_name: str,
        filename: str,
        data: bytes | IO[bytes],
        *,
        content_type: str | None = None,
        text_field: str | None = None,
        vector_field: str | None = None,
        embedding_model: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> DocumentUploadResponse:
        """Chunk, embed and index one document (``POST .../indices/{name}/ingest``).

        The API answers ``200`` even when the document is refused: read the result's ``files``
        entry, whose ``status`` is ``completed``, ``error``, ``not_attempted`` (the time budget ran
        out first; nothing was written) or ``timeout``; the last two are not counted in the totals.
        A ``timeout``, or a ``504``, may still complete: read the store back before sending it
        again. Embedding is billed.

        Waits at least 150 s for the response; raise it with ``client.with_options(timeout=...)``.

        Args:
            index_name: The index to ingest into.
            filename: The document's file name; its extension must be
                ``.csv``, ``.json``, ``.jsonl``, ``.md`` or ``.txt``.
            data: The document, at most 10 MiB, as bytes or a seekable binary file object.
            content_type: The document's media type. Omitted, none is sent.
            text_field: The text field to fill. Omitted, the API detects it.
            vector_field: The vector field to fill. Omitted, the API detects it.
            embedding_model: The embedding model. Omitted, the API picks one
                that matches the vector field's dimensions.
            chunk_size: Characters per chunk; the server default is ``500``.
            chunk_overlap: Characters shared by adjacent chunks; the server default is ``50``.

        Returns:
            :class:`DocumentUploadResponse` — totals and one ``files`` entry.

        Raises:
            ValueError: If ``index_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            perceivo_client.signing.SigningError: If request signing is on and
                the request cannot be signed. A signed multipart body is held in memory.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoAPIError: On any other error response, including ``400`` for an unsupported
                file or an undetectable field, ``413`` for a file over 10 MiB, and ``504``
                (``PerceivoServerError``) when the ingest timed out.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._ingest(
            "ingest_search_index",
            f"{_SEARCH}/{segment(index_name, 'index_name')}/ingest",
            filename,
            data,
            content_type,
            {
                "text_field": text_field,
                "vector_field": vector_field,
                "embedding_model": embedding_model,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
        )
