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
    CollectionSummary,
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
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources._multipart import file_part, refuse_if_signing

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


class InfrastructureResource(BaseResource):
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

    # -- cluster services (service: milvus | elasticsearch | redis | mcp) ---
    def list_cluster_services(self) -> ClusterServiceStatusList:
        """List every cluster service with its status (``GET /infrastructure/cluster``).

        Returns:
            :class:`ClusterServiceStatusList` — ``items`` (one
            :class:`ClusterServiceStatus` per service, carrying ``service`` and
            ``status``) and ``total``.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ClusterServiceStatusList, self._get(_CLUSTER))

    def get_cluster_service(self, service: str) -> dict[str, Any]:
        """Read one cluster service's record (``GET /infrastructure/cluster/{service}``).

        Args:
            service: ``milvus``, ``elasticsearch``, ``redis`` or ``mcp``.

        Returns:
            ``dict[str, Any]`` — the service's own record. Its keys carry the
            service's prefix (``milvus_status``, ``elasticsearch_size``,
            ``redis_mode``, ...); unlike the items of
            :meth:`list_cluster_services` it has no ``service`` or ``status``
            key.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoValidationError: For an unknown ``service`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._get(f"{_CLUSTER}/{segment(service, 'service')}")

    def update_cluster_service(self, service: str, body: dict[str, Any]) -> dict[str, Any]:
        """Change a cluster service's configuration (``PATCH /infrastructure/cluster/{service}``).

        Only the fields sent change, and nothing is restarted: a new size or
        resource setting takes effect on the next start, and resource fields
        can change only while the service is stopped. ``auto_shutdown`` and
        ``idle_timeout_minutes`` can change at any time. Raising resources
        raises what a running service is billed.

        Args:
            service: ``milvus``, ``elasticsearch``, ``redis`` or ``mcp``.
            body: A ``ClusterServiceConfiguration`` object with the generic
                field names (``size``, ``cpu_millicores``, ``memory_mb``,
                ``storage_gb``, ``auto_shutdown``, ``idle_timeout_minutes``,
                ...). The MCP server accepts only ``auto_shutdown`` and
                ``idle_timeout_minutes``.

        Returns:
            ``dict[str, Any]`` — the service's updated record, with
            service-prefixed keys as :meth:`get_cluster_service` returns.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoConflictError: For a resource field changed while the
                service is running, or a Redis ``mode`` change while Redis is
                active (``409``).
            PerceivoValidationError: For a field the service does not accept,
                or a value out of range (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._patch(f"{_CLUSTER}/{segment(service, 'service')}", json=body)

    def start_cluster_service(self, service: str) -> dict[str, Any]:
        """Start a cluster service (``POST /infrastructure/cluster/{service}/start``).

        Billing starts with the service. The call returns once the workload is
        created, which can take minutes: the API stops waiting after 120 s with
        ``502`` while the start continues, and the client's default timeout is
        30 s, so construct the client with ``timeout=150`` and, on a timeout,
        read :meth:`get_cluster_service` instead of starting again.
        Elasticsearch and Redis restore their last backup when they start.

        Args:
            service: ``milvus``, ``elasticsearch``, ``redis`` or ``mcp``.

        Returns:
            ``dict[str, Any]`` — ``{"<service>_status": "running",
            "<service>_host": ..., "<service>_port": ...}``. The host is
            reachable only from inside the organization's namespace.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoGrantError: For a key without ``INFRA_PROVISION``, or a
                suspended organization (``403``).
            PerceivoValidationError: For an unknown ``service`` (``422``).
            PerceivoExecutionLockedError: For an organization whose execution
                is locked (``429``).
            PerceivoRateLimitError: For a ``429`` that is not an execution
                lock.
            PerceivoServerError: When provisioning failed (``500``), the API
                stopped waiting (``502``, the start continues) or a backing
                service is unreachable (``503``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached, or the
                client's timeout passed while the start continues.
        """
        return self._post(f"{_CLUSTER}/{segment(service, 'service')}/start")

    def stop_cluster_service(self, service: str) -> dict[str, Any]:
        """Stop a cluster service and keep its data (``POST /infrastructure/cluster/{service}/stop``).

        Compute billing stops. Elasticsearch and Redis are backed up before
        they stop, which can take longer than the client's default 30 s
        timeout: construct the client with ``timeout=150``.

        Args:
            service: ``milvus``, ``elasticsearch``, ``redis`` or ``mcp``.

        Returns:
            ``dict[str, Any]`` — ``{"<service>_status": "stopped"}``.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoGrantError: For a key without ``INFRA_DEPROVISION``
                (``403``).
            PerceivoConflictError: While a running intelligence or
                orchestration depends on the service (``409``).
            PerceivoValidationError: For an unknown ``service`` (``422``).
            PerceivoServerError: When the backup or teardown failed (``500``),
                or the API stopped waiting (``502``, the stop continues).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._post(f"{_CLUSTER}/{segment(service, 'service')}/stop")

    # -- compute quota ------------------------------------------------------
    def get_capacity(self) -> CapacityRead:
        """Read the compute quota and what it is consuming (``GET /infrastructure/capacity``).

        Reports the default nodepool; a private nodepool's capacity is on its
        own record (:meth:`get_nodepool`). Requires ``BILLING_READ``, not an
        ``INFRA_*`` privilege.

        Returns:
            :class:`CapacityRead`.

        Raises:
            PerceivoGrantError: For a key without ``BILLING_READ``
                (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(CapacityRead, self._get(f"{_BASE}/capacity"))

    # -- nodepools ----------------------------------------------------------
    def list_nodepools(self) -> NodepoolListResponse:
        """List the organization's private nodepools (``GET .../cluster/nodepools``).

        Returns:
            :class:`NodepoolListResponse` — ``items`` and ``total``.

        Raises:
            PerceivoGrantError: For a key without ``CLUSTER_LIST``
                (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(NodepoolListResponse, self._get(_NODEPOOLS))

    def create_nodepool(self, body: dict[str, Any]) -> NodepoolDetail:
        """Create a private nodepool (``POST .../cluster/nodepools``).

        Nodes are billed per node-hour once the nodepool scales above zero.

        Args:
            body: A ``NodepoolProvision`` object.

        Returns:
            :class:`NodepoolDetail` — the nodepool as created (``201``, or
            ``202`` while it is provisioned).

        Raises:
            PerceivoGrantError: For a key without the nodepool-creation
                privilege (``403``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(NodepoolDetail, self._post(_NODEPOOLS, json=body))

    def get_nodepool(self, nodepool_name: str) -> NodepoolDetail:
        """Read one private nodepool (``GET .../cluster/nodepools/{name}``).

        Args:
            nodepool_name: The nodepool to read.

        Returns:
            :class:`NodepoolDetail` — the nodepool, its size and capacity.

        Raises:
            ValueError: If ``nodepool_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For no nodepool of that name (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            NodepoolDetail, self._get(f"{_NODEPOOLS}/{segment(nodepool_name, 'nodepool_name')}")
        )

    def update_nodepool(self, nodepool_name: str, body: dict[str, Any]) -> NodepoolDetail:
        """Change a private nodepool (``PATCH .../cluster/nodepools/{name}``).

        Args:
            nodepool_name: The nodepool to change.
            body: A ``NodepoolWrite`` object; only the fields it carries change.

        Returns:
            :class:`NodepoolDetail` — the nodepool after the change.

        Raises:
            ValueError: If ``nodepool_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For no nodepool of that name (``404``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            NodepoolDetail,
            self._patch(f"{_NODEPOOLS}/{segment(nodepool_name, 'nodepool_name')}", json=body),
        )

    def scale_nodepool(self, nodepool_name: str, body: dict[str, Any]) -> NodepoolDetail:
        """Resize a private nodepool (``POST .../cluster/nodepools/{name}/scale``).

        Scaling up adds nodes billed per node-hour. The API does not check the
        target against the nodepool's ``min_nodes`` and ``max_nodes``.

        Args:
            nodepool_name: The nodepool to resize.
            body: A ``NodepoolScale`` object, ``{"target_nodes": n}``.

        Returns:
            :class:`NodepoolDetail` — the refreshed nodepool at its new size.

        Raises:
            ValueError: If ``nodepool_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For no nodepool of that name (``404``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            NodepoolDetail,
            self._post(f"{_NODEPOOLS}/{segment(nodepool_name, 'nodepool_name')}/scale", json=body),
        )

    def delete_nodepool(self, nodepool_name: str) -> None:
        """Delete a private nodepool (``DELETE .../cluster/nodepools/{name}``).

        Irreversible. A nodepool that was never provisioned is removed at once;
        otherwise it is marked ``deleting`` and disappears from the list when
        the nodes are gone. A nodepool with workloads still on it is refused.

        Args:
            nodepool_name: The nodepool to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``nodepool_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``CLUSTER_LIST`` and
                ``CLUSTER_DELETE`` (``403``).
            PerceivoNotFoundError: For no nodepool of that name (``404``).
            PerceivoConflictError: While workloads or pods still run on the
                nodepool (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_NODEPOOLS}/{segment(nodepool_name, 'nodepool_name')}")

    # -- MCP server ---------------------------------------------------------
    def get_mcp_config(self) -> McpConfigDocument:
        """Read the MCP server's configuration (``GET .../cluster/mcp/config``).

        Readable whether or not the server is running.

        Returns:
            :class:`McpConfigDocument` — ``auto_shutdown`` and
            ``idle_timeout_minutes``.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(McpConfigDocument, self._get(f"{_MCP}/config"))

    def replace_mcp_config(self, body: dict[str, Any]) -> McpConfigDocument:
        """Replace the MCP server's configuration (``PUT .../cluster/mcp/config``).

        A replace, not a merge: send both fields. They can change while the
        server runs.

        Args:
            body: A ``McpConfigReplace`` object: ``auto_shutdown`` and
                ``idle_timeout_minutes``, both required.

        Returns:
            :class:`McpConfigDocument` — the configuration as stored.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoValidationError: For a missing or out-of-range field
                (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(McpConfigDocument, self._put(f"{_MCP}/config", json=body))

    def list_mcp_tools(self) -> McpToolList:
        """List the running MCP server's tools (``GET .../cluster/mcp/tools``).

        Returns:
            :class:`McpToolList` — ``tools`` (each with ``name``,
            ``description`` and ``input_schema``) and ``count``. A server still
            initialising lists none.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoConflictError: While the MCP server is not running
                (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(McpToolList, self._get(f"{_MCP}/tools"))

    def invoke_mcp_tool(
        self, tool_name: str, body: dict[str, Any] | None = None
    ) -> McpToolInvokeResult:
        """Run one of the MCP server's tools (``POST .../cluster/mcp/tools/{tool}/invoke``).

        Synchronous: the call waits for the tool, up to 120 s. Tool execution
        is billed, and its side effects are the tool's own.

        Args:
            tool_name: The tool's ``name`` from :meth:`list_mcp_tools`.
            body: An optional ``McpToolInvokeRequest`` object,
                ``{"arguments": {...}}``. Omitted, an empty object is sent.

        Returns:
            :class:`McpToolInvokeResult` — ``tool_name``, ``content`` and
            ``is_error``.

        Raises:
            ValueError: If ``tool_name`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoGrantError: For a key without ``COMPONENT_EXECUTE``
                (``403``).
            PerceivoNotFoundError: For a tool the server does not expose, or
                arguments it rejects (``404``).
            PerceivoConflictError: While the MCP server is not running
                (``409``).
            PerceivoExecutionLockedError: For an organization whose execution
                is locked (``429``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            McpToolInvokeResult,
            self._post(f"{_MCP}/tools/{segment(tool_name, 'tool_name')}/invoke", json=body or {}),
        )

    # -- managed services (service: postgres | redis) -----------------------
    def list_managed_services(self) -> ManagedServiceListResponse:
        """List the organization's managed service instances (``GET /infrastructure/managed``).

        Each item is a projection that withholds connection details and the
        instance id.

        Returns:
            :class:`ManagedServiceListResponse` — ``items`` (one
            :class:`ManagedServiceRead` per instance) and ``total``.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_LIST`` (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ManagedServiceListResponse, self._get(f"{_BASE}/managed"))

    def get_managed_service(self, service: str) -> ManagedServiceRead:
        """Read one managed service instance (``GET /infrastructure/managed/{service}``).

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`ManagedServiceRead` — a projection without connection
            details.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead, self._get(f"{_BASE}/managed/{segment(service, 'service')}")
        )

    def update_managed_service(self, service: str, body: dict[str, Any]) -> ManagedServiceRead:
        """Change a managed service's name, size or shutdown policy (``PATCH .../managed/{service}``).

        Only the fields sent change. A larger ``sku`` is a larger billed
        instance. ``configuration`` is returned verbatim on every read, so do
        not put a credential in it: keep credentials in ``client.secrets``.

        Args:
            service: ``postgres`` or ``redis``.
            body: A ``ManagedServiceUpdate`` object.

        Returns:
            :class:`ManagedServiceRead` — the instance after the change.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a malformed body, or a ``service``
                other than ``postgres`` or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead,
            self._patch(f"{_BASE}/managed/{segment(service, 'service')}", json=body),
        )

    def start_managed_service(self, service: str) -> ManagedServiceRead:
        """Start a stopped managed service (``POST .../managed/{service}/start``).

        Asynchronous, and it resumes billing. The answer acknowledges the
        request even when the start is later refused, so poll
        :meth:`get_managed_service` until ``status`` is ``running``.

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`ManagedServiceRead` — the instance as the request left it.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead, self._post(f"{_BASE}/managed/{segment(service, 'service')}/start")
        )

    def stop_managed_service(self, service: str) -> ManagedServiceRead:
        """Stop a running managed service (``POST .../managed/{service}/stop``).

        Asynchronous: the answer acknowledges the request, so poll
        :meth:`get_managed_service` for ``stopped``.

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`ManagedServiceRead` — the instance as the request left it.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead, self._post(f"{_BASE}/managed/{segment(service, 'service')}/stop")
        )

    def list_managed_service_backups(self, service: str) -> BackupListResponse:
        """List a managed service's backups, most recent first (``GET .../managed/{service}/backups``).

        At most the 50 most recent backups are listed.

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`BackupListResponse` — ``items`` (one :class:`BackupRead`
            per backup) and ``total``.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BackupListResponse, self._get(f"{_BASE}/managed/{segment(service, 'service')}/backups")
        )

    def get_managed_service_backup(self, service: str, backup_id: str) -> BackupRead:
        """Read one backup of a managed service (``GET .../managed/{service}/backups/{id}``).

        Only the 50 most recent backups can be read.

        Args:
            service: ``postgres`` or ``redis``.
            backup_id: The backup to read.

        Returns:
            :class:`BackupRead` — the backup and its status.

        Raises:
            ValueError: If ``service`` or ``backup_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoNotFoundError: For a backup that is not among the 50 most
                recent (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BackupRead,
            self._get(
                f"{_BASE}/managed/{segment(service, 'service')}/backups/{segment(backup_id, 'backup_id')}"
            ),
        )

    def create_managed_service_backup(
        self, service: str, body: dict[str, Any] | None = None
    ) -> BackupRead:
        """Record a backup request for a managed service (``POST .../managed/{service}/backups``).

        The API writes a backup record that reports ``in_progress`` and
        answers ``202``. No component of the platform performs the backup, so
        the record is not a backup you can restore from.

        Args:
            service: ``postgres`` or ``redis``.
            body: An optional ``BackupCreate`` object (``backup_type``).
                Omitted, no body is sent and the API's default applies.

        Returns:
            :class:`BackupRead` — the backup record just written.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoValidationError: For a malformed body, or a ``service``
                other than ``postgres`` or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BackupRead,
            self._post(f"{_BASE}/managed/{segment(service, 'service')}/backups", json=body),
        )

    # -- dedicated databases ------------------------------------------------
    def get_database(self, database_id: str) -> DedicatedDatabaseRead:
        """Read one dedicated database (``GET /infrastructure/databases/{database_id}``).

        A projection: host, port, admin user name and default database name
        are withheld.

        Args:
            database_id: The dedicated database to read.

        Returns:
            :class:`DedicatedDatabaseRead` — including its lifecycle
            ``status``.

        Raises:
            ValueError: If ``database_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For a database that does not exist or
                belongs to another organization (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DedicatedDatabaseRead,
            self._get(f"{_BASE}/databases/{segment(database_id, 'database_id')}"),
        )

    def start_database(self, database_id: str) -> DedicatedDatabaseStartAccepted:
        """Start a stopped dedicated database (``POST .../databases/{database_id}/start``).

        Asynchronous (``202``), and it resumes compute billing subject to your
        usage limits: poll :meth:`get_database` until ``status`` is
        ``running``.

        Args:
            database_id: The dedicated database to start.

        Returns:
            :class:`DedicatedDatabaseStartAccepted` — the acknowledgement.

        Raises:
            ValueError: If ``database_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For a database that does not exist or
                belongs to another organization (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DedicatedDatabaseStartAccepted,
            self._post(f"{_BASE}/databases/{segment(database_id, 'database_id')}/start"),
        )

    def record_database_activity(self, database_id: str) -> None:
        """Reset a dedicated database's idle-shutdown timer (``POST .../databases/{database_id}/activity``).

        Args:
            database_id: The dedicated database to mark as active.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``database_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For a database that does not exist or
                belongs to another organization (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._post(f"{_BASE}/databases/{segment(database_id, 'database_id')}/activity")

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

    def create_search_index(self, body: dict[str, Any]) -> CollectionSummary:
        """Create a search index (``POST /infrastructure/search-index/indices``).

        Args:
            body: A ``CollectionCreate`` object in the platform's own create
                shape, not Elasticsearch's create-index API: ``name`` (1 to
                255 characters, required), ``mappings`` (an Elasticsearch
                mappings object) and ``settings`` (an Elasticsearch index
                settings object). Any other key is dropped without an error,
                and the index is still created (``201``).

        Returns:
            :class:`CollectionSummary` — the index just created (``201``).

        Raises:
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoConflictError: For an index that already exists, or while
                Elasticsearch is not running (``409``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(CollectionSummary, self._post(_SEARCH, json=body))

    def delete_search_index(self, index_name: str) -> CollectionSummary:
        """Delete a search index and everything in it (``DELETE .../indices/{name}``).

        Irreversible: :meth:`export_search_index` it first if its contents
        matter.

        Args:
            index_name: The index to delete.

        Returns:
            :class:`CollectionSummary` — the index as it was deleted.

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
            CollectionSummary, self._delete(f"{_SEARCH}/{segment(index_name, 'index_name')}")
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
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown index (``404``).
            PerceivoConflictError: While Elasticsearch is not running (``409``).
            PerceivoAPIError: On any other error response, including ``400``
                for a document the store refuses and ``503`` when the store
                cannot be reached.
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
            perceivo_client.signing.SigningError: If request signing is
                enabled: a multipart body cannot be signed.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown index (``404``).
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
            perceivo_client.signing.SigningError: If request signing is
                enabled: a multipart body cannot be signed.
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

    def create_vector_store_collection(self, body: dict[str, Any]) -> CollectionSummary:
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
            :class:`CollectionSummary` — the collection just created (``201``).

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
        return self._model(CollectionSummary, self._post(_VECTOR, json=body))

    def delete_vector_store_collection(self, collection_name: str) -> CollectionSummary:
        """Delete a vector-store collection and everything in it (``DELETE .../collections/{name}``).

        Irreversible: :meth:`export_vector_store_collection` it first if its
        contents matter.

        Args:
            collection_name: The collection to delete.

        Returns:
            :class:`CollectionSummary` — the collection as it was deleted.

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
            CollectionSummary,
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
                for entities the store refuses and ``503`` when the store
                cannot be reached.
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
            perceivo_client.signing.SigningError: If request signing is
                enabled: a multipart body cannot be signed.
            PerceivoGrantError: For a key without ``INFRA_CONFIGURE``
                (``403``).
            PerceivoNotFoundError: For an unknown collection (``404``).
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
            perceivo_client.signing.SigningError: If request signing is
                enabled: a multipart body cannot be signed.
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

    # -- cache (Redis) ------------------------------------------------------
    def list_cache_keys(self) -> RedisKeyScanResult:
        """List keys in the organization's cache (``GET /infrastructure/cache/keys``).

        Every call returns the first batch of the scan: the API offers no
        pattern, cursor or count, so the key space cannot be paged.

        Returns:
            :class:`RedisKeyScanResult`.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_READ`` (``403``).
            PerceivoConflictError: While Redis is not running (``409``).
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
            ValueError: If ``key`` is empty, ``.`` or ``..`` (refused before the
                request is sent).
            PerceivoNotFoundError: For an absent key (``404``).
            PerceivoConflictError: While Redis is not running (``409``).
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
            perceivo_client.signing.SigningError: If request signing is
                enabled: a multipart body cannot be signed.
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
        refuse_if_signing(self._t, f"infrastructure.{method_name}")
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
        refuse_if_signing(self._t, f"infrastructure.{method_name}")
        parts = {"file": (_IMPORT_FILENAME, _import_file(data), _IMPORT_CONTENT_TYPE)}
        return self._model(CollectionWriteResult, self._post(path, files=parts))
