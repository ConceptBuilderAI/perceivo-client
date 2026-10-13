# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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
    canvas_state: dict[str, Any] | None = Field(None, title="Canvas State")
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


class OrchestrationPortDefine(BaseModel):
    """
    A port of an unsaved definition, attached to a node by its position in `nodes`.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    alias: str | None = Field(None, title="Alias")
    component_port_id: UUID = Field(..., title="Component Port Id")
    effective_contract: dict[str, Any] | None = Field(None, title="Effective Contract")
    node_index: int = Field(
        ..., description="Zero-based index into the `nodes` list.", title="Node Index"
    )


class OrchestrationRead(BaseModel):
    """
    Orchestration resource representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    tags: list[str] | None = Field(None, title="Tags")
    updated_at: str | None = Field(None, title="Updated At")


class OrchestrationRestoreResult(BaseModel):
    """
    Result of restoring a soft-deleted orchestration.
    """

    id: str = Field(
        ..., description="The identifier the request addressed.", title="Id"
    )
    restored_count: int | None = Field(
        0, description="The number of versions restored.", title="Restored Count"
    )
    restored_ids: list[str] | None = Field(
        None, description="Every version this call restored.", title="Restored Ids"
    )
    root_id: str | None = Field(
        None,
        description="Identifier of the first version of the lineage.",
        title="Root Id",
    )
    status: str = Field(
        ...,
        description="The addressed version's status after the restore.",
        title="Status",
    )


class OrchestrationUpdateResult(BaseModel):
    """
    The orchestration after an update.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    tags: list[str] | None = Field(None, title="Tags")
    updated_at: str | None = Field(None, title="Updated At")
    version_created: bool = Field(
        ...,
        description="`true` when the update produced a new asset — a new version — and `id` is that new asset's identifier; `false` when the asset was updated in place. Follow `id` either way.",
        title="Version Created",
    )


class OrchestrationUsageResponse(BaseModel):
    """
    ``GET /v1/billing/orchestration-usage`` — compute + token usage.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    by_provider: dict[str, Any] | None = Field(None, title="By Provider")
    by_workload: dict[str, Any] | None = Field(None, title="By Workload")
    cpu_hours: float | None = Field(None, title="Cpu Hours")
    cpu_seconds: float | None = Field(None, title="Cpu Seconds")
    gpu_hours: float | None = Field(None, title="Gpu Hours")
    gpu_seconds: float | None = Field(None, title="Gpu Seconds")
    memory_gb_hours: float | None = Field(None, title="Memory Gb Hours")
    memory_gb_seconds: float | None = Field(None, title="Memory Gb Seconds")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    resource_snapshot_count: int | None = Field(None, title="Resource Snapshot Count")
    system_token_cost_usd: float | None = Field(None, title="System Token Cost Usd")
    system_tokens_in: int | None = Field(None, title="System Tokens In")
    system_tokens_out: int | None = Field(None, title="System Tokens Out")
    token_snapshot_count: int | None = Field(None, title="Token Snapshot Count")
    total_token_cost_usd: float | None = Field(None, title="Total Token Cost Usd")
    total_tokens_in: int | None = Field(None, title="Total Tokens In")
    total_tokens_out: int | None = Field(None, title="Total Tokens Out")
    user_token_cost_usd: float | None = Field(None, title="User Token Cost Usd")
    user_tokens_in: int | None = Field(None, title="User Tokens In")
    user_tokens_out: int | None = Field(None, title="User Tokens Out")


class OrchestrationValidationError(BaseModel):
    """
    One reason a definition was rejected.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    code: str | None = Field(None, title="Code")
    message: str | None = Field(None, title="Message")


class OrchestrationValidationResult(BaseModel):
    """
    The verdict on a submitted definition.

    A definition that fails validation is still a successful request: you asked
    a question and got an answer, so the status is `200` and `valid` is `false`.
    `errors` is empty exactly when `valid` is `true`.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    errors: list[OrchestrationValidationError] | None = Field(None, title="Errors")
    valid: bool = Field(..., title="Valid")


class OrchestrationsCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/orchestrations``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    llm_managed_cost_usd: float | None = Field(None, title="Llm Managed Cost Usd")
    llm_user_cost_usd: float | None = Field(None, title="Llm User Cost Usd")
    orchestrations: list[dict[str, Any]] | None = Field(None, title="Orchestrations")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")
