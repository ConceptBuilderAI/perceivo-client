"""Organization namespace (``client.organization``).

The caller's own organization, at ``/organization``. The organization is taken
from the credential, never from an argument, so every method here acts on the
caller's organization only: read its profile, its usage limits and its
subscriptions. The profile is changed by a signed-in user in the web console;
the API refuses every API key that tries.
"""

from __future__ import annotations

from perceivo_client.generated.models import (
    OrganizationLimitsRead,
    OrganizationRead,
    SubscriptionReadV1,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/organization"


class OrganizationResource(BaseResource):
    """Read the caller's organization."""

    def get(self) -> OrganizationRead:
        """Read the caller's organization profile (``GET /organization``).

        Returns:
            :class:`OrganizationRead`.

        Raises:
            PerceivoAPIError: On an error response, for example
                ``PerceivoServerError`` (``502``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(OrganizationRead, self._get(_BASE))

    def get_limits(self) -> OrganizationLimitsRead:
        """Read the organization's usage limits (``GET /organization/limits``).

        Returns:
            :class:`OrganizationLimitsRead`.

        Raises:
            PerceivoNotFoundError: For an organization with no live
                subscription (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(OrganizationLimitsRead, self._get(f"{_BASE}/limits"))

    def get_subscription(self) -> list[SubscriptionReadV1]:
        """Read the organization's subscriptions (``GET /organization/subscription``).

        Returns:
            ``list[SubscriptionReadV1]`` — every subscription record, as a list.

        Raises:
            PerceivoAPIError: On an error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(SubscriptionReadV1, self._get(f"{_BASE}/subscription"))
