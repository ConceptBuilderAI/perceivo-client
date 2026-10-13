# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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


class TimeoutMinutes(RootModel[int]):
    root: int = Field(
        ...,
        description="How long the reviewer has, in minutes. The review's expiry is recalculated from this; it cannot be set directly.",
        ge=1,
        title="Timeout Minutes",
    )


class ReviewPatch(BaseModel):
    """
    Fields of a review that may be changed in place.

    Every field is optional and only the fields you send are changed. Sending
    none of them is refused rather than treated as a successful no-op.
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
    assignment_type: str | None = Field(
        None,
        description="Whether the review is handed to a user, a group, or a pool.",
        title="Assignment Type",
    )
    context_data: dict[str, Any] | None = Field(
        None,
        description="Free-form context shown to the reviewer. Replaced, not merged.",
        title="Context Data",
    )
    timeout_minutes: TimeoutMinutes | None = Field(
        None,
        description="How long the reviewer has, in minutes. The review's expiry is recalculated from this; it cannot be set directly.",
        title="Timeout Minutes",
    )


class ReviewRead(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str | None = Field(None, title="Capability Id")
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    review_type: str | None = Field(None, title="Review Type")
    status: str | None = Field(None, title="Status")
    updated_at: str | None = Field(None, title="Updated At")


class ReviewerAssignmentRequest(BaseModel):
    """
    A human-review node in this run that the calling API key reviews itself.
    """

    assignee_group_id: Any | None = Field(
        None, description="Must be absent or null.", title="Assignee Group Id"
    )
    assignee_user_sub: str | None = Field(
        None,
        description="If supplied, must equal the calling key's own subject (`api_key:<id>`).",
        title="Assignee User Sub",
    )
    assignment_type: str | None = Field(
        None, description="If supplied, must be `USER`.", title="Assignment Type"
    )
    node_id: str = Field(
        ...,
        description="The review node's id in the orchestration.",
        min_length=1,
        title="Node Id",
    )
    required: bool | None = Field(
        True, description="Whether the review blocks the run.", title="Required"
    )


class RoleCreateV1(BaseModel):
    """
    Body for ``POST /v1/roles``.

    Note: ``privileges`` is validated downstream by ``validate_grantable_privileges``,
    which rejects unknown strings, the bare ``MANAGE`` wildcard and
    ``SYSTEM_ADMIN``. That validation is deliberately not duplicated here: a
    second copy of a security allowlist is a second thing to forget to update,
    and the copy that matters is the one next to the database.

    Note: ``privileges`` is REQUIRED and must name at least one privilege. A role
    with no privileges is never accepted, whether the field is left out of the
    request or sent as an empty list.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    applies_to: str | None = Field(
        None,
        description="The kind of resource the role is meant to be granted on: `organization`, `subscription`, `group`, `asset`, `secret`, `file`, `folder`, `storage_space`, `intelligence` or `capability`.",
        title="Applies To",
    )
    description: str | None = Field(
        None,
        description="Free text describing what the role is for.",
        title="Description",
    )
    name: str = Field(
        ...,
        description="The role's name, unique among your organization's custom roles.",
        max_length=255,
        min_length=1,
        title="Name",
    )
    privileges: list[str] = Field(
        ...,
        description="The privileges the role confers, at least one. Each must be one your own credential holds on your organization.",
        min_length=1,
        title="Privileges",
    )
