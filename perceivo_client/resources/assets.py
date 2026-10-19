"""Assets namespace (``client.assets``): operations on an asset of any type.

Copy an asset, export it as a portable bundle, create an asset from a bundle,
and restore a soft-deleted asset. Access to an asset is managed through
``client.grants``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import AssetRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/assets"


class AssetsResource(BaseResource):
    """Copy, export, import and restore assets of any type."""

    def copy(self, asset_id: str, body: dict[str, Any] | None = None) -> AssetRead:
        """Copy an asset you can read into one you own (``POST /assets/{asset_id}/copy``).

        This is how a shared, read-only platform template becomes an asset you
        can update and run. ``body`` is an optional ``AssetCopyRequest``
        (``new_name``, ``organization_id``); omitted, an empty object is sent.
        A credential that reaches more than one organization must name the
        destination, or the API answers ``400``. The copy starts a new lineage.

        Copying needs the asset type's read and create privileges on a source in
        your organization, plus its create privilege in the destination (for an
        orchestration, ``ORCHESTRATION_READ`` and ``ORCHESTRATION_CREATE``). A
        platform template needs only the create privilege in the destination.

        Args:
            asset_id: The asset to copy.
            body: An optional ``AssetCopyRequest``; omitted, ``{}`` is sent.

        Returns:
            :class:`AssetRead`: the new copy.

        Raises:
            ValueError: If ``asset_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``400`` when a credential
                that reaches more than one organization names no destination, ``403``
                (``PerceivoGrantError``) without the privileges above, ``404``
                (``PerceivoNotFoundError``) for an asset that does not exist or belongs to another
                organization, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetRead, self._post(f"{_BASE}/{segment(asset_id, 'asset_id')}/copy", json=body or {})
        )

    def export_bundle(self, asset_id: str) -> dict[str, Any]:
        """Export an asset as a portable bundle (``GET /assets/{asset_id}/export``).

        The contract declares no model for the bundle: its shape follows the
        asset's ``export_type``, so the JSON object is returned as a ``dict``.
        :meth:`import_bundle` accepts it unchanged as ``bundle``. Secrets
        cannot be exported: exporting one is refused with ``403``.

        Args:
            asset_id: The asset to export.

        Returns:
            ``dict[str, Any]``: the bundle, passed through unvalidated.

        Raises:
            ValueError: If ``asset_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for an asset that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._get(f"{_BASE}/{segment(asset_id, 'asset_id')}/export")

    def import_bundle(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create an asset from a bundle (``POST /assets/import``).

        ``body`` is an ``AssetImportRequest``: ``bundle`` (what
        :meth:`export_bundle` returned) is required and ``organization_id``
        names the destination when the credential reaches more than one.
        Any organization named inside the bundle is ignored. The response shape
        follows the bundle's ``export_type`` and the contract declares no model
        for it, so the JSON object is returned as a ``dict``. Bodies above
        16 MiB are refused with ``413``.

        Args:
            body: An ``AssetImportRequest`` object, sent as the JSON body.

        Returns:
            ``dict[str, Any]``: the created asset, passed through unvalidated.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``400`` for a bundle the API
                refuses, ``413`` for a request body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._post(f"{_BASE}/import", json=body)

    def restore(self, asset_id: str) -> AssetRead:
        """Return a soft-deleted asset to active use (``POST /assets/{asset_id}/restore``).

        Restoring an active asset succeeds and returns it unchanged, so a retry
        is safe. Only assets your organization owns can be restored.

        Args:
            asset_id: The asset to restore.

        Returns:
            :class:`AssetRead`: the asset, active.

        Raises:
            ValueError: If ``asset_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for an asset that does not exist or belongs to another
                organization, ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetRead, self._post(f"{_BASE}/{segment(asset_id, 'asset_id')}/restore")
        )
