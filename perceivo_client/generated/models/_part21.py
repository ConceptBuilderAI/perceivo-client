# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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


class TrainingGroupDetail(BaseModel):
    """
    A training group and the configurations it contains.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    created_by_user_sub: str | None = Field(None, title="Created By User Sub")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    is_default: bool | None = Field(False, title="Is Default")
    member_count: int | None = Field(0, title="Member Count")
    members: list[TrainingGroupMemberRead] | None = Field(
        [], title="Members", validate_default=True
    )
    name: str = Field(..., title="Name")
    updated_at: str | None = Field(None, title="Updated At")


class ValidationCheck(BaseModel):
    """
    One validation finding.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    category: str | None = Field(
        None, description="The family of check that produced it.", title="Category"
    )
    id: str | None = Field(
        None, description="Stable identifier for this check.", title="Id"
    )
    location: ValidationLocation | None = Field(
        None,
        description="Where in the script the finding applies, when it is positional.",
    )
    message: str | None = Field(
        None, description="What is wrong and why.", title="Message"
    )
    severity: str | None = Field(
        None,
        description="How serious the finding is: `error`, `warning` or `info`.",
        title="Severity",
    )
    suggestion: str | None = Field(
        None, description="How to resolve the finding.", title="Suggestion"
    )
    title: str | None = Field(
        None, description="Short summary of the finding.", title="Title"
    )


class ComponentExportDocument(BaseModel):
    """
    A self-contained export of one component, accepted unchanged by import.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component: ComponentTransferData
    export_type: Literal["component"] = Field("component", title="Export Type")
    export_version: str | None = Field("1.0", title="Export Version")
    exported_at: AwareDatetime = Field(..., title="Exported At")


class ComponentImportBody(BaseModel):
    """
    A component export document to import into your organization.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    component: ComponentTransferData = Field(
        ..., description="The exported component, unchanged from the export document."
    )
    export_type: Literal["component"] = Field(
        "component",
        description="Only a component export can be imported here.",
        title="Export Type",
    )
    export_version: str | None = Field(
        "1.0",
        description="The export format version, as the export document gives it.",
        title="Export Version",
    )
    exported_at: AwareDatetime | None = Field(
        None,
        description="When the export was made, as the export document gives it.",
        title="Exported At",
    )
    new_name: str | None = Field(
        None,
        description="A name for the imported component, in place of the exported one.",
        title="New Name",
    )


class ComponentValidationReport(BaseModel):
    """
    The result of validating a component definition.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    checks: list[ValidationCheck] | None = Field(
        None, description="Every finding, in the order produced.", title="Checks"
    )
    derived_contract: dict[str, Any] | None = Field(
        None,
        description="The contract this validation ran against: the `contract` you supplied, or, when you supplied none, the `contract` block read from `manifest_yaml`. It is not inferred from your code.",
        title="Derived Contract",
    )
    runtime_observations: RuntimeObservations | None = Field(
        None,
        description="What static analysis of the script found. The script is not run.",
    )
    summary: ValidationSummary | None = Field(
        None, description="Finding counts by severity."
    )
    valid: bool | None = Field(
        None, description="Whether the definition would be accepted.", title="Valid"
    )
