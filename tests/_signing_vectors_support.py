"""Shared table fixture, literals and helpers for the golden-vector test modules.

Not a test module — pytest does not collect ``_``-prefixed files, and nothing here
asserts anything. It exists so ``test_signing_vectors.py`` (the table itself) and
``test_signing_vector_cases.py`` (the individual canonicalization cases the table
exists to pin) share **one** set of primary-vector literals and **one** parse of
the table. Two copies of those literals would be two things that can drift apart,
which is the exact failure mode the golden-vector exercise exists to prevent.

Each test module declares its own module-scoped ``table`` fixture over
``load_table()`` rather than importing a fixture from here. Importing a fixture is
a redefinition every collected test then shadows, and the three-line declaration
keeps the *loading* shared, which is the part that could drift.
"""

from __future__ import annotations

import base64
from pathlib import Path

from perceivo_client.signing import build_canonical_request, load_golden_vectors, split_target

# The table is read through the SHIPPED accessor, never through a path. That is
# the surface a consumer uses, so it is the surface these tests must exercise —
# a test that opens the source-tree JSON would keep passing on the day the wheel
# stops carrying it, which is the exact defect the packaging move closed.
#
# The generator, by contrast, is a development script that is deliberately NOT
# packaged, so it can only be addressed by path.
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "vectors" / "generate_vectors.py"

# --- the primary test vector, pinned as literals ---------------------------
# These literals are the eleven-field wire format v1 values. A signature that
# omits canonical field 9, the organization, could be presented with a different
# organization, so the literals pin all eleven fields.
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
    # field 8 — this request carries no Content-Type
    "\n"
    # field 9 — this request carries no Perceivo-Organization (NEW in revision 3)
    "\n"
    "1767225600\n"
    "sT8kQ2vX7wLpR4nB1mZ6yH0j"
)
PRIMARY_SIGNATURE = "v1=ee71c0810679e5b5477186d4d1ca0444d7823b8be284a0a9bc4a07bd9e1ebdd8"

# The revision-2 TEN-field string for the SAME request: field 9 OMITTED rather
# than empty. It is now the downgrade an attacker tries first, and it is also
# exactly what a signer carried forward from revision 2 emits on every request.
# Kept as a literal for the reason the six-field one is.
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

# The six-field string for the SAME request. Kept as a literal because the
# downgrade is what an attacker tries first, and a test that constructs it by
# slicing the eleven-field string would go green the day the slicing is wrong.
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
        # key_id_input, NOT key_id: v28 supplies an uppercase uuid and the
        # normalisation is the thing under test. Recomputing from the already
        # normalised field would make that vector vacuous.
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
