"""Predict, singly and in batches; the serving runtime and traffic plans; inference requests and prediction logs.

One of the mixins that make up
:class:`~perceivo_client.resources.intelligence.IntelligenceResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    BatchPredictionResponse,
    IntelligenceTrafficPlanResult,
    PredictionLogRead,
    PredictionOutcomes,
    PredictionPage,
    PredictionRecord,
    PredictionResponse,
)
from perceivo_client.resources.intelligence._common import _BASE, _MixinBase


class _ServingMixin(_MixinBase):
    """The ``client.intelligence`` methods this module's docstring lists."""

    # -- inference ---------------------------------------------------------
    def predict(self, intelligence_id: str, body: dict[str, Any]) -> PredictionResponse:
        """Make one prediction (``POST .../inference/predict``).

        The intelligence must be running with a promoted champion model. Each
        call runs the model and is billed; a repeat runs it again. No
        inference-request record is written.

        Args:
            intelligence_id: The intelligence to predict with.
            body: ``{"features": {...}, "metadata": {...}}``: ``features`` is
                the model input and ``metadata`` optional request context.

        Returns:
            :class:`PredictionResponse` — ``prediction``, ``correlation_id``,
            ``model_id`` and ``metadata``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_PREDICT`` on
                the intelligence (``403``).
            PerceivoNotFoundError: For a running intelligence with no inference
                endpoint (``404``).
            PerceivoServerError: When the inference service is unreachable
                (``502``) or refuses for a backlog (``503``).
            PerceivoAPIError: On any other error response, including ``400``
                for an intelligence that is not running.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PredictionResponse,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/predict",
                json=body,
            ),
        )

    def predict_batch(self, intelligence_id: str, body: dict[str, Any]) -> BatchPredictionResponse:
        """Make up to 500 predictions in one call (``POST .../inference/predict/batch``).

        All or nothing: the first input that fails cancels the rest and the
        call fails. The answer (``202``) is the complete result set; there is
        nothing to poll. The API stops waiting after 30 s while the batch keeps
        running, so keep a batch small enough to finish within that. Each input
        is billed.

        Args:
            intelligence_id: The intelligence to predict with.
            body: A batch envelope: ``inputs`` (1 to 500 items, each with
                ``features`` and an optional ``correlation_id``), and optionally
                ``max_concurrency`` (1 to 100, default 10) and ``timeout_s``
                (default 60, at most 300).

        Returns:
            :class:`BatchPredictionResponse` — ``batch_id``,
            ``prediction_ids`` and one item per input, in request order. A
            ``prediction_ids`` entry is not an inference-request id.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_PREDICT`` on
                the intelligence (``403``).
            PerceivoValidationError: For a body outside the limits above
                (``422``).
            PerceivoServerError: When an input failed (``502``, with
                ``details`` naming it), the batch ran past the API's wait
                (``503``) or past ``timeout_s`` (``504``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BatchPredictionResponse,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/predict/batch",
                json=body,
            ),
        )

    # -- serving runtime ---------------------------------------------------
    def start(self, intelligence_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Start the serving runtime (``POST .../start``).

        Deploys the intelligence's services and answers once they are deployed,
        typically after about 90 seconds; from then the runtime is billed. That
        is longer than the client's default 30 s timeout, so construct the
        client with ``timeout=130`` for a start. If no answer arrives, read
        :meth:`get_status` instead of starting again: a second start while the
        first is in progress is refused.

        Args:
            intelligence_id: The intelligence to start.
            body: An optional ``StartIntelligenceRequest`` object.
                ``force_restart=True`` stops a running runtime and starts it
                again. Omitted, an empty object is sent.

        Returns:
            ``dict[str, Any]`` — ``status`` (the runtime status, normally
            ``RUNNING``), ``message`` and ``job_ids``. It is not the
            intelligence record.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ`` and
                ``INTELLIGENCE_START_STOP``, or a suspended organization (``403``).
            PerceivoNotFoundError: For an intelligence that is absent, deleted
                or another organization's (``404``).
            PerceivoConflictError: For a runtime that is running (without
                ``force_restart``) or still starting (``409``).
            PerceivoExecutionLockedError: For an organization whose execution
                is locked (``429``).
            PerceivoServerError: When the deployment failed (``500``), or no
                answer came in time (``502``, ``504``); the start may still
                finish, so read :meth:`get_status`.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached, or the
                client's timeout passed while the start continues.
        """
        return self._post(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/start", json=body or {}
        )

    def stop(self, intelligence_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Stop the serving runtime (``POST .../stop``).

        Removes the intelligence's services; billing for the runtime ends.
        Safe to repeat.

        Args:
            intelligence_id: The intelligence to stop.
            body: An optional ``StopIntelligenceRequest`` object: ``graceful``
                (default ``true``) and ``timeout_seconds`` (0 to 300, default
                30). Omitted, an empty object is sent.

        Returns:
            ``dict[str, Any]`` — the stopped runtime record: ``id`` (the
            runtime's id, not the intelligence's), ``intelligence_id``,
            ``organization_id``, ``status`` (``STOPPED``), ``started_at``,
            ``stopped_at``, ``service_endpoints``, ``error_message``,
            ``created_at`` and ``updated_at``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ`` and
                ``INTELLIGENCE_START_STOP`` (``403``).
            PerceivoNotFoundError: For an intelligence that was never started,
                or is absent or another organization's (``404``).
            PerceivoValidationError: For ``timeout_seconds`` outside 0 to 300
                (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._post(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/stop", json=body or {}
        )

    def get_status(self, intelligence_id: str) -> dict[str, Any]:
        """Read the intelligence, its runtime, services and models (``GET .../status``).

        The platform's record, not a live check of the cluster.

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            ``dict[str, Any]`` — ``intelligence`` (the intelligence record;
            ``intelligence["status"]`` is the state to wait on), ``runtime``
            (the latest runtime record, or ``None`` if never started),
            ``services`` (one entry per configured service) and ``models``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence that is absent, deleted
                or another organization's (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/status")

    def apply_traffic_plan(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> IntelligenceTrafficPlanResult:
        """Set the traffic split across model families (``POST .../traffic-plan``).

        Args:
            intelligence_id: The intelligence whose traffic is split.
            body: An ``IntelligenceTrafficPlanApply`` object, sent as the JSON
                body. Every family and model it names must belong to this
                intelligence.

        Returns:
            :class:`IntelligenceTrafficPlanResult`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a family or model in the plan that does not belong
                to this intelligence or does not exist (nothing is applied); ``409``
                (``PerceivoConflictError``) for a plan sent while a promotion freeze is active (body
                ``{"error":"promotion_freeze_active"}``); and ``422`` (``PerceivoValidationError``)
                for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceTrafficPlanResult,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/traffic-plan", json=body
            ),
        )

    # -- inference requests and prediction logs ---------------------------
    def list_inference_requests(
        self,
        intelligence_id: str,
        *,
        status: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> PredictionPage:
        """List stored inference requests, newest first (``GET .../inference/requests``).

        The page is the ``data``, ``page``, ``page_size``, ``total``, ``next``
        envelope, so ``paginate_pages`` does not walk it: pass ``page=n`` until
        ``next`` is ``None``. ``next`` is a path without scheme or host. An
        intelligence your organization does not own answers an empty page.

        Args:
            intelligence_id: The intelligence whose requests are listed.
            status: Only requests in this status. Omitted, every status.
            page: Page number; the server default is ``1``.
            page_size: Requests per page, at most 200; the server default is
                ``50``.

        Returns:
            :class:`PredictionPage` — one page of requests.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoValidationError: For a malformed query, including a
                ``page_size`` above 200 (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"status": status, "page": page, "page_size": page_size}
        return self._model(
            PredictionPage,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/requests",
                params=params,
            ),
        )

    def get_inference_request(self, intelligence_id: str, request_id: str) -> PredictionRecord:
        """Read one stored inference request (``GET .../inference/requests/{request_id}``).

        The poll target of an asynchronous prediction: while it is in flight
        the API sends ``Retry-After``. A ``prediction_ids`` entry of
        :meth:`predict_batch` is not a request id and is refused.

        Args:
            intelligence_id: The intelligence that served the request.
            request_id: The inference request to read (a UUID).

        Returns:
            :class:`PredictionRecord`.

        Raises:
            ValueError: If ``intelligence_id`` or ``request_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoNotFoundError: For a request that never existed, has
                expired, or belongs to another intelligence or organization
                (``404``).
            PerceivoValidationError: For an id that is not a UUID (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PredictionRecord,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/requests/{segment(request_id, 'request_id')}"
            ),
        )

    def get_inference_request_artifact(self, intelligence_id: str, request_id: str) -> bytes:
        """Download an inference request's artifact (``GET .../inference/requests/{request_id}/artifact``).

        Args:
            intelligence_id: The intelligence that served the request.
            request_id: The inference request whose artifact is downloaded.

        Returns:
            ``bytes`` — the response body exactly as received (empty for an
            empty response).

        Raises:
            ValueError: If ``intelligence_id`` or ``request_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoNotFoundError: For a request with no artifact, or one that
                is not yours or does not exist (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        response = self._t.request(
            "GET",
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/requests/{segment(request_id, 'request_id')}/artifact",
        )
        return response.content

    def list_predictions(
        self,
        intelligence_id: str,
        *,
        model_id: str | None = None,
        served_by: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> list[PredictionLogRead]:
        """List the logs of served predictions (``GET .../inference/predictions``).

        The body is a bare array, so ``paginate_pages`` does not walk it: pass
        ``page=n`` until a page comes back short.

        Args:
            intelligence_id: The intelligence whose predictions are listed.
            model_id: Only predictions served by this model.
            served_by: Only predictions served in this role.
            start_date: Earliest prediction time.
            end_date: Latest prediction time.
            page: Page number; the server default is ``1``.
            page_size: Logs per page; the server default is ``25``.

        Returns:
            ``list[PredictionLogRead]`` — one page of prediction logs.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_VIEW_LOGS``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "model_id": model_id,
            "served_by": served_by,
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "page_size": page_size,
        }
        return self._list(
            PredictionLogRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/predictions",
                params=params,
            ),
        )

    def list_prediction_outcomes(
        self, intelligence_id: str, prediction_id: str, *, prediction_time: str | None = None
    ) -> PredictionOutcomes:
        """List the outcome events of one prediction.

        Calls ``GET .../inference/predictions/{prediction_id}/outcomes``.

        Args:
            intelligence_id: The intelligence that served the prediction.
            prediction_id: The prediction whose outcomes are listed.
            prediction_time: When the prediction was made; narrows the
                search. Omitted, the parameter is not sent.

        Returns:
            :class:`PredictionOutcomes`.

        Raises:
            ValueError: If ``intelligence_id`` or ``prediction_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"prediction_time": prediction_time}
        return self._model(
            PredictionOutcomes,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/inference/predictions/{segment(prediction_id, 'prediction_id')}/outcomes",
                params=params,
            ),
        )
