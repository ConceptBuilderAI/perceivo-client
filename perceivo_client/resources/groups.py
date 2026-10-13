"""Groups namespace (``client.groups``).

Groups of members in the caller's organization, at the top-level ``/groups``
surface. Create, list, inspect, update and delete groups; list a group's
members, change the privileges a member holds in the group, and remove a member
from it. The contract publishes no operation that adds a member to a group, so
this namespace has none.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import GroupMemberRead, GroupRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/groups"


class GroupsResource(BaseResource):
    """Manage organization groups and their membership."""

    def create(self, body: dict[str, Any]) -> GroupRead:
        """Create a group (``POST /groups``).

        Args:
            body: A ``GroupCreate`` object, sent as the JSON body.

        Returns:
            :class:`GroupRead`: the new group.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``400`` for
                ``system`` visibility, which only the platform assigns, ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the key lacks the privilege, or the person the
                group would be owned by is not an active member, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(GroupRead, self._post(_BASE, json=body))

    def list(self) -> list[GroupRead]:
        """Every group in the caller's organization (``GET /groups``).

        This method sends no paging parameters, so one response returns every
        group. The API also accepts ``page`` and ``page_size`` (at most 100) to
        request one page; ``sort_by`` and ``sort_order`` are accepted but not
        applied.

        Returns:
            ``list[GroupRead]``: every group, in one response.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential may not reach group operations,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(GroupRead, self._get(_BASE))

    def get(self, group_id: str) -> GroupRead:
        """One group (``GET /groups/{group_id}``).

        Args:
            group_id: The group to read.

        Returns:
            :class:`GroupRead`.

        Raises:
            ValueError: If ``group_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential may not reach group operations,
                ``404`` (``PerceivoNotFoundError``) for a group that does not exist or belongs to
                another organization, ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(GroupRead, self._get(f"{_BASE}/{segment(group_id, 'group_id')}"))

    def update(self, group_id: str, body: dict[str, Any]) -> GroupRead:
        """Update a group (``PATCH /groups/{group_id}``).

        Args:
            group_id: The group to update.
            body: A ``GroupUpdate`` object; only the fields it carries change.

        Returns:
            :class:`GroupRead`: the group after the update.

        Raises:
            ValueError: If ``group_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400`` for a move to
                ``system`` visibility, ``403`` (``PerceivoGrantError``) for a key without both
                ``GROUP_UPDATE`` and ``GROUP_MANAGE_MEMBERS``, ``404`` (``PerceivoNotFoundError``)
                for a group that does not exist or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            GroupRead, self._patch(f"{_BASE}/{segment(group_id, 'group_id')}", json=body)
        )

    def delete(self, group_id: str) -> None:
        """Delete a group (``DELETE /groups/{group_id}``).

        Args:
            group_id: The group to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``group_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400`` for the
                organization's default group, ``403`` (``PerceivoGrantError``) for a key
                without ``GROUP_DELETE``, ``404`` (``PerceivoNotFoundError``) for a group that does
                not exist or belongs to another organization (so a repeated delete answers ``404``),
                and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(group_id, 'group_id')}")

    def list_members(self, group_id: str) -> list[GroupMemberRead]:
        """A group's members (``GET /groups/{group_id}/members``).

        The route is not paged: every member is returned in one response.

        Args:
            group_id: The group whose members to list.

        Returns:
            ``list[GroupMemberRead]``.

        Raises:
            ValueError: If ``group_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential may not reach group operations,
                ``404`` (``PerceivoNotFoundError``) for a group that does not exist or belongs to
                another organization, ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            GroupMemberRead,
            self._get(f"{_BASE}/{segment(group_id, 'group_id')}/members"),
        )

    def update_member(self, group_id: str, user_id: str, body: dict[str, Any]) -> GroupMemberRead:
        """Replace the privileges a member holds in the group.

        Calls ``PATCH /groups/{group_id}/members/{user_id}``.

        Args:
            group_id: The group.
            user_id: The member whose privileges change.
            body: A ``GroupMemberPrivileges`` object.

        Returns:
            :class:`GroupMemberRead`: the membership after the change.

        Raises:
            ValueError: If ``group_id`` or ``user_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) when the key lacks ``GROUP_MANAGE_MEMBERS``, hands out
                privileges it does not hold itself, or touches ``ADMIN_GROUP``
                (``group_authority_reserved``), ``404`` (``PerceivoNotFoundError``) for a group that
                does not exist or belongs to another organization, or a user who is not a member of
                it, ``422`` (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            GroupMemberRead,
            self._patch(
                f"{_BASE}/{segment(group_id, 'group_id')}/members/{segment(user_id, 'user_id')}",
                json=body,
            ),
        )

    def remove_member(self, group_id: str, user_id: str) -> None:
        """Remove a member from a group (``DELETE /groups/{group_id}/members/{user_id}``).

        Args:
            group_id: The group.
            user_id: The member to remove.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``group_id`` or ``user_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) when the key lacks ``GROUP_MANAGE_MEMBERS``, or the
                member holds ``ADMIN_GROUP`` (``group_authority_reserved``), ``404``
                (``PerceivoNotFoundError``) for a group that does not exist or belongs to another
                organization, or a user who is not a member of it (so a repeated removal answers
                ``404``), and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(group_id, 'group_id')}/members/{segment(user_id, 'user_id')}"
        )
