"""Components namespace (``client.components``).

Create, read, change and delete components; validate a definition before
saving it; export a component as a self-contained document and import it into
another organization; read and replace its script; find what uses it; run it on
its own; and work with its version lineage.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    ComponentDetailRead,
    ComponentExportDocument,
    ComponentImportResult,
    ComponentRead,
    ComponentRunResult,
    ComponentUpdateResult,
    ComponentUsageReport,
    ComponentValidationReport,
    LineageRestoreResult,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/components"


class ComponentsResource(BaseResource):
    """Author, validate, move and run components."""

    def list(self, *, page: int | None = None, page_size: int | None = None) -> list[ComponentRead]:
        """One page of the organization's components (``GET /components``).

        The newest version of each component the key may read, newest first.
        Each row is the full record, script included, and the record's other
        fields are kept as extra attributes. The page is a bare array with no
        total: request the next ``page`` until one holds fewer than
        ``page_size`` items.

        Args:
            page: Page number from ``1``. Omitted, the API answers page ``1``.
            page_size: Rows per page, ``1`` to ``100``. Omitted, the API uses
                ``25``.

        Returns:
            ``list[ComponentRead]``: one page of components.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``COMPONENT_LIST``, ``422``
                (``PerceivoValidationError``) for a ``page`` or ``page_size``
                out of range, and ``502`` (``PerceivoServerError``) when an
                upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ComponentRead, self._get(_BASE, params={"page": page, "page_size": page_size})
        )

    def create(self, body: dict[str, Any]) -> ComponentRead:
        """Create a component, version 1 (``POST /components``).

        The key is granted ``COMPONENT_EXECUTE`` on the new component. A ``502``
        with ``create_grant_failed`` means the component was created but the
        grant was not.

        Args:
            body: A ``ComponentCreate`` object, sent as the JSON body.

        Returns:
            :class:`ComponentRead`: the new component.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``COMPONENT_CREATE``, ``422``
                (``PerceivoValidationError``) for a malformed body, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ComponentRead, self._post(_BASE, json=body))

    def get(self, component_id: str) -> ComponentRead:
        """One component version (``GET /components/{component_id}``).

        Args:
            component_id: The component version to read.

        Returns:
            :class:`ComponentRead`; the record's other fields (``script``,
            ``ports`` and the rest) are kept as extra attributes.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) or ``404``
                (``PerceivoNotFoundError``) for a component the key cannot
                read, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when an upstream
                service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ComponentRead, self._get(f"{_BASE}/{segment(component_id, 'component_id')}")
        )

    def update(self, component_id: str, body: dict[str, Any]) -> ComponentUpdateResult:
        """Change a component by creating a new version (``PATCH /components/{component_id}``).

        Components are immutable: a change to an orchestration component
        creates a new version with a new ``id`` and ``version_created`` true,
        and ``component_id`` keeps naming the previous version, unchanged. Use
        the returned ``id`` from then on. Only the latest version can be
        changed. Omitted fields are carried forward.

        Args:
            component_id: The latest version of the component.
            body: A ``ComponentUpdate`` object, sent as the JSON body.

        Returns:
            :class:`ComponentUpdateResult`: the resulting version, with
            ``version_created``.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` for a script or
                manifest that fails validation, ``403``
                (``PerceivoGrantError``) or ``404``
                (``PerceivoNotFoundError``) for a component the key cannot
                edit, ``409`` (``PerceivoConflictError``) for a version that is
                not the latest (``details.latest_version_id`` names it) or a
                template, ``422`` (``PerceivoValidationError``) for a malformed
                body, and ``502`` (``PerceivoServerError``) when an upstream
                service fails, in which case a version may have been created.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ComponentUpdateResult,
            self._patch(f"{_BASE}/{segment(component_id, 'component_id')}", json=body),
        )

    def delete(self, component_id: str) -> None:
        """Soft-delete every live version of a lineage (``DELETE /components/{component_id}``).

        :meth:`restore` undoes it. If any version is used by a live
        orchestration, nothing is deleted; :meth:`get_dependents` finds the
        users.

        Args:
            component_id: Any version of the lineage.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) or ``404``
                (``PerceivoNotFoundError``) for a lineage the key cannot
                delete, ``409`` (``PerceivoConflictError``, ``ENTITY_LOCKED``,
                with ``details.blocking_version_ids``) while a version is in
                use, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when an upstream
                service fails, in which case the delete may have happened.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(f"{_BASE}/{segment(component_id, 'component_id')}")

    def validate(self, body: dict[str, Any]) -> ComponentValidationReport:
        """Check an unsaved definition (``POST /components/validate``).

        Nothing is saved. An invalid definition is a ``200`` with ``valid``
        false and the findings in the report, not an error.

        Args:
            body: A ``ComponentDefinitionValidate`` object: ``component_type``
                and ``script`` are required; ``manifest_yaml``, ``contract``,
                ``ports`` and ``validation_profile`` (``quick`` or ``full``,
                the default) are optional.

        Returns:
            :class:`ComponentValidationReport`.

        Raises:
            PerceivoAPIError: On an error response: ``422``
                (``PerceivoValidationError``) for a malformed body, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ComponentValidationReport, self._post(f"{_BASE}/validate", json=body))

    def export_bundle(self, component_id: str) -> ComponentExportDocument:
        """Export a component as a self-contained document (``GET .../export``).

        Calls ``GET /components/{component_id}/export``. The document carries
        the definition, script, ports and state-machine states;
        :meth:`import_bundle` accepts it unchanged.

        Args:
            component_id: The component version to export.

        Returns:
            :class:`ComponentExportDocument`.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a component the key cannot
                read, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when an upstream
                service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ComponentExportDocument,
            self._get(f"{_BASE}/{segment(component_id, 'component_id')}/export"),
        )

    def import_bundle(self, body: dict[str, Any]) -> ComponentImportResult:
        """Create a component from an export document (``POST /components/import``).

        The component is created in the key's organization. The body may not
        name an organization, and only ``export_type`` ``component`` is
        accepted; orchestration and intelligence bundles go through
        ``client.assets.import_bundle``.

        Args:
            body: A ``ComponentImportBody``: the document
                :meth:`export_bundle` returned (``component`` is required),
                optionally with ``new_name``. Any other field is refused.

        Returns:
            :class:`ComponentImportResult`: ``asset_id`` names the new
            component.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``COMPONENT_CREATE``, ``413``
                for a body over 16 MiB, ``422`` (``PerceivoValidationError``)
                for a field the API refuses, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ComponentImportResult, self._post(f"{_BASE}/import", json=body))

    # -- script artifact -----------------------------------------------------
    def get_artifact(self, component_id: str) -> str:
        """The component's current script, as text (``GET /components/{component_id}/artifact``).

        The route answers ``text/plain``; the body is returned verbatim rather
        than decoded as JSON, so a script that happens to parse as JSON still
        comes back as the string it is.

        Args:
            component_id: The component (version) whose script to read.

        Returns:
            ``str``: the script source, exactly as the API sent it.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a component of another organization, one that does
                not exist, or one the key lacks ``COMPONENT_READ`` on, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        response = self._t.request(
            "GET", f"{_BASE}/{segment(component_id, 'component_id')}/artifact"
        )
        return response.text

    def replace_artifact(self, component_id: str, body: dict[str, Any]) -> ComponentDetailRead:
        """Replace the script, and optionally the manifest.

        Calls ``PUT /components/{component_id}/artifact``.

        ``body`` is a ``ComponentArtifactReplace``: ``script`` is required and
        an omitted ``manifest_yaml`` carries the current manifest forward.
        Components are immutable, so this creates a **new version with a new
        id**: keep the ``id`` on the result. ``component_id`` still names the
        previous version, which is left intact.

        Args:
            component_id: The component version to derive the new version from.
            body: A ``ComponentArtifactReplace`` object, sent as the JSON body.

        Returns:
            :class:`ComponentDetailRead`: the **new** version, with its new ``id``.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a component of another organization, one that does
                not exist, or one the key may not edit, and ``422`` (``PerceivoValidationError``)
                for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ComponentDetailRead,
            self._put(f"{_BASE}/{segment(component_id, 'component_id')}/artifact", json=body),
        )

    # -- usage and execution -------------------------------------------------
    def get_dependents(self, component_id: str) -> ComponentUsageReport:
        """What uses this component (``GET /components/{component_id}/dependents``).

        Args:
            component_id: The component to look up.

        Returns:
            :class:`ComponentUsageReport`: the assets that reference it.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a component of another organization, one that does
                not exist, or one the key lacks ``COMPONENT_READ`` on, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502``
                (``PerceivoServerError``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ComponentUsageReport,
            self._get(f"{_BASE}/{segment(component_id, 'component_id')}/dependents"),
        )

    def run(self, component_id: str, body: dict[str, Any]) -> ComponentRunResult:
        """Execute one component in isolation (``POST /components/{component_id}/run``).

        ``body`` is a ``ComponentRunRequest`` (``request_data`` and an optional
        ``artifact``). The run is synchronous and creates no run record: keep
        the result. A script that raises is ``success: false`` with the reason
        in ``errors`` and still a ``200``.

        Args:
            component_id: The component to execute.
            body: A ``ComponentRunRequest`` object, sent as the JSON body.

        Returns:
            :class:`ComponentRunResult`: read ``success`` and ``errors``; a
            returned result does not mean the script succeeded.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a component of another organization or one that does
                not exist, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ComponentRunResult,
            self._post(f"{_BASE}/{segment(component_id, 'component_id')}/run", json=body),
        )

    # -- lineage and versions ------------------------------------------------
    def get_lineage(self, component_id: str) -> AssetLineageRead:
        """The component's version lineage (``GET /components/{component_id}/lineage``).

        Args:
            component_id: Any version of the component.

        Returns:
            :class:`AssetLineageRead`: the versions of the lineage.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) or ``403`` (``PerceivoGrantError``) for an id that
                names no component the caller can read, ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetLineageRead, self._get(f"{_BASE}/{segment(component_id, 'component_id')}/lineage")
        )

    def delete_version(self, component_id: str, version_id: str) -> None:
        """Soft-delete one version of the lineage.

        Calls ``DELETE /components/{component_id}/versions/{version_id}``.
        :meth:`restore` undoes the most recent deletion.

        Args:
            component_id: Any version of the component's lineage.
            version_id: The version to soft-delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``component_id`` or ``version_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a version that is not live, not in
                the lineage, or not deletable by the caller, ``409``
                (``PerceivoConflictError``, ``ENTITY_LOCKED``, with
                ``details.usage`` and ``details.blocked_field``) for a version
                still in use, ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when an
                upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(component_id, 'component_id')}/versions/{segment(version_id, 'version_id')}"
        )

    def restore(self, component_id: str) -> LineageRestoreResult:
        """Undo the lineage's most recent deletion (``POST /components/{component_id}/restore``).

        Args:
            component_id: Any version of the component's lineage.

        Returns:
            :class:`LineageRestoreResult`: what was restored.

        Raises:
            ValueError: If ``component_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) when any version is not restorable by the caller
                (needs ``COMPONENT_UPDATE``), ``404`` (``PerceivoNotFoundError``) for a lineage with
                nothing deleted or one the caller cannot see, ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``) when an upstream
                service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LineageRestoreResult,
            self._post(f"{_BASE}/{segment(component_id, 'component_id')}/restore"),
        )
