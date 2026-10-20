# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from ._part06 import DetailRefusal, EdgeRefusal, ErrorResponse


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
    than a fixed schema. ``correlation_id`` is always injected by the serving layer so
    the prediction can be linked to downstream outcome events. Model-specific extras
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


class RegisterFileItem(BaseModel):
    """
    One uploaded file to register as an entry.
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
    version_comment: str | None = Field(
        None, description="Comment for this version", title="Version Comment"
    )


class RegisterFileOutcome(BaseModel):
    """
    What happened to one submitted file.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    detail: str | None = Field(
        None, description="Why the file was not registered", title="Detail"
    )
    entry_id: UUID | None = Field(
        None, description="The entry, when registered", title="Entry Id"
    )
    file_name: str = Field(
        ..., description="The file's name, as submitted", title="File Name"
    )
    file_path: str = Field(
        ..., description="The file's path, as submitted", title="File Path"
    )
    index: int = Field(
        ..., description="The file's position in the request, from 0", title="Index"
    )
    status: str = Field(..., description="`registered` or `failed`", title="Status")
    status_code: int | None = Field(
        None,
        description="The status a single registration would have answered",
        title="Status Code",
    )


class ResidualGroupPrivileges(BaseModel):
    """
    Organization privileges a member still holds through one group.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    group_id: UUID = Field(..., title="Group Id")
    group_name: str = Field(..., title="Group Name")
    privileges: list[str] = Field(..., title="Privileges")


class ResourceBreakdownResponse(BaseModel):
    """
    ``GET /v1/billing/resource-breakdown``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    intelligences: dict[str, Any] | None = Field(None, title="Intelligences")
    namespace: str | None = Field(None, title="Namespace")
    orchestrations: dict[str, Any] | None = Field(None, title="Orchestrations")
    organization_id: str | None = Field(None, title="Organization Id")
    overhead_total: dict[str, Any] | None = Field(None, title="Overhead Total")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    ray: dict[str, Any] | None = Field(None, title="Ray")
    redis: dict[str, Any] | None = Field(None, title="Redis")
    total: dict[str, Any] | None = Field(None, title="Total")
    variable_total: dict[str, Any] | None = Field(None, title="Variable Total")


class ReviewAssign(BaseModel):
    """
    Who a review is handed to.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    assignee_group_id: str | None = Field(
        None,
        description="The group to hand the review to, when assigning to a group.",
        title="Assignee Group Id",
    )
    assignee_user_sub: str | None = Field(
        None,
        description="The user to hand the review to, when assigning to a user.",
        title="Assignee User Sub",
    )
    assignment_type: str = Field(
        ...,
        description="Whether the review is handed to a user, a group, or a pool.",
        title="Assignment Type",
    )


class ReviewComplete(BaseModel):
    """
    Reviewer's answers for a pending review.

    Completing the last blocking review on a workload resumes the parked run.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    response_data: dict[str, Any] = Field(
        ...,
        description="Reviewer answers keyed by the question ids declared in the review's survey_spec. Required.",
        title="Response Data",
    )


class ReviewDraft(BaseModel):
    """
    Partial reviewer answers, saved without submitting the decision.

    Saving a draft on a pending review moves it to in-progress. A later save
    replaces the whole draft; it does not merge into it.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    draft_data: dict[str, Any] = Field(
        ...,
        description="Partial reviewer answers keyed by the question ids declared in the review's survey_spec. Required.",
        title="Draft Data",
    )
