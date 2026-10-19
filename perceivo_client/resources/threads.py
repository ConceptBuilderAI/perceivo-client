"""Messaging namespace (``client.threads``).

Person-to-person threads inside your organization, on the ``/v1/threads``
routes: open, list, search, read and rename a thread, post and read its
messages, mark it read, and manage who is on it. Every read is limited to the
threads the credential's user is on.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    ThreadListResponse,
    ThreadMessage,
    ThreadMessagesPage,
    ThreadParticipant,
    ThreadRead,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/threads"


class ThreadsResource(BaseResource):
    """Open threads, exchange messages and manage participants."""

    def list(self, **params: Any) -> ThreadListResponse:
        """List the threads you are on, most recently active first (``GET /threads``).

        The page is ``data``/``page``/``page_size``/``total``/``next``, not
        ``items``, so :func:`perceivo_client.paginate_pages` does not walk it:
        pass ``page=n`` until ``next`` is ``None``.

        Args:
            **params: Query parameters: ``page`` (default ``1``) and
                ``page_size`` (default ``25``, at most ``100``).

        Returns:
            :class:`ThreadListResponse` — one ``data``/``total``/``next`` page.

        Raises:
            PerceivoAPIError: On an error response: ``422``
                (``PerceivoValidationError``) for a malformed request, such as a
                ``page_size`` over 100, and ``502`` (``PerceivoServerError``)
                when the platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ThreadListResponse, self._get(_BASE, params=params or None))

    def search(self, q: str, **params: Any) -> ThreadListResponse:
        """Find threads whose title or any message matches ``q`` (``GET /threads/search``).

        Answers the same page as :meth:`list`.

        Args:
            q: The search text, 1 to 200 characters, sent as the ``q`` query
                parameter.
            **params: Further query parameters: ``page`` (default ``1``) and
                ``page_size`` (default ``25``, at most ``100``).

        Returns:
            :class:`ThreadListResponse` — one ``data``/``total``/``next`` page.

        Raises:
            PerceivoAPIError: On an error response: ``422``
                (``PerceivoValidationError``) for a malformed request, such as a
                ``q`` outside 1 to 200 characters, and ``502``
                (``PerceivoServerError``) when the platform did not answer;
                nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ThreadListResponse, self._get(f"{_BASE}/search", params={**params, "q": q})
        )

    def create(self, body: dict[str, Any]) -> ThreadRead:
        """Open a thread (``POST /threads``, ``201``).

        ``body`` is a ``ThreadCreate``: ``participant_user_ids`` and an
        optional ``title``. You are added automatically. Opening a thread with
        exactly one other person returns the existing direct thread if there is
        one.

        Args:
            body: A ``ThreadCreate`` object, sent as the JSON body.

        Returns:
            :class:`ThreadRead` — the new thread, or the existing direct one.

        Raises:
            PerceivoAPIError: On an error response: ``400`` when
                ``participant_user_ids`` names nobody but you, an unknown
                person, or someone who is not a current member of your
                organization, ``422`` (``PerceivoValidationError``) for a
                malformed request, and ``502`` (``PerceivoServerError``) when
                the platform did not answer: list your threads before
                retrying, because the thread may have been opened.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ThreadRead, self._post(_BASE, json=body))

    def get(self, thread_id: str) -> ThreadRead:
        """Read one thread, its participants and its latest message (``GET /threads/{thread_id}``).

        Args:
            thread_id: The thread to read.

        Returns:
            :class:`ThreadRead`.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a thread that does not exist or
                that you are not on, ``422`` (``PerceivoValidationError``) for
                a malformed request, and ``502`` (``PerceivoServerError``) when
                the platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(ThreadRead, self._get(f"{_BASE}/{segment(thread_id, 'thread_id')}"))

    def update(self, thread_id: str, body: dict[str, Any]) -> ThreadRead:
        """Rename a thread you are on (``PATCH /threads/{thread_id}``).

        Args:
            thread_id: The thread to rename.
            body: A ``ThreadUpdate`` object (``title``), sent as the JSON body.

        Returns:
            :class:`ThreadRead` — the thread after the update.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a thread you are not on,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the thread before retrying, because the change may
                have been applied.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ThreadRead, self._patch(f"{_BASE}/{segment(thread_id, 'thread_id')}", json=body)
        )

    def delete(self, thread_id: str) -> None:
        """Delete a thread with its messages and participants (``DELETE /threads/{thread_id}``).

        The owner may delete the thread. Once no owner is a current member of
        the thread's organization, any remaining participant may delete it
        too. Irreversible.

        Args:
            thread_id: The thread to delete.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a thread that does not exist or
                that you may not delete (you are not the owner and an owner is
                still a member of the organization), ``422`` (``PerceivoValidationError``)
                for a malformed request, and ``502`` (``PerceivoServerError``)
                when the platform did not answer: read the thread before
                retrying, because it may have been deleted.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._delete(f"{_BASE}/{segment(thread_id, 'thread_id')}")

    def acknowledge(self, thread_id: str) -> None:
        """Mark everything in a thread as read for you (``POST /threads/{thread_id}/acknowledge``).

        Clears your unread count and nobody else's. No request body is sent and
        none is returned.

        Args:
            thread_id: The thread to mark as read.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a thread you are not on,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer; the thread may already be marked read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        self._post(f"{_BASE}/{segment(thread_id, 'thread_id')}/acknowledge")

    def list_messages(self, thread_id: str, **params: Any) -> ThreadMessagesPage:
        """Read a window of a thread's messages, oldest first (``GET /threads/{thread_id}/messages``).

        Page backwards by passing the ``created_at`` of the oldest message you
        hold as ``before`` while ``has_more`` is true.

        Args:
            thread_id: The thread to read.
            **params: Query parameters: ``limit`` (default ``50``, at most
                ``100``) and ``before`` (an ISO-8601 timestamp; omitted, the
                newest window).

        Returns:
            :class:`ThreadMessagesPage` — the messages and ``has_more``.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when ``before``
                is not an ISO-8601 timestamp, ``404``
                (``PerceivoNotFoundError``) for a thread you are not on,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ThreadMessagesPage,
            self._get(f"{_BASE}/{segment(thread_id, 'thread_id')}/messages", params=params or None),
        )

    def create_message(self, thread_id: str, body: dict[str, Any]) -> ThreadMessage:
        """Post a message into a thread you are on (``POST /threads/{thread_id}/messages``, ``201``).

        ``body`` is a ``ThreadMessageCreate`` (``body``, optional
        ``metadata``). The sender is taken from your credential. Not
        idempotent: a retry posts a second message.

        Args:
            thread_id: The thread to post into.
            body: A ``ThreadMessageCreate`` object, sent as the JSON body.

        Returns:
            :class:`ThreadMessage` — the message as stored.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a thread you are not on,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` (``PerceivoServerError``) when the platform did not
                answer: read the thread's messages before retrying, because the
                message may have been posted.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ThreadMessage,
            self._post(f"{_BASE}/{segment(thread_id, 'thread_id')}/messages", json=body),
        )

    def list_participants(self, thread_id: str) -> list[ThreadParticipant]:
        """List everyone on a thread you are on (``GET /threads/{thread_id}/participants``).

        One request returns every participant; the list is not paged.

        Args:
            thread_id: The thread to read.

        Returns:
            ``list[ThreadParticipant]`` — every participant.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a thread that does not exist or
                that you are not on, ``422`` (``PerceivoValidationError``) for
                a malformed request, and ``502`` (``PerceivoServerError``) when
                the platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ThreadParticipant,
            self._get(f"{_BASE}/{segment(thread_id, 'thread_id')}/participants"),
        )

    def add_participant(self, thread_id: str, body: dict[str, Any]) -> ThreadParticipant:
        """Add a person to a group thread (``POST /threads/{thread_id}/participants``, ``201``).

        ``body`` is a ``ThreadParticipantAdd`` (``user_id``). A direct thread
        has a fixed pair and takes no third person.

        Args:
            thread_id: The group thread to add to.
            body: A ``ThreadParticipantAdd`` object, sent as the JSON body.

        Returns:
            :class:`ThreadParticipant` — the added participant.

        Raises:
            ValueError: If ``thread_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a direct thread, a thread you
                are not on, or an unknown person, ``409``
                (``PerceivoConflictError``) when the person is already on the
                thread (nothing is changed), ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: list the participants before retrying, because the
                person may have been added.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ThreadParticipant,
            self._post(f"{_BASE}/{segment(thread_id, 'thread_id')}/participants", json=body),
        )

    def remove_participant(self, thread_id: str, user_id: str) -> None:
        """Remove a person from a group thread you are on (``DELETE .../participants/{user_id}``).

        Wraps ``DELETE /threads/{thread_id}/participants/{user_id}``. Anyone
        may remove themselves; only the owner may remove somebody else. The
        owner cannot leave: to end the thread, the owner deletes it instead.
        Nobody can be removed from a direct thread.

        Args:
            thread_id: The group thread to remove from.
            user_id: The person to remove.

        Raises:
            ValueError: If ``thread_id`` or ``user_id`` is empty, ``.`` or
                ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a direct thread, a thread you
                are not on, or (when you are not the owner) a person other than
                yourself, ``409`` (``PerceivoConflictError``) when the owner
                tries to remove themselves, ``422``
                (``PerceivoValidationError``) for a malformed request, and ``502`` (``PerceivoServerError``) when
                the platform did not answer: list the participants before
                retrying, because the person may have been removed.
            PerceivoConnectionError: If the API cannot be reached.
        """
        thread = segment(thread_id, "thread_id")
        user = segment(user_id, "user_id")
        self._delete(f"{_BASE}/{thread}/participants/{user}")
