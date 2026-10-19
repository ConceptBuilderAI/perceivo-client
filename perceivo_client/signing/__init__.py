"""HMAC-SHA256 request signing for the Perceivo API (signature version ``v1``).

The package uses only the standard library and makes no network calls. The
wire format, with a standalone example signer, is specified in
``docs/HMAC_REQUEST_SIGNING.md``.
"""

from __future__ import annotations

from perceivo_client.signing._constants import (
    AUDIENCE_LOCAL,
    AUDIENCE_PRODUCTION,
    CANONICAL_AUDIENCE_PATTERN,
    CANONICAL_DOMAIN,
    CANONICAL_FIELD_COUNT,
    CANONICAL_ORGANIZATION_PATTERN,
    EMPTY_BODY_SHA256,
    HEADER_KEY_ID,
    HEADER_NONCE,
    HEADER_ORGANIZATION,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    MAX_CLOCK_SKEW_SECONDS,
    SIGNATURE_PREFIX,
    SIGNATURE_VERSION,
    BodyType,
    ContentTypeType,
    OrganizationType,
    SecretType,
)
from perceivo_client.signing.canonical import (
    SigningError,
    body_sha256_hex,
    build_canonical_request,
    canonical_audience,
    canonical_content_type,
    canonical_key_id,
    canonical_organization,
    canonical_path,
    canonical_query,
    generate_nonce,
    split_target,
)
from perceivo_client.signing.golden_vectors import (
    golden_vectors_bytes,
    load_golden_vectors,
)
from perceivo_client.signing.signer import (
    RequestSigner,
    SignedRequest,
    SigningCredentials,
    compute_signature,
    resolve_signing_credentials,
    sign_request,
    verify_signature,
    verify_signed_request,
)

__all__ = [
    "AUDIENCE_LOCAL",
    "AUDIENCE_PRODUCTION",
    "CANONICAL_AUDIENCE_PATTERN",
    "CANONICAL_DOMAIN",
    "CANONICAL_FIELD_COUNT",
    "CANONICAL_ORGANIZATION_PATTERN",
    "EMPTY_BODY_SHA256",
    "HEADER_KEY_ID",
    "HEADER_NONCE",
    "HEADER_ORGANIZATION",
    "HEADER_SIGNATURE",
    "HEADER_TIMESTAMP",
    "MAX_CLOCK_SKEW_SECONDS",
    "SIGNATURE_PREFIX",
    "SIGNATURE_VERSION",
    "BodyType",
    "ContentTypeType",
    "OrganizationType",
    "RequestSigner",
    "SecretType",
    "SignedRequest",
    "SigningCredentials",
    "SigningError",
    "body_sha256_hex",
    "build_canonical_request",
    "canonical_audience",
    "canonical_content_type",
    "canonical_key_id",
    "canonical_organization",
    "canonical_path",
    "canonical_query",
    "compute_signature",
    "generate_nonce",
    "golden_vectors_bytes",
    "load_golden_vectors",
    "resolve_signing_credentials",
    "sign_request",
    "split_target",
    "verify_signature",
    "verify_signed_request",
]
