"""Alerts namespace (``client.alerts``): the alerts raised for the calling key.

Read fired alerts and acknowledge or resolve them. The rules that raise alerts
are managed on ``client.alert_rules`` and the channels they notify on
``client.alert_channels``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AlertListResponse,
    AlertRead,
    AlertSummary,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/alerts"


class AlertsResource(BaseResource):
    """List, summarize, read, acknowledge and resolve alerts."""

    def list(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        severity: str | None = None,
        status: str | None = None,
        q: str | None = None,
    ) -> AlertListResponse:
        """One page of the alerts addressed to the calling key (``GET /alerts``).

        Newest first. Only alerts whose recipients include the key are listed,
        so a key normally sees the alerts raised by rules it created. Increase
        ``page`` until ``has_more`` is false; an alert raised between two
        requests shifts the window, so deduplicate on ``id`` when walking.

        Args:
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Alerts per page, ``1`` to ``100``. Omitted, the API uses
                ``25``.
            severity: Sent as ``filter[severity]``: ``warning`` or
                ``critical``. Any other value matches nothing.
            status: Sent as ``filter[status]``: ``active``,
                ``acknowledged`` or ``resolved``. Any other value is ignored.
            q: Case-insensitive substring match on the title or message.

        Returns:
            :class:`AlertListResponse` with ``items``, ``total`` and
            ``has_more``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a ``page`` below ``1`` or a
                ``page_size`` over ``100``, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "filter[severity]": severity,
            "filter[status]": status,
            "q": q,
        }
        return self._model(AlertListResponse, self._get(_BASE, params=params))

    def get_summary(self) -> AlertSummary:
        """Counts of the alerts addressed to the calling key (``GET /alerts/summary``).

        Counts are by severity and status over the alerts :meth:`list` would
        return with no filter; they are not a census of the organization.

        Returns:
            :class:`AlertSummary`.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(AlertSummary, self._get(f"{_BASE}/summary"))

    def get(self, alert_id: str) -> AlertRead:
        """One alert (``GET /alerts/{alert_id}``).

        Args:
            alert_id: The alert to read, as ``id`` in a listing.

        Returns:
            :class:`AlertRead`.

        Raises:
            ValueError: If ``alert_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an alert that does not exist,
                belongs to another organization, is older than 30 days or is
                not addressed to the key, and ``502`` (``PerceivoServerError``)
                when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(AlertRead, self._get(f"{_BASE}/{segment(alert_id, 'alert_id')}"))

    def acknowledge(self, alert_id: str) -> AlertRead:
        """Mark an alert as seen (``POST /alerts/{alert_id}/acknowledge``).

        The status becomes ``acknowledged`` and ``acknowledged_at`` and
        ``acknowledged_by`` are recorded. The operation takes no request body.
        No status is checked first: acknowledging a resolved alert sets it
        back to ``acknowledged``, and acknowledging twice overwrites the time.

        Args:
            alert_id: The alert to acknowledge.

        Returns:
            :class:`AlertRead` after the change.

        Raises:
            ValueError: If ``alert_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an alert that does not exist,
                belongs to another organization or is not addressed to the key,
                and ``502`` (``PerceivoServerError``) when an upstream service
                fails, in which case the change may have landed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AlertRead, self._post(f"{_BASE}/{segment(alert_id, 'alert_id')}/acknowledge")
        )

    def resolve(self, alert_id: str, body: dict[str, Any] | None = None) -> AlertRead:
        """Resolve an alert (``POST /alerts/{alert_id}/resolve``).

        The status becomes ``resolved`` and ``resolved_at`` and
        ``resolved_by`` are recorded. Resolving twice succeeds and overwrites
        the time.

        Args:
            alert_id: The alert to resolve.
            body: An optional ``AlertResolve`` object
                (``{"resolution_notes": "..."}``, at most 2,000 characters).
                Omitted, no request body is sent.

        Returns:
            :class:`AlertRead` after the change.

        Raises:
            ValueError: If ``alert_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an alert that does not exist,
                belongs to another organization or is not addressed to the key,
                ``422`` (``PerceivoValidationError``) for notes the API refuses,
                and ``502`` (``PerceivoServerError``) when an upstream service
                fails, in which case the change may have landed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AlertRead,
            self._post(f"{_BASE}/{segment(alert_id, 'alert_id')}/resolve", json=body),
        )
