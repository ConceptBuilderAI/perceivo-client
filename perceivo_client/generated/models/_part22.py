# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


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
