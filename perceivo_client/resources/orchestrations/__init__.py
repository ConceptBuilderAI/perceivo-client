"""Orchestrations namespace (``client.orchestrations``).

The orchestration lifecycle: create, read, change and delete orchestrations;
start a run; edit the graph through drafts and publish a draft as the next
version; validate a definition; assign an orchestration to a capability and
check its compatibility; copy, export and import; read the graph and the
version lineage; delete and restore versions; and read the secrets bound to
nodes.

A run, once started, is monitored on ``client.runs``.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    AssetLineageRead,
    AssignCapabilityResultRead,
    CapabilityCompatibilityRead,
    ExecuteResponseRead,
    ImportResultRead,
    NodeSecretBinding,
    NodeSecretRead,
    OrchestrationDraftPublished,
    OrchestrationDraftRead,
    OrchestrationExportRead,
    OrchestrationGraph,
    OrchestrationRead,
    OrchestrationRestoreResult,
    OrchestrationUpdateResult,
    OrchestrationValidationResult,
    PaginatedItemsResponse,
)
from perceivo_client.resources._base import BaseResource
from perceivo_client.resources.orchestrations._common import _BASE
from perceivo_client.resources.orchestrations._drafts import _DraftsMixin
from perceivo_client.resources.orchestrations._lifecycle import _LifecycleMixin
from perceivo_client.resources.orchestrations._versions import _VersionsMixin

# ``Any``, ``segment``, the models and ``_BASE`` stay importable from this module,
# as they were from the single-file module this package replaced.


class OrchestrationsResource(_LifecycleMixin, _DraftsMixin, _VersionsMixin, BaseResource):
    """Create, change, version and run orchestrations."""
