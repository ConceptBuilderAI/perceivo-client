"""Feature views, materialization and ingest; ingest triggers.

One of the mixins that make up
:class:`~perceivo_client.resources.intelligence.IntelligenceResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    FeatureViewRead,
    IngestResponse,
    IngestTriggerRead,
    IntelligenceMaterializeAccepted,
    IntelligenceTriggerExecutionRead,
)
from perceivo_client.resources.intelligence._common import _BASE, _MixinBase


class _FeaturesMixin(_MixinBase):
    """The ``client.intelligence`` methods this module's docstring lists."""

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
