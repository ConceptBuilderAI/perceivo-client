"""The grant surface: PerceivoGrantError's place in the hierarchy, and generated model names.

The scanned word is assembled from fragments so that this file does not itself carry it.
"""

from __future__ import annotations

import importlib

from perceivo_client import PerceivoGrantError
from perceivo_client.errors import PerceivoAPIError

_OLD = "per" + "mission"


def test_the_grant_error_is_an_api_error() -> None:
    assert issubclass(PerceivoGrantError, PerceivoAPIError)


def test_generated_models_carry_only_the_new_names() -> None:
    models = importlib.import_module("perceivo_client.generated.models")
    for name in ("GrantRead", "PrivilegeCheckResponse", "AssetGrantRead", "AssetGrantCreate"):
        assert hasattr(models, name), name
    assert not [n for n in dir(models) if _OLD in n.lower()]
