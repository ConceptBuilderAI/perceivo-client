"""Runs namespace (``client.runs``): monitor and control orchestration runs.

A run is one execution of an orchestration. Start one with
:meth:`perceivo_client.resources.orchestrations.OrchestrationsResource.run`,
which returns the ``run_id`` the methods here take: read the run's status,
result, artifacts, events, steps and logs, and pause, resume, stop or cancel
it. :meth:`RunsResource.list` lists the organization's runs.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    RunArtifacts,
    RunControlResult,
    RunEvents,
    RunPage,
    RunResult,
    RunStatus,
    RunSteps,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/orchestrations/runs"
_LOGS = "/v1/logs"


class RunLogPage(BaseModel):
    """The log lines of one run, as :meth:`RunsResource.logs` returns them.

    Attributes:
        entries: The log lines. Each is a mapping with ``timestamp`` (RFC 3339),
            ``labels`` (the stream labels), ``line`` (the raw line) and
            ``json`` (the line parsed as JSON, or ``None``).
        count: The number of lines in ``entries``.
        limit: The line limit the read was made with.
        workload_id: The workload the run belongs to; its lines are read
            inside the run's own start and end times.
        run_id: The run, echoed only for a run that has not started (which
            has no lines yet).
        namespace_resolved: ``False`` when the platform could not locate the
            organization's log streams, so an empty ``entries`` does not mean
            the run wrote nothing.
    """

    model_config = ConfigDict(extra="allow")

    entries: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    limit: int | None = None
    workload_id: str | None = None
    run_id: str | None = None
    namespace_resolved: bool | None = None


class RunsResource(BaseResource):
    """List, monitor and control orchestration runs."""

    def list(
        self,
        *,
        status: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> RunPage:
        """List the organization's runs, newest first (``GET /orchestrations/runs``).

        Runs are collected from the organization's 100 most recently created
        workloads; read an older run by ``run_id``. A key without
        ``WORKLOAD_READ`` sees only the runs of workloads it started.

        :func:`perceivo_client.paginate_pages` refuses this method, because
        ``total`` counts only the runs in the returned page. Page it yourself:
        pass ``page=1, 2, ...`` with a fixed ``page_size`` until a page shorter
        than ``page_size``, or an empty one, comes back.

        Args:
            status: Run state to filter on (for example ``"RUNNING"``,
                case-insensitive), sent as ``filter[status]``. Omit it for
                every state.
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Runs per page, at most ``100``. Omitted, the API uses
                ``20``.

        Returns:
            :class:`RunPage` — one ``items``/``total`` page of runs. ``total``
            counts the runs in the returned page only.

        Raises:
            PerceivoAPIError: On an error response: ``422``
                (``PerceivoValidationError``) for a ``page`` or ``page_size``
                out of range, ``502`` (``PerceivoServerError``) when the
                platform answers with something that is not a run list, and
                ``504`` (``PerceivoServerError``) when the runs cannot be
                collected in time; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"filter[status]": status, "page": page, "page_size": page_size}
        return self._model(RunPage, self._get(_BASE, params=params))

    def get(self, run_id: str) -> RunStatus:
        """Read a run's status (``GET /orchestrations/runs/{run_id}``).

        Requires ``WORKLOAD_READ``, or being the key that started the run.

        Args:
            run_id: The run to read.

        Returns:
            :class:`RunStatus`.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller that did not start
                the run and lacks ``WORKLOAD_READ``, ``404``
                (``PerceivoNotFoundError``) for a run that is unknown, belongs
                to another organization, or whose workload has been removed,
                and ``502`` (``PerceivoServerError``) when the platform answers
                with something that is not this run; nothing was read, so
                retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RunStatus, self._get(f"{_BASE}/{segment(run_id, 'run_id')}"))

    def result(self, run_id: str) -> RunResult:
        """Read a run's output (``GET /orchestrations/runs/{run_id}/result``).

        ``output_payload`` is ``None`` until the run has finished. A failed run
        answers normally with its terminal ``status`` and ``error_message``.

        Args:
            run_id: The run to read.

        Returns:
            :class:`RunResult`.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, as for :meth:`get`.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RunResult, self._get(f"{_BASE}/{segment(run_id, 'run_id')}/result"))

    def logs(
        self,
        run_id: str,
        *,
        channel: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int | None = None,
        order: str | None = None,
    ) -> RunLogPage:
        """Read a run's log lines (``GET /logs?scope=run&scope_id=<run_id>``).

        The same read as ``client.query.logs("run", scope_id=run_id, ...)``,
        with a typed answer. The lines are the run's workload's lines inside
        the run's own start and end times: a ``start`` or ``end`` outside that
        window is narrowed to it, and a run that has not started returns no
        lines. Requires ``WORKLOAD_READ``. An argument left as ``None`` is not
        sent.

        Args:
            run_id: The run, sent as ``scope_id``.
            channel: The kind of line: ``provider``, ``conversation``,
                ``conversation_input``, ``conversation_stream``, ``error``,
                ``extension``, ``snapshot`` or ``state_transition``. Omitted,
                every kind.
            start: Window start, RFC 3339 or Unix nanoseconds; sent as
                ``from``.
            end: Window end, in the same forms; sent as ``to``.
            limit: Lines to return, at most ``5000``. Omitted, the API returns
                ``100``.
            order: ``newest_first`` (the default) or ``oldest_first``.

        Returns:
            :class:`RunLogPage` — the lines under ``entries``.

        Raises:
            ValueError: If ``run_id`` is empty (refused before the request is
                sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a run that is unknown, belongs
                to another organization, or that the caller may not read,
                ``422`` (``PerceivoValidationError``) for an unknown channel or
                order, a ``start`` or ``end`` that is not a time, or a
                ``limit`` over ``5000``, and ``502`` (``PerceivoServerError``)
                when the log store cannot be read.
            PerceivoConnectionError: If the API cannot be reached.
        """
        ident = str(run_id)
        if not ident:
            raise ValueError("run_id must not be empty")
        params = {
            "scope": "run",
            "scope_id": ident,
            "channel": channel,
            "from": start,
            "to": end,
            "limit": limit,
            "order": order,
        }
        return self._model(RunLogPage, self._get(_LOGS, params=params))

    def artifacts(self, run_id: str) -> RunArtifacts:
        """Read the artifact a run produced (``GET /orchestrations/runs/{run_id}/artifacts``).

        Only this run's own artifact is returned, never a later run's.

        Args:
            run_id: The run to read.

        Returns:
            :class:`RunArtifacts`.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, as for :meth:`get`, and
                ``404`` (``PerceivoNotFoundError``) when the run recorded no
                artifact.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            RunArtifacts, self._get(f"{_BASE}/{segment(run_id, 'run_id')}/artifacts")
        )

    def events(self, run_id: str) -> RunEvents:
        """Read a run's execution events, in order (``GET /orchestrations/runs/{run_id}/events``).

        The list is a snapshot that the runtime rewrites as the run proceeds,
        so successive reads can differ. A run with no recorded events answers
        an empty list. Requires ``WORKLOAD_READ``; starting the run is not
        enough.

        Args:
            run_id: The run to read.

        Returns:
            :class:`RunEvents`.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an unknown run or a caller
                without ``WORKLOAD_READ``, ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``)
                when the platform answers with something that is not this run;
                nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RunEvents, self._get(f"{_BASE}/{segment(run_id, 'run_id')}/events"))

    def steps(self, run_id: str) -> RunSteps:
        """Read the per-node detail of a run (``GET /orchestrations/runs/{run_id}/steps``).

        One step per node, sorted by ``node_id``, with execution counts and
        durations. Requires ``WORKLOAD_READ``; starting the run is not enough.

        Args:
            run_id: The run to read.

        Returns:
            :class:`RunSteps`.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, as for :meth:`events`.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RunSteps, self._get(f"{_BASE}/{segment(run_id, 'run_id')}/steps"))

    def cancel(self, run_id: str) -> RunControlResult:
        """Cancel a run (``POST /orchestrations/runs/{run_id}/cancel``).

        The answer does not prove the outcome: when the platform cannot
        confirm the cancel in time it answers ``202`` with status
        ``CANCELLING``. Read the run with :meth:`get` and cancel again if it is
        not ``CANCELED``. Requires ``WORKLOAD_CONTROL`` and ``WORKLOAD_READ``,
        or being the key that started the run.

        Args:
            run_id: The run to cancel.

        Returns:
            :class:`RunControlResult` — the outcome of the control request.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller without the
                privileges, ``404`` (``PerceivoNotFoundError``) for an unknown
                or foreign run, ``409`` (``PerceivoConflictError``) for a run
                that has already finished (nothing is sent), ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform could not
                complete the request: read the run before sending the control
                again.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            RunControlResult, self._post(f"{_BASE}/{segment(run_id, 'run_id')}/cancel")
        )

    def pause(self, run_id: str) -> RunControlResult:
        """Pause a running run (``POST /orchestrations/runs/{run_id}/pause``).

        Accepted only while the run's workload is running; the answer's status
        is ``PAUSING``. A paused run keeps its compute.

        Args:
            run_id: The run to pause.

        Returns:
            :class:`RunControlResult` — the outcome of the control request.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when the workload
                is not running, and otherwise as for :meth:`cancel`.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            RunControlResult, self._post(f"{_BASE}/{segment(run_id, 'run_id')}/pause")
        )

    def resume(self, run_id: str) -> RunControlResult:
        """Resume a paused run (``POST /orchestrations/runs/{run_id}/resume``).

        Args:
            run_id: The run to resume.

        Returns:
            :class:`RunControlResult` — the outcome of the control request.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when the workload
                is not paused, ``409`` (``PerceivoConflictError``) for a run
                that has finished, including a stopped one, ``429``
                (``PerceivoRateLimitError``) when the organization may not run
                work (its execution is locked, it is over a usage limit, or it
                has no live subscription), and otherwise as for :meth:`cancel`.
                That ``429`` gives its reason as text only, with no
                ``execution_locked`` code, so it is not raised as
                ``PerceivoExecutionLockedError``. Waiting does not clear it,
                and the client does not retry it.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            RunControlResult, self._post(f"{_BASE}/{segment(run_id, 'run_id')}/resume")
        )

    def stop(self, run_id: str) -> RunControlResult:
        """Stop a run gracefully (``POST /orchestrations/runs/{run_id}/stop``).

        In-flight work is allowed to finish; the answer's status is
        ``STOPPING``. Once stopped, the run is ``CANCELED`` and cannot be
        resumed.

        Args:
            run_id: The run to stop.

        Returns:
            :class:`RunControlResult` — the outcome of the control request.

        Raises:
            ValueError: If ``run_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when the workload
                is neither running nor paused, and otherwise as for
                :meth:`cancel`.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            RunControlResult, self._post(f"{_BASE}/{segment(run_id, 'run_id')}/stop")
        )
