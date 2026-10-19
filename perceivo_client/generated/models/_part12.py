# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class NodepoolScale(BaseModel):
    """
    A target size for a nodepool.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    target_nodes: int = Field(..., ge=0, title="Target Nodes")


class NodepoolWriteName(RootModel[str]):
    root: str = Field(..., max_length=100, min_length=1, title="Name")


class NodepoolWrite(BaseModel):
    """
    Changes to apply to a nodepool.

    Every field is optional; only the fields present in the request are
    changed. Renaming requires the nodepool to be stopped.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    idle_timeout_minutes: IdleTimeoutMinutes | None = Field(
        None, title="Idle Timeout Minutes"
    )
    max_nodes: MaxNodes | None = Field(None, title="Max Nodes")
    min_nodes: MinNodes | None = Field(None, title="Min Nodes")
    name: NodepoolWriteName | None = Field(None, title="Name")


class OffsetPaginatedResponse(BaseModel):
    """
    ``GET /v1/billing/infrastructure-costs`` — offset/limit page of cost
    entries (``{items,total,limit,offset,has_more}``).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    has_more: bool | None = Field(False, title="Has More")
    items: list[dict[str, Any]] = Field(..., title="Items")
    limit: int = Field(..., title="Limit")
    offset: int = Field(..., title="Offset")
    total: int = Field(..., title="Total")


class Operation(BaseModel):
    """
    One asynchronous operation, and the target you poll for its status.

    Poll this at `GET /v1/operations/{operation_id}`. `status` is one of
    `queued`, `running`, `paused`, `completed`, `failed`, `cancelled`,
    `expired`; treat an unrecognised value as non-terminal. A non-terminal
    response carries a `Retry-After` header and an `ETag`; a repeat poll with
    `If-None-Match` returns `304`. A terminal record is retained for at least 30
    days, after which the operation returns `410`.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    cancel_requested: bool | None = Field(
        None,
        description="Whether cancellation has been requested.",
        title="Cancel Requested",
    )
    created_at: str = Field(..., title="Created At")
    error: dict[str, Any] | None = Field(
        None, description="The error of a failed operation.", title="Error"
    )
    id: str = Field(..., title="Id")
    kind: str = Field(
        ..., description="Always `operation` on this plane.", title="Kind"
    )
    operation_type: str | None = Field(
        None,
        description="What kind of work produced the operation.",
        title="Operation Type",
    )
    poll: str = Field(
        ..., description="The poll path for this operation.", title="Poll"
    )
    request: dict[str, Any] | None = Field(
        None,
        description="The parameters the operation was started with.",
        title="Request",
    )
    result: dict[str, Any] | None = Field(
        None, description="The inline result of a completed operation.", title="Result"
    )
    result_href: str | None = Field(
        None,
        description="A link to the result, when it is not inlined.",
        title="Result Href",
    )
    retry_after: int | None = Field(
        None, description="Seconds to wait before the next poll.", title="Retry After"
    )
    status: str = Field(..., title="Status")
    terminal_at: str | None = Field(
        None,
        description="When the operation reached a terminal state.",
        title="Terminal At",
    )
    updated_at: str | None = Field(None, title="Updated At")


class OperationPage(BaseModel):
    """
    One page of the principal's recent operations, most recent first.

    Page with the opaque `next` cursor until it is absent. `filter[status]`
    restricts to a single status.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[Operation] = Field(
        ..., description="The operations in this page.", title="Items"
    )
    next: str | None = Field(
        None,
        description="Opaque cursor for the next page, or absent when last.",
        title="Next",
    )


class OperationQueueDepth(BaseModel):
    """
    How much work a queue is holding.

    Note: ``pending`` is absent when ``pending_available`` is false. Some queues do
    not expose a waiting count, and reporting zero for one that cannot be
    measured would be indistinguishable from a queue that is genuinely empty —
    the reading a caller is most likely to act on.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    pending: int | None = Field(
        None,
        description="Items waiting to start. Absent when not measurable.",
        title="Pending",
    )
    pending_available: bool = Field(
        ...,
        description="Whether `pending` could be measured for this queue.",
        title="Pending Available",
    )
    running: int = Field(..., description="Items currently executing.", title="Running")


class OperationQueueDetail(BaseModel):
    """
    One queue, addressed directly.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    backing: str = Field(
        ..., description="The kind of store the queue is held in.", title="Backing"
    )
    depth: OperationQueueDepth
    description: str = Field(..., title="Description")
    label: str = Field(..., title="Label")
    organization_id: str = Field(..., title="Organization Id")
    queue: str = Field(
        ..., description="The queue's identifier, used to address it.", title="Queue"
    )


class OrchestrationCopyRequest(BaseModel):
    """
    Request body for copying an orchestration.
    """

    capability_id: str | None = Field(None, title="Capability Id")
    copy_secret_bindings: bool | None = Field(False, title="Copy Secret Bindings")
    new_name: str | None = Field(None, title="New Name")
    standalone: bool | None = Field(False, title="Standalone")


class OrchestrationCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/orchestration/{orchestration_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    children: list[dict[str, Any]] | None = Field(None, title="Children")
    component_costs: list[dict[str, Any]] | None = Field(None, title="Component Costs")
    infrastructure_overhead: dict[str, Any] | None = Field(
        None, title="Infrastructure Overhead"
    )
    llm_costs: dict[str, Any] | None = Field(None, title="Llm Costs")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    orchestration_name: str | None = Field(None, title="Orchestration Name")
    organization_id: str | None = Field(None, title="Organization Id")
    period: dict[str, Any] | None = Field(None, title="Period")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    summary: dict[str, Any] | None = Field(None, title="Summary")
    user_reported_costs: dict[str, Any] | None = Field(
        None, title="User Reported Costs"
    )


class OrchestrationCreate(BaseModel):
    """
    Create a new orchestration.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")


class OrchestrationDraftCreate(BaseModel):
    """
    Create an unvalidated WIP canvas draft. `organization_id` defaults to the
    calling service account's org.
    """

    base_version_id: UUID | None = Field(
        None,
        description="Bind the draft to this published version of an orchestration, so that publishing it creates that orchestration's next version. Set only at create and never changed; an orchestration has at most one bound draft.",
        title="Base Version Id",
    )
    canvas_state: dict[str, Any] = Field(
        ...,
        description="Full canvas snapshot, e.g. `{nodes, edges, metadata}`; `{}` is accepted.",
        title="Canvas State",
    )
    description: str | None = Field(None, title="Description")
    name: str = Field(..., title="Name")
    organization_id: UUID | None = Field(None, title="Organization Id")
    source_orchestration_id: UUID | None = Field(None, title="Source Orchestration Id")


class OrchestrationDraftPatch(BaseModel):
    """
    The changes a publish applies to the new version: the complete desired
    state of each field you send. Fields you omit are left as they are.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    additional_packages: list[str] | None = Field(None, title="Additional Packages")
    capability_image_id: UUID | None = Field(None, title="Capability Image Id")
    description: str | None = Field(None, title="Description")
    edges: list[dict[str, Any]] | None = Field(None, title="Edges")
    name: str | None = Field(None, title="Name")
    nodes: list[dict[str, Any]] | None = Field(None, title="Nodes")
    ports: list[dict[str, Any]] | None = Field(None, title="Ports")
    requires_gpu: bool | None = Field(None, title="Requires Gpu")
    runtime_config: dict[str, Any] | None = Field(None, title="Runtime Config")
    secrets: list[dict[str, Any]] | None = Field(None, title="Secrets")
    tags: list[str] | None = Field(None, title="Tags")


class OrchestrationDraftPublish(BaseModel):
    """
    Publish a draft bound to a published version.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    expected_base_version_id: UUID = Field(
        ...,
        description="The version the draft is bound to. If that version is no longer the orchestration's latest, the publish is refused `409` `DRAFT_BASE_STALE`.",
        title="Expected Base Version Id",
    )


class ChangeNote(RootModel[str]):
    root: str = Field(
        ...,
        description="Recorded as the new version's change note.",
        max_length=500,
        title="Change Note",
    )


class OrchestrationDraftPublished(BaseModel):
    """
    The new version created by a publish.
    """

    orchestration_id: str = Field(..., title="Orchestration Id")


class OrchestrationDraftRead(BaseModel):
    base_version_id: UUID | None = Field(None, title="Base Version Id")
    canvas_state: dict[str, Any] = Field(..., title="Canvas State")
    created_at: AwareDatetime | None = Field(None, title="Created At")
    created_by_user_id: str = Field(..., title="Created By User Id")
    description: str | None = Field(None, title="Description")
    id: UUID = Field(..., title="Id")
    lineage_root_id: UUID | None = Field(None, title="Lineage Root Id")
    name: str = Field(..., title="Name")
    organization_id: UUID = Field(..., title="Organization Id")
    publish_payload: dict[str, Any] | None = Field(None, title="Publish Payload")
    source_orchestration_id: UUID | None = Field(None, title="Source Orchestration Id")
    staged_changes: list[dict[str, Any]] | None = Field(None, title="Staged Changes")
    updated_at: AwareDatetime | None = Field(None, title="Updated At")


class Op(StrEnum):
    add = "add"
    remove = "remove"


class OrchestrationDraftSecretOp(BaseModel):
    """
    Bind (`add`) or unbind (`remove`) a secret on one node of the new version.
    """

    alias: str = Field(..., max_length=100, min_length=1, title="Alias")
    node_ref: str = Field(
        ...,
        description="A node id of the base version, or a node name.",
        max_length=255,
        min_length=1,
        title="Node Ref",
    )
    op: Op = Field(..., title="Op")
    secret_ref: UUID | None = Field(None, title="Secret Ref")


class OrchestrationDraftStagedChange(BaseModel):
    """
    Re-pin one node of the base version to a different component.
    """

    component_asset_id: UUID = Field(..., title="Component Asset Id")
    node_id: UUID = Field(..., title="Node Id")
    source_operation_id: UUID | None = Field(None, title="Source Operation Id")


class EdgeKind(StrEnum):
    mainflow = "MAINFLOW"
    invoke = "INVOKE"
    return_ = "RETURN"
    transition = "TRANSITION"


class OrchestrationEdge(BaseModel):
    """
    One connection between two node ports.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    edge_kind: EdgeKind = Field(..., title="Edge Kind")
    id: str = Field(..., title="Id")
    orchestration_id: str = Field(..., title="Orchestration Id")
    source_orch_port_id: str = Field(..., title="Source Orch Port Id")
    target_orch_port_id: str = Field(..., title="Target Orch Port Id")


class OrchestrationEdgeDefine(BaseModel):
    """
    An edge of an unsaved definition, joining two entries of `ports` by position.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    edge_kind: EdgeKind = Field(..., title="Edge Kind")
    source_port_index: int = Field(
        ...,
        description="Zero-based index into the `ports` list.",
        title="Source Port Index",
    )
    target_port_index: int = Field(
        ...,
        description="Zero-based index into the `ports` list.",
        title="Target Port Index",
    )


class OrchestrationExportRead(BaseModel):
    """
    Exported orchestration bundle (metadata + components + graph).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    components: dict[str, Any] | None = Field(None, title="Components")
    edges: list[dict[str, Any]] | None = Field(None, title="Edges")
    export_type: str | None = Field(None, title="Export Type")
    export_version: str | None = Field(None, title="Export Version")
    exported_at: str | None = Field(None, title="Exported At")
    nodes: list[dict[str, Any]] | None = Field(None, title="Nodes")
    orchestration: dict[str, Any] | None = Field(None, title="Orchestration")
    ports: list[dict[str, Any]] | None = Field(None, title="Ports")
    secrets_required: list[dict[str, Any]] | None = Field(
        None, title="Secrets Required"
    )


class OrchestrationMetadataUpdate(BaseModel):
    """
    Update an orchestration's name, description or tags (all optional).

    The graph and runtime settings are not edited here: save them in a draft's
    `publish_payload.patch` and publish it with
    `POST /v1/orchestrations/drafts/{draft_id}/publish`.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    description: str | None = Field(None, title="Description")
    name: str | None = Field(None, title="Name")
    tags: list[str] | None = Field(None, title="Tags")


class OrchestrationNode(BaseModel):
    """
    One node of an orchestration graph.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component_asset_id: str = Field(
        ..., description="The component this node runs", title="Component Asset Id"
    )
    config: dict[str, Any] = Field(..., title="Config")
    id: str = Field(..., title="Id")
    name: str | None = Field(None, title="Name")
    orchestration_id: str = Field(..., title="Orchestration Id")
    position: dict[str, Any] | None = Field(
        None, description="Editor coordinates, if any", title="Position"
    )


class OrchestrationNodeDefine(BaseModel):
    """
    A node of an unsaved definition.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    component_id: UUID = Field(..., title="Component Id")
    config: dict[str, Any] | None = Field(None, title="Config")
    name: str | None = Field(None, title="Name")
    position: dict[str, Any] | None = Field(None, title="Position")
