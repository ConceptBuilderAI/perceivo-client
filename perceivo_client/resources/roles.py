"""Roles namespace (``client.roles``).

Roles visible to your organization: the platform's system roles and your
organization's custom roles. List, create, inspect, update and delete custom
roles.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import RoleListItem, RoleReadV1
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/roles"


class RolesResource(BaseResource):
    """List system roles and manage your organization's custom roles."""

    def list(self) -> list[RoleListItem]:
        """List every role visible to your organization (``GET /roles``).

        One request returns every role: system roles first, then custom roles
        by name. The method sends no paging parameters, and without them the API
        returns the whole list. A list item carries ``privilege_count``, not
        the privileges; read one role with :meth:`get` for its full privilege list.
        Requires ``ROLE_LIST``.

        Returns:
            ``list[RoleListItem]`` — every role.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ROLE_LIST``, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(RoleListItem, self._get(_BASE))

    def create(self, body: dict[str, Any]) -> RoleReadV1:
        """Create a custom role in your organization (``POST /roles``, ``201``).

        ``body`` is a ``RoleCreateV1``: ``name``, ``privileges`` and optional
        ``description`` and ``applies_to``. The calling key must hold every
        privilege the role carries. Requires ``ROLE_CREATE``.

        Args:
            body: A ``RoleCreateV1`` object, sent as the JSON body.

        Returns:
            :class:`RoleReadV1` — the new role.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ROLE_CREATE`` or for a
                privilege the key does not hold, ``409``
                (``PerceivoConflictError``) when a custom role with that name
                already exists in your organization, ``422``
                (``PerceivoValidationError``) for a missing or unknown
                privilege or a malformed request, and ``502``
                (``PerceivoServerError``) when the platform did not answer:
                list the roles before retrying, because the role may have been
                created.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RoleReadV1, self._post(_BASE, json=body))

    def get(self, role_id: str) -> RoleReadV1:
        """Read one role with its full privilege list (``GET /roles/{role_id}``).

        Args:
            role_id: The role to read.

        Returns:
            :class:`RoleReadV1`.

        Raises:
            ValueError: If ``role_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ROLE_READ``, ``404``
                (``PerceivoNotFoundError``) for a role that does not exist, was
                deleted, or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed id, and ``502``
                (``PerceivoServerError``) when the platform did not answer;
                nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(RoleReadV1, self._get(f"{_BASE}/{segment(role_id, 'role_id')}"))

    def update(self, role_id: str, body: dict[str, Any]) -> RoleReadV1:
        """Change a custom role (``PATCH /roles/{role_id}``).

        ``body`` is a ``RoleUpdateV1``; a ``privileges`` list replaces the
        role's privileges. The change applies to every grant of the role.
        System roles cannot be changed. Requires ``ROLE_UPDATE``.

        Args:
            role_id: The custom role to change.
            body: A ``RoleUpdateV1`` object, sent as the JSON body.

        Returns:
            :class:`RoleReadV1` — the role after the change.

        Raises:
            ValueError: If ``role_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ROLE_UPDATE``, for a
                system role, or for an added privilege the key does not hold,
                ``404`` (``PerceivoNotFoundError``) for a role that does not
                exist or belongs to another organization, ``409``
                (``PerceivoConflictError``) when the change would leave an
                asset with no administrator (nothing is changed), ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the role before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            RoleReadV1, self._patch(f"{_BASE}/{segment(role_id, 'role_id')}", json=body)
        )

    def delete(self, role_id: str) -> None:
        """Delete a custom role (``DELETE /roles/{role_id}``, ``204``).

        System roles cannot be deleted. Requires ``ROLE_DELETE``.

        Args:
            role_id: The custom role to delete.

        Raises:
            ValueError: If ``role_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ROLE_DELETE`` or for a
                system role, ``404`` (``PerceivoNotFoundError``) for a role
                that does not exist, was already deleted, or belongs to another
                organization, ``409`` (``PerceivoConflictError``) when an asset
                would lose its last administrator (nothing is deleted), ``422``
                (``PerceivoValidationError``) for a malformed id, and ``502``
                (``PerceivoServerError``) when the platform did not answer:
                read the role before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(role_id, 'role_id')}")
