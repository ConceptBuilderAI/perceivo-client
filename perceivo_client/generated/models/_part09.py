# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class IngestRequest(BaseModel):
    """
    Trigger data ingestion.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")


class IngestResponse(BaseModel):
    """
    Response from an ingest trigger.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    job_id: str | None = Field(None, title="Job Id")
    message: str | None = Field(None, title="Message")
    operation_id: str | None = Field(None, title="Operation Id")
    records_loaded: int | None = Field(None, title="Records Loaded")
    status: str | None = Field(None, title="Status")


class IngestTriggerRead(BaseModel):
    """
    A configured trigger.

    ``http_token`` is returned only on the create and update responses, and only
    when ``http_enabled`` is set. It is shown **once** and cannot be read back
    afterwards — store it when you receive it, or issue a new trigger.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")
    created_at: str | None = Field(None, title="Created At")
    created_by_user_sub: str | None = Field(None, title="Created By User Sub")
    cron_enabled: bool | None = Field(None, title="Cron Enabled")
    cron_expression: str | None = Field(None, title="Cron Expression")
    cron_timezone: str | None = Field(None, title="Cron Timezone")
    execution_count: int | None = Field(None, title="Execution Count")
    http_enabled: bool | None = Field(None, title="Http Enabled")
    http_endpoint_url: str | None = Field(None, title="Http Endpoint Url")
    http_token: str | None = Field(None, title="Http Token")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    is_active: bool | None = Field(None, title="Is Active")
    last_executed_at: str | None = Field(None, title="Last Executed At")
    next_execution_at: str | None = Field(None, title="Next Execution At")
    trigger_type: str | None = Field(None, title="Trigger Type")
    updated_at: str | None = Field(None, title="Updated At")


class IngestTriggerType(StrEnum):
    """
    What a trigger fires.

    ``feature_ingest`` loads data into the feature store.
    ``online_evaluation`` evaluates the model on live traffic, and
    ``drift_evaluation`` checks the features for drift.
    """

    feature_ingest = "feature_ingest"
    online_evaluation = "online_evaluation"
    drift_evaluation = "drift_evaluation"


class IngestTriggerUpdate(BaseModel):
    """
    Update a trigger. Every field is optional; omitted fields are unchanged.
    """

    config: dict[str, Any] | None = Field(None, title="Config")
    cron_enabled: bool | None = Field(None, title="Cron Enabled")
    cron_expression: str | None = Field(None, title="Cron Expression")
    cron_timezone: str | None = Field(None, title="Cron Timezone")
    http_enabled: bool | None = Field(None, title="Http Enabled")
    is_active: bool | None = Field(None, title="Is Active")


class IntelligenceCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/intelligence/{intelligence_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    children: list[dict[str, Any]] | None = Field(None, title="Children")
    component_costs: list[dict[str, Any]] | None = Field(None, title="Component Costs")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    intelligence_name: str | None = Field(None, title="Intelligence Name")
    organization_id: str | None = Field(None, title="Organization Id")
    period: dict[str, Any] | None = Field(None, title="Period")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    summary: dict[str, Any] | None = Field(None, title="Summary")


class IntelligenceCreate(BaseModel):
    """
    Create a new intelligence asset.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")
    description: str | None = Field(None, title="Description")
    model_families: list[dict[str, Any]] | None = Field(None, title="Model Families")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")


class IntelligenceExport(BaseModel):
    """
    Self-contained intelligence export bundle.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_images: dict[str, Any] | None = Field(None, title="Capability Images")
    components: dict[str, Any] | None = Field(None, title="Components")
    export_type: str | None = Field(None, title="Export Type")
    export_version: str | None = Field(None, title="Export Version")
    exported_at: str | None = Field(None, title="Exported At")
    intelligence: dict[str, Any] | None = Field(None, title="Intelligence")
    model_families: list[dict[str, Any]] | None = Field(None, title="Model Families")
    services: list[dict[str, Any]] | None = Field(None, title="Services")


class IntelligenceImportResult(BaseModel):
    """
    Result of an intelligence import operation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    asset_id: str | None = Field(None, title="Asset Id")
    asset_name: str | None = Field(None, title="Asset Name")
    component_ids: list[str] | None = Field(None, title="Component Ids")
    components_created: int | None = Field(None, title="Components Created")
    model_families_created: int | None = Field(None, title="Model Families Created")
    services_created: int | None = Field(None, title="Services Created")
    success: bool | None = Field(None, title="Success")
    validation_warnings: list[str] | None = Field(None, title="Validation Warnings")


class IntelligenceMaterializeRequest(BaseModel):
    """
    Which feature data to materialize into the online store.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    end_date: str | None = Field(
        None, description="ISO 8601 end of the range, for `custom`", title="End Date"
    )
    feature_views: list[str] | None = Field(
        None,
        description="Feature views to materialize. All of them when omitted.",
        title="Feature Views",
    )
    scope: str | None = Field(
        "last_ingest",
        description="`last_ingest` (default), `last_24h`, or `custom` with a date range",
        title="Scope",
    )
    start_date: str | None = Field(
        None,
        description="ISO 8601 start of the range, for `custom`",
        title="Start Date",
    )


class IntelligenceRead(BaseModel):
    """
    Intelligence resource representation.
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


class IntelligenceSnapshotsResponse(BaseModel):
    """
    ``GET /v1/billing/intelligence-snapshots`` — paginated snapshots.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    limit: int | None = Field(None, title="Limit")
    offset: int | None = Field(None, title="Offset")
    snapshots: list[dict[str, Any]] | None = Field(None, title="Snapshots")
    total: int | None = Field(None, title="Total")


class IntelligenceStatusRead(BaseModel):
    """
    Intelligence runtime status.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    intelligence_id: str = Field(..., title="Intelligence Id")
    runtime_status: dict[str, Any] | None = Field(None, title="Runtime Status")
    status: str = Field(..., title="Status")


class Source(StrEnum):
    manual = "manual"
    recommendation = "recommendation"
    rollback = "rollback"


class IntelligenceTrafficPlanModel(BaseModel):
    """
    One model's role and share within a model family.
    """

    model_id: UUID = Field(..., title="Model Id")
    role: str = Field(..., description="`champion`, `canary` or `shadow`", title="Role")
    traffic_percent: int = Field(..., title="Traffic Percent")


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
