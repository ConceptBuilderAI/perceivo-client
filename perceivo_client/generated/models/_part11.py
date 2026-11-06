# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 4cb0cc1fb62e540b6329e643c14e3ed2ef7982f14766508c71bd02701feb1b21

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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


class ModelLifecycleResult(BaseModel):
    """
    Result of a model-lifecycle transition (retire/restore).

    The response wraps the model in a status envelope:
    ``{success, model_id, from_status, to_status, model}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    from_status: str | None = Field(None, title="From Status")
    model: dict[str, Any] | None = Field(None, title="Model")
    model_id: str | None = Field(None, title="Model Id")
    success: bool | None = Field(None, title="Success")
    to_status: str | None = Field(None, title="To Status")


class ModelPromotionResult(BaseModel):
    """
    Result of promoting a model to a target stage (champion or canary).

    All promotions return ``message`` and ``model_id``; the remaining fields are
    stage-specific:

    * **champion** — ``inference_endpoint``
    * **canary** — ``traffic_percent``, ``canary_endpoint``, ``champion_traffic_percent``
    """

    model_config = ConfigDict(
        extra="allow",
    )
    canary_endpoint: str | None = Field(None, title="Canary Endpoint")
    champion_traffic_percent: int | None = Field(None, title="Champion Traffic Percent")
    inference_endpoint: str | None = Field(None, title="Inference Endpoint")
    message: str | None = Field(None, title="Message")
    model_id: str | None = Field(None, title="Model Id")
    traffic_percent: int | None = Field(None, title="Traffic Percent")


class ModelRead(BaseModel):
    """
    Trained model representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    name: str | None = Field(
        None,
        description="The name of the model family this model belongs to. A model has no name of its own.",
        title="Name",
    )
    stage: str | None = Field(None, title="Stage")


class ModelRegisterRequest(BaseModel):
    """
    A pre-trained model to register without running the training pipeline.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_path: str = Field(..., min_length=1, title="Artifact Path")
    family_id: str = Field(..., title="Family Id")
    hyperparameters: dict[str, Any] | None = Field(None, title="Hyperparameters")
    metrics: dict[str, float | None] | None = Field(None, title="Metrics")
    source_type: str | None = Field("uploaded", title="Source Type")


class NamespaceReconciliation(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    capabilities: dict[str, Any] = Field(
        ...,
        description="Capability CU and cost: component execution, platform overhead, idle.",
        title="Capabilities",
    )
    experiments: dict[str, Any] = Field(
        ..., description="Experiment run-time CU and cost.", title="Experiments"
    )
    infrastructure_cluster: dict[str, Any] = Field(
        ...,
        description="Cluster infrastructure CU and cost by service (Ray, the cache, Milvus, Elasticsearch, MCP server, dedicated nodepool).",
        title="Infrastructure Cluster",
    )
    infrastructure_other: dict[str, Any] = Field(
        ...,
        description="Managed services, storage and egress cost.",
        title="Infrastructure Other",
    )
    intelligence: dict[str, Any] = Field(
        ...,
        description="Intelligence execution and idle CU and cost.",
        title="Intelligence",
    )
    orchestrations: dict[str, Any] = Field(
        ..., description="Orchestration CU and cost.", title="Orchestrations"
    )
    organization_id: str = Field(
        ..., description="The organization reconciled (UUID).", title="Organization Id"
    )
    period_end: str = Field(
        ..., description="End of the reconciled period (ISO 8601).", title="Period End"
    )
    period_start: str = Field(
        ...,
        description="Start of the reconciled period (ISO 8601).",
        title="Period Start",
    )
    token_costs: dict[str, Any] = Field(
        ..., description="Model token cost by source.", title="Token Costs"
    )
    total_compute_cu_hours: float = Field(
        ...,
        description="Total compute CU-hours in the period.",
        title="Total Compute Cu Hours",
    )
    total_cost_usd: float = Field(
        ..., description="Total cost in the period, USD.", title="Total Cost Usd"
    )
    verification: dict[str, Any] = Field(
        ...,
        description="Metered compute against reported compute: the delta in CU and percent, and `status` (`OK` when they agree, else `WARN`).",
        title="Verification",
    )


class NodeSecretBinding(RootModel[dict[str, UUID]]):
    """
    The secrets bound to one node, keyed by the alias its script reads them under.
    """

    root: dict[str, UUID]


class NodeSecretRead(BaseModel):
    """
    Node secret binding representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    alias: str = Field(..., title="Alias")
    created_at: str | None = Field(None, title="Created At")
    id: str = Field(..., title="Id")
    node_id: str = Field(..., title="Node Id")
    orchestration_id: str = Field(..., title="Orchestration Id")
    secret_expiration_date: str | None = Field(None, title="Secret Expiration Date")
    secret_id: str = Field(..., title="Secret Id")
    secret_name: str | None = Field(None, title="Secret Name")
    secret_status: str | None = Field(None, title="Secret Status")


class NodepoolCost(BaseModel):
    """
    One nodepool cost row. ``GET /v1/billing/nodepool-costs`` returns a JSON
    ARRAY of these.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    nodepool_id: str | None = Field(None, title="Nodepool Id")
    nodepool_name: str | None = Field(None, title="Nodepool Name")
    sku: str | None = Field(None, title="Sku")
    snapshot_count: int | None = Field(None, title="Snapshot Count")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_uptime_hours: float | None = Field(None, title="Total Uptime Hours")
