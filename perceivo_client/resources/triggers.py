"""Triggers namespace (``client.triggers``): scheduled triggers.

A trigger runs an orchestration on a cron schedule. Create, inspect, update and
delete triggers under ``/triggers``, and run one immediately with
:meth:`TriggersResource.invoke`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    OperationEnvelope,
    ScheduledTriggerListResponse,
    ScheduledTriggerRead,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/triggers"


class TriggersResource(BaseResource):
    """Manage scheduled triggers and run them on demand."""

    def list(self, **params: Any) -> ScheduledTriggerListResponse:
        """List the organization's triggers (``GET /triggers``).

        Args:
            **params: Query parameters: ``page`` (default ``1``) and
                ``page_size`` (default ``25``, at most ``100``). ``sort_by``
                and ``sort_order`` are accepted and ignored.

        Returns:
            :class:`ScheduledTriggerListResponse` — one ``items``/``total``
            page; ``total`` counts every visible trigger, so walk pages until
            ``page * page_size >= total``.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) when the key's organization
                cannot be verified, ``422`` (``PerceivoValidationError``) for a
                malformed query, and ``502`` (``PerceivoServerError``) when the
                platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ScheduledTriggerListResponse, self._get(_BASE, params=params or None))

    def create(self, body: dict[str, Any]) -> ScheduledTriggerRead:
        """Create a trigger (``POST /triggers``, ``201``).

        ``body`` is a ``ScheduledTriggerCreate``: the orchestration to run, a
        ``cron_expression`` and its time zone, and optional input, window and
        reviewer settings. The key needs ``ORCHESTRATION_EXECUTE`` on the
        orchestration. Not idempotent: a retry creates a second trigger.

        Args:
            body: A ``ScheduledTriggerCreate`` object, sent as the JSON body.

        Returns:
            :class:`ScheduledTriggerRead` — the new trigger.

        Raises:
            PerceivoAPIError: On an error response: ``400`` for an invalid
                ``cron_expression``, ``starts_at`` or ``ends_at``, ``403``
                (``PerceivoGrantError``) for a caller that may not run the
                orchestration, ``404`` (``PerceivoNotFoundError``) for an
                orchestration that does not exist, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: list the triggers before retrying, because the trigger
                may have been created.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ScheduledTriggerRead, self._post(_BASE, json=body))

    def get(self, trigger_id: str) -> ScheduledTriggerRead:
        """Read one trigger (``GET /triggers/{trigger_id}``).

        Args:
            trigger_id: The trigger to read.

        Returns:
            :class:`ScheduledTriggerRead`.

        Raises:
            ValueError: If ``trigger_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a trigger that does not exist or
                belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ScheduledTriggerRead, self._get(f"{_BASE}/{segment(trigger_id, 'trigger_id')}")
        )

    def update(self, trigger_id: str, body: dict[str, Any]) -> ScheduledTriggerRead:
        """Change a trigger (``PATCH /triggers/{trigger_id}``).

        ``body`` is a ``ScheduledTriggerUpdate``; only the fields sent change.

        Args:
            trigger_id: The trigger to change.
            body: A ``ScheduledTriggerUpdate`` object, sent as the JSON body.

        Returns:
            :class:`ScheduledTriggerRead` — the trigger after the change.

        Raises:
            ValueError: If ``trigger_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` for an invalid
                ``cron_expression``, ``starts_at`` or ``ends_at``, ``403``
                (``PerceivoGrantError``) for a caller that may not run the
                orchestration, ``404`` (``PerceivoNotFoundError``) for a
                trigger that does not exist or belongs to another organization,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the trigger before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ScheduledTriggerRead,
            self._patch(f"{_BASE}/{segment(trigger_id, 'trigger_id')}", json=body),
        )

    def delete(self, trigger_id: str) -> None:
        """Delete a trigger (``DELETE /triggers/{trigger_id}``, ``204``).

        Runs the trigger already started are not affected.

        Args:
            trigger_id: The trigger to delete.

        Raises:
            ValueError: If ``trigger_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller without authority
                over the trigger, ``404`` (``PerceivoNotFoundError``) for a
                trigger that does not exist or belongs to another organization,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer: list the triggers before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(trigger_id, 'trigger_id')}")

    def invoke(self, trigger_id: str, body: dict[str, Any] | None = None) -> OperationEnvelope:
        """Run a trigger's orchestration now (``POST /triggers/{trigger_id}/invoke``, ``202``).

        Starts one run immediately without touching the schedule. ``body`` is
        an optional ``TriggerInvokeRequest``: ``input_payload`` overrides the
        trigger's stored input for this run only. With no ``body``, no request
        body is sent and the stored input is used. The run is chargeable, and
        a retry starts another run.

        The answer is an operation handle that cannot be followed through this
        client: its ``poll``, ``result`` and ``events`` links name
        ``/v1/runs/{id}``, which the API does not serve, and its ``id``
        (``run_`` followed by 32 hexadecimal digits) is not a run id that
        :class:`perceivo_client.resources.runs.RunsResource` accepts. Find the
        started run with ``client.runs.list()``, which lists the newest runs
        first.

        Args:
            trigger_id: The trigger to run.
            body: An optional ``TriggerInvokeRequest`` object, sent as the JSON
                body when given.

        Returns:
            :class:`OperationEnvelope` — the handle of the started run.

        Raises:
            ValueError: If ``trigger_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller that may not run the
                orchestration, ``404`` (``PerceivoNotFoundError``) for a
                trigger that does not exist, was deleted, or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a
                malformed request, ``429`` (``PerceivoExecutionLockedError``) when
                the organization's execution is locked, and ``502``
                (``PerceivoServerError``) when the run could not be started;
                nothing was started, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OperationEnvelope,
            self._post(f"{_BASE}/{segment(trigger_id, 'trigger_id')}/invoke", json=body),
        )
