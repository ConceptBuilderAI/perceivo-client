# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class CreateFolderEntry(BaseModel):
    """
    A folder to create in a storage space.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    name: str = Field(..., description="Folder name", max_length=255, title="Name")
    parent_id: UUID | None = Field(
        None,
        description="Parent folder; null creates at the space root",
        title="Parent Id",
    )
    type: Literal["folder"] = Field(
        ..., description="Discriminator: create a folder", title="Type"
    )


class CreateGraphConfigRequestDescription(RootModel[str]):
    root: str = Field(..., max_length=1000, title="Description")


class CreateGraphConfigRequest(BaseModel):
    """
    Create a graph configuration.

    The capability comes from the path, and the organization and author from the
    caller's credentials, so none of them is a body field. A field not listed
    here is refused with 422.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    blackbox_fsm_nodes: bool | None = Field(False, title="Blackbox Fsm Nodes")
    cron_expression: str | None = Field(None, title="Cron Expression")
    cron_timezone: str | None = Field("UTC", title="Cron Timezone")
    description: CreateGraphConfigRequestDescription | None = Field(
        None, title="Description"
    )
    enabled: bool | None = Field(True, title="Enabled")
    exclude_direct_triggers: bool | None = Field(True, title="Exclude Direct Triggers")
    exclude_intermediate_artifacts: bool | None = Field(
        False, title="Exclude Intermediate Artifacts"
    )
    exclude_unreviewed: bool | None = Field(False, title="Exclude Unreviewed")
    fsm_node_id: UUID | None = Field(None, title="Fsm Node Id")
    graph_type: str | None = Field("full_run", title="Graph Type")
    include_unscored: bool | None = Field(False, title="Include Unscored")
    log_types: list[str] | None = Field(None, title="Log Types")
    name: str = Field(..., max_length=255, title="Name")
    orchestration_ids: list[str] | None = Field(None, title="Orchestration Ids")
    retain_last_n: int | None = Field(10, title="Retain Last N")
    rolling_window_hours: int | None = Field(
        168,
        description="Hours of history for scheduled builds",
        title="Rolling Window Hours",
    )
    schedule_end: AwareDatetime | None = Field(None, title="Schedule End")
    schedule_start: AwareDatetime | None = Field(None, title="Schedule Start")
    target_intelligence_id: UUID | None = Field(None, title="Target Intelligence Id")
    triggers_feature_ingest: bool | None = Field(False, title="Triggers Feature Ingest")


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


class DetailRefusal(BaseModel):
    """
    An error answered by the router or by a platform component behind this service. `detail` is usually a sentence; a validation refusal from a platform component carries a list.
    """

    detail: Any = Field(..., description="What was refused, and why.")


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


class EdgeRefusal(BaseModel):
    """
    An error refused before the request is routed, or by this service's own edge checks. `error` is a short machine-readable code such as `unauthorized`, `forbidden`, `organization_suspended`, `organization_unavailable`, `not_found` or `rate_limited`; some refusals add `reason`.
    """

    error: Any = Field(..., description="Machine-readable error code.")
    reason: str | None = Field(None, description="Further detail, when given.")


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


class EmptyTrashResult(BaseModel):
    """
    How many trashed entries were permanently deleted.

    200 with ``deleted_count``, or 202 with ``message`` added while the stored
    content is still being cleaned up in the background.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    deleted_count: int = Field(
        ..., description="Trashed entries permanently deleted.", title="Deleted Count"
    )
    message: str | None = Field(
        None,
        description="Present on 202 only: the background clean-up still in progress.",
        title="Message",
    )


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

    Every response this contract declares with this schema uses this shape: validation failures (422), whose field errors are under `details.errors`. Errors raised by route handlers and unhandled exceptions use it too, and so does every 400, 403, 404, 409 and 415 answered after routing: `error_code` is `PCV-APIS-VAL-0001` (400, 415), `PCV-APIS-AUTH-0001` (403), `PCV-APIS-NOTF-0001` (404) or `PCV-APIS-CONF-0001` (409), and the refusing component's original body is under `details`, unless that component set a code of its own.

    It is not the only error shape on the wire. 401, 403 and 404 are declared on the operations that can return them with the `RefusalBody` schema: this envelope, `{"error": ...}` (`EdgeRefusal`) or `{"detail": ...}` (`DetailRefusal`), because their bodies differ by producer. Authentication, account-lock and rate-limit refusals may be returned before routing, and 401, 403 or 429 may also be returned with a different body after routing; 404 and 405 from the router use another shape. 429 is declared on every rate-limited operation with the `RefusalBody` schema and a `Retry-After` header. 405 is not declared: it answers only a method an operation does not declare. Do not assume this envelope, or any header set, for a status an operation does not declare with this schema.

    A request body over the size limit is refused with 413 by the request-size layer, not by the operation. That response is not this envelope: its body has the keys `error`, `reason` and `limit_bytes`. The default limit is 1 MiB, and `limit_bytes` states the limit that applied. An operation that accepts a larger body states its limit in its description. The signature check on a signed request has its own limit, 1 MiB by default, and its 413 carries `error` and `reason` only. The same layers answer 503 while request-body capacity is in use and 408 when a body is not received in time. The 408, and the 411 and 415 these layers answer, carry the keys `error` and `reason`. These refusals carry those bodies even on an operation that declares 413 or 408 with this schema. The 503, and the 503 the signature check answers while it cannot verify, is this envelope with `error_code` `PCV-APIS-DEP-0001`, `details` `{"error": "service_unavailable", "reason": ...}` and a `Retry-After` header; it is declared on every operation that API-key authentication guards.
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
