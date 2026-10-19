"""Shared table loader, primary-vector literals and helpers for the golden-vector tests."""

from __future__ import annotations

import base64
from pathlib import Path

from perceivo_client.signing import build_canonical_request, load_golden_vectors, split_target

# The table is read through the packaged accessor; the generator is not packaged.
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "vectors" / "generate_vectors.py"

# --- the primary test vector, pinned as literals ---------------------------
PRIMARY_ID = "v01-get-empty-body-empty-query"
PRIMARY_SECRET = "perceivo-test-signing-secret-v1"
PRIMARY_AUDIENCE = "perceivo-api-local"
PRIMARY_KEY_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"
PRIMARY_METHOD = "GET"
PRIMARY_TARGET = "/v1/orchestrations"
PRIMARY_BODY = None
PRIMARY_CONTENT_TYPE = None
PRIMARY_ORGANIZATION = None
PRIMARY_TIMESTAMP = "1767225600"
PRIMARY_NONCE = "sT8kQ2vX7wLpR4nB1mZ6yH0j"
PRIMARY_CANONICAL = (
    "perceivo-hmac-v1\n"
    "perceivo-api-local\n"
    "0f8fad5b-d9cb-469f-a165-70867728950e\n"
    "GET\n"
    "/v1/orchestrations\n"
    "\n"
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n"
    # field 8: no Content-Type
    "\n"
    # field 9: no Perceivo-Organization
    "\n"
    "1767225600\n"
    "sT8kQ2vX7wLpR4nB1mZ6yH0j"
)
PRIMARY_SIGNATURE = "v1=ee71c0810679e5b5477186d4d1ca0444d7823b8be284a0a9bc4a07bd9e1ebdd8"

# The same request with field 9 omitted rather than empty, a downgrade form.
PRIMARY_TEN_FIELD_CANONICAL = (
    "perceivo-hmac-v1\n"
    "perceivo-api-local\n"
    "0f8fad5b-d9cb-469f-a165-70867728950e\n"
    "GET\n"
    "/v1/orchestrations\n"
    "\n"
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n"
    "\n"
    "1767225600\n"
    "sT8kQ2vX7wLpR4nB1mZ6yH0j"
)

# The six-field downgrade form of the same request.
PRIMARY_SIX_FIELD_CANONICAL = (
    "GET\n"
    "/v1/orchestrations\n"
    "\n"
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n"
    "1767225600\n"
    "sT8kQ2vX7wLpR4nB1mZ6yH0j"
)


def load_table() -> dict:
    return load_golden_vectors()


def canonical_for(vector: dict) -> str:
    raw_path, query = split_target(vector["target"])
    body = None if vector["body_base64"] is None else base64.b64decode(vector["body_base64"])
    return build_canonical_request(
        audience=vector["audience"],
        # key_id_input: key-id normalisation is part of what the vectors test.
        key_id=vector["key_id_input"],
        method=vector["method"],
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=vector["content_type"],
        organization=vector["organization"],
        timestamp=vector["timestamp"],
        nonce=vector["nonce"],
    )


def find(table: dict, vector_id: str) -> dict:
    return next(v for v in table["vectors"] if v["id"] == vector_id)
