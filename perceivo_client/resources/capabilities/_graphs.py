"""Execution graphs and graph configurations.

One of the mixins that make up
:class:`~perceivo_client.resources.capabilities.CapabilitiesResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    ExecutionGraphBuildResponse,
    ExecutionGraphConfigRead,
    GraphConfigBuildResponse,
    PaginatedItemsResponse,
)
from perceivo_client.resources.capabilities._common import _BASE, _MixinBase


class _GraphsMixin(_MixinBase):
    # -- execution graphs --------------------------------------------------------
    def list_execution_graphs(self, capability_id: str) -> PaginatedItemsResponse:
        """The capability's stored execution graphs (``GET .../execution-graphs``).

        Calls ``GET /capabilities/{capability_id}/execution-graphs``. Newest
        first, every graph in one response. Each item carries ``graph_id``,
        ``capability_id``, ``blob_path``, ``entry_count``,
        ``orchestration_summary`` and ``created_at``.

        Args:
            capability_id: The capability whose graphs to list.

        Returns:
            :class:`PaginatedItemsResponse`: ``items`` and ``total``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ORCHESTRATION_READ``, ``404``
                (``PerceivoNotFoundError``) for a capability of another
                organization, and ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PaginatedItemsResponse,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs"),
        )

    def get_execution_graph(self, capability_id: str, graph_id: str) -> dict[str, Any]:
        """One stored execution graph (``GET .../execution-graphs/{graph_id}``).

        Calls ``GET /capabilities/{capability_id}/execution-graphs/{graph_id}``.
        The answer is the graph document as it was built, with its
        ``graph_id``, ``created_at``, ``entries`` and summary data; a large
        graph is a large response.

        Args:
            capability_id: The capability the graph belongs to.
            graph_id: The graph to read, as ``graph_id`` in a listing.

        Returns:
            ``dict[str, Any]``: the graph document, unvalidated.

        Raises:
            ValueError: If ``capability_id`` or ``graph_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ORCHESTRATION_READ``, ``404``
                (``PerceivoNotFoundError``) for a graph that does not exist,
                and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._get(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/{segment(graph_id, 'graph_id')}"
        )

    def delete_execution_graph(self, capability_id: str, graph_id: str) -> None:
        """Permanently delete a stored graph (``DELETE .../execution-graphs/{graph_id}``).

        Calls ``DELETE /capabilities/{capability_id}/execution-graphs/{graph_id}``.
        There is no restore.

        Args:
            capability_id: The capability the graph belongs to.
            graph_id: The graph to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``graph_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_DELETE``, ``404``
                (``PerceivoNotFoundError``) for a graph that does not exist
                (also on a repeat), and ``422`` (``PerceivoValidationError``)
                for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/{segment(graph_id, 'graph_id')}"
        )

    def build_execution_graph(
        self, capability_id: str, body: dict[str, Any]
    ) -> ExecutionGraphBuildResponse:
        """Build and store a new execution graph (``POST .../execution-graphs/build``).

        Calls ``POST /capabilities/{capability_id}/execution-graphs/build``.
        Aggregates the capability's runs into a graph; no compute is started,
        and the call can take up to 120 seconds. Each call stores a new graph.

        Args:
            capability_id: The capability to build a graph for.
            body: A ``BuildExecutionGraphRequest`` object. The API reads the
                capability from the body, so it must carry ``capability_id``
                (the same as the path) and ``organization_id`` (the key's
                organization) as well as the build options.

        Returns:
            :class:`ExecutionGraphBuildResponse`: ``graph_id``,
            ``entry_count`` and the summary of the new graph.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when the body names
                no capability, ``403`` (``PerceivoGrantError``) without
                ``ORCHESTRATION_READ``, ``404`` (``PerceivoNotFoundError``) when no runs
                match, and ``422`` (``PerceivoValidationError``) for a malformed
                body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExecutionGraphBuildResponse,
            self._post(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/build",
                json=body,
            ),
        )

    def list_graph_configs(self, capability_id: str) -> PaginatedItemsResponse:
        """The capability's saved graph configurations (``GET .../execution-graphs/configs``).

        Calls ``GET /capabilities/{capability_id}/execution-graphs/configs``.
        Newest first, every configuration in one response. Each item has the
        fields of :class:`ExecutionGraphConfigRead`.

        Args:
            capability_id: The capability whose configurations to list.

        Returns:
            :class:`PaginatedItemsResponse`: ``items`` and ``total``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ORCHESTRATION_READ``, ``404``
                (``PerceivoNotFoundError``) for a capability of another
                organization, and ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PaginatedItemsResponse,
            self._get(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/configs"
            ),
        )

    def create_graph_config(
        self, capability_id: str, body: dict[str, Any]
    ) -> ExecutionGraphConfigRead:
        """Save a graph-build configuration (``POST .../execution-graphs/configs``).

        Calls ``POST /capabilities/{capability_id}/execution-graphs/configs``.
        A configuration can also schedule builds with ``cron_expression``.

        Args:
            capability_id: The capability the configuration builds graphs for.
            body: A ``CreateGraphConfigRequest`` object with ``name``.

        Returns:
            :class:`ExecutionGraphConfigRead`: the configuration as stored.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_CREATE``, ``404`` (``PerceivoNotFoundError``) for a
                target intelligence the caller cannot reach, and ``422``
                (``PerceivoValidationError``) for a malformed body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExecutionGraphConfigRead,
            self._post(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/configs",
                json=body,
            ),
        )

    def update_graph_config(
        self, capability_id: str, config_id: str, body: dict[str, Any]
    ) -> ExecutionGraphConfigRead:
        """Change a saved configuration (``PUT .../execution-graphs/configs/{config_id}``).

        Calls ``PUT /capabilities/{capability_id}/execution-graphs/configs/{config_id}``.
        Only the fields sent change; the others are kept.

        Args:
            capability_id: The capability the configuration belongs to.
            config_id: The configuration to change.
            body: An ``UpdateGraphConfigRequest`` object.

        Returns:
            :class:`ExecutionGraphConfigRead`: the configuration after the
            change.

        Raises:
            ValueError: If ``capability_id`` or ``config_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_UPDATE``, ``404``
                (``PerceivoNotFoundError``) for a configuration the caller
                cannot reach, and ``422`` (``PerceivoValidationError``) for a
                malformed body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExecutionGraphConfigRead,
            self._put(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/configs/{segment(config_id, 'config_id')}",
                json=body,
            ),
        )

    def delete_graph_config(self, capability_id: str, config_id: str) -> None:
        """Permanently delete a saved configuration (``DELETE .../configs/{config_id}``).

        Calls ``DELETE /capabilities/{capability_id}/execution-graphs/configs/{config_id}``.
        Graphs the configuration built are kept.

        Args:
            capability_id: The capability the configuration belongs to.
            config_id: The configuration to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``config_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_DELETE``, ``404``
                (``PerceivoNotFoundError``) for a configuration that does not
                exist (also on a repeat), and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/configs/{segment(config_id, 'config_id')}"
        )

    def build_from_config(
        self, capability_id: str, config_id: str, body: dict[str, Any] | None = None
    ) -> GraphConfigBuildResponse:
        """Build a graph now from a saved configuration (``POST .../configs/{config_id}/build``).

        Calls ``POST /capabilities/{capability_id}/execution-graphs/configs/{config_id}/build``.
        Stores a new graph, records it as the configuration's last build and
        deletes graphs beyond the configuration's ``retain_last_n``. The call
        can take up to 120 seconds.

        Args:
            capability_id: The capability the configuration belongs to.
            config_id: The configuration to build from.
            body: An optional ``BuildExecutionGraphRequest`` carrying
                ``time_range_start`` and ``time_range_end``. Omitted, no body is
                sent and the window is the configuration's rolling window,
                ending now.

        Returns:
            :class:`GraphConfigBuildResponse`: ``graph_id``, ``entry_count``
            and ``status``.

        Raises:
            ValueError: If ``capability_id`` or ``config_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ORCHESTRATION_READ``, ``404``
                (``PerceivoNotFoundError``) for a configuration the caller
                cannot reach or when there are no runs to build from, and
                ``422`` (``PerceivoValidationError``) for a malformed body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            GraphConfigBuildResponse,
            self._post(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/execution-graphs/configs/{segment(config_id, 'config_id')}/build",
                json=body,
            ),
        )
