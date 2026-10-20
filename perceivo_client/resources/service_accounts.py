"""Service-accounts namespace (``client.service_accounts``).

Machine identities (API keys) of your organization: list, create, inspect,
update, rotate the credential, unlock and revoke.

:meth:`ServiceAccountsResource.create` and :meth:`ServiceAccountsResource.rotate`
return :class:`ServiceAccountCreated`, which carries the plaintext credential
once; :meth:`ServiceAccountsResource.delete` returns the
:class:`ServiceAccountRevoked` receipt; every other method returns the
metadata-only :class:`ServiceAccountRead`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    ServiceAccountCreated,
    ServiceAccountRead,
    ServiceAccountRevoked,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/service-accounts"


class ServiceAccountsResource(BaseResource):
    """Manage service-account (machine) identities and their credentials."""

    def list(self) -> list[ServiceAccountRead]:
        """List every service account of your organization (``GET /service-accounts``).

        One request returns every account, revoked ones included, newest
        first. The method sends no paging parameters, and without them the API
        returns the whole list. No key material is returned, only key prefixes.

        Returns:
            ``list[ServiceAccountRead]`` — every account.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a suspended organization,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(ServiceAccountRead, self._get(_BASE))

    def create(self, body: dict[str, Any]) -> ServiceAccountCreated:
        """Create a service account (``POST /service-accounts``, ``201``).

        ``body`` is a ``ServiceAccountCreate``. The new account's privileges
        and confinement are capped to the calling key's own. The plaintext
        credential is in the answer and is never shown again.

        Args:
            body: A ``ServiceAccountCreate`` object, sent as the JSON body.

        Returns:
            :class:`ServiceAccountCreated` — the account and its one-time
            credential.

        Raises:
            PerceivoAPIError: On an error response: ``400`` for an
                ``auth_mode`` the organization may not use, ``403``
                (``PerceivoGrantError``) when the caller holds none of the
                requested privileges or asks for wider confinement than its
                own, ``422`` (``PerceivoValidationError``) for an unknown
                privilege or a malformed request, and ``502``
                (``PerceivoServerError``) when the platform did not answer:
                list the service accounts before retrying, because the account
                may have been created.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ServiceAccountCreated, self._post(_BASE, json=body))

    def get(self, service_account_id: str) -> ServiceAccountRead:
        """Read one service account (``GET /service-accounts/{service_account_id}``).

        Args:
            service_account_id: The service account to read.

        Returns:
            :class:`ServiceAccountRead`.

        Raises:
            ValueError: If ``service_account_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for an account of another
                organization, ``404`` (``PerceivoNotFoundError``) for one that
                does not exist, ``422`` (``PerceivoValidationError``) for a
                malformed id, and ``502`` (``PerceivoServerError``) when the
                platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceAccountRead,
            self._get(f"{_BASE}/{segment(service_account_id, 'service_account_id')}"),
        )

    def update(self, service_account_id: str, body: dict[str, Any]) -> ServiceAccountRead:
        """Change a service account (``PATCH /service-accounts/{service_account_id}``).

        ``body`` is a ``ServiceAccountUpdate``. Requires
        ``ORG_MANAGE_MEMBERS``.

        Args:
            service_account_id: The service account to change.
            body: A ``ServiceAccountUpdate`` object, sent as the JSON body.

        Returns:
            :class:`ServiceAccountRead` — the account after the change.

        Raises:
            ValueError: If ``service_account_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without
                ``ORG_MANAGE_MEMBERS``, for an account of another
                organization, or for a privilege the caller does not hold,
                ``404`` (``PerceivoNotFoundError``) for an account that does not
                exist, ``409`` (``PerceivoConflictError``) for a signing
                ``auth_mode`` on an account without a signing secret, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the account before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceAccountRead,
            self._patch(f"{_BASE}/{segment(service_account_id, 'service_account_id')}", json=body),
        )

    def rotate(self, service_account_id: str) -> ServiceAccountCreated:
        """Replace a service account's credential (``POST /service-accounts/{id}/rotate``).

        The previous credential stops working at once; the new plaintext
        credential is in the answer and is never shown again. The ``prefix``
        does not change on rotation: it is a display label shared by every key
        in the organization, so identify the account by ``id``.
        A lock survives rotation, and a revoked account cannot be rotated. The
        caller must hold every privilege of the target account. No request body
        is sent.

        Args:
            service_account_id: The service account to rotate.

        Returns:
            :class:`ServiceAccountCreated` — the account and its new one-time
            credential.

        Raises:
            ValueError: If ``service_account_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response: ``400`` for a revoked
                account, ``403`` (``PerceivoGrantError``) for an account of
                another organization or one holding a privilege the caller
                lacks, ``404`` (``PerceivoNotFoundError``) for an account that
                does not exist, ``422`` (``PerceivoValidationError``) for a
                malformed id, and ``502`` (``PerceivoServerError``) when the
                platform did not answer: the credential may already have been
                replaced, so rotate again before using it.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceAccountCreated,
            self._post(f"{_BASE}/{segment(service_account_id, 'service_account_id')}/rotate"),
        )

    def unlock(self, service_account_id: str) -> ServiceAccountRead:
        """Clear a service account's automatic lock (``POST /service-accounts/{id}/unlock``).

        Fix the cause of the lock first, or the same traffic locks the account
        again. Unlocking an account that is not locked changes nothing.
        Requires ``ORG_MANAGE_MEMBERS`` and every privilege of the
        target account. No request body is sent.

        Args:
            service_account_id: The service account to unlock.

        Returns:
            :class:`ServiceAccountRead` — the account after the unlock.

        Raises:
            ValueError: If ``service_account_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without the privileges or for an
                account of another organization, ``404``
                (``PerceivoNotFoundError``) for an account that does not exist,
                ``422`` (``PerceivoValidationError``) for a malformed id, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the account before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceAccountRead,
            self._post(f"{_BASE}/{segment(service_account_id, 'service_account_id')}/unlock"),
        )

    def delete(self, service_account_id: str) -> ServiceAccountRevoked:
        """Revoke a service account (``DELETE /service-accounts/{service_account_id}``).

        The credential stops authenticating at once; revocation is permanent.
        The API answers with a receipt, not an empty ``204``, and a repeat
        answers a receipt again. Requires ``ORG_MANAGE_MEMBERS``.

        Args:
            service_account_id: The service account to revoke.

        Returns:
            :class:`ServiceAccountRevoked` — the revocation receipt.

        Raises:
            ValueError: If ``service_account_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without
                ``ORG_MANAGE_MEMBERS`` or for an account of another
                organization, ``404`` (``PerceivoNotFoundError``) for an
                account that does not exist, ``422``
                (``PerceivoValidationError``) for a malformed id, and ``502``
                (``PerceivoServerError``) when the platform did not answer:
                read the account before retrying, because it may already be
                revoked.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceAccountRevoked,
            self._delete(f"{_BASE}/{segment(service_account_id, 'service_account_id')}"),
        )
