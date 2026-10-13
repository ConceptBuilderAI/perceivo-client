# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class InvoiceLineItem(BaseModel):
    """
    One priced line on an invoice.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    billing_segment_id: str | None = Field(None, title="Billing Segment Id")
    category: str | None = Field(None, title="Category")
    charge_period_start: str | None = Field(None, title="Charge Period Start")
    description: str | None = Field(None, title="Description")
    enterprise_entitlement_id: str | None = Field(
        None, title="Enterprise Entitlement Id"
    )
    id: str = Field(..., title="Id")
    markup_percent: float | None = Field(None, title="Markup Percent")
    quantity: float | None = Field(None, title="Quantity")
    resource_type: str | None = Field(None, title="Resource Type")
    sort_order: int | None = Field(None, title="Sort Order")
    subtotal_usd: float | None = Field(None, title="Subtotal Usd")
    total_usd: float | None = Field(None, title="Total Usd")
    unit: str | None = Field(None, title="Unit")
    unit_price_usd: float | None = Field(None, title="Unit Price Usd")


class LifecycleOperationResponse(BaseModel):
    """
    Result of a capability start/stop/restart lifecycle operation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    capability_id: str | None = Field(None, title="Capability Id")
    details: dict[str, Any] | None = Field(None, title="Details")
    final_status: str | None = Field(None, title="Final Status")
    message: str | None = Field(None, title="Message")
    operation_id: str | None = Field(None, title="Operation Id")
    success: bool | None = Field(None, title="Success")


class LineageRestoreResult(BaseModel):
    """
    The versions one restore returned to their prior status.
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


class LogPage(BaseModel):
    """
    A bounded slice of log lines.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    channel: str | None = Field(None, title="Channel")
    logs: list[dict[str, Any]] | None = Field(None, title="Logs")
    scope: str | None = Field(None, title="Scope")


class ManagedServiceRead(BaseModel):
    """
    One managed (Azure-hosted) service instance.

    `service` is the name used in the request path. Managed services are
    addressed by name, not by instance identifier: an organization holds at
    most one live instance of each type.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    azure_resource_name: str | None = Field(None, title="Azure Resource Name")
    configuration: dict[str, Any] | None = Field(None, title="Configuration")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    hourly_rate_usd: float | None = Field(None, title="Hourly Rate Usd")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    last_activity_at: str | None = Field(None, title="Last Activity At")
    name: str | None = Field(None, title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    provisioned_at: str | None = Field(None, title="Provisioned At")
    service: str = Field(
        ...,
        description="The service name, as used in the request path.",
        title="Service",
    )
    service_display_name: str | None = Field(None, title="Service Display Name")
    sku: str | None = Field(None, title="Sku")
    status: str = Field(
        ...,
        description="Lifecycle state, e.g. pending, provisioning, running, stopping, stopped, failed.",
        title="Status",
    )
    stopped_at: str | None = Field(None, title="Stopped At")
    updated_at: str | None = Field(None, title="Updated At")


class ManagedServiceType(StrEnum):
    """
    The managed (Azure-hosted) service to operate on.
    """

    postgres = "postgres"
    redis = "redis"


class ManagedServiceUpdate(BaseModel):
    """
    Changes to apply to a managed service instance.

    Every field is optional; only the fields present in the request are
    changed. Lifecycle state is changed through the `start` and `stop`
    operations, never here.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    configuration: dict[str, Any] | None = Field(None, title="Configuration")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    name: str | None = Field(None, title="Name")
    sku: str | None = Field(None, title="Sku")


class MaterializeResponse(BaseModel):
    """
    Response from a materialize trigger.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    feature_views: list[str] | None = Field(None, title="Feature Views")
    message: str | None = Field(None, title="Message")
    status: str | None = Field(None, title="Status")


class McpConfigDocument(BaseModel):
    """
    The MCP server's configuration.

    The complete document: these are the only settings this surface manages,
    and they are exactly the settings the replace operation accepts.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool = Field(
        ...,
        description="Whether the server shuts down after a period of inactivity.",
        title="Auto Shutdown",
    )
    idle_timeout_minutes: int = Field(
        ...,
        description="Minutes of inactivity before an idle shutdown.",
        title="Idle Timeout Minutes",
    )


class McpConfigReplace(BaseModel):
    """
    A complete replacement MCP server configuration.

    Both fields are required: this operation replaces the configuration rather
    than merging into it, so the document you send is the document that results.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool = Field(
        ...,
        description="Whether the server shuts down after a period of inactivity.",
        title="Auto Shutdown",
    )
    idle_timeout_minutes: int = Field(
        ...,
        description="Minutes of inactivity before an idle shutdown.",
        ge=5,
        le=1440,
        title="Idle Timeout Minutes",
    )


class McpToolInvokeRequest(BaseModel):
    """
    Arguments for an MCP tool invocation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    arguments: dict[str, Any] | None = Field(
        None,
        description="The tool's arguments, as the tool's own schema declares them.",
        title="Arguments",
    )


class McpToolInvokeResult(BaseModel):
    """
    The result of an MCP tool invocation.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class McpToolList(BaseModel):
    """
    The tools the MCP server currently exposes.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class Message(RootModel[str]):
    root: str = Field(
        ...,
        description="A note included in the invitation e-mail.",
        max_length=1000,
        min_length=1,
        title="Message",
    )


class MemberInviteRole(StrEnum):
    """
    The role the person joins with when they accept.
    """

    admin = "admin"
    billing_admin = "billing_admin"
    member = "member"


class MemberInvite(BaseModel):
    """
    Invite a person to join your organization by e-mail.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    email: str = Field(
        ...,
        description="The address the invitation is sent to.",
        max_length=320,
        pattern="^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$",
        title="Email",
    )
    message: Message | None = Field(
        None, description="A note included in the invitation e-mail.", title="Message"
    )
    role: MemberInviteRole | None = Field(
        "member",
        description="The role the person joins with when they accept.",
        title="Role",
    )


class MemberRole(StrEnum):
    global_admin = "global_admin"
    admin = "admin"
    billing_admin = "billing_admin"
    member = "member"


class MemberRead(BaseModel):
    """
    One member of your organization.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    added_by_user_id: UUID | None = Field(None, title="Added By User Id")
    email: str = Field(..., title="Email")
    first_name: str | None = Field(None, title="First Name")
    joined_at: AwareDatetime = Field(..., title="Joined At")
    last_name: str | None = Field(None, title="Last Name")
    name: str = Field(..., title="Name")
    removed_at: AwareDatetime | None = Field(
        None,
        description="When the member was removed; absent while they are active.",
        title="Removed At",
    )
    role: MemberRole = Field(..., title="Role")
    user_id: UUID = Field(..., title="User Id")


class MemberRoleChangeRole(StrEnum):
    global_admin = "global_admin"
    admin = "admin"
    billing_admin = "billing_admin"
    member = "member"


class MemberRoleUpdateRole(StrEnum):
    """
    The member's new role.
    """

    admin = "admin"
    billing_admin = "billing_admin"
    member = "member"


class MemberRoleUpdate(BaseModel):
    """
    Change a member's role.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    role: MemberRoleUpdateRole = Field(
        ..., description="The member's new role.", title="Role"
    )


class MetricSeries(BaseModel):
    """
    An operational metrics summary or time series.

    The shape depends on the selectors. A capability or orchestration summary
    carries run counts, success rate and average duration; its `runs` series
    carries `buckets`. An intelligence summary carries the current service
    metrics; its series carries `metric`, `granularity`, `unit` and `points`.
    Only the fields below are declared; the report's own keys are passed
    through.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    buckets: list[dict[str, Any]] | None = Field(
        None,
        description="Run counts per time bucket, for `series=runs`.",
        title="Buckets",
    )
    granularity: str | None = Field(
        None,
        description="The bucket size of an intelligence series.",
        title="Granularity",
    )
    metric: str | None = Field(
        None, description="The metric of an intelligence series.", title="Metric"
    )
    points: list[dict[str, Any]] | None = Field(
        None,
        description="Evenly spaced buckets of an intelligence series, oldest first.",
        title="Points",
    )
    time_range: str | None = Field(
        None, description="The lookback window the report covers.", title="Time Range"
    )
    unit: str | None = Field(
        None, description="The unit of an intelligence series.", title="Unit"
    )
    version: str | None = Field(
        None, description="The version pinned by the request, if any.", title="Version"
    )


class ModelFamilyCreateRequest(BaseModel):
    """
    Create a model family.

    ``training_service_id`` pins the training service this family's jobs run on.
    A family without one cannot train: submitting a training job fails with
    ``PCV-INTM-VAL-0001`` ("no pinned training service").
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    inference_nodepool_id: str | None = Field(None, title="Inference Nodepool Id")
    inference_resources: dict[str, Any] | None = Field(
        None, title="Inference Resources"
    )
    inference_service_id: str | None = Field(None, title="Inference Service Id")
    name: str = Field(..., title="Name")
    private_cluster_id: str | None = Field(None, title="Private Cluster Id")
    training_nodepool_id: str | None = Field(None, title="Training Nodepool Id")
    training_resources: dict[str, Any] | None = Field(None, title="Training Resources")
    training_service_id: str | None = Field(None, title="Training Service Id")


class ModelFamilyRead(BaseModel):
    """
    A model family.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    champion_traffic_percent: int | None = Field(None, title="Champion Traffic Percent")
    created_at: str | None = Field(None, title="Created At")
    current_canary_id: str | None = Field(None, title="Current Canary Id")
    current_champion_id: str | None = Field(None, title="Current Champion Id")
    description: str | None = Field(None, title="Description")
    id: str | None = Field(None, title="Id")
    inference_nodepool_id: str | None = Field(None, title="Inference Nodepool Id")
    inference_service_id: str | None = Field(None, title="Inference Service Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    is_active: bool | None = Field(None, title="Is Active")
    name: str | None = Field(None, title="Name")
    private_cluster_id: str | None = Field(None, title="Private Cluster Id")
    traffic_percent: int | None = Field(None, title="Traffic Percent")
    training_nodepool_id: str | None = Field(None, title="Training Nodepool Id")
    training_service_id: str | None = Field(None, title="Training Service Id")
    updated_at: str | None = Field(None, title="Updated At")


class ModelFamilyUpdateRequest(BaseModel):
    """
    Update a model family (all fields optional).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    inference_nodepool_id: str | None = Field(None, title="Inference Nodepool Id")
    inference_resources: dict[str, Any] | None = Field(
        None, title="Inference Resources"
    )
    inference_service_id: str | None = Field(None, title="Inference Service Id")
    is_active: bool | None = Field(None, title="Is Active")
    name: str | None = Field(None, title="Name")
    private_cluster_id: str | None = Field(None, title="Private Cluster Id")
    traffic_percent: int | None = Field(None, title="Traffic Percent")
    training_nodepool_id: str | None = Field(None, title="Training Nodepool Id")
    training_resources: dict[str, Any] | None = Field(None, title="Training Resources")
    training_service_id: str | None = Field(None, title="Training Service Id")
