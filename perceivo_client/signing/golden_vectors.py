"""The golden-vector table for ``v1`` request signing, shipped as package data.

Each entry gives a request with the canonical request and signature it must
produce; ``table["secret_utf8"]`` is a published test constant that must not be
used as a real signing secret.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

__all__ = ["golden_vectors_bytes", "load_golden_vectors"]

_RESOURCE_PACKAGE = "perceivo_client.signing"
_RESOURCE_DIRECTORY = "vectors"
_RESOURCE_NAME = "hmac_v1_vectors.json"


@lru_cache(maxsize=1)
def _read_bytes() -> bytes:
    """Read the packaged table once; the cache holds immutable bytes."""
    resource = files(_RESOURCE_PACKAGE).joinpath(_RESOURCE_DIRECTORY, _RESOURCE_NAME)
    return resource.read_bytes()


def golden_vectors_bytes() -> bytes:
    """Return the packaged table's bytes.

    ``hashlib.sha256(golden_vectors_bytes()).hexdigest()`` identifies the file an
    implementation was validated against.
    """
    return _read_bytes()


def load_golden_vectors() -> dict[str, Any]:
    """Return the parsed golden-vector table.

    Each call returns a new object, which the caller may modify.
    """
    return json.loads(_read_bytes())
