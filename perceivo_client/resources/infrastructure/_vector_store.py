"""The vector store (Milvus): collections, entities, query, export, import and ingest.

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
    VectorStoreCollectionCreated,
    VectorStoreCollectionDeleted,
)
from perceivo_client.resources.infrastructure._common import (
    _VECTOR,
    _ImportData,
    _MultipartMixin,
)


class _VectorStoreMixin(_MultipartMixin):
    # -- vector store (Milvus) ----------------------------------------------
    def list_vector_store_collections(self) -> CollectionList:
        """List the vector-store collections (``GET /infrastructure/vector-store/collections``).

        Returns:
            :class:`CollectionList` — the collections under ``collections``,
            read from ``model_extra``.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(CollectionList, self._get(_VECTOR))

    def get_vector_store_collection(self, collection_name: str) -> CollectionDetail:
        """Describe one vector-store collection (``GET .../collections/{name}``).

        Args:
            collection_name: The collection to describe.

        Returns:
            :class:`CollectionDetail` — the collection's schema and statistics,
            in Milvus's own terms.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoNotFoundError: For an unknown collection (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionDetail, self._get(f"{_VECTOR}/{segment(collection_name, 'collection_name')}")
        )

    def create_vector_store_collection(self, body: dict[str, Any]) -> VectorStoreCollectionCreated:
        """Create a vector-store collection (``POST /infrastructure/vector-store/collections``).

        Args:
            body: A ``CollectionCreate`` object in the platform's own create
                shape, not Milvus's: ``name`` and ``schema`` are required.
                ``schema`` is ``{"fields": [...]}``, each field an object with
                ``name``, ``dtype`` (a Milvus ``DataType`` name such as
                ``INT64`` or ``FLOAT_VECTOR``), and optionally ``is_primary``,
                ``auto_id``, ``dim`` and ``max_length``. ``description`` is
                optional. ``index`` is an optional ``{"field_name",
                "index_type", "metric_type", "params"}`` object; with it the
                collection is indexed and loaded, ready to search. Any other
                key is dropped without an error.

        Returns:
            :class:`VectorStoreCollectionCreated` — ``created`` and the
            ``collection`` name (``201``).

        Raises:
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoConflictError: For a collection that already exists, or
                while Milvus is not running (``409``).
            PerceivoValidationError: For a malformed body, including one
                without ``schema`` (``422``).
            PerceivoAPIError: On any other error response, including ``400``
                for an unknown ``dtype``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(VectorStoreCollectionCreated, self._post(_VECTOR, json=body))

    def delete_vector_store_collection(self, collection_name: str) -> VectorStoreCollectionDeleted:
        """Delete a vector-store collection and everything in it (``DELETE .../collections/{name}``).

        Irreversible: :meth:`export_vector_store_collection` it first if its
        contents matter.

        Args:
            collection_name: The collection to delete.

        Returns:
            :class:`VectorStoreCollectionDeleted` — ``dropped`` and the
            ``collection`` name.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INFRA_DEPROVISION``
                (``403``).
            PerceivoNotFoundError: For an unknown collection (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            VectorStoreCollectionDeleted,
            self._delete(f"{_VECTOR}/{segment(collection_name, 'collection_name')}"),
        )

    def list_vector_store_entities(
        self, collection_name: str, *, page: int | None = None, page_size: int | None = None
    ) -> CollectionDataPage:
        """Read one page of a collection's entities (``GET .../collections/{name}/entities``).

        The page is Milvus's own body, and its ``total`` may count only this
        page, so neither pagination helper walks it: request the next page
        until a short or empty one comes back.

        Args:
            collection_name: The collection to read.
            page: Page number, 1 or more; the server default is ``1``.
            page_size: Entities per page, 1 to 100; the server default is
                ``20``. A larger value is refused, not reduced.

        Returns:
            :class:`CollectionDataPage` — one page, in Milvus's terms.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoNotFoundError: For an unknown collection (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoValidationError: For an out-of-range ``page`` or
                ``page_size`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionDataPage,
            self._get(
                f"{_VECTOR}/{segment(collection_name, 'collection_name')}/entities",
                params={"page": page, "page_size": page_size},
            ),
        )

    def add_vector_store_entities(
        self, collection_name: str, body: dict[str, Any]
    ) -> CollectionWriteResult:
        """Add entities to a collection (``POST .../collections/{name}/entities``).

        Nothing is embedded: each entity carries its own vector. Adding the
        same entities twice inserts them twice.

        Args:
            collection_name: The collection to add to.
            body: A ``CollectionDataWrite`` object in Milvus's record format:
                ``entities``, a list of 1 to 1000 objects.

        Returns:
            :class:`CollectionWriteResult` — what the write stored (``201``).

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown collection (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response, including ``400``
                for entities the store refuses.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionWriteResult,
            self._post(
                f"{_VECTOR}/{segment(collection_name, 'collection_name')}/entities", json=body
            ),
        )

    def delete_vector_store_entity(
        self, collection_name: str, entity_id: str
    ) -> CollectionWriteResult:
        """Delete one entity (``DELETE .../collections/{name}/entities/{entity_id}``).

        Deleting an entity that does not exist also answers success.

        Args:
            collection_name: The collection holding the entity.
            entity_id: The entity's primary key, encoded as one path segment.

        Returns:
            :class:`CollectionWriteResult` — what the delete removed.

        Raises:
            ValueError: If ``collection_name`` or ``entity_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown collection (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionWriteResult,
            self._delete(
                f"{_VECTOR}/{segment(collection_name, 'collection_name')}/entities/{segment(entity_id, 'entity_id')}"
            ),
        )

    def query_vector_store_collection(
        self, collection_name: str, body: dict[str, Any]
    ) -> CollectionQueryResult:
        """Run a similarity search on a collection (``POST .../collections/{name}/search``).

        Args:
            collection_name: The collection to search.
            body: A ``CollectionQuery`` object in the platform's own search
                shape, not Milvus's: ``vector`` (the query vector) or
                ``entity_id`` (search with that entity's stored vector) is
                required, with ``top_k`` (1 to 1000, default 10), ``filter``
                (a Milvus boolean expression), ``search_params`` and
                ``output_fields``. A body with neither ``vector`` nor
                ``entity_id``, such as Milvus's own ``data``/``limit``
                keys, is refused with ``400``.

        Returns:
            :class:`CollectionQueryResult` — ``results`` (each with ``id``,
            ``distance`` and ``entity``), ``total_results`` and
            ``search_time_ms``.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoNotFoundError: For an unknown collection, or an
                ``entity_id`` the collection does not hold (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response, including ``400``
                for a body with neither ``vector`` nor ``entity_id``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CollectionQueryResult,
            self._post(
                f"{_VECTOR}/{segment(collection_name, 'collection_name')}/search", json=body
            ),
        )

    def export_vector_store_collection(self, collection_name: str) -> str:
        """Export a collection's entities as NDJSON (``POST .../collections/{name}/export``).

        At most the first 10,000 entities are exported, and a failure part
        way, or an unknown collection, can answer a truncated or empty export
        rather than an error: compare the line count with the collection's
        entity count. A large export can outlast the client's default 30 s
        timeout. Sent once, not retried.

        Args:
            collection_name: The collection to export.

        Returns:
            ``str`` — the export file exactly as the API sent it:
            newline-delimited JSON, one object per line. Pass it unchanged to
            :meth:`import_vector_store_collection`.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached, or the
                transfer outlasts the client's timeout.
        """
        # Read as text, not decoded as JSON: the body is NDJSON, and a JSON
        # decode would turn a one-line export into an object.
        return self._t.request(
            "POST", f"{_VECTOR}/{segment(collection_name, 'collection_name')}/export"
        ).text

    def import_vector_store_collection(
        self, collection_name: str, data: _ImportData
    ) -> CollectionWriteResult:
        """Load an export file into a collection (``POST .../collections/{name}/import``).

        Importing into a collection that already holds the rows adds them
        again.

        Args:
            collection_name: The collection to load into.
            data: The NDJSON text :meth:`export_vector_store_collection`
                returned, or the export file as bytes or a seekable binary file
                object. Sent as the multipart part ``file``; text is encoded to
                UTF-8.

        Returns:
            :class:`CollectionWriteResult` — what the import stored.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            perceivo_client.signing.SigningError: If request signing is on and
                the request cannot be signed. A signed multipart body is held in memory.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response, including ``411``
                without a ``Content-Length`` and ``413`` for a request over
                16 MiB.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._import(
            "import_vector_store_collection",
            f"{_VECTOR}/{segment(collection_name, 'collection_name')}/import",
            data,
        )

    def ingest_vector_store_collection(
        self,
        collection_name: str,
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
        """Chunk, embed and insert one document (``POST .../collections/{name}/ingest``).

        The API answers ``200`` even when the document is refused: read the result's ``files``
        entry, whose ``status`` is ``completed``, ``error``, ``not_attempted`` (the time budget ran
        out first; nothing was written) or ``timeout``; the last two are not counted in the totals.
        A ``timeout``, or a ``504``, may still complete: read the store back before sending it
        again. Embedding is billed.

        Waits at least 150 s for the response; raise it with ``client.with_options(timeout=...)``.

        Args:
            collection_name: The collection to ingest into.
            filename: The document's file name; its extension must be
                ``.csv``, ``.json``, ``.jsonl``, ``.md`` or ``.txt``.
            data: The document, at most 10 MiB, as bytes or a seekable binary file object.
            content_type: The document's media type. Omitted, none is sent.
            text_field: The collection's ``VARCHAR`` field to fill. Omitted,
                the collection's only one is used.
            vector_field: The vector field to fill. Omitted, the collection's
                only one is used.
            embedding_model: The embedding model. Omitted, the API picks one
                whose dimensions match the vector field.
            chunk_size: Characters per chunk; the server default is ``500``.
            chunk_overlap: Characters shared by adjacent chunks; the server default is ``50``.

        Returns:
            :class:`DocumentUploadResponse` — totals and one ``files`` entry.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            perceivo_client.signing.SigningError: If request signing is on and
                the request cannot be signed. A signed multipart body is held in memory.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown collection (``404``).
            PerceivoConflictError: While Milvus is not running (``409``).
            PerceivoAPIError: On any other error response, including ``400`` for an unsupported
                file or an undetectable field, ``413`` for a file over 10 MiB, and ``504``
                (``PerceivoServerError``) when the ingest timed out.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._ingest(
            "ingest_vector_store_collection",
            f"{_VECTOR}/{segment(collection_name, 'collection_name')}/ingest",
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
