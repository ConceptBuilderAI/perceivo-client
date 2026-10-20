"""Evaluation runs, the evaluation configuration and summary, and evaluation triggers.

One of the mixins that make up
:class:`~perceivo_client.resources.capabilities.CapabilitiesResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    CapabilityEvaluationConfigRead,
    CapabilityEvaluationSummaryRead,
    CapabilityTriggerRead,
    EvaluationTriggerResponse,
)
from perceivo_client.resources.capabilities._common import _BASE, _MixinBase
from perceivo_client.resources.capabilities._models import (
    EvaluationRunPage,
    EvaluationRunStatus,
)


class _EvaluationMixin(_MixinBase):
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
