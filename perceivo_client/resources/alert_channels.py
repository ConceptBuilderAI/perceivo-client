"""Alert channels namespace (``client.alert_channels``).

The destinations alert rules notify. Create, list, inspect, update and delete
channels at ``/alert-channels``. Rules are managed on ``client.alert_rules``
and fired alerts are read on ``client.alerts``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import AlertChannelRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/alert-channels"


class AlertChannelsResource(BaseResource):
    """Manage alert notification channels."""

    def create(self, body: dict[str, Any]) -> AlertChannelRead:
        """Create a channel (``POST /alert-channels``).

        Args:
            body: An ``AlertChannelCreate`` object, sent as the JSON body.

        Returns:
            :class:`AlertChannelRead`: the channel as stored.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a body the API refuses, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(AlertChannelRead, self._post(_BASE, json=body))

    def list(self) -> list[AlertChannelRead]:
        """Every channel in the organization (``GET /alert-channels``).

        The route is not paged. Each channel's ``config`` is returned as it
        was stored, including any signing secret or token it carries, so treat
        the result as a credential.

        Returns:
            ``list[AlertChannelRead]``: every channel, in one response.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(AlertChannelRead, self._get(_BASE))

    def get(self, channel_id: str) -> AlertChannelRead:
        """One channel (``GET /alert-channels/{channel_id}``).

        ``config`` is returned as it was stored, including any signing secret
        or token it carries.

        Args:
            channel_id: The channel to read.

        Returns:
            :class:`AlertChannelRead`.

        Raises:
            ValueError: If ``channel_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a channel that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AlertChannelRead, self._get(f"{_BASE}/{segment(channel_id, 'channel_id')}")
        )

    def update(self, channel_id: str, body: dict[str, Any]) -> AlertChannelRead:
        """Update a channel (``PATCH /alert-channels/{channel_id}``).

        Args:
            channel_id: The channel to update.
            body: An ``AlertChannelUpdate`` object; only the fields it carries
                change.

        Returns:
            :class:`AlertChannelRead`: the channel after the update.

        Raises:
            ValueError: If ``channel_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a channel that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AlertChannelRead, self._patch(f"{_BASE}/{segment(channel_id, 'channel_id')}", json=body)
        )

    def delete(self, channel_id: str) -> None:
        """Delete a channel (``DELETE /alert-channels/{channel_id}``).

        Args:
            channel_id: The channel to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``channel_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a channel that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(channel_id, 'channel_id')}")
