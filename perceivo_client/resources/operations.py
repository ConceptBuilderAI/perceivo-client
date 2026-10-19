"""Operations namespace (``client.operations``).

An operation is the platform's durable record of long-running work that is
neither an orchestration run nor a prediction: its status, its result or error,
and whether cancellation was requested. Its id starts with ``op_``. Poll one
with :meth:`get`, request cancellation with :meth:`cancel`, and page through
the operations the calling key started with :meth:`list`.
"""

from __future__ import annotations

from perceivo_client._paths import segment
from perceivo_client.generated.models import Operation, OperationPage
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/operations"


class OperationsResource(BaseResource):
    """Poll, list and cancel asynchronous operations."""

    def list(
        self,
        *,
        status: str | None = None,
        cursor: str | None = None,
        page_size: int | None = None,
    ) -> OperationPage:
        """List the operations the calling key started, newest first (``GET /operations``).

        The page is cursor-based: pass ``cursor=page.next`` until ``next`` is
        absent. A terminal operation drops out of the list 30 days after it
        finished.

        Args:
            status: Only operations in this status (the ``filter[status]``
                query parameter). Omitted, it is not sent.
            cursor: The ``next`` cursor of the previous page. Omitted, the
                first page is read.
            page_size: Operations per page, 1 to 100. Omitted, the server
                default (20) applies.

        Returns:
            :class:`OperationPage` — one page and its ``next`` cursor.

        Raises:
            PerceivoValidationError: For a malformed query (``422``).
            PerceivoAPIError: On any other error response, for example
                ``PerceivoServerError`` (``502``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"filter[status]": status, "cursor": cursor, "page_size": page_size}
        return self._model(OperationPage, self._get(_BASE, params=params))

    def get(self, operation_id: str) -> Operation:
        """Read one operation (``GET /operations/{operation_id}``).

        Args:
            operation_id: The operation to read (``op_...``).

        Returns:
            :class:`Operation`.

        Raises:
            ValueError: If ``operation_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For an unknown operation id, including a run
                id (``404``).
            PerceivoAPIError: On any other error response. A terminal record
                more than 30 days old answers ``410``, which has no subclass:
                test ``status_code == 410``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(Operation, self._get(f"{_BASE}/{segment(operation_id, 'operation_id')}"))

    def cancel(self, operation_id: str) -> Operation:
        """Request cancellation of an operation (``POST /operations/{operation_id}/cancel``).

        Only a ``queued``, ``running`` or ``paused`` operation can be
        cancelled. The request sets ``cancel_requested`` and leaves the status
        unchanged; the status becomes ``cancelled`` only once the work's
        producer observes the flag and stops.

        Args:
            operation_id: The operation to cancel.

        Returns:
            :class:`Operation` — its updated record.

        Raises:
            ValueError: If ``operation_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For an unknown operation id (``404``).
            PerceivoConflictError: For an operation already in a terminal state
                (``409``).
            PerceivoAPIError: On any other error response, including ``410``
                for a terminal record more than 30 days old.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            Operation, self._post(f"{_BASE}/{segment(operation_id, 'operation_id')}/cancel")
        )
