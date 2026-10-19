# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class AssetSearchResponse(BaseModel):
    """
    A page of assets of every type.

    Note: The envelope is `{items, total, page, page_size, total_pages}` — the shape
    the wire actually carries. It is not the
    `{data, page, page_size, total, next}` pagination envelope; no component
    between this service and the store applies that envelope, and declaring it here would document a shape
    no caller will ever receive.

    Important: **`total` counts the rows matched before the `protection` filter.** That
    filter is a property of the (asset, caller) pair rather than a stored column,
    so it is applied to each page after the count. When you pass `protection`,
    a short or even empty page is ordinary: keep paging while `page` is at most
    `total_pages`, and do not stop at the first empty `items`.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[AssetSearchRow] = Field(..., title="Items")
    page: int = Field(..., title="Page")
    page_size: int = Field(..., title="Page Size")
    total: int = Field(..., title="Total")
    total_pages: int = Field(..., title="Total Pages")


class BackupListResponse(BaseModel):
    """
    The backups held for one managed service.
    """

    items: list[BackupRead] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class BillingUsageEntriesPage(BaseModel):
    """
    ``GET /v1/billing/costs`` — paginated billing usage entries
    (``{items, total, has_more}``).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    has_more: bool | None = Field(False, title="Has More")
    items: list[BillingUsageEntryItem] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class CapabilityEvaluationSummaryRead(BaseModel):
    """
    Aggregate scores for every scored orchestration of a capability.
    """

    capability_id: UUID = Field(..., title="Capability Id")
    orchestrations: list[CapabilityOrchestrationEvaluationSummary] = Field(
        ..., title="Orchestrations"
    )


class CascadeApplyResult(BaseModel):
    """
    What an apply wrote, beside the change set it applied.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    applied: bool = Field(..., title="Applied")
    change_set: ChangeSet
    grant_ids: list[str] | None = Field(None, title="Grant Ids")
    narrowed_grant_ids: list[str] | None = Field(None, title="Narrowed Grant Ids")
    operation: CascadeApplyResultOperation = Field(..., title="Operation")
    revoked_grant_ids: list[str] | None = Field(None, title="Revoked Grant Ids")


class ComponentDetailRead(BaseModel):
    """
    A component, including the script and manifest of its current version.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    additional_packages: list[str] | None = Field(None, title="Additional Packages")
    artifact_type_input: str | None = Field(None, title="Artifact Type Input")
    artifact_type_output: str | None = Field(None, title="Artifact Type Output")
    asset_type: str = Field(..., title="Asset Type")
    capability_image_id: str | None = Field(None, title="Capability Image Id")
    category: str | None = Field(None, title="Category")
    config: dict[str, Any] | None = Field(None, title="Config")
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    description: str | None = Field(None, title="Description")
    fsm_states: list[dict[str, Any]] | None = Field(None, title="Fsm States")
    id: str = Field(..., title="Id")
    manifest_yaml: str | None = Field(None, title="Manifest Yaml")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    parent_asset_id: str | None = Field(
        None,
        description="The previous version, or null for the original.",
        title="Parent Asset Id",
    )
    ports: list[ComponentPortRead] | None = Field(None, title="Ports")
    root_asset_id: str | None = Field(
        None, description="The first version in this lineage.", title="Root Asset Id"
    )
    script: str | None = Field(None, title="Script")
    short_description: str | None = Field(None, title="Short Description")
    status: str = Field(..., title="Status")
    tags: list[str] | None = Field(None, title="Tags")
    updated_at: str = Field(..., title="Updated At")
    version_number: int | None = Field(
        1,
        description="Version number in the lineage; 1 is the original.",
        title="Version Number",
    )


class ComponentTransferData(BaseModel):
    """
    The component in an export document: its definition, script and ports.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    additional_packages: list[str] | None = Field(None, title="Additional Packages")
    artifact_type_input: str | None = Field(None, title="Artifact Type Input")
    artifact_type_output: str | None = Field(None, title="Artifact Type Output")
    asset_id: str | None = Field(None, title="Asset Id")
    category: str = Field(..., title="Category")
    config: dict[str, Any] | None = Field(None, title="Config")
    description: str | None = Field(None, title="Description")
    fsm_states: list[ComponentTransferFsmState] | None = Field(None, title="Fsm States")
    is_prebuilt_reference: bool | None = Field(False, title="Is Prebuilt Reference")
    is_template_clone: bool | None = Field(False, title="Is Template Clone")
    manifest_yaml: str | None = Field(None, title="Manifest Yaml")
    name: str = Field(..., title="Name")
    ports: list[ComponentTransferPort] | None = Field(None, title="Ports")
    prebuilt_asset_id: str | None = Field(None, title="Prebuilt Asset Id")
    requires_gpu: bool | None = Field(False, title="Requires Gpu")
    script: str | None = Field(None, title="Script")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")
    template_source_id: str | None = Field(None, title="Template Source Id")


class ComponentUsageReport(BaseModel):
    """
    Where a component is in use, across every version in its lineage.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component_id: str | None = Field(
        None, description="The component asked about.", title="Component Id"
    )
    lineage_root_id: str | None = Field(
        None,
        description="The first version in the component's lineage.",
        title="Lineage Root Id",
    )
    target_asset_id: str | None = Field(
        None,
        description="The version an upgrade would move consumers to.",
        title="Target Asset Id",
    )
    target_version: int | None = Field(
        None, description="That version's number.", title="Target Version"
    )
    total_consumers: int | None = Field(
        None,
        description="How many orchestrations pin any version of the component.",
        title="Total Consumers",
    )
    versions: list[ComponentVersionUsage] | None = Field(
        None, description="Usage for each version in the lineage.", title="Versions"
    )


class CostEstimate(BaseModel):
    """
    What a configuration would cost over a monthly period.

    Note: **This is an estimate, not a quote and not a bill.** It prices the usage
    you describe against your organization's current plan and rates. It reserves
    nothing, commits nothing, and does not change what you are charged.

    Money and quantity values are **strings** throughout. Parse them with a
    decimal type; reading them as binary floating point loses precision.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    base_price_included: bool = Field(
        ...,
        description="Whether `base_price_usd` is counted in `total_usd`.",
        title="Base Price Included",
    )
    base_price_usd: str = Field(
        ..., description="The plan's recurring charge.", title="Base Price Usd"
    )
    basis: dict[str, Any] | None = Field(
        None,
        description="The plan, quotas and rates the estimate was computed against, so a surprising total can be explained without a second request.",
        title="Basis",
    )
    currency: str = Field(
        ..., description="Currency of every money value here.", title="Currency"
    )
    line_items: list[CostEstimateLineItem] | None = Field(
        None,
        description="One entry per priced resource: compute, storage and egress.",
        title="Line Items",
    )
    note: str | None = Field(
        None, description="Any caveat that applies to this estimate.", title="Note"
    )
    organization_id: str = Field(..., title="Organization Id")
    period: str = Field(
        ..., description="The period the estimate covers.", title="Period"
    )
    total_usd: str = Field(
        ...,
        description="What the described configuration would cost.",
        title="Total Usd",
    )
    usage_total_usd: str = Field(
        ...,
        description="The line items summed, without the base.",
        title="Usage Total Usd",
    )


class DriftConfig(BaseModel):
    """
    Drift-detection configuration for an intelligence.

    `dataset_drift_threshold` and `feature_drift_threshold` are the thresholds drift is judged against. On a replace, a threshold you omit keeps its current value, and `metrics.dataset_drift.threshold` or `metrics.feature_drift.threshold` sets the matching threshold when the flat field is not given. An empty or null feature list means all features.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    create_alert: bool | None = Field(
        True, description="Raise an alert when drift is found.", title="Create Alert"
    )
    dataset_drift_threshold: DatasetDriftThreshold | None = Field(
        None,
        description="Dataset-level drift threshold, 0 to 1. Omitted or null keeps the current value.",
        title="Dataset Drift Threshold",
    )
    enabled: bool | None = Field(
        True, description="Whether drift detection is on.", title="Enabled"
    )
    feature_drift_threshold: FeatureDriftThreshold | None = Field(
        None,
        description="Per-feature drift threshold, 0 to 1. Omitted or null keeps the current value.",
        title="Feature Drift Threshold",
    )
    freeze_promotions: bool | None = Field(
        False,
        description="Block model promotions while drift is found.",
        title="Freeze Promotions",
    )
    ignore_features: list[str] | None = Field(
        None,
        description="Features to leave out of drift detection.",
        title="Ignore Features",
    )
    metrics: dict[str, DriftMetricSetting] | None = Field(
        {},
        description="Per-metric settings, keyed by metric name. `dataset_drift` and `feature_drift` thresholds set the matching flat threshold when it is not given.",
        title="Metrics",
        validate_default=True,
    )
    monitored_features: list[str] | None = Field(
        None,
        description="Features to monitor. Empty or null means all features.",
        title="Monitored Features",
    )
    webhook_url: str | None = Field(
        None,
        description="Not supported: must be null or omitted, and always null when read. A value is refused with `422`. To be notified of drift, subscribe a webhook to the `drift.detected` event with `POST /v1/webhooks`.",
        title="Webhook Url",
    )


class ExecuteOrchestrationRequest(BaseModel):
    """
    Execute an orchestration.

    Undeclared keys are accepted and forwarded, but the execute plane reads only
    the fields below and silently drops the rest.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact: Any | None = Field(None, title="Artifact")
    artifacts: Any | None = Field(None, title="Artifacts")
    callback_url: str | None = Field(None, title="Callback Url")
    conversation_enabled: bool | None = Field(None, title="Conversation Enabled")
    input: dict[str, Any] | None = Field(None, title="Input")
    input_data: dict[str, Any] | None = Field(None, title="Input Data")
    reviewer_assignments: list[ReviewerAssignmentRequest] | None = Field(
        None,
        description="Blocking human-review nodes in this run that the calling API key will review itself. Name each node by `node_id`; the assignee is always the calling key. Supplying `assignee_user_sub` other than the calling key's own subject, any `assignee_group_id`, or an `assignment_type` other than `USER` is refused with `422`.",
        title="Reviewer Assignments",
    )
    stream: bool | None = Field(None, title="Stream")


class ExperimentListResponse(BaseModel):
    """
    A window onto your organization's experiments.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[ExperimentRead] = Field(..., title="Items")
    limit: int = Field(..., title="Limit")
    offset: int = Field(..., title="Offset")
    total: int = Field(..., title="Total")


class FileUploadBatchResult(BaseModel):
    """
    The per-file outcome of an upload batch.
    """

    failed: int = Field(
        ..., description="How many items have status error", title="Failed"
    )
    items: list[FileUploadItem] = Field(..., title="Items")
    succeeded: int = Field(
        ..., description="How many items have status completed", title="Succeeded"
    )


class IngestTriggerCreate(BaseModel):
    """
    Create an ingest or evaluation trigger.

    ``trigger_type`` is required. The remaining fields may be omitted and take
    the defaults shown.

    ``config`` carries the trigger's data pointer — a ``feature_ingest``
    trigger takes ``space_id`` and ``folder_id`` there. A trigger created with
    an empty ``config`` is valid and will fire, but ingests nothing.
    """

    config: dict[str, Any] | None = Field(
        None,
        description="Dispatch configuration; feature_ingest reads space_id and folder_id",
        title="Config",
    )
    cron_enabled: bool | None = Field(False, title="Cron Enabled")
    cron_expression: str | None = Field(None, title="Cron Expression")
    cron_timezone: str | None = Field("UTC", title="Cron Timezone")
    http_enabled: bool | None = Field(False, title="Http Enabled")
    trigger_type: IngestTriggerType = Field(
        ..., description="feature_ingest, online_evaluation or drift_evaluation"
    )


class IntelligenceMaterializeAccepted(BaseModel):
    """
    A materialization accepted by the platform.
    """

    operation_id: str | None = Field(None, title="Operation Id")
    result: MaterializeResponse | None = None
    status: str | None = Field(
        None, description="`accepted` when the request was taken", title="Status"
    )


class IntelligenceStatusRead(BaseModel):
    """
    Intelligence asset status: the asset, its runtime, its services and its models.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    intelligence: IntelligenceRead
    models: list[ModelRead] | None = Field(None, title="Models")
    runtime: dict[str, Any] | None = Field(
        None,
        description="The runtime record, or null when the asset has never been started.",
        title="Runtime",
    )
    services: list[IntelligenceServiceStatusRead] | None = Field(None, title="Services")


class IntelligenceTrafficPlanFamily(BaseModel):
    """
    One model family's share of the intelligence's traffic, and its models.
    """

    family_id: UUID = Field(..., title="Family Id")
    family_name: str | None = Field(None, title="Family Name")
    models: list[IntelligenceTrafficPlanModel] = Field(..., title="Models")
    traffic_percent: int | None = Field(
        100, description="The family's share of all traffic", title="Traffic Percent"
    )


class IntelligenceTrafficPlanSpec(BaseModel):
    """
    A complete traffic plan: every family that serves, and its models.
    """

    families: list[IntelligenceTrafficPlanFamily] = Field(..., title="Families")


class IntelligenceTrainingJobRead(BaseModel):
    """
    A training job of this intelligence and the runs it has produced.
    """

    completed_at: AwareDatetime | None = Field(None, title="Completed At")
    created_at: AwareDatetime = Field(..., title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    family_id: UUID = Field(..., title="Family Id")
    hyperparameter_grid: dict[str, list[Any]] = Field(..., title="Hyperparameter Grid")
    id: UUID = Field(..., title="Id")
    intelligence_id: UUID = Field(..., title="Intelligence Id")
    runs: list[IntelligenceTrainingRunRead] = Field(..., title="Runs")
    started_at: AwareDatetime | None = Field(None, title="Started At")
    status: str = Field(..., title="Status")
    training_config: dict[str, Any] = Field(..., title="Training Config")
