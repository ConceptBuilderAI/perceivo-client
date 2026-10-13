# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class ExperimentDeleteResponse(BaseModel):
    """
    Body for ``DELETE /v1/experiments/{id}`` — the soft-delete acknowledgement.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    experiment_id: str = Field(..., title="Experiment Id")
    status: str = Field(..., title="Status")


class ExperimentRead(BaseModel):
    """
    An experiment, as every read on this plane returns it.

    Note: Identifiers and timestamps arrive as JSON **strings**, not as native
    types.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_config: dict[str, Any] | None = Field(None, title="Compute Config")
    connection_endpoint: str | None = Field(None, title="Connection Endpoint")
    created_at: str = Field(..., title="Created At")
    deleted_at: str | None = Field(None, title="Deleted At")
    description: str | None = Field(None, title="Description")
    error_message: str | None = Field(None, title="Error Message")
    id: str = Field(..., title="Id")
    idle_warning_sent_at: str | None = Field(None, title="Idle Warning Sent At")
    kernel_id: str | None = Field(None, title="Kernel Id")
    last_activity_at: str | None = Field(None, title="Last Activity At")
    name: str = Field(..., title="Name")
    notebook_content: dict[str, Any] | None = Field(None, title="Notebook Content")
    organization_id: str = Field(..., title="Organization Id")
    started_at: str | None = Field(None, title="Started At")
    status: str = Field(..., title="Status")
    stopped_at: str | None = Field(None, title="Stopped At")
    user_id: str = Field(..., title="User Id")


class ExperimentRunResponse(BaseModel):
    """
    ``202`` body for ``POST /v1/experiments/{id}/run`` — the queued job.

    Nothing is running when this returns: the experiment moves to ``QUEUED`` and
    a worker outside the request path provisions the pod. Poll
    ``GET /v1/experiments/{id}/session`` for progress.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    experiment_id: str = Field(..., title="Experiment Id")
    job_id: str = Field(..., title="Job Id")
    position: int | None = Field(0, title="Position")
    status: str = Field(..., title="Status")


class ExperimentSession(BaseModel):
    """
    The live session of one experiment, as ``GET /v1/experiments/{id}/session``
    returns it.

    There is no session id: the session *is* the experiment row while it is up.
    ``connection_endpoint`` and ``kernel_id`` are ``null`` until the pod is
    running, which is the honest shape of a queued experiment.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    connection_endpoint: str | None = Field(None, title="Connection Endpoint")
    experiment_id: str = Field(..., title="Experiment Id")
    kernel_id: str | None = Field(None, title="Kernel Id")
    last_activity_at: str | None = Field(None, title="Last Activity At")
    started_at: str | None = Field(None, title="Started At")
    status: str = Field(..., title="Status")


class ExperimentStopResponse(BaseModel):
    """
    Body for ``POST /v1/experiments/{id}/stop`` — the requested transition.

    Idempotent: stopping an already-stopped experiment reports the state it is in
    rather than raising, so a client retrying after a timeout is not told its
    successful stop failed.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    experiment_id: str = Field(..., title="Experiment Id")
    status: str = Field(..., title="Status")


class ExperimentUpdateName(RootModel[str]):
    root: str = Field(
        ...,
        description="A name for the experiment, shown wherever the experiment is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )


class ExperimentUpdate(BaseModel):
    """
    Editable fields for an experiment. All optional — send any subset.

    Only ``name``, ``description`` and ``compute_config`` can be changed;
    runtime state (status, kernel, connection endpoint) is managed for you and
    any other field in the body is ignored.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_config: dict[str, Any] | None = Field(
        None,
        description="The resources the experiment's session is started with, such as its CPU, memory and GPU requests. It is read each time the experiment is run.",
        title="Compute Config",
    )
    description: str | None = Field(
        None,
        description="What the experiment is for, in your own words.",
        title="Description",
    )
    name: ExperimentUpdateName | None = Field(
        None,
        description="A name for the experiment, shown wherever the experiment is listed.",
        title="Name",
    )


class ExperimentUsageResponse(BaseModel):
    """
    ``GET /v1/billing/experiment-usage`` — experiment usage/cost aggregate.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    experiment_count: int | None = Field(None, title="Experiment Count")
    experiments: list[dict[str, Any]] | None = Field(None, title="Experiments")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")
    total_uptime_seconds: float | None = Field(None, title="Total Uptime Seconds")


class ExperimentsCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/experiments``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    experiments: list[dict[str, Any]] | None = Field(None, title="Experiments")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    llm_managed_cost_usd: float | None = Field(None, title="Llm Managed Cost Usd")
    llm_user_cost_usd: float | None = Field(None, title="Llm User Cost Usd")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_cu_hours: float | None = Field(None, title="Total Cu Hours")


class ExportFormat(StrEnum):
    """
    File format of the export.
    """

    azure_partner_center = "azure_partner_center"
    csv = "csv"
    json = "json"


class ExportCreate(BaseModel):
    """
    ``POST /v1/billing/exports`` — request a billing export for the key's
    own organization.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    export_format: ExportFormat = Field(
        ..., description="File format of the export.", title="Export Format"
    )
    period_end: str = Field(
        ..., description="End of the billing period, ISO 8601.", title="Period End"
    )
    period_start: str = Field(
        ..., description="Start of the billing period, ISO 8601.", title="Period Start"
    )


class ExportListResponse(BaseModel):
    """
    ``GET /v1/billing/exports`` — returns ``{exports,total}``, not the generic
    ``PaginatedResponse`` (``items/total/page/page_size/has_next``).
    """

    model_config = ConfigDict(
        extra="allow",
    )
    exports: list[dict[str, Any]] | None = Field(None, title="Exports")
    total: int | None = Field(None, title="Total")


class ExportRead(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    download_url: str | None = Field(None, title="Download Url")
    format: str | None = Field(None, title="Format")
    id: str = Field(..., title="Id")
    organization_id: str | None = Field(None, title="Organization Id")
    status: str | None = Field(None, title="Status")


class FeatureViewRead(BaseModel):
    """
    A feature view served by the intelligence's feature store.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    entities: list[str] | None = Field(None, title="Entities")
    features: list[dict[str, Any]] | None = Field(None, title="Features")
    name: str | None = Field(None, title="Name")


class FileEntryCopy(BaseModel):
    """
    Where to copy a file or folder to.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    dest_parent_id: UUID | None = Field(
        None,
        description="Destination folder; null copies to the space root",
        title="Dest Parent Id",
    )


class FileEntryMove(BaseModel):
    """
    Where to move a file or folder to.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    new_parent_id: UUID | None = Field(
        None,
        description="Destination folder; null moves the entry to the space root",
        title="New Parent Id",
    )


class FileEntryRead(BaseModel):
    """
    A file or folder entry.
    """

    blob_name: str | None = Field(None, title="Blob Name")
    created_at: AwareDatetime = Field(..., title="Created At")
    created_by_user_id: UUID = Field(..., title="Created By User Id")
    entry_type: EntryType
    id: UUID = Field(..., title="Id")
    is_starred: bool = Field(..., title="Is Starred")
    is_trashed: bool = Field(..., title="Is Trashed")
    mime_type: str | None = Field(None, title="Mime Type")
    name: str = Field(..., title="Name")
    parent_id: UUID | None = Field(None, title="Parent Id")
    path: str = Field(..., title="Path")
    size_bytes: int | None = Field(None, title="Size Bytes")
    storage_space_id: UUID = Field(..., title="Storage Space Id")
    trashed_at: AwareDatetime | None = Field(None, title="Trashed At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    updated_by_user_id: UUID = Field(..., title="Updated By User Id")


class FileEntryUpdateName(RootModel[str]):
    root: str = Field(..., description="New entry name", max_length=255, title="Name")


class FileEntryUpdate(BaseModel):
    """
    Fields to change on a file or folder. Omitted fields are left alone.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    is_starred: bool | None = Field(
        None, description="Star or unstar the entry", title="Is Starred"
    )
    name: FileEntryUpdateName | None = Field(
        None, description="New entry name", title="Name"
    )


class FileTrashRestore(BaseModel):
    """
    The trashed files and folders to restore.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    entry_ids: list[UUID] = Field(
        ...,
        description="The trashed files and folders to restore, one to a hundred",
        max_length=100,
        min_length=1,
        title="Entry Ids",
    )


class FileUploadStatus(StrEnum):
    """
    completed when the file was stored; error when it was refused
    """

    completed = "completed"
    error = "error"


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
