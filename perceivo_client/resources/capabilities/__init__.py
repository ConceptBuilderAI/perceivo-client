"""Capabilities namespace (``client.capabilities``).

A capability serves its inputs through member orchestrations under a traffic
plan. This namespace covers the capability record and its versions, running
and restarting it, member orchestrations, the traffic plan, evaluation and its
schedule, and execution graphs. A capability's queued inputs are in
``client.queue``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    CapabilityEvaluationConfigRead,
    CapabilityEvaluationSummaryRead,
    CapabilityRead,
    CapabilityTrafficPlanRead,
    CapabilityTriggerRead,
    CapabilityUpdateResult,
    EvaluationTriggerResponse,
    ExecutionGraphBuildResponse,
    ExecutionGraphConfigRead,
    GraphConfigBuildResponse,
    LifecycleOperationResponse,
    LineageRestoreResult,
    PaginatedItemsResponse,
    TestInvokeResponse,
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources.capabilities._common import _BASE
from perceivo_client.resources.capabilities._evaluation import _EvaluationMixin
from perceivo_client.resources.capabilities._graphs import _GraphsMixin
from perceivo_client.resources.capabilities._models import (
    EvaluationRun,
    EvaluationRunPage,
    EvaluationRunStatus,
    _update_result,
)
from perceivo_client.resources.capabilities._orchestrations import _OrchestrationsMixin
from perceivo_client.resources.capabilities._records import _RecordsMixin
from perceivo_client.resources.capabilities._traffic import _TrafficMixin


class CapabilitiesResource(
    _RecordsMixin,
    _EvaluationMixin,
    _TrafficMixin,
    _OrchestrationsMixin,
    _GraphsMixin,
    BaseResource,
):
    """Invoke capabilities and manage rollout."""
