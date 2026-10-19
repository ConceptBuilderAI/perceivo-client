"""Alert rules namespace (``client.alert_rules``).

The conditions that raise alerts. Create, list, inspect, update, delete and
test rules at ``/alert-rules``, and read the catalog of rule types the platform
supports. Notification destinations are managed on ``client.alert_channels``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AlertRuleCatalog,
    AlertRuleRead,
    AlertRuleTestResult,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/alert-rules"


class AlertRulesResource(BaseResource):
    """Manage alert rules."""

    def create(self, body: dict[str, Any]) -> AlertRuleRead:
        """Create a rule (``POST /alert-rules``).

        Args:
            body: An ``AlertRuleCreate`` object, sent as the JSON body.

        Returns:
            :class:`AlertRuleRead`: the rule as stored.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a body the API refuses, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(AlertRuleRead, self._post(_BASE, json=body))

    def list(self) -> list[AlertRuleRead]:
        """Every rule in the organization (``GET /alert-rules``).

        The route is not paged.

        Returns:
            ``list[AlertRuleRead]``: every rule, in one response.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(AlertRuleRead, self._get(_BASE))

    def get_catalog(self) -> AlertRuleCatalog:
        """The rule types a rule may use (``GET /alert-rules/catalog``).

        Each type is listed with its parameters.

        Returns:
            :class:`AlertRuleCatalog`.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(AlertRuleCatalog, self._get(f"{_BASE}/catalog"))

    def get(self, rule_id: str) -> AlertRuleRead:
        """One rule (``GET /alert-rules/{rule_id}``).

        Args:
            rule_id: The rule to read.

        Returns:
            :class:`AlertRuleRead`.

        Raises:
            ValueError: If ``rule_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a rule that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(AlertRuleRead, self._get(f"{_BASE}/{segment(rule_id, 'rule_id')}"))

    def update(self, rule_id: str, body: dict[str, Any]) -> AlertRuleRead:
        """Update a rule (``PATCH /alert-rules/{rule_id}``).

        Args:
            rule_id: The rule to update.
            body: An ``AlertRuleUpdate`` object; only the fields it carries
                change.

        Returns:
            :class:`AlertRuleRead`: the rule after the update.

        Raises:
            ValueError: If ``rule_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a rule that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AlertRuleRead, self._patch(f"{_BASE}/{segment(rule_id, 'rule_id')}", json=body)
        )

    def delete(self, rule_id: str) -> None:
        """Delete a rule (``DELETE /alert-rules/{rule_id}``).

        Args:
            rule_id: The rule to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``rule_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a rule that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(rule_id, 'rule_id')}")

    def test(self, rule_id: str, body: dict[str, Any] | None = None) -> AlertRuleTestResult:
        """Send a real test notification through a rule (``POST /alert-rules/{rule_id}/test``).

        Warning:
            This always delivers. The notification goes to the rule's
            recipients on its channels whether or not the rule's condition
            matches the synthetic event; ``matched`` only reports whether a real
            event of that type would have fired the rule. No alert is recorded
            and the rule's cooldown is not armed. A rule that reaches more than
            its creator can be test-fired once per 15 minutes.

        Args:
            rule_id: The rule to test-fire.
            body: An optional ``AlertRuleTest`` object (``event_type``,
                ``message``, ``source_name``). Omitted, no request body is sent
                and the API uses its defaults.

        Returns:
            :class:`AlertRuleTestResult`: ``matched``, ``dispatched`` (the
            dispatch was attempted without an exception, not a delivery
            receipt) and ``recipients``.

        Raises:
            ValueError: If ``rule_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a rule that does not exist or
                belongs to another organization, ``422``
                (``PerceivoValidationError``) for an unknown body field, ``429``
                (``PerceivoRateLimitError``) when the rule or the organization
                has used its test-fire allowance for the 15-minute window, and
                ``502`` (``PerceivoServerError``) when an upstream service
                fails, in which case the test may already have been delivered.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AlertRuleTestResult,
            self._post(f"{_BASE}/{segment(rule_id, 'rule_id')}/test", json=body),
        )
