# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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


class RunOverheadResponse(BaseModel):
    """
    ``GET /v1/billing/run-overhead/{run_id}`` — component vs overhead split
    for one run.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    is_final: bool | None = Field(None, title="Is Final")
    overhead_cost_usd: float | None = Field(None, title="Overhead Cost Usd")
    overhead_cu_hours: float | None = Field(None, title="Overhead Cu Hours")
    overhead_duration_ms: int | None = Field(None, title="Overhead Duration Ms")
    run_id: str | None = Field(None, title="Run Id")
    total_component_cost_usd: float | None = Field(
        None, title="Total Component Cost Usd"
    )
    total_component_duration_ms: int | None = Field(
        None, title="Total Component Duration Ms"
    )


class RunResult(BaseModel):
    """
    The output of a run.

    ``output_payload`` is null until the run reaches a terminal status. A run
    that failed carries its terminal ``status`` and ``error_message``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact: dict[str, Any] | None = Field(None, title="Artifact")
    completed_at: str | None = Field(None, title="Completed At")
    error_message: str | None = Field(None, title="Error Message")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    output_payload: dict[str, Any] | None = Field(None, title="Output Payload")
    run_id: str = Field(..., title="Run Id")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    workload_id: str | None = Field(None, title="Workload Id")


class RunStatus(BaseModel):
    """
    The status of a run.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    completed_at: str | None = Field(None, title="Completed At")
    error: str | None = Field(None, title="Error")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    run_id: str = Field(..., title="Run Id")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    workload_id: str | None = Field(None, title="Workload Id")


class RunSteps(BaseModel):
    """
    Per-node execution detail for one run of a workload.

    Each entry in ``steps`` describes one node's activity, including when it
    first and last executed and one span per execution. A node that ran more
    than once has more than one span.

    Note: ``count`` is the number of steps **in this response**, which is the whole
    set for the run — this collection is not windowed.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    count: int | None = Field(
        None, description="Number of steps returned.", title="Count"
    )
    run_id: str | None = Field(None, title="Run Id")
    run_number: int | None = Field(None, title="Run Number")
    status: str | None = Field(
        None, description="Status of the run described.", title="Status"
    )
    steps: list[dict[str, Any]] | None = Field(
        None, description="One entry per node that executed.", title="Steps"
    )
    workload_id: str = Field(..., title="Workload Id")


class RunSummary(BaseModel):
    """
    One run. ``run_id`` is accepted by every ``/v1/orchestrations/runs/{run_id}`` operation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    completed_at: str | None = Field(None, title="Completed At")
    error: str | None = Field(None, title="Error")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    queued_at: str | None = Field(None, title="Queued At")
    run_id: str = Field(..., title="Run Id")
    source: str | None = Field(None, title="Source")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    workload_id: str | None = Field(None, title="Workload Id")
    workload_type: str | None = Field(None, title="Workload Type")


class RuntimeObservations(BaseModel):
    """
    What static analysis of the script found. The script is never run.

    Despite the name, nothing here observes an execution. The validator parses
    the script into a syntax tree and inspects it; it does not import, evaluate
    or run any part of it, in a sandbox or otherwise. Every field below is a
    property of the source **text**, so each is a lower bound: anything a
    program assembles at run time is invisible to all three.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    calls: list[str] | None = Field(
        None,
        description="Platform SDK calls that appear in the script's source, as dotted names such as `perceivo.log.info`. Sorted and de-duplicated: a call written once and a call written in a loop both appear once, a call inside an unreachable branch still appears, and no arguments, ordering or counts are reported. This is what the code *contains*, not what it did.",
        title="Calls",
    )
    detected_hosts: list[str] | None = Field(
        None,
        description="Hostnames of `http://` and `https://` URLs written as literal strings in the script.\n\nNote: This is not a list of the hosts the component will contact, and an empty list is not evidence that it contacts none. The check is a pattern match over string literals, so a URL the script assembles at run time — by concatenation, formatting, an f-string, an environment variable or a configuration value — does not appear here. Use it to notice hard-coded endpoints, not to establish that a component has no egress.",
        title="Detected Hosts",
    )
    logs: list[str] | None = Field(
        None,
        description="Notes from the validator recording which groups of checks it ran. These are the validator's own messages — the script is not run, so it emits nothing. Present only when `validation_profile` is `full`.",
        title="Logs",
    )


class SearchIndexCreated(BaseModel):
    """
    The index was created.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created: bool = Field(..., description="Always true on success.", title="Created")
    index: str = Field(..., description="Name of the index created.", title="Index")


class SearchIndexDeleted(BaseModel):
    """
    The index and everything in it were deleted.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    deleted: bool = Field(..., description="Always true on success.", title="Deleted")
    index: str = Field(..., description="Name of the index deleted.", title="Index")


class SecretCreate(BaseModel):
    """
    A new secret. The value is write-only: no read on this API returns it.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    expiration_date: str | None = Field(None, title="Expiration Date")
    name: str = Field(..., title="Name")
    value: str = Field(..., title="Value")
