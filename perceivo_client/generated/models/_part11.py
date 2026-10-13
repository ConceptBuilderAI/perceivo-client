# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class ModelLifecycleResult(BaseModel):
    """
    Result of a model-lifecycle transition (retire/restore).

    The gateway wraps the underlying model in a status envelope:
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
    name: str | None = Field(None, title="Name")
    stage: str | None = Field(None, title="Stage")


class ModelRegisterRequestName(RootModel[str]):
    root: str = Field(..., max_length=255, title="Name")


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
    name: ModelRegisterRequestName | None = Field(None, title="Name")
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


class NodeSecretBindRequest(BaseModel):
    """
    The secret to bind. The node and the alias are named by the path.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    secret_id: UUID = Field(
        ...,
        description="The secret to bind. You must have read access to it.",
        title="Secret Id",
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


class NodepoolDetail(BaseModel):
    """
    One private compute nodepool belonging to this organization.

    Nodepools are addressed by `name` on this surface. Provisioning and
    teardown are asynchronous: `status` reports where the nodepool actually is,
    which is not necessarily what the last request asked for.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    created_at: str | None = Field(None, title="Created At")
    error_message: str | None = Field(None, title="Error Message")
    gpu_type: str | None = Field(None, title="Gpu Type")
    hourly_rate_usd: float | None = Field(None, title="Hourly Rate Usd")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    last_activity_at: str | None = Field(None, title="Last Activity At")
    max_nodes: int | None = Field(None, title="Max Nodes")
    min_nodes: int | None = Field(None, title="Min Nodes")
    name: str = Field(..., title="Name")
    node_count: int | None = Field(None, title="Node Count")
    organization_id: str | None = Field(None, title="Organization Id")
    provisioned_at: str | None = Field(None, title="Provisioned At")
    sku: str | None = Field(None, title="Sku")
    status: str | None = Field(None, title="Status")
    updated_at: str | None = Field(None, title="Updated At")
    warning_message: str | None = Field(None, title="Warning Message")


class NodepoolListResponse(BaseModel):
    """
    Every private nodepool this organization holds.
    """

    items: list[NodepoolDetail] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class IdleTimeoutMinutes(RootModel[int]):
    root: int = Field(..., gt=0, title="Idle Timeout Minutes")


class MaxNodes(RootModel[int]):
    root: int = Field(..., gt=0, title="Max Nodes")


class MinNodes(RootModel[int]):
    root: int = Field(..., ge=0, title="Min Nodes")


class NodepoolProvision(BaseModel):
    """
    A new private compute nodepool.

    Provisioning is asynchronous and takes minutes; the response acknowledges
    the request and reports the nodepool as `pending`.
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
    name: str = Field(..., max_length=100, min_length=1, title="Name")
    sku: str = Field(..., min_length=1, title="Sku")


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


class OperationEnvelope(BaseModel):
    """
    An accepted asynchronous operation.

    Note: for trigger invocations, `poll` does not resolve to a run status, and
    the run's status cannot currently be looked up through the public API. Do
    not poll it.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str = Field(
        ..., description="When the work was accepted, ISO-8601 UTC.", title="Created At"
    )
    events: str = Field(
        ...,
        description="The events URL the platform names for this work. For a trigger invocation it does not currently resolve.",
        title="Events",
    )
    id: str = Field(
        ..., description="Identifier of the work that was started.", title="Id"
    )
    kind: str | None = Field(
        "run", description="What kind of work this is, such as `run`.", title="Kind"
    )
    poll: str = Field(
        ...,
        description="The progress URL the platform names for this work. For a trigger invocation it does not currently resolve.",
        title="Poll",
    )
    result: str = Field(
        ...,
        description="The result URL the platform names for this work. For a trigger invocation it does not currently resolve.",
        title="Result",
    )
    status: str | None = Field(
        "queued",
        description="The state of the work when this response was sent, for example `queued`. It is not updated afterwards.",
        title="Status",
    )


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
