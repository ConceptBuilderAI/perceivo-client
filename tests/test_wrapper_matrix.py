"""Exhaustive method+path matrix for every convenience wrapper.

REGENERATED (not hand-maintained). One row per public wrapper method on every
registered namespace: call it with placeholder args, then assert the HTTP method
and URL path it produced against the served /v1 surface. ``test_spec_conformance``
(G-18) closes the loop by validating every row against ``openapi/openapi-v1.json``.

To regenerate after a wrapper change: rebuild from the live client + vendored spec
(introspect each namespace method, capture method+path). Do not hand-edit rows.
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
# alphabetical; every public wrapper method is present exactly once.


@pytest.mark.parametrize("call,method,path", CASES)
def test_wrapper_targets_correct_endpoint(call, method, path):
    client, rec = make_client(_shape_aware_handler)
    call(client)
    assert rec.last.method == method
    assert rec.last.url.path == path
