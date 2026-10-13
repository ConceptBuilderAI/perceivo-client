# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class SubscriptionRead(BaseModel):
    """
    ``GET /v1/billing/subscription`` — the org's billing configuration record.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    azure_subscription_id: str | None = Field(None, title="Azure Subscription Id")
    azure_tenant_id: str | None = Field(None, title="Azure Tenant Id")
    billing_currency: str | None = Field(None, title="Billing Currency")
    billing_cycle: str | None = Field(None, title="Billing Cycle")
    created_at: str | None = Field(None, title="Created At")
    csp_partner_id: str | None = Field(None, title="Csp Partner Id")
    csp_partner_name: str | None = Field(None, title="Csp Partner Name")
    default_compute_markup_percent: float | None = Field(
        None, title="Default Compute Markup Percent"
    )
    default_llm_markup_percent: float | None = Field(
        None, title="Default Llm Markup Percent"
    )
    default_storage_markup_percent: float | None = Field(
        None, title="Default Storage Markup Percent"
    )
    default_transfer_markup_percent: float | None = Field(
        None, title="Default Transfer Markup Percent"
    )
    id: str | None = Field(None, title="Id")
    invoice_email: str | None = Field(None, title="Invoice Email")
    is_active: bool | None = Field(None, title="Is Active")
    markup_overrides: list[Any] | None = Field(None, title="Markup Overrides")
    organization_id: str | None = Field(None, title="Organization Id")
    updated_at: str | None = Field(None, title="Updated At")


class SubscriptionReadV1(BaseModel):
    """
    One subscription.

    Note: The subscriptions operation returns a **list**, even though its path is
    singular — an organization may hold more than one.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    organization_id: str = Field(..., title="Organization Id")
    status: str | None = Field(None, title="Status")
    tier_id: str | None = Field(None, title="Tier Id")
    updated_at: str = Field(..., title="Updated At")


class SupportAttachmentCreate(BaseModel):
    """
    A file to attach to a support ticket.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    comment: str | None = Field(
        None,
        description="Comment recorded alongside the attachment. Defaults to a note naming the file.",
        title="Comment",
    )
    content_type: str | None = Field(
        "application/octet-stream",
        description="Media type of the file. One of: image/png, image/jpeg, image/gif, image/webp, text/plain, text/markdown, text/csv, application/json, application/pdf, application/x-yaml, text/yaml, application/octet-stream.",
        title="Content Type",
    )
    data_base64: str = Field(
        ...,
        description="File content, base64-encoded. The decoded size must not exceed 10 MB.",
        max_length=14348938,
        title="Data Base64",
    )
    filename: str = Field(
        ...,
        description="Name the file is stored and served under. Quotes, slashes and control characters are not accepted.",
        max_length=256,
        min_length=1,
        title="Filename",
    )


class SupportAttachmentRead(BaseModel):
    """
    A file attached to a support ticket.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    attachment_id: str = Field(..., title="Attachment Id")
    blob_name: str = Field(..., title="Blob Name")
    comment_id: str | None = Field(None, title="Comment Id")
    content_type: str = Field(..., title="Content Type")
    created_at: str | None = Field(None, title="Created At")
    filename: str = Field(..., title="Filename")
    size_bytes: int = Field(..., title="Size Bytes")


class SupportTicketLink(BaseModel):
    """
    A relationship recorded between two tickets.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    link_type: str | None = Field(None, title="Link Type")
    source_ticket_id: str | None = Field(None, title="Source Ticket Id")
    target_ticket_id: str | None = Field(None, title="Target Ticket Id")


class SupportTicketSummary(BaseModel):
    """
    A support ticket without its comment thread or links.

    Returned when a ticket is raised or amended. Read the ticket to get its
    comments and links.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    category: str | None = Field(None, title="Category")
    claimed_at: str | None = Field(None, title="Claimed At")
    closed_at: str | None = Field(None, title="Closed At")
    components_affected: list[str] | None = Field(None, title="Components Affected")
    created_at: str | None = Field(None, title="Created At")
    customer_email: str | None = Field(None, title="Customer Email")
    customer_name: str | None = Field(None, title="Customer Name")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    operator_email: str | None = Field(None, title="Operator Email")
    operator_name: str | None = Field(None, title="Operator Name")
    operator_user_id: str | None = Field(None, title="Operator User Id")
    organization_id: str | None = Field(None, title="Organization Id")
    pr_urls: list[str] | None = Field(None, title="Pr Urls")
    priority: str | None = Field(None, title="Priority")
    reason: str | None = Field(None, title="Reason")
    resolution: str | None = Field(None, title="Resolution")
    resolution_method: str | None = Field(None, title="Resolution Method")
    resolution_text: str | None = Field(None, title="Resolution Text")
    source: str | None = Field(None, title="Source")
    status: str | None = Field(None, title="Status")
    tags: list[str] | None = Field(None, title="Tags")
    ticket_number: int | None = Field(None, title="Ticket Number")
    ticket_type: str | None = Field(None, title="Ticket Type")
    title: str | None = Field(None, title="Title")
    updated_at: str | None = Field(None, title="Updated At")
    user_display_name: str | None = Field(None, title="User Display Name")
    user_email: str | None = Field(None, title="User Email")
    user_id: str | None = Field(None, title="User Id")
    workload_id: str | None = Field(None, title="Workload Id")


class TestInvokeResponse(BaseModel):
    """
    Result of a capability test-invoke (execute).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str | None = Field(None, title="Capability Id")
    message: str | None = Field(None, title="Message")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    position: int | None = Field(None, title="Position")
    request_id: str | None = Field(None, title="Request Id")
    status: str | None = Field(None, title="Status")
    success: bool | None = Field(None, title="Success")


class ThreadCreateTitle(RootModel[str]):
    root: str = Field(
        ..., description="Optional thread title.", max_length=255, title="Title"
    )


class ThreadCreate(BaseModel):
    """
    Open a thread with a set of people in your organization.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    participant_user_ids: list[str] = Field(
        ...,
        description="The people to include. You are added automatically, so a single other person opens a direct thread.",
        min_length=1,
        title="Participant User Ids",
    )
    title: ThreadCreateTitle | None = Field(
        None, description="Optional thread title.", title="Title"
    )


class ThreadMessage(BaseModel):
    """
    A single message in a thread.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    body: str = Field(..., title="Body")
    conversation_id: str = Field(..., title="Conversation Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    metadata: dict[str, Any] | None = Field(None, title="Metadata")
    sender_id: str | None = Field(None, title="Sender Id")
    sender_name: str | None = Field(None, title="Sender Name")
    sender_type: str = Field(..., title="Sender Type")


class ThreadMessageCreate(BaseModel):
    """
    Post a message into a thread.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    body: str = Field(..., description="The message text.", min_length=1, title="Body")
    metadata: dict[str, Any] | None = Field(
        None,
        description="Arbitrary JSON stored alongside the message.",
        title="Metadata",
    )


class ThreadMessagesPage(BaseModel):
    """
    A window of messages, oldest first.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    has_more: bool | None = Field(False, title="Has More")
    messages: list[ThreadMessage] | None = Field(None, title="Messages")


class ThreadParticipant(BaseModel):
    """
    Someone on a thread.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    display_name: str | None = Field(None, title="Display Name")
    last_read_at: AwareDatetime | None = Field(None, title="Last Read At")
    role: str = Field(..., title="Role")
    user_id: str = Field(..., title="User Id")


class ThreadParticipantAdd(BaseModel):
    """
    Add someone to a group thread.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    user_id: str = Field(..., description="The person to add.", title="User Id")


class ThreadRead(BaseModel):
    """
    A thread, with its participants and a preview of the latest message.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    conversation_type: str = Field(..., title="Conversation Type")
    created_at: AwareDatetime = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    last_message: ThreadMessage | None = None
    organization_id: str = Field(..., title="Organization Id")
    participants: list[ThreadParticipant] | None = Field(None, title="Participants")
    title: str | None = Field(None, title="Title")
    unread_count: int | None = Field(0, title="Unread Count")
    updated_at: AwareDatetime = Field(..., title="Updated At")


class ThreadUpdateTitle(RootModel[str]):
    root: str = Field(
        ..., description="New thread title.", max_length=255, title="Title"
    )


class ThreadUpdate(BaseModel):
    """
    Amend a thread you are on.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    title: ThreadUpdateTitle | None = Field(
        None, description="New thread title.", title="Title"
    )


class CommentType(StrEnum):
    """
    `note` or `customer_message`.
    """

    note = "note"
    customer_message = "customer_message"


class TicketCommentCreate(BaseModel):
    """
    Create a ticket comment: ``content`` plus optional ``comment_type``.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    comment_type: CommentType | None = Field(
        "note", description="`note` or `customer_message`.", title="Comment Type"
    )
    content: str = Field(
        ...,
        description="The comment text.",
        max_length=1000000,
        min_length=1,
        title="Content",
    )


class TicketCommentRead(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    comment_type: str | None = Field(None, title="Comment Type")
    content: str = Field(..., title="Content")
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    ticket_id: str = Field(..., title="Ticket Id")


class Category(StrEnum):
    """
    The area of the platform the ticket concerns.
    """

    user_request = "user_request"
    platform_issue = "platform_issue"
    builder_failure = "builder_failure"
    infrastructure = "infrastructure"
    security = "security"
    performance = "performance"
    documentation = "documentation"


class TicketCreate(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    category: Category | None = Field(
        None,
        description="The area of the platform the ticket concerns.",
        title="Category",
    )
    components_affected: list[str] | None = Field(
        None,
        description="The names of the components the ticket concerns.",
        title="Components Affected",
    )
    customer_email: str | None = Field(
        None,
        description="The email address of the person the ticket is for.",
        title="Customer Email",
    )
    customer_name: str | None = Field(
        None,
        description="The name of the person the ticket is for.",
        title="Customer Name",
    )
    description: str | None = Field(
        None,
        description="The full account of the problem or request.",
        title="Description",
    )
    priority: str | None = Field(
        None,
        description="How urgent the ticket is: `critical`, `high`, `normal` or `low`. Defaults to `normal`.",
        title="Priority",
    )
    source: str | None = Field(
        None,
        description="Where the ticket came from. Defaults to `manual`.",
        title="Source",
    )
    tags: list[str] | None = Field(
        None,
        description="Free-form labels for finding and grouping tickets.",
        title="Tags",
    )
    ticket_type: str | None = Field(
        None,
        description="The kind of ticket: `bug`, `feature_request`, `incident`, `customer_inquiry`, `task` or `improvement`. Defaults to `task`.",
        title="Ticket Type",
    )
    title: str = Field(
        ...,
        description="A one-line summary of the problem or request, at most 256 characters.",
        title="Title",
    )


class TicketSummaryOut(BaseModel):
    """
    Ticket summary returned by action endpoints (e.g. reopen).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    category: str | None = Field(None, title="Category")
    claimed_at: str | None = Field(None, title="Claimed At")
    closed_at: str | None = Field(None, title="Closed At")
    components_affected: list[str] | None = Field(None, title="Components Affected")
    created_at: str | None = Field(None, title="Created At")
    customer_email: str | None = Field(None, title="Customer Email")
    customer_name: str | None = Field(None, title="Customer Name")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    operator_email: str | None = Field(None, title="Operator Email")
    operator_name: str | None = Field(None, title="Operator Name")
    operator_user_id: str | None = Field(None, title="Operator User Id")
    organization_id: str | None = Field(None, title="Organization Id")
    pr_urls: list[str] | None = Field(None, title="Pr Urls")
    priority: str | None = Field(None, title="Priority")
    reason: str | None = Field(None, title="Reason")
    resolution: str | None = Field(None, title="Resolution")
    resolution_method: str | None = Field(None, title="Resolution Method")
    resolution_text: str | None = Field(None, title="Resolution Text")
    source: str | None = Field(None, title="Source")
    status: str | None = Field(None, title="Status")
    tags: list[str] | None = Field(None, title="Tags")
    ticket_number: int | None = Field(None, title="Ticket Number")
    ticket_type: str | None = Field(None, title="Ticket Type")
    title: str | None = Field(None, title="Title")
    updated_at: str | None = Field(None, title="Updated At")
    user_display_name: str | None = Field(None, title="User Display Name")
    user_email: str | None = Field(None, title="User Email")
    user_id: str | None = Field(None, title="User Id")
    workload_id: str | None = Field(None, title="Workload Id")
