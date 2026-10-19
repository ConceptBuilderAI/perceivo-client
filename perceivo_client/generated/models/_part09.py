# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class InfrastructureCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/infrastructure``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    categories: list[dict[str, Any]] | None = Field(None, title="Categories")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")
    totals: dict[str, Any] | None = Field(None, title="Totals")


class InfrastructureServiceType(StrEnum):
    """
    The infrastructure service to operate on.
    """

    elasticsearch = "elasticsearch"
    mcp = "mcp"
    milvus = "milvus"
    redis = "redis"


class IngestJob(BaseModel):
    """
    An ingest job: its state, its counts and the source it was created from.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    chunks_inserted: int = Field(
        ..., description="Chunks written to the store.", title="Chunks Inserted"
    )
    created_at: AwareDatetime | None = Field(
        None, description="When the job was created.", title="Created At"
    )
    embedding_tokens: int = Field(
        ..., description="Embedding tokens spent by this job.", title="Embedding Tokens"
    )
    files_failed: int = Field(
        ...,
        description="Files that failed, each with a reason code.",
        title="Files Failed",
    )
    files_pending: int = Field(
        ..., description="Files not yet finished.", title="Files Pending"
    )
    files_succeeded: int = Field(
        ..., description="Files ingested.", title="Files Succeeded"
    )
    files_total: int | None = Field(
        None,
        description="Files in the job; absent until a folder has been read.",
        title="Files Total",
    )
    finished_at: AwareDatetime | None = Field(
        None, description="When the job ended.", title="Finished At"
    )
    id: str = Field(..., description="The job id.", title="Id")
    resumed_from: str | None = Field(
        None,
        description="The job this one resumes, when it is a resume.",
        title="Resumed From",
    )
    source: dict[str, Any] = Field(
        ..., description="The source as submitted.", title="Source"
    )
    started_at: AwareDatetime | None = Field(
        None, description="When processing first started.", title="Started At"
    )
    status: str = Field(
        ...,
        description="`queued`, `running`, `completed`, `completed_with_errors`, `failed`, `cancelling` or `cancelled`.",
        title="Status",
    )
    store: str = Field(..., description="`milvus` or `elasticsearch`.", title="Store")
    target: str = Field(
        ..., description="The collection or index the job writes to.", title="Target"
    )
    version: int = Field(
        ...,
        description="The job's version; send it as `If-Match` to resume. Also the `ETag`.",
        title="Version",
    )


class IngestJobFile(BaseModel):
    """
    One file of an ingest job and how it ended.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    chunks_inserted: int = Field(
        ...,
        description="Chunks of this file written to the store.",
        title="Chunks Inserted",
    )
    entry_id: str = Field(..., description="The file entry.", title="Entry Id")
    name: str | None = Field(None, description="The file's name.", title="Name")
    reason: str | None = Field(
        None, description="Fixed text for `reason_code`.", title="Reason"
    )
    reason_code: str | None = Field(
        None,
        description="Why the file did not succeed, from a closed set of codes.",
        title="Reason Code",
    )
    status: str = Field(
        ...,
        description="`pending`, `running`, `succeeded`, `failed`, `skipped` or `cancelled`.",
        title="Status",
    )


class IngestJobFilePage(BaseModel):
    """
    One page of an ingest job's files.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[IngestJobFile] = Field(
        ..., description="The files in this page.", title="Items"
    )
    next: str | None = Field(
        None,
        description="Cursor for the next page (`after`), or absent when last.",
        title="Next",
    )


class IngestJobPage(BaseModel):
    """
    One page of a container's ingest jobs, most recent first.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[IngestJob] = Field(
        ..., description="The jobs in this page.", title="Items"
    )
    next: str | None = Field(
        None,
        description="Cursor for the next page (`before`), or absent when last.",
        title="Next",
    )


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


class IntelligenceRuntimeRead(BaseModel):
    """
    The intelligence asset's runtime record after the stop.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str = Field(..., title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    organization_id: str = Field(..., title="Organization Id")
    service_endpoints: dict[str, str] | None = Field(None, title="Service Endpoints")
    started_at: str | None = Field(None, title="Started At")
    status: str = Field(
        ...,
        description="STOPPED, STARTING, RUNNING, STOPPING, FAILED or DEGRADED.",
        title="Status",
    )
    stopped_at: str | None = Field(None, title="Stopped At")
    updated_at: str = Field(..., title="Updated At")


class IntelligenceServiceStatusRead(BaseModel):
    """
    A service the intelligence asset configures.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    name: str = Field(..., title="Name")
    ready_replicas: int | None = Field(None, title="Ready Replicas")
    replicas: int | None = Field(None, title="Replicas")
    status: str = Field(..., title="Status")
    type: str = Field(..., title="Type")
    url: str | None = Field(None, title="Url")


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


class IntelligenceStartResult(BaseModel):
    """
    The start was accepted. Poll the asset's status for readiness.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    job_ids: dict[str, str] | None = Field(
        None,
        description="Queued job per service type; empty when nothing was queued.",
        title="Job Ids",
    )
    message: str = Field(..., title="Message")
    status: str = Field(
        ...,
        description="The runtime's status once the start was accepted.",
        title="Status",
    )


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
