"""Queue namespace (``client.queue``).

The inputs a capability has queued: list them, read how many are waiting, and
cancel them. Every method addresses the ``input`` queue family, the only one
the API serves for a capability, and ``asset_id`` is the capability's
identifier.
"""

from __future__ import annotations

from typing import Literal, overload

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    ActivityResponse,
    BulkCancelResponse,
    CancelInputResponse,
    CapabilityQueueDepthRead,
    CapabilityQueuePurgeResult,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/queue"
_KIND = "input"


class QueueResource(BaseResource):
    """List, measure and cancel a capability's queued inputs."""

    def list(self, asset_id: str) -> ActivityResponse:
        """List one capability's queue items (``GET /queue?kind=input&asset_id=...``).

        The inputs queued for, running on, and recently finished by the
        capability, listed without their input payloads. An item's ``id`` is
        the ``request_id`` a queued ``client.orchestrations.run`` returned; its
        ``run_id`` is set once the input is dispatched. This operation does not
        return input payloads.

        Args:
            asset_id: The capability whose queue items are listed.

        Returns:
            :class:`ActivityResponse`: the ``queued``, ``running`` and
            ``recent`` queue items, each without its input payload, and
            ``counts``.

        Raises:
            PerceivoNotFoundError: For a capability that is unknown or belongs
                to another organization (``404``).
            PerceivoValidationError: For an ``asset_id`` that is not a UUID
                (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ActivityResponse, self._get(_BASE, params={"kind": _KIND, "asset_id": asset_id})
        )

    def get_summary(self, asset_id: str) -> CapabilityQueueDepthRead:
        """Read one capability's queue depth (``GET /queue/summary?kind=input&asset_id=...``).

        How many inputs are waiting for the capability and how long the oldest
        has waited. Work already running is not counted.

        Args:
            asset_id: The capability whose queue is measured.

        Returns:
            :class:`CapabilityQueueDepthRead`.

        Raises:
            PerceivoNotFoundError: For a capability that is not in your
                organization (``404``).
            PerceivoValidationError: For an ``asset_id`` that is not a UUID
                (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityQueueDepthRead,
            self._get(f"{_BASE}/summary", params={"kind": _KIND, "asset_id": asset_id}),
        )

    def cancel_item(self, item_id: str) -> CancelInputResponse:
        """Cancel one input, waiting or running (``DELETE /queue/{item_id}?kind=input``).

        Args:
            item_id: The input to cancel.

        Returns:
            :class:`CancelInputResponse`.

        Raises:
            ValueError: If ``item_id`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoGrantError: For a key without ``WORKLOAD_CONTROL``
                (``403``).
            PerceivoNotFoundError: For an input that is unknown or belongs to
                another organization (``404``).
            PerceivoAPIError: On any other error response, including ``400``
                for an input that is already ``completed``, ``failed`` or
                ``cancelled``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CancelInputResponse,
            self._delete(f"{_BASE}/{segment(item_id, 'item_id')}", params={"kind": _KIND}),
        )

    @overload
    def cancel(
        self, asset_id: str, *, include_running: Literal[False]
    ) -> CapabilityQueuePurgeResult: ...

    @overload
    def cancel(self, asset_id: str, *, include_running: Literal[True]) -> BulkCancelResponse: ...

    @overload
    def cancel(
        self, asset_id: str, *, include_running: bool
    ) -> BulkCancelResponse | CapabilityQueuePurgeResult: ...

    def cancel(
        self, asset_id: str, *, include_running: bool
    ) -> BulkCancelResponse | CapabilityQueuePurgeResult:
        """Cancel the work queued for one capability (``POST /queue/cancel``).

        With ``include_running=False`` every input still waiting is dropped and
        running work is left alone. With ``include_running=True`` running inputs
        are stopped as well. ``include_running`` has no default because the API
        requires it and there is no undo.

        Args:
            asset_id: The capability whose queue is cancelled.
            include_running: Whether running inputs are stopped too.

        Returns:
            :class:`CapabilityQueuePurgeResult` when ``include_running`` is
            ``False``; :class:`BulkCancelResponse` when it is ``True``.

        Raises:
            PerceivoGrantError: For a key without ``CAPABILITY_START_STOP`` on
                the capability (``403``).
            PerceivoNotFoundError: For a capability that is unknown or belongs
                to another organization (``404``).
            PerceivoServerError: When the result could not be read (``502``);
                the cancellation may have happened, and the request is not
                retried.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        body = {"kind": _KIND, "asset_id": asset_id, "include_running": include_running}
        response = self._post(f"{_BASE}/cancel", json=body)
        if include_running:
            return self._model(BulkCancelResponse, response)
        return self._model(CapabilityQueuePurgeResult, response)
