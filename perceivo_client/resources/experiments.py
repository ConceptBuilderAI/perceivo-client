"""Experiments namespace (``client.experiments``).

CRUD for notebook experiments, and the session lifecycle: queue a run, read
the live session, stop it, on the ``/v1/experiments`` routes.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    ExperimentDeleteResponse,
    ExperimentListResponse,
    ExperimentRead,
    ExperimentRunResponse,
    ExperimentSession,
    ExperimentStopResponse,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/experiments"


class ExperimentsResource(BaseResource):
    """Create experiments and run their notebook sessions."""

    def list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> ExperimentListResponse:
        """One page of the organization's experiments, newest first (``GET /experiments``).

        An ``items,total`` page, so ``paginate_pages(client.experiments.list)``
        walks it. Deleted experiments are excluded.

        Args:
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Items per page, ``1`` to ``100``. Omitted, the API uses
                ``25``.

        Returns:
            :class:`ExperimentListResponse`: one ``items,total`` page.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a ``page`` or ``page_size``
                out of range, and ``502`` (``PerceivoServerError``) when an
                upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentListResponse,
            self._get(_BASE, params={"page": page, "page_size": page_size}),
        )

    def create(self, body: dict[str, Any]) -> ExperimentRead:
        """Create an experiment in ``DRAFT`` (``POST /experiments``).

        Creating one starts no session and incurs no compute.

        Args:
            body: An ``ExperimentCreate`` object; ``name`` is required.

        Returns:
            :class:`ExperimentRead`: the new experiment.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a body the API refuses, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ExperimentRead, self._post(_BASE, json=body))

    def get(self, experiment_id: str) -> ExperimentRead:
        """Fetch one experiment (``GET /experiments/{experiment_id}``).

        Args:
            experiment_id: The experiment to read.

        Returns:
            :class:`ExperimentRead`.

        Raises:
            ValueError: If ``experiment_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for an experiment that does not exist or belongs to
                another organization, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentRead, self._get(f"{_BASE}/{segment(experiment_id, 'experiment_id')}")
        )

    def update(self, experiment_id: str, body: dict[str, Any]) -> ExperimentRead:
        """Patch an experiment (``PATCH /experiments/{experiment_id}``).

        Only ``name``, ``description`` and ``compute_config`` change. Runtime
        fields are managed by the platform; any other field is ignored.

        Args:
            experiment_id: The experiment to update.
            body: An ``ExperimentUpdate`` object.

        Returns:
            :class:`ExperimentRead`: the experiment after the update.

        Raises:
            ValueError: If ``experiment_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an experiment that does not
                exist, is deleted or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentRead,
            self._patch(f"{_BASE}/{segment(experiment_id, 'experiment_id')}", json=body),
        )

    def delete(self, experiment_id: str) -> ExperimentDeleteResponse:
        """Soft-delete an experiment (``DELETE /experiments/{experiment_id}``).

        Only the deletion time is recorded: the experiment leaves the list and
        its run, session and stop operations answer ``404`` from then on. A
        running session is not stopped by the delete, so call :meth:`stop`
        first. There is no undelete. The route answers ``200`` with an
        ``ExperimentDeleteResponse``, not ``204``.

        Args:
            experiment_id: The experiment to delete.

        Returns:
            :class:`ExperimentDeleteResponse`.

        Raises:
            ValueError: If ``experiment_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for an experiment that does not exist or belongs to
                another organization, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when an upstream service fails,
                in which case the delete may have been applied.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentDeleteResponse,
            self._delete(f"{_BASE}/{segment(experiment_id, 'experiment_id')}"),
        )

    def run(self, experiment_id: str) -> ExperimentRunResponse:
        """Queue the experiment's session to start (``POST .../run``, ``202``).

        Full path: ``POST /experiments/{experiment_id}/run``. Nothing is
        running yet when this returns: poll :meth:`get_session`. The session runs
        compute. The route takes no request body.

        Args:
            experiment_id: The experiment to run.

        Returns:
            :class:`ExperimentRunResponse`.

        Raises:
            ValueError: If ``experiment_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``409``
                (``PerceivoConflictError``) when the experiment is already queued, running or
                stopping, ``404`` (``PerceivoNotFoundError``) for an experiment that does not exist,
                is deleted or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentRunResponse,
            self._post(f"{_BASE}/{segment(experiment_id, 'experiment_id')}/run"),
        )

    def get_session(self, experiment_id: str) -> ExperimentSession:
        """The live session: status, kernel endpoint and activity (``GET .../session``).

        Full path: ``GET /experiments/{experiment_id}/session``.
        ``connection_endpoint`` and ``kernel_id`` are ``None`` while the
        experiment is queued or stopped.

        Args:
            experiment_id: The experiment whose session to read.

        Returns:
            :class:`ExperimentSession`.

        Raises:
            ValueError: If ``experiment_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an experiment that does not
                exist, is deleted or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentSession,
            self._get(f"{_BASE}/{segment(experiment_id, 'experiment_id')}/session"),
        )

    def stop(self, experiment_id: str) -> ExperimentStopResponse:
        """Request teardown of the session (``POST .../stop``).

        Full path: ``POST /experiments/{experiment_id}/stop``. A stopped,
        failed or stopping experiment is left as it is and its status is
        reported, so a retry after a timeout is safe. From any other status,
        ``DRAFT`` and ``QUEUED`` included, the status becomes ``STOPPING``.
        The route takes no request body.

        Args:
            experiment_id: The experiment to stop.

        Returns:
            :class:`ExperimentStopResponse`.

        Raises:
            ValueError: If ``experiment_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an experiment that does not
                exist, is deleted or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ExperimentStopResponse,
            self._post(f"{_BASE}/{segment(experiment_id, 'experiment_id')}/stop"),
        )
