"""Reviews namespace (``client.reviews``).

Human-in-the-loop review requests raised by REVIEW nodes: list, inspect,
update, claim, assign, save a draft of, complete and cancel them.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from perceivo_client._paths import segment
from perceivo_client.generated.models import PaginatedItemsResponse, ReviewRead
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/reviews"


class ReviewCompletion(BaseModel):
    """The answer to :meth:`ReviewsResource.complete`.

    Completing a review answers with the completed review and whether the
    completion released the run the review had parked, not with a bare review
    record.

    Attributes:
        review_request: The completed review.
        ready_to_resume: ``True`` when this completion released the parked run.
        workload_id: The workload that was resumed; ``None`` when
            ``ready_to_resume`` is ``False``.
        workload_user_sub: The identity the resumed workload runs as; ``None``
            when nothing was resumed.
        workload_orchestration_id: The orchestration of the resumed workload;
            ``None`` when nothing was resumed.
    """

    model_config = ConfigDict(extra="allow")

    review_request: ReviewRead
    ready_to_resume: bool = False
    workload_id: str | None = None
    workload_user_sub: str | None = None
    workload_orchestration_id: str | None = None


class ReviewsResource(BaseResource):
    """List, inspect, update, claim, assign, complete and cancel review requests."""

    def list(self, **params: Any) -> PaginatedItemsResponse:
        """List the reviews visible to the caller (``GET /reviews``).

        A key sees the reviews assigned to it, completed by it, or assigned to
        a group it belongs to; a key with ``ORG_MANAGE_MEMBERS`` sees
        every review of its organization. Requires ``REVIEW_READ``.

        Args:
            **params: Query parameters: ``status``, ``capability_id``, ``page``
                (default ``1``) and ``page_size`` (default ``25``, at most
                ``100``). ``sort_by`` and ``sort_order`` are accepted and
                ignored: reviews come newest first.

        Returns:
            :class:`PaginatedItemsResponse` — one ``items``/``total`` page of
            review records. :func:`perceivo_client.paginate_pages` walks it.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``REVIEW_READ``, ``422``
                (``PerceivoValidationError``) for a malformed query, and ``502``
                (``PerceivoServerError``) when the platform did not answer;
                nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(PaginatedItemsResponse, self._get(_BASE, params=params or None))

    def get(self, review_id: str) -> ReviewRead:
        """Read one review (``GET /reviews/{review_id}``).

        Args:
            review_id: The review to read.

        Returns:
            :class:`ReviewRead`.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller that is neither the
                assignee nor holds ``REVIEW_READ``, ``404``
                (``PerceivoNotFoundError``) for a review that does not exist or
                that the caller may not see, ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``)
                when the platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ReviewRead, self._get(f"{_BASE}/{segment(review_id, 'review_id')}"))

    def update(self, review_id: str, body: dict[str, Any]) -> ReviewRead:
        """Change a review in place (``PATCH /reviews/{review_id}``).

        ``body`` is a ``ReviewPatch``. Changing the assignee requires
        ``assignment_type`` and, like :meth:`assign`, returns the review to
        pending and discards an in-progress claim. Requires control of the
        reviewed asset or ``REVIEW_ADMIN``.

        Args:
            review_id: The review to change.
            body: A ``ReviewPatch`` object, sent as the JSON body.

        Returns:
            :class:`ReviewRead` — the review after the change.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` for an assignee
                change without ``assignment_type``, ``403``
                (``PerceivoGrantError``) for a caller without authority,
                ``404`` (``PerceivoNotFoundError``) for a review the caller may
                not see, ``409`` (``PerceivoConflictError``) for an empty body,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the review before retrying, because the change may
                have been applied.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ReviewRead, self._patch(f"{_BASE}/{segment(review_id, 'review_id')}", json=body)
        )

    def start(self, review_id: str) -> ReviewRead:
        """Claim a review as the calling credential (``POST /reviews/{review_id}/start``).

        Moves a pending review to in-progress and records the caller as its
        reviewer. A review in any other status is returned unchanged. Claiming
        does not reassign the review: one assigned to someone else stays
        completable only by its assignee. Requires ``REVIEW_PERFORM``.

        Args:
            review_id: The review to claim.

        Returns:
            :class:`ReviewRead` — the claimed review.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``REVIEW_PERFORM``,
                ``404`` (``PerceivoNotFoundError``) for a review the caller may
                not see, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when the
                platform did not answer: read the review before retrying.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ReviewRead, self._post(f"{_BASE}/{segment(review_id, 'review_id')}/start")
        )

    def complete(self, review_id: str, body: dict[str, Any]) -> ReviewCompletion:
        """Answer a review and resume its run (``POST /reviews/{review_id}/complete``).

        ``body`` is a ``ReviewComplete``: ``{"response_data": {...}}``, the
        answers keyed by the question ids of the review's survey. When this is
        the last blocking review of a parked run, the run resumes. Completing
        again with the same answers is safe and retries a failed resume.

        Args:
            review_id: The review to complete.
            body: A ``ReviewComplete`` object, sent as the JSON body.

        Returns:
            :class:`ReviewCompletion` — the completed review
            (``review_request``) and whether the run was released
            (``ready_to_resume``, with the resumed ``workload_id``).

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller that is neither the
                assignee nor holds ``REVIEW_PERFORM``, ``404``
                (``PerceivoNotFoundError``) for a review the caller may not
                see, ``409`` (``PerceivoConflictError``) for a review already
                completed with other answers or not open, ``422``
                (``PerceivoValidationError``) for a malformed body or answers
                the survey refuses (the per-question ``errors`` are in
                ``exc.response.json()``), and ``502`` (``PerceivoServerError``)
                when the answers were saved but the run could not be resumed,
                or the platform did not answer: complete again with the same
                answers.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ReviewCompletion,
            self._post(f"{_BASE}/{segment(review_id, 'review_id')}/complete", json=body),
        )

    def assign(self, review_id: str, body: dict[str, Any]) -> ReviewRead:
        """Hand a review to another user or group (``POST /reviews/{review_id}/assign``).

        ``body`` is a ``ReviewAssign``: ``assignment_type`` and the
        ``assignee_user_sub`` or ``assignee_group_id`` it names. Assigning
        returns the review to pending and discards an in-progress claim.
        Requires ``REVIEW_ADMIN``; being the current assignee is not enough. To
        claim a review for yourself use :meth:`start`.

        Args:
            review_id: The review to reassign.
            body: A ``ReviewAssign`` object, sent as the JSON body.

        Returns:
            :class:`ReviewRead` — the review after the assignment.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``REVIEW_ADMIN``, ``404``
                (``PerceivoNotFoundError``) for a review the caller may not see
                or one that is no longer pending or in progress, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the review before retrying, because the change may
                have been applied.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ReviewRead,
            self._post(f"{_BASE}/{segment(review_id, 'review_id')}/assign", json=body),
        )

    def save_draft(self, review_id: str, body: dict[str, Any]) -> ReviewRead:
        """Save partial answers without submitting (``PUT /reviews/{review_id}/draft``).

        ``body`` is a ``ReviewDraft`` (``draft_data``). Each save replaces the
        whole draft; it does not merge, so send every answer to keep. Saving on
        a pending review moves it to in-progress. A draft neither completes the
        review nor resumes a parked run: :meth:`complete` does both. Requires
        ``REVIEW_PERFORM``.

        Args:
            review_id: The review to save a draft of.
            body: A ``ReviewDraft`` object (``draft_data``), sent as the JSON
                body; it replaces any earlier draft.

        Returns:
            :class:`ReviewRead` — the review with the saved draft.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``REVIEW_PERFORM``,
                ``404`` (``PerceivoNotFoundError``) for a review the caller may
                not see or one that is no longer pending or in progress,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the review before retrying, because the draft may
                have been saved.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ReviewRead,
            self._put(f"{_BASE}/{segment(review_id, 'review_id')}/draft", json=body),
        )

    def cancel(self, review_id: str) -> None:
        """Cancel a pending or in-progress review (``DELETE /reviews/{review_id}``).

        The review is cancelled, not deleted: it stays readable through
        :meth:`get` and :meth:`list`. Cancelling a blocking review does not
        resume the run it parked.

        Args:
            review_id: The review to cancel.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for a caller without authority,
                ``404`` (``PerceivoNotFoundError``) for a review the caller may
                not see (checked before authority), ``409``
                (``PerceivoConflictError``) for a review already in a final
                status, ``422`` (``PerceivoValidationError``) for a malformed
                request, and ``502`` (``PerceivoServerError``) when the
                platform did not answer: read the review before retrying,
                because it may have been cancelled.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(review_id, 'review_id')}")

    def start_and_complete(self, review_id: str, body: dict[str, Any]) -> ReviewCompletion:
        """Claim a review with :meth:`start`, then answer it with :meth:`complete`.

        The two requests are not atomic. If :meth:`start` fails, nothing is
        sent to :meth:`complete` and its error propagates. If :meth:`complete`
        fails, the claim stays in place; call :meth:`complete` again to finish.

        Args:
            review_id: The review to claim and complete.
            body: A ``ReviewComplete`` object, sent as the JSON body of the
                completion.

        Returns:
            :class:`ReviewCompletion` — as :meth:`complete` returns it.

        Raises:
            ValueError: If ``review_id`` is empty, ``.`` or ``..`` (refused
                before any request is sent).
            PerceivoAPIError: On an error response from either request; see
                :meth:`start` and :meth:`complete`.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self.start(review_id)
        return self.complete(review_id, body)
