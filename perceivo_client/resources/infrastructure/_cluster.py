"""Cluster services, the compute quota, private nodepools and the MCP server.

One of the mixins that make up
:class:`~perceivo_client.resources.infrastructure.InfrastructureResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    CapacityRead,
    ClusterServiceStatusList,
    McpConfigDocument,
    McpToolInvokeResult,
    McpToolList,
    NodepoolDetail,
    NodepoolListResponse,
)
from perceivo_client.resources.infrastructure._common import (
    _BASE,
    _CLUSTER,
    _MCP,
    _NODEPOOLS,
    _MixinBase,
)


class _ClusterMixin(_MixinBase):
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
