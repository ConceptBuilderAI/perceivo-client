"""Auth namespace (``client.auth``): what the presented credential is and may do.

:meth:`AuthResource.whoami` describes the calling credential, and
:meth:`AuthResource.check_privilege` and :meth:`AuthResource.allowed` ask
whether it holds one privilege at organization level.
"""

from __future__ import annotations

from perceivo_client.errors import PerceivoGrantError
from perceivo_client.generated.models import PrivilegeCheckResponse, WhoamiResponse
from perceivo_client.resources._base import BaseResource

_WHOAMI = "/v1/whoami"
_CHECK = "/v1/grants/check"


class AuthResource(BaseResource):
    """Introspect the calling credential."""

    def whoami(self) -> WhoamiResponse:
        """Describe the calling credential (``GET /whoami``).

        The first call to make when a request is refused: it shows which
        organization the key belongs to and what it holds there.

        Returns:
            :class:`WhoamiResponse`: the principal ``type`` and ``id``,
            ``organization_id`` and ``organization_name``, ``roles``,
            ``endpoint_access`` (the key's endpoint-access policy),
            ``effective_privileges`` (organization-level privileges; resource
            grants are not listed) and ``is_admin``.

        Raises:
            PerceivoAPIError: On an error response: ``401``
                (``PerceivoAuthError``) for a credential that does not
                authenticate, and ``502`` (``PerceivoServerError``) when an
                upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(WhoamiResponse, self._get(_WHOAMI))

    def check_privilege(self, privilege: str) -> PrivilegeCheckResponse:
        """Ask whether the caller holds ``privilege`` (``GET /grants/check``).

        The answer is always about the calling credential, and it comes from
        the credential's organization-level privileges. A denial is a ``200``
        with ``allowed`` false, not an error.

        Args:
            privilege: The privilege to check.

        Returns:
            :class:`PrivilegeCheckResponse`: ``allowed`` and ``privileges``,
            the caller's effective privilege list.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``422``
                (``PerceivoValidationError``) for a malformed request and
                ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {"privilege": privilege}
        return self._model(PrivilegeCheckResponse, self._get(_CHECK, params=params))

    def allowed(self, privilege: str) -> bool:
        """Whether the caller holds ``privilege``, as a boolean.

        Calls :meth:`check_privilege` and returns ``True`` only when its
        ``allowed`` is ``True``. A ``403`` (``PerceivoGrantError``) is
        answered ``False``; any other error propagates.

        Args:
            privilege: The privilege to check.

        Returns:
            ``bool``.

        Raises:
            PerceivoAPIError: On an error response other than ``403``: ``422``
                (``PerceivoValidationError``) for a malformed request and
                ``502`` (``PerceivoServerError``) when an upstream service
                fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        try:
            result = self.check_privilege(privilege)
        except PerceivoGrantError:
            return False
        return getattr(result, "allowed", None) is True
