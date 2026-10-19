"""Support namespace (``client.support``): your support tickets.

Raise, list, read and amend support tickets under ``/support/tickets``, and
read and add their comments and attachments. A ticket raised with an API key is
raised for the person who created the key.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    SupportAttachmentRead,
    SupportTicketDetail,
    SupportTicketListResponse,
    SupportTicketSummary,
    TicketCommentRead,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/support/tickets"


class SupportResource(BaseResource):
    """Raise and follow support tickets, their comments and their attachments."""

    def list(self, **params: Any) -> SupportTicketListResponse:
        """List the tickets you raised (``GET /support/tickets``).

        Active tickets only by default, ordered by priority and then newest
        first. A key whose creator holds ``SUPPORT_VIEW_ALL`` sees every ticket
        of the organization. Requires ``ORGANIZATION_READ`` on the key, for
        every form of the list, with or without ``filter[ticket_number]``.

        Args:
            **params: Query parameters: ``page`` (default ``1``),
                ``page_size`` (default ``25``, at most ``100``),
                ``filter[status]`` (``active``, the default, ``open``,
                ``resolved``, ``all``, or a comma-separated list of statuses),
                ``filter[ticket_number]`` and ``q`` (a substring of the title or
                description, or a ticket number). Pass the bracketed names
                with ``**{"filter[status]": "all"}``.

        Returns:
            :class:`SupportTicketListResponse` — one ``data``/``total``/``next``
            page; pass ``page=n`` until ``next`` is ``None``.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) when the key lacks
                ``ORGANIZATION_READ``, whatever the filters (nothing was
                read), ``422`` (``PerceivoValidationError``)
                for a malformed query, and ``502`` (``PerceivoServerError``)
                when the platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(SupportTicketListResponse, self._get(_BASE, params=params or None))

    def create(self, body: dict[str, Any]) -> SupportTicketSummary:
        """Raise a support ticket (``POST /support/tickets``, ``201``).

        ``body`` is a ``TicketCreate``: ``title`` and optional
        ``description``, ``ticket_type``, ``priority``, ``category``,
        ``components_affected``, ``tags``, ``customer_email`` and
        ``customer_name``. Not idempotent: a retry raises a second ticket.

        Args:
            body: A ``TicketCreate`` object, sent as the JSON body.

        Returns:
            :class:`SupportTicketSummary` — the new ticket record.

        Raises:
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) for an inactive key or one with no
                creator, ``422`` (``PerceivoValidationError``) for a missing
                ``title`` or a malformed field, and ``502`` or ``503``
                (``PerceivoServerError``) when the platform did not answer:
                list your tickets before retrying, because the ticket may have
                been raised.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(SupportTicketSummary, self._post(_BASE, json=body))

    def get(self, ticket_id: str) -> SupportTicketDetail:
        """Read one ticket with its comments and links (``GET /support/tickets/{ticket_id}``).

        Args:
            ticket_id: The ticket to read.

        Returns:
            :class:`SupportTicketDetail` — the ticket record under ``ticket``,
            at most its first 100 comments, oldest first, under ``comments``,
            and its ``links``. Read every comment with :meth:`list_comments`.

        Raises:
            ValueError: If ``ticket_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ORGANIZATION_READ``,
                ``404`` (``PerceivoNotFoundError``) for a ticket that does not
                exist or that you may not read, ``422``
                (``PerceivoValidationError``) for a malformed id, and ``502``
                or ``503`` (``PerceivoServerError``) when the platform did not
                answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SupportTicketDetail, self._get(f"{_BASE}/{segment(ticket_id, 'ticket_id')}")
        )

    def update(self, ticket_id: str, body: dict[str, Any]) -> SupportTicketSummary:
        """Amend a ticket you raised (``PATCH /support/tickets/{ticket_id}``).

        ``body`` is a ``TicketUpdate``. Only fields sent with a non-null value
        change; ``null`` clears nothing. The status cannot be set here.
        Requires ``ORGANIZATION_UPDATE``.

        Args:
            ticket_id: The ticket to amend.
            body: A ``TicketUpdate`` object, sent as the JSON body.

        Returns:
            :class:`SupportTicketSummary` — the ticket record after the change.

        Raises:
            ValueError: If ``ticket_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``403``
                (``PerceivoGrantError``) without ``ORGANIZATION_UPDATE``,
                ``404`` (``PerceivoNotFoundError``) for a ticket that does not
                exist or that you neither raised nor may see, ``422``
                (``PerceivoValidationError``) for a malformed value or id, and
                ``502`` or ``503`` (``PerceivoServerError``) when the platform
                did not answer: read the ticket before retrying, because the
                change may have been applied.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SupportTicketSummary,
            self._patch(f"{_BASE}/{segment(ticket_id, 'ticket_id')}", json=body),
        )

    def list_comments(
        self, ticket_id: str, *, page: int | None = None, page_size: int | None = None
    ) -> list[TicketCommentRead]:
        """Read a ticket's comments, oldest first (``GET /support/tickets/{ticket_id}/comments``).

        The page is a plain array with no total: request ``page=1, 2, ...``
        until a page holds fewer than ``page_size`` comments. A requester sees
        customer-visible comments only.

        Args:
            ticket_id: The ticket to read.
            page: The page to return, from ``1`` (the API default).
            page_size: Comments per page, from 1 through 100 (API default
                ``25``).

        Returns:
            ``list[TicketCommentRead]`` — one page of comments.

        Raises:
            ValueError: If ``ticket_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a ticket you may not read,
                ``422`` (``PerceivoValidationError``) for a malformed request,
                and ``502`` or ``503`` (``PerceivoServerError``) when the
                platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        query = {
            key: value
            for key, value in (("page", page), ("page_size", page_size))
            if value is not None
        }
        return self._list(
            TicketCommentRead,
            self._get(f"{_BASE}/{segment(ticket_id, 'ticket_id')}/comments", params=query or None),
        )

    def create_comment(self, ticket_id: str, body: dict[str, Any]) -> TicketCommentRead:
        """Add a comment to a ticket (``POST /support/tickets/{ticket_id}/comments``, ``201``).

        ``body`` is a ``TicketCommentCreate``: ``content`` and optional
        ``comment_type`` (``note``, the default, or ``customer_message``). Not
        idempotent: a retry adds the comment again.

        Args:
            ticket_id: The ticket to comment on.
            body: A ``TicketCommentCreate`` object, sent as the JSON body.

        Returns:
            :class:`TicketCommentRead` — the comment as stored.

        Raises:
            ValueError: If ``ticket_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a ticket you may not read,
                ``422`` (``PerceivoValidationError``) for a missing
                ``content`` or a malformed field, and ``502`` or ``503``
                (``PerceivoServerError``) when the platform did not answer:
                read the comments before retrying, because the comment may have
                been added.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TicketCommentRead,
            self._post(f"{_BASE}/{segment(ticket_id, 'ticket_id')}/comments", json=body),
        )

    def list_attachments(self, ticket_id: str) -> list[SupportAttachmentRead]:
        """List a ticket's attachments (``GET /support/tickets/{ticket_id}/attachments``).

        One request returns every attachment you may see; the list is not
        paged.

        Args:
            ticket_id: The ticket to read.

        Returns:
            ``list[SupportAttachmentRead]`` — every attachment.

        Raises:
            ValueError: If ``ticket_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a ticket you may not read,
                ``422`` (``PerceivoValidationError``) for a malformed id, and
                ``502`` or ``503`` (``PerceivoServerError``) when the platform
                did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            SupportAttachmentRead,
            self._get(f"{_BASE}/{segment(ticket_id, 'ticket_id')}/attachments"),
        )

    def create_attachment(self, ticket_id: str, body: dict[str, Any]) -> SupportAttachmentRead:
        """Attach a file to a ticket (``POST /support/tickets/{ticket_id}/attachments``, ``201``).

        ``body`` is a ``SupportAttachmentCreate``: ``filename``,
        ``data_base64`` (at most 10 MB once decoded) and optional
        ``content_type`` and ``comment``. The file is stored with a comment
        that carries it. Not idempotent: a retry attaches a second copy.

        Args:
            ticket_id: The ticket to attach the file to.
            body: A ``SupportAttachmentCreate`` object, sent as the JSON body.

        Returns:
            :class:`SupportAttachmentRead` — the stored attachment.

        Raises:
            ValueError: If ``ticket_id`` is empty, ``.`` or ``..`` (refused
                before the request is sent).
            PerceivoAPIError: On an error response: ``400`` when
                ``data_base64`` is not valid base64, ``404``
                (``PerceivoNotFoundError``) for a ticket you may not read,
                ``422`` (``PerceivoValidationError``) for an unsafe filename, a
                media type that is not accepted, or a file over 10 MB, ``413``
                for a request body over the request-size limit (``details``
                holds ``limit_bytes``), and ``502`` or ``503`` (``PerceivoServerError``) when the upload
                could not be completed or confirmed: list the attachments
                before retrying, because the file may have been attached.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            SupportAttachmentRead,
            self._post(f"{_BASE}/{segment(ticket_id, 'ticket_id')}/attachments", json=body),
        )

    def get_attachment_content(self, ticket_id: str, attachment_id: str) -> bytes:
        """Download an attachment's bytes (``GET .../attachments/{attachment_id}/content``).

        Wraps
        ``GET /support/tickets/{ticket_id}/attachments/{attachment_id}/content``.
        The body is returned exactly as received, whatever its media type: an
        image, a PDF or a JSON file all come back as the file's bytes.

        Args:
            ticket_id: The ticket the attachment belongs to.
            attachment_id: The attachment to download.

        Returns:
            ``bytes`` — the file's content.

        Raises:
            ValueError: If ``ticket_id`` or ``attachment_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for a ticket you may not read, or an
                attachment that does not exist, is on another ticket, or that
                you may not see, ``422`` (``PerceivoValidationError``) for a
                malformed ticket id, and ``502`` (``PerceivoServerError``) when
                the platform did not answer; nothing was read, so retry.
            PerceivoConnectionError: If the API cannot be reached.
        """
        ticket = segment(ticket_id, "ticket_id")
        attachment = segment(attachment_id, "attachment_id")
        response = self._t.request("GET", f"{_BASE}/{ticket}/attachments/{attachment}/content")
        return response.content

    def delete_attachment(self, ticket_id: str, attachment_id: str) -> None:
        """Delete one attachment from a ticket (``DELETE .../attachments/{attachment_id}``, ``204``).

        Wraps ``DELETE /support/tickets/{ticket_id}/attachments/{attachment_id}``.
        The stored file is deleted with it, permanently. Only the attachment's
        author may delete it.

        Args:
            ticket_id: The ticket the attachment belongs to.
            attachment_id: The attachment to delete.

        Raises:
            ValueError: If ``ticket_id`` or ``attachment_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response: ``404``
                (``PerceivoNotFoundError``) for an attachment that does not
                exist, is not yours to delete, or is on another ticket, ``422``
                (``PerceivoValidationError``) for a malformed request, and
                ``502`` (``PerceivoServerError``) when the platform did not
                answer: list the ticket's attachments before retrying, because
                the attachment may have been deleted.
            PerceivoConnectionError: If the API cannot be reached.
        """
        ticket = segment(ticket_id, "ticket_id")
        attachment = segment(attachment_id, "attachment_id")
        self._delete(f"{_BASE}/{ticket}/attachments/{attachment}")
