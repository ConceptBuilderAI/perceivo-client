"""Intelligence namespace (``client.intelligence``).

The machine-learning lifecycle of an intelligence: create, read, change and
delete it; start, stop and read its serving runtime; predict, singly and in
batches; read inference requests and prediction logs; train, evaluate,
register, promote and retire models; manage model families, traffic plans,
drift baselines and drift configuration; export, import and version it;
manage training configurations and groups; read feature views, materialize and
ingest; configure PII and prediction logging; bind service secrets; and manage
ingest triggers.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    BatchPredictionResponse,
    DriftBaselineRead,
    DriftConfig,
    EvaluationRead,
    FeatureViewRead,
    IngestResponse,
    IngestTriggerRead,
    IntelligenceExport,
    IntelligenceImportResult,
    IntelligenceMaterializeAccepted,
    IntelligenceRead,
    IntelligenceTrafficPlanResult,
    IntelligenceTrainingJobRead,
    IntelligenceTriggerExecutionRead,
    IntelligenceUpdateResult,
    LineageRestoreResult,
    ModelFamilyRead,
    ModelLifecycleResult,
    ModelPromotionResult,
    ModelRead,
    PaginatedItemsResponse,
    PiiConfig,
    PredictionLoggingConfig,
    PredictionLogRead,
    PredictionOutcomes,
    PredictionPage,
    PredictionRecord,
    PredictionResponse,
    ServiceSecretRead,
    TrainingConfigurationRead,
    TrainingGroupDetail,
    TrainingGroupMemberRead,
    TrainingGroupRead,
    TrainingJobSubmitResponse,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/intelligence"


class IntelligenceResource(BaseResource):
    """Train, serve, and manage intelligence assets.

    In the method summaries below, a path that starts with ``...`` is relative
    to ``/intelligence/{intelligence_id}``.
    """

    # -- CRUD --------------------------------------------------------------
    def list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> PaginatedItemsResponse:
        """List the organization's intelligences, newest first (``GET /intelligence``).

        ``paginate_pages`` walks this list.

        Args:
            page: Page number, 1 or more; the server default is ``1``.
            page_size: Items per page, 1 to 100; the server default is ``25``.

        Returns:
            :class:`PaginatedItemsResponse` — ``items`` (one intelligence
            record per item) and ``total``.

        Raises:
            PerceivoValidationError: For an out-of-range ``page`` or
                ``page_size`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"page": page, "page_size": page_size}
        return self._model(PaginatedItemsResponse, self._get(_BASE, params=params))

    def create(self, body: dict[str, Any]) -> IntelligenceRead:
        """Create an intelligence (``POST /intelligence``).

        Each call creates another intelligence. Nothing runs, and nothing is
        billed, until :meth:`start`.

        Args:
            body: An ``IntelligenceCreate`` object: ``name`` (3 to 100
                characters) is required; ``config`` names the services and
                compute.

        Returns:
            :class:`IntelligenceRead` — the new intelligence (``201``).

        Raises:
            PerceivoGrantError: For a key without ``INTELLIGENCE_CREATE`` on the
                organization (``403``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(IntelligenceRead, self._post(_BASE, json=body))

    def get(self, intelligence_id: str) -> IntelligenceRead:
        """Read one intelligence (``GET /intelligence/{intelligence_id}``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`IntelligenceRead`.

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
        return self._model(
            IntelligenceRead, self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}")
        )

    def update(self, intelligence_id: str, body: dict[str, Any]) -> IntelligenceUpdateResult:
        """Change an intelligence (``PATCH /intelligence/{intelligence_id}``).

        Only the fields sent change. A compute change is applied to running
        services.

        Args:
            intelligence_id: The intelligence to change.
            body: An ``IntelligenceUpdate`` object.

        Returns:
            :class:`IntelligenceUpdateResult` — the record and
            ``version_created``. Follow its ``id``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without the update privilege
                (``403``).
            PerceivoNotFoundError: For an intelligence that is absent, deleted
                or another organization's (``404``).
            PerceivoConflictError: For a locked intelligence (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceUpdateResult,
            self._patch(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}", json=body),
        )

    def delete(self, intelligence_id: str) -> None:
        """Delete an intelligence's whole lineage (``DELETE /intelligence/{intelligence_id}``).

        A soft delete, undone by :meth:`restore`. A running runtime is not
        stopped by the delete: :meth:`stop` it first, or it stays billed.

        Args:
            intelligence_id: Any version of the lineage.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without the delete privilege,
                or a repeated delete (``403``).
            PerceivoNotFoundError: For an intelligence that is absent or
                another organization's (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}")

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

    # -- training ----------------------------------------------------------
    def train(
        self, intelligence_id: str, body: dict[str, Any] | None = None
    ) -> TrainingJobSubmitResponse:
        """Start a training job (``POST .../train``).

        Training consumes compute. The job runs in the background: poll
        :meth:`get_training_job` with the returned ``id``.

        Args:
            intelligence_id: The intelligence to train.
            body: An optional ``TrainingRequest`` object. Omitted, an empty
                object is sent.

        Returns:
            :class:`TrainingJobSubmitResponse` — the accepted job (``202``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_TRAIN`` and a
                direct grant on the intelligence (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingJobSubmitResponse,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/train", json=body or {}
            ),
        )

    # -- evaluation & models ----------------------------------------------
    def evaluate(self, intelligence_id: str, body: dict[str, Any] | None = None) -> EvaluationRead:
        """Evaluate the intelligence's models (``POST .../evaluate``).

        Evaluation consumes compute.

        Args:
            intelligence_id: The intelligence to evaluate.
            body: An optional ``EvaluateRequest`` object. Omitted, an empty
                object is sent.

        Returns:
            :class:`EvaluationRead` — the evaluation record.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            EvaluationRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/evaluate", json=body or {}
            ),
        )

    def list_models(self, intelligence_id: str) -> list[ModelRead]:
        """List the intelligence's models (``GET .../models``).

        Every model comes in one response; the list takes no filters.

        Args:
            intelligence_id: The intelligence whose models are listed.

        Returns:
            ``list[ModelRead]``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ModelRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models"),
        )

    def get_model(self, intelligence_id: str, model_id: str) -> ModelRead:
        """Read one model (``GET .../models/{model_id}``).

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to read.

        Returns:
            :class:`ModelRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For a model or intelligence your
                organization cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}"
            ),
        )

    def promote_model(
        self, intelligence_id: str, model_id: str, body: dict[str, Any] | None = None
    ) -> ModelPromotionResult:
        """Promote a model, for example to canary or champion (``POST .../models/{model_id}/promote``).

        Promotion deploys serving capacity for the model.

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to promote.
            body: An optional ``PromoteModelRequest`` object (``target_stage``).
                Omitted, an empty object is sent.

        Returns:
            :class:`ModelPromotionResult`.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without the model-management
                privilege (``403``).
            PerceivoNotFoundError: For a model or intelligence your
                organization cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelPromotionResult,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}/promote",
                json=body or {},
            ),
        )

    def retire_model(self, intelligence_id: str, model_id: str) -> ModelLifecycleResult:
        """Retire a model (``POST .../models/{model_id}/retire``).

        No body is sent.

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to retire.

        Returns:
            :class:`ModelLifecycleResult`.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: Without a required privilege (``403``): ``INTELLIGENCE_READ``
                on the intelligence and ``INTELLIGENCE_MANAGE_MODELS``.
            PerceivoNotFoundError: For a model that does not exist or does not belong to
                the named intelligence; nothing is retired (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelLifecycleResult,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}/retire"
            ),
        )

    # -- drift baselines ---------------------------------------------------
    def list_drift_baselines(
        self,
        intelligence_id: str,
        *,
        include_inactive: bool | None = None,
        model_family_id: str | None = None,
    ) -> list[DriftBaselineRead]:
        """List drift baselines (``GET .../drift/baselines``).

        Args:
            intelligence_id: The intelligence whose baselines are listed.
            include_inactive: ``True`` also lists inactive baselines. Omitted,
                the parameter is not sent.
            model_family_id: Only baselines of this model family. Omitted,
                every family's are listed.

        Returns:
            ``list[DriftBaselineRead]``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"include_inactive": include_inactive, "model_family_id": model_family_id}
        return self._list(
            DriftBaselineRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/baselines",
                params=params,
            ),
        )

    def create_drift_baseline(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> DriftBaselineRead:
        """Create a drift baseline (``POST .../drift/baselines``).

        Args:
            intelligence_id: The intelligence to create the baseline on.
            body: A ``CreateDriftBaselineRequest`` object.

        Returns:
            :class:`DriftBaselineRead` — the baseline as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_UPDATE``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DriftBaselineRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/baselines", json=body
            ),
        )

    def get_drift_baseline(self, intelligence_id: str, baseline_id: str) -> DriftBaselineRead:
        """One drift baseline (``GET .../drift/baselines/{baseline_id}``).

        Args:
            intelligence_id: The intelligence that holds the baseline.
            baseline_id: The baseline to read.

        Returns:
            :class:`DriftBaselineRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``baseline_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a key without ``INTELLIGENCE_READ``; ``404``
                (``PerceivoNotFoundError``) for an intelligence your organization cannot see;
                ``422`` (``PerceivoValidationError``) for a malformed request; and ``502``
                (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DriftBaselineRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/baselines/{segment(baseline_id, 'baseline_id')}"
            ),
        )

    def activate_drift_baseline(self, intelligence_id: str, baseline_id: str) -> DriftBaselineRead:
        """Make a baseline the one drift is measured against.

        Calls ``POST .../drift/baselines/{baseline_id}/activate``. No body is
        sent.

        Args:
            intelligence_id: The intelligence that holds the baseline.
            baseline_id: The baseline to activate.

        Returns:
            :class:`DriftBaselineRead` — the baseline, now active.

        Raises:
            ValueError: If ``intelligence_id`` or ``baseline_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a key with only ``INTELLIGENCE_READ`` (``INTELLIGENCE_UPDATE``
                is required); ``404`` (``PerceivoNotFoundError``) for an intelligence your
                organization cannot see; ``422`` (``PerceivoValidationError``) for a malformed
                request; and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DriftBaselineRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/baselines/{segment(baseline_id, 'baseline_id')}/activate"
            ),
        )

    def delete_drift_baseline(self, intelligence_id: str, baseline_id: str) -> None:
        """Delete a drift baseline (``DELETE .../drift/baselines/{baseline_id}``, ``204``).

        Args:
            intelligence_id: The intelligence that holds the baseline.
            baseline_id: The baseline to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` or ``baseline_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a key with only ``INTELLIGENCE_READ`` (``INTELLIGENCE_UPDATE``
                is required); ``404`` (``PerceivoNotFoundError``) for an intelligence your
                organization cannot see; ``422`` (``PerceivoValidationError``) for a malformed
                request; and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/baselines/{segment(baseline_id, 'baseline_id')}"
        )

    def get_drift_config(self, intelligence_id: str) -> DriftConfig:
        """The drift-monitoring configuration (``GET .../drift/config``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`DriftConfig`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a key without ``INTELLIGENCE_READ``; ``404``
                (``PerceivoNotFoundError``) for an intelligence your organization cannot see;
                ``422`` (``PerceivoValidationError``) for a malformed request; and ``502``
                (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DriftConfig,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/config"),
        )

    def replace_drift_config(self, intelligence_id: str, body: dict[str, Any]) -> DriftConfig:
        """Replace the drift-monitoring configuration (``PUT .../drift/config``).

        Args:
            intelligence_id: The intelligence to configure.
            body: A ``DriftConfig`` that replaces the whole configuration; ``webhook_url`` must be
                null or omitted. For drift alerts, subscribe a webhook to ``drift.detected``.

        Returns:
            :class:`DriftConfig` — the configuration as stored.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) for a key with only
                ``INTELLIGENCE_READ`` (``INTELLIGENCE_UPDATE`` is required); ``404``
                (``PerceivoNotFoundError``) for an intelligence your organization cannot see; ``422``
                (``PerceivoValidationError``) for a threshold outside 0 to 1 or a non-null ``webhook_url``,
                changing nothing; and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DriftConfig,
            self._put(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/drift/config", json=body
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

    # -- training jobs and model registration ------------------------------
    def get_training_job(self, intelligence_id: str, job_id: str) -> IntelligenceTrainingJobRead:
        """One training job and its runs (``GET .../training-jobs/{job_id}``).

        The ``id`` of the :class:`TrainingJobSubmitResponse` that :meth:`train`
        returns is the ``job_id`` here.

        Args:
            intelligence_id: The intelligence that ran the job.
            job_id: The training job to read.

        Returns:
            :class:`IntelligenceTrainingJobRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``job_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a job of another intelligence or one that does not
                exist, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceTrainingJobRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-jobs/{segment(job_id, 'job_id')}"
            ),
        )

    def register_model(self, intelligence_id: str, body: dict[str, Any]) -> ModelRead:
        """Register a model on the intelligence (``POST .../models``).

        Args:
            intelligence_id: The intelligence to register the model on.
            body: A ``ModelRegisterRequest`` object, sent as the JSON body.

        Returns:
            :class:`ModelRead` — the registered model (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelRead,
            self._post(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models", json=body),
        )

    def delete_model(self, intelligence_id: str, model_id: str) -> None:
        """Delete a model (``DELETE .../models/{model_id}``, ``204``).

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a model that does not belong to this intelligence or
                does not exist; ``409`` (``PerceivoConflictError``) for a model still referenced by
                a traffic role, a deployment or an evaluation (the body names the constraint; there
                is no force); and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}"
        )

    # -- model families ----------------------------------------------------
    def list_model_families(
        self, intelligence_id: str, *, active_only: bool | None = None
    ) -> list[ModelFamilyRead]:
        """List model families (``GET .../model-families``).

        Args:
            intelligence_id: The intelligence whose families are listed.
            active_only: ``True`` lists only active families. Omitted, the
                parameter is not sent and the server default, ``false``,
                applies.

        Returns:
            ``list[ModelFamilyRead]``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ModelFamilyRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families",
                params={"active_only": active_only},
            ),
        )

    def create_model_family(self, intelligence_id: str, body: dict[str, Any]) -> ModelFamilyRead:
        """Create a model family (``POST .../model-families``).

        Args:
            intelligence_id: The intelligence to create the family on.
            body: A ``ModelFamilyCreateRequest`` object, sent as the JSON
                body.

        Returns:
            :class:`ModelFamilyRead` — the family as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without ``INTELLIGENCE_MANAGE_MODELS``; ``404``
                (``PerceivoNotFoundError``) for an intelligence that does not exist or belongs to
                another organization; and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families", json=body
            ),
        )

    def get_model_family(self, intelligence_id: str, family_id: str) -> ModelFamilyRead:
        """One model family (``GET .../model-families/{family_id}``).

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to read.

        Returns:
            :class:`ModelFamilyRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}"
            ),
        )

    def update_model_family(
        self, intelligence_id: str, family_id: str, body: dict[str, Any]
    ) -> ModelFamilyRead:
        """Update a model family (``PATCH .../model-families/{family_id}``).

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to update.
            body: A ``ModelFamilyUpdateRequest`` object, sent as the JSON
                body. Fields it omits are left unchanged.

        Returns:
            :class:`ModelFamilyRead` — the family after the update.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without ``INTELLIGENCE_MANAGE_MODELS``, or
                without ``INTELLIGENCE_MANAGE_TRAFFIC`` when the body sets ``traffic_percent`` or
                ``is_active``; ``404`` (``PerceivoNotFoundError``) for an intelligence that does not
                exist or belongs to another organization; and ``422`` (``PerceivoValidationError``)
                for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}",
                json=body,
            ),
        )

    def activate_model_family(self, intelligence_id: str, family_id: str) -> ModelFamilyRead:
        """Activate a model family (``POST .../model-families/{family_id}/activate``).

        No body is sent.

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to activate.

        Returns:
            :class:`ModelFamilyRead` — the family, now active.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without ``INTELLIGENCE_MANAGE_MODELS``; ``404``
                (``PerceivoNotFoundError``) for an intelligence that does not exist or belongs to
                another organization; and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}/activate"
            ),
        )

    def deactivate_model_family(self, intelligence_id: str, family_id: str) -> dict[str, Any]:
        """Deactivate a model family (``DELETE .../model-families/{family_id}``).

        The family is marked inactive and its traffic set to zero; nothing is
        destroyed. Needs ``INTELLIGENCE_MANAGE_MODELS`` and ``INTELLIGENCE_MANAGE_TRAFFIC``.

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to deactivate.

        Returns:
            ``dict[str, Any]`` — ``{"message": ...}``: ``Model family
            deactivated``, or ``Family already inactive`` for a repeat.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller missing ``INTELLIGENCE_MANAGE_MODELS`` or
                ``INTELLIGENCE_MANAGE_TRAFFIC`` (nothing is deactivated); ``404``
                (``PerceivoNotFoundError``) for an intelligence that does not exist or belongs to
                another organization; and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}"
        )

    # -- transfer, lineage and versions ------------------------------------
    def export_bundle(self, intelligence_id: str) -> IntelligenceExport:
        """Export an intelligence as a portable document (``GET .../export``).

        Args:
            intelligence_id: The intelligence to export.

        Returns:
            :class:`IntelligenceExport` — the document :meth:`import_bundle`
            accepts.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceExport,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/export"),
        )

    def import_bundle(self, body: dict[str, Any]) -> IntelligenceImportResult:
        """Create an intelligence from an export document (``POST /intelligence/import``).

        The request body is limited to 16 MiB (``413`` above it).

        Args:
            body: The document :meth:`export_bundle` returned, sent as the
                JSON body.

        Returns:
            :class:`IntelligenceImportResult` (``201``).

        Raises:
            PerceivoAPIError: On an error response. The route declares ``413`` for a request body
                over 16 MiB, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(IntelligenceImportResult, self._post(f"{_BASE}/import", json=body))

    def get_lineage(self, intelligence_id: str) -> AssetLineageRead:
        """Read the intelligence's version lineage, newest first (``GET .../lineage``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`AssetLineageRead`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) or ``404`` (``PerceivoNotFoundError``) for an
                identifier that names no intelligence the caller can read (``INTELLIGENCE_READ`` is
                required); ``422`` (``PerceivoValidationError``) for a malformed request; and
                ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetLineageRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/lineage"),
        )

    def delete_version(self, intelligence_id: str, version_id: str) -> None:
        """Soft-delete one version of the lineage (``DELETE .../versions/{version_id}``).

        Args:
            intelligence_id: The intelligence whose lineage holds the version.
            version_id: The version to soft-delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` or ``version_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without the privilege, checked before
                anything is read; ``404`` (``PerceivoNotFoundError``) for a version that is not live
                or not in this lineage; ``422`` (``PerceivoValidationError``) for a malformed
                request; and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/versions/{segment(version_id, 'version_id')}"
        )

    def restore(self, intelligence_id: str) -> LineageRestoreResult:
        """Undo the lineage's most recent deletion (``POST .../restore``).

        No body is sent.

        Args:
            intelligence_id: The intelligence whose lineage is restored.

        Returns:
            :class:`LineageRestoreResult`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a version the caller cannot restore
                (``INTELLIGENCE_UPDATE`` is required on every version, and the whole call is refused);
                ``404`` (``PerceivoNotFoundError``) for a lineage with nothing deleted, or one the
                caller cannot see; ``422`` (``PerceivoValidationError``) for a malformed request;
                and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LineageRestoreResult,
            self._post(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/restore"),
        )

    # -- training configurations -------------------------------------------
    def list_training_configurations(
        self, intelligence_id: str, *, family_id: str | None = None
    ) -> list[TrainingConfigurationRead]:
        """List training configurations (``GET .../training-configurations``).

        ``family_id`` narrows the list to one model family. The body is a bare
        array and the route takes no page parameters.

        Args:
            intelligence_id: The intelligence whose configurations are listed.
            family_id: Only configurations of this model family. Omitted,
                every family's are listed.

        Returns:
            ``list[TrainingConfigurationRead]`` — every configuration, in one
            response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            TrainingConfigurationRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations",
                params={"family_id": family_id},
            ),
        )

    def create_training_configuration(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> TrainingConfigurationRead:
        """Create a training configuration (``POST .../training-configurations``).

        Args:
            intelligence_id: The intelligence to create the configuration on.
            body: A ``TrainingConfigurationCreate`` object, sent as the JSON
                body.

        Returns:
            :class:`TrainingConfigurationRead` — the configuration as stored
            (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingConfigurationRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations",
                json=body,
            ),
        )

    def get_training_configuration(
        self, intelligence_id: str, config_id: str
    ) -> TrainingConfigurationRead:
        """One training configuration (``GET .../training-configurations/{config_id}``).

        Args:
            intelligence_id: The intelligence that holds the configuration.
            config_id: The configuration to read.

        Returns:
            :class:`TrainingConfigurationRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``config_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingConfigurationRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations/{segment(config_id, 'config_id')}"
            ),
        )

    def update_training_configuration(
        self, intelligence_id: str, config_id: str, body: dict[str, Any]
    ) -> TrainingConfigurationRead:
        """Update a training configuration (``PATCH .../training-configurations/{config_id}``).

        Only the fields sent are changed.

        Args:
            intelligence_id: The intelligence that holds the configuration.
            config_id: The configuration to update.
            body: A ``TrainingConfigurationUpdate`` object, sent as the JSON
                body.

        Returns:
            :class:`TrainingConfigurationRead` — the configuration after the
            update.

        Raises:
            ValueError: If ``intelligence_id`` or ``config_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingConfigurationRead,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations/{segment(config_id, 'config_id')}",
                json=body,
            ),
        )

    def delete_training_configuration(self, intelligence_id: str, config_id: str) -> dict[str, Any]:
        """Delete a training configuration (``DELETE .../training-configurations/{config_id}``).

        A configuration that is a member of a training group is removed from it.

        Args:
            intelligence_id: The intelligence that holds the configuration.
            config_id: The configuration to delete.

        Returns:
            ``dict[str, Any]`` — ``{"message": "Training configuration
            deleted"}``.

        Raises:
            ValueError: If ``intelligence_id`` or ``config_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations/{segment(config_id, 'config_id')}"
        )

    # -- training groups ---------------------------------------------------
    def list_training_groups(
        self, intelligence_id: str, *, include_members: bool | None = None
    ) -> list[TrainingGroupRead]:
        """List training groups (``GET .../training-groups``).

        ``include_members`` asks for each group's members. The body is a bare
        array and the route takes no page parameters.

        Args:
            intelligence_id: The intelligence whose groups are listed.
            include_members: ``True`` includes each group's members.
                Omitted, the parameter is not sent and the server default,
                ``false``, applies.

        Returns:
            ``list[TrainingGroupRead]`` — every group, in one response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            TrainingGroupRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups",
                params={"include_members": include_members},
            ),
        )

    def create_training_group(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> TrainingGroupDetail:
        """Create a training group (``POST .../training-groups``).

        Args:
            intelligence_id: The intelligence to create the group on.
            body: A ``TrainingGroupCreate`` object, sent as the JSON body.

        Returns:
            :class:`TrainingGroupDetail` — the group as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupDetail,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups", json=body
            ),
        )

    def get_training_group(self, intelligence_id: str, group_id: str) -> TrainingGroupDetail:
        """One training group and its members (``GET .../training-groups/{group_id}``).

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to read.

        Returns:
            :class:`TrainingGroupDetail`.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupDetail,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}"
            ),
        )

    def update_training_group(
        self, intelligence_id: str, group_id: str, body: dict[str, Any]
    ) -> TrainingGroupDetail:
        """Update a training group (``PATCH .../training-groups/{group_id}``).

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to update.
            body: A ``TrainingGroupUpdate`` object, sent as the JSON body.

        Returns:
            :class:`TrainingGroupDetail` — the group after the update.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupDetail,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}",
                json=body,
            ),
        )

    def delete_training_group(self, intelligence_id: str, group_id: str) -> dict[str, Any]:
        """Delete a training group (``DELETE .../training-groups/{group_id}``).

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to delete.

        Returns:
            ``dict[str, Any]`` — ``{"message": "Training group deleted"}``.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}"
        )

    def replace_training_group_member(
        self, intelligence_id: str, group_id: str, member_id: str, body: dict[str, Any]
    ) -> TrainingGroupMemberRead:
        """Put a configuration in a group.

        Calls ``PUT .../training-groups/{group_id}/members/{member_id}``.
        Answers ``201`` for a new member and ``200`` for a replaced one; both
        carry a ``TrainingGroupMemberRead``.

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to put the member in.
            member_id: The member to create or replace.
            body: A ``TrainingGroupMemberReplace`` object, sent as the JSON
                body. The model family is taken from the configuration it
                names and cannot be set.

        Returns:
            :class:`TrainingGroupMemberRead` — the member as stored.

        Raises:
            ValueError: If ``intelligence_id``, ``group_id`` or ``member_id``
                is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a group or configuration that does not exist under
                this intelligence, or belongs to another organization; ``409``
                (``PerceivoConflictError``) for a second membership for a model family the group
                already covers; and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupMemberRead,
            self._put(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}/members/{segment(member_id, 'member_id')}",
                json=body,
            ),
        )

    def remove_training_group_member(
        self, intelligence_id: str, group_id: str, member_id: str
    ) -> dict[str, Any]:
        """Remove a member from a group.

        Calls ``DELETE .../training-groups/{group_id}/members/{member_id}``.

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to remove the member from.
            member_id: The member to remove.

        Returns:
            ``dict[str, Any]`` — ``{"message": "Member removed from training
            group"}``.

        Raises:
            ValueError: If ``intelligence_id``, ``group_id`` or ``member_id``
                is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}/members/{segment(member_id, 'member_id')}"
        )

    def run_training_group(self, intelligence_id: str, group_id: str) -> dict[str, Any]:
        """Train every configuration in a group (``POST .../training-groups/{group_id}/run``).

        Submits one training job per member, as one batch. Training consumes
        compute. No body is sent. Not safe to retry blindly: a member that
        fails answers ``500`` after earlier members' jobs were already queued.

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to run.

        Returns:
            ``dict[str, Any]`` — ``message``, ``job_ids``, ``run_count``,
            ``group_id`` and ``group_name``. A batch that could not be started
            still answers here, with a ``message`` beginning ``Training batch
            was not started:``; read it before assuming jobs exist.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._post(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}/run"
        )

    # -- feature views, materialization and ingest -------------------------
    def list_feature_views(self, intelligence_id: str) -> list[FeatureViewRead]:
        """List the intelligence's feature views (``GET .../features``).

        A feature service that is still starting answers an empty list.

        Args:
            intelligence_id: The intelligence whose feature views are listed.

        Returns:
            ``list[FeatureViewRead]`` — read from the body's ``feature_views``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        body = self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/features")
        views = body.get("feature_views") if isinstance(body, dict) else body
        return self._list(FeatureViewRead, views or [])

    def get_feature_view(self, intelligence_id: str, view_name: str) -> FeatureViewRead | None:
        """Read one feature view (``GET .../features/{view_name}``).

        Args:
            intelligence_id: The intelligence that holds the feature view.
            view_name: The feature view's name.

        Returns:
            :class:`FeatureViewRead`, or ``None`` while the feature service is
            starting.

        Raises:
            ValueError: If ``intelligence_id`` or ``view_name`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoServerError: For another
                feature-service failure (``500``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            FeatureViewRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/features/{segment(view_name, 'view_name')}"
            ),
        )

    def sample_feature_view(
        self, intelligence_id: str, view_name: str, *, limit: int | None = None
    ) -> dict[str, Any]:
        """Read rows of one feature view from the offline store (``GET .../features/{view_name}/sample``).

        Values of features marked as PII are not masked here.

        Args:
            intelligence_id: The intelligence that holds the feature view.
            view_name: The feature view's name.
            limit: The most rows to return, 1 to 1000. Omitted, every row of
                the view is returned, which can be very large.

        Returns:
            ``dict[str, Any]`` — ``feature_view``, ``count``, ``results`` (the
            rows) and ``metadata``.

        Raises:
            ValueError: If ``intelligence_id`` or ``view_name`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoValidationError: For a ``limit`` outside 1 to 1000
                (``422``).
            PerceivoServerError: For a failed
                read (``500``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._get(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/features/{segment(view_name, 'view_name')}/sample",
            params={"limit": limit},
        )

    def materialize(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> IntelligenceMaterializeAccepted:
        """Load feature data into the online store (``POST .../materialize``).

        ``body`` is an ``IntelligenceMaterializeRequest`` (``scope``,
        ``feature_views``, ``start_date``, ``end_date``). The request is
        accepted and runs in the background. Materialization consumes compute.

        Args:
            intelligence_id: The intelligence to materialize.
            body: An ``IntelligenceMaterializeRequest``, sent as the JSON body.

        Returns:
            :class:`IntelligenceMaterializeAccepted` — the acceptance, not the
            finished load.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for an intelligence that is not yours, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceMaterializeAccepted,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/materialize", json=body
            ),
        )

    def ingest(self, intelligence_id: str, body: dict[str, Any]) -> IngestResponse:
        """Run the intelligence's ingest (``POST .../execute/ingest``).

        ``body`` is an ``IngestRequest`` (``config``). Ingest consumes compute.

        Args:
            intelligence_id: The intelligence to ingest into.
            body: An ``IngestRequest``, sent as the JSON body.

        Returns:
            :class:`IngestResponse`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IngestResponse,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/execute/ingest", json=body
            ),
        )

    # -- PII and prediction-logging configuration --------------------------
    def get_pii_config(self, intelligence_id: str) -> PiiConfig:
        """The features treated as PII (``GET .../config/pii``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`PiiConfig`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PiiConfig,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/config/pii"),
        )

    def replace_pii_config(self, intelligence_id: str, body: dict[str, Any]) -> PiiConfig:
        """Replace the PII configuration (``PUT .../config/pii``).

        Args:
            intelligence_id: The intelligence to configure.
            body: A ``PiiConfig`` object, sent as the JSON body. It replaces
                the whole configuration.

        Returns:
            :class:`PiiConfig` — the configuration as stored.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PiiConfig,
            self._put(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/config/pii", json=body
            ),
        )

    def get_prediction_logging_config(self, intelligence_id: str) -> PredictionLoggingConfig:
        """Prediction-log sampling and retention (``GET .../config/prediction-logging``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`PredictionLoggingConfig`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PredictionLoggingConfig,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/config/prediction-logging"
            ),
        )

    def replace_prediction_logging_config(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> PredictionLoggingConfig:
        """Replace prediction-log sampling and retention (``PUT .../config/prediction-logging``).

        ``body`` is a ``PredictionLoggingConfigWrite``. Retained logs are
        billed storage.

        Args:
            intelligence_id: The intelligence to configure.
            body: A ``PredictionLoggingConfigWrite``, sent as the JSON body.

        Returns:
            :class:`PredictionLoggingConfig` — the configuration as stored.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PredictionLoggingConfig,
            self._put(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/config/prediction-logging",
                json=body,
            ),
        )

    # -- service-secret bindings -------------------------------------------
    def list_service_secrets(self, intelligence_id: str) -> list[ServiceSecretRead]:
        """List secret bindings (``GET .../service-secrets``).

        Each binding carries its alias, service type and secret id, never the
        secret's value.

        Args:
            intelligence_id: The intelligence whose bindings are listed.

        Returns:
            ``list[ServiceSecretRead]`` — every binding, in one response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ServiceSecretRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/service-secrets"),
        )

    def attach_service_secret(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> ServiceSecretRead:
        """Bind an organization secret to one service (``POST .../service-secrets``).

        ``body`` is a ``ServiceSecretCreate`` (``service_type``, ``secret_id``,
        ``alias``). Only the secret's id travels, never its value.

        Args:
            intelligence_id: The intelligence to bind the secret to.
            body: A ``ServiceSecretCreate``, sent as the JSON body.

        Returns:
            :class:`ServiceSecretRead` — the binding as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceSecretRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/service-secrets", json=body
            ),
        )

    def detach_service_secret(self, intelligence_id: str, service_type: str, alias: str) -> None:
        """Detach a binding (``DELETE .../service-secrets/{service_type}/{alias}``, ``204``).

        The organization secret itself is kept.

        Args:
            intelligence_id: The intelligence that holds the binding.
            service_type: The service the secret is bound to.
            alias: The binding's alias.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id``, ``service_type`` or ``alias``
                is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/service-secrets/{segment(service_type, 'service_type')}/{segment(alias, 'alias')}"
        )

    # -- ingest triggers ---------------------------------------------------
    def list_triggers(self, intelligence_id: str) -> list[IngestTriggerRead]:
        """List the intelligence's ingest triggers (``GET .../triggers``).

        Args:
            intelligence_id: The intelligence whose triggers are listed.

        Returns:
            ``list[IngestTriggerRead]`` — every trigger, in one response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            IngestTriggerRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/triggers"),
        )

    def create_trigger(self, intelligence_id: str, body: dict[str, Any]) -> IngestTriggerRead:
        """Create a trigger (``POST .../triggers``).

        An intelligence holds at most one trigger of each type: a second answers
        ``409``. With ``http_enabled`` the response carries ``http_token`` once;
        it cannot be read back, so store it when you receive it.

        Args:
            intelligence_id: The intelligence to create the trigger on.
            body: An ``IngestTriggerCreate`` object, sent as the JSON body.

        Returns:
            :class:`IngestTriggerRead` — the trigger as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``409``
                (``PerceivoConflictError``) for a second trigger of a type that already exists (it
                does not replace the first), and ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IngestTriggerRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/triggers", json=body
            ),
        )

    def update_trigger(
        self, intelligence_id: str, trigger_id: str, body: dict[str, Any]
    ) -> IngestTriggerRead:
        """Update a trigger (``PATCH .../triggers/{trigger_id}``).

        As with :meth:`create_trigger`, ``http_token`` is returned once when
        ``http_enabled`` is set.

        Args:
            intelligence_id: The intelligence that holds the trigger.
            trigger_id: The trigger to update.
            body: An ``IngestTriggerUpdate`` object, sent as the JSON body.

        Returns:
            :class:`IngestTriggerRead` — the trigger after the update.

        Raises:
            ValueError: If ``intelligence_id`` or ``trigger_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IngestTriggerRead,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/triggers/{segment(trigger_id, 'trigger_id')}",
                json=body,
            ),
        )

    def delete_trigger(self, intelligence_id: str, trigger_id: str) -> None:
        """Delete a trigger and its execution history (``DELETE .../triggers/{trigger_id}``).

        Args:
            intelligence_id: The intelligence that holds the trigger.
            trigger_id: The trigger to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` or ``trigger_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/triggers/{segment(trigger_id, 'trigger_id')}"
        )

    def get_trigger_execution(
        self, intelligence_id: str, trigger_id: str, execution_id: str
    ) -> IntelligenceTriggerExecutionRead:
        """One execution of a trigger.

        Calls ``GET .../triggers/{trigger_id}/executions/{execution_id}``.

        Args:
            intelligence_id: The intelligence that holds the trigger.
            trigger_id: The trigger that ran.
            execution_id: The execution to read.

        Returns:
            :class:`IntelligenceTriggerExecutionRead`.

        Raises:
            ValueError: If ``intelligence_id``, ``trigger_id`` or
                ``execution_id`` is empty, ``.`` or ``..`` (refused before the
                request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for an execution of another trigger, a trigger of
                another intelligence, or one that does not exist, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceTriggerExecutionRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/triggers/{segment(trigger_id, 'trigger_id')}/executions/{segment(execution_id, 'execution_id')}"
            ),
        )
