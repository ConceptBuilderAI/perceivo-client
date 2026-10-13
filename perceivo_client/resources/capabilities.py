"""Capabilities namespace (``client.capabilities``).

A capability serves its inputs through member orchestrations under a traffic
plan. This namespace covers the capability record and its versions, running
and restarting it, member orchestrations, the traffic plan, evaluation and its
schedule, and execution graphs. A capability's queued inputs are in
``client.queue``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    CapabilityEvaluationConfigRead,
    CapabilityEvaluationSummaryRead,
    CapabilityRead,
    CapabilityTrafficPlanRead,
    CapabilityTriggerRead,
    CapabilityUpdateResult,
    EvaluationTriggerResponse,
    ExecutionGraphBuildResponse,
    ExecutionGraphConfigRead,
    GraphConfigBuildResponse,
    LifecycleOperationResponse,
    LineageRestoreResult,
    PaginatedItemsResponse,
    TestInvokeResponse,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/capabilities"


class EvaluationRun(BaseModel):
    """One stored evaluation run, as :meth:`CapabilitiesResource.list_evaluations` lists it.

    Attributes:
        id: The evaluation run; pass it to
            :meth:`CapabilitiesResource.get_evaluation` as ``evaluation_id``.
        organization_id: The organization that owns the run.
        kind: The kind of evaluation, for example ``capability_run``.
        subject_type: What was evaluated: ``capability``.
        subject_id: The capability that was evaluated.
        evaluator_asset_id: The evaluator asset, when one was used.
        status: The run's state, for example ``running``, ``completed`` or
            ``failed``.
        trigger_type: What started the run, for example ``online`` or
            ``scheduled``.
        triggered_by_user_sub: Who started it; ``system`` for a scheduled run.
        started_at: When the run started, ISO 8601.
        completed_at: When the run finished, ISO 8601, or ``None``.
        duration_ms: How long the run took, in milliseconds, or ``None``.
        recommendation: The evaluator's recommendation, or ``None``.
        summary_metrics: The run's summary metrics, or ``None``.
        config: The configuration the run used, or ``None``.
        error_message: Why the run failed, or ``None``.
        created_at: When the row was created, ISO 8601.
        updated_at: When the row last changed, ISO 8601.
    """

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    organization_id: str | None = None
    kind: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    evaluator_asset_id: str | None = None
    status: str | None = None
    trigger_type: str | None = None
    triggered_by_user_sub: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    recommendation: str | None = None
    summary_metrics: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EvaluationRunPage(BaseModel):
    """A capability's most recent evaluation runs, from :meth:`CapabilitiesResource.list_evaluations`.

    Attributes:
        items: Up to the 20 most recent runs, newest first.
        total: How many runs the capability has in all; it can be larger than
            ``len(items)``.
    """

    model_config = ConfigDict(extra="allow")

    items: list[EvaluationRun] = Field(default_factory=list)
    total: int = 0


class EvaluationRunStatus(BaseModel):
    """One evaluation run's state, as :meth:`CapabilitiesResource.get_evaluation` returns it.

    Attributes:
        evaluation_id: The evaluation run.
        capability_id: The capability it evaluates.
        organization_id: The organization that owns the run.
        status: ``queued``, ``deploying``, ``running``, ``completed`` or
            ``failed``.
        summary_metrics: The run's summary metrics, or ``None``.
        error: Why the run failed, or ``None``.
        started_at: When the run started, ISO 8601. ``None`` while the
            platform still holds the run in progress.
        completed_at: When the run finished, ISO 8601, or ``None``.
        result: The evaluator's full result. Present only while the platform
            still holds the run in progress; ``None`` once it is read from
            storage.
    """

    model_config = ConfigDict(extra="allow")

    evaluation_id: str | None = None
    capability_id: str | None = None
    organization_id: str | None = None
    status: str | None = None
    summary_metrics: dict[str, Any] | None = None
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: Any = None


def _update_result(data: Any) -> Any:
    """Bring both update answers to the ``CapabilityUpdateResult`` shape.

    An in-place update answers the capability with ``version_created``. A
    change that creates a new version answers ``{"capability": {...},
    "versioned": true, "propagation_summary": ...}`` with no top-level ``id``;
    its ``capability`` is lifted to the top level, ``version_created`` is set
    from ``versioned``, and ``propagation_summary`` is kept.
    """
    if isinstance(data, dict) and "id" not in data and isinstance(data.get("capability"), dict):
        lifted = dict(data["capability"])
        lifted["version_created"] = data.get("versioned") is True
        lifted["propagation_summary"] = data.get("propagation_summary")
        return lifted
    return data


class CapabilitiesResource(BaseResource):
    """Invoke capabilities and manage rollout."""

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

        The server decides from the fields sent whether the change is made in
        place or creates a new version: a different ``start_component_id``,
        ``end_component_id`` or ``orchestration_review_spec`` creates a new
        version, and anything else is changed in place. Either way, follow the
        returned ``id``: when ``version_created`` is true it names the new
        version, and ``propagation_summary`` (``None`` when no orchestration
        was affected) reports how member orchestrations were carried over.

        Args:
            capability_id: The capability version to change. A change that
                creates a new version must address the latest version.
            body: A ``CapabilityUpdate`` object; only the fields it carries
                change.

        Returns:
            :class:`CapabilityUpdateResult`.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without the privilege the change
                needs, ``404`` (``PerceivoNotFoundError``) for a capability the
                caller cannot read, ``409`` (``PerceivoConflictError``) for a
                new version requested from a version that is not the latest,
                and ``422`` (``PerceivoValidationError``) for a malformed body.
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
                (``PerceivoConflictError``) when no plan is active, ``422``
                (``PerceivoValidationError``) for a malformed body and ``429``
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

    # -- evaluation --------------------------------------------------------------
    def evaluate(self, capability_id: str) -> EvaluationTriggerResponse:
        """Start an evaluation of the capability's runs (``POST .../evaluate``).

        Calls ``POST /capabilities/{capability_id}/evaluate``. The evaluator
        runs in the background with the settings of
        :meth:`get_evaluation_config`; the call answers once the batch is
        queued and takes no request body. Each call opens a new batch and
        starts billed compute. Scores appear in :meth:`get_evaluation_summary`.

        Args:
            capability_id: The capability to evaluate.

        Returns:
            :class:`EvaluationTriggerResponse`: ``status`` (``queued``) and
            ``evaluation_id``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_START_STOP``,
                ``404`` (``PerceivoNotFoundError``) for a capability the caller
                cannot reach, ``422`` (``PerceivoValidationError``) for a
                malformed request and ``429``
                (``PerceivoExecutionLockedError``) while the organization's
                execution is locked.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            EvaluationTriggerResponse,
            self._post(f"{_BASE}/{segment(capability_id, 'capability_id')}/evaluate"),
        )

    def list_evaluations(self, capability_id: str) -> EvaluationRunPage:
        """The capability's most recent evaluation runs (``GET .../evaluations``).

        Calls ``GET /capabilities/{capability_id}/evaluations``. The answer
        holds at most the 20 most recent runs, newest first; ``total`` counts
        every run. The route takes no paging or filter parameters, so older
        runs cannot be listed; read one by id with :meth:`get_evaluation`.
        Requires ``CAPABILITY_READ``.

        Args:
            capability_id: The capability whose evaluation runs to list.

        Returns:
            :class:`EvaluationRunPage` — ``items`` (each an
            :class:`EvaluationRun`) and ``total``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_READ``, ``404``
                (``PerceivoNotFoundError``) for a
                capability the caller cannot read, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            EvaluationRunPage,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/evaluations"),
        )

    def get_evaluation(self, capability_id: str, evaluation_id: str) -> EvaluationRunStatus:
        """One evaluation run (``GET .../evaluations/{evaluation_id}``).

        Calls ``GET /capabilities/{capability_id}/evaluations/{evaluation_id}``.
        The run's id is ``evaluation_id`` in the answer, not ``id``. While the
        platform still holds the run in progress the answer carries ``result``
        and no times; once the run is read from storage it carries
        ``started_at`` and ``completed_at`` and no ``result``. Requires
        ``CAPABILITY_READ``.

        Args:
            capability_id: The capability the run belongs to.
            evaluation_id: The run to read: ``evaluation_id`` from
                :meth:`evaluate`, or ``id`` from :meth:`list_evaluations`.

        Returns:
            :class:`EvaluationRunStatus`.

        Raises:
            ValueError: If ``capability_id`` or ``evaluation_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``CAPABILITY_READ``, ``404``
                (``PerceivoNotFoundError``) for a
                run or capability the caller cannot read, including a run that
                belongs to another capability, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            EvaluationRunStatus,
            self._get(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/evaluations/{segment(evaluation_id, 'evaluation_id')}"
            ),
        )

    def get_evaluation_config(self, capability_id: str) -> CapabilityEvaluationConfigRead:
        """How the capability's runs are evaluated (``GET .../evaluation-config``).

        Calls ``GET /capabilities/{capability_id}/evaluation-config``. The
        schedule that runs evaluations is not part of this document: it is
        read with :meth:`list_triggers`.

        Args:
            capability_id: The capability whose configuration to read.

        Returns:
            :class:`CapabilityEvaluationConfigRead`.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) when the capability has no
                evaluation configuration or is not yours (the two are
                indistinguishable), ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when
                an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityEvaluationConfigRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/evaluation-config"),
        )

    def replace_evaluation_config(
        self, capability_id: str, body: dict[str, Any]
    ) -> CapabilityEvaluationConfigRead:
        """Store the complete evaluation configuration.

        Calls ``PUT /capabilities/{capability_id}/evaluation-config``.

        ``body`` is a ``CapabilityEvaluationConfigWrite``. This is a replace,
        not a merge: an omitted field is reset to its default, so read
        :meth:`get_evaluation_config` first to change one setting. The stored
        schedule (:meth:`list_triggers`) is kept.

        Args:
            capability_id: The capability to configure.
            body: A ``CapabilityEvaluationConfigWrite`` object, sent as the JSON
                body.

        Returns:
            :class:`CapabilityEvaluationConfigRead`: the configuration as stored.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a capability that is not yours, ``403``
                (``PerceivoGrantError``), ``429`` (``PerceivoRateLimitError``) or a ``5xx``
                (``PerceivoServerError``) when the read of the stored configuration is refused
                (nothing is written), ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityEvaluationConfigRead,
            self._put(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/evaluation-config", json=body
            ),
        )

    def get_evaluation_summary(self, capability_id: str) -> CapabilityEvaluationSummaryRead:
        """Score statistics per evaluated orchestration (``GET .../evaluation-summary``).

        Calls ``GET /capabilities/{capability_id}/evaluation-summary``. A
        capability with no scores yet answers an empty ``orchestrations``
        list.

        Args:
            capability_id: The capability whose evaluations to summarise.

        Returns:
            :class:`CapabilityEvaluationSummaryRead`.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a capability that is not yours or does not exist,
                ``422`` (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityEvaluationSummaryRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/evaluation-summary"),
        )

    # -- traffic plan ------------------------------------------------------------
    def replace_traffic(
        self, capability_id: str, body: dict[str, Any]
    ) -> CapabilityTrafficPlanRead:
        """Replace the capability's traffic plan (``PUT .../traffic``).

        Calls ``PUT /capabilities/{capability_id}/traffic``. The allocations
        sent become the new ``active`` plan and the previous plan is
        superseded in the same transaction. :meth:`get_traffic` reads the
        plan this writes and :meth:`delete_traffic` supersedes it.

        Args:
            capability_id: The capability whose plan to replace.
            body: A ``CapabilityTrafficReplace`` object, sent as the JSON body.

        Returns:
            :class:`CapabilityTrafficPlanRead`: the plan now live.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC`` on the capability, ``409``
                (``PerceivoConflictError``) while another plan change is in progress (wait and
                retry), ``404`` (``PerceivoNotFoundError``) for another organization's capability or
                a missing one, ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTrafficPlanRead,
            self._put(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic", json=body),
        )

    def get_traffic(self, capability_id: str) -> CapabilityTrafficPlanRead | None:
        """The routing plan a run resolves against (``GET .../traffic``).

        Calls ``GET /capabilities/{capability_id}/traffic``.

        ``None`` when the capability has no live plan, and the same ``None``
        when the capability is not yours or does not exist: the three are
        deliberately indistinguishable. :meth:`replace_traffic` writes the
        plan.

        Args:
            capability_id: The capability whose plan to read.

        Returns:
            :class:`CapabilityTrafficPlanRead`, or ``None`` (see above).

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request. An unknown capability answers ``None``, not ``404``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTrafficPlanRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic"),
        )

    def delete_traffic(self, capability_id: str) -> None:
        """Supersede the live plan, releasing its hold on member orchestrations (``204``).

        Wraps ``DELETE /capabilities/{capability_id}/traffic``. While a plan is
        live its allocation blocks deleting the capability and its member
        orchestrations; stopping the capability does not release it. ``404``
        when there is no live plan.

        Args:
            capability_id: The capability whose plan to supersede.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC`` on the capability, ``404``
                (``PerceivoNotFoundError``) with no live plan or not your capability, ``422``
                (``PerceivoValidationError``) if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic")

    def get_traffic_plan(self, capability_id: str) -> CapabilityTrafficPlanRead | None:
        """The live traffic plan, through the rollout route (``GET .../traffic-plan``).

        Calls ``GET /capabilities/{capability_id}/traffic-plan``. It reads the
        same plan as :meth:`get_traffic` and answers the same record, with its
        ``allocations``; it is the read that pairs with
        :meth:`apply_traffic_plan` and :meth:`delete_traffic_plan`.

        ``None`` when the capability has no live plan or does not exist.

        Args:
            capability_id: The capability whose plan to read.

        Returns:
            :class:`CapabilityTrafficPlanRead`, or ``None`` (see above).

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request. An unknown capability answers ``None``, not ``404``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTrafficPlanRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic-plan"),
        )

    def apply_traffic_plan(
        self, capability_id: str, body: dict[str, Any]
    ) -> LifecycleOperationResponse:
        """Apply a traffic plan (``POST /capabilities/{capability_id}/traffic-plan``).

        ``body`` is an ``ApplyTrafficPlanRequest`` (``traffic_plan`` required).

        Args:
            capability_id: The capability to apply the plan to.
            body: An ``ApplyTrafficPlanRequest`` object, sent as the JSON body.

        Returns:
            :class:`LifecycleOperationResponse`: the lifecycle operation the
            apply started.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC``, ``404`` (``PerceivoNotFoundError``) for an unknown
                capability, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LifecycleOperationResponse,
            self._post(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic-plan", json=body
            ),
        )

    def delete_traffic_plan(self, capability_id: str) -> None:
        """Supersede every live traffic plan (``DELETE .../traffic-plan``, ``204``).

        Calls ``DELETE /capabilities/{capability_id}/traffic-plan``. The
        counterpart to :meth:`apply_traffic_plan`; ``404`` when there is no
        live plan to supersede.

        Args:
            capability_id: The capability whose plans to supersede.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC`` on the capability, ``404``
                (``PerceivoNotFoundError``) with no live plan, ``422`` if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic-plan")

    # -- evaluation trigger --------------------------------------------------
    def list_triggers(self, capability_id: str) -> list[CapabilityTriggerRead]:
        """The schedule that runs this capability's evaluations (``GET .../triggers``).

        Calls ``GET /capabilities/{capability_id}/triggers``.

        A bare array of at most one trigger; empty means no evaluations are
        scheduled. The route takes no page parameters.

        Args:
            capability_id: The capability whose schedule to read.

        Returns:
            ``list[CapabilityTriggerRead]``: zero or one trigger.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a capability that is not yours or does not exist,
                ``422`` (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            CapabilityTriggerRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/triggers"),
        )

    def create_trigger(self, capability_id: str, body: dict[str, Any]) -> CapabilityTriggerRead:
        """Schedule the capability's evaluations on a UTC cron (``POST .../triggers``).

        Calls ``POST /capabilities/{capability_id}/triggers``.

        ``body`` is a ``CapabilityTriggerCreate`` (``cron_expression``
        required). Each scheduled evaluation runs compute. A capability has at
        most one trigger and needs an evaluation configuration first; either
        missing precondition answers ``409``.

        Args:
            capability_id: The capability to schedule.
            body: A ``CapabilityTriggerCreate`` object, sent as the JSON body.

        Returns:
            :class:`CapabilityTriggerRead`: the trigger as stored.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``409``
                (``PerceivoConflictError``) when the capability already has a trigger or has no
                evaluation configuration, ``404`` (``PerceivoNotFoundError``) for a capability that
                is not yours, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTriggerRead,
            self._post(f"{_BASE}/{segment(capability_id, 'capability_id')}/triggers", json=body),
        )

    def update_trigger(
        self, capability_id: str, trigger_id: str, body: dict[str, Any]
    ) -> CapabilityTriggerRead:
        """Change the cron or turn the schedule on or off (``PATCH .../triggers/{trigger_id}``).

        Calls ``PATCH /capabilities/{capability_id}/triggers/{trigger_id}``.

        ``body`` is a ``CapabilityTriggerUpdate``; omitted fields are kept.

        Args:
            capability_id: The capability the trigger belongs to.
            trigger_id: The trigger to update.
            body: A ``CapabilityTriggerUpdate`` object, sent as the JSON body.

        Returns:
            :class:`CapabilityTriggerRead`: the trigger after the update.

        Raises:
            ValueError: If ``capability_id`` or ``trigger_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a trigger that does not exist or a capability that
                is not yours, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTriggerRead,
            self._patch(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/triggers/{segment(trigger_id, 'trigger_id')}",
                json=body,
            ),
        )

    def delete_trigger(self, capability_id: str, trigger_id: str) -> None:
        """Stop scheduling evaluations (``204``); the evaluation configuration is kept.

        Calls ``DELETE /capabilities/{capability_id}/triggers/{trigger_id}``.

        Args:
            capability_id: The capability the trigger belongs to.
            trigger_id: The trigger to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``trigger_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a trigger that does not exist or a capability that
                is not yours, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/triggers/{segment(trigger_id, 'trigger_id')}"
        )

    # -- member orchestrations -----------------------------------------------
    def list_orchestrations(
        self,
        capability_id: str,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> PaginatedItemsResponse:
        """One page of the capability's member orchestrations (``GET .../orchestrations``).

        Calls ``GET /capabilities/{capability_id}/orchestrations``. Newest
        first, as an ``items,total`` page, so
        ``paginate_pages(functools.partial(client.capabilities.list_orchestrations,
        capability_id))`` walks it. A capability that is not yours and one with
        nothing attached both answer an empty page.

        Args:
            capability_id: The capability whose members to list.
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Items per page, ``1`` to ``100``. Omitted, the API uses
                ``25``.

        Returns:
            :class:`PaginatedItemsResponse`: ``items`` and ``total``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PaginatedItemsResponse,
            self._get(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/orchestrations",
                params={"page": page, "page_size": page_size},
            ),
        )

    def attach_orchestration(self, capability_id: str, orchestration_id: str) -> None:
        """Make an orchestration a member (``PUT .../orchestrations/{orchestration_id}``).

        Calls ``PUT /capabilities/{capability_id}/orchestrations/{orchestration_id}``.

        Answers ``204``; a repeat is a no-op. Needs ``CAPABILITY_READ`` and
        ``CAPABILITY_UPDATE`` on the capability and update rights on the orchestration
        (``ORCHESTRATION_UPDATE`` for a key). A START/END ``409`` changes nothing.

        Args:
            capability_id: The capability to attach to.
            orchestration_id: The orchestration to attach.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``orchestration_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: ``404`` (``PerceivoNotFoundError``) without ``CAPABILITY_READ``;
                ``403`` (``PerceivoGrantError``) without the others; ``409``
                (``PerceivoConflictError``) if in another capability (detach it there first) or off
                the START/END contract; ``422`` (``PerceivoValidationError``) if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._put(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/orchestrations/{segment(orchestration_id, 'orchestration_id')}"
        )

    def detach_orchestration(self, capability_id: str, orchestration_id: str) -> None:
        """Remove a member orchestration; it reverts to standalone (``204``).

        Calls ``DELETE /capabilities/{capability_id}/orchestrations/{orchestration_id}``.

        Refused with ``409`` while it carries traffic under a live plan: supersede the plan first
        (:meth:`delete_traffic`). Needs what :meth:`attach_orchestration` needs.

        Args:
            capability_id: The capability to detach from.
            orchestration_id: The member orchestration to detach.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``orchestration_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: ``404`` (``PerceivoNotFoundError``) without ``CAPABILITY_READ``;
                ``403`` (``PerceivoGrantError``) without the others; ``409``
                (``PerceivoConflictError``) while it, or any version in its lineage, carries traffic
                under a live plan; ``422`` (``PerceivoValidationError``) if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/orchestrations/{segment(orchestration_id, 'orchestration_id')}"
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
