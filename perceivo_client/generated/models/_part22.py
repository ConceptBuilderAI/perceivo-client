# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 3d2e3229cf0345c18b422900b349f609addd473ac07f1b9df7959452816c96c3

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class TrainingGroupDetail(BaseModel):
    """
    A training group and the configurations it contains.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str | None = Field(None, title="Created At")
    created_by_user_sub: str | None = Field(None, title="Created By User Sub")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    intelligence_id: str = Field(..., title="Intelligence Id")
    is_default: bool | None = Field(False, title="Is Default")
    member_count: int | None = Field(0, title="Member Count")
    members: list[TrainingGroupMemberRead] | None = Field(
        [], title="Members", validate_default=True
    )
    name: str = Field(..., title="Name")
    updated_at: str | None = Field(None, title="Updated At")


class ValidationCheck(BaseModel):
    """
    One validation finding.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    category: str | None = Field(
        None, description="The family of check that produced it.", title="Category"
    )
    id: str | None = Field(
        None, description="Stable identifier for this check.", title="Id"
    )
    location: ValidationLocation | None = Field(
        None,
        description="Where in the script the finding applies, when it is positional.",
    )
    message: str | None = Field(
        None, description="What is wrong and why.", title="Message"
    )
    severity: str | None = Field(
        None,
        description="How serious the finding is: `error`, `warning` or `info`.",
        title="Severity",
    )
    suggestion: str | None = Field(
        None, description="How to resolve the finding.", title="Suggestion"
    )
    title: str | None = Field(
        None, description="Short summary of the finding.", title="Title"
    )


class ComponentExportDocument(BaseModel):
    """
    A self-contained export of one component, accepted unchanged by import.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    component: ComponentTransferData
    export_type: Literal["component"] = Field("component", title="Export Type")
    export_version: str | None = Field("1.0", title="Export Version")
    exported_at: AwareDatetime = Field(..., title="Exported At")


class ComponentImportBody(BaseModel):
    """
    A component export document to import into your organization.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    component: ComponentTransferData = Field(
        ..., description="The exported component, unchanged from the export document."
    )
    export_type: Literal["component"] = Field(
        "component",
        description="Only a component export can be imported here.",
        title="Export Type",
    )
    export_version: str | None = Field(
        "1.0",
        description="The export format version, as the export document gives it.",
        title="Export Version",
    )
    exported_at: AwareDatetime | None = Field(
        None,
        description="When the export was made, as the export document gives it.",
        title="Exported At",
    )
    new_name: str | None = Field(
        None,
        description="A name for the imported component, in place of the exported one.",
        title="New Name",
    )


class ComponentValidationReport(BaseModel):
    """
    The result of validating a component definition.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    checks: list[ValidationCheck] | None = Field(
        None, description="Every finding, in the order produced.", title="Checks"
    )
    derived_contract: dict[str, Any] | None = Field(
        None,
        description="The contract this validation ran against: the `contract` you supplied, or, when you supplied none, the `contract` block read from `manifest_yaml`. It is not inferred from your code.",
        title="Derived Contract",
    )
    runtime_observations: RuntimeObservations | None = Field(
        None,
        description="What static analysis of the script found. The script is not run.",
    )
    summary: ValidationSummary | None = Field(
        None, description="Finding counts by severity."
    )
    valid: bool | None = Field(
        None, description="Whether the definition would be accepted.", title="Valid"
    )


class IntelligenceTrafficPlanApply(BaseModel):
    """
    Apply a traffic plan to this intelligence.
    """

    source: Source = Field(..., title="Source")
    source_id: str | None = Field(
        None,
        description="The evaluation or history entry this plan came from",
        title="Source Id",
    )
    traffic_plan: IntelligenceTrafficPlanSpec
