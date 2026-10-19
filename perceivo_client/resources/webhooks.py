"""Webhooks namespace (``client.webhooks``).

Register and manage the organization's event subscriptions under
``/v1/webhooks``, read their delivery attempts and send test deliveries. To
verify a delivery your endpoint receives, use
:func:`perceivo_client.verify_webhook`.

A webhook record carries the fields :class:`WebhookRead` declares and three
more that every read returns: ``organization_id``, ``created_by_user_sub`` (the
creating identity, ``api_key:<key id>`` for a key) and ``updated_at``. Read
them as attributes, for example ``webhook.updated_at``, or from
``webhook.model_extra``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    WebhookDeliveryRead,
    WebhookEventTypeRead,
    WebhookRead,
    WebhookTestResult,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/webhooks"


class WebhooksResource(BaseResource):
    """Register, inspect, test and remove webhooks, and read their deliveries."""

    def list(self) -> list[WebhookRead]:
        """List the organization's webhooks (``GET /webhooks``).

        One request returns every webhook; the list is not paged.

        Returns:
            ``list[WebhookRead]`` — every webhook.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a key whose endpoint groups
                exclude ``webhooks``, ``404`` (``PerceivoNotFoundError``) for a
                key not bound to its organization, and ``502``
                (``PerceivoServerError``) when the platform did not answer;
                nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(WebhookRead, self._get(_BASE))

    def create(self, body: dict[str, Any]) -> WebhookRead:
        """Register a webhook (``POST /webhooks``, ``201``).

        ``body`` is a ``WebhookCreate``: ``name``, an ``https://`` ``url``, a
        signing ``secret`` of at least 16 characters, and optional ``events``
        (empty means every type) and ``description``. The secret is never
        returned.

        Args:
            body: A ``WebhookCreate`` object, sent as the JSON body.

        Returns:
            :class:`WebhookRead` — the new webhook.

        Raises:
            PerceivoAPIError: On an error response: ``400`` for an event type
                that is unknown or not subscribable, or a ``url`` that is not
                ``https://``, ``403`` (``PerceivoGrantError``) for a key
                whose endpoint groups exclude ``webhooks``, ``422``
                (``PerceivoValidationError``) for a missing or malformed field,
                and ``502`` or ``503`` (``PerceivoServerError``) when the
                platform could not complete the request: list the webhooks
                before retrying, because the webhook may have been created.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(WebhookRead, self._post(_BASE, json=body))

    def get(self, webhook_id: str) -> WebhookRead:
        """Read one webhook (``GET /webhooks/{webhook_id}``).

        Args:
            webhook_id: The webhook to read.

        Returns:
            :class:`WebhookRead`.

        Raises:
            ValueError: If ``webhook_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a webhook that does not exist
                or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(WebhookRead, self._get(f"{_BASE}/{segment(webhook_id, 'webhook_id')}"))

    def update(self, webhook_id: str, body: dict[str, Any]) -> WebhookRead:
        """Change a webhook (``PATCH /webhooks/{webhook_id}``).

        ``body`` is a ``WebhookUpdate``; only the fields sent change. Sending
        ``secret`` replaces the signing secret. Re-enabling a disabled webhook
        does not reset ``consecutive_failures``.

        Args:
            webhook_id: The webhook to change.
            body: A ``WebhookUpdate`` object, sent as the JSON body.

        Returns:
            :class:`WebhookRead` — the webhook after the change.

        Raises:
            ValueError: If ``webhook_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` for an event type
                that is unknown or not subscribable, or a ``url`` that is not
                ``https://``, ``404`` (``PerceivoNotFoundError``) for a webhook
                that does not exist or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed field, and
                ``502`` or ``503`` (``PerceivoServerError``) when the platform
                could not complete the request: read the webhook before
                retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            WebhookRead, self._patch(f"{_BASE}/{segment(webhook_id, 'webhook_id')}", json=body)
        )

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook (``DELETE /webhooks/{webhook_id}``, ``204``).

        Args:
            webhook_id: The webhook to delete.

        Raises:
            ValueError: If ``webhook_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a webhook that does not exist
                or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: list the webhooks before retrying, because it may have
                been deleted.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(webhook_id, 'webhook_id')}")

    def list_deliveries(self, webhook_id: str) -> list[WebhookDeliveryRead]:
        """List a webhook's most recent deliveries (``GET /webhooks/{webhook_id}/deliveries``).

        At most the 50 most recent deliveries, newest first; older deliveries
        cannot be read, so treat a list of exactly 50 as truncated. A
        delivery's ``id`` equals the ``Perceivo-Delivery-Id`` header it was
        sent with.

        Args:
            webhook_id: The webhook to read.

        Returns:
            ``list[WebhookDeliveryRead]`` — up to 50 deliveries.

        Raises:
            ValueError: If ``webhook_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a webhook that does not exist
                or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            WebhookDeliveryRead,
            self._get(f"{_BASE}/{segment(webhook_id, 'webhook_id')}/deliveries"),
        )

    def get_delivery(self, webhook_id: str, delivery_id: str) -> WebhookDeliveryRead:
        """Read one delivery attempt (``GET /webhooks/{webhook_id}/deliveries/{delivery_id}``).

        Only a delivery among the webhook's 50 most recent can be read.

        Args:
            webhook_id: The webhook the delivery belongs to.
            delivery_id: The delivery to read.

        Returns:
            :class:`WebhookDeliveryRead`.

        Raises:
            ValueError: If ``webhook_id`` or ``delivery_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a webhook that does not exist
                or belongs to another organization, or a delivery that does not
                exist or is older than the 50 most recent, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        webhook = segment(webhook_id, "webhook_id")
        delivery = segment(delivery_id, "delivery_id")
        return self._model(
            WebhookDeliveryRead, self._get(f"{_BASE}/{webhook}/deliveries/{delivery}")
        )

    def test(self, webhook_id: str) -> WebhookTestResult:
        """Send one signed test delivery now (``POST /webhooks/{webhook_id}/test``).

        The test is sent even to a disabled webhook, is not recorded as a
        delivery, and does not change ``consecutive_failures``. The result says
        what the endpoint answered.

        Args:
            webhook_id: The webhook to test.

        Returns:
            :class:`WebhookTestResult` — ``delivered`` (the endpoint answered
            below ``400``), ``response_code`` and ``error``.

        Raises:
            ValueError: If ``webhook_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a webhook that does not exist
                or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; the test may have been sent.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            WebhookTestResult, self._post(f"{_BASE}/{segment(webhook_id, 'webhook_id')}/test")
        )

    def list_event_types(self) -> list[WebhookEventTypeRead]:
        """List the event types a webhook may subscribe to (``GET /webhooks/event-types``).

        Returns:
            ``list[WebhookEventTypeRead]``.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a key whose endpoint groups
                exclude ``webhooks``, ``429`` (``PerceivoRateLimitError``) when
                requests arrive too fast, ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``)
                when the platform could not produce the list.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(WebhookEventTypeRead, self._get(f"{_BASE}/event-types"))
