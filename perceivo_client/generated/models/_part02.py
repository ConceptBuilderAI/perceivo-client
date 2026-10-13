# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class BuildExecutionGraphRequest(BaseModel):
    """
    Build an execution graph.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    config: dict[str, Any] | None = Field(None, title="Config")


class BulkCancelResponse(BaseModel):
    """
    Count of cancelled inputs from a bulk-cancel.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    cancelled_count: int | None = Field(None, title="Cancelled Count")


class BulkOperationResult(BaseModel):
    """
    Outcome counts for a bulk file-manager operation.
    """

    failed_count: int = Field(..., title="Failed Count")
    failed_ids: list[UUID] | None = Field([], title="Failed Ids")
    message: str = Field(..., title="Message")
    success_count: int = Field(..., title="Success Count")


class CancelInputResponse(BaseModel):
    """
    Result of cancelling a single persistent input request.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    request_id: str | None = Field(None, title="Request Id")
    status: str | None = Field(None, title="Status")


class CapabilitiesCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/capabilities``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capabilities: list[dict[str, Any]] | None = Field(None, title="Capabilities")
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
    total_evaluation_cost_usd: float | None = Field(
        None, title="Total Evaluation Cost Usd"
    )
    total_evaluation_cu_hours: float | None = Field(
        None, title="Total Evaluation Cu Hours"
    )
    total_runs: int | None = Field(None, title="Total Runs")


class CapabilityCompatibilityRead(BaseModel):
    """
    Dry-run report for assigning an orchestration to a capability.

    ``incompatible_edge_count`` is the number of edges the assignment would
    DISCONNECT. Assignment succeeds regardless -- it drops those edges rather
    than refusing -- so a non-zero count here is the only warning a caller gets
    before the graph is silently altered.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    details: list[str] | None = Field(None, title="Details")
    end_compatible: bool | None = Field(None, title="End Compatible")
    incompatible_edge_count: int | None = Field(None, title="Incompatible Edge Count")
    is_compatible: bool | None = Field(None, title="Is Compatible")
    start_compatible: bool | None = Field(None, title="Start Compatible")


class CapabilityCopyRequestNewName(RootModel[str]):
    root: str = Field(
        ...,
        description="Name for the copy. Defaults to the source name followed by `(copy)`.",
        max_length=255,
        min_length=1,
        title="New Name",
    )


class CapabilityCopyRequest(BaseModel):
    """
    Body for ``POST /v1/capabilities/{capability_id}/copy``.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    new_name: CapabilityCopyRequestNewName | None = Field(
        None,
        description="Name for the copy. Defaults to the source name followed by `(copy)`.",
        title="New Name",
    )


class CapabilityCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/capability/{capability_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str | None = Field(None, title="Capability Id")
    capability_name: str | None = Field(None, title="Capability Name")
    children: list[dict[str, Any]] | None = Field(None, title="Children")
    component_costs: list[dict[str, Any]] | None = Field(None, title="Component Costs")
    llm_costs: dict[str, Any] | None = Field(None, title="Llm Costs")
    organization_id: str | None = Field(None, title="Organization Id")
    period: dict[str, Any] | None = Field(None, title="Period")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    summary: dict[str, Any] | None = Field(None, title="Summary")
    user_reported_costs: dict[str, Any] | None = Field(
        None, title="User Reported Costs"
    )


class CapabilityCreate(BaseModel):
    """
    Create a new capability.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    end_component_id: str | None = Field(None, title="End Component Id")
    execution_mode: str | None = Field(None, title="Execution Mode")
    expected_output_schema: dict[str, Any] | None = Field(
        None, title="Expected Output Schema"
    )
    idle_timeout_seconds: int | None = Field(None, title="Idle Timeout Seconds")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    start_component_id: str | None = Field(None, title="Start Component Id")
    tags: list[str] | None = Field(None, title="Tags")


class CapabilityEvaluationConfigRead(BaseModel):
    """
    A capability's evaluation configuration.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    auto_accept: bool | None = Field(False, title="Auto Accept")
    capability_id: str = Field(..., title="Capability Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    enabled: bool = Field(..., title="Enabled")
    evaluation_window_hours: int | None = Field(24, title="Evaluation Window Hours")
    evaluator_component_id: str | None = Field(None, title="Evaluator Component Id")
    id: str = Field(..., title="Id")
    last_evaluated_at: AwareDatetime | None = Field(None, title="Last Evaluated At")
    next_evaluation_at: AwareDatetime | None = Field(None, title="Next Evaluation At")
    organization_id: str = Field(..., title="Organization Id")
    requires_review: bool = Field(..., title="Requires Review")
    resources: dict[str, Any] | None = Field(None, title="Resources")
    updated_at: AwareDatetime = Field(..., title="Updated At")


class CapabilityEvaluationConfigWrite(BaseModel):
    """
    The complete evaluation configuration to store for a capability.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_accept: bool | None = Field(
        False,
        description="Whether a score is accepted without waiting for review.",
        title="Auto Accept",
    )
    enabled: bool | None = Field(
        False,
        description="Whether this capability's runs are evaluated.",
        title="Enabled",
    )
    evaluation_window_hours: int | None = Field(
        24,
        description="How many hours of runs each evaluation covers.",
        title="Evaluation Window Hours",
    )
    evaluator_component_id: str | None = Field(
        None,
        description="The evaluator component that scores each run.",
        title="Evaluator Component Id",
    )
    requires_review: bool | None = Field(
        False,
        description="Whether a score must be reviewed before it counts.",
        title="Requires Review",
    )
    resources: dict[str, Any] | None = Field(
        None,
        description="Resource settings for the evaluator run, stored as given.",
        title="Resources",
    )


class CapabilityOrchestrationEvaluationSummary(BaseModel):
    """
    Aggregate scores for one orchestration of the capability.
    """

    avg_score: float = Field(..., title="Avg Score")
    count: int = Field(
        ..., description="How many scores the aggregates are taken over", title="Count"
    )
    max_score: float = Field(..., title="Max Score")
    min_score: float = Field(..., title="Min Score")
    orchestration_id: UUID = Field(..., title="Orchestration Id")
    orchestration_name: str | None = Field(None, title="Orchestration Name")


class CapabilityQueueDepthRead(BaseModel):
    """
    How much work is waiting for a capability, and how long the oldest item has waited.
    """

    capability_id: str = Field(..., title="Capability Id")
    oldest_wait_seconds: float | None = Field(
        None,
        description="Seconds the oldest waiting item has been queued, if any",
        title="Oldest Wait Seconds",
    )
    queue_depth: int = Field(
        ...,
        description="Total items waiting across every queue for this capability",
        title="Queue Depth",
    )


class CapabilityQueuePurgeResult(BaseModel):
    """
    What a queue purge dropped.
    """

    cancelled_requests: int = Field(
        ...,
        description="Queued input records marked cancelled. Running work is not affected.",
        title="Cancelled Requests",
    )
    capability_id: str = Field(..., title="Capability Id")
    purged_queue_keys: int = Field(
        ...,
        description="Per-orchestration and capability-level queues that were cleared",
        title="Purged Queue Keys",
    )


class CapabilityRead(BaseModel):
    """
    Capability resource representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    execution_mode: str | None = Field(None, title="Execution Mode")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    status: str | None = Field(None, title="Status")
    updated_at: str | None = Field(None, title="Updated At")


class CapabilityTrafficAllocationRead(BaseModel):
    """
    One member orchestration of a traffic plan, and the share of traffic it takes.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    execution_mode: str | None = Field(
        "persistent",
        description="How the member runs: persistent or on-demand",
        title="Execution Mode",
    )
    id: str = Field(..., title="Id")
    orchestration_id: str = Field(..., title="Orchestration Id")
    role: str = Field(
        ...,
        description="This member's role in the plan, such as champion or canary",
        title="Role",
    )
    traffic_percent: float = Field(
        ...,
        description="Share of traffic routed to this orchestration",
        title="Traffic Percent",
    )
    traffic_plan_id: str = Field(..., title="Traffic Plan Id")


class CapabilityTrafficAllocationWrite(BaseModel):
    """
    One member orchestration of a submitted traffic plan.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    execution_mode: str | None = Field(
        "persistent",
        description="How this member runs: persistent or on_demand.",
        pattern="^(persistent|on_demand)$",
        title="Execution Mode",
    )
    orchestration_id: UUID = Field(..., title="Orchestration Id")
    role: str = Field(
        ...,
        description="This member's role in the plan: champion, canary or shadow.",
        pattern="^(champion|canary|shadow)$",
        title="Role",
    )
    traffic_percent: float | None = Field(
        0,
        description="Share of traffic routed to this orchestration.",
        ge=0.0,
        le=100.0,
        title="Traffic Percent",
    )
    workload_config: dict[str, Any] | None = Field(None, title="Workload Config")


class CapabilityTrafficPlanRead(BaseModel):
    """
    The routing plan a capability run resolves against.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    allocations: list[CapabilityTrafficAllocationRead] | None = Field(
        None, title="Allocations"
    )
    capability_id: str = Field(..., title="Capability Id")
    change_reason: str | None = Field(None, title="Change Reason")
    change_source: str = Field(
        ..., description="What produced this plan", title="Change Source"
    )
    created_at: AwareDatetime = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    implemented_at: AwareDatetime | None = Field(None, title="Implemented At")
    previous_plan_id: str | None = Field(None, title="Previous Plan Id")
    status: str = Field(
        ...,
        description="Plan lifecycle state, such as active or stopped",
        title="Status",
    )


class CapabilityTrafficReplace(BaseModel):
    """
    The complete desired traffic plan.

    `allocations` must be non-empty: an empty plan is not a plan. To stop
    routing altogether, supersede the plan with
    `DELETE /v1/capabilities/{capability_id}/traffic`.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    allocations: list[CapabilityTrafficAllocationWrite] = Field(
        ...,
        description="Every member of the plan. Replaces the current set.",
        min_length=1,
        title="Allocations",
    )
    change_reason: str | None = Field(
        None,
        description="Free text recorded against this plan revision.",
        title="Change Reason",
    )


class CapabilityTriggerCreate(BaseModel):
    """
    The evaluation schedule to create for a capability.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    cron_expression: str = Field(
        ...,
        description="A cron expression, evaluated in UTC. It must parse; an expression that does not is refused rather than stored.",
        title="Cron Expression",
    )
    enabled: bool | None = Field(
        True, description="Whether the schedule fires.", title="Enabled"
    )
    http_enabled: bool | None = Field(
        False,
        description="Always `false`; a capability trigger cannot be invoked.",
        title="Http Enabled",
    )
    timezone: Literal["UTC"] = Field(
        "UTC", description="Always `UTC`; no other zone is accepted.", title="Timezone"
    )
    trigger_type: Literal["evaluation"] = Field(
        "evaluation",
        description="The only trigger type a capability has.",
        title="Trigger Type",
    )


class CapabilityTriggerRead(BaseModel):
    """
    A capability's evaluation trigger.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    cron_expression: str = Field(..., title="Cron Expression")
    enabled: bool = Field(..., title="Enabled")
    id: UUID = Field(..., title="Id")
    last_evaluated_at: AwareDatetime | None = Field(
        None,
        description="When the schedule last fired an evaluation. Set by the platform.",
        title="Last Evaluated At",
    )
    timezone: str = Field(..., title="Timezone")
    trigger_type: Literal["evaluation"] = Field(..., title="Trigger Type")
