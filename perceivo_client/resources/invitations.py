"""Invitations namespace (``client.invitations``).

Invitations into the caller's organization (``/invitations``): list them,
cancel a pending one, or resend one. An invitation is created by
``client.members.invite``.
"""

from __future__ import annotations

from perceivo_client._paths import segment
from perceivo_client.generated.models import InvitationRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/invitations"


class InvitationsResource(BaseResource):
    """Manage pending organization invitations."""

    def list(self, *, status: str | None = None) -> list[InvitationRead]:
        """List invitations (``GET /invitations``).

        Args:
            status: Only invitations in this state (the ``status`` query
                parameter). Omitted, the parameter is not sent and every
                invitation is listed.

        Returns:
            ``list[InvitationRead]``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) for a key without ``ORG_MANAGE_MEMBERS``, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"status": status} if status is not None else None
        return self._list(InvitationRead, self._get(_BASE, params=params))

    def cancel(self, invitation_id: str) -> InvitationRead:
        """Cancel a pending invitation (``POST /invitations/{invitation_id}/cancel``).

        Args:
            invitation_id: The invitation to cancel.

        Returns:
            :class:`InvitationRead` — the invitation after cancellation.

        Raises:
            ValueError: If ``invitation_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400`` for an invitation
                that is no longer pending, ``401`` (``PerceivoAuthError``) without a valid
                credential, ``403`` (``PerceivoGrantError``) for a key without
                ``ORG_MANAGE_MEMBERS``, ``404`` (``PerceivoNotFoundError``) for an invitation that
                does not exist or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            InvitationRead, self._post(f"{_BASE}/{segment(invitation_id, 'invitation_id')}/cancel")
        )

    def resend(self, invitation_id: str, *, rotate_token: bool | None = None) -> InvitationRead:
        """Resend an invitation email (``POST /invitations/{invitation_id}/resend``).

        Args:
            invitation_id: The invitation to resend.
            rotate_token: Query parameter. ``True`` issues a new link; omitted,
                the parameter is not sent and the server default (``false``)
                applies.

        Returns:
            :class:`InvitationRead` — the invitation after the resend.

        Raises:
            ValueError: If ``invitation_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400`` for an invitation
                that is no longer pending, ``401`` (``PerceivoAuthError``) without a valid
                credential, ``403`` (``PerceivoGrantError``) for a key without
                ``ORG_MANAGE_MEMBERS``, one that does not hold every privilege of the invited role,
                or a ``global_admin`` invitation (``global_admin_reserved``), ``404``
                (``PerceivoNotFoundError``) for an invitation that does not exist or belongs to
                another organization, ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"rotate_token": rotate_token} if rotate_token is not None else None
        return self._model(
            InvitationRead,
            self._post(f"{_BASE}/{segment(invitation_id, 'invitation_id')}/resend", params=params),
        )
