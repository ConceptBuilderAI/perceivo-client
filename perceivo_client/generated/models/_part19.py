# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class UploadUrlRequest(BaseModel):
    """
    The storage space a direct upload is destined for, and the one file.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    file_name: str = Field(
        ...,
        description="Name of the one file to upload",
        max_length=255,
        min_length=1,
        title="File Name",
    )
    relative_path: RelativePath | None = Field(
        None,
        description="Folder within the space, e.g. reports/2026",
        title="Relative Path",
    )
    size_bytes: int = Field(
        ...,
        description="Size of the file in bytes, checked against the storage quota",
        ge=0,
        title="Size Bytes",
    )
    space_id: UUID = Field(
        ..., description="Storage space the upload is destined for", title="Space Id"
    )


class UploadUrlsRequest(BaseModel):
    """
    The storage space the uploads are destined for, and up to 100 files.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    files: list[UploadUrlFile] = Field(
        ...,
        description="The files to upload, one to a hundred; their total size is checked against the space's storage quota once",
        max_length=100,
        min_length=1,
        title="Files",
    )
    space_id: UUID = Field(
        ..., description="Storage space the uploads are destined for", title="Space Id"
    )


class UploadUrlsResponse(BaseModel):
    """
    One upload URL per requested file, in request order.
    """

    targets: list[UploadTargetResponse] = Field(
        ..., description="One target per file, in request order", title="Targets"
    )


class UsageBreakdownResponse(BaseModel):
    """
    ``GET /v1/billing/usage/breakdown`` — per-service usage breakdown.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    elasticsearch: dict[str, Any] | None = Field(None, title="Elasticsearch")
    intelligence: dict[str, Any] | None = Field(None, title="Intelligence")
    mcp: dict[str, Any] | None = Field(None, title="Mcp")
    milvus: dict[str, Any] | None = Field(None, title="Milvus")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    ray: dict[str, Any] | None = Field(None, title="Ray")
    redis: dict[str, Any] | None = Field(None, title="Redis")
    snapshot_count: int | None = Field(None, title="Snapshot Count")
    total: dict[str, Any] | None = Field(None, title="Total")


class UsageMetricsResponse(BaseModel):
    """
    ``GET /v1/billing/usage`` — org usage metrics: a summary block plus a
    per-bucket time series.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    summary: dict[str, Any] | None = Field(None, title="Summary")
    time_series: list[dict[str, Any]] | None = Field(None, title="Time Series")


class UsageReport(BaseModel):
    """
    A cost and consumption report.

    The reports behind each aggregation dimension are shaped differently — a
    per-asset row set, a category summary, an infrastructure breakdown — so only
    the fields present on all of them are declared. The report's own keys are
    passed through.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    currency: str | None = Field(None, title="Currency")
    group_by: str | None = Field(
        None,
        description="The aggregation dimension this report was grouped by.",
        title="Group By",
    )


class UsageSnapshotEntry(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    base_cost_usd: float | None = Field(
        None, description="Cost before overhead, USD.", title="Base Cost Usd"
    )
    category_breakdown: dict[str, Any] | None = Field(
        None,
        description="The sample split by workload category.",
        title="Category Breakdown",
    )
    cpu_seconds: float | None = Field(
        None, description="CPU seconds in the sample.", title="Cpu Seconds"
    )
    gpu_seconds: float | None = Field(
        None, description="GPU seconds in the sample.", title="Gpu Seconds"
    )
    id: str = Field(..., description="Row identifier (UUID).", title="Id")
    memory_gb_seconds: float | None = Field(
        None, description="Memory GB-seconds in the sample.", title="Memory Gb Seconds"
    )
    namespace: str | None = Field(
        None,
        description="Your organization's workload namespace the sample was taken in.",
        title="Namespace",
    )
    pod_count: int | None = Field(
        None, description="Pods running when sampled.", title="Pod Count"
    )
    timestamp: str | None = Field(
        None, description="When the usage was sampled (ISO 8601).", title="Timestamp"
    )
    total_cost_usd: float | None = Field(
        None, description="Cost including overhead, USD.", title="Total Cost Usd"
    )


class UsageSnapshotPage(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    entries: list[UsageSnapshotEntry] = Field(
        ..., description="This page, newest first.", title="Entries"
    )
    total_count: int = Field(
        ...,
        description="Snapshots in the window, across all pages.",
        title="Total Count",
    )


class UsageSummaryResponse(BaseModel):
    """
    ``GET /v1/billing/usage-summary`` — quota/usage summary. Each metric is a
    block of used/limit/remaining values.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    cu_hours: dict[str, Any] | None = Field(None, title="Cu Hours")
    egress_gb: dict[str, Any] | None = Field(None, title="Egress Gb")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    platform_tokens: dict[str, Any] | None = Field(None, title="Platform Tokens")
    storage_gb: dict[str, Any] | None = Field(None, title="Storage Gb")


class ValidationLocation(BaseModel):
    """
    Where in the script a finding applies.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    column: int | None = Field(
        None, description="1-based column number.", title="Column"
    )
    line: int | None = Field(None, description="1-based line number.", title="Line")


class ValidationSummary(BaseModel):
    """
    Counts of findings by severity.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    errors: int | None = Field(
        None, description="Number of findings that block a save.", title="Errors"
    )
    info: int | None = Field(
        None, description="Number of informational findings.", title="Info"
    )
    unverifiable: int | None = Field(
        None,
        description="Findings the validator could not decide. A cross-cut of `errors`, not a fourth severity.",
        title="Unverifiable",
    )
    warnings: int | None = Field(
        None,
        description="Number of findings that do not block a save.",
        title="Warnings",
    )


class WebhookCreate(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(
        None,
        description="What the webhook is for, in your own words.",
        title="Description",
    )
    events: list[str] | None = Field(
        None,
        description="The event types to deliver, each one `GET /v1/webhooks/event-types` lists. Omit it, or send an empty list, to receive every event type.",
        title="Events",
    )
    is_enabled: bool | None = Field(
        None,
        description="Whether events are delivered to the webhook. A disabled webhook keeps its subscriptions and receives nothing. Defaults to `true`.",
        title="Is Enabled",
    )
    name: str = Field(
        ...,
        description="A name for the webhook, shown wherever the webhook is listed.",
        title="Name",
    )
    secret: str = Field(
        ...,
        description="The secret deliveries are signed with, at least 16 characters. It is stored and never returned by any response, so keep your own copy.",
        title="Secret",
    )
    url: str = Field(
        ...,
        description="The endpoint deliveries are sent to. It must begin with `https://`; any other scheme is refused with `400`.",
        title="Url",
    )


class WebhookDeliveryRead(BaseModel):
    """
    One attempt to deliver an event to a webhook subscriber.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    attempts: int | None = Field(None, title="Attempts")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    event_id: str | None = Field(None, title="Event Id")
    event_type: str | None = Field(None, title="Event Type")
    id: str = Field(..., title="Id")
    last_attempt_at: str | None = Field(None, title="Last Attempt At")
    max_attempts: int | None = Field(None, title="Max Attempts")
    response_code: int | None = Field(None, title="Response Code")
    status: str | None = Field(None, title="Status")
    webhook_id: str = Field(..., title="Webhook Id")


class WebhookEventTypeRead(BaseModel):
    """
    One event type a webhook may subscribe to now.
    """

    data: dict[str, Any] = Field(
        ...,
        description="The JSON Schema (draft 2020-12) of the `data` object a delivery of this event type carries. Every property is closed: no field outside the schema is sent.",
        title="Data",
    )
    description: str = Field(
        ...,
        description="What happened when this event is delivered.",
        title="Description",
    )
    name: str = Field(
        ...,
        description="The event type, as it appears in a webhook's `events` list and in the `event_type` of each delivery, for example `review.completed`.",
        title="Name",
    )
    version: int = Field(
        ...,
        description="The version of the delivery's `data` object for this event type. A change that removes or retypes a field is published as a new version.",
        title="Version",
    )


class WebhookRead(BaseModel):
    """
    A webhook subscription registered by your organization.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    consecutive_failures: int | None = Field(None, title="Consecutive Failures")
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    events: list[str] | None = Field(None, title="Events")
    id: str = Field(..., title="Id")
    is_enabled: bool | None = Field(None, title="Is Enabled")
    name: str = Field(..., title="Name")
    url: str = Field(..., title="Url")


class WebhookTestResult(BaseModel):
    """
    Result of a test webhook delivery.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    delivered: bool | None = Field(None, title="Delivered")
    error: str | None = Field(None, title="Error")
    response_code: int | None = Field(None, title="Response Code")


class WebhookUpdate(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(
        None,
        description="What the webhook is for, in your own words.",
        title="Description",
    )
    events: list[str] | None = Field(
        None,
        description="The complete new list of event types to deliver. A type it adds must be one `GET /v1/webhooks/event-types` lists; a type the webhook already subscribes to is kept even when it is no longer listed.",
        title="Events",
    )
    is_enabled: bool | None = Field(
        None,
        description="Whether events are delivered to the webhook. A disabled webhook keeps its subscriptions and receives nothing.",
        title="Is Enabled",
    )
    name: str | None = Field(
        None,
        description="A name for the webhook, shown wherever the webhook is listed.",
        title="Name",
    )
    secret: str | None = Field(
        None,
        description="A replacement signing secret, at least 16 characters. Deliveries are signed with it from then on, and it is never returned.",
        title="Secret",
    )
    url: str | None = Field(
        None,
        description="The endpoint deliveries are sent to. It must begin with `https://`; any other scheme is refused with `400`.",
        title="Url",
    )


class WhoamiResponse(BaseModel):
    """
    Self-introspection payload for the authenticated caller (A8).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    effective_privileges: list[str] | None = Field(
        None,
        description="Org-level privileges the caller resolves to through the RBAC engine.",
        title="Effective Privileges",
    )
    endpoint_access: dict[str, Any] | None = Field(
        None,
        description='The calling API key\'s endpoint_access policy (``{"allow_all": true}`` for keys with no scoped policy and for users).',
        title="Endpoint Access",
    )
    id: str = Field(
        ...,
        description="Service-account key id (or user sub) of the caller.",
        title="Id",
    )
    is_admin: bool | None = Field(
        False,
        description="Convenience flag: true when the caller has ORG_MANAGE_MEMBERS.",
        title="Is Admin",
    )
    kind: str | None = Field(
        None,
        description='Principal kind: "service_account" or "system". Other values are reserved and may appear in future; clients MUST tolerate unknown values rather than failing on them.',
        title="Kind",
    )
    modes: list[str] | None = Field(
        None,
        description='Authentication modes this principal accepts: a subset of ["api_key", "hmac"].',
        title="Modes",
    )
    organization: PrincipalOrganization | None = Field(
        None,
        description='The principal\'s organization, or null when it has none. Non-null for a "system" principal: by design, a system principal always belongs to the system organization.',
    )
    organization_id: str | None = Field(
        None, description="Resolved organization UUID, if any.", title="Organization Id"
    )
    organization_name: str | None = Field(
        None,
        description="Resolved organization name, if any.",
        title="Organization Name",
    )
    roles: list[str] | None = Field(
        None, description="Role names on the caller's organization.", title="Roles"
    )
    type: str = Field(
        ..., description='Principal type: "service_account" or "user".', title="Type"
    )


class ActivityResponse(BaseModel):
    """
    The inputs queued for, running on, and recently finished by one capability.
    """

    counts: ActivityCounts | None = Field(None, description="Totals by state.")
    queued: list[QueueItem] = Field(
        ..., description="Inputs still waiting.", title="Queued"
    )
    recent: list[QueueItem] = Field(
        ..., description="Inputs that recently finished.", title="Recent"
    )
    running: list[QueueItem] = Field(
        ..., description="Inputs running now.", title="Running"
    )


class AlertListResponse(BaseModel):
    """
    A page of alerts.
    """

    has_more: bool = Field(..., title="Has More")
    items: list[AlertRead] = Field(..., title="Items")
    total: int = Field(..., title="Total")
