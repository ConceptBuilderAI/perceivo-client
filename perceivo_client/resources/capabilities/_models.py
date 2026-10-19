"""The evaluation-run models and the update-result reshaping of the capabilities namespace.

Re-exported from :mod:`perceivo_client.resources.capabilities`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvaluationRun(BaseModel):
    """One stored evaluation run, as :meth:`CapabilitiesResource.list_evaluations` lists it.

    Attributes:
        id: The evaluation run; pass it to
            :meth:`CapabilitiesResource.get_evaluation` as ``evaluation_id``.
        organization_id: The organization that owns the run.
        kind: The kind of evaluation, for example ``capability_run``.
        subject_type: What was evaluated: ``capability``.
        subject_id: The capability that was evaluated.
        evaluator_asset_id: The evaluator asset, when one was used.
        status: The run's state, for example ``running``, ``completed`` or
            ``failed``.
        trigger_type: What started the run, for example ``online`` or
            ``scheduled``.
        triggered_by_user_sub: Who started it; ``system`` for a scheduled run.
        started_at: When the run started, ISO 8601.
        completed_at: When the run finished, ISO 8601, or ``None``.
        duration_ms: How long the run took, in milliseconds, or ``None``.
        recommendation: The evaluator's recommendation, or ``None``.
        summary_metrics: The run's summary metrics, or ``None``.
        config: The configuration the run used, or ``None``.
        error_message: Why the run failed, or ``None``.
        created_at: When the row was created, ISO 8601.
        updated_at: When the row last changed, ISO 8601.
    """

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    organization_id: str | None = None
    kind: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    evaluator_asset_id: str | None = None
    status: str | None = None
    trigger_type: str | None = None
    triggered_by_user_sub: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    recommendation: str | None = None
    summary_metrics: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EvaluationRunPage(BaseModel):
    """A capability's most recent evaluation runs, from :meth:`CapabilitiesResource.list_evaluations`.

    Attributes:
        items: Up to the 20 most recent runs, newest first.
        total: How many runs the capability has in all; it can be larger than
            ``len(items)``.
    """

    model_config = ConfigDict(extra="allow")

    items: list[EvaluationRun] = Field(default_factory=list)
    total: int = 0


class EvaluationRunStatus(BaseModel):
    """One evaluation run's state, as :meth:`CapabilitiesResource.get_evaluation` returns it.

    Attributes:
        evaluation_id: The evaluation run.
        capability_id: The capability it evaluates.
        organization_id: The organization that owns the run.
        status: ``queued``, ``deploying``, ``running``, ``completed`` or
            ``failed``.
        summary_metrics: The run's summary metrics, or ``None``.
        error: Why the run failed, or ``None``.
        started_at: When the run started, ISO 8601. ``None`` while the
            platform still holds the run in progress.
        completed_at: When the run finished, ISO 8601, or ``None``.
        result: The evaluator's full result. Present only while the platform
            still holds the run in progress; ``None`` once it is read from
            storage.
    """

    model_config = ConfigDict(extra="allow")

    evaluation_id: str | None = None
    capability_id: str | None = None
    organization_id: str | None = None
    status: str | None = None
    summary_metrics: dict[str, Any] | None = None
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: Any = None


def _update_result(data: Any) -> Any:
    """Bring both update answers to the ``CapabilityUpdateResult`` shape.

    An in-place update answers the capability with ``version_created``. A
    change that creates a new version answers ``{"capability": {...},
    "versioned": true, "propagation_summary": ...}`` with no top-level ``id``;
    its ``capability`` is lifted to the top level, ``version_created`` is set
    from ``versioned``, and ``propagation_summary`` is kept.
    """
    if isinstance(data, dict) and "id" not in data and isinstance(data.get("capability"), dict):
        lifted = dict(data["capability"])
        lifted["version_created"] = data.get("versioned") is True
        lifted["propagation_summary"] = data.get("propagation_summary")
        return lifted
    return data
