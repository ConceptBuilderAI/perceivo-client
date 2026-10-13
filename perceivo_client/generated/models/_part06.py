# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class DedicatedDatabaseRead(BaseModel):
    """
    One dedicated PostgreSQL database in your organization.
    """

    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    compute_tier: str | None = Field(None, title="Compute Tier")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    high_availability: str | None = Field(None, title="High Availability")
    hourly_rate_usd: float | None = Field(None, title="Hourly Rate Usd")
    id: str = Field(..., title="Id")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    last_activity_at: str | None = Field(None, title="Last Activity At")
    memory_gb: float | None = Field(None, title="Memory Gb")
    name: str | None = Field(None, title="Name")
    organization_id: str = Field(..., title="Organization Id")
    postgres_version: str | None = Field(None, title="Postgres Version")
    provisioned_at: str | None = Field(None, title="Provisioned At")
    sku: str | None = Field(None, title="Sku")
    status: str = Field(
        ...,
        description="Lifecycle state: pending, provisioning, starting, running, stopping, stopped, failed, deleting or deleted. A started database is ready when this is `running`.",
        title="Status",
    )
    stopped_at: str | None = Field(None, title="Stopped At")
    storage_gb: int | None = Field(None, title="Storage Gb")
    updated_at: str | None = Field(None, title="Updated At")
    vcpu_count: int | None = Field(None, title="Vcpu Count")


class DedicatedDatabaseStartAccepted(BaseModel):
    """
    Acknowledgement that a dedicated database start was accepted.
    """

    database_id: str = Field(..., title="Database Id")
    message: str | None = Field(None, title="Message")
    status: str = Field(
        ..., description="`accepted` when the start request was taken.", title="Status"
    )


class DocumentUploadResponse(BaseModel):
    """
    Result of a document upload.

    ``collection`` is set for vector-store uploads, ``key_prefix`` for
    key-value uploads.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    collection: str | None = Field(None, title="Collection")
    embedding_model: str | None = Field(None, title="Embedding Model")
    files: list[dict[str, Any]] | None = Field([], title="Files")
    key_prefix: str | None = Field(None, title="Key Prefix")
    total_chunks: int | None = Field(None, title="Total Chunks")
    total_inserted: int | None = Field(None, title="Total Inserted")


class DriftBaselineRead(BaseModel):
    """
    A drift-detection baseline.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_path: str = Field(..., title="Artifact Path")
    baseline_type: str = Field(..., title="Baseline Type")
    created_at: str | None = Field(None, title="Created At")
    created_by_user_sub: str | None = Field(None, title="Created By User Sub")
    description: str | None = Field(None, title="Description")
    feature_schema: list[dict[str, Any]] | None = Field([], title="Feature Schema")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    is_active: bool | None = Field(True, title="Is Active")
    model_family_id: str | None = Field(None, title="Model Family Id")
    name: str = Field(..., title="Name")
    sample_count: int = Field(..., title="Sample Count")
    source_end: str | None = Field(None, title="Source End")
    source_start: str | None = Field(None, title="Source Start")
    training_job_id: str | None = Field(None, title="Training Job Id")


class DatasetDriftThreshold(RootModel[float]):
    root: float = Field(
        ...,
        description="Dataset-level drift threshold, 0 to 1. Omitted or null keeps the current value.",
        ge=0.0,
        le=1.0,
        title="Dataset Drift Threshold",
    )


class FeatureDriftThreshold(RootModel[float]):
    root: float = Field(
        ...,
        description="Per-feature drift threshold, 0 to 1. Omitted or null keeps the current value.",
        ge=0.0,
        le=1.0,
        title="Feature Drift Threshold",
    )


class Threshold(RootModel[float]):
    root: float = Field(..., ge=0.0, le=1.0, title="Threshold")


class DriftMetricSetting(BaseModel):
    """
    Settings for one drift metric.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    enabled: bool | None = Field(True, title="Enabled")
    method: str | None = Field(None, title="Method")
    threshold: Threshold | None = Field(None, title="Threshold")


class EgressUsageResponse(BaseModel):
    """
    ``GET /v1/billing/egress-usage``. The old ``UsageResponse`` stub required a
    top-level ``organization_id`` this payload does not carry.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    by_destination: list[dict[str, Any]] | None = Field(None, title="By Destination")
    entries: list[dict[str, Any]] | None = Field(None, title="Entries")
    summary: dict[str, Any] | None = Field(None, title="Summary")
    total_count: int | None = Field(None, title="Total Count")


class EndpointAccess(BaseModel):
    """
    Endpoint access confinement for a service account (API key).

    ``allow_all=true`` grants every endpoint. ``allow_all=false`` confines the
    key to endpoints whose domain group is listed in ``groups``, or whose exact
    ``METHOD /path`` string is listed in ``endpoints``. An entry is not the
    ``/v1`` path published in this reference: ``GET /v1/whoami`` is matched by
    the entry ``GET /auth/whoami``, and ``GET /whoami`` never matches. An
    endpoint_access refusal names the refused endpoint in exactly the accepted
    form, so copy that value verbatim. The webhook and organization
    infrastructure endpoints are the exception to the shape of that example:
    their accepted entry is longer than the route name, so for those always
    copy the refused value rather than deriving one.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    allow_all: bool | None = Field(
        True,
        description="If true, the key may reach every endpoint. If false, access is limited to what `groups` and `endpoints` grant.",
        title="Allow All",
    )
    endpoints: list[str] | None = Field(
        None,
        description="Individual endpoints in 'METHOD /path' form. An entry is not the '/v1' path published in this reference: GET /v1/whoami is matched by the entry 'GET /auth/whoami', and 'GET /whoami' never matches. An endpoint_access refusal (403) names the refused endpoint in exactly the accepted form, so copy the value it reports verbatim. The webhook and organization infrastructure endpoints are the exception to the shape of that example: their accepted entry is longer than the route name, so for those always copy the refused value rather than deriving one.",
        title="Endpoints",
    )
    groups: list[str] | None = Field(
        None,
        description="Endpoint groups the key may access, e.g. 'orchestrations'.",
        title="Groups",
    )


class EntryType(StrEnum):
    """
    Kind of file-manager entry.
    """

    file = "file"
    folder = "folder"


class ErrorResponse(BaseModel):
    """
    Standard error envelope.

    Every response this contract declares with this schema uses this shape: validation failures (422), whose field errors are under `details.errors`. Errors raised by route handlers and unhandled exceptions use it too.

    It is not the only error shape on the wire. 401, 403 and 404 are declared on the operations that can return them without a body schema, because their bodies differ by producer. Authentication, account-lock and rate-limit refusals may be returned before routing, and 401, 403 or 429 may also be returned with a different body after routing; 404 and 405 from the router use another shape. 429 and 405 are not declared. Do not assume this envelope, or any header set, for a status an operation does not declare with this schema.

    A request body over the size limit is refused with 413 by the request-size layer, not by the operation. That response is not this envelope: its body has the keys `error`, `reason` and `limit_bytes`. The default limit is 1 MiB, and `limit_bytes` states the limit that applied. An operation that accepts a larger body states its limit in its description. The signature check on a signed request has its own limit, 1 MiB by default, and its 413 carries `error` and `reason` only. The same layers answer 503 while request-body capacity is in use and 408 when a body is not received in time, each with the keys `error` and `reason`. These refusals carry those bodies even on an operation that declares 413, 503 or 408 with this schema.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    correlation_id: str = Field(
        ..., description="X-Correlation-Id for log correlation.", title="Correlation Id"
    )
    crash_report_id: str | None = Field(
        None,
        description="Set in prod mode when a crash report was emitted.",
        title="Crash Report Id",
    )
    details: dict[str, Any] | None = Field(
        None, description="Structured context. JSON-safe values only.", title="Details"
    )
    error_code: str = Field(
        ..., description="Registered code, e.g. PCV-DATA-NOTF-0001", title="Error Code"
    )
    message: str = Field(
        ..., description="Human-readable; never includes secrets.", title="Message"
    )
    service: str = Field(
        ...,
        description="Opaque identifier for the platform component that produced this error. Quote it when reporting a problem; do not branch on its value — it is not part of the stable contract.",
        title="Service",
    )
    timestamp: str = Field(
        ..., description="ISO-8601 UTC timestamp.", title="Timestamp"
    )
    trace_id: str | None = Field(
        None, description="Distributed trace id.", title="Trace Id"
    )


class EvaluateRequest(BaseModel):
    """
    Trigger an evaluation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")


class EvaluationRead(BaseModel):
    """
    Intelligence evaluation result.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    scores: dict[str, Any] | None = Field(None, title="Scores")
    status: str = Field(..., title="Status")


class EvaluationRunRead(BaseModel):
    """
    Capability evaluation run.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str = Field(..., title="Capability Id")
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    status: str | None = Field(None, title="Status")


class EvaluationTriggerResponse(BaseModel):
    """
    Acknowledgement returned when an evaluation is triggered.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str | None = Field(None, title="Capability Id")
    evaluation_id: str | None = Field(None, title="Evaluation Id")
    status: str | None = Field(None, title="Status")


class EventPage(BaseModel):
    """
    A bounded slice of audit and state-change events, newest first.

    Each event describes one state-changing action taken against the
    organization — who acted, on what, when, and the outcome. The audit trail is
    forward-only: it records actions taken from the moment the capability became
    available, so an empty page for an early time window means no recorded
    actions in that window, not an unmonitored subsystem. Individual event fields
    are passed through.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    count: int | None = Field(None, title="Count")
    events: list[dict[str, Any]] | None = Field(None, title="Events")
    has_more: bool | None = Field(None, title="Has More")
    limit: int | None = Field(None, title="Limit")
    organization_id: str | None = Field(None, title="Organization Id")


class ExecuteCapabilityRequest(BaseModel):
    """
    Run a capability. A prompt or input goes inside ``config``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact: dict[str, Any] | None = Field(
        None, description="Artifact to send with the run.", title="Artifact"
    )
    config: dict[str, Any] | None = Field(
        None, description="Request data for the run.", title="Config"
    )


class ExecuteResponseRead(BaseModel):
    """
    Response from executing an orchestration action.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    action: str | None = Field(None, title="Action")
    message: str | None = Field(None, title="Message")
    result: dict[str, Any] | None = Field(None, title="Result")
    success: bool | None = Field(None, title="Success")
    target_id: str | None = Field(None, title="Target Id")


class ExecutionGraphBuildResponse(BaseModel):
    """
    Summary of a freshly-built execution graph.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    blob_path: str | None = Field(None, title="Blob Path")
    capability_id: str | None = Field(None, title="Capability Id")
    created_at: str | None = Field(None, title="Created At")
    entry_count: int | None = Field(None, title="Entry Count")
    graph_id: str | None = Field(None, title="Graph Id")
    graph_type: str | None = Field(None, title="Graph Type")
    orchestration_summary: dict[str, Any] | None = Field(
        None, title="Orchestration Summary"
    )


class ExecutionGraphConfigRead(BaseModel):
    """
    A saved execution-graph build configuration.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    blackbox_fsm_nodes: bool | None = Field(None, title="Blackbox Fsm Nodes")
    capability_id: str | None = Field(None, title="Capability Id")
    created_at: str | None = Field(None, title="Created At")
    created_by_user_sub: str | None = Field(None, title="Created By User Sub")
    cron_expression: str | None = Field(None, title="Cron Expression")
    cron_timezone: str | None = Field(None, title="Cron Timezone")
    description: str | None = Field(None, title="Description")
    enabled: bool | None = Field(None, title="Enabled")
    exclude_direct_triggers: bool | None = Field(None, title="Exclude Direct Triggers")
    exclude_intermediate_artifacts: bool | None = Field(
        None, title="Exclude Intermediate Artifacts"
    )
    exclude_unreviewed: bool | None = Field(None, title="Exclude Unreviewed")
    fsm_node_id: str | None = Field(None, title="Fsm Node Id")
    graph_type: str | None = Field(None, title="Graph Type")
    id: str | None = Field(None, title="Id")
    include_unscored: bool | None = Field(None, title="Include Unscored")
    last_built_at: str | None = Field(None, title="Last Built At")
    last_graph_id: str | None = Field(None, title="Last Graph Id")
    log_types: list[Any] | None = Field(None, title="Log Types")
    name: str | None = Field(None, title="Name")
    orchestration_ids: list[Any] | None = Field(None, title="Orchestration Ids")
    organization_id: str | None = Field(None, title="Organization Id")
    retain_last_n: int | None = Field(None, title="Retain Last N")
    rolling_window_hours: int | None = Field(None, title="Rolling Window Hours")
    schedule_end: str | None = Field(None, title="Schedule End")
    schedule_start: str | None = Field(None, title="Schedule Start")
    target_intelligence_id: str | None = Field(None, title="Target Intelligence Id")
    triggers_feature_ingest: bool | None = Field(None, title="Triggers Feature Ingest")
    updated_at: str | None = Field(None, title="Updated At")


class ExecutionGraphRead(BaseModel):
    """
    Execution graph representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str = Field(..., title="Capability Id")
    config: dict[str, Any] | None = Field(None, title="Config")
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")


class ExperimentCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/experiment/{experiment_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    children: list[dict[str, Any]] | None = Field(None, title="Children")
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    entry_count: int | None = Field(None, title="Entry Count")
    experiment_id: str | None = Field(None, title="Experiment Id")
    experiment_name: str | None = Field(None, title="Experiment Name")
    first_billed_at: str | None = Field(None, title="First Billed At")
    last_billed_at: str | None = Field(None, title="Last Billed At")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    llm_managed_cost_usd: float | None = Field(None, title="Llm Managed Cost Usd")
    llm_user_cost_usd: float | None = Field(None, title="Llm User Cost Usd")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    summary: dict[str, Any] | None = Field(None, title="Summary")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")
    uptime_seconds: float | None = Field(None, title="Uptime Seconds")


class ExperimentCreate(BaseModel):
    """
    Body for ``POST /v1/experiments``.

    The experiment is created in the organization your API key belongs to and is
    owned by the credential you presented. Neither can be chosen in the body.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_config: dict[str, Any] | None = Field(
        None,
        description="The resources the experiment's session is started with, such as its CPU, memory and GPU requests. It is read each time the experiment is run.",
        title="Compute Config",
    )
    description: str | None = Field(
        None,
        description="What the experiment is for, in your own words.",
        title="Description",
    )
    name: str = Field(
        ...,
        description="A name for the experiment, shown wherever the experiment is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )
