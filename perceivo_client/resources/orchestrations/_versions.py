"""Capability assignment, node secrets, lineage and versions of ``client.orchestrations``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    AssignCapabilityResultRead,
    CapabilityCompatibilityRead,
    NodeSecretBinding,
    NodeSecretRead,
    OrchestrationRestoreResult,
)
from perceivo_client.resources.orchestrations._common import _BASE

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _VersionsMixin(_MixinBase):
    """Capability assignment, node secrets, lineage and versions of ``client.orchestrations``."""

    # -- node secret bindings ------------------------------------------------
    def list_node_secret_bindings(self, orchestration_id: str) -> list[NodeSecretRead]:
        """List every node secret binding of an orchestration version (``GET .../node-secrets``).

        Calls ``GET /orchestrations/{orchestration_id}/node-secrets``. Each row
        names the node, the alias, and the secret's id, name, status and
        expiry; no operation returns a secret value. The rows come in one
        response, ordered by node and alias. For one node's aliases alone,
        use :meth:`get_node_secret_aliases`. To bind or unbind a node secret,
        stage ``secret_ops`` in a draft's ``publish_payload`` (:meth:`create_draft`
        or :meth:`update_draft`) and publish it with :meth:`publish_draft`.

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

    def get_node_secret_aliases(self, orchestration_id: str, node_id: str) -> NodeSecretBinding:
        """Read one node's bindings as an alias-to-secret-id map (``GET .../nodes/{node_id}/secrets``).

        Calls ``GET /orchestrations/{orchestration_id}/nodes/{node_id}/secrets``.
        A node with no bindings, including a node the version does not have,
        answers an empty map. Bindings change only through a draft's
        ``secret_ops``, applied by :meth:`publish_draft`.

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
