"""Secrets namespace (``client.secrets``).

The organization's secrets under ``/secrets``: list, create, inspect, update,
rotate and delete. Reads return metadata only (name, description, status,
timestamps), never the value. :meth:`SecretsResource.get_value` reads the value
and needs ``SECRET_READ_VALUE``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import SecretRead, SecretValueRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/secrets"
#: The value read lives on the infrastructure secrets route: ``/secrets`` has
#: no value operation.
_VALUE = "/v1/infrastructure/secrets/{secret_id}/value"
#: The largest page the API serves. :meth:`SecretsResource.list` walks with it
#: so a walk takes as few requests as it can.
_MAX_PAGE_SIZE = 100


def _secret_id(item: Any) -> Any:
    """The identity a walked page is de-duplicated on: the secret's ``id``.

    ``None`` for an item without one; such an item is never treated as a
    repeat.
    """
    return item.get("id") if isinstance(item, dict) else None


def _checked_page_size(page_size: int) -> int:
    """Refuse a ``page_size`` the API would refuse, before any request is sent."""
    if isinstance(page_size, bool) or not isinstance(page_size, int):
        raise TypeError("page_size must be a non-boolean int")
    if not 1 <= page_size <= _MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {_MAX_PAGE_SIZE}")
    return page_size


def _checked_page(page: int) -> int:
    """Refuse a ``page`` the API would refuse, before any request is sent."""
    if isinstance(page, bool) or not isinstance(page, int):
        raise TypeError("page must be a non-boolean int")
    if page < 1:
        raise ValueError("page must be 1 or more")
    return page


class SecretsResource(BaseResource):
    """Manage the organization's secrets."""

    def list(self, *, page: int | None = None, page_size: int | None = None) -> list[SecretRead]:
        """List the organization's secrets, newest first (``GET /secrets``).

        The API pages this list and answers each page as a plain array, with no
        total. With no ``page``, this method walks every page and returns all
        the secrets: it requests ``page=1, 2, ...`` and stops at a page shorter
        than ``page_size``, or at one that adds no secret it has not already
        returned. A secret reported on two pages, because the list changed
        during the walk, is returned once. With ``page``, it sends one request
        and returns that page. Requires ``SECRET_LIST``.

        Args:
            page: The one page to return, from ``1``. Omit it to walk every
                page.
            page_size: Secrets per request, from 1 through 100. Defaults to
                ``100`` for a walk and to the API's default (``25``) for one
                page.

        Returns:
            ``list[SecretRead]`` — every secret, or the one requested page.

        Raises:
            TypeError: If ``page`` or ``page_size`` is not an ``int`` (a
                ``bool`` is refused too).
            ValueError: If ``page`` is below 1 or ``page_size`` is outside 1
                through 100.
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``SECRET_LIST``, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        if page_size is not None:
            _checked_page_size(page_size)
        if page is not None:
            query: dict[str, Any] = {"page": _checked_page(page)}
            if page_size is not None:
                query["page_size"] = page_size
            return self._list(SecretRead, self._get(_BASE, params=query))
        size = _MAX_PAGE_SIZE if page_size is None else page_size
        collected: list[Any] = []
        seen: set[Any] = set()
        number = 1
        while True:
            batch = self._get(_BASE, params={"page": number, "page_size": size})
            if not isinstance(batch, list):
                # A body that is not an array ends the walk; on the first page
                # it is returned as received, as every other list method does.
                return self._list(SecretRead, collected if number > 1 else batch)
            fresh = [item for item in batch if _secret_id(item) not in seen]
            seen.update(_secret_id(item) for item in fresh)
            seen.discard(None)
            collected.extend(fresh)
            if len(batch) != size or not fresh:
                return self._list(SecretRead, collected)
            number += 1

    def create(self, body: dict[str, Any]) -> SecretRead:
        """Create a secret (``POST /secrets``, ``201``).

        ``body`` is a ``SecretCreate``: ``name``, ``value`` and optional
        ``description`` and ``expiration_date``. The answer carries the
        metadata only, never the value. Requires ``SECRET_CREATE``.

        Args:
            body: A ``SecretCreate`` object, sent as the JSON body.

        Returns:
            :class:`SecretRead` — the new secret's metadata.

        Raises:
            PerceivoAPIError: On an error response: ``400`` for an expiry that
                is not in the future or an organization at its secret limit,
                ``403`` (``PerceivoGrantError``) without
                ``SECRET_CREATE``, ``422`` (``PerceivoValidationError``) for a
                missing ``name`` or ``value`` or a malformed field, and ``502``
                (``PerceivoServerError``) when the platform did not answer:
                list the secrets before retrying, because the secret may have
                been created.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(SecretRead, self._post(_BASE, json=body))

    def get(self, secret_id: str) -> SecretRead:
        """Read a secret's metadata (``GET /secrets/{secret_id}``).

        Requires ``SECRET_READ``. The value is not returned; see
        :meth:`get_value`.

        Args:
            secret_id: The secret to read.

        Returns:
            :class:`SecretRead`.

        Raises:
            ValueError: If ``secret_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``SECRET_READ``, ``404``
                (``PerceivoNotFoundError``) for a secret that does not exist,
                was deleted, or belongs to another organization, and ``502`` or
                ``503`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(SecretRead, self._get(f"{_BASE}/{segment(secret_id, 'secret_id')}"))

    def get_value(self, secret_id: str) -> SecretValueRead:
        """Read a secret's value (``GET /infrastructure/secrets/{secret_id}/value``).

        Requires ``SECRET_READ_VALUE``; ``SECRET_READ`` alone is not enough.
        The value is served from the infrastructure secrets route, because
        ``/secrets`` has no value operation. The response is sent with
        ``Cache-Control: no-store``: do not log or persist the returned value.

        Args:
            secret_id: The secret whose value to read.

        Returns:
            :class:`SecretValueRead` — ``value`` and ``expires_at``.

        Raises:
            ValueError: If ``secret_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``SECRET_READ_VALUE``,
                ``404`` (``PerceivoNotFoundError``) for a secret that does not
                exist or belongs to another organization (the two cannot be
                told apart), ``410`` for an expired secret, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SecretValueRead, self._get(_VALUE.format(secret_id=segment(secret_id, "secret_id")))
        )

    def update(self, secret_id: str, body: dict[str, Any]) -> SecretRead:
        """Change a secret (``PATCH /secrets/{secret_id}``).

        ``body`` is a ``SecretUpdate``: any of ``name``, ``description``,
        ``expiration_date`` and ``value``. Requires ``SECRET_UPDATE``.

        Args:
            secret_id: The secret to change.
            body: A ``SecretUpdate`` object, sent as the JSON body.

        Returns:
            :class:`SecretRead` — the secret's metadata after the change.

        Raises:
            ValueError: If ``secret_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``SECRET_UPDATE``, for an
                expiry that is not in the future, or when the value could not
                be stored, ``404`` (``PerceivoNotFoundError``) for a secret that
                does not exist or belongs to another organization, ``422``
                (``PerceivoValidationError``) for a malformed field, and ``502``
                or ``503`` (``PerceivoServerError``) when the platform did not
                answer: read the secret before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SecretRead, self._patch(f"{_BASE}/{segment(secret_id, 'secret_id')}", json=body)
        )

    def rotate(self, secret_id: str, body: dict[str, Any]) -> SecretRead:
        """Replace a secret's value (``POST /secrets/{secret_id}/rotate``).

        ``body`` is a ``SecretRotate``: ``{"value": "<new value>"}``, required
        and non-empty. Rotation changes neither the expiry nor the status: an
        expired secret stays expired. Requires ``SECRET_UPDATE``.

        Args:
            secret_id: The secret to rotate.
            body: A ``SecretRotate`` object, sent as the JSON body.

        Returns:
            :class:`SecretRead` — the secret's metadata after the rotation.

        Raises:
            ValueError: If ``secret_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``SECRET_UPDATE`` or when
                the value could not be stored, ``404``
                (``PerceivoNotFoundError``) for a secret that does not exist or
                belongs to another organization, ``422``
                (``PerceivoValidationError``) for an empty ``value`` or an
                extra field, and ``502`` or ``503`` (``PerceivoServerError``)
                when the platform did not answer: the rotation may have landed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SecretRead,
            self._post(f"{_BASE}/{segment(secret_id, 'secret_id')}/rotate", json=body),
        )

    def delete(self, secret_id: str) -> None:
        """Delete a secret (``DELETE /secrets/{secret_id}``, ``204``).

        Requires ``SECRET_DELETE``.

        Args:
            secret_id: The secret to delete.

        Raises:
            ValueError: If ``secret_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``SECRET_DELETE``,
                ``404`` (``PerceivoNotFoundError``) for a secret that does not
                exist, was already deleted, or belongs to another organization,
                and ``502`` or ``503`` (``PerceivoServerError``) when the
                platform did not answer: read the secret before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(secret_id, 'secret_id')}")
