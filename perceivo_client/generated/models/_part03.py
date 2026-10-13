# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class CapabilityTriggerUpdate(BaseModel):
    """
    The fields of a capability's trigger to change.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    cron_expression: str | None = Field(
        None,
        description="A cron expression, evaluated in UTC. It must parse; an expression that does not is refused rather than stored.",
        title="Cron Expression",
    )
    enabled: bool | None = Field(
        None, description="Whether the schedule fires.", title="Enabled"
    )


class CapabilityUpdate(BaseModel):
    """
    Update a capability (all fields optional).
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
    name: str | None = Field(None, title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    short_description: str | None = Field(None, title="Short Description")
    start_component_id: str | None = Field(None, title="Start Component Id")
    tags: list[str] | None = Field(None, title="Tags")


class CapabilityUpdateResult(BaseModel):
    """
    The capability after an update.
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
    version_created: bool = Field(
        ...,
        description="`true` when the update produced a new asset — a new version — and `id` is that new asset's identifier; `false` when the asset was updated in place. Follow `id` either way.",
        title="Version Created",
    )


class CapacityRead(BaseModel):
    """
    This organization's compute quota and what it is currently consuming.

    `*_limit` is the ceiling the subscription allows, `*_in_use` is what running
    and idle workloads currently hold, and `*_available` is the difference.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    gpu_available: int | None = Field(None, title="Gpu Available")
    gpu_in_use: int | None = Field(None, title="Gpu In Use")
    gpu_limit: int | None = Field(None, title="Gpu Limit")
    memory_gb_available: float | None = Field(None, title="Memory Gb Available")
    memory_gb_in_use: float | None = Field(None, title="Memory Gb In Use")
    memory_gb_limit: float | None = Field(None, title="Memory Gb Limit")
    nodepool_type: str | None = Field(
        None,
        description="'default_cpu', 'default_gpu', or 'dedicated'",
        title="Nodepool Type",
    )
    organization_id: str | None = Field(None, title="Organization Id")
    vcpu_available: float | None = Field(None, title="Vcpu Available")
    vcpu_in_use: float | None = Field(None, title="Vcpu In Use")
    vcpu_limit: float | None = Field(None, title="Vcpu Limit")


class GranteeType(StrEnum):
    """
    The kind of principal the change is for.
    """

    user = "user"
    group = "group"
    service_account = "service_account"


class CascadeApplyOperation(StrEnum):
    """
    Whether access is granted or revoked.
    """

    grant = "grant"
    revoke = "revoke"


class CascadeApplyPrivilege(RootModel[str]):
    root: str = Field(
        ...,
        description="One privilege name. The only form a revoke takes.",
        max_length=128,
        min_length=1,
        title="Privilege",
    )


class CascadeApplyPrivilegesItem(RootModel[str]):
    root: str = Field(..., max_length=128, min_length=1)


class Privileges(RootModel[list[CascadeApplyPrivilegesItem]]):
    root: list[CascadeApplyPrivilegesItem] = Field(
        ...,
        description="Privilege names written as one direct grant. Grant only.",
        min_length=1,
        title="Privileges",
    )


class ResourceKind(StrEnum):
    """
    Whether the resource is an asset or a capability.
    """

    asset = "asset"
    capability = "capability"


class CascadeApply(BaseModel):
    """
    Apply a previewed change set, confirmed by its fingerprint.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    all_versions: bool | None = Field(
        False,
        description="Revoke across every version of the resource. Valid on a revoke only.",
        title="All Versions",
    )
    fingerprint: str = Field(
        ...,
        description="The `fingerprint` of the change set this call confirms.",
        max_length=64,
        min_length=64,
        title="Fingerprint",
    )
    grantee_id: UUID = Field(
        ...,
        description="The user, group or service account the change is for.",
        title="Grantee Id",
    )
    grantee_type: GranteeType = Field(
        ...,
        description="The kind of principal the change is for.",
        title="Grantee Type",
    )
    operation: CascadeApplyOperation = Field(
        ..., description="Whether access is granted or revoked.", title="Operation"
    )
    privilege: CascadeApplyPrivilege | None = Field(
        None,
        description="One privilege name. The only form a revoke takes.",
        title="Privilege",
    )
    privileges: Privileges | None = Field(
        None,
        description="Privilege names written as one direct grant. Grant only.",
        title="Privileges",
    )
    reason: str | None = Field(
        "",
        description="Recorded on every grant this change ends.",
        max_length=500,
        title="Reason",
    )
    replaces_grant_id: UUID | None = Field(
        None,
        description="The grantee's existing grant on this resource, ended in the same change. Grant only, with `role_id` or `privileges`.",
        title="Replaces Grant Id",
    )
    resource_id: UUID = Field(
        ...,
        description="The asset or capability the change starts from.",
        title="Resource Id",
    )
    resource_kind: ResourceKind | None = Field(
        "asset",
        description="Whether the resource is an asset or a capability.",
        title="Resource Kind",
    )
    role_id: UUID | None = Field(
        None, description="A role to grant. Grant only.", title="Role Id"
    )


class CascadeApplyResultOperation(StrEnum):
    grant = "grant"
    revoke = "revoke"


class CascadeOperationOperation(StrEnum):
    """
    Whether access is granted or revoked.
    """

    grant = "grant"
    revoke = "revoke"


class CascadeOperationPrivilege(RootModel[str]):
    root: str = Field(
        ...,
        description="One privilege name. The only form a revoke takes.",
        max_length=128,
        min_length=1,
        title="Privilege",
    )


class CascadeOperationPrivilegesItem(RootModel[str]):
    root: str = Field(..., max_length=128, min_length=1)


class CascadeOperationPrivileges(RootModel[list[CascadeOperationPrivilegesItem]]):
    root: list[CascadeOperationPrivilegesItem] = Field(
        ...,
        description="Privilege names written as one direct grant. Grant only.",
        min_length=1,
        title="Privileges",
    )


class CascadeOperation(BaseModel):
    """
    A grant or revoke on one asset or capability, to be previewed as a change set.

    Send exactly one of `privilege`, `privileges` and `role_id`. A revoke takes
    `privilege` only.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    all_versions: bool | None = Field(
        False,
        description="Revoke across every version of the resource. Valid on a revoke only.",
        title="All Versions",
    )
    grantee_id: UUID = Field(
        ...,
        description="The user, group or service account the change is for.",
        title="Grantee Id",
    )
    grantee_type: GranteeType = Field(
        ...,
        description="The kind of principal the change is for.",
        title="Grantee Type",
    )
    operation: CascadeOperationOperation = Field(
        ..., description="Whether access is granted or revoked.", title="Operation"
    )
    privilege: CascadeOperationPrivilege | None = Field(
        None,
        description="One privilege name. The only form a revoke takes.",
        title="Privilege",
    )
    privileges: CascadeOperationPrivileges | None = Field(
        None,
        description="Privilege names written as one direct grant. Grant only.",
        title="Privileges",
    )
    replaces_grant_id: UUID | None = Field(
        None,
        description="The grantee's existing grant on this resource, ended in the same change. Grant only, with `role_id` or `privileges`.",
        title="Replaces Grant Id",
    )
    resource_id: UUID = Field(
        ...,
        description="The asset or capability the change starts from.",
        title="Resource Id",
    )
    resource_kind: ResourceKind | None = Field(
        "asset",
        description="Whether the resource is an asset or a capability.",
        title="Resource Kind",
    )
    role_id: UUID | None = Field(
        None, description="A role to grant. Grant only.", title="Role Id"
    )


class ChangeSetOperation(StrEnum):
    grant = "grant"
    revoke = "revoke"


class ChangeSet(BaseModel):
    """
    Every grant or revoke row one operation would write, and why.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    affected: list[dict[str, Any]] | None = Field(None, title="Affected")
    blocked: list[dict[str, Any]] | None = Field(None, title="Blocked")
    derived: list[dict[str, Any]] | None = Field(None, title="Derived")
    fingerprint: str = Field(..., max_length=64, min_length=64, title="Fingerprint")
    group_sourced: list[dict[str, Any]] | None = Field(None, title="Group Sourced")
    missing: list[dict[str, Any]] | None = Field(None, title="Missing")
    operation: ChangeSetOperation = Field(..., title="Operation")
    principal: dict[str, str] = Field(..., title="Principal")
    privilege: str | None = Field(
        None,
        description="The single privilege; absent for the list and role forms.",
        title="Privilege",
    )
    privileges: list[str] | None = Field(None, title="Privileges")
    refused: bool = Field(..., title="Refused")
    replaces_grant_id: UUID | None = Field(None, title="Replaces Grant Id")
    requires_confirmation: bool = Field(..., title="Requires Confirmation")
    role_id: UUID | None = Field(None, title="Role Id")
    root: dict[str, Any] = Field(..., title="Root")
    warnings: list[str] | None = Field(None, title="Warnings")


class CpuMillicores(RootModel[int]):
    root: int = Field(..., ge=250, le=4000, title="Cpu Millicores")


class MaxReplicas(RootModel[int]):
    root: int = Field(..., ge=1, le=10, title="Max Replicas")


class MemoryMb(RootModel[int]):
    root: int = Field(..., ge=256, le=8192, title="Memory Mb")


class MinReplicas(RootModel[int]):
    root: int = Field(..., ge=1, le=10, title="Min Replicas")


class StorageGb(RootModel[int]):
    root: int = Field(..., ge=1, le=100, title="Storage Gb")


class ClusterServiceConfiguration(BaseModel):
    """
    Configuration to apply to one in-cluster service.

    Every field is optional; only the fields present in the request are
    changed. Fields are named without a service prefix — send `size`, not
    `redis_size`.

    Not every service accepts every field. `mode` applies to the cache only,
    `storage_gb` to Milvus and Elasticsearch only, and the MCP server accepts
    only `auto_shutdown` and `idle_timeout_minutes`. A field the addressed
    service does not accept is refused with `422` and named in the response.

    Several services require a resource change to be made while the service is
    stopped; the platform refuses the change otherwise.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    auto_shutdown: bool | None = Field(None, title="Auto Shutdown")
    autoscale: bool | None = Field(None, title="Autoscale")
    cpu_limit: str | None = Field(None, title="Cpu Limit")
    cpu_millicores: CpuMillicores | None = Field(None, title="Cpu Millicores")
    cpu_request: str | None = Field(None, title="Cpu Request")
    idle_timeout_minutes: int | None = Field(None, title="Idle Timeout Minutes")
    max_replicas: MaxReplicas | None = Field(None, title="Max Replicas")
    memory_limit: str | None = Field(None, title="Memory Limit")
    memory_mb: MemoryMb | None = Field(None, title="Memory Mb")
    memory_request: str | None = Field(None, title="Memory Request")
    min_replicas: MinReplicas | None = Field(None, title="Min Replicas")
    mode: str | None = Field(
        None, description="The cache only: in_cluster or azure_managed.", title="Mode"
    )
    nodepool_id: str | None = Field(None, title="Nodepool Id")
    size: str | None = Field(None, title="Size")
    storage_gb: StorageGb | None = Field(None, title="Storage Gb")


class ClusterServiceStatus(BaseModel):
    """
    One in-cluster service: its name, its status, and its own configuration.

    The remaining keys are the backing service's own, and they are
    service-prefixed: an Elasticsearch record carries `elasticsearch_size` and
    `elasticsearch_host`, a cache record carries `redis_size` and `redis_mode`.
    They are passed through exactly as the platform reports them.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    service: str = Field(
        ...,
        description="The service name, as used in the request path.",
        title="Service",
    )
    status: str | None = Field(
        None,
        description="Lifecycle state: stopped, starting, running or stopping.",
        title="Status",
    )


class ClusterServiceStatusList(BaseModel):
    """
    Every in-cluster service the organization can operate, with its status.
    """

    items: list[ClusterServiceStatus] = Field(..., title="Items")
    total: int = Field(..., title="Total")


class CollectionCreate(BaseModel):
    """
    A new container.

    `name` is required. Every other field is the store's own definition
    language — a Milvus `schema` and `index`, an Elasticsearch `mappings` and
    `settings` — and is passed to the store unchanged. See
    `GET /v1/infrastructure/{tier}/{service}` for the dialect a store speaks.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    name: str = Field(
        ...,
        description="Name of the container.",
        max_length=255,
        min_length=1,
        title="Name",
    )
