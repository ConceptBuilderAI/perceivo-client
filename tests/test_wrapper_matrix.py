"""Method and path matrix for every convenience wrapper.

One row per public wrapper method: call it with placeholder arguments and assert
the HTTP method and URL path it produced.
"""

from __future__ import annotations

import httpx
import pytest

from tests.conftest import make_client
from tests.fixtures_wrapper_cases import CASES, B


def _shape_aware_handler(request):
    payloads = {
        f"{B}/billing/costs": {"items": [], "total": 0},
        f"{B}/billing/nodepool-costs": [],
        f"{B}/billing/costs/x0": [],
        f"{B}/capabilities": [],
        f"{B}/components": [],
        # files.list_entries validates its envelope at the client boundary, so the
        # shape-aware default `{}` is not a valid body for this path.
        f"{B}/files/spaces/x0/entries": {"items": []},
    }
    return httpx.Response(200, json=payloads.get(request.url.path, {}))


# (lambda client: call, expected_method, expected_path). Grouped by namespace,
# alphabetical; every public wrapper method is present once.


@pytest.mark.parametrize("call,method,path", CASES)
def test_wrapper_targets_correct_endpoint(call, method, path):
    client, rec = make_client(_shape_aware_handler)
    call(client)
    assert rec.last.method == method
    assert rec.last.url.path == path
