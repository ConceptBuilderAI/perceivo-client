"""Ingest jobs on the vector store and the search index (part of ``client.infrastructure``).

An ingest job reads files you have already uploaded to a storage space (see
``client.files``), chunks and embeds them, and writes the chunks to one
collection or index, in the background. Name the source as entry ids (at most
100 files) or as a space with an optional folder. Every operation needs
``INFRA_CONFIGURE``, reads included, held by the key and granted by the
organization.

A job's ``version`` is its ``ETag``. :meth:`InfrastructureResource.resume_vector_store_ingest_job`
and its search-index twin need the version of the job as you last read it, and
start a new job over the files that did not succeed; files that succeeded are
not read again.

``Idempotency-Key`` (at most 237 characters) makes a create or a resume safe to
retry: the same key returns the job the first request made, and the same key
with a different body, store or target is refused with ``409``.

These methods are mixed into :class:`~perceivo_client.resources.infrastructure.InfrastructureResource`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import IngestJob, IngestJobFilePage, IngestJobPage

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object

_BASE = "/v1/infrastructure"
_STORES = {
    "vector_store": (f"{_BASE}/vector-store/collections", "collection_name"),
    "search_index": (f"{_BASE}/search-index/indices", "index_name"),
}


def _key_header(idempotency_key: str | None) -> dict[str, str]:
    return {} if idempotency_key is None else {"Idempotency-Key": idempotency_key}


class _IngestJobsMixin(_MixinBase):
    """The twelve ingest-job operations: six on each container store."""

    # --- vector store ---
    def create_vector_store_ingest_job(
        self, collection_name: str, body: dict[str, Any], *, idempotency_key: str | None = None
    ) -> IngestJob:
        """Start an ingest job into a vector-store collection
        (``POST /infrastructure/vector-store/collections/{name}/ingest-jobs``, ``202``).

        ``body`` is an ``IngestJobCreate``: ``source`` is ``{"entry_ids": [...]}``
        (1 to 100 file entries) or ``{"space_id": ..., "folder_id": ...,
        "recursive": true}``; ``embedding_model``, ``text_field`` and
        ``vector_field`` are required; ``chunk_size`` (50-8000, default 500),
        ``chunk_overlap`` (0-2000, default 50) and ``text_column`` are optional.
        Every entry, space and folder must be the organization's own.

        Args:
            collection_name: The collection to write to.
            body: An ``IngestJobCreate`` object, sent as the JSON body.
            idempotency_key: Optional, at most 237 characters; a retry with the
                same key returns the same job.

        Returns:
            :class:`IngestJob`, queued.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoNotFoundError: For an unknown collection, or an entry, space
                or folder that is not the organization's (``404``).
            PerceivoAPIError: ``409`` for a reused key with a different request,
                ``422`` (``PerceivoValidationError``) for a malformed body or key,
                ``429`` when too many jobs are queued, ``502`` when the store
                cannot be reached.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._create("vector_store", collection_name, body, idempotency_key)

    def list_vector_store_ingest_jobs(
        self, collection_name: str, *, limit: int | None = None, before: str | None = None
    ) -> IngestJobPage:
        """A page of a collection's ingest jobs, most recent first
        (``GET .../collections/{name}/ingest-jobs``).

        Args:
            collection_name: The collection.
            limit: Jobs per page, 1 to 100 (the API's default is 50).
            before: The previous page's ``next``; omit for the first page.

        Returns:
            :class:`IngestJobPage`: ``items`` and ``next`` (absent on the last page).
            A collection that does not exist answers an empty page.

        Raises:
            ValueError: If ``collection_name`` is empty, ``.`` or ``..``.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoAPIError: On another error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list_jobs("vector_store", collection_name, limit, before)

    def get_vector_store_ingest_job(self, collection_name: str, job_id: str) -> IngestJob:
        """One ingest job (``GET .../collections/{name}/ingest-jobs/{job_id}``).

        Returns:
            :class:`IngestJob`, whose ``version`` is what a resume needs.

        Raises:
            ValueError: If ``collection_name`` or ``job_id`` is empty, ``.`` or ``..``.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoNotFoundError: For an unknown job or collection (``404``).
            PerceivoAPIError: ``410`` for a job past its retention.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._job_call("vector_store", collection_name, job_id, "GET")

    def list_vector_store_ingest_job_files(
        self,
        collection_name: str,
        job_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
    ) -> IngestJobFilePage:
        """A page of an ingest job's files, each with its status and, when it did
        not succeed, a ``reason_code`` (``GET .../ingest-jobs/{job_id}/files``).

        Args:
            collection_name: The collection.
            job_id: The job.
            limit: Files per page, 1 to 500 (the API's default is 100).
            after: The previous page's ``next``; omit for the first page.

        Returns:
            :class:`IngestJobFilePage`.

        Raises:
            ValueError: If ``collection_name`` or ``job_id`` is empty, ``.`` or ``..``.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoNotFoundError: For an unknown job or collection (``404``).
            PerceivoAPIError: ``410`` for a job past its retention.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._files("vector_store", collection_name, job_id, limit, after)

    def cancel_vector_store_ingest_job(self, collection_name: str, job_id: str) -> IngestJob:
        """Cancel an ingest job (``POST .../ingest-jobs/{job_id}/cancel``, ``202``).

        A queued job is cancelled at once; a running one stops after its current
        batch. Nothing already written is removed.

        Raises:
            ValueError: If ``collection_name`` or ``job_id`` is empty, ``.`` or ``..``.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoNotFoundError: For an unknown job or collection (``404``).
            PerceivoAPIError: ``409`` for a job that has already ended, ``410``
                for one past its retention.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._job_call("vector_store", collection_name, job_id, "POST", "/cancel")

    def resume_vector_store_ingest_job(
        self,
        collection_name: str,
        job_id: str,
        *,
        version: int,
        idempotency_key: str | None = None,
    ) -> IngestJob:
        """Start a new job over the files of a failed, cancelled or partly failed
        job that did not succeed (``POST .../ingest-jobs/{job_id}/resume``, ``202``).

        Args:
            collection_name: The collection.
            job_id: The job to resume.
            version: The job's ``version`` as last read; sent as ``If-Match``.
            idempotency_key: Optional, at most 237 characters.

        Returns:
            :class:`IngestJob`: the new job, with ``resumed_from`` set.

        Raises:
            ValueError: If ``collection_name`` or ``job_id`` is empty, ``.`` or
                ``..``, or ``version`` is not a non-negative integer.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE`` (``403``).
            PerceivoNotFoundError: For an unknown job or collection (``404``).
            PerceivoAPIError: ``412`` when ``version`` is stale, ``409`` for a job
                in another state, ``410`` for one past its retention.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._resume("vector_store", collection_name, job_id, version, idempotency_key)

    # --- search index ---
    def create_search_index_ingest_job(
        self, index_name: str, body: dict[str, Any], *, idempotency_key: str | None = None
    ) -> IngestJob:
        """Start an ingest job into a search index
        (``POST /infrastructure/search-index/indices/{name}/ingest-jobs``, ``202``).
        As :meth:`create_vector_store_ingest_job`, for an index."""
        return self._create("search_index", index_name, body, idempotency_key)

    def list_search_index_ingest_jobs(
        self, index_name: str, *, limit: int | None = None, before: str | None = None
    ) -> IngestJobPage:
        """A page of an index's ingest jobs (``GET .../indices/{name}/ingest-jobs``).
        As :meth:`list_vector_store_ingest_jobs`, for an index."""
        return self._list_jobs("search_index", index_name, limit, before)

    def get_search_index_ingest_job(self, index_name: str, job_id: str) -> IngestJob:
        """One ingest job (``GET .../indices/{name}/ingest-jobs/{job_id}``).
        As :meth:`get_vector_store_ingest_job`, for an index."""
        return self._job_call("search_index", index_name, job_id, "GET")

    def list_search_index_ingest_job_files(
        self, index_name: str, job_id: str, *, limit: int | None = None, after: str | None = None
    ) -> IngestJobFilePage:
        """A page of an ingest job's files (``GET .../indices/{name}/ingest-jobs/{job_id}/files``).
        As :meth:`list_vector_store_ingest_job_files`, for an index."""
        return self._files("search_index", index_name, job_id, limit, after)

    def cancel_search_index_ingest_job(self, index_name: str, job_id: str) -> IngestJob:
        """Cancel an ingest job (``POST .../indices/{name}/ingest-jobs/{job_id}/cancel``).
        As :meth:`cancel_vector_store_ingest_job`, for an index."""
        return self._job_call("search_index", index_name, job_id, "POST", "/cancel")

    def resume_search_index_ingest_job(
        self, index_name: str, job_id: str, *, version: int, idempotency_key: str | None = None
    ) -> IngestJob:
        """Resume an ingest job (``POST .../indices/{name}/ingest-jobs/{job_id}/resume``).
        As :meth:`resume_vector_store_ingest_job`, for an index."""
        return self._resume("search_index", index_name, job_id, version, idempotency_key)

    # --- shared ---
    @staticmethod
    def _jobs(store: str, name: str) -> str:
        root, field = _STORES[store]
        return f"{root}/{segment(name, field)}/ingest-jobs"

    def _create(self, store: str, name: str, body: dict[str, Any], key: str | None) -> IngestJob:
        path = self._jobs(store, name)
        return self._model(IngestJob, self._post(path, json=body, headers=_key_header(key)))

    def _list_jobs(
        self, store: str, name: str, limit: int | None, before: str | None
    ) -> IngestJobPage:
        params = {"limit": limit, "before": before}
        return self._model(IngestJobPage, self._get(self._jobs(store, name), params=params))

    def _files(
        self, store: str, name: str, job_id: str, limit: int | None, after: str | None
    ) -> IngestJobFilePage:
        path = f"{self._jobs(store, name)}/{segment(job_id, 'job_id')}/files"
        return self._model(
            IngestJobFilePage, self._get(path, params={"limit": limit, "after": after})
        )

    def _job_call(
        self, store: str, name: str, job_id: str, method: str, suffix: str = ""
    ) -> IngestJob:
        path = f"{self._jobs(store, name)}/{segment(job_id, 'job_id')}{suffix}"
        return self._model(IngestJob, self._request(method, path))

    def _resume(
        self, store: str, name: str, job_id: str, version: int, key: str | None
    ) -> IngestJob:
        if isinstance(version, bool) or not isinstance(version, int) or version < 0:
            raise ValueError("version must be the job's version, a non-negative integer")
        path = f"{self._jobs(store, name)}/{segment(job_id, 'job_id')}/resume"
        headers = {"If-Match": f'"{version}"', **_key_header(key)}
        return self._model(IngestJob, self._post(path, headers=headers))
