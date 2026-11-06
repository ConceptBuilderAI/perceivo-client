# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 4cb0cc1fb62e540b6329e643c14e3ed2ef7982f14766508c71bd02701feb1b21

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from ._part06 import DetailRefusal, EdgeRefusal, ErrorResponse


class PaginatedFileList(BaseModel):
    """
    A page of file-manager entries.
    """

    items: list[FileEntryRead] = Field(..., title="Items")
    page: int = Field(..., title="Page")
    page_size: int = Field(..., title="Page Size")
    total: int = Field(..., title="Total")
    total_pages: int = Field(..., title="Total Pages")


class PaginatedItemsResponse(BaseModel):
    """
    A list response: the returned items plus the full-collection total.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[dict[str, Any]] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class PiiConfig(BaseModel):
    """
    The feature views marked as carrying personally identifiable information.

    `pii_features` is a flat list of `view_name__feature_name` strings.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    pii_features: list[str] | None = Field([], title="Pii Features")


class PredictionLogRead(BaseModel):
    """
    One logged prediction.

    Only prediction metadata is retained; the model input and the prediction
    payload are not.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    correlation_id: str | None = Field(None, title="Correlation Id")
    created_at: str | None = Field(None, title="Created At")
    family_id: str | None = Field(None, title="Family Id")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    latency_ms: float | None = Field(None, title="Latency Ms")
    model_id: str | None = Field(None, title="Model Id")
    served_by: str | None = Field(None, title="Served By")


class PredictionLoggingConfig(BaseModel):
    """
    Prediction-log retention and sampling for an intelligence.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    aggregate_to_daily: bool | None = Field(True, title="Aggregate To Daily")
    aggregate_to_hourly: bool | None = Field(True, title="Aggregate To Hourly")
    created_at: str | None = Field(None, title="Created At")
    error_retention_days: int | None = Field(90, title="Error Retention Days")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    retention_days: int | None = Field(30, title="Retention Days")
    sampling_enabled: bool | None = Field(False, title="Sampling Enabled")
    sampling_rate: float | None = Field(1.0, title="Sampling Rate")
    updated_at: str | None = Field(None, title="Updated At")


class PredictionLoggingConfigWrite(BaseModel):
    """
    New prediction-log retention and sampling settings.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    aggregate_to_daily: bool | None = Field(True, title="Aggregate To Daily")
    aggregate_to_hourly: bool | None = Field(True, title="Aggregate To Hourly")
    error_retention_days: int | None = Field(
        90, ge=1, le=365, title="Error Retention Days"
    )
    retention_days: int | None = Field(30, ge=1, le=365, title="Retention Days")
    sampling_enabled: bool | None = Field(False, title="Sampling Enabled")
    sampling_rate: float | None = Field(1.0, ge=0.0, le=1.0, title="Sampling Rate")


class PredictionOutcomeCreate(BaseModel):
    """
    An outcome or feedback event to record against one prediction.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    entity_id: str | None = Field(
        None,
        description="The entity the outcome is about, such as a customer.",
        title="Entity Id",
    )
    event_type: str | None = Field(
        "feedback",
        description="The outcome event type. Defaults to `feedback`.",
        title="Event Type",
    )
    ground_truth: dict[str, Any] | None = Field(
        None,
        description='Structured ground truth, for example `{"label": "approved"}`.',
        title="Ground Truth",
    )
    item_id: str | None = Field(
        None,
        description="The item the outcome is about, such as a product.",
        title="Item Id",
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Free-form context stored with the event.", title="Metadata"
    )
    model_id: str | None = Field(
        None,
        description="The model that served the prediction, when known.",
        title="Model Id",
    )
    outcome: str | None = Field(
        None,
        description="Categorical outcome label, for example `correct`, `incorrect` or `approved`.",
        title="Outcome",
    )
    session_id: str | None = Field(
        None, description="The session the outcome was observed in.", title="Session Id"
    )
    value: float | None = Field(
        None,
        description="Numeric outcome value, such as revenue or a score.",
        title="Value",
    )


class PredictionOutcomeRecorded(BaseModel):
    """
    The outcome event that was recorded.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    event_type: str = Field(..., title="Event Type")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    logged_at: str = Field(..., title="Logged At")
    prediction_id: str = Field(..., title="Prediction Id")


class PredictionOutcomes(BaseModel):
    """
    The outcome events recorded against one prediction.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    outcomes: list[dict[str, Any]] | None = Field([], title="Outcomes")
    total: int | None = Field(0, title="Total")


class PredictionRecord(BaseModel):
    """
    One prediction record.

    ``status`` is the polling status. The terminal values are ``completed``,
    ``failed``, ``cancelled`` and ``expired``; anything else is non-terminal and
    the response carries a ``Retry-After`` header. A client MUST treat
    an unrecognised value as non-terminal rather than as an error.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_content_type: str | None = Field(None, title="Artifact Content Type")
    artifact_filename: str | None = Field(None, title="Artifact Filename")
    artifact_path: str | None = Field(None, title="Artifact Path")
    completed_at: str | None = Field(None, title="Completed At")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    model_id: str | None = Field(None, title="Model Id")
    organization_id: str = Field(..., title="Organization Id")
    request_payload: dict[str, Any] | None = Field(None, title="Request Payload")
    result_payload: dict[str, Any] | None = Field(None, title="Result Payload")
    status: str = Field(
        ...,
        description="Lifecycle state. Terminal values are completed, failed, cancelled and expired; any other value means the prediction is still in flight and the response carries Retry-After.",
        title="Status",
    )
    updated_at: str | None = Field(None, title="Updated At")
    user_sub: str | None = Field(None, title="User Sub")


class PredictionResponse(BaseModel):
    """
    Real-time single prediction result served by the deployed model.

    The ``prediction`` payload is model-defined — its concrete shape is set by the
    deployed model's inference contract — so it is typed as a free-form value rather
    than a fixed schema. ``correlation_id`` is always set so the prediction can be
    linked to later outcome events. Model-specific extras
    (e.g. ``metadata`` sub-fields) are preserved via ``extra="allow"``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    correlation_id: str | None = Field(None, title="Correlation Id")
    metadata: dict[str, Any] | None = Field(None, title="Metadata")
    model_id: str | None = Field(None, title="Model Id")
    prediction: Any | None = Field(None, title="Prediction")


class PrincipalOrganization(BaseModel):
    """
    The organization a principal belongs to.

    Non-null for a ``system`` principal: by design, a system principal always
    belongs to the system organization.
    """

    id: str = Field(..., description="Organization UUID.", title="Id")
    name: str | None = Field(
        None, description="Organization display name.", title="Name"
    )


class PrivilegeCheckResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    allowed: bool | None = Field(None, title="Allowed")
    privileges: list[str] | None = Field(None, title="Privileges")


class PromoteModelRequest(BaseModel):
    """
    Promote a model to a target stage.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")
    target_stage: str | None = Field(None, title="Target Stage")


class QueueCancelRequest(BaseModel):
    """
    Cancel the queued work of one capability.

    With `include_running` false, only work that is still waiting is dropped and
    running work is left alone. With `include_running` true, running work is
    stopped as well.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    asset_id: UUID = Field(
        ...,
        description="Identifier of the capability whose queue is cancelled.",
        title="Asset Id",
    )
    include_running: bool = Field(
        ...,
        description="Whether work that is already running is stopped too. `false` drains the backlog only; `true` also stops running work.",
        title="Include Running",
    )
    kind: Literal["input"] = Field(
        ...,
        description="The queue family. `input` is the only value served.",
        title="Kind",
    )


class QueueItem(BaseModel):
    """
    One input in the queue, as returned to a caller.

    Every field is optional and may be `null`. Input payloads, artifacts,
    callback addresses and the identity of the submitter are not returned.
    """

    capability_id: str | None = Field(
        None, description="The capability it targets.", title="Capability Id"
    )
    completed_at: str | None = Field(
        None, description="When it finished.", title="Completed At"
    )
    created_at: str | None = Field(
        None, description="When it was created.", title="Created At"
    )
    dispatched_at: str | None = Field(
        None, description="When it was handed out.", title="Dispatched At"
    )
    dispatched_to_workload_id: str | None = Field(
        None,
        description="The workload it was handed to.",
        title="Dispatched To Workload Id",
    )
    enqueued_at: str | None = Field(
        None, description="When it was queued.", title="Enqueued At"
    )
    error_message: str | None = Field(
        None, description="Why it failed, if it did.", title="Error Message"
    )
    id: str | None = Field(None, description="Identifier of the input.", title="Id")
    orchestration_ended_at: str | None = Field(
        None,
        description="When its orchestration ended.",
        title="Orchestration Ended At",
    )
    orchestration_id: str | None = Field(
        None, description="The orchestration it runs.", title="Orchestration Id"
    )
    orchestration_started_at: str | None = Field(
        None,
        description="When its orchestration started.",
        title="Orchestration Started At",
    )
    organization_id: str | None = Field(
        None, description="Your organization.", title="Organization Id"
    )
    parent_run_id: str | None = Field(
        None, description="The run that submitted it.", title="Parent Run Id"
    )
    priority: int | None = Field(None, description="Its priority.", title="Priority")
    queue_position: int | None = Field(
        None,
        description="Its position while it is still waiting.",
        title="Queue Position",
    )
    run_id: str | None = Field(None, description="The run it produced.", title="Run Id")
    source: str | None = Field(
        None, description="How it was submitted.", title="Source"
    )
    status: str | None = Field(None, description="Its current state.", title="Status")
    workload_id: str | None = Field(
        None, description="The workload it targets.", title="Workload Id"
    )


class RedisKeyDetail(BaseModel):
    """
    Value and metadata for a single cache key.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    cardinality: int | None = Field(None, title="Cardinality")
    display_range: list[int] | None = Field(None, title="Display Range")
    encoding: str | None = Field(None, title="Encoding")
    field_count: int | None = Field(None, title="Field Count")
    key: str = Field(..., title="Key")
    length: int | None = Field(None, title="Length")
    memory_bytes: int | None = Field(None, title="Memory Bytes")
    truncated: bool | None = Field(None, title="Truncated")
    ttl: int | None = Field(None, title="Ttl")
    type: str = Field(..., title="Type")
    value: Any | None = Field(None, title="Value")


class RedisKeyEntry(BaseModel):
    """
    A single cache key with metadata in a scan result.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    encoding: str | None = Field(None, title="Encoding")
    key: str = Field(..., title="Key")
    memory_bytes: int | None = Field(None, title="Memory Bytes")
    ttl: int | None = Field(None, title="Ttl")
    type: str = Field(..., title="Type")


class RedisKeyScanResult(BaseModel):
    """
    Paginated cache key scan result.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    has_more: bool | None = Field(None, title="Has More")
    keys: list[RedisKeyEntry] | None = Field([], title="Keys", validate_default=True)
    next_cursor: int | None = Field(None, title="Next Cursor")
    scan_count: int | None = Field(None, title="Scan Count")


class RefusalBody(RootModel[ErrorResponse | EdgeRefusal | DetailRefusal]):
    root: ErrorResponse | EdgeRefusal | DetailRefusal = Field(
        ...,
        description='The body of a 401, 403, 404, 415, 429 or 503. It depends on which layer refused the request: the standard error envelope, `{"error": ...}` or `{"detail": ...}`.',
        title="RefusalBody",
    )


class RegisterFileEntry(BaseModel):
    """
    A file already uploaded through the pre-signed upload URL, to register
    as an entry.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    blob_name: str = Field(
        ...,
        description="Blob path returned by the upload URL",
        max_length=1024,
        title="Blob Name",
    )
    checksum_md5: str | None = Field(
        None, description="MD5 of the uploaded blob", title="Checksum Md5"
    )
    file_name: str = Field(
        ..., description="Display name for the entry", max_length=255, title="File Name"
    )
    file_path: str = Field(
        ...,
        description="Virtual path within the space",
        max_length=1024,
        title="File Path",
    )
    mime_type: str | None = Field(
        "application/octet-stream", description="Content type", title="Mime Type"
    )
    parent_id: UUID | None = Field(
        None, description="Parent folder; null for the root", title="Parent Id"
    )
    size_bytes: int = Field(
        ..., description="Size of the uploaded blob in bytes", ge=0, title="Size Bytes"
    )
    type: Literal["file"] = Field(
        ..., description="Discriminator: register an uploaded blob", title="Type"
    )
    version_comment: str | None = Field(
        None, description="Comment for this version", title="Version Comment"
    )
