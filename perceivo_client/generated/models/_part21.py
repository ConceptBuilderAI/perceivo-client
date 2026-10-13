# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class IntelligenceTrainingJobRead(BaseModel):
    """
    A training job of this intelligence and the runs it has produced.
    """

    completed_at: AwareDatetime | None = Field(None, title="Completed At")
    created_at: AwareDatetime = Field(..., title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    family_id: UUID = Field(..., title="Family Id")
    hyperparameter_grid: dict[str, list[Any]] = Field(..., title="Hyperparameter Grid")
    id: UUID = Field(..., title="Id")
    intelligence_id: UUID = Field(..., title="Intelligence Id")
    runs: list[IntelligenceTrainingRunRead] = Field(..., title="Runs")
    started_at: AwareDatetime | None = Field(None, title="Started At")
    status: str = Field(..., title="Status")
    training_config: dict[str, Any] = Field(..., title="Training Config")


class Invoice(BaseModel):
    """
    One invoice for your organization.

    `line_items` is populated on the single-invoice read and is normally empty
    on the list.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    billing_channel: str | None = Field(None, title="Billing Channel")
    created_at: str | None = Field(None, title="Created At")
    currency: str | None = Field(None, title="Currency")
    due_at: str | None = Field(None, title="Due At")
    id: str = Field(..., title="Id")
    invoice_number: str | None = Field(None, title="Invoice Number")
    issued_at: str | None = Field(None, title="Issued At")
    line_items: list[InvoiceLineItem] | None = Field(
        [], title="Line Items", validate_default=True
    )
    organization_id: str | None = Field(None, title="Organization Id")
    paid_at: str | None = Field(None, title="Paid At")
    pdf_url: str | None = Field(
        None,
        description="Download location for the rendered invoice, or `null` while none has been rendered. This value is a stored pointer and is not fetchable on its own. `GET /v1/billing/invoices/{invoice_id}/content` is the operation to use: it returns a fresh, short-lived location that does resolve, and it produces the document on demand if none has been rendered yet — so `null` here does not mean the invoice is unavailable.",
        title="Pdf Url",
    )
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    status: str | None = Field(None, title="Status")
    subtotal_usd: float | None = Field(None, title="Subtotal Usd")
    tax_usd: float | None = Field(None, title="Tax Usd")
    total_usd: float | None = Field(None, title="Total Usd")
    usage_priced_through: str | None = Field(None, title="Usage Priced Through")


class InvoicePage(BaseModel):
    """
    A page of invoices.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    invoices: list[Invoice] | None = Field([], title="Invoices", validate_default=True)
    total: int | None = Field(
        None,
        description="Number of invoices your organization has in total, across every page — not the size of this page.",
        title="Total",
    )


class ManagedServiceListResponse(BaseModel):
    """
    Every managed service instance the organization holds.
    """

    items: list[ManagedServiceRead] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class MemberRoleChangeRead(BaseModel):
    """
    A member after a role change.

    A role change does not remove group membership, so
    `residual_group_privileges` reports what the member still holds through
    their groups afterwards.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    added_by_user_id: UUID | None = Field(None, title="Added By User Id")
    email: str = Field(..., title="Email")
    first_name: str | None = Field(None, title="First Name")
    joined_at: AwareDatetime = Field(..., title="Joined At")
    last_name: str | None = Field(None, title="Last Name")
    name: str = Field(..., title="Name")
    removed_at: AwareDatetime | None = Field(
        None,
        description="When the member was removed; absent while they are active.",
        title="Removed At",
    )
    residual_group_privileges: list[ResidualGroupPrivileges] | None = Field(
        None, title="Residual Group Privileges"
    )
    role: MemberRoleChangeRole = Field(..., title="Role")
    user_id: UUID = Field(..., title="User Id")


class OperationQueue(BaseModel):
    """
    One work queue in your organization's estate.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    backing: str = Field(
        ..., description="The kind of store the queue is held in.", title="Backing"
    )
    depth: OperationQueueDepth
    description: str = Field(..., title="Description")
    label: str = Field(..., title="Label")
    queue: str = Field(
        ..., description="The queue's identifier, used to address it.", title="Queue"
    )


class OperationQueueList(BaseModel):
    """
    The work queues in your organization's estate.

    Note: ``unreported`` names queues that exist but whose depth is not being
    published, with the reason for each. They are **not** in ``queues`` and
    addressing one directly is refused — so a caller that only reads ``queues``
    is not being told those queues do not exist, and should not conclude it.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    count: int = Field(..., description="Number of queues in `queues`.", title="Count")
    organization_id: str = Field(..., title="Organization Id")
    queues: list[OperationQueue] | None = Field(None, title="Queues")
    unreported: dict[str, Any] | None = Field(
        None,
        description="Queues whose depth is not published, mapped to the reason.",
        title="Unreported",
    )


class OrchestrationDefinitionValidate(BaseModel):
    """
    An unsaved orchestration definition to validate.

    This is the create payload without a name: a definition being checked has
    not been named yet, and requiring one would make validation reject documents
    that import accepts.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    capability_id: UUID | None = Field(None, title="Capability Id")
    description: str | None = Field(None, title="Description")
    edges: list[OrchestrationEdgeDefine] | None = Field(None, title="Edges")
    nodes: list[OrchestrationNodeDefine] | None = Field(None, title="Nodes")
    ports: list[OrchestrationPortDefine] | None = Field(None, title="Ports")
    runtime_config: dict[str, Any] | None = Field(None, title="Runtime Config")
    tags: list[str] | None = Field(None, title="Tags")


class OrchestrationDraftPublishPayload(BaseModel):
    """
    What publishing the draft applies to the new version.
    """

    change_note: ChangeNote | None = Field(
        None,
        description="Recorded as the new version's change note.",
        title="Change Note",
    )
    patch: OrchestrationDraftPatch
    secret_ops: list[OrchestrationDraftSecretOp] | None = Field(
        None, title="Secret Ops"
    )


class OrchestrationDraftUpdate(BaseModel):
    base_version_id: UUID | None = Field(
        None,
        description="Cannot be changed after create; a request that sends it is refused `400`.",
        title="Base Version Id",
    )
    canvas_state: dict[str, Any] | None = Field(None, title="Canvas State")
    description: str | None = Field(None, title="Description")
    name: str | None = Field(None, title="Name")
    publish_payload: OrchestrationDraftPublishPayload | None = None
    staged_changes: list[OrchestrationDraftStagedChange] | None = Field(
        None, title="Staged Changes"
    )


class OrchestrationGraph(BaseModel):
    """
    The nodes of an orchestration and the connections between them.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    edges: list[OrchestrationEdge] | None = Field(None, title="Edges")
    nodes: list[OrchestrationNode] | None = Field(None, title="Nodes")


class PredictionPage(BaseModel):
    """
    A page of prediction records.

    Note: **This is the page-based pagination envelope — ``data``/``page``/``page_size``/
    ``total``/``next`` — and not the ``items``/``limit``/``offset`` dialect the
    older list operations on this service publish.** The difference is the
    backing's, not a choice made here: ``list_predictions`` declares ``page`` and
    ``page_size`` query parameters and builds a ``next`` URL. Renaming the fields
    to match this service's older lists would describe a body that never arrives.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    data: list[PredictionRecord] | None = Field(None, title="Data")
    next: str | None = Field(
        None,
        description="URL of the next page, or null on the last page. It is a complete URL — follow it rather than composing your own.",
        title="Next",
    )
    page: int = Field(..., title="Page")
    page_size: int = Field(..., title="Page Size")
    total: int = Field(..., title="Total")


class RegisterFileEntries(BaseModel):
    """
    Up to 100 uploaded files to register in one call.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    files: list[RegisterFileItem] = Field(
        ...,
        description="The files to register, one to a hundred",
        max_length=100,
        min_length=1,
        title="Files",
    )


class RegisterFileEntriesResult(BaseModel):
    """
    The counts, and one outcome per submitted file in request order.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    failed_count: int = Field(
        ..., description="Files not registered", title="Failed Count"
    )
    message: str = Field(..., description="A one-line summary", title="Message")
    results: list[RegisterFileOutcome] = Field(
        ..., description="One outcome per file", title="Results"
    )
    success_count: int = Field(
        ..., description="Files registered", title="Success Count"
    )


class RunPage(BaseModel):
    """
    One page of runs.

    Note: ``total`` is the number of runs **in this page**, not the size of the whole
    result set — the platform does not compute a global count for this
    collection. Do not use it to size a progress bar or to decide when to stop
    paging: request the next page until a short or empty page is returned.

    Note: This is deliberately **not** the standard pagination envelope. That
    envelope's ``total`` means the full result-set size, and presenting a
    page-level count under that name would be false in exactly the way a client
    cannot detect.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[RunSummary] = Field(
        ..., description="The runs in this page.", title="Items"
    )
    total: int = Field(
        ...,
        description="Number of runs in THIS page. Not a global count.",
        title="Total",
    )


class ScheduledTriggerCreate(BaseModel):
    """
    Body for ``POST /v1/triggers``.

    The organization is taken from the orchestration you name, which must be one
    your credential can reach; it cannot be chosen here.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifacts: dict[str, dict[str, Any]] | None = Field(
        None,
        description="Named artifacts supplied to each run, as an object keyed by artifact name.",
        title="Artifacts",
    )
    cron_expression: str = Field(
        ...,
        description="Standard five-field cron expression.",
        max_length=100,
        min_length=1,
        title="Cron Expression",
    )
    description: str | None = Field(
        None,
        description="What the trigger is for, in your own words.",
        title="Description",
    )
    enabled: bool | None = Field(
        True,
        description="Whether the trigger fires on its schedule. A disabled trigger has no next run time.",
        title="Enabled",
    )
    ends_at: str | None = Field(
        None, description="ISO-8601 UTC, or null.", title="Ends At"
    )
    input_payload: dict[str, Any] | None = Field(
        None,
        description="The input each scheduled run of the orchestration receives.",
        title="Input Payload",
    )
    is_one_time: bool | None = Field(
        False,
        description="Fire once only. A one-time trigger with `starts_at` fires at that time; without it, at the next time the cron expression matches.",
        title="Is One Time",
    )
    name: str = Field(
        ...,
        description="A name for the trigger, shown wherever the trigger is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )
    nodepool_id: str | None = Field(
        None,
        description="Private nodepool to schedule the workload on.",
        title="Nodepool Id",
    )
    orchestration_id: str = Field(
        ...,
        description="The orchestration this trigger runs.",
        title="Orchestration Id",
    )
    resources: ScheduledTriggerResources | None = Field(
        None, description="The compute each workload this trigger creates is given."
    )
    reviewer_assignments: list[ScheduledTriggerReviewerAssignment] | None = Field(
        None,
        description="Who reviews each review step of the orchestration on the runs this trigger starts, one entry per review node.",
        title="Reviewer Assignments",
    )
    starts_at: str | None = Field(
        None, description="ISO-8601 UTC, or null.", title="Starts At"
    )
    timezone: str | None = Field(
        "UTC",
        description="The time zone the cron expression is evaluated in, as an IANA name such as `Europe/Berlin`. A name that is not recognized is treated as `UTC`.",
        max_length=50,
        title="Timezone",
    )
    trigger_type: str | None = Field(
        "cron", description="Only `cron` is supported.", title="Trigger Type"
    )


class ScheduledTriggerListResponse(BaseModel):
    """
    A window onto your organization's triggers.

    Only the newest version of each trigger appears, and deleted triggers are
    excluded.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[ScheduledTriggerRead] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class SupportTicketDetail(BaseModel):
    """
    A support ticket with its comment thread and recorded links.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    comments: list[TicketCommentRead] | None = Field(None, title="Comments")
    links: list[SupportTicketLink] | None = Field(None, title="Links")
    ticket: TicketSummaryOut


class SupportTicketListResponse(BaseModel):
    """
    A page of support tickets you raised.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    data: list[TicketSummaryOut] = Field(..., title="Data")
    next: str | None = Field(None, title="Next")
    page: int = Field(..., title="Page")
    page_size: int = Field(..., title="Page Size")
    total: int = Field(..., title="Total")


class ThreadListResponse(BaseModel):
    """
    A page of threads you are on.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    data: list[ThreadRead] | None = Field(None, title="Data")
    next: str | None = Field(None, title="Next")
    page: int = Field(..., title="Page")
    page_size: int = Field(..., title="Page Size")
    total: int = Field(..., title="Total")
