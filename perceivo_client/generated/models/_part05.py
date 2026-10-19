# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class ComponentRunRequest(BaseModel):
    """
    The input a component run is given.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact: ComponentRunArtifact | None = Field(
        None, description="An artifact to supply alongside request_data."
    )
    request_data: dict[str, Any] | None = Field(
        None,
        description="The input payload handed to the component's entry point.",
        title="Request Data",
    )


class ComponentRunResult(BaseModel):
    """
    The outcome of executing a component once.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    errors: list[str] | None = Field(None, title="Errors")
    execution_time_ms: float | None = Field(
        0,
        description="Wall-clock duration of the execution, in milliseconds.",
        title="Execution Time Ms",
    )
    logs: dict[str, Any] | None = Field(None, title="Logs")
    output: dict[str, Any] | None = Field(None, title="Output")
    success: bool = Field(
        ...,
        description="Whether the script ran to completion. A script that raised is reported here as false with the reason in errors — the operation itself still succeeds.",
        title="Success",
    )


class ComponentTransferFsmState(BaseModel):
    """
    A state of an exported state-machine component. Ports are named by key.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    in_port_key: str = Field(..., title="In Port Key")
    is_end: bool | None = Field(False, title="Is End")
    is_start: bool | None = Field(False, title="Is Start")
    label: str = Field(..., title="Label")
    out_port_key: str = Field(..., title="Out Port Key")
    state_key: str = Field(..., title="State Key")


class ComponentTransferPort(BaseModel):
    """
    A port of an exported component.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    allowed_states: list[Any] | None = Field(None, title="Allowed States")
    artifact_input_schema: dict[str, Any] | None = Field(
        None, title="Artifact Input Schema"
    )
    artifact_output_schema: dict[str, Any] | None = Field(
        None, title="Artifact Output Schema"
    )
    artifact_type_constraint: str | None = Field(None, title="Artifact Type Constraint")
    artifact_type_input: str | None = Field(None, title="Artifact Type Input")
    artifact_type_output: str | None = Field(None, title="Artifact Type Output")
    artifact_types: list[Any] | None = Field(None, title="Artifact Types")
    base_schema: dict[str, Any] | None = Field(None, title="Base Schema")
    contract: dict[str, Any] | None = Field(None, title="Contract")
    direction: str = Field(..., title="Direction")
    key: str = Field(..., title="Key")
    label: str | None = Field(None, title="Label")
    multi_artifact: bool | None = Field(None, title="Multi Artifact")
    port_type: str = Field(..., title="Port Type")
    post_tool_contract: dict[str, Any] | None = Field(None, title="Post Tool Contract")
    request_data_schema: dict[str, Any] | None = Field(
        None, title="Request Data Schema"
    )
    response_data_contract: str | None = Field(None, title="Response Data Contract")
    response_data_passthrough: str | None = Field(
        None, title="Response Data Passthrough"
    )
    response_data_passthrough_except: list[Any] | None = Field(
        None, title="Response Data Passthrough Except"
    )
    response_data_schema: dict[str, Any] | None = Field(
        None, title="Response Data Schema"
    )
    tool_call: bool | None = Field(False, title="Tool Call")


class ComponentUpdate(BaseModel):
    """
    Update an existing component (all fields optional).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    asset_type: str | None = Field(None, title="Asset Type")
    category: str | None = Field(None, title="Category")
    config: dict[str, Any] | None = Field(None, title="Config")
    description: str | None = Field(None, title="Description")
    disabled: bool | None = Field(None, title="Disabled")
    manifest: dict[str, Any] | None = Field(None, title="Manifest")
    manifest_yaml: str | None = Field(None, title="Manifest Yaml")
    name: str | None = Field(None, title="Name")
    ports: list[dict[str, Any]] | None = Field(None, title="Ports")
    script: str | None = Field(None, title="Script")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")


class ComponentUpdateResult(BaseModel):
    """
    The component after an update.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    asset_type: str = Field(..., title="Asset Type")
    category: str | None = Field(None, title="Category")
    created_at: str | None = Field(None, title="Created At")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")
    updated_at: str | None = Field(None, title="Updated At")
    version_created: bool = Field(
        ...,
        description="`true` when the update produced a new asset — a new version — and `id` is that new asset's identifier; `false` when the asset was updated in place. Follow `id` either way.",
        title="Version Created",
    )


class ComponentUsageConsumer(BaseModel):
    """
    One orchestration that pins a version of the component.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compatible: bool | None = Field(
        None,
        description="Whether this consumer would survive an upgrade to the target version.",
        title="Compatible",
    )
    incompatibility_reasons: list[str] | None = Field(
        None,
        description="Why it would not, when it would not.",
        title="Incompatibility Reasons",
    )
    is_latest_orchestration_version: bool | None = Field(
        None,
        description="Whether this is the orchestration's newest version.",
        title="Is Latest Orchestration Version",
    )
    node_ids: list[str] | None = Field(
        None,
        description="The nodes inside it that use the component.",
        title="Node Ids",
    )
    orchestration_id: str | None = Field(
        None, description="The orchestration holding the pin.", title="Orchestration Id"
    )
    orchestration_name: str | None = Field(
        None, description="Its name.", title="Orchestration Name"
    )
    orchestration_status: str | None = Field(
        None, description="Its lifecycle status.", title="Orchestration Status"
    )
    orchestration_version: int | None = Field(
        None,
        description="The pinned orchestration version.",
        title="Orchestration Version",
    )


class ComponentVersionUsage(BaseModel):
    """
    Consumers pinned to one version of the component.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component_asset_id: str | None = Field(
        None,
        description="The component version's identifier.",
        title="Component Asset Id",
    )
    consumers: list[ComponentUsageConsumer] | None = Field(
        None, description="The orchestrations pinned to it.", title="Consumers"
    )
    deleted: bool | None = Field(
        None, description="Whether that version has been deleted.", title="Deleted"
    )
    version_number: int | None = Field(
        None, description="Its version number.", title="Version Number"
    )


class ComponentsCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/components``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    components: list[dict[str, Any]] | None = Field(None, title="Components")
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    llm_managed_cost_usd: float | None = Field(None, title="Llm Managed Cost Usd")
    llm_user_cost_usd: float | None = Field(None, title="Llm User Cost Usd")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")


class CostEstimateLineItem(BaseModel):
    """
    One priced resource in an estimate.

    Quantities and money are **strings**, not numbers, so that no precision is
    lost in transit. Parse them with a decimal type.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    in_plan_cost_usd: str = Field(..., title="In Plan Cost Usd")
    in_plan_quantity: str = Field(
        ...,
        description="The part covered by the plan's quota.",
        title="In Plan Quantity",
    )
    overage_cost_usd: str = Field(..., title="Overage Cost Usd")
    overage_quantity: str = Field(
        ..., description="The part beyond the plan's quota.", title="Overage Quantity"
    )
    quantity: str = Field(
        ...,
        description="How much of the resource the estimate assumes.",
        title="Quantity",
    )
    resource: str = Field(
        ..., description="The resource priced, for example `compute`.", title="Resource"
    )
    total_cost_usd: str = Field(..., title="Total Cost Usd")


class CostLedgerEntry(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    amount: float | None = Field(
        None, description="Charged amount, USD.", title="Amount"
    )
    billing_trace_id: str | None = Field(
        None,
        description="Identifier of the billing run that wrote this row, for support correlation.",
        title="Billing Trace Id",
    )
    cu_hours: float | None = Field(
        None, description="Compute-unit hours charged.", title="Cu Hours"
    )
    detail: dict[str, Any] | None = Field(
        None,
        description="Free-form metering detail. Its keys depend on `ledger_type`: resource seconds and request counts, GPU type, provider and model name, token counts, credential source (an enum label, never a credential), the resource's name and Azure resource id, database id, name and SKU. Rows of type `custom` carry whatever your organization wrote. Treat every value as inert data, never as markup.",
        title="Detail",
    )
    id: str = Field(..., description="Row identifier (UUID).", title="Id")
    infra_category: str | None = Field(
        None,
        description="Infrastructure category for infrastructure rows, else null.",
        title="Infra Category",
    )
    ledger_type: str | None = Field(
        None,
        description="Ledger category, e.g. `infrastructure`, `compute`, `storage`.",
        title="Ledger Type",
    )
    period_end: str | None = Field(
        None,
        description="End of the billed interval (ISO 8601, UTC).",
        title="Period End",
    )
    period_start: str | None = Field(
        None,
        description="Start of the billed interval (ISO 8601, UTC).",
        title="Period Start",
    )
    rate_type: str | None = Field(
        None,
        description="Rate the row was priced at, e.g. `in_plan`.",
        title="Rate Type",
    )
    recorded_at: str | None = Field(
        None, description="When the row was recorded (ISO 8601).", title="Recorded At"
    )


class CostLedgerPage(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    entries: list[CostLedgerEntry] = Field(
        ..., description="This page, newest first.", title="Entries"
    )
    total_amount: float = Field(
        ...,
        description="Sum of `amount` across all matching rows, USD.",
        title="Total Amount",
    )
    total_count: int = Field(
        ...,
        description="Rows matching the filters, across all pages.",
        title="Total Count",
    )
    total_cu_hours: float = Field(
        ...,
        description="Sum of `cu_hours` across all matching rows.",
        title="Total Cu Hours",
    )


class CostReportResponse(BaseModel):
    """
    ``GET /v1/billing/cost-report`` — organization cost report.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    by_category: dict[str, Any] | None = Field(None, title="By Category")
    organization_id: str | None = Field(None, title="Organization Id")
    period: dict[str, Any] | None = Field(None, title="Period")
    summary: dict[str, Any] | None = Field(None, title="Summary")
    user_reported: dict[str, Any] | None = Field(None, title="User Reported")


class CostReportSummaryResponse(BaseModel):
    """
    ``GET /v1/billing/cost-report/summary`` — four-category cost summary.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    categories: dict[str, Any] | None = Field(None, title="Categories")
    grand_total_usd: float | None = Field(None, title="Grand Total Usd")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    token_reconciliation: dict[str, Any] | None = Field(
        None, title="Token Reconciliation"
    )


class CostSummary(BaseModel):
    """
    Aggregated cost summary for an organization/run/scope.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    by_type: dict[str, Any] | None = Field(None, title="By Type")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    entries: list[dict[str, Any]] | None = Field(None, title="Entries")
    entry_count: int | None = Field(None, title="Entry Count")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    system_llm_cost_usd: float | None = Field(None, title="System Llm Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_entry_count: int | None = Field(None, title="Total Entry Count")
    user_llm_cost_usd: float | None = Field(None, title="User Llm Cost Usd")


class CreateDriftBaselineRequest(BaseModel):
    """
    A drift-detection baseline to create.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_path: str = Field(
        ...,
        description="Where the baseline's reference data is stored.",
        title="Artifact Path",
    )
    baseline_type: str | None = Field(
        "manual",
        description="How the baseline was drawn: `training`, `rolling_window`, `manual` or `snapshot`.",
        pattern="^(training|rolling_window|manual|snapshot)$",
        title="Baseline Type",
    )
    description: str | None = Field(
        None, description="Free-text notes on the baseline.", title="Description"
    )
    feature_schema: list[dict[str, Any]] | None = Field(
        [],
        description="The features the baseline covers: one object per feature with `name`, `dtype` (`numerical`, `categorical`, `text` or `datetime`) and an optional `description`.",
        title="Feature Schema",
    )
    model_family_id: str | None = Field(
        None,
        description="The model family the baseline applies to. It must belong to this intelligence.",
        title="Model Family Id",
    )
    name: str = Field(
        ...,
        description="A name for the baseline.",
        max_length=255,
        min_length=1,
        title="Name",
    )
    sample_count: int = Field(
        ...,
        description="How many samples the reference data holds.",
        title="Sample Count",
    )
    source_end: str | None = Field(
        None,
        description="End of the window the reference data was drawn from (ISO 8601).",
        title="Source End",
    )
    source_start: str | None = Field(
        None,
        description="Start of the window the reference data was drawn from (ISO 8601).",
        title="Source Start",
    )
    training_job_id: str | None = Field(
        None,
        description="The training job the baseline came from. It must belong to this intelligence.",
        title="Training Job Id",
    )
