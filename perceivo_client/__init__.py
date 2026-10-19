"""The Python client for the Perceivo REST API."""

from __future__ import annotations

# Imported for its side effect: keeps secret fields out of model repr()/str().
from perceivo_client import _redaction
from perceivo_client._version import __version__
from perceivo_client.async_client import AsyncClient
from perceivo_client.auth import (
    AmbiguousCredentialsError,
    APICredentials,
    BearerCredentials,
    MissingCredentialsError,
    resolve_bearer_credentials,
    resolve_credentials,
)
from perceivo_client.client import Client
from perceivo_client.errors import (
    PerceivoAPIError,
    PerceivoAuthError,
    PerceivoConflictError,
    PerceivoConnectionError,
    PerceivoError,
    PerceivoExecutionLockedError,
    PerceivoGrantError,
    PerceivoNotFoundError,
    PerceivoRateLimitError,
    PerceivoServerError,
    PerceivoValidationError,
)
from perceivo_client.generated import models
from perceivo_client.pagination import paginate, paginate_pages
from perceivo_client.ratelimit import RateLimitInfo
from perceivo_client.resources.capabilities import (
    EvaluationRun,
    EvaluationRunPage,
    EvaluationRunStatus,
)
from perceivo_client.resources.reviews import ReviewCompletion
from perceivo_client.resources.runs import RunLogPage
from perceivo_client.signing import (
    RequestSigner,
    SignedRequest,
    SigningCredentials,
    SigningError,
    build_canonical_request,
    generate_nonce,
    load_golden_vectors,
    resolve_signing_credentials,
    sign_request,
    verify_signature,
)
from perceivo_client.typed import parse
from perceivo_client.webhooks import compute_webhook_signature, verify_webhook

__all__ = [
    "APICredentials",
    "AmbiguousCredentialsError",
    "AsyncClient",
    "BearerCredentials",
    "Client",
    "EvaluationRun",
    "EvaluationRunPage",
    "EvaluationRunStatus",
    "MissingCredentialsError",
    "PerceivoAPIError",
    "PerceivoAuthError",
    "PerceivoConflictError",
    "PerceivoConnectionError",
    "PerceivoError",
    "PerceivoExecutionLockedError",
    "PerceivoGrantError",
    "PerceivoNotFoundError",
    "PerceivoRateLimitError",
    "PerceivoServerError",
    "PerceivoValidationError",
    "RateLimitInfo",
    "RequestSigner",
    "ReviewCompletion",
    "RunLogPage",
    "SignedRequest",
    "SigningCredentials",
    "SigningError",
    "__version__",
    "build_canonical_request",
    "compute_webhook_signature",
    "generate_nonce",
    "load_golden_vectors",
    "models",
    "paginate",
    "paginate_pages",
    "parse",
    "resolve_bearer_credentials",
    "resolve_credentials",
    "resolve_signing_credentials",
    "sign_request",
    "verify_signature",
    "verify_webhook",
]
