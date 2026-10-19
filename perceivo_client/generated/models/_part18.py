# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class TrafficPlanRead(BaseModel):
    """
    Traffic plan representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str = Field(..., title="Capability Id")
    orchestration_weights: list[dict[str, Any]] | None = Field(
        None, title="Orchestration Weights"
    )


class TrafficPlanSource(StrEnum):
    """
    Origin of a traffic-plan change.
    """

    user_manual = "user_manual"
    rollback_from_history = "rollback_from_history"
    recommendation_auto = "recommendation_auto"
    recommendation_manual = "recommendation_manual"


class TrafficPlanSpec(BaseModel):
    """
    A complete traffic plan: which orchestrations serve, and in what share.
    """

    allocations: list[TrafficAllocationSpec] = Field(..., title="Allocations")


class TrainingConfigurationCreate(BaseModel):
    """
    A training configuration to create.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    family_id: str | None = Field(None, title="Family Id")
    hyperparameters: dict[str, Any] | None = Field({}, title="Hyperparameters")
    name: str = Field(..., max_length=255, min_length=1, title="Name")
    training_mode: str | None = Field(
        "one_shot", pattern="^(one_shot|grid_search)$", title="Training Mode"
    )
    training_parameters: dict[str, Any] | None = Field({}, title="Training Parameters")
    training_service_id: str | None = Field(None, title="Training Service Id")
    training_settings: dict[str, Any] | None = Field({}, title="Training Settings")


class TrainingConfigurationRead(BaseModel):
    """
    A training configuration.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    family_id: str | None = Field(None, title="Family Id")
    hyperparameters: dict[str, Any] | None = Field({}, title="Hyperparameters")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    name: str = Field(..., title="Name")
    training_mode: str = Field(..., title="Training Mode")
    training_parameters: dict[str, Any] | None = Field({}, title="Training Parameters")
    training_service_id: str | None = Field(None, title="Training Service Id")
    training_settings: dict[str, Any] | None = Field({}, title="Training Settings")
    updated_at: str | None = Field(None, title="Updated At")


class TrainingConfigurationUpdateName(RootModel[str]):
    root: str = Field(..., max_length=255, min_length=1, title="Name")


class TrainingMode(RootModel[str]):
    root: str = Field(..., pattern="^(one_shot|grid_search)$", title="Training Mode")


class TrainingConfigurationUpdate(BaseModel):
    """
    Changes to apply to a training configuration.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    hyperparameters: dict[str, Any] | None = Field(None, title="Hyperparameters")
    name: TrainingConfigurationUpdateName | None = Field(None, title="Name")
    training_mode: TrainingMode | None = Field(None, title="Training Mode")
    training_parameters: dict[str, Any] | None = Field(
        None, title="Training Parameters"
    )
    training_settings: dict[str, Any] | None = Field(None, title="Training Settings")


class TrainingGroupCreate(BaseModel):
    """
    A training group to create.

    `configuration_ids` seeds the group's members.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    configuration_ids: list[str] | None = Field([], title="Configuration Ids")
    description: str | None = Field(None, title="Description")
    is_default: bool | None = Field(False, title="Is Default")
    name: str = Field(..., max_length=255, min_length=1, title="Name")


class TrainingGroupMemberRead(BaseModel):
    """
    One configuration's membership of a training group.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    configuration_name: str | None = Field(None, title="Configuration Name")
    created_at: str | None = Field(None, title="Created At")
    family_id: str = Field(..., title="Family Id")
    family_name: str | None = Field(None, title="Family Name")
    group_id: str = Field(..., title="Group Id")
    id: str = Field(..., title="Id")
    training_configuration_id: str = Field(..., title="Training Configuration Id")


class TrainingGroupMemberReplace(BaseModel):
    """
    The training configuration this membership slot should hold.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    training_configuration_id: UUID = Field(
        ...,
        description="The training configuration to place in this group.",
        title="Training Configuration Id",
    )


class TrainingGroupRead(BaseModel):
    """
    A training group.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    is_default: bool | None = Field(None, title="Is Default")
    members: list[dict[str, Any]] | None = Field(None, title="Members")
    name: str | None = Field(None, title="Name")
    updated_at: str | None = Field(None, title="Updated At")


class TrainingGroupUpdateName(RootModel[str]):
    root: str = Field(..., max_length=255, min_length=1, title="Name")


class TrainingGroupUpdate(BaseModel):
    """
    Changes to apply to a training group.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    is_default: bool | None = Field(None, title="Is Default")
    name: TrainingGroupUpdateName | None = Field(None, title="Name")


class TrainingJobSubmitResponse(BaseModel):
    """
    Response from submitting a training job.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    completed_at: str | None = Field(None, title="Completed At")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    family_id: str | None = Field(None, title="Family Id")
    hyperparameter_grid: dict[str, Any] | None = Field(
        None, title="Hyperparameter Grid"
    )
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    runs: list[dict[str, Any]] | None = Field(None, title="Runs")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    training_config: dict[str, Any] | None = Field(None, title="Training Config")


class TrainingRequest(BaseModel):
    """
    Submit a training job.

    ``training_service_id`` pins the exact training service version to run. If
    you omit it, the platform resolves one — first from the model family, then
    from the intelligence's own configuration.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")
    training_service_id: str | None = Field(None, title="Training Service Id")


class Transaction(BaseModel):
    """
    One movement on your organization's account — a credit, a charge or an
    adjustment.

    `balance_before_usd` and `balance_after_usd` are the account balance either
    side of this movement, so a sequence of transactions reconciles against the
    balance without re-adding the amounts.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    amount_usd: float | None = Field(None, title="Amount Usd")
    balance_after_usd: float | None = Field(None, title="Balance After Usd")
    balance_before_usd: float | None = Field(None, title="Balance Before Usd")
    completed_at: str | None = Field(None, title="Completed At")
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    failed_at: str | None = Field(None, title="Failed At")
    failure_reason: str | None = Field(None, title="Failure Reason")
    fee_usd: float | None = Field(None, title="Fee Usd")
    id: str = Field(..., title="Id")
    net_amount_usd: float | None = Field(None, title="Net Amount Usd")
    organization_id: str | None = Field(None, title="Organization Id")
    status: str | None = Field(None, title="Status")
    transaction_type: str | None = Field(
        None,
        description="What the movement was, for example a top-up or a charge.",
        title="Transaction Type",
    )


class TransactionPage(BaseModel):
    """
    A page of account transactions.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    total: int | None = Field(
        None,
        description="Number of transactions matching the filter in total, across every page — not the size of this page.",
        title="Total",
    )
    transactions: list[Transaction] | None = Field(
        [], title="Transactions", validate_default=True
    )


class UnifiedCostResponse(BaseModel):
    """
    ``GET /v1/billing/unified-cost``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    entries: list[dict[str, Any]] | None = Field(None, title="Entries")
    groupings: list[dict[str, Any]] | None = Field(None, title="Groupings")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    summary: dict[str, Any] | None = Field(None, title="Summary")
    total_entry_count: int | None = Field(None, title="Total Entry Count")


class UpdateGraphConfigRequest(BaseModel):
    """
    Update a graph configuration.

    Only the fields sent are changed. The capability, organization and author are
    fixed when the configuration is created, so none of them is a body field. A
    field not listed here is refused with 422.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    blackbox_fsm_nodes: bool | None = Field(None, title="Blackbox Fsm Nodes")
    cron_expression: str | None = Field(None, title="Cron Expression")
    cron_timezone: str | None = Field(None, title="Cron Timezone")
    description: str | None = Field(None, title="Description")
    enabled: bool | None = Field(None, title="Enabled")
    exclude_direct_triggers: bool | None = Field(None, title="Exclude Direct Triggers")
    exclude_intermediate_artifacts: bool | None = Field(
        None, title="Exclude Intermediate Artifacts"
    )
    exclude_unreviewed: bool | None = Field(None, title="Exclude Unreviewed")
    fsm_node_id: UUID | None = Field(None, title="Fsm Node Id")
    graph_type: str | None = Field(None, title="Graph Type")
    include_unscored: bool | None = Field(None, title="Include Unscored")
    log_types: list[str] | None = Field(None, title="Log Types")
    name: str | None = Field(None, title="Name")
    orchestration_ids: list[str] | None = Field(None, title="Orchestration Ids")
    retain_last_n: int | None = Field(None, title="Retain Last N")
    rolling_window_hours: int | None = Field(None, title="Rolling Window Hours")
    schedule_end: AwareDatetime | None = Field(None, title="Schedule End")
    schedule_start: AwareDatetime | None = Field(None, title="Schedule Start")
    target_intelligence_id: UUID | None = Field(None, title="Target Intelligence Id")
    triggers_feature_ingest: bool | None = Field(None, title="Triggers Feature Ingest")


class UploadResponse(BaseModel):
    """
    Result of an upload or upload registration.
    """

    entry: FileEntryRead
    version: FileVersionRead


class UploadTargetResponse(BaseModel):
    """
    Write-only SAS over exactly one blob. PUT to ``upload_url``, register ``blob_name``.
    """

    blob_name: str = Field(..., title="Blob Name")
    container_name: str = Field(..., title="Container Name")
    expires_at: AwareDatetime = Field(..., title="Expires At")
    file_name: str = Field(..., title="File Name")
    relative_path: str | None = Field(None, title="Relative Path")
    upload_url: str = Field(..., title="Upload Url")


class RelativePath(RootModel[str]):
    root: str = Field(
        ...,
        description="Folder within the space, e.g. reports/2026",
        max_length=1024,
        title="Relative Path",
    )


class UploadUrlFile(BaseModel):
    """
    One file to get an upload URL for.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    file_name: str = Field(
        ...,
        description="Name of the file to upload",
        max_length=255,
        min_length=1,
        title="File Name",
    )
    relative_path: RelativePath | None = Field(
        None,
        description="Folder within the space, e.g. reports/2026",
        title="Relative Path",
    )
    size_bytes: int = Field(
        ...,
        description="Size of the file in bytes, counted against the storage quota",
        ge=0,
        title="Size Bytes",
    )


class UploadUrlRequest(BaseModel):
    """
    The storage space a direct upload is destined for, and the one file.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    file_name: str = Field(
        ...,
        description="Name of the one file to upload",
        max_length=255,
        min_length=1,
        title="File Name",
    )
    relative_path: RelativePath | None = Field(
        None,
        description="Folder within the space, e.g. reports/2026",
        title="Relative Path",
    )
    size_bytes: int = Field(
        ...,
        description="Size of the file in bytes, checked against the storage quota",
        ge=0,
        title="Size Bytes",
    )
    space_id: UUID = Field(
        ..., description="Storage space the upload is destined for", title="Space Id"
    )


class UploadUrlsRequest(BaseModel):
    """
    The storage space the uploads are destined for, and up to 100 files.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    files: list[UploadUrlFile] = Field(
        ...,
        description="The files to upload, one to a hundred; their total size is checked against the space's storage quota once",
        max_length=100,
        min_length=1,
        title="Files",
    )
    space_id: UUID = Field(
        ..., description="Storage space the uploads are destined for", title="Space Id"
    )


class UploadUrlsResponse(BaseModel):
    """
    One upload URL per requested file, in request order.
    """

    targets: list[UploadTargetResponse] = Field(
        ..., description="One target per file, in request order", title="Targets"
    )


class UsageBreakdownResponse(BaseModel):
    """
    ``GET /v1/billing/usage/breakdown`` — per-service usage breakdown.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    elasticsearch: dict[str, Any] | None = Field(None, title="Elasticsearch")
    intelligence: dict[str, Any] | None = Field(None, title="Intelligence")
    mcp: dict[str, Any] | None = Field(None, title="Mcp")
    milvus: dict[str, Any] | None = Field(None, title="Milvus")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    ray: dict[str, Any] | None = Field(None, title="Ray")
    redis: dict[str, Any] | None = Field(None, title="Redis")
    snapshot_count: int | None = Field(None, title="Snapshot Count")
    total: dict[str, Any] | None = Field(None, title="Total")
