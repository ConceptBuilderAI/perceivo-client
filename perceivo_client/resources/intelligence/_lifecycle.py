"""Create, read, change and delete an intelligence; export, import, lineage, versions and restore; service-secret bindings.

One of the mixins that make up
:class:`~perceivo_client.resources.intelligence.IntelligenceResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    IntelligenceExport,
    IntelligenceImportResult,
    IntelligenceRead,
    IntelligenceUpdateResult,
    LineageRestoreResult,
    PaginatedItemsResponse,
    ServiceSecretRead,
)
from perceivo_client.resources.intelligence._common import _BASE, _MixinBase


class _LifecycleMixin(_MixinBase):
    """The ``client.intelligence`` methods this module's docstring lists."""

    # -- CRUD --------------------------------------------------------------
    def list(
        self, *, page: int | None = None, page_size: int | None = None
    ) -> PaginatedItemsResponse:
        """List the organization's intelligences, newest first (``GET /intelligence``).

        ``paginate_pages`` walks this list.

        Args:
            page: Page number, 1 or more; the server default is ``1``.
            page_size: Items per page, 1 to 100; the server default is ``25``.

        Returns:
            :class:`PaginatedItemsResponse` — ``items`` (one intelligence
            record per item) and ``total``.

        Raises:
            PerceivoValidationError: For an out-of-range ``page`` or
                ``page_size`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"page": page, "page_size": page_size}
        return self._model(PaginatedItemsResponse, self._get(_BASE, params=params))

    def create(self, body: dict[str, Any]) -> IntelligenceRead:
        """Create an intelligence (``POST /intelligence``).

        Each call creates another intelligence. Nothing runs, and nothing is
        billed, until :meth:`start`.

        Args:
            body: An ``IntelligenceCreate`` object: ``name`` (3 to 100
                characters) is required; ``config`` names the services and
                compute.

        Returns:
            :class:`IntelligenceRead` — the new intelligence (``201``).

        Raises:
            PerceivoGrantError: For a key without ``INTELLIGENCE_CREATE`` on the
                organization (``403``).
            PerceivoValidationError: For a malformed body (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(IntelligenceRead, self._post(_BASE, json=body))

    def get(self, intelligence_id: str) -> IntelligenceRead:
        """Read one intelligence (``GET /intelligence/{intelligence_id}``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`IntelligenceRead`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence that is absent, deleted
                or another organization's (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceRead, self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}")
        )

    def update(self, intelligence_id: str, body: dict[str, Any]) -> IntelligenceUpdateResult:
        """Change an intelligence (``PATCH /intelligence/{intelligence_id}``).

        Only the fields sent change. A compute change is applied to running
        services.

        Args:
            intelligence_id: The intelligence to change.
            body: An ``IntelligenceUpdate`` object.

        Returns:
            :class:`IntelligenceUpdateResult` — the record and
            ``version_created``. Follow its ``id``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without the update privilege
                (``403``).
            PerceivoNotFoundError: For an intelligence that is absent, deleted
                or another organization's (``404``).
            PerceivoConflictError: For a locked intelligence (``409``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceUpdateResult,
            self._patch(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}", json=body),
        )

    def delete(self, intelligence_id: str) -> None:
        """Delete an intelligence's whole lineage (``DELETE /intelligence/{intelligence_id}``).

        A soft delete, undone by :meth:`restore`. It never stops a runtime: :meth:`stop` it first.

        Args:
            intelligence_id: Any version of the lineage.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: Without the delete privilege, or for a repeated delete (``403``).
            PerceivoNotFoundError: For an absent intelligence or another organization's (``404``).
            PerceivoConflictError: While any live version of the lineage has a runtime whose
                status is not ``STOPPED`` or ``FAILED`` (``409``); nothing is deleted.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}")

    # -- transfer, lineage and versions ------------------------------------
    def export_bundle(self, intelligence_id: str) -> IntelligenceExport:
        """Export an intelligence as a portable document (``GET .../export``).

        Args:
            intelligence_id: The intelligence to export.

        Returns:
            :class:`IntelligenceExport` — the document :meth:`import_bundle`
            accepts.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceExport,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/export"),
        )

    def import_bundle(self, body: dict[str, Any]) -> IntelligenceImportResult:
        """Create an intelligence from an export document (``POST /intelligence/import``).

        The request body is limited to 16 MiB (``413`` above it).

        Args:
            body: The document :meth:`export_bundle` returned, sent as the
                JSON body.

        Returns:
            :class:`IntelligenceImportResult` (``201``).

        Raises:
            PerceivoAPIError: On an error response. The route declares ``413`` for a request body
                over 16 MiB, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(IntelligenceImportResult, self._post(f"{_BASE}/import", json=body))

    def get_lineage(self, intelligence_id: str) -> AssetLineageRead:
        """Read the intelligence's version lineage, newest first (``GET .../lineage``).

        Args:
            intelligence_id: The intelligence to read.

        Returns:
            :class:`AssetLineageRead`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) or ``404`` (``PerceivoNotFoundError``) for an
                identifier that names no intelligence the caller can read (``INTELLIGENCE_READ`` is
                required); ``422`` (``PerceivoValidationError``) for a malformed request; and
                ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            AssetLineageRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/lineage"),
        )

    def delete_version(self, intelligence_id: str, version_id: str) -> None:
        """Soft-delete one version of the lineage (``DELETE .../versions/{version_id}``).

        Args:
            intelligence_id: The intelligence whose lineage holds the version.
            version_id: The version to soft-delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` or ``version_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without the privilege, checked before anything
                is read; ``404`` (``PerceivoNotFoundError``) for a version that is not live or not
                in this lineage; ``409`` (``PerceivoConflictError``) while its runtime is not
                ``STOPPED`` or ``FAILED``; ``422`` (``PerceivoValidationError``) for a malformed
                request; and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/versions/{segment(version_id, 'version_id')}"
        )

    def restore(self, intelligence_id: str) -> LineageRestoreResult:
        """Undo the lineage's most recent deletion (``POST .../restore``).

        No body is sent.

        Args:
            intelligence_id: The intelligence whose lineage is restored.

        Returns:
            :class:`LineageRestoreResult`.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a version the caller cannot restore
                (``INTELLIGENCE_UPDATE`` is required on every version, and the whole call is refused);
                ``404`` (``PerceivoNotFoundError``) for a lineage with nothing deleted, or one the
                caller cannot see; ``422`` (``PerceivoValidationError``) for a malformed request;
                and ``502`` (``PerceivoServerError``) for a failure behind the API.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            LineageRestoreResult,
            self._post(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/restore"),
        )

    # -- service-secret bindings -------------------------------------------
    def list_service_secrets(self, intelligence_id: str) -> list[ServiceSecretRead]:
        """List secret bindings (``GET .../service-secrets``).

        Each binding carries its alias, service type and secret id, never the
        secret's value.

        Args:
            intelligence_id: The intelligence whose bindings are listed.

        Returns:
            ``list[ServiceSecretRead]`` — every binding, in one response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ServiceSecretRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/service-secrets"),
        )

    def attach_service_secret(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> ServiceSecretRead:
        """Bind an organization secret to one service (``POST .../service-secrets``).

        ``body`` is a ``ServiceSecretCreate`` (``service_type``, ``secret_id``,
        ``alias``). Only the secret's id travels, never its value.

        Args:
            intelligence_id: The intelligence to bind the secret to.
            body: A ``ServiceSecretCreate``, sent as the JSON body.

        Returns:
            :class:`ServiceSecretRead` — the binding as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ServiceSecretRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/service-secrets", json=body
            ),
        )

    def detach_service_secret(self, intelligence_id: str, service_type: str, alias: str) -> None:
        """Detach a binding (``DELETE .../service-secrets/{service_type}/{alias}``, ``204``).

        The organization secret itself is kept.

        Args:
            intelligence_id: The intelligence that holds the binding.
            service_type: The service the secret is bound to.
            alias: The binding's alias.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id``, ``service_type`` or ``alias``
                is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/service-secrets/{segment(service_type, 'service_type')}/{segment(alias, 'alias')}"
        )
