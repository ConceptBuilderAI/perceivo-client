"""Orchestrations namespace (``client.orchestrations``).

The orchestration lifecycle: create, read, change and delete orchestrations;
start a run; edit the graph through drafts and publish a draft as the next
version; validate a definition; assign an orchestration to a capability and
check its compatibility; copy, export and import; read the graph and the
version lineage; delete and restore versions; and bind secrets to nodes.

A run, once started, is monitored on ``client.runs``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    AssignCapabilityResultRead,
    CapabilityCompatibilityRead,
    ExecuteResponseRead,
    ImportResultRead,
    NodeSecretBinding,
    NodeSecretRead,
    OrchestrationDraftPublished,
    OrchestrationDraftRead,
    OrchestrationExportRead,
    OrchestrationGraph,
    OrchestrationRead,
    OrchestrationRestoreResult,
    OrchestrationUpdateResult,
    OrchestrationValidationResult,
    PaginatedItemsResponse,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/orchestrations"


class OrchestrationsResource(BaseResource):
    """Create, change, version and run orchestrations."""

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

    # -- node secret bindings ------------------------------------------------
    def list_node_secret_bindings(self, orchestration_id: str) -> list[NodeSecretRead]:
        """List every node secret binding of an orchestration version (``GET .../node-secrets``).

        Calls ``GET /orchestrations/{orchestration_id}/node-secrets``. Each row
        names the node, the alias, and the secret's id, name, status and
        expiry; no operation returns a secret value. The rows come in one
        response, ordered by node and alias. For one node's aliases alone,
        use :meth:`get_node_secret_aliases`.

        Args:
            orchestration_id: The orchestration version whose bindings are
                listed.

        Returns:
            ``list[NodeSecretRead]``.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_READ`` on the
                orchestration, or another organization's orchestration
                (``403``).
            PerceivoNotFoundError: For an orchestration that is absent or
                deleted (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            NodeSecretRead,
            self._get(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/node-secrets"),
        )

    def create_node_secret_binding(
        self, orchestration_id: str, body: dict[str, Any]
    ) -> NodeSecretRead:
        """Bind a secret to a node under an alias (``POST .../node-secrets``).

        Calls ``POST /orchestrations/{orchestration_id}/node-secrets``. Not
        idempotent: binding an alias the node already has is refused. For an
        idempotent bind use :meth:`replace_node_secret_binding`.

        Args:
            orchestration_id: The orchestration version to bind into.
            body: A ``BindNodeSecretRequest`` object. ``node_id``, ``alias``
                and ``secret_id`` are all required. The request carries the
                secret's id, never its value.

        Returns:
            :class:`NodeSecretRead` — the stored binding (``201``).

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without
                ``ORCHESTRATION_UPDATE`` on the orchestration (``403``).
            PerceivoNotFoundError: For an orchestration or secret that is
                absent or not usable by the key (``404``).
            PerceivoConflictError: For a template orchestration (``409``).
            PerceivoValidationError: For a missing or malformed field (``422``).
            PerceivoAPIError: On any other error response, including ``400``
                for a secret that is not active or an alias already bound on
                the node.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            NodeSecretRead,
            self._post(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/node-secrets", json=body
            ),
        )

    def get_node_secret_aliases(self, orchestration_id: str, node_id: str) -> NodeSecretBinding:
        """Read one node's bindings as an alias-to-secret-id map (``GET .../nodes/{node_id}/secrets``).

        Calls ``GET /orchestrations/{orchestration_id}/nodes/{node_id}/secrets``.
        A node with no bindings, including a node the version does not have,
        answers an empty map.

        Args:
            orchestration_id: The orchestration version.
            node_id: The node.

        Returns:
            :class:`NodeSecretBinding` — read the map from ``.root``.

        Raises:
            ValueError: If ``orchestration_id`` or ``node_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_READ`` on the
                orchestration, or another organization's orchestration
                (``403``).
            PerceivoNotFoundError: For an orchestration that is absent or
                deleted (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            NodeSecretBinding,
            self._get(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/nodes/{segment(node_id, 'node_id')}/secrets"
            ),
        )

    def replace_node_secret_binding(
        self, orchestration_id: str, node_id: str, alias: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        """Make a node's alias name a secret (``PUT .../nodes/{node_id}/secrets/{alias}``).

        Calls ``PUT /orchestrations/{orchestration_id}/nodes/{node_id}/secrets/{alias}``.
        Idempotent: binding an alias to the secret it already names changes
        nothing. An alias bound to a different secret is refused; to rebind,
        :meth:`delete_node_secret_binding` first.

        Args:
            orchestration_id: The orchestration version.
            node_id: The node.
            alias: The name the node's script reads the secret by.
            body: A ``NodeSecretBindRequest`` object, ``{"secret_id": ...}``.

        Returns:
            ``dict[str, Any]`` — on a new binding (``201``) the stored row
            (``id``, ``orchestration_id``, ``node_id``, ``alias``,
            ``secret_id``, ``created_at`` and the secret's name, status and
            expiry); when the alias already named this secret (``200``),
            ``{node_id, alias, secret_id}``.

        Raises:
            ValueError: If ``orchestration_id``, ``node_id`` or ``alias`` is
                empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``ORCHESTRATION_READ`` and
                ``ORCHESTRATION_UPDATE`` on the orchestration (``403``).
            PerceivoNotFoundError: For an orchestration or secret that is
                absent or not usable by the key (``404``).
            PerceivoConflictError: For an alias bound to a different secret
                (``code`` ``alias_bound_to_another_secret``), or a template
                orchestration (``409``).
            PerceivoServerError: When the current bindings could not be read
                (``502``); nothing changed.
            PerceivoAPIError: On any other error response, including ``400``
                for a secret that is not active.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._put(
            f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/nodes/{segment(node_id, 'node_id')}/secrets/{segment(alias, 'alias')}",
            json=body,
        )

    def delete_node_secret_binding(self, orchestration_id: str, node_id: str, alias: str) -> None:
        """Remove a node's secret binding (``DELETE .../nodes/{node_id}/secrets/{alias}``).

        Calls ``DELETE /orchestrations/{orchestration_id}/nodes/{node_id}/secrets/{alias}``.
        Only the binding is removed; the secret itself is kept. Runs already
        in flight keep the binding they started with.

        Args:
            orchestration_id: The orchestration version.
            node_id: The node whose binding is removed.
            alias: The alias to unbind.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``orchestration_id``, ``node_id`` or ``alias`` is
                empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without
                ``ORCHESTRATION_UPDATE`` on the orchestration (``403``).
            PerceivoNotFoundError: For an orchestration that is absent, or no
                binding with that node and alias (``404``).
            PerceivoConflictError: For a template orchestration (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(
            f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/nodes/{segment(node_id, 'node_id')}/secrets/{segment(alias, 'alias')}"
        )

    # -- drafts --------------------------------------------------------------
    def list_drafts(self) -> list[OrchestrationDraftRead]:
        """List the caller's orchestration drafts (``GET /orchestrations/drafts``).

        The body is a bare array and the route takes no page parameters.

        Returns:
            ``list[OrchestrationDraftRead]`` — every draft, in one response.

        Raises:
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(OrchestrationDraftRead, self._get(f"{_BASE}/drafts"))

    def create_draft(self, body: dict[str, Any]) -> OrchestrationDraftRead:
        """Open a draft (``POST /orchestrations/drafts``).

        A draft holds graph and runtime changes until :meth:`publish_draft`
        turns it into the next version.

        Args:
            body: An ``OrchestrationDraftCreate`` object, sent as the JSON body.
                Include ``canvas_state``: the API refuses a draft without it.
                At most 16 MiB.

        Returns:
            :class:`OrchestrationDraftRead` — the new draft.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``413``
                (``PerceivoAPIError``) for a body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(OrchestrationDraftRead, self._post(f"{_BASE}/drafts", json=body))

    def get_draft(self, draft_id: str) -> OrchestrationDraftRead:
        """Read one draft (``GET /orchestrations/drafts/{draft_id}``).

        Args:
            draft_id: The draft to read.

        Returns:
            :class:`OrchestrationDraftRead`.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationDraftRead, self._get(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}")
        )

    def update_draft(self, draft_id: str, body: dict[str, Any]) -> OrchestrationDraftRead:
        """Change a draft (``PATCH /orchestrations/drafts/{draft_id}``).

        ``OrchestrationDraftUpdate`` body. This is how an orchestration's graph
        and runtime settings change: save them in a draft, then
        :meth:`publish_draft`.

        Args:
            draft_id: The draft to update.
            body: An ``OrchestrationDraftUpdate`` object; only the fields it
                carries change.

        Returns:
            :class:`OrchestrationDraftRead` — the draft after the update.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``413``
                (``PerceivoAPIError``) for a body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationDraftRead,
            self._patch(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}", json=body),
        )

    def delete_draft(self, draft_id: str) -> None:
        """Discard a draft (``DELETE /orchestrations/drafts/{draft_id}``, ``204``).

        Args:
            draft_id: The draft to discard.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}")

    def publish_draft(self, draft_id: str, body: dict[str, Any]) -> OrchestrationDraftPublished:
        """Publish a draft as the next version (``POST .../drafts/{draft_id}/publish``).

        Calls ``POST /orchestrations/drafts/{draft_id}/publish``.

        ``body`` is an ``OrchestrationDraftPublish``; ``expected_base_version_id``
        is required and a mismatch answers ``409``. On success the draft is
        deleted and the result names the new version's ``orchestration_id``.
        The reason for a ``409`` or ``422`` is in the error's
        ``details["error_code"]``, not its top-level ``code``. A failure after
        the version was committed can still be reported as an error: before
        publishing again, check :meth:`get_lineage` for the new version.

        Args:
            draft_id: The draft to publish.
            body: An ``OrchestrationDraftPublish`` object, sent as the JSON body.

        Returns:
            :class:`OrchestrationDraftPublished` — names the new version.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoConflictError: With ``details["error_code"]``
                ``DRAFT_BASE_STALE``, ``LINEAGE_VERSION_CONFLICT``,
                ``DRAFT_NOT_LINEAGE_BOUND`` or ``DRAFT_PAYLOAD_MISSING``
                (``409``).
            PerceivoValidationError: With ``details["error_code"]``
                ``ORCHESTRATION_INVALID`` or ``STAGED_CHANGE_TARGET_MISSING``,
                or for a malformed request (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationDraftPublished,
            self._post(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}/publish", json=body),
        )

    # -- definition and capability -------------------------------------------
    def validate(self, body: dict[str, Any]) -> OrchestrationValidationResult:
        """Validate a definition without creating anything (``POST /orchestrations/validate``).

        An invalid definition is not an error: the answer is ``200`` with
        ``valid: false`` and the reasons.

        Args:
            body: An ``OrchestrationDefinitionValidate`` object (the definition
                to check), sent as the JSON body.

        Returns:
            :class:`OrchestrationValidationResult` — read ``valid`` and the
            reasons.

        Raises:
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
                An invalid definition is not an error.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationValidationResult, self._post(f"{_BASE}/validate", json=body)
        )

    def assign_capability(
        self, orchestration_id: str, body: dict[str, Any]
    ) -> AssignCapabilityResultRead:
        """Clone the orchestration into a capability (``POST .../assign-capability``).

        Calls ``POST /orchestrations/{orchestration_id}/assign-capability``.

        ``body`` is an ``AssignCapabilityRequest`` (``capability_id`` required).
        The source is left untouched; check ``compatibility.disconnected_edges``
        on the result, since edges that no longer type-check are dropped, not
        refused.

        Args:
            orchestration_id: The orchestration to clone.
            body: An ``AssignCapabilityRequest`` object, sent as the JSON body.

        Returns:
            :class:`AssignCapabilityResultRead` — the clone and its
            ``compatibility`` report.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssignCapabilityResultRead,
            self._post(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/assign-capability",
                json=body,
            ),
        )

    def get_compatibility(
        self, orchestration_id: str, capability_id: str
    ) -> CapabilityCompatibilityRead:
        """Check whether the orchestration's edges type-check against a capability.

        Calls ``GET /orchestrations/{orchestration_id}/compatibility?capability_id=...``.

        Args:
            orchestration_id: The orchestration to check.
            capability_id: The capability to check against (the required
                ``capability_id`` query parameter).

        Returns:
            :class:`CapabilityCompatibilityRead`.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a capability you cannot see or that does not exist,
                and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityCompatibilityRead,
            self._get(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/compatibility",
                params={"capability_id": capability_id},
            ),
        )

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

    # -- lineage and versions ------------------------------------------------
    def get_lineage(self, orchestration_id: str) -> AssetLineageRead:
        """Read the orchestration's version lineage (``GET .../lineage``).

        Calls ``GET /orchestrations/{orchestration_id}/lineage``.

        Args:
            orchestration_id: Any version of the orchestration.

        Returns:
            :class:`AssetLineageRead` — the versions of the lineage, newest
            first.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetLineageRead,
            self._get(f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/lineage"),
        )

    def delete_version(self, orchestration_id: str, version_id: str) -> None:
        """Soft-delete one version of the lineage (``DELETE .../versions/{version_id}``).

        Calls ``DELETE /orchestrations/{orchestration_id}/versions/{version_id}``.
        :meth:`restore` undoes the most recent deletion.

        Args:
            orchestration_id: Any version of the orchestration's lineage.
            version_id: The version to soft-delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``orchestration_id`` or ``version_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a version the caller cannot delete, ``404``
                (``PerceivoNotFoundError``) for a version that is not live or not in the lineage,
                ``409`` (``PerceivoConflictError``) for a version a traffic plan still allocates,
                ``422`` (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(
            f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/versions/{segment(version_id, 'version_id')}"
        )

    def restore(
        self, orchestration_id: str, *, detach: bool | None = None
    ) -> OrchestrationRestoreResult:
        """Undo the lineage's most recent deletion (``POST .../restore``).

        Calls ``POST /orchestrations/{orchestration_id}/restore``.
        ``detach=True`` detaches every restored version from its capability.

        Args:
            orchestration_id: Any version of the orchestration's lineage.
            detach: Optional boolean ``detach`` query parameter, sent only when
                not ``None``; omitted, the server default ``false`` applies.

        Returns:
            :class:`OrchestrationRestoreResult` — what was restored.

        Raises:
            ValueError: If ``orchestration_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) when any version is not restorable by the caller
                (needs ``ORCHESTRATION_UPDATE``), ``404`` (``PerceivoNotFoundError``) for a lineage with
                nothing deleted or one the caller cannot see, ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``) when an upstream
                service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = None if detach is None else {"detach": detach}
        return self._model(
            OrchestrationRestoreResult,
            self._post(
                f"{_BASE}/{segment(orchestration_id, 'orchestration_id')}/restore", params=params
            ),
        )
