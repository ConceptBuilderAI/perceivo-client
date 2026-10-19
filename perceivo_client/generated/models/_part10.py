# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class IntelligenceTrafficPlanResult(BaseModel):
    """
    The outcome of applying a traffic plan.
    """

    details: dict[str, Any] | None = Field(None, title="Details")
    final_status: str = Field(
        ...,
        description="`completed`, `rolled_back` or `failed` once the apply has finished",
        title="Final Status",
    )
    intelligence_id: str = Field(..., title="Intelligence Id")
    message: str = Field(..., title="Message")
    operation_id: str = Field(..., title="Operation Id")
    success: bool = Field(..., title="Success")


class IntelligenceTrainingRunRead(BaseModel):
    """
    One run of a training job, with the hyperparameters it tried.
    """

    completed_at: AwareDatetime | None = Field(None, title="Completed At")
    duration_seconds: int | None = Field(None, title="Duration Seconds")
    error_message: str | None = Field(None, title="Error Message")
    hyperparameters: dict[str, Any] = Field(..., title="Hyperparameters")
    id: UUID = Field(..., title="Id")
    metrics: dict[str, float] = Field(..., title="Metrics")
    started_at: AwareDatetime | None = Field(None, title="Started At")
    status: str = Field(..., title="Status")


class IntelligenceTriggerExecutionRead(BaseModel):
    """
    One execution of an intelligence trigger.
    """

    completed_at: AwareDatetime | None = Field(None, title="Completed At")
    created_at: AwareDatetime = Field(..., title="Created At")
    duration_seconds: int | None = Field(None, title="Duration Seconds")
    error_message: str | None = Field(None, title="Error Message")
    id: UUID = Field(..., title="Id")
    idempotency_key: str = Field(..., title="Idempotency Key")
    result: dict[str, Any] | None = Field(None, title="Result")
    source: str = Field(
        ...,
        description="What started the execution: `cron`, `http` or `manual`",
        title="Source",
    )
    started_at: AwareDatetime | None = Field(None, title="Started At")
    status: str = Field(
        ...,
        description="`pending`, `running`, `completed`, `failed` or `skipped`",
        title="Status",
    )
    trigger_id: UUID = Field(..., title="Trigger Id")
    workload_id: UUID | None = Field(None, title="Workload Id")


class IntelligenceUpdate(BaseModel):
    """
    Update an intelligence asset (all fields optional).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")
    description: str | None = Field(None, title="Description")
    name: str | None = Field(None, title="Name")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")


class IntelligenceUpdateResult(BaseModel):
    """
    The intelligence asset after an update.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    status: str | None = Field(None, title="Status")
    tags: list[str] | None = Field(None, title="Tags")
    updated_at: str | None = Field(None, title="Updated At")
    version_created: bool = Field(
        ...,
        description="`true` when the update produced a new asset — a new version — and `id` is that new asset's identifier; `false` when the asset was updated in place. Follow `id` either way.",
        title="Version Created",
    )


class IntelligenceUsageResponse(BaseModel):
    """
    ``GET /v1/billing/intelligence-usage``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    by_service_type: dict[str, Any] | None = Field(None, title="By Service Type")
    intelligences: list[dict[str, Any]] | None = Field(None, title="Intelligences")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    total: dict[str, Any] | None = Field(None, title="Total")


class IntelligencesCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/intelligences``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    intelligences: list[dict[str, Any]] | None = Field(None, title="Intelligences")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    llm_managed_cost_usd: float | None = Field(None, title="Llm Managed Cost Usd")
    llm_user_cost_usd: float | None = Field(None, title="Llm User Cost Usd")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")
    total_executions: int | None = Field(None, title="Total Executions")


class InvitationRole(StrEnum):
    global_admin = "global_admin"
    admin = "admin"
    billing_admin = "billing_admin"
    member = "member"


class InvitationStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
    cancelled = "cancelled"


class InvitationRead(BaseModel):
    """
    One invitation to join your organization.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    accepted_at: AwareDatetime | None = Field(None, title="Accepted At")
    created_at: AwareDatetime = Field(..., title="Created At")
    email: str = Field(..., title="Email")
    email_attempt_count: int = Field(
        ...,
        description="Send attempts so far, across resends.",
        title="Email Attempt Count",
    )
    email_delivery_status: str = Field(
        ...,
        description="`pending`, `sent` or `failed`. `sent` means the message was handed to the mail provider, not that it reached the inbox.",
        title="Email Delivery Status",
    )
    email_sent_at: AwareDatetime | None = Field(None, title="Email Sent At")
    expires_at: AwareDatetime = Field(..., title="Expires At")
    id: UUID = Field(..., title="Id")
    invited_by: UUID = Field(..., title="Invited By")
    invited_by_name: str | None = Field(None, title="Invited By Name")
    message: str | None = Field(None, title="Message")
    role: InvitationRole = Field(..., title="Role")
    status: InvitationStatus = Field(..., title="Status")


class InvoiceContent(BaseModel):
    """
    Where to fetch the rendered invoice document.

    Note: This operation returns a **download location**, not the document bytes.
    The rendered invoice is a PDF held in object storage and the API answers
    with the URL to retrieve it from; fetch that URL to obtain the file.

    The location is **short-lived and single-purpose**: it is minted for the
    request that asked for it, expires within the hour, and is not the same
    string twice. Fetch it promptly rather than storing it, and ask again
    rather than reusing an old one. An invoice that has not been rendered yet
    is rendered on demand rather than refused; an invoice still in `draft` has
    no document to hand back.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    pdf_url: str = Field(
        ...,
        description="Location the rendered invoice PDF can be downloaded from. Short-lived — fetch it now rather than storing it.",
        title="Pdf Url",
    )


class InvoiceLineItem(BaseModel):
    """
    One priced line on an invoice.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    billing_segment_id: str | None = Field(None, title="Billing Segment Id")
    category: str | None = Field(None, title="Category")
    charge_period_start: str | None = Field(None, title="Charge Period Start")
    description: str | None = Field(None, title="Description")
    enterprise_entitlement_id: str | None = Field(
        None, title="Enterprise Entitlement Id"
    )
    id: str = Field(..., title="Id")
    markup_percent: float | None = Field(None, title="Markup Percent")
    quantity: float | None = Field(None, title="Quantity")
    resource_type: str | None = Field(None, title="Resource Type")
    sort_order: int | None = Field(None, title="Sort Order")
    subtotal_usd: float | None = Field(None, title="Subtotal Usd")
    total_usd: float | None = Field(None, title="Total Usd")
    unit: str | None = Field(None, title="Unit")
    unit_price_usd: float | None = Field(None, title="Unit Price Usd")


class LifecycleOperationResponse(BaseModel):
    """
    Result of a capability start/stop/restart lifecycle operation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str | None = Field(None, title="Capability Id")
    details: dict[str, Any] | None = Field(None, title="Details")
    final_status: str | None = Field(None, title="Final Status")
    message: str | None = Field(None, title="Message")
    operation_id: str | None = Field(None, title="Operation Id")
    success: bool | None = Field(None, title="Success")


class LineageRestoreResult(BaseModel):
    """
    The versions one restore returned to their prior status.
    """

    id: str = Field(
        ..., description="The identifier the request addressed.", title="Id"
    )
    restored_count: int | None = Field(
        0, description="The number of versions restored.", title="Restored Count"
    )
    restored_ids: list[str] | None = Field(
        None, description="Every version this call restored.", title="Restored Ids"
    )
    root_id: str | None = Field(
        None,
        description="Identifier of the first version of the lineage.",
        title="Root Id",
    )
    status: str = Field(
        ...,
        description="The addressed version's status after the restore.",
        title="Status",
    )


class LogPage(BaseModel):
    """
    A bounded slice of log lines.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    channel: str | None = Field(None, title="Channel")
    logs: list[dict[str, Any]] | None = Field(None, title="Logs")
    scope: str | None = Field(None, title="Scope")


class ManagedServiceRead(BaseModel):
    """
    One managed (Azure-hosted) service instance.

    `service` is the name used in the request path. Managed services are
    addressed by name, not by instance identifier: an organization holds at
    most one live instance of each type.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    azure_resource_name: str | None = Field(None, title="Azure Resource Name")
    configuration: dict[str, Any] | None = Field(None, title="Configuration")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    hourly_rate_usd: float | None = Field(None, title="Hourly Rate Usd")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    last_activity_at: str | None = Field(None, title="Last Activity At")
    name: str | None = Field(None, title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    provisioned_at: str | None = Field(None, title="Provisioned At")
    service: str = Field(
        ...,
        description="The service name, as used in the request path.",
        title="Service",
    )
    service_display_name: str | None = Field(None, title="Service Display Name")
    sku: str | None = Field(None, title="Sku")
    status: str = Field(
        ...,
        description="Lifecycle state, e.g. pending, provisioning, running, stopping, stopped, failed.",
        title="Status",
    )
    stopped_at: str | None = Field(None, title="Stopped At")
    updated_at: str | None = Field(None, title="Updated At")


class ManagedServiceType(StrEnum):
    """
    The managed (Azure-hosted) service to operate on.
    """

    postgres = "postgres"
    redis = "redis"


class ManagedServiceUpdate(BaseModel):
    """
    Changes to apply to a managed service instance.

    Every field is optional; only the fields present in the request are
    changed. Lifecycle state is changed through the `start` and `stop`
    operations, never here.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    configuration: dict[str, Any] | None = Field(None, title="Configuration")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    name: str | None = Field(None, title="Name")
    sku: str | None = Field(None, title="Sku")


class MaterializeResponse(BaseModel):
    """
    Response from a materialize trigger.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    feature_views: list[str] | None = Field(None, title="Feature Views")
    message: str | None = Field(None, title="Message")
    status: str | None = Field(None, title="Status")


class McpConfigDocument(BaseModel):
    """
    The MCP server's configuration.

    The complete document: these are the only settings this surface manages,
    and they are exactly the settings the replace operation accepts.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool = Field(
        ...,
        description="Whether the server shuts down after a period of inactivity.",
        title="Auto Shutdown",
    )
    idle_timeout_minutes: int = Field(
        ...,
        description="Minutes of inactivity before an idle shutdown.",
        title="Idle Timeout Minutes",
    )


class McpConfigReplace(BaseModel):
    """
    A complete replacement MCP server configuration.

    Both fields are required: this operation replaces the configuration rather
    than merging into it, so the document you send is the document that results.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool = Field(
        ...,
        description="Whether the server shuts down after a period of inactivity.",
        title="Auto Shutdown",
    )
    idle_timeout_minutes: int = Field(
        ...,
        description="Minutes of inactivity before an idle shutdown.",
        ge=5,
        le=1440,
        title="Idle Timeout Minutes",
    )


class McpToolInvokeRequest(BaseModel):
    """
    Arguments for an MCP tool invocation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    arguments: dict[str, Any] | None = Field(
        None,
        description="The tool's arguments, as the tool's own schema declares them.",
        title="Arguments",
    )


class McpToolInvokeResult(BaseModel):
    """
    The result of an MCP tool invocation.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class McpToolList(BaseModel):
    """
    The tools the MCP server currently exposes.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class Message(RootModel[str]):
    root: str = Field(
        ...,
        description="A note included in the invitation e-mail.",
        max_length=1000,
        min_length=1,
        title="Message",
    )
