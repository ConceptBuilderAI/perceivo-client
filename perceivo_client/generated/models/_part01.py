# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class AlertRuleUpdate(BaseModel):
    """
    Changes to an alert rule. Every field is optional.
    """

    condition: dict[str, Any] | None = Field(
        None,
        description="The condition itself. Its keys depend on `condition_type`; the catalogue lists them for each kind.",
        title="Condition",
    )
    condition_type: ConditionType | None = Field(
        None,
        description="The kind of condition the rule carries. `GET /v1/alert-rules/catalog` lists the kinds and whether each is evaluated.",
        title="Condition Type",
    )
    cooldown_minutes: CooldownMinutes | None = Field(
        None,
        description="Minutes after the rule fires during which it does not fire again. The platform may hold some rules to a longer minimum.",
        title="Cooldown Minutes",
    )
    description: Description | None = Field(
        None,
        description="What the rule is for, in your own words.",
        title="Description",
    )
    is_enabled: bool | None = Field(
        None,
        description="Whether the rule fires. A disabled rule is kept and can be enabled again.",
        title="Is Enabled",
    )
    message_template: MessageTemplate | None = Field(
        None,
        description="The message of each alert the rule raises.",
        title="Message Template",
    )
    name: AlertRuleUpdateName | None = Field(
        None,
        description="A name for the rule, shown wherever the rule is listed.",
        title="Name",
    )
    notify_channels: list[str] | None = Field(
        None,
        description="The kinds of channel the rule delivers on, such as `in_app` or `email`. These are channel kinds from the catalogue, not channel identifiers.",
        title="Notify Channels",
    )
    severity: Severity | None = Field(
        None,
        description="The severity of the alerts the rule raises.",
        title="Severity",
    )
    target_type: TargetType | None = Field(
        None,
        description="Who receives the rule's alerts: `creator` (the default) is the rule's author, `user` is the people named in `target_user_subs`, and `organization` is every member of your organization who can read alerts. An `organization` rule needs a `cooldown_minutes` of at least 15.",
        title="Target Type",
    )
    target_user_subs: list[str] | None = Field(
        None,
        description="The people a `user` rule delivers to, by user identifier. Required and non-empty when `target_type` is `user`, and refused for any other target type. Each must be a member of your organization; a rule naming anyone else is refused with `404`.",
        title="Target User Subs",
    )
    title_template: TitleTemplate | None = Field(
        None,
        description="The title of each alert the rule raises.",
        title="Title Template",
    )


class AlertSummary(BaseModel):
    """
    Alert counts by severity and status for the calling organization.
    """

    active_critical: int | None = Field(0, title="Active Critical")
    active_warning: int | None = Field(0, title="Active Warning")
    total_acknowledged: int | None = Field(0, title="Total Acknowledged")
    total_active: int | None = Field(0, title="Total Active")
    total_resolved: int | None = Field(0, title="Total Resolved")
    total_unread: int | None = Field(0, title="Total Unread")


class NewName(RootModel[str]):
    root: str = Field(
        ...,
        description="Name for the copy. Defaults to the source name followed by `(copy)`.",
        max_length=255,
        title="New Name",
    )


class AssetCopyRequest(BaseModel):
    """
    Body for ``POST /v1/assets/{asset_id}/copy``.

    Both fields are optional. The copy is always attributed to the credential you
    present; there is no field for naming another creator.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    new_name: NewName | None = Field(
        None,
        description="Name for the copy. Defaults to the source name followed by `(copy)`.",
        title="New Name",
    )
    organization_id: str | None = Field(
        None,
        description="Destination organization. Required only when your credential reaches more than one organization; it must be one of yours.",
        title="Organization Id",
    )


class AssetGrantCreate(BaseModel):
    """
    Body for ``POST /v1/assets/{asset_id}/grants``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    privileges: list[str] = Field(
        ...,
        description="The privileges to grant. Accepted values are `LIST_GROUP`, `READ_GROUP`, `LIST_ASSETS`, `READ_ASSETS`, `USE_ASSETS`, `COPY_ASSETS`, `ADD_ASSETS`, `EDIT_GROUP`, `MANAGE_MEMBERS` and `ADMIN_GROUP`. Granting the same user again replaces the previous grant rather than adding to it.",
        title="Privileges",
    )
    user_id: str = Field(
        ...,
        description="The user profile this grant applies to. An API key's own id — what `GET /v1/whoami` returns for a key — is not a user profile id and is refused. Both are UUIDs and parse identically here, so the refusal comes from the platform as a `400` rather than from this schema.",
        title="User Id",
    )


class AssetGrantRead(BaseModel):
    """
    One individual privilege grant on an asset.

    A grant recorded here overrides the privileges the user would otherwise
    inherit from group membership. `id` is the grant identifier; `user_id`
    identifies the user the grant is for.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    asset_id: str = Field(..., title="Asset Id")
    granted_at: str = Field(..., title="Granted At")
    granted_by_user_id: str = Field(..., title="Granted By User Id")
    id: str = Field(..., title="Id")
    privileges: list[str] = Field(..., title="Privileges")
    revoked_at: str | None = Field(None, title="Revoked At")
    user_id: str = Field(..., title="User Id")


class AssetImportRequest(BaseModel):
    """
    Body for ``POST /v1/assets/import``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    bundle: dict[str, Any] = Field(
        ...,
        description="A bundle previously produced by `GET /v1/assets/{asset_id}/export`. Its `export_type` selects the asset type to create and must be one of `component`, `orchestration` or `intelligence`.",
        title="Bundle",
    )
    organization_id: str | None = Field(
        None,
        description="Destination organization. Required only when your credential reaches more than one organization; it must be one of yours. Any organization named inside the bundle itself is ignored.",
        title="Organization Id",
    )


class AssetLineageRead(BaseModel):
    """
    Version-history lineage for an asset (orchestration/component/capability).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    latest_version_id: str | None = Field(None, title="Latest Version Id")
    versions: list[dict[str, Any]] | None = Field(None, title="Versions")


class AssetRead(BaseModel):
    """
    An asset of any type.

    Note: Identifiers and timestamps arrive as JSON **strings**, not as native
    types. `type` is one of `orchestration`, `orchestration_component`,
    `intelligence`, `intelligence_component` or `secret`.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    category: str | None = Field(None, title="Category")
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str = Field(..., title="Created By User Id")
    current_version_id: str | None = Field(None, title="Current Version Id")
    deleted_at: str | None = Field(None, title="Deleted At")
    description: str | None = Field(None, title="Description")
    disabled_reason: str | None = Field(None, title="Disabled Reason")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    status: str = Field(..., title="Status")
    tags: list[str] | None = Field(None, title="Tags")
    type: str = Field(..., title="Type")
    updated_at: str = Field(..., title="Updated At")


class AssetSearchRow(BaseModel):
    """
    One asset in the cross-type search result.

    Note: Identifiers and timestamps arrive as JSON **strings**, not as native
    types. `type` is one of `orchestration`, `orchestration_component`,
    `intelligence`, `intelligence_component` or `secret`.

    `ownership` says whether your organization owns this asset (`owned`) or
    reaches it through a share (`shared`). `protection` is the asset's
    protection class, which governs which generic operations are permitted on
    it: `managed` means it belongs to your organization and you may write it;
    `platform` means the platform shares it with every organization, and it is
    readable and copyable but never writable.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    category: str | None = Field(None, title="Category")
    created_at: str | None = Field(None, title="Created At")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    current_version_id: str | None = Field(None, title="Current Version Id")
    deleted_at: str | None = Field(None, title="Deleted At")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    ownership: str = Field(
        ..., description="Either `owned` or `shared`.", title="Ownership"
    )
    protection: str = Field(
        ..., description="Either `managed` or `platform`.", title="Protection"
    )
    short_description: str | None = Field(None, title="Short Description")
    status: str = Field(..., title="Status")
    tags: list[str] | None = Field(None, title="Tags")
    type: str = Field(..., title="Type")
    updated_at: str | None = Field(None, title="Updated At")


class AssignCapabilityRequest(BaseModel):
    """
    Request body for assigning an orchestration to a capability.
    """

    capability_id: str = Field(..., title="Capability Id")
    new_name: str | None = Field(None, title="New Name")


class AssignCapabilityResultRead(BaseModel):
    """
    Result of assigning an orchestration to a capability.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compatibility: dict[str, Any] | None = Field(None, title="Compatibility")
    orchestration: dict[str, Any] | None = Field(None, title="Orchestration")


class BackupType(StrEnum):
    manual = "manual"
    scheduled = "scheduled"
    pre_shutdown = "pre_shutdown"


class BackupCreate(BaseModel):
    """
    A backup to take.

    Taking a backup is asynchronous; the response acknowledges the request and
    reports the backup as `in_progress`.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    backup_type: BackupType | None = Field(None, title="Backup Type")


class BackupRead(BaseModel):
    """
    One backup of a managed service instance.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    backup_type: str | None = Field(None, title="Backup Type")
    completed_at: str | None = Field(None, title="Completed At")
    error_message: str | None = Field(None, title="Error Message")
    id: str = Field(..., title="Id")
    organization_id: str | None = Field(None, title="Organization Id")
    service: str = Field(..., title="Service")
    size_bytes: int | None = Field(None, title="Size Bytes")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")


class BatchPredictionItem(BaseModel):
    """
    One input's outcome inside a batch prediction response.

    ``result`` carries the model's output for that input. ``status`` is
    ``"completed"`` on every item of every response: the batch is all-or-nothing,
    so a single input failing fails the whole call and no body is returned.
    ``error`` is reserved for a future partial-success mode and is always null
    today — do not branch on it.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    correlation_id: str = Field(..., title="Correlation Id")
    error: str | None = Field(None, title="Error")
    prediction_id: str = Field(..., title="Prediction Id")
    result: dict[str, Any] | None = Field(None, title="Result")
    status: str = Field(..., title="Status")


class BatchPredictionResponse(BaseModel):
    """
    Batch prediction result, one entry per input.

    ``prediction_ids`` and ``items`` are parallel lists in request order. The
    batch is all-or-nothing: ``status`` is ``"completed"`` on every success, a
    single input failing fails the whole batch, so there is no partial-success
    body.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    batch_id: str = Field(..., title="Batch Id")
    failed: int = Field(..., title="Failed")
    items: list[BatchPredictionItem] = Field(..., title="Items")
    prediction_ids: list[str] = Field(..., title="Prediction Ids")
    status: str = Field(..., title="Status")
    succeeded: int = Field(..., title="Succeeded")
    total: int = Field(..., title="Total")


class BillingSummaryReport(BaseModel):
    """
    ``GET /v1/billing/summary`` — full billing summary with markup applied.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    csp_partner_id: str | None = Field(None, title="Csp Partner Id")
    csp_partner_name: str | None = Field(None, title="Csp Partner Name")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    daily_costs: list[dict[str, Any]] | None = Field(None, title="Daily Costs")
    intelligence_cost_usd: float | None = Field(None, title="Intelligence Cost Usd")
    line_items: list[dict[str, Any]] | None = Field(None, title="Line Items")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    nodepool_breakdown: list[dict[str, Any]] | None = Field(
        None, title="Nodepool Breakdown"
    )
    organization_id: str | None = Field(None, title="Organization Id")
    organization_name: str | None = Field(None, title="Organization Name")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    reserved_capacity_cost_usd: float | None = Field(
        None, title="Reserved Capacity Cost Usd"
    )
    storage_cost_usd: float | None = Field(None, title="Storage Cost Usd")
    system_llm_cost_usd: float | None = Field(None, title="System Llm Cost Usd")
    total_base_cost_usd: float | None = Field(None, title="Total Base Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cpu_seconds: float | None = Field(None, title="Total Cpu Seconds")
    total_data_transfer_gb: float | None = Field(None, title="Total Data Transfer Gb")
    total_gpu_seconds: float | None = Field(None, title="Total Gpu Seconds")
    total_llm_tokens_in: int | None = Field(None, title="Total Llm Tokens In")
    total_llm_tokens_out: int | None = Field(None, title="Total Llm Tokens Out")
    total_markup_usd: float | None = Field(None, title="Total Markup Usd")
    total_memory_gb_seconds: float | None = Field(None, title="Total Memory Gb Seconds")
    total_storage_gb_hours: float | None = Field(None, title="Total Storage Gb Hours")
    transfer_cost_usd: float | None = Field(None, title="Transfer Cost Usd")
    usage_entries: list[dict[str, Any]] | None = Field(None, title="Usage Entries")
    user_llm_cost_usd: float | None = Field(None, title="User Llm Cost Usd")


class BillingUsageEntryItem(BaseModel):
    """
    One immutable billing ledger entry.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    base_cost_usd: float | None = Field(None, title="Base Cost Usd")
    capability_id: str | None = Field(None, title="Capability Id")
    credential_source: str | None = Field(None, title="Credential Source")
    currency: str | None = Field("USD", title="Currency")
    entry_id: str = Field(..., title="Entry Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    markup_amount_usd: float | None = Field(None, title="Markup Amount Usd")
    markup_percent: float | None = Field(None, title="Markup Percent")
    metadata: dict[str, Any] | None = Field(None, title="Metadata")
    meter_category: str | None = Field(None, title="Meter Category")
    meter_id: str | None = Field(None, title="Meter Id")
    meter_name: str | None = Field(None, title="Meter Name")
    model_name: str | None = Field(None, title="Model Name")
    nodepool_id: str | None = Field(None, title="Nodepool Id")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    provider: str | None = Field(None, title="Provider")
    quantity: float = Field(..., title="Quantity")
    resource_category: str = Field(..., title="Resource Category")
    resource_type: str = Field(..., title="Resource Type")
    run_id: str | None = Field(None, title="Run Id")
    source_id: str | None = Field(None, title="Source Id")
    source_kind: str = Field(..., title="Source Kind")
    source_timestamp: str = Field(..., title="Source Timestamp")
    tokens_in: int | None = Field(None, title="Tokens In")
    tokens_out: int | None = Field(None, title="Tokens Out")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    unit: str = Field(..., title="Unit")
    unit_price_usd: float | None = Field(None, title="Unit Price Usd")
    workload_id: str | None = Field(None, title="Workload Id")


class BindNodeSecretRequest(BaseModel):
    """
    Bind a secret to an orchestration node.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    alias: str | None = Field(None, title="Alias")
    node_id: str | None = Field(None, title="Node Id")
    secret_id: str = Field(..., title="Secret Id")


class BodyReplaceFileEntryContent(BaseModel):
    file: str = Field(
        ...,
        description="Replacement content",
        json_schema_extra={"contentMediaType": "application/octet-stream"},
        title="File",
    )
