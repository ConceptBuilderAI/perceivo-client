"""Grants namespace (``client.grants``): access grants in the caller's organization.

A grant links a grantee (a user, a group or a service account) to a resource
(the organization, an asset, an intelligence or a capability), through a role
or through direct privileges. List, create, change and revoke grants, and
preview then apply a change that cascades across an asset or capability built
from other assets. A user's access to one asset is a grant whose
``resource_type`` is ``asset``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import CascadeApplyResult, ChangeSet, GrantRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/grants"


class GrantsResource(BaseResource):
    """List, create, change and revoke access grants; preview and apply change sets."""

    def list(
        self,
        *,
        grantee: str | None = None,
        grantee_type: str | None = None,
        grantee_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        include_revoked: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[GrantRead]:
        """List the organization's access grants (``GET /grants``).

        ``grantee="me"`` lists only the grants made directly to the presented
        credential and needs no privilege; any other listing needs
        ``GRANT_READ``. A grant made to a group is listed as the group's
        grant, not expanded into its members. The organization is taken from
        the credential, never from the request.

        ``grantee`` cannot be combined with ``grantee_type`` or ``grantee_id``,
        and ``grantee_type``/``grantee_id`` and ``resource_type``/
        ``resource_id`` are each sent together or not at all.

        Args:
            grantee: ``me``: only the grants made directly to the presented
                credential.
            grantee_type: ``user``, ``group`` or ``service_account``.
            grantee_id: The grantee, with ``grantee_type``.
            resource_type: ``organization``, ``asset``, ``intelligence`` or
                ``capability``.
            resource_id: The resource, with ``resource_type``.
            include_revoked: Include revoked grants. Omitted, the API leaves
                them out.
            limit: At most this many grants, ``1`` to ``1000``.
            offset: Skip this many grants first. Omitted, ``0``.

        Returns:
            ``list[GrantRead]``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) for a listing other than
                ``grantee=me`` without ``GRANT_READ``, ``422``
                (``PerceivoValidationError``) for a filter
                combination it refuses, and ``502`` (``PerceivoServerError``)
                when the access service answers a body it cannot publish.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "grantee": grantee,
            "grantee_type": grantee_type,
            "grantee_id": grantee_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "include_revoked": include_revoked,
            "limit": limit,
            "offset": offset,
        }
        return self._list(GrantRead, self._get(_BASE, params=params))

    def create(self, body: dict[str, Any]) -> GrantRead:
        """Grant a role, or direct privileges, on a resource (``POST /grants``).

        A credential grants only what it holds: an API key needs
        ``GRANT_CREATE`` and must itself hold, on the resource, every
        privilege the grant confers. A second grant to the same grantee on the
        same resource is answered ``409``; change it with :meth:`update`. On a
        composite asset or capability the ``409`` carries ``change_set`` and
        ``reason`` in ``details``; send the same grant through :meth:`preview` and
        :meth:`apply` instead. A grant on a group is refused with ``422``.

        Args:
            body: A ``GrantCreate`` object, sent as the JSON body:
                ``grantee_type``, ``grantee_id``, ``resource_type`` and
                ``resource_id`` are required, with ``role_id`` or
                ``direct_privileges``.

        Returns:
            :class:`GrantRead`: the new grant.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential lacks the privilege or does not
                hold what it would grant, or the grantee is not in the resource's organization,
                ``404`` (``PerceivoNotFoundError``) for a resource, role or grant that does not
                exist, is revoked or belongs to another organization, ``409`` (``PerceivoConflictError``) for a duplicate grant or
                one that needs the change-set preview and apply, ``422``
                (``PerceivoValidationError``) for a malformed request or a group grant, and
                ``502`` (``PerceivoServerError``) when the access service answers a body it
                cannot publish.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(GrantRead, self._post(_BASE, json=body))

    def update(self, grant_id: str, body: dict[str, Any]) -> GrantRead:
        """Change a grant's role or direct privileges (``PATCH /grants/{grant_id}``).

        Each field sent replaces that part of the grant. An API key needs
        ``GRANT_CREATE`` for a change that confers anything and
        ``GRANT_REVOKE`` for one that removes anything, and must hold every
        privilege the change adds or removes on the resource. A role grant
        refused with ``409`` is replaced through :meth:`preview` and
        :meth:`apply` with ``replaces_grant_id`` set to ``grant_id``.

        Args:
            grant_id: The grant to change, as ``id`` in its record.
            body: A ``GrantUpdate`` object (``role_id``,
                ``direct_privileges``), sent as the JSON body.

        Returns:
            :class:`GrantRead`: the grant after the change.

        Raises:
            ValueError: If ``grant_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential lacks the privilege or does not
                hold what the change adds or removes, ``404`` (``PerceivoNotFoundError``) for a
                grant, role or resource that does not exist, is revoked or belongs to another
                organization, ``409``
                (``PerceivoConflictError``) for a change that would remove an asset's last
                administrator or needs the change-set preview and apply, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when the access service answers a body it cannot
                publish.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            GrantRead, self._patch(f"{_BASE}/{segment(grant_id, 'grant_id')}", json=body)
        )

    def delete(self, grant_id: str) -> None:
        """Revoke a grant (``DELETE /grants/{grant_id}``).

        The grant is ended, not erased; revoking it again is answered ``404``.
        An API key needs ``GRANT_REVOKE`` and may revoke only what it could
        have granted. A revoke that would remove an asset's last administrator,
        or leave the grantee holding the privilege on assets built from this
        one, is answered ``409`` with ``change_set`` in ``details``; revoke through
        :meth:`preview` and :meth:`apply` instead.

        Args:
            grant_id: The grant to revoke, as ``id`` in its record.

        Returns:
            ``None`` (``204``).

        Raises:
            ValueError: If ``grant_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential could not have granted what it
                revokes, ``404`` (``PerceivoNotFoundError``) for a grant that does not exist, is
                already revoked or belongs to another organization, ``409`` (``PerceivoConflictError``) when the revoke needs the
                change-set preview and apply, and ``422`` (``PerceivoValidationError``) for a
                malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(grant_id, 'grant_id')}")

    def preview(self, body: dict[str, Any]) -> ChangeSet:
        """Describe every row one grant or revoke would write (``POST /grants/preview``).

        It writes nothing. Pass the returned ``fingerprint``, with the same
        body, to :meth:`apply`.

        Args:
            body: A ``CascadeOperation`` object, sent as the JSON body:
                ``operation`` (``grant`` or ``revoke``), ``grantee_type``,
                ``grantee_id`` and ``resource_id`` are required, with exactly
                one of ``privilege`` (the only form a revoke takes),
                ``privileges`` and ``role_id``; optionally
                ``replaces_grant_id`` (grant forms ``privileges`` and
                ``role_id`` only), ``resource_kind`` (``asset``, the default,
                or ``capability``) and ``all_versions``.

        Returns:
            :class:`ChangeSet`: ``fingerprint`` binds a later :meth:`apply` to
            exactly this set; ``refused`` is true when the set reaches assets
            the caller does not administer, and ``requires_confirmation`` when
            it writes more than the one row asked for.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential lacks ``GRANT_CREATE`` /
                ``GRANT_REVOKE`` or is not allowed to manage grants on the resource, ``404``
                (``PerceivoNotFoundError``) for a resource, role or replaced grant that is absent
                or not visible, ``409`` (``PerceivoConflictError``, ``details.reason``
                ``refused``) when the grantee already has a
                grant that ``replaces_grant_id`` does not name or the replacement would leave
                an asset with no administrator, ``422`` (``PerceivoValidationError``) for a body
                breaking the one-of rules, and ``502`` (``PerceivoServerError``) when the access
                service answers a body it cannot publish.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ChangeSet, self._post(f"{_BASE}/preview", json=body))

    def apply(self, body: dict[str, Any]) -> CascadeApplyResult:
        """Apply a previewed change set (``POST /grants/apply``).

        The set is recomputed rather than taken from the request; when its
        fingerprint still matches and nothing is blocked, every row is written
        in one transaction. A repeat after success is answered ``409``, because
        the set has moved, so this method is not safe to retry blindly.

        Args:
            body: A ``CascadeApply`` object, sent as the JSON body: the body
                sent to :meth:`preview`, plus its ``fingerprint`` (required)
                and an optional ``reason`` recorded on every grant the change
                ends.

        Returns:
            :class:`CascadeApplyResult`: ``applied``, the ``change_set``,
            ``grant_ids`` (every grant written, the replaced grant first)
            and ``revoked_grant_ids``.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``401``
                (``PerceivoAuthError``) without a valid credential, ``403``
                (``PerceivoGrantError``) when the credential lacks the privileges
                :meth:`preview` names, ``404`` (``PerceivoNotFoundError``) for a resource, role or
                replaced grant that is absent or not visible, ``409``
                (``PerceivoConflictError``) when the set moved since the preview
                (``details.reason`` ``stale``, with the fresh ``details.change_set``) or
                cannot be applied (``details.reason`` ``refused``), nothing being written
                either way, ``422`` (``PerceivoValidationError``) for a malformed body, and ``502``
                (``PerceivoServerError``) when the access service answers a body it cannot
                publish.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(CascadeApplyResult, self._post(f"{_BASE}/apply", json=body))
