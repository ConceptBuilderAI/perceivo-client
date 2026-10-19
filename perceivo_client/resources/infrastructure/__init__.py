"""Infrastructure namespace (``client.infrastructure``).

The organization's data plane: the cluster services (Milvus, Elasticsearch,
Redis and the MCP server) and their lifecycle and configuration; the vector
store, the search index and the cache that run on them; the MCP server's tools;
private nodepools and the compute quota; the managed (Azure-hosted) services
and their backups; and dedicated databases. File storage is in
``client.files`` and secrets are in ``client.secrets``.

A running cluster service is billed until it stops. With ``auto_shutdown`` on
(the default) the platform stops a store once it has been idle for
``idle_timeout_minutes`` (default 30), and the vector-store, search-index and
cache operations here do not count as activity: a store used only through this
API stops about 30 minutes after it started. Raise ``idle_timeout_minutes``
with :meth:`InfrastructureResource.update_cluster_service`, and stop the store
yourself when you are done.

Every vector-store and search-index method can also raise ``PerceivoServerError`` (``502``,
``503``) when the platform cannot reach the store or the store answers with an error; a search-index
method also passes on any other Elasticsearch error status unchanged.

No method here returns a credential: managed services and dedicated databases
are published as projections that withhold connection details.
"""

from __future__ import annotations

from typing import IO, Any

from perceivo_client._paths import segment
from perceivo_client._transport import _LONG_TIMEOUT
from perceivo_client.generated.models import (
    BackupListResponse,
    BackupRead,
    CapacityRead,
    ClusterServiceStatusList,
    CollectionDataPage,
    CollectionDetail,
    CollectionList,
    CollectionQueryResult,
    CollectionWriteResult,
    DedicatedDatabaseRead,
    DedicatedDatabaseStartAccepted,
    DocumentUploadResponse,
    ManagedServiceListResponse,
    ManagedServiceRead,
    McpConfigDocument,
    McpToolInvokeResult,
    McpToolList,
    NodepoolDetail,
    NodepoolListResponse,
    OrganizationInfrastructureRead,
    RedisKeyDetail,
    RedisKeyScanResult,
    SearchIndexCreated,
    SearchIndexDeleted,
    VectorStoreCollectionCreated,
    VectorStoreCollectionDeleted,
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources._multipart import file_part
from perceivo_client.resources.infrastructure._cache import _CacheMixin
from perceivo_client.resources.infrastructure._cluster import _ClusterMixin
from perceivo_client.resources.infrastructure._common import (
    _BASE,
    _CLUSTER,
    _IMPORT_CONTENT_TYPE,
    _IMPORT_FILENAME,
    _MCP,
    _NODEPOOLS,
    _SEARCH,
    _VECTOR,
    _import_file,
    _ImportData,
    _MixinBase,
    _MultipartMixin,
)
from perceivo_client.resources.infrastructure._ingest_jobs import _IngestJobsMixin
from perceivo_client.resources.infrastructure._managed import _ManagedMixin
from perceivo_client.resources.infrastructure._search_index import _SearchIndexMixin
from perceivo_client.resources.infrastructure._vector_store import _VectorStoreMixin


class InfrastructureResource(
    _ClusterMixin,
    _ManagedMixin,
    _SearchIndexMixin,
    _VectorStoreMixin,
    _CacheMixin,
    _IngestJobsMixin,
    BaseResource,
):
    """Cluster services, data stores, nodepools, managed services and databases."""

    def get(self) -> OrganizationInfrastructureRead:
        """Read the organization's infrastructure record (``GET /infrastructure``).

        One record for the caller's organization: the status, size, idle
        settings and in-cluster address of each cluster service, and the
        storage roll-up. The first read creates the record when the
        organization has none.

        Returns:
            :class:`OrganizationInfrastructureRead`.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(OrganizationInfrastructureRead, self._get(_BASE))
