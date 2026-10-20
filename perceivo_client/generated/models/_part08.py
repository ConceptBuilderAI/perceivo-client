# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class FileUploadItem(BaseModel):
    """
    The outcome for one file of an upload batch, in the order it was sent.
    """

    entry: FileEntryRead | None = Field(
        None, description="The stored file entry, when status is completed"
    )
    error: str | None = Field(
        None, description="Why the file was refused", title="Error"
    )
    filename: str = Field(
        ..., description="The file name the part was sent with", title="Filename"
    )
    status: FileUploadStatus = Field(
        ...,
        description="completed when the file was stored; error when it was refused",
        title="Status",
    )


class FileVersionRead(BaseModel):
    """
    One stored version of a file entry.
    """

    blob_version_id: str | None = Field(None, title="Blob Version Id")
    checksum_md5: str | None = Field(
        None,
        description="MD5 checksum of the version's content, when recorded",
        title="Checksum Md5",
    )
    comment: str | None = Field(None, title="Comment")
    created_at: AwareDatetime = Field(..., title="Created At")
    created_by_user_id: UUID = Field(..., title="Created By User Id")
    file_entry_id: UUID = Field(..., title="File Entry Id")
    id: UUID = Field(..., title="Id")
    is_current: bool = Field(..., title="Is Current")
    size_bytes: int = Field(..., title="Size Bytes")
    version_number: int = Field(..., title="Version Number")


class DirectPrivileges(RootModel[list[str]]):
    root: list[str] = Field(
        ...,
        description="Privilege names to grant directly instead of a role. At least one.",
        min_length=1,
        title="Direct Privileges",
    )


class GrantCreateGranteeType(StrEnum):
    """
    The kind of principal that receives the grant.
    """

    user = "user"
    group = "group"
    service_account = "service_account"


class ResourceType(StrEnum):
    """
    The kind of resource the grant is on.
    """

    organization = "organization"
    asset = "asset"
    intelligence = "intelligence"
    capability = "capability"
    group = "group"
    database = "database"
    file = "file"
    folder = "folder"
    subscription = "subscription"


class GrantCreate(BaseModel):
    """
    Grant a role, or direct privileges, on one resource of your organization.

    Send exactly one of `role_id` and `direct_privileges`.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    direct_privileges: DirectPrivileges | None = Field(
        None,
        description="Privilege names to grant directly instead of a role. At least one.",
        title="Direct Privileges",
    )
    grantee_id: UUID = Field(
        ...,
        description="The user, group or service account receiving the grant.",
        title="Grantee Id",
    )
    grantee_type: GrantCreateGranteeType = Field(
        ...,
        description="The kind of principal that receives the grant.",
        title="Grantee Type",
    )
    resource_id: UUID = Field(
        ..., description="The resource the grant is on.", title="Resource Id"
    )
    resource_type: ResourceType = Field(
        ..., description="The kind of resource the grant is on.", title="Resource Type"
    )
    role_id: UUID | None = Field(
        None,
        description="A system role, or one of your organization's roles, to grant.",
        title="Role Id",
    )


class GrantGranteeType(StrEnum):
    user = "user"
    group = "group"
    service_account = "service_account"


class GrantRead(BaseModel):
    """
    One access grant: a grantee, a resource, and a role or direct privileges.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    direct_privileges: list[str] | None = Field(None, title="Direct Privileges")
    granted_at: AwareDatetime = Field(..., title="Granted At")
    granted_by_user_id: UUID | None = Field(None, title="Granted By User Id")
    grantee_id: UUID = Field(..., title="Grantee Id")
    grantee_name: str | None = Field(None, title="Grantee Name")
    grantee_type: GrantGranteeType = Field(..., title="Grantee Type")
    id: UUID = Field(..., title="Id")
    resource_id: UUID = Field(..., title="Resource Id")
    resource_name: str | None = Field(None, title="Resource Name")
    resource_type: str = Field(..., title="Resource Type")
    revoked_at: AwareDatetime | None = Field(None, title="Revoked At")
    role_id: UUID | None = Field(None, title="Role Id")
    role_name: str | None = Field(None, title="Role Name")


class GrantUpdateDirectPrivileges(RootModel[list[str]]):
    root: list[str] = Field(
        ...,
        description="The grant's complete list of direct privileges. At least one.",
        min_length=1,
        title="Direct Privileges",
    )


class GrantUpdate(BaseModel):
    """
    Change a grant. Each field sent replaces that part of the grant.

    Send at least one of `role_id` and `direct_privileges`.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    direct_privileges: GrantUpdateDirectPrivileges | None = Field(
        None,
        description="The grant's complete list of direct privileges. At least one.",
        title="Direct Privileges",
    )
    role_id: UUID | None = Field(
        None, description="The role the grant now confers.", title="Role Id"
    )


class GraphConfigBuildResponse(BaseModel):
    """
    Result of building a graph from a saved config.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    blob_path: str | None = Field(None, title="Blob Path")
    entry_count: int | None = Field(None, title="Entry Count")
    graph_id: str | None = Field(None, title="Graph Id")
    status: str | None = Field(None, title="Status")


class GroupCreate(BaseModel):
    """
    Body for ``POST /v1/groups``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(
        None, description="Free text about the group.", title="Description"
    )
    name: str = Field(
        ..., description="The group's name.", max_length=255, min_length=1, title="Name"
    )
    visibility: str | None = Field(
        None,
        description="`private` or `public`. `private` when omitted.",
        title="Visibility",
    )


class GroupMemberAddPrincipalType(StrEnum):
    """
    `user` or `service_account`; inferred when omitted.
    """

    user = "user"
    service_account = "service_account"


class Privilege(StrEnum):
    list_group = "LIST_GROUP"
    read_group = "READ_GROUP"
    list_assets = "LIST_ASSETS"
    read_assets = "READ_ASSETS"
    use_assets = "USE_ASSETS"
    copy_assets = "COPY_ASSETS"
    add_assets = "ADD_ASSETS"
    edit_group = "EDIT_GROUP"
    manage_members = "MANAGE_MEMBERS"
    admin_group = "ADMIN_GROUP"


class GroupMemberAdd(BaseModel):
    """
    Add a member of your organization to a group: a user or a service account.

    Send exactly one of `user_id` and `service_account_id`. `principal_type`, when
    sent, must name the same kind.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    principal_type: GroupMemberAddPrincipalType | None = Field(
        None,
        description="`user` or `service_account`; inferred when omitted.",
        title="Principal Type",
    )
    privileges: list[Privilege] = Field(
        ...,
        description="The member's complete set of group privileges. At least one.",
        min_length=1,
        title="Privileges",
    )
    service_account_id: UUID | None = Field(
        None, description="The service account to add.", title="Service Account Id"
    )
    user_id: UUID | None = Field(None, description="The user to add.", title="User Id")


class GroupMemberPrivileges(BaseModel):
    """
    Replace a group member's privileges with the list sent.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    privileges: list[Privilege] = Field(
        ...,
        description="The member's complete set of group privileges. At least one.",
        min_length=1,
        title="Privileges",
    )


class GroupMemberPrincipalType(StrEnum):
    user = "user"
    service_account = "service_account"


class GroupMemberRead(BaseModel):
    """
    One group membership.

    Only groups in your own organization are reachable, so every membership you
    can read belongs to a group in your organization.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    added_by_user_id: UUID = Field(..., title="Added By User Id")
    is_owner: bool | None = Field(False, title="Is Owner")
    joined_at: AwareDatetime = Field(..., title="Joined At")
    principal_type: GroupMemberPrincipalType | None = Field(
        None, title="Principal Type"
    )
    privileges: list[str] | None = Field(None, title="Privileges")
    service_account_id: UUID | None = Field(None, title="Service Account Id")
    user_email: str | None = Field(None, title="User Email")
    user_id: UUID | None = Field(None, title="User Id")
    user_name: str | None = Field(None, title="User Name")


class GroupOrganizationInfo(BaseModel):
    """
    The lightweight organization block embedded in a group body.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")


class GroupRead(BaseModel):
    """
    A group, as every group operation returns it.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str = Field(..., title="Created By User Id")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    is_default: bool | None = Field(False, title="Is Default")
    name: str = Field(..., max_length=255, title="Name")
    organization: GroupOrganizationInfo | None = None
    organization_id: str = Field(..., title="Organization Id")
    updated_at: str = Field(..., title="Updated At")
    visibility: str = Field(..., title="Visibility")


class GroupUpdateName(RootModel[str]):
    root: str = Field(
        ..., description="The new name.", max_length=255, min_length=1, title="Name"
    )


class GroupUpdate(BaseModel):
    """
    Body for ``PATCH /v1/groups/{group_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(
        None, description="The new description.", title="Description"
    )
    name: GroupUpdateName | None = Field(
        None, description="The new name.", title="Name"
    )
    visibility: str | None = Field(
        None,
        description="The new visibility. A group cannot be moved to `system`.",
        title="Visibility",
    )


class ImportResultRead(BaseModel):
    """
    Result of importing an orchestration bundle.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    asset_id: str | None = Field(None, title="Asset Id")
    asset_name: str | None = Field(None, title="Asset Name")
    component_ids: list[str] | None = Field(None, title="Component Ids")
    components_created: int | None = Field(None, title="Components Created")
    success: bool | None = Field(None, title="Success")
    unresolved_secrets: list[dict[str, Any]] | None = Field(
        None, title="Unresolved Secrets"
    )
    validation_warnings: list[str] | None = Field(None, title="Validation Warnings")


class InfraOverheadEntry(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    billing_trace_id: str | None = Field(
        None,
        description="Identifier of the billing run that wrote this row, for support correlation.",
        title="Billing Trace Id",
    )
    category: str | None = Field(
        None,
        description="Infrastructure service, e.g. `milvus`, `mcp`.",
        title="Category",
    )
    cost_usd: float | None = Field(
        None, description="Charged cost, USD.", title="Cost Usd"
    )
    cpu_seconds: float | None = Field(
        None, description="CPU seconds consumed.", title="Cpu Seconds"
    )
    cu_hours: float | None = Field(
        None, description="Compute-unit hours charged.", title="Cu Hours"
    )
    gpu_seconds: float | None = Field(
        None, description="GPU seconds consumed.", title="Gpu Seconds"
    )
    id: str = Field(..., description="Row identifier (UUID).", title="Id")
    memory_gb_seconds: float | None = Field(
        None, description="Memory GB-seconds consumed.", title="Memory Gb Seconds"
    )
    org_usage_snapshot_id: str | None = Field(
        None,
        description="The usage snapshot this row was derived from (see snapshots).",
        title="Org Usage Snapshot Id",
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
    rate_per_cu_hour_usd: float | None = Field(
        None,
        description="The per-CU-hour rate this row was priced at, USD.",
        title="Rate Per Cu Hour Usd",
    )
    rate_type: str | None = Field(
        None, description="Rate the row was priced at.", title="Rate Type"
    )


class InfraOverheadPage(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    entries: list[InfraOverheadEntry] = Field(
        ..., description="This page, newest first.", title="Entries"
    )
    total_cost_usd: float = Field(
        ...,
        description="Sum of `cost_usd` across all matching rows.",
        title="Total Cost Usd",
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
