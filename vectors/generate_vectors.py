"""Regenerate ``hmac_v1_vectors.json``, the golden vectors for request signing.

Run from the repository root::

    python vectors/generate_vectors.py

This script is a development tool. It ships in the source distribution but is
not part of the installed package. It writes the table into the package, at
``perceivo_client/signing/vectors/hmac_v1_vectors.json``, which ships as package
data and is read with :func:`perceivo_client.signing.load_golden_vectors`.

Regenerating produces no change unless the canonicalisation rules or the
descriptive text change. The inputs, canonical requests and signatures define the
wire format: a change to any of them changes what every implementation must
produce.

``tests/test_signing_golden_signatures.py`` pins every signature in the table as
a literal, so a defect that reached both this generator and the signer would
still fail the tests.
"""

from __future__ import annotations

import base64
import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# This directory too, so the sibling modules resolve when the file is loaded with
# importlib rather than run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _cases import CASES, KEY_ID_CASES, ORGANIZATION_CASES
from _constants import (
    KEY_ID,
    NONCE,
    SECRET,
    TIMESTAMP,
)
from _invariants import assert_table_invariants
from _negative import negative_vectors_for
from _notes import NOTES
from _secret_transport import build_transport_rows, secret_transport_block
from _unsignable_cases import UNSIGNABLE_CASES, UNSIGNABLE_ORGANIZATION_CASES

from perceivo_client.signing import (
    AUDIENCE_LOCAL,
    SigningError,
    build_canonical_request,
    canonical_content_type,
    canonical_key_id,
    canonical_organization,
    canonical_path,
    compute_signature,
)


def _vector(
    vector_id: str,
    description: str,
    method: str,
    target: str,
    body: bytes | None,
    content_type: str | None,
    key_id_input: str = KEY_ID,
    audience: str = AUDIENCE_LOCAL,
    organization: str | None = None,
) -> dict:
    """Return one positive row.

    ``organization`` defaults to ``None``, meaning the request sends no
    ``Perceivo-Organization`` header, which is true of most rows. The signing API
    gives the parameter no default, so a caller always states it.
    """
    raw_path, _, query = target.partition("?")
    canonical = build_canonical_request(
        audience=audience,
        key_id=key_id_input,
        method=method,
        raw_path=raw_path,
        query_string=query,
        body=body,
        content_type=content_type,
        organization=organization,
        timestamp=TIMESTAMP,
        nonce=NONCE,
    )
    return {
        "id": vector_id,
        "description": description,
        "audience": audience,
        "key_id_input": key_id_input,
        "key_id": canonical_key_id(key_id_input),
        "method": method,
        "target": target,
        "raw_path": raw_path,
        "canonical_path": canonical_path(raw_path),
        "query_string": query,
        "body_base64": None if body is None else base64.b64encode(body).decode("ascii"),
        "content_type": content_type,
        "canonical_content_type": canonical_content_type(content_type),
        # Field 9. `organization` is the header as sent (null when absent) and
        # `canonical_organization` is the field in the canonical request (the
        # empty string when absent), as for `content_type`.
        "organization": organization,
        "canonical_organization": canonical_organization(organization),
        "timestamp": str(TIMESTAMP),
        "nonce": NONCE,
        "canonical_request": canonical,
        "signature": compute_signature(canonical, SECRET),
    }


def _unsignable_organization_vectors() -> list[dict]:
    """Return the field 9 rows a conforming signer must refuse.

    Like :func:`_unsignable_vectors`, each row has no ``canonical_request`` and no
    ``signature``. The refusal is checked here, so a row the signer accepts is
    never published as unsignable.
    """
    vectors = []
    for vector_id, description, raw, reason in UNSIGNABLE_ORGANIZATION_CASES:
        try:
            canonical_organization(raw)
        except SigningError:
            refused = True
        else:  # pragma: no cover - a generated table must never contain this
            refused = False
        if not refused:
            raise AssertionError(
                f"{vector_id} is published as unsignable but this signer accepted it"
            )
        values = raw if isinstance(raw, list) else [raw]
        vectors.append(
            {
                "id": vector_id,
                "description": description,
                "field": "organization",
                "field_number": 9,
                # Always a list, even for single values, because the duplicate
                # header row needs one and every row has the same shape.
                "organization_values_base64": [
                    base64.b64encode(value.encode("utf-8")).decode("ascii") for value in values
                ],
                "signable": False,
                "must_sign": False,
                "reason": reason,
            }
        )
    return vectors


def _unsignable_vectors() -> list[dict]:
    """Return the field 8 rows a conforming signer must refuse.

    A consumer checks these by canonicalising the input and requiring an error.
    The rows have no ``canonical_request`` and no ``signature``, because the only
    correct response to the input is a refusal.
    """
    vectors = []
    for vector_id, description, raw in UNSIGNABLE_CASES:
        try:
            canonical_content_type(raw)
        except SigningError:
            refused = True
        else:  # pragma: no cover - a generated table must never contain this
            refused = False
        if not refused:
            raise AssertionError(
                f"{vector_id} is published as unsignable but this signer accepted it"
            )
        vectors.append(
            {
                "id": vector_id,
                "description": description,
                "field": "content_type",
                "field_number": 8,
                "content_type_base64": base64.b64encode(raw).decode("ascii"),
                "signable": False,
                "must_sign": False,
                "reason": "content_type_charset",
            }
        )
    return vectors


def build() -> dict:
    """Build the complete table."""
    vectors = [_vector(*case) for case in CASES]
    vectors.extend(
        _vector(
            vector_id,
            description,
            method,
            target,
            body,
            content_type,
            key_id_input=key_id_input,
        )
        for vector_id, description, key_id_input, method, target, body, content_type in KEY_ID_CASES
    )
    vectors.extend(
        _vector(
            vector_id,
            description,
            method,
            target,
            body,
            content_type,
            organization=organization,
        )
        for vector_id, description, method, target, body, content_type, organization in ORGANIZATION_CASES
    )
    vectors.sort(key=lambda vector: vector["id"])

    primary = next(v for v in vectors if v["id"] == "v01-get-empty-body-empty-query")
    negative_vectors = negative_vectors_for(primary["canonical_request"])
    unsignable_vectors = _unsignable_vectors() + _unsignable_organization_vectors()
    secret_transport_vectors = build_transport_rows(primary, SECRET)

    assert_table_invariants(vectors, negative_vectors, unsignable_vectors)

    return {
        "schema": "perceivo.hmac-request-signing.golden-vectors/1",
        "signature_version": "v1",
        "wire_format_revision": 3,
        "algorithm": "HMAC-SHA256",
        "canonical_form": (
            "perceivo-hmac-v1\\n{audience}\\n{key_id}\\n{METHOD}\\n{canonical_path}\\n"
            "{canonical_query}\\n{sha256_hex(body)}\\n{content_type}\\n{organization}\\n"
            "{timestamp}\\n{nonce}"
        ),
        "field_count": 11,
        "audience": AUDIENCE_LOCAL,
        "key_id": KEY_ID,
        "specification": (
            "Perceivo HMAC request signing, signature version v1, as specified in "
            "the perceivo_client.signing package docstring in the perceivo-client repository. The "
            "canonical request has eleven fields; field 9 is the "
            "Perceivo-Organization header verbatim, or the empty string when the "
            "header is absent."
        ),
        "secret_utf8": SECRET,
        "secret_base64": base64.b64encode(SECRET.encode()).decode("ascii"),
        "secret_note": (
            "This key is published deliberately and protects nothing. Each row "
            "maps (audience, key_id, method, path, query, body, content_type, "
            "organization, timestamp, nonce, secret) to a signature, so the key "
            "must be included for any implementation to reproduce a row. It is a "
            "fixed test constant. Never configure it as a signing key in any "
            "environment: anyone can sign with it. Static analysis tools may "
            "report it as a stored secret; it is a public test value."
        ),
        "secret_transport": secret_transport_block(),
        "notes": NOTES,
        "generated_under": {
            "note": (
                "The environment that generated this table. The server parser "
                "contract below is declared, not measured here."
            ),
            "python": platform.python_version(),
            "generator": "perceivo-client/vectors/generate_vectors.py",
        },
        "server_parser_contract": {
            "note": (
                "The HTTP parser the server's path and query handling is specified "
                "against. Declared, not measured by this repository. If the "
                "server's parser changes, the vectors must be checked again."
            ),
            "http_parser": "httptools",
            "uvicorn": "0.35.0",
            "starlette": "unresolved from this repository",
            "fastapi": "unresolved from this repository",
        },
        # The sizes are declared so no consumer has to hardcode one, and no prose
        # in the table states one.
        "vector_counts": {
            "positive": len(vectors),
            "negative": len(negative_vectors),
            "unsignable": len(unsignable_vectors),
            "secret_transport": len(secret_transport_vectors),
        },
        "vectors": vectors,
        "negative_vectors": negative_vectors,
        "unsignable_vectors": unsignable_vectors,
        # The lists above vary the request with a fixed key; this one varies the
        # spelling of the secret with a fixed request. See `secret_transport`.
        "secret_transport_vectors": secret_transport_vectors,
    }


def main() -> None:
    # The table is package data, so it is written inside the package.
    out = (
        Path(__file__).resolve().parents[1]
        / "perceivo_client"
        / "signing"
        / "vectors"
        / "hmac_v1_vectors.json"
    )
    # Build once, so the reported sizes describe the table that was written.
    table = build()
    # newline="\n" so the file is identical on every platform.
    out.write_text(
        json.dumps(table, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"wrote {len(table['vectors'])} vectors, "
        f"{len(table['negative_vectors'])} negative vectors, "
        f"{len(table['unsignable_vectors'])} unsignable vectors and "
        f"{len(table['secret_transport_vectors'])} secret-transport vectors to {out}"
    )


if __name__ == "__main__":
    main()
