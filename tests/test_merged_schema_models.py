"""Wrapper models preserve the merged API's actual response envelopes."""

from __future__ import annotations

import pytest

from perceivo_client.generated.models import (
    PaginatedItemsResponse,
    UsageBreakdownResponse,
    UsageMetricsResponse,
)
from tests.conftest import json_handler, make_client


@pytest.mark.parametrize("namespace", ["orchestrations", "intelligence", "reviews"])
def test_list_wrappers_use_items_total_model(namespace):
    payload = {"items": [{"id": "example"}], "total": 1}
    client, recorder = make_client(json_handler(payload))
    with client:
        result = getattr(client, namespace).list(page=1, page_size=25)
    assert type(result) is PaginatedItemsResponse
    assert result.model_dump() == payload
    assert recorder.last.url.path == f"/v1/{namespace}"


@pytest.mark.parametrize(
    "method,model,payload",
    [
        ("usage", UsageMetricsResponse, {"summary": {"tokens": 7}, "time_series": []}),
        (
            "usage_breakdown",
            UsageBreakdownResponse,
            {"organization_id": "org-example", "redis": {"bytes": 42}},
        ),
    ],
)
def test_billing_usage_wrappers_use_their_distinct_models(method, model, payload):
    client, _ = make_client(json_handler(payload))
    with client:
        result = getattr(client.billing, method)()
    assert type(result) is model
    assert result.model_dump(exclude_unset=True) == payload
