"""Drift baselines and drift configuration; PII and prediction-logging configuration.

One of the mixins that make up
:class:`~perceivo_client.resources.intelligence.IntelligenceResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    DriftBaselineRead,
    DriftConfig,
    PiiConfig,
    PredictionLoggingConfig,
)
from perceivo_client.resources.intelligence._common import _BASE, _MixinBase


class _ConfigMixin(_MixinBase):
    """The ``client.intelligence`` methods this module's docstring lists."""

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
