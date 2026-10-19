"""The traffic plan.

One of the mixins that make up
:class:`~perceivo_client.resources.capabilities.CapabilitiesResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    CapabilityTrafficPlanRead,
    LifecycleOperationResponse,
)
from perceivo_client.resources.capabilities._common import _BASE, _MixinBase


class _TrafficMixin(_MixinBase):
    # -- traffic plan ------------------------------------------------------------
    def replace_traffic(
        self, capability_id: str, body: dict[str, Any]
    ) -> CapabilityTrafficPlanRead:
        """Replace the capability's traffic plan (``PUT .../traffic``).

        Calls ``PUT /capabilities/{capability_id}/traffic``. The allocations
        sent become the new ``active`` plan and the previous plan is
        superseded in the same transaction. :meth:`get_traffic` reads the
        plan this writes and :meth:`delete_traffic` supersedes it.

        Args:
            capability_id: The capability whose plan to replace.
            body: A ``CapabilityTrafficReplace`` object, sent as the JSON body.

        Returns:
            :class:`CapabilityTrafficPlanRead`: the plan now live.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC`` on the capability, ``409``
                (``PerceivoConflictError``) while another plan change is in progress (wait and
                retry), ``404`` (``PerceivoNotFoundError``) for another organization's capability or
                a missing one, ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTrafficPlanRead,
            self._put(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic", json=body),
        )

    def get_traffic(self, capability_id: str) -> CapabilityTrafficPlanRead | None:
        """The routing plan a run resolves against (``GET .../traffic``).

        Calls ``GET /capabilities/{capability_id}/traffic``.

        ``None`` when the capability has no live plan, and the same ``None`` when the
        capability is not yours or does not exist: the three are
        indistinguishable. :meth:`replace_traffic` writes the plan.

        Args:
            capability_id: The capability whose plan to read.

        Returns:
            :class:`CapabilityTrafficPlanRead`, or ``None`` (see above).

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request. An unknown capability answers ``None``, not ``404``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTrafficPlanRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic"),
        )

    def delete_traffic(self, capability_id: str) -> None:
        """Supersede the live plan, releasing its hold on member orchestrations (``204``).

        Wraps ``DELETE /capabilities/{capability_id}/traffic``. While a plan is
        live its allocation blocks deleting the capability and its member
        orchestrations; stopping the capability does not release it. ``404``
        when there is no live plan.

        Args:
            capability_id: The capability whose plan to supersede.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC`` on the capability, ``404``
                (``PerceivoNotFoundError``) with no live plan or not your capability, ``422``
                (``PerceivoValidationError``) if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic")

    def get_traffic_plan(self, capability_id: str) -> CapabilityTrafficPlanRead | None:
        """The live traffic plan, through the rollout route (``GET .../traffic-plan``).

        Calls ``GET /capabilities/{capability_id}/traffic-plan``. It reads the same plan as
        :meth:`get_traffic` and answers the same record, with its ``allocations``; it is
        the read that pairs with :meth:`apply_traffic_plan` and :meth:`delete_traffic_plan`.

        ``None`` when the capability has no live plan or does not exist.

        Args:
            capability_id: The capability whose plan to read.

        Returns:
            :class:`CapabilityTrafficPlanRead`, or ``None`` (see above).

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``422`` (``PerceivoValidationError``) for a
                malformed request. An unknown capability answers ``None``, not ``404``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            CapabilityTrafficPlanRead,
            self._get(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic-plan"),
        )

    def apply_traffic_plan(
        self, capability_id: str, body: dict[str, Any]
    ) -> LifecycleOperationResponse:
        """Apply a traffic plan (``POST /capabilities/{capability_id}/traffic-plan``).

        ``body`` is an ``ApplyTrafficPlanRequest`` (``traffic_plan`` required).

        Args:
            capability_id: The capability to apply the plan to.
            body: An ``ApplyTrafficPlanRequest`` object, sent as the JSON body.

        Returns:
            :class:`LifecycleOperationResponse`: the lifecycle operation the
            apply started.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC``, ``404`` (``PerceivoNotFoundError``) for an unknown
                capability, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LifecycleOperationResponse,
            self._post(
                f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic-plan", json=body
            ),
        )

    def delete_traffic_plan(self, capability_id: str) -> None:
        """Supersede every live traffic plan (``DELETE .../traffic-plan``, ``204``).

        Calls ``DELETE /capabilities/{capability_id}/traffic-plan``. The
        counterpart to :meth:`apply_traffic_plan`; ``404`` when there is no
        live plan to supersede.

        Args:
            capability_id: The capability whose plans to supersede.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``capability_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403`` (``PerceivoGrantError``) without
                ``CAPABILITY_MANAGE_TRAFFIC`` on the capability, ``404``
                (``PerceivoNotFoundError``) with no live plan, ``422`` if malformed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(capability_id, 'capability_id')}/traffic-plan")
