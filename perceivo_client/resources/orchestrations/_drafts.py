"""Drafts and definition validation of ``client.orchestrations``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    OrchestrationDraftPublished,
    OrchestrationDraftRead,
    OrchestrationValidationResult,
)
from perceivo_client.resources.orchestrations._common import _BASE

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object


class _DraftsMixin(_MixinBase):
    """Drafts and definition validation of ``client.orchestrations``."""

    # -- drafts --------------------------------------------------------------
    def list_drafts(self) -> list[OrchestrationDraftRead]:
        """List the caller's orchestration drafts (``GET /orchestrations/drafts``).

        The body is a bare array and the route takes no page parameters.

        Returns:
            ``list[OrchestrationDraftRead]`` — every draft, in one response.

        Raises:
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(OrchestrationDraftRead, self._get(f"{_BASE}/drafts"))

    def create_draft(self, body: dict[str, Any]) -> OrchestrationDraftRead:
        """Open a draft (``POST /orchestrations/drafts``).

        A draft holds graph and runtime changes until :meth:`publish_draft`
        turns it into the next version.

        Args:
            body: An ``OrchestrationDraftCreate`` object, sent as the JSON body.
                Include ``canvas_state``: the API refuses a draft without it.
                At most 16 MiB.

        Returns:
            :class:`OrchestrationDraftRead` — the new draft.

        Raises:
            PerceivoAPIError: On an error response. The route declares ``413``
                (``PerceivoAPIError``) for a body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(OrchestrationDraftRead, self._post(f"{_BASE}/drafts", json=body))

    def get_draft(self, draft_id: str) -> OrchestrationDraftRead:
        """Read one draft (``GET /orchestrations/drafts/{draft_id}``).

        Args:
            draft_id: The draft to read.

        Returns:
            :class:`OrchestrationDraftRead`.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationDraftRead, self._get(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}")
        )

    def update_draft(self, draft_id: str, body: dict[str, Any]) -> OrchestrationDraftRead:
        """Change a draft (``PATCH /orchestrations/drafts/{draft_id}``).

        ``OrchestrationDraftUpdate`` body. This is how an orchestration's graph
        and runtime settings change: save them in a draft, then
        :meth:`publish_draft`.

        Args:
            draft_id: The draft to update.
            body: An ``OrchestrationDraftUpdate`` object; only the fields it
                carries change.

        Returns:
            :class:`OrchestrationDraftRead` — the draft after the update.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``413``
                (``PerceivoAPIError``) for a body over 16 MiB, and ``422``
                (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationDraftRead,
            self._patch(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}", json=body),
        )

    def delete_draft(self, draft_id: str) -> None:
        """Discard a draft (``DELETE /orchestrations/drafts/{draft_id}``, ``204``).

        Args:
            draft_id: The draft to discard.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}")

    def publish_draft(self, draft_id: str, body: dict[str, Any]) -> OrchestrationDraftPublished:
        """Publish a draft as the next version (``POST .../drafts/{draft_id}/publish``).

        Calls ``POST /orchestrations/drafts/{draft_id}/publish``.

        ``body`` is an ``OrchestrationDraftPublish``; ``expected_base_version_id``
        is required and a mismatch answers ``409``. On success the draft is
        deleted and the result names the new version's ``orchestration_id``.
        The reason for a ``409`` or ``422`` is in the error's
        ``details["error_code"]``, not its top-level ``code``. A failure after
        the version was committed can still be reported as an error: before
        publishing again, check :meth:`get_lineage` for the new version.

        Args:
            draft_id: The draft to publish.
            body: An ``OrchestrationDraftPublish`` object, sent as the JSON body.

        Returns:
            :class:`OrchestrationDraftPublished` — names the new version.

        Raises:
            ValueError: If ``draft_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoConflictError: With ``details["error_code"]``
                ``DRAFT_BASE_STALE``, ``LINEAGE_VERSION_CONFLICT``,
                ``DRAFT_NOT_LINEAGE_BOUND`` or ``DRAFT_PAYLOAD_MISSING``
                (``409``).
            PerceivoValidationError: With ``details["error_code"]``
                ``ORCHESTRATION_INVALID`` or ``STAGED_CHANGE_TARGET_MISSING``,
                or for a malformed request (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationDraftPublished,
            self._post(f"{_BASE}/drafts/{segment(draft_id, 'draft_id')}/publish", json=body),
        )

    # -- definition and capability -------------------------------------------
    def validate(self, body: dict[str, Any]) -> OrchestrationValidationResult:
        """Validate a definition without creating anything (``POST /orchestrations/validate``).

        An invalid definition is not an error: the answer is ``200`` with
        ``valid: false`` and the reasons.

        Args:
            body: An ``OrchestrationDefinitionValidate`` object (the definition
                to check), sent as the JSON body.

        Returns:
            :class:`OrchestrationValidationResult` — read ``valid`` and the
            reasons.

        Raises:
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
                An invalid definition is not an error.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            OrchestrationValidationResult, self._post(f"{_BASE}/validate", json=body)
        )
