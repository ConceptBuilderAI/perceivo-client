"""Member orchestrations.

One of the mixins that make up
:class:`~perceivo_client.resources.capabilities.CapabilitiesResource`.
"""

from __future__ import annotations

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    PaginatedItemsResponse,
)
from perceivo_client.resources.capabilities._common import _BASE, _MixinBase


class _OrchestrationsMixin(_MixinBase):
    # -- member orchestrations -----------------------------------------------
    def list_orchestrations(
        self,
        capability_id: str,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> PaginatedItemsResponse:
        """One page of the capability's member orchestrations (``GET .../orchestrations``).

        Calls ``GET /capabilities/{capability_id}/orchestrations``. Newest
        first, as an ``items,total`` page, so
        ``paginate_pages(functools.partial(client.capabilities.list_orchestrations,
        capability_id))`` walks it. A capability that is not yours and one with
        nothing attached both answer an empty page.

        Args:
            capability_id: The capability whose members to list.
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Items per page, ``1`` to ``100``. Omitted, the API uses
                ``25``.

        Returns:
            :class:`PaginatedItemsResponse`: ``items`` and ``total``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            PaginatedItemsResponse,
            self._get(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/orchestrations",
                params={"page": page, "page_size": page_size},
            ),
        )

    def attach_orchestration(self, capability_id: str, orchestration_id: str) -> None:
        """Make an orchestration a member (``PUT .../orchestrations/{orchestration_id}``).

        Calls ``PUT /capabilities/{capability_id}/orchestrations/{orchestration_id}``.

        Answers ``204``; a repeat is a no-op. Needs ``CAPABILITY_READ`` and
        ``CAPABILITY_UPDATE`` on the capability and update rights on the orchestration
        (``ORCHESTRATION_UPDATE`` for a key). A START/END ``409`` changes nothing.

        Args:
            capability_id: The capability to attach to.
            orchestration_id: The orchestration to attach.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``orchestration_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: ``404`` (``PerceivoNotFoundError``) without ``CAPABILITY_READ``;
                ``403`` (``PerceivoGrantError``) without the others; ``409``
                (``PerceivoConflictError``) if in another capability (detach it there first) or off
                the START/END contract; ``422`` (``PerceivoValidationError``) if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._put(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/orchestrations/{segment(orchestration_id, 'orchestration_id')}"
        )

    def detach_orchestration(self, capability_id: str, orchestration_id: str) -> None:
        """Remove a member orchestration; it reverts to standalone (``204``).

        Calls ``DELETE /capabilities/{capability_id}/orchestrations/{orchestration_id}``.

        Refused with ``409`` while it carries traffic under a live plan: supersede the plan first
        (:meth:`delete_traffic`). Needs what :meth:`attach_orchestration` needs.

        Args:
            capability_id: The capability to detach from.
            orchestration_id: The member orchestration to detach.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` or ``orchestration_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: ``404`` (``PerceivoNotFoundError``) without ``CAPABILITY_READ``;
                ``403`` (``PerceivoGrantError``) without the others; ``409``
                (``PerceivoConflictError``) while it, or any version in its lineage, carries traffic
                under a live plan; ``422`` (``PerceivoValidationError``) if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(capability_id, 'capability_id')}/orchestrations/{segment(orchestration_id, 'orchestration_id')}"
        )
