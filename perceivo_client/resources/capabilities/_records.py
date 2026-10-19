"""Capability records; run and restart; copy, lineage and versions.

One of the mixins that make up
:class:`~perceivo_client.resources.capabilities.CapabilitiesResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    CapabilityRead,
    CapabilityUpdateResult,
    LifecycleOperationResponse,
    LineageRestoreResult,
    TestInvokeResponse,
)
from perceivo_client.resources.capabilities._common import _BASE, _MixinBase
from perceivo_client.resources.capabilities._models import (
    _update_result,
)


class _RecordsMixin(_MixinBase):
    # -- records ---------------------------------------------------------------
    def list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> list[dict[str, Any]]:
        """One page of the organization's capabilities (``GET /capabilities``).

        The latest version of each live capability, ordered by name. The page
        is a bare array with no total: request the next ``page`` until one
        holds fewer than ``page_size`` items. The contract declares no model
        for an item, so each is the record the API sends.

        Args:
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Items per page, ``1`` to ``100``. Omitted, the API uses
                ``25``.

        Returns:
            ``list[dict[str, Any]]``: one page of capability records.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a ``page`` or ``page_size``
                out of range.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._get(_BASE, params={"page": page, "page_size": page_size})

    def create(self, body: dict[str, Any]) -> CapabilityRead:
        """Create a capability, version 1 (``POST /capabilities``).

        Not idempotent: a repeat creates another capability.

        Args:
            body: A ``CapabilityCreate`` object, sent as the JSON body.

        Returns:
            :class:`CapabilityRead`: the new capability.

        Raises:
            PerceivoAPIError: On an error response: ``400`` for a missing or
                unsuitable contract component, ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_CREATE``, and
                ``422`` (``PerceivoValidationError``) for a malformed body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(CapabilityRead, self._post(_BASE, json=body))

    def get(self, capability_id: str) -> CapabilityRead:
        """One capability version (``GET /capabilities/{capability_id}``).

        Args:
            capability_id: The capability version to read.

        Returns:
            :class:`CapabilityRead`; the record's other fields (``config``,
            ``orchestrations`` and the rest) are kept as extra attributes.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a capability that is deleted,
                does not exist or belongs to another organization, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityRead, self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}")
        )

    def update(self, capability_id: str, body: dict[str, Any]) -> CapabilityUpdateResult:
        """Change a capability (``PATCH /capabilities/{capability_id}``).

        The server decides from the fields sent whether the change is made in place or creates a
        new version: a different ``start_component_id``, ``end_component_id`` or
        ``orchestration_review_spec`` creates a new version, and anything else is changed in
        place. Either way, follow the returned ``id``: when ``version_created`` is true it names
        the new version, and ``propagation_summary`` (``None`` when no orchestration was
        affected) reports how member orchestrations were carried over.

        Args:
            capability_id: The capability version to change. A change that
                creates a new version must address the latest version.
            body: A ``CapabilityUpdate`` object; only the fields it carries change.

        Returns:
            :class:`CapabilityUpdateResult`.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` (the base ``PerceivoAPIError``)
                when a new ``start_component_id`` or ``end_component_id`` names a component
                that is missing, deleted, or not a START or END component, or for a change
                the Experimental capability does not allow, ``403`` (``PerceivoGrantError``)
                without the privilege the change needs, ``404`` (``PerceivoNotFoundError``)
                for a capability the caller cannot read, ``409`` (``PerceivoConflictError``)
                for a new version requested from a version that is not the latest, and
                ``422`` (``PerceivoValidationError``) for a malformed body.
            PerceivoConnectionError: If the API cannot be reached.
        """
        data = self._patch(f"{_BASE}/{segment(capability_id, 'capability_id')}", json=body)
        return self._model(CapabilityUpdateResult, _update_result(data))

    def delete(self, capability_id: str) -> None:
        """Soft-delete every live version of a lineage (``DELETE /capabilities/{capability_id}``).

        :meth:`restore` undoes it. A lineage with member orchestrations is
        refused and nothing is deleted.

        Args:
            capability_id: Any version of the lineage.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400``
                for an Experimental capability, ``409``
                (``PerceivoConflictError``) while member orchestrations are
                attached, ``422`` (``PerceivoValidationError``) for a malformed
                request and ``502`` (``PerceivoServerError``) when an upstream
                service fails. ``403`` (``PerceivoGrantError``) is answered
                without ``CAPABILITY_DELETE`` and ``404`` (``PerceivoNotFoundError``)
                for a capability the caller cannot read.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(capability_id, 'capability_id')}")

    # -- run and restart ---------------------------------------------------------
    def run(self, capability_id: str, body: dict[str, Any] | None = None) -> TestInvokeResponse:
        """Run the capability once (``POST /capabilities/{capability_id}/run``).

        The input goes to a member chosen by the live traffic plan, and the
        run is billed. When ``status`` is ``DISPATCHED``, ``request_id`` is the
        run id to follow with ``client.runs``; when it is ``QUEUED``, it names
        a queued input in ``client.queue``.

        Args:
            capability_id: The capability to run.
            body: An ``ExecuteCapabilityRequest`` object (``config``, the run's
                input, and ``artifact``). Omitted, ``{}`` is sent.

        Returns:
            :class:`TestInvokeResponse`: ``status``, ``request_id`` and the
            chosen ``orchestration_id``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when the plan has
                no eligible member, ``403`` (``PerceivoGrantError``)
                without ``CAPABILITY_INVOKE``, ``404`` (``PerceivoNotFoundError``)
                for a capability the caller cannot reach, ``409``
                (``PerceivoConflictError``) when no plan is active, ``413`` for a
                body over the request-size limit (``details`` holds
                ``limit_bytes``), ``422`` (``PerceivoValidationError``) for a
                malformed body and ``429``
                (``PerceivoExecutionLockedError``) while the organization's
                execution is locked.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TestInvokeResponse,
            self._post(f"{_BASE}/{segment(capability_id, 'capability_id')}/run", json=body or {}),
        )

    def restart(self, capability_id: str) -> LifecycleOperationResponse:
        """Restart the capability's workloads (``POST /capabilities/{capability_id}/restart``).

        Re-applies the plan in the background and replaces the running
        workloads with new ones carrying the latest configuration. A change to
        a member orchestration, a component or the plan's workload settings
        reaches a running capability only after a restart. The call answers as
        soon as the restart starts, takes no request body, and provisions
        billed compute.

        Args:
            capability_id: The capability to restart.

        Returns:
            :class:`LifecycleOperationResponse`: ``final_status`` is
            ``starting`` and ``operation_id`` names the restart.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when there is no
                plan or it has no allocations, ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_START_STOP``,
                ``404`` (``PerceivoNotFoundError``) for a capability the caller
                cannot reach, ``422`` (``PerceivoValidationError``) for a
                malformed request and ``429``
                (``PerceivoExecutionLockedError``) while the organization's
                execution is locked.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LifecycleOperationResponse,
            self._post(f"{_BASE}/{segment(capability_id, 'capability_id')}/restart"),
        )

    # -- copy, lineage and versions -------------------------------------------
    def copy(self, capability_id: str, body: dict[str, Any] | None = None) -> CapabilityRead:
        """Copy the capability's configuration as a new capability (``POST .../copy``).

        Calls ``POST /capabilities/{capability_id}/copy``.

        ``body`` is an optional ``CapabilityCopyRequest`` (``new_name``);
        omitted, an empty object is sent. Attached orchestrations and the
        traffic plan are not copied.

        Args:
            capability_id: The capability to copy.
            body: An optional ``CapabilityCopyRequest`` object, sent as the
                JSON body.

        Returns:
            :class:`CapabilityRead`: the new capability.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a source the caller cannot read, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityRead,
            self._post(f"{_BASE}/{segment(capability_id, 'capability_id')}/copy", json=body or {}),
        )

    def get_lineage(self, capability_id: str) -> AssetLineageRead:
        """The capability's version lineage (``GET .../lineage``).

        Calls ``GET /capabilities/{capability_id}/lineage``.

        Args:
            capability_id: Any version of the capability.

        Returns:
            :class:`AssetLineageRead`: the versions of the lineage.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) or ``403`` (``PerceivoGrantError``) for an id that
                names no capability the caller can read, ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetLineageRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/lineage"),
        )

    def delete_version(self, capability_id: str, version_id: str) -> None:
        """Soft-delete one version of the lineage (``DELETE .../versions/{version_id}``).

        Calls ``DELETE /capabilities/{capability_id}/versions/{version_id}``.
        :meth:`restore` undoes the most recent deletion.

        Args:
            capability_id: Any version of the capability's lineage.
            version_id: The version to soft-delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``version_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400``
                (``PerceivoAPIError``) for an Experimental capability, ``403``
                (``PerceivoGrantError``) for a version the caller cannot delete, ``404``
                (``PerceivoNotFoundError``) for a version that is not live, not in the lineage, or
                not visible to the caller, ``409`` (``PerceivoConflictError``) for a version an
                orchestration still uses, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/versions/{segment(version_id, 'version_id')}"
        )

    def restore(self, capability_id: str) -> LineageRestoreResult:
        """Undo the lineage's most recent deletion (``POST .../restore``).

        Calls ``POST /capabilities/{capability_id}/restore``.

        Args:
            capability_id: Any version of the capability's lineage.

        Returns:
            :class:`LineageRestoreResult`: what was restored.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) when any version is not restorable by the caller
                (needs ``CAPABILITY_UPDATE``), ``404`` (``PerceivoNotFoundError``) for a lineage with
                nothing deleted or one the caller cannot see, ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``) when an upstream
                service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LineageRestoreResult,
            self._post(f"{_BASE}/{segment(capability_id, 'capability_id')}/restore"),
        )
