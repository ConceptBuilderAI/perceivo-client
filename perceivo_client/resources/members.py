"""Members namespace (``client.members``).

The people in the caller's organization (``/members``): list members, invite a
new one, change a member's organization role, remove a member and restore a
removed one. Pending invitations are managed on ``client.invitations``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import InvitationRead, MemberRead, MemberRoleChangeRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/members"


class MembersResource(BaseResource):
    """Manage the members of the caller's organization."""

    def list(self, *, include_removed: bool | None = None) -> list[MemberRead]:
        """List members (``GET /members``).

        Args:
            include_removed: ``True`` also lists removed members (the
                ``include_removed`` query parameter). Omitted, the parameter is
                not sent and the server default, ``false``, applies.

        Returns:
            ``list[MemberRead]``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) for a key without ``ORGANIZATION_READ``, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"include_removed": include_removed} if include_removed is not None else None
        return self._list(MemberRead, self._get(_BASE, params=params))

    def invite(self, body: dict[str, Any]) -> InvitationRead:
        """Invite a person by email (``POST /members``).

        Args:
            body: A ``MemberInvite`` object, sent as the JSON body.

        Returns:
            :class:`InvitationRead` — the invitation, managed afterwards on
            ``client.invitations``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) for a key without ``ORG_MANAGE_MEMBERS`` or without
                every privilege of the role it invites into, ``409`` (``PerceivoConflictError``)
                when the address already belongs to a member (``already_a_member``) or has a pending
                invitation (``invitation_pending``), ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(InvitationRead, self._post(_BASE, json=body))

    def update_role(self, user_id: str, body: dict[str, Any]) -> MemberRoleChangeRead:
        """Change a member's organization role (``PATCH /members/{user_id}``).

        Args:
            user_id: The member whose role changes.
            body: A ``MemberRoleUpdate`` object.

        Returns:
            :class:`MemberRoleChangeRead`.

        Raises:
            ValueError: If ``user_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) for a key without ``ORG_MANAGE_MEMBERS``, without
                every privilege of both roles, or for a ``global_admin`` member
                (``global_admin_reserved``), ``404`` (``PerceivoNotFoundError``) for a user who is
                not a member of your organization, ``409`` (``PerceivoConflictError``) for a change
                that would leave no active administrator or ``global_admin``, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            MemberRoleChangeRead, self._patch(f"{_BASE}/{segment(user_id, 'user_id')}", json=body)
        )

    def remove(self, user_id: str, *, handoff_to_user_id: str | None = None) -> None:
        """Remove a member (``DELETE /members/{user_id}``).

        Args:
            user_id: The member to remove.
            handoff_to_user_id: Query parameter naming who inherits what the
                member owns; omitted, the parameter is not sent.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``user_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400`` when
                ``handoff_to_user_id`` names the member being removed or someone who is not an
                active administrator, ``401`` (``PerceivoAuthError``) without a valid credential,
                ``403`` (``PerceivoGrantError``) for a key without ``ORG_MANAGE_MEMBERS``,
                without every privilege of the member's role, or for a ``global_admin`` member
                (``global_admin_reserved``), ``404`` (``PerceivoNotFoundError``) for a user who is
                not a member of your organization (so a repeated removal answers ``404``), ``409``
                (``PerceivoConflictError``) when a group owner is removed without a handoff
                (``handoff_required``) or the removal would leave no active administrator or
                ``global_admin``, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = (
            {"handoff_to_user_id": handoff_to_user_id} if handoff_to_user_id is not None else None
        )
        return self._delete(f"{_BASE}/{segment(user_id, 'user_id')}", params=params)

    def restore(self, user_id: str) -> MemberRead:
        """Restore a removed member (``POST /members/{user_id}/restore``).

        Args:
            user_id: The removed member to restore.

        Returns:
            :class:`MemberRead` — the restored member.

        Raises:
            ValueError: If ``user_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) for a key without ``ORG_MANAGE_MEMBERS``, without
                every privilege of the restored role, or for a ``global_admin`` member
                (``global_admin_reserved``), ``404`` (``PerceivoNotFoundError``) for a user who is
                an active member or was never a member, ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(MemberRead, self._post(f"{_BASE}/{segment(user_id, 'user_id')}/restore"))
