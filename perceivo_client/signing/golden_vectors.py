"""The golden-vector table for ``v1`` request signing, shipped as package data.

The table lists requests with the canonical request and signature each must
produce. Any signer or verifier, in any language, can check itself against it.
Read it with :func:`load_golden_vectors`, which resolves the packaged file through
:mod:`importlib.resources` and works from a source checkout, an installed wheel or
a zip import::

    from perceivo_client.signing import load_golden_vectors

    table = load_golden_vectors()
    for vector in table["vectors"]:
        ...  # reproduce vector["canonical_request"] and vector["signature"]

The table contains these lists; ``table["vector_counts"]`` gives their sizes:

* ``vectors``: requests to reproduce, with their canonical request and signature.
* ``negative_vectors``: canonical requests whose MAC is correct but which a
  verifier must reject, because a bound field is wrong or fields are missing.
  ``refused_by`` names the check that rejects each one.
* ``unsignable_vectors``: header values a signer must refuse to sign.
* ``secret_transport_vectors``: how an issued secret becomes the HMAC key. The
  64-hex-character secret is decoded to 32 bytes, not encoded as UTF-8.

The test secret
===============
``table["secret_utf8"]`` and ``table["secret_transport"]["disclosure_secret_hex"]``
are published test constants. They protect nothing and must never be configured
as a signing secret anywhere. The signatures in the table cannot be recomputed
without them.

Stability
=========
The inputs, canonical requests and signatures in the table define the wire format
and do not change within ``v1``. Descriptive text in the table may change between
releases, so :func:`golden_vectors_bytes` identifies the exact file rather than
the wire format.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

__all__ = ["golden_vectors_bytes", "load_golden_vectors"]

#: Package-relative location of the table. Read it through the functions below.
_RESOURCE_PACKAGE = "perceivo_client.signing"
_RESOURCE_DIRECTORY = "vectors"
_RESOURCE_NAME = "hmac_v1_vectors.json"


@lru_cache(maxsize=1)
def _read_bytes() -> bytes:
    """Read the packaged table once.

    The cache holds immutable bytes rather than the parsed table, so no caller can
    modify another caller's copy.
    """
    resource = files(_RESOURCE_PACKAGE).joinpath(_RESOURCE_DIRECTORY, _RESOURCE_NAME)
    return resource.read_bytes()


def golden_vectors_bytes() -> bytes:
    """Return the packaged table's exact bytes.

    ``hashlib.sha256(golden_vectors_bytes()).hexdigest()`` identifies the exact
    file an implementation was validated against.
    """
    return _read_bytes()


def load_golden_vectors() -> dict[str, Any]:
    """Return the parsed golden-vector table.

    Each call returns a new object, which the caller may modify.
    """
    return json.loads(_read_bytes())
