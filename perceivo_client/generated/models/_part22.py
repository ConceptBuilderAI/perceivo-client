# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 4cb0cc1fb62e540b6329e643c14e3ed2ef7982f14766508c71bd02701feb1b21

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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
