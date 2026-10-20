# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class CollectionDataPage(BaseModel):
    """
    One page of records, as the store returns them.

    The records and the key they arrive under are the store's own and differ
    between stores. See `GET /v1/infrastructure/{tier}/{service}` for the
    dialect a store speaks.

    Note: Where a store reports a `total`, it may count only the records in this
    page rather than every record in the container. Do not page against it:
    request the next page until a short or empty page is returned.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class CollectionDataWrite(BaseModel):
    """
    Records to load, in the addressed store's own record format.

    Milvus takes `entities`, a list of objects. Elasticsearch takes a single
    `document` and an optional `doc_id`. See
    `GET /v1/infrastructure/{tier}/{service}` for the dialect a store speaks.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class CollectionDetail(BaseModel):
    """
    One container's definition and statistics, as the store reports them.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class CollectionList(BaseModel):
    """
    The containers a store currently holds.

    The body is the store's own; its shape differs between stores.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class CollectionQuery(BaseModel):
    """
    A query, in the addressed store's own query language.

    Milvus takes a vector search — `vector` or `entity_id`, with `top_k`,
    `filter` and `output_fields`. Elasticsearch takes a `query` string with
    `fields`, `from`, `size` and `sort`. See
    `GET /v1/infrastructure/{tier}/{service}` for the dialect a store speaks.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class CollectionQueryResult(BaseModel):
    """
    A query's matches, as the store returns them.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class CollectionWriteResult(BaseModel):
    """
    The outcome of a write, as the store reports it.
    """

    model_config = ConfigDict(
        extra="allow",
    )


class ManifestYaml(RootModel[str]):
    root: str = Field(
        ...,
        description="Base64-encoded YAML manifest. Omit to carry the component's current manifest forward unchanged; there is no way to remove a manifest through this operation.",
        max_length=200000,
        title="Manifest Yaml",
    )


class ComponentArtifactReplace(BaseModel):
    """
    A replacement script for a component, and optionally its manifest.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    manifest_yaml: ManifestYaml | None = Field(
        None,
        description="Base64-encoded YAML manifest. Omit to carry the component's current manifest forward unchanged; there is no way to remove a manifest through this operation.",
        title="Manifest Yaml",
    )
    script: str = Field(
        ...,
        description="The complete replacement script. Limited to 500,000 characters.",
        max_length=500000,
        title="Script",
    )


class ComponentCostReport(BaseModel):
    """
    ``GET /v1/billing/cost-report/component/{component_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component_id: str | None = Field(None, title="Component Id")
    component_name: str | None = Field(None, title="Component Name")
    component_type: str | None = Field(None, title="Component Type")
    orchestrations: list[dict[str, Any]] | None = Field(None, title="Orchestrations")
    organization_id: str | None = Field(None, title="Organization Id")
    period_end: str | None = Field(None, title="Period End")
    period_start: str | None = Field(None, title="Period Start")
    summary: dict[str, Any] | None = Field(None, title="Summary")


class ComponentCostsByCapabilityResponse(BaseModel):
    """
    ``GET /v1/billing/component-costs/capability/{capability_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    compute_cost_usd: float | None = Field(None, title="Compute Cost Usd")
    custom_cost_usd: float | None = Field(None, title="Custom Cost Usd")
    entries: list[dict[str, Any]] | None = Field(None, title="Entries")
    idle_cost_usd: float | None = Field(None, title="Idle Cost Usd")
    llm_cost_usd: float | None = Field(None, title="Llm Cost Usd")
    platform_cost_usd: float | None = Field(None, title="Platform Cost Usd")
    total_cost_usd: float | None = Field(None, title="Total Cost Usd")
    total_entry_count: int | None = Field(None, title="Total Entry Count")


class ComponentCostsByComponentResponse(BaseModel):
    """
    ``GET /v1/billing/component-costs/component/{component_id}``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    by_orchestration: list[dict[str, Any]] | None = Field(
        None, title="By Orchestration"
    )
    component_id: str | None = Field(None, title="Component Id")
    summary: dict[str, Any] | None = Field(None, title="Summary")


class ComponentCreateType(RootModel[str]):
    root: str = Field(..., min_length=1, title="Type")


class ComponentCreateTypeNone(RootModel[None]):
    root: None = Field(..., min_length=1, title="Type")


class ComponentCreateWithType(BaseModel):
    """
    Create a new component.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_type_input: str | None = Field(None, title="Artifact Type Input")
    artifact_type_output: str | None = Field(None, title="Artifact Type Output")
    asset_type: str | None = Field(None, title="Asset Type")
    category: str | None = Field(None, title="Category")
    component_type: str | None = Field(None, title="Component Type")
    config: dict[str, Any] | None = Field(None, title="Config")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    description: str | None = Field(None, title="Description")
    disabled: bool | None = Field(None, title="Disabled")
    fsm_states: list[dict[str, Any]] | None = Field(None, title="Fsm States")
    manifest_yaml: str | None = Field(None, title="Manifest Yaml")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    ports: list[dict[str, Any]] | None = Field(None, title="Ports")
    script: str | None = Field(None, title="Script")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")
    type: ComponentCreateType | ComponentCreateTypeNone | None = Field(
        ..., title="Type"
    )


class ComponentCreateComponentType(RootModel[str]):
    root: str = Field(..., min_length=1, title="Component Type")


class ComponentCreateComponentTypeNone(RootModel[None]):
    root: None = Field(..., min_length=1, title="Component Type")


class ComponentCreateWithComponentType(BaseModel):
    """
    Create a new component.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_type_input: str | None = Field(None, title="Artifact Type Input")
    artifact_type_output: str | None = Field(None, title="Artifact Type Output")
    asset_type: str | None = Field(None, title="Asset Type")
    category: str | None = Field(None, title="Category")
    component_type: (
        ComponentCreateComponentType | ComponentCreateComponentTypeNone | None
    ) = Field(..., title="Component Type")
    config: dict[str, Any] | None = Field(None, title="Config")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    description: str | None = Field(None, title="Description")
    disabled: bool | None = Field(None, title="Disabled")
    fsm_states: list[dict[str, Any]] | None = Field(None, title="Fsm States")
    manifest_yaml: str | None = Field(None, title="Manifest Yaml")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    ports: list[dict[str, Any]] | None = Field(None, title="Ports")
    script: str | None = Field(None, title="Script")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")
    type: str | None = Field(None, title="Type")


class ComponentCreateCategory(StrEnum):
    evaluation = "evaluation"
    feature = "feature"
    inference = "inference"
    training = "training"


class ComponentCreateCategoryNone(Enum):
    evaluation = "evaluation"
    feature = "feature"
    inference = "inference"
    training = "training"


class ComponentCreateWithCategory(BaseModel):
    """
    Create a new component.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact_type_input: str | None = Field(None, title="Artifact Type Input")
    artifact_type_output: str | None = Field(None, title="Artifact Type Output")
    asset_type: str | None = Field(None, title="Asset Type")
    category: ComponentCreateCategory | ComponentCreateCategoryNone | None = Field(
        ..., title="Category"
    )
    component_type: str | None = Field(None, title="Component Type")
    config: dict[str, Any] | None = Field(None, title="Config")
    created_by_user_id: str | None = Field(None, title="Created By User Id")
    description: str | None = Field(None, title="Description")
    disabled: bool | None = Field(None, title="Disabled")
    fsm_states: list[dict[str, Any]] | None = Field(None, title="Fsm States")
    manifest_yaml: str | None = Field(None, title="Manifest Yaml")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    ports: list[dict[str, Any]] | None = Field(None, title="Ports")
    script: str | None = Field(None, title="Script")
    short_description: str | None = Field(None, title="Short Description")
    tags: list[str] | None = Field(None, title="Tags")
    type: str | None = Field(None, title="Type")


class ComponentCreate(
    RootModel[
        ComponentCreateWithType
        | ComponentCreateWithComponentType
        | ComponentCreateWithCategory
    ]
):
    root: (
        ComponentCreateWithType
        | ComponentCreateWithComponentType
        | ComponentCreateWithCategory
    ) = Field(..., description="Create a new component.", title="ComponentCreate")


class ComponentDefinitionValidateManifestYaml(RootModel[str]):
    root: str = Field(
        ...,
        description="The component manifest, as YAML. Limited to 100,000 characters.",
        max_length=100000,
        title="Manifest Yaml",
    )


class Ports(RootModel[list[dict[str, Any]]]):
    root: list[dict[str, Any]] = Field(
        ...,
        description="Port definitions to validate the script against.",
        max_length=1000,
        title="Ports",
    )


class ValidationProfile(StrEnum):
    """
    How much to check.

    Both profiles parse the script and run the syntax, security-policy and component-interface checks in full. `full` additionally runs the checks specific to the component's type, which reconcile the script against its manifest and declared ports.

    `full` can therefore report errors that `quick` does not — a component with a missing or contradicted manifest can validate under `quick` and fail under `full`. `quick` is a faster subset, not an equivalent verdict.
    """

    quick = "quick"
    full = "full"


class ComponentDefinitionValidate(BaseModel):
    """
    An unsaved component definition to validate.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    component_type: str = Field(
        ...,
        description="The kind of component the script implements.",
        title="Component Type",
    )
    contract: dict[str, Any] | None = Field(
        None,
        description="The component's declared input and output contract.",
        title="Contract",
    )
    manifest_yaml: ComponentDefinitionValidateManifestYaml | None = Field(
        None,
        description="The component manifest, as YAML. Limited to 100,000 characters.",
        title="Manifest Yaml",
    )
    ports: Ports | None = Field(
        None,
        description="Port definitions to validate the script against.",
        title="Ports",
    )
    script: str = Field(
        ...,
        description="The component script to validate. Limited to 100,000 characters.",
        max_length=100000,
        title="Script",
    )
    validation_profile: ValidationProfile | None = Field(
        "full",
        description="How much to check.\n\nBoth profiles parse the script and run the syntax, security-policy and component-interface checks in full. `full` additionally runs the checks specific to the component's type, which reconcile the script against its manifest and declared ports.\n\n`full` can therefore report errors that `quick` does not — a component with a missing or contradicted manifest can validate under `quick` and fail under `full`. `quick` is a faster subset, not an equivalent verdict.",
        title="Validation Profile",
    )


class ComponentImportResult(BaseModel):
    """
    What an import created.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    asset_id: str | None = Field(None, title="Asset Id")
    asset_name: str = Field(..., title="Asset Name")
    component_ids: list[str] | None = Field(None, title="Component Ids")
    components_created: int | None = Field(0, title="Components Created")
    created_orchestration_ids: list[str] | None = Field(
        None, title="Created Orchestration Ids"
    )
    referenced_orchestration_ids: list[str] | None = Field(
        None, title="Referenced Orchestration Ids"
    )
    success: bool = Field(..., title="Success")
    unresolved_secrets: list[dict[str, Any]] | None = Field(
        None, title="Unresolved Secrets"
    )
    validation_warnings: list[str] | None = Field(None, title="Validation Warnings")


class ComponentPortRead(BaseModel):
    """
    Component port representation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    contract: dict[str, Any] | None = Field(None, title="Contract")
    direction: str = Field(..., title="Direction")
    id: str = Field(..., title="Id")
    key: str = Field(..., title="Key")
    label: str | None = Field(None, title="Label")
    port_type: str | None = Field(None, title="Port Type")


class ComponentRead(BaseModel):
    """
    Component resource representation.
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


class ComponentRunArtifact(BaseModel):
    """
    An artifact supplied to a component run as its input.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    data: Any = Field(None, title="Data")
    mime_type: str | None = Field(None, title="Mime Type")
    type: str | None = Field(None, title="Type")
