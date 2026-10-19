"""The cache (Redis): key scan, key read and ingest.

One of the mixins that make up
:class:`~perceivo_client.resources.infrastructure.InfrastructureResource`.
"""

from __future__ import annotations

from typing import IO

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    DocumentUploadResponse,
    RedisKeyDetail,
    RedisKeyScanResult,
)
from perceivo_client.resources.infrastructure._common import (
    _BASE,
    _MultipartMixin,
)


class _CacheMixin(_MultipartMixin):
    # -- cache (Redis) ------------------------------------------------------
    def list_cache_keys(self) -> RedisKeyScanResult:
        """List keys in the organization's cache (``GET /infrastructure/cache/keys``).

        Returns:
            :class:`RedisKeyScanResult`, the first batch of the scan on every call: the API
                offers no pattern, cursor or count, so the key space cannot be paged.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoNotFoundError: If the organization's Redis has no connection details (``404``).
            PerceivoConflictError: While Redis is not running (``409``).
            PerceivoServerError: Redis unreachable or unresponsive (``502``-``504``), after retries.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RedisKeyScanResult, self._get(f"{_BASE}/cache/keys"))

    def get_cache_key(self, key: str) -> RedisKeyDetail:
        """Read one cache key (``GET /infrastructure/cache/keys/{key}``).

        Args:
            key: The key, encoded as one path segment.

        Returns:
            :class:`RedisKeyDetail`.

        Raises:
            ValueError: If ``key`` is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoNotFoundError: For an absent key (``404``).
            PerceivoConflictError: While Redis is not running (``409``).
            PerceivoServerError: Redis unreachable or unresponsive (``502``-``504``), after retries.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RedisKeyDetail, self._get(f"{_BASE}/cache/keys/{segment(key, 'key')}"))

    def ingest_cache(
        self,
        key_prefix: str,
        filename: str,
        data: bytes | IO[bytes],
        *,
        content_type: str | None = None,
        ttl: int | None = None,
        embedding_model: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> DocumentUploadResponse:
        """Chunk, embed and store one document under a key prefix (``POST /infrastructure/cache/ingest``).

        The API answers ``200`` even when the document is refused, including while Redis is
        stopped: read the result's ``files`` entry, whose ``status`` is ``completed``, ``error``,
        ``not_attempted`` (the time budget ran out first; nothing was written) or ``timeout``; the
        last two are not counted in the totals. A ``timeout``, or a ``504``, may still complete:
        read the store back before sending it again. Embedding is billed.

        Waits at least 150 s for the response; raise it with ``client.with_options(timeout=...)``.

        Args:
            key_prefix: The prefix of the keys the chunks are stored under.
            filename: The document's file name; its extension must be
                ``.csv``, ``.json``, ``.jsonl``, ``.md`` or ``.txt``.
            data: The document, at most 10 MiB, as bytes or a seekable binary file object.
            content_type: The document's media type. Omitted, none is sent.
            ttl: Expiry of the stored keys, in seconds. Omitted, keys do not expire.
            embedding_model: The embedding model. Omitted, the API picks one.
            chunk_size: Characters per chunk; the server default is ``500``.
            chunk_overlap: Characters shared by adjacent chunks; the server default is ``50``.

        Returns:
            :class:`DocumentUploadResponse` — totals and one ``files`` entry.

        Raises:
            perceivo_client.signing.SigningError: If request signing is on and
                the request cannot be signed. A signed multipart body is held in memory.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoAPIError: On any other error response, including ``400`` for an unsupported
                file, ``413`` for a file over 10 MiB, and ``504`` (``PerceivoServerError``) when
                the ingest timed out.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._ingest(
            "ingest_cache",
            f"{_BASE}/cache/ingest",
            filename,
            data,
            content_type,
            {
                "key_prefix": key_prefix,
                "ttl": ttl,
                "embedding_model": embedding_model,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
        )
