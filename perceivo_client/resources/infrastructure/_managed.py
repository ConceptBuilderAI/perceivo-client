"""Managed (Azure-hosted) services and their backups; dedicated databases.

One of the mixins that make up
:class:`~perceivo_client.resources.infrastructure.InfrastructureResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    BackupListResponse,
    BackupRead,
    DedicatedDatabaseRead,
    DedicatedDatabaseStartAccepted,
    ManagedServiceListResponse,
    ManagedServiceRead,
)
from perceivo_client.resources.infrastructure._common import (
    _BASE,
    _MixinBase,
)


class _ManagedMixin(_MixinBase):
    # -- managed services (service: postgres | redis) -----------------------
    def list_managed_services(self) -> ManagedServiceListResponse:
        """List the organization's managed service instances (``GET /infrastructure/managed``).

        Each item is a projection that withholds connection details and the
        instance id.

        Returns:
            :class:`ManagedServiceListResponse` — ``items`` (one
            :class:`ManagedServiceRead` per instance) and ``total``.

        Raises:
            PerceivoGrantError: For a key without ``INFRA_LIST`` (``403``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ManagedServiceListResponse, self._get(f"{_BASE}/managed"))

    def get_managed_service(self, service: str) -> ManagedServiceRead:
        """Read one managed service instance (``GET /infrastructure/managed/{service}``).

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`ManagedServiceRead` — a projection without connection
            details.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead, self._get(f"{_BASE}/managed/{segment(service, 'service')}")
        )

    def update_managed_service(self, service: str, body: dict[str, Any]) -> ManagedServiceRead:
        """Change a managed service's name, size or shutdown policy (``PATCH .../managed/{service}``).

        Only the fields sent change. A larger ``sku`` is a larger billed
        instance. ``configuration`` is returned verbatim on every read, so do
        not put a credential in it: keep credentials in ``client.secrets``.

        Args:
            service: ``postgres`` or ``redis``.
            body: A ``ManagedServiceUpdate`` object.

        Returns:
            :class:`ManagedServiceRead` — the instance after the change.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a malformed body, or a ``service``
                other than ``postgres`` or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead,
            self._patch(f"{_BASE}/managed/{segment(service, 'service')}", json=body),
        )

    def start_managed_service(self, service: str) -> ManagedServiceRead:
        """Start a stopped managed service (``POST .../managed/{service}/start``).

        Asynchronous, and it resumes billing. The answer acknowledges the
        request even when the start is later refused, so poll
        :meth:`get_managed_service` until ``status`` is ``running``.

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`ManagedServiceRead` — the instance as the request left it.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead, self._post(f"{_BASE}/managed/{segment(service, 'service')}/start")
        )

    def stop_managed_service(self, service: str) -> ManagedServiceRead:
        """Stop a running managed service (``POST .../managed/{service}/stop``).

        Asynchronous: the answer acknowledges the request, so poll
        :meth:`get_managed_service` for ``stopped``.

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`ManagedServiceRead` — the instance as the request left it.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoNotFoundError: For no instance of that service (``404``).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ManagedServiceRead, self._post(f"{_BASE}/managed/{segment(service, 'service')}/stop")
        )

    def list_managed_service_backups(self, service: str) -> BackupListResponse:
        """List a managed service's backups, most recent first (``GET .../managed/{service}/backups``).

        At most the 50 most recent backups are listed.

        Args:
            service: ``postgres`` or ``redis``.

        Returns:
            :class:`BackupListResponse` — ``items`` (one :class:`BackupRead`
            per backup) and ``total``.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoValidationError: For a ``service`` other than ``postgres``
                or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BackupListResponse, self._get(f"{_BASE}/managed/{segment(service, 'service')}/backups")
        )

    def get_managed_service_backup(self, service: str, backup_id: str) -> BackupRead:
        """Read one backup of a managed service (``GET .../managed/{service}/backups/{id}``).

        Only the 50 most recent backups can be read.

        Args:
            service: ``postgres`` or ``redis``.
            backup_id: The backup to read.

        Returns:
            :class:`BackupRead` — the backup and its status.

        Raises:
            ValueError: If ``service`` or ``backup_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoNotFoundError: For a backup that is not among the 50 most
                recent (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BackupRead,
            self._get(
                f"{_BASE}/managed/{segment(service, 'service')}/backups/{segment(backup_id, 'backup_id')}"
            ),
        )

    def create_managed_service_backup(
        self, service: str, body: dict[str, Any] | None = None
    ) -> BackupRead:
        """Record a backup request for a managed service (``POST .../managed/{service}/backups``).

        The API writes a backup record that reports ``in_progress`` and
        answers ``202``. No component of the platform performs the backup, so
        the record is not a backup you can restore from.

        Args:
            service: ``postgres`` or ``redis``.
            body: An optional ``BackupCreate`` object (``backup_type``).
                Omitted, no body is sent and the API's default applies.

        Returns:
            :class:`BackupRead` — the backup record just written.

        Raises:
            ValueError: If ``service`` is empty, ``.`` or ``..`` (refused before
                the request is sent).
            PerceivoValidationError: For a malformed body, or a ``service``
                other than ``postgres`` or ``redis`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            BackupRead,
            self._post(f"{_BASE}/managed/{segment(service, 'service')}/backups", json=body),
        )

    # -- dedicated databases ------------------------------------------------
    def get_database(self, database_id: str) -> DedicatedDatabaseRead:
        """Read one dedicated database (``GET /infrastructure/databases/{database_id}``).

        A projection: host, port, admin user name and default database name
        are withheld.

        Args:
            database_id: The dedicated database to read.

        Returns:
            :class:`DedicatedDatabaseRead` — including its lifecycle
            ``status``.

        Raises:
            ValueError: If ``database_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For a database that does not exist or
                belongs to another organization (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DedicatedDatabaseRead,
            self._get(f"{_BASE}/databases/{segment(database_id, 'database_id')}"),
        )

    def start_database(self, database_id: str) -> DedicatedDatabaseStartAccepted:
        """Start a stopped dedicated database (``POST .../databases/{database_id}/start``).

        Asynchronous (``202``), and it resumes compute billing subject to your
        usage limits: poll :meth:`get_database` until ``status`` is
        ``running``.

        Args:
            database_id: The dedicated database to start.

        Returns:
            :class:`DedicatedDatabaseStartAccepted` — the acknowledgement.

        Raises:
            ValueError: If ``database_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For a database that does not exist or
                belongs to another organization (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            DedicatedDatabaseStartAccepted,
            self._post(f"{_BASE}/databases/{segment(database_id, 'database_id')}/start"),
        )

    def record_database_activity(self, database_id: str) -> None:
        """Reset a dedicated database's idle-shutdown timer (``POST .../databases/{database_id}/activity``).

        Args:
            database_id: The dedicated database to mark as active.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``database_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoNotFoundError: For a database that does not exist or
                belongs to another organization (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._post(f"{_BASE}/databases/{segment(database_id, 'database_id')}/activity")
