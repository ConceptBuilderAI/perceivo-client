# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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


class OrganizationInfrastructureRead(BaseModel):
    """
    The organization's infrastructure configuration (a single object).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    elasticsearch_auto_shutdown: bool | None = Field(
        None, title="Elasticsearch Auto Shutdown"
    )
    elasticsearch_blob_container: str | None = Field(
        None, title="Elasticsearch Blob Container"
    )
    elasticsearch_host: str | None = Field(None, title="Elasticsearch Host")
    elasticsearch_idle_timeout_minutes: int | None = Field(
        None, title="Elasticsearch Idle Timeout Minutes"
    )
    elasticsearch_last_activity_at: str | None = Field(
        None, title="Elasticsearch Last Activity At"
    )
    elasticsearch_port: int | None = Field(None, title="Elasticsearch Port")
    elasticsearch_size: str | None = Field(None, title="Elasticsearch Size")
    elasticsearch_snapshot_repo: str | None = Field(
        None, title="Elasticsearch Snapshot Repo"
    )
    elasticsearch_started_at: str | None = Field(None, title="Elasticsearch Started At")
    elasticsearch_status: str | None = Field(None, title="Elasticsearch Status")
    elasticsearch_storage_bytes: int | None = Field(
        None, title="Elasticsearch Storage Bytes"
    )
    feast_registry_url: str | None = Field(None, title="Feast Registry Url")
    files_storage_bytes: int | None = Field(None, title="Files Storage Bytes")
    id: str = Field(..., title="Id")
    intelligence_storage_bytes: int | None = Field(
        None, title="Intelligence Storage Bytes"
    )
    milvus_auto_shutdown: bool | None = Field(None, title="Milvus Auto Shutdown")
    milvus_blob_container: str | None = Field(None, title="Milvus Blob Container")
    milvus_file_share: str | None = Field(None, title="Milvus File Share")
    milvus_health_reason: str | None = Field(None, title="Milvus Health Reason")
    milvus_host: str | None = Field(None, title="Milvus Host")
    milvus_idle_timeout_minutes: int | None = Field(
        None, title="Milvus Idle Timeout Minutes"
    )
    milvus_last_activity_at: str | None = Field(None, title="Milvus Last Activity At")
    milvus_last_health_check_at: str | None = Field(
        None, title="Milvus Last Health Check At"
    )
    milvus_port: int | None = Field(None, title="Milvus Port")
    milvus_size: str | None = Field(None, title="Milvus Size")
    milvus_started_at: str | None = Field(None, title="Milvus Started At")
    milvus_status: str | None = Field(None, title="Milvus Status")
    milvus_storage_bytes: int | None = Field(None, title="Milvus Storage Bytes")
    orchestrations_storage_bytes: int | None = Field(
        None, title="Orchestrations Storage Bytes"
    )
    org_container_name: str | None = Field(None, title="Org Container Name")
    organization_id: str = Field(..., title="Organization Id")
    redis_auto_shutdown: bool | None = Field(None, title="Redis Auto Shutdown")
    redis_azure_resource_name: str | None = Field(
        None, title="Redis Azure Resource Name"
    )
    redis_host: str | None = Field(None, title="Redis Host")
    redis_idle_timeout_minutes: int | None = Field(
        None, title="Redis Idle Timeout Minutes"
    )
    redis_last_activity_at: str | None = Field(None, title="Redis Last Activity At")
    redis_mode: str | None = Field(None, title="Redis Mode")
    redis_port: int | None = Field(None, title="Redis Port")
    redis_size: str | None = Field(None, title="Redis Size")
    redis_started_at: str | None = Field(None, title="Redis Started At")
    redis_status: str | None = Field(None, title="Redis Status")
    redis_storage_bytes: int | None = Field(None, title="Redis Storage Bytes")
    status: str | None = Field(None, title="Status")
    storage_last_updated_at: str | None = Field(None, title="Storage Last Updated At")
    teardown_scheduled_at: str | None = Field(None, title="Teardown Scheduled At")
    total_storage_bytes: int | None = Field(None, title="Total Storage Bytes")
    updated_at: str | None = Field(None, title="Updated At")


class OrganizationLimitsRead(BaseModel):
    """
    The effective resource limits of a subscription.

    Note: ``max_concurrent_workloads`` and ``max_monthly_cost_usd`` are always
    ``None``: no tier or override column carries either, and spend is bounded
    by the balance stops, not a monthly cap. The four ``*_enforcement_limit``
    fields are the caps that are actually enforced.

    ``platform_token_monthly_quota`` is the included-token figure billing uses.
    ``max_monthly_input_tokens`` / ``max_monthly_output_tokens`` are legacy:
    not enforced and not the billing basis.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    cu_hours_enforcement_limit: int | None = Field(
        None,
        description="Compute-unit hours per billing period before new work is refused.",
        title="Cu Hours Enforcement Limit",
    )
    egress_gb_enforcement_limit: int | None = Field(
        None,
        description="Egress in GB per billing period before new egress is refused.",
        title="Egress Gb Enforcement Limit",
    )
    enforcement_override_effective_until: date | None = Field(
        None,
        description="Last day an operator override of the enforcement limits applies; afterwards the tier values do. None when no expiry is set.",
        title="Enforcement Override Effective Until",
    )
    max_concurrent_workloads: int | None = Field(None, title="Max Concurrent Workloads")
    max_gpu_hours: float | None = Field(None, title="Max Gpu Hours")
    max_monthly_cost_usd: float | None = Field(None, title="Max Monthly Cost Usd")
    max_monthly_input_tokens: int | None = Field(
        None,
        deprecated=True,
        description="Legacy per-direction input-token figure; not enforced and not the billing basis. Use platform_token_monthly_quota. A null value does not mean token usage is unlimited or free.",
        title="Max Monthly Input Tokens",
    )
    max_monthly_output_tokens: int | None = Field(
        None,
        deprecated=True,
        description="Legacy per-direction output-token figure; not enforced and not the billing basis. Use platform_token_monthly_quota. A null value does not mean token usage is unlimited or free.",
        title="Max Monthly Output Tokens",
    )
    platform_token_enforcement_limit: int | None = Field(
        None,
        description="Platform tokens per billing period before new work is refused.",
        title="Platform Token Enforcement Limit",
    )
    platform_token_monthly_quota: int | None = Field(
        None,
        description="Platform tokens, input and output combined, included per billing period before overage is billed. This is the token figure billing uses. 0 means every token is billed as overage; null means unlimited.",
        title="Platform Token Monthly Quota",
    )
    storage_gb_enforcement_limit: int | None = Field(
        None,
        description="Storage in GB before new writes are refused.",
        title="Storage Gb Enforcement Limit",
    )


class OrganizationRead(BaseModel):
    """
    The caller's organization.

    Note: ``user_role`` is optional rather than required: reading the organization
    returns it, updating the organization does not, and declaring it required
    would advertise a field the update response never carries.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    billing_channel: str | None = Field(None, title="Billing Channel")
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str = Field(..., title="Created By User Id")
    execution_locked: bool | None = Field(False, title="Execution Locked")
    id: str = Field(..., title="Id")
    logo_url: str | None = Field(None, title="Logo Url")
    member_count: int | None = Field(None, title="Member Count")
    name: str = Field(..., title="Name")
    status: str = Field(..., title="Status")
    subscription_count: int | None = Field(None, title="Subscription Count")
    updated_at: str = Field(..., title="Updated At")
    user_role: str | None = Field(
        None,
        description="The caller's role. Present on read, absent on update.",
        title="User Role",
    )


class OrganizationUpdateName(RootModel[str]):
    root: str = Field(..., max_length=255, min_length=1, title="Name")


class OrganizationUpdate(BaseModel):
    """
    Body for ``PATCH /v1/organization``.

    Deliberately narrow. ``status``, ``execution_locked`` and ``billing_channel``
    are operator-controlled and are not writable from the tenant plane.

    Forbidding costs forward-compatibility on this one write path, which is the
    right trade for a tenant surface onto an operator-owned resource: a caller
    who names a field they may not write gets a 422 that says so, rather than a
    200 that may or may not have applied it.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    description: str | None = Field(None, title="Description")
    employee_count_range: str | None = Field(None, title="Employee Count Range")
    industry: str | None = Field(None, title="Industry")
    name: OrganizationUpdateName | None = Field(None, title="Name")
    website: str | None = Field(None, title="Website")


class PaginatedFileList(BaseModel):
    """
    A page of file-manager entries.
    """

    items: list[FileEntryRead] = Field(..., title="Items")
    page: int = Field(..., title="Page")
    page_size: int = Field(..., title="Page Size")
    total: int = Field(..., title="Total")
    total_pages: int = Field(..., title="Total Pages")


class PaginatedItemsResponse(BaseModel):
    """
    A list response: the returned items plus the full-collection total.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    items: list[dict[str, Any]] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class PiiConfig(BaseModel):
    """
    The feature views marked as carrying personally identifiable information.

    `pii_features` is a flat list of `view_name__feature_name` strings.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    pii_features: list[str] | None = Field([], title="Pii Features")


class PredictionLogRead(BaseModel):
    """
    One logged prediction.

    Only prediction metadata is retained; the model input and the prediction
    payload are not.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    correlation_id: str | None = Field(None, title="Correlation Id")
    created_at: str | None = Field(None, title="Created At")
    family_id: str | None = Field(None, title="Family Id")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    latency_ms: float | None = Field(None, title="Latency Ms")
    model_id: str | None = Field(None, title="Model Id")
    served_by: str | None = Field(None, title="Served By")


class PredictionLoggingConfig(BaseModel):
    """
    Prediction-log retention and sampling for an intelligence.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    aggregate_to_daily: bool | None = Field(True, title="Aggregate To Daily")
    aggregate_to_hourly: bool | None = Field(True, title="Aggregate To Hourly")
    created_at: str | None = Field(None, title="Created At")
    error_retention_days: int | None = Field(90, title="Error Retention Days")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    retention_days: int | None = Field(30, title="Retention Days")
    sampling_enabled: bool | None = Field(False, title="Sampling Enabled")
    sampling_rate: float | None = Field(1.0, title="Sampling Rate")
    updated_at: str | None = Field(None, title="Updated At")


class PredictionLoggingConfigWrite(BaseModel):
    """
    New prediction-log retention and sampling settings.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    aggregate_to_daily: bool | None = Field(True, title="Aggregate To Daily")
    aggregate_to_hourly: bool | None = Field(True, title="Aggregate To Hourly")
    error_retention_days: int | None = Field(
        90, ge=1, le=365, title="Error Retention Days"
    )
    retention_days: int | None = Field(30, ge=1, le=365, title="Retention Days")
    sampling_enabled: bool | None = Field(False, title="Sampling Enabled")
    sampling_rate: float | None = Field(1.0, ge=0.0, le=1.0, title="Sampling Rate")
