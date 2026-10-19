"""Orchestration CRUD, run, import, copy, export and graph of ``client.orchestrations``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    ExecuteResponseRead,
    ImportResultRead,
    OrchestrationExportRead,
    OrchestrationGraph,
    OrchestrationRead,
    OrchestrationUpdateResult,
    PaginatedItemsResponse,
)
from perceivo_client.resources.orchestrations._common import _BASE

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _LifecycleMixin(_MixinBase):
    """Orchestration CRUD, run, import, copy, export and graph of ``client.orchestrations``."""

    # -- CRUD --------------------------------------------------------------
    def list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> PaginatedItemsResponse:
        """List the organization's orchestrations, newest first (``GET /orchestrations``).

        Only the root of each lineage is listed. Each item carries the newest
        live version's fields; its ``id`` stays the root's and
        ``current_version_id`` names the newest version, which is the one to
        read or run. Page until ``page * page_size >= total``;
        ``paginate_pages`` walks this list.

        Args:
            page: Page number, 1 or more; the server default is ``1``.
            page_size: Items per page, 1 to 100; the server default is ``25``.

        Returns:
            :class:`PaginatedItemsResponse` — ``items`` (one orchestration
            record per item) and ``total``.

        Raises:
            PerceivoValidationError: For an out-of-range ``page`` or
                ``page_size`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"page": page, "page_size": page_size}
        return self._model(PaginatedItemsResponse, self._get(_BASE, params=params))

    def create(self, body: dict[str, Any]) -> OrchestrationRead:
        """Create an empty orchestration (``POST /orchestrations``).

        The orchestration has no nodes; add the graph through a draft
        (:meth:`create_draft`, :meth:`publish_draft`). The calling key is
        granted ``ORCHESTRATION_EXECUTE`` on it. Each call creates another
        orchestration.

        Args:
            body: An ``OrchestrationCreate`` object: ``name`` is required,
                ``description`` optional.

        Returns:
            :class:`OrchestrationRead` — the new orchestration (``201``).

        Raises:
            PerceivoGrantError: For a key without ``ORCHESTRATION_CREATE`` on the
                organization (``403``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(OrchestrationRead, self._post(_BASE, json=body))

    def get(self, orchestration_id: str) -> OrchestrationRead:
        """Read one orchestration with its nodes, ports and edges (``GET /orchestrations/{id}``).

        Args:
            orchestration_id: The orchestration version to read.

        Returns:
            :class:`OrchestrationRead`. The ``nodes``, ``ports`` and ``edges``
            are extra attributes beyond the declared fields.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_READ`` on the
                orchestration (``403``).
            PerceivoNotFoundError: For an orchestration that is absent, deleted
                or another organization's (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationRead, self._get(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}")
        )

    def update(self, orchestration_id: str, body: dict[str, Any]) -> OrchestrationUpdateResult:
        """Change an orchestration's name, description or tags (``PATCH /orchestrations/{id}``).

        The change is made in place. The graph and runtime settings change
        through a draft (:meth:`update_draft`, :meth:`publish_draft`); sending
        them here is refused.

        Args:
            orchestration_id: The orchestration to change.
            body: An ``OrchestrationMetadataUpdate`` object: any of ``name``,
                ``description`` and ``tags`` (which replaces the whole list).

        Returns:
            :class:`OrchestrationUpdateResult` — the record and
            ``version_created``. Follow its ``id``.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_UPDATE``
                (``403``).
            PerceivoNotFoundError: For an orchestration that is absent, deleted
                or another organization's (``404``).
            PerceivoConflictError: For a template (``409``).
            PerceivoValidationError: For a graph, runtime or unknown field
                (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationUpdateResult,
            self._patch(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}", json=body),
        )

    def delete(self, orchestration_id: str) -> None:
        """Delete every live version of an orchestration's lineage (``DELETE /orchestrations/{id}``).

        A soft delete, undone by :meth:`restore`. Any version id of the lineage
        may be passed. A version still allocated by a draft or a traffic plan,
        or nested by another orchestration, blocks the whole delete.

        Args:
            orchestration_id: Any version of the lineage.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_DELETE`` on
                every live version (``403``).
            PerceivoNotFoundError: For an orchestration that is absent, already
                deleted or another organization's (``404``).
            PerceivoConflictError: For a version still in use (``409``);
                ``details`` names the blocking versions and their users.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}")

    # -- run -----------------------------------------------------------------
    def run(self, orchestration_id: str, body: dict[str, Any] | None = None) -> ExecuteResponseRead:
        """Start a run of one orchestration version (``POST /orchestrations/{id}/run``).

        The run spends compute while it executes. Where the orchestration
        belongs to a capability, the input may be queued instead of run at
        once. The ``result`` mapping of the answer says which:

        * ``result["run_id"]``: the run; poll it with ``client.runs``.
        * ``result["request_id"]``: the queued input, when no run exists yet.
          Find its run through ``client.queue.list``: the item whose ``id`` is
          the ``request_id`` carries the ``run_id`` once it is dispatched.

        Args:
            orchestration_id: The orchestration version to run.
            body: An optional ``ExecuteOrchestrationRequest`` object, for
                example ``{"input": {...}}``. Omitted, an empty object is sent
                and the run starts with an empty input.

        Returns:
            :class:`ExecuteResponseRead` — ``success``, ``action``,
            ``target_id``, ``message`` and the ``result`` mapping described
            above.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_EXECUTE`` on the
                orchestration or one of its components (``403``).
            PerceivoNotFoundError: For an orchestration that is absent, deleted
                or another organization's, or one with no nodes (``404``).
            PerceivoExecutionLockedError: For an organization whose execution
                is locked (``429``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExecuteResponseRead,
            self._post(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/run", json=body or {}
            ),
        )

    # -- import ------------------------------------------------------------
    def import_bundle(self, body: dict[str, Any]) -> ImportResultRead:
        """Create an orchestration from an export document (``POST /orchestrations/import``).

        Every component in the document is created anew in the caller's
        organization; nothing is reused. The import is all or nothing. Secret
        values are not carried over: ``unresolved_secrets`` on the result lists
        the bindings to make. Each call creates another orchestration.

        Args:
            body: The document :meth:`export_bundle` returned, optionally with
                ``new_name`` and ``import_as_draft``. At most 16 MiB.

        Returns:
            :class:`ImportResultRead` (``201``).

        Raises:
            PerceivoGrantError: For a key without ``ORCHESTRATION_CREATE``
                (``403``).
            PerceivoNotFoundError: For a node naming a component the
                organization cannot use (``404``).
            PerceivoValidationError: For a document that does not match the
                export format (``422``).
            PerceivoAPIError: On any other error response, including ``400``
                for a graph that fails validation and ``413`` for a body over
                16 MiB.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ImportResultRead, self._post(f"{_BASE}/import", json=body))

    # -- copy, export and graph ----------------------------------------------
    def copy(self, orchestration_id: str, body: dict[str, Any] | None = None) -> OrchestrationRead:
        """Copy an orchestration as a new, unrelated asset (``POST .../copy``).

        Calls ``POST /orchestrations/{orchestration_id}/copy``.

        ``body`` is an optional ``OrchestrationCopyRequest`` (``new_name``,
        ``capability_id``, ``standalone``, ``copy_secret_bindings``); omitted,
        an empty object is sent.

        Args:
            orchestration_id: The orchestration to copy.
            body: An optional ``OrchestrationCopyRequest`` object, sent as the
                JSON body.

        Returns:
            :class:`OrchestrationRead` — the new orchestration.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationRead,
            self._post(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/copy", json=body or {}
            ),
        )

    def export_bundle(self, orchestration_id: str) -> OrchestrationExportRead:
        """Export an orchestration as a portable document (``GET .../export``).

        Calls ``GET /orchestrations/{orchestration_id}/export``.

        Args:
            orchestration_id: The orchestration to export.

        Returns:
            :class:`OrchestrationExportRead` — the document
            :meth:`import_bundle` accepts.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationExportRead,
            self._get(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/export"),
        )

    def get_graph(self, orchestration_id: str) -> OrchestrationGraph:
        """Read the orchestration's nodes, ports and edges (``GET .../graph``).

        Calls ``GET /orchestrations/{orchestration_id}/graph``.

        Args:
            orchestration_id: The orchestration to read.

        Returns:
            :class:`OrchestrationGraph`.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationGraph,
            self._get(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/graph"),
        )
