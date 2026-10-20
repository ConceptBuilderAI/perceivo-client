"""Intelligence namespace (``client.intelligence``).

The machine-learning lifecycle of an intelligence: create, read, change and
delete it; start, stop and read its serving runtime; predict, singly and in
batches; read inference requests and prediction logs; train, evaluate,
register, promote and retire models; manage model families, traffic plans,
drift baselines and drift configuration; export, import and version it;
manage training configurations and groups; read feature views, materialize and
ingest; configure PII and prediction logging; bind service secrets; and manage
ingest triggers.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    BatchPredictionResponse,
    DriftBaselineRead,
    DriftConfig,
    EvaluationRead,
    FeatureViewRead,
    IngestResponse,
    IngestTriggerRead,
    IntelligenceExport,
    IntelligenceImportResult,
    IntelligenceMaterializeAccepted,
    IntelligenceRead,
    IntelligenceTrafficPlanResult,
    IntelligenceTrainingJobRead,
    IntelligenceTriggerExecutionRead,
    IntelligenceUpdateResult,
    LineageRestoreResult,
    ModelFamilyRead,
    ModelLifecycleResult,
    ModelPromotionResult,
    ModelRead,
    PaginatedItemsResponse,
    PiiConfig,
    PredictionLoggingConfig,
    PredictionLogRead,
    PredictionOutcomes,
    PredictionPage,
    PredictionRecord,
    PredictionResponse,
    ServiceSecretRead,
    TrainingConfigurationRead,
    TrainingGroupDetail,
    TrainingGroupMemberRead,
    TrainingGroupRead,
    TrainingJobSubmitResponse,
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources.intelligence._common import _BASE
from perceivo_client.resources.intelligence._config import _ConfigMixin
from perceivo_client.resources.intelligence._features import _FeaturesMixin
from perceivo_client.resources.intelligence._lifecycle import _LifecycleMixin
from perceivo_client.resources.intelligence._models import _ModelsMixin
from perceivo_client.resources.intelligence._serving import _ServingMixin
from perceivo_client.resources.intelligence._training import _TrainingMixin

# ``Any``, ``segment``, the models and ``_BASE`` stay importable from this module,
# as they were from the single-file module this package replaced.


class IntelligenceResource(
    _LifecycleMixin,
    _ServingMixin,
    _ModelsMixin,
    _ConfigMixin,
    _TrainingMixin,
    _FeaturesMixin,
    BaseResource,
):
    """Train, serve, and manage intelligence assets.

    In the method summaries below, a path that starts with ``...`` is relative
    to ``/intelligence/{intelligence_id}``.
    """
