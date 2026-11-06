# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 4cb0cc1fb62e540b6329e643c14e3ed2ef7982f14766508c71bd02701feb1b21

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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


class RoleCreateV1(BaseModel):
    """
    Body for ``POST /v1/roles``.

    Note: every entry in ``privileges`` must be a privilege that can be granted
    to a role. An unknown string, the bare ``MANAGE`` wildcard and
    ``SYSTEM_ADMIN`` are rejected, and the role is not created.

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


class RoleListItem(BaseModel):
    """
    A role as the collection endpoint returns it.

    Note: ``privilege_count`` is a count; the privilege list itself is only on the
    single-role shape.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    applies_to: str | None = Field(None, title="Applies To")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    is_system: bool = Field(..., title="Is System")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    privilege_count: int = Field(..., title="Privilege Count")


class RoleReadV1(BaseModel):
    """
    A role as every single-role endpoint returns it, privileges included.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    applies_to: str | None = Field(None, title="Applies To")
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    is_system: bool = Field(..., title="Is System")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    privileges: list[str] | None = Field(None, title="Privileges")
    updated_at: str = Field(..., title="Updated At")


class RoleUpdateName(RootModel[str]):
    root: str = Field(
        ...,
        description="A new name, unique among your organization's custom roles.",
        max_length=255,
        min_length=1,
        title="Name",
    )


class RoleUpdateV1(BaseModel):
    """
    Body for ``PATCH /v1/roles/{role_id}``.

    Send only the fields you want to change. A field you omit is left as it is;
    a field you send is replaced outright, including when you send a partial
    object for it.
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
        description="New free text describing what the role is for.",
        title="Description",
    )
    name: RoleUpdateName | None = Field(
        None,
        description="A new name, unique among your organization's custom roles.",
        title="Name",
    )
    privileges: list[str] | None = Field(
        None,
        description="The role's complete new privilege list, at least one, replacing the current one. Every grantee of the role holds the new list at once.",
        title="Privileges",
    )


class RunArtifacts(BaseModel):
    """
    The artifact document produced by a run.

    A run has a single artifact document rather than a named collection.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact: dict[str, Any] | None = Field(None, title="Artifact")
    run_id: str | None = Field(None, title="Run Id")


class RunComponentCost(BaseModel):
    """
    One per-component compute-cost row for a run. ``GET /v1/billing/costs/{run_id}``
    returns a JSON ARRAY of these.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component_name: str | None = Field(None, title="Component Name")
    component_type: str | None = Field(None, title="Component Type")
    cost_usd: float | None = Field(None, title="Cost Usd")
    cpu_request_vcpu: float | None = Field(None, title="Cpu Request Vcpu")
    cu_cost_usd: float | None = Field(None, title="Cu Cost Usd")
    cu_hours: float | None = Field(None, title="Cu Hours")
    duration_ms: int | None = Field(None, title="Duration Ms")
    ended_at: str | None = Field(None, title="Ended At")
    gpu_count: int | None = Field(None, title="Gpu Count")
    gpu_type: str | None = Field(None, title="Gpu Type")
    id: str | None = Field(None, title="Id")
    memory_request_gb: float | None = Field(None, title="Memory Request Gb")
    node_id: str | None = Field(None, title="Node Id")
    rate_per_cu_hour: float | None = Field(None, title="Rate Per Cu Hour")
    rate_type: str | None = Field(None, title="Rate Type")
    started_at: str | None = Field(None, title="Started At")


class RunControlResult(BaseModel):
    """
    The outcome of a run-control action.

    Every field is optional: the body is produced by the execution layer and is
    passed through unchanged.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    message: str | None = Field(None, title="Message")
    status: str | None = Field(None, title="Status")


class RunEvents(BaseModel):
    """
    The execution events recorded for one run of a workload.

    Note: ``count`` is the number of events **in this response**, which is the whole
    recorded set for the run — this collection is not windowed. It is not a
    global count across runs.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    count: int | None = Field(
        None, description="Number of events returned.", title="Count"
    )
    events: list[dict[str, Any]] | None = Field(
        None, description="The recorded events.", title="Events"
    )
    run_id: str | None = Field(None, title="Run Id")
    run_number: int | None = Field(None, title="Run Number")
    status: str | None = Field(
        None, description="Status of the run described.", title="Status"
    )
    workload_id: str = Field(..., title="Workload Id")
