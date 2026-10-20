"""Focused fixtures for handwritten SDK response-shape contracts."""

from __future__ import annotations

import asyncio

import pytest

from perceivo_client import AsyncClient
from perceivo_client.generated.models import ComponentRead, PaginatedFileList
from tests.conftest import BASE_URL, json_handler, make_client


@pytest.mark.parametrize(
    ("call", "payload", "path"),
    [
        (
            lambda client: client.billing.nodepool_costs(),
            [{"nodepool_id": "np-1"}],
            "/v1/billing/nodepool-costs",
        ),
        (
            lambda client: client.billing.run_cost("run-1"),
            [{"amount": 3}],
            "/v1/billing/costs/run-1",
        ),
        (lambda client: client.capabilities.list(), [{"id": "cap-1"}], "/v1/capabilities"),
    ],
)
def test_bare_array_contracts_return_the_served_list(call, payload, path):
    client, recorder = make_client(json_handler(payload))

    assert call(client) == payload
    assert recorder.last.url.path == path


@pytest.mark.parametrize(
    "payload",
    [
        {"items": [{"amount": 3}], "total": 1, "has_more": True},
        {"items": [], "total": 0},
    ],
)
def test_billing_costs_preserves_its_distinct_object_envelope(payload):
    client, _recorder = make_client(json_handler(payload))

    result = client.billing.costs()

    assert result == payload
    assert result["items"] == payload["items"]
    assert result["total"] == payload["total"]
    assert "has_next" not in result


@pytest.mark.parametrize(
    "payload", [{"exports": [{"id": "export-1"}], "total": 1}, {}, {"exports": None, "total": None}]
)
def test_billing_exports_preserves_optional_and_nullable_object_fields(payload):
    client, _recorder = make_client(json_handler(payload))

    assert client.billing.exports() == payload


def test_billing_object_contracts_reject_non_objects_and_missing_cost_keys():
    client, _recorder = make_client(json_handler([]))
    with pytest.raises(ValueError, match=r"billing\.costs expected an object"):
        client.billing.costs()

    client, _recorder = make_client(json_handler({"items": []}))
    with pytest.raises(ValueError, match="requires items and total"):
        client.billing.costs()

    client, _recorder = make_client(json_handler([]))
    with pytest.raises(ValueError, match=r"billing\.exports expected an object"):
        client.billing.exports()


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.billing.nodepool_costs(),
        lambda client: client.billing.run_cost("run-1"),
    ],
)
def test_bare_list_contracts_reject_a_non_list(call):
    client, _recorder = make_client(json_handler({}))
    with pytest.raises(ValueError, match="expected a list response"):
        call(client)


def test_sync_and_thread_backed_async_share_the_billing_mapping_contracts():
    import httpx

    payloads = iter(
        [
            {"items": [{"amount": 3}], "total": 1},
            {"exports": None, "total": None},
        ]
    )
    http_client = httpx.Client(
        base_url=BASE_URL,
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=next(payloads))),
    )
    client = AsyncClient(api_key="test-key", base_url=BASE_URL, http_client=http_client)

    async def call():
        return await client.billing.costs(), await client.billing.exports()

    costs, exports = asyncio.run(call())
    assert costs == {"items": [{"amount": 3}], "total": 1}
    assert exports == {"exports": None, "total": None}


def test_all_seven_contracts_are_available_through_the_thread_backed_async_client():
    import httpx

    payloads = {
        "/v1/billing/nodepool-costs": [{"nodepool_id": "np-1"}],
        "/v1/billing/costs/run-1": [{"amount": 3}],
        "/v1/capabilities": [{"id": "cap-1"}],
        "/v1/components": [{"id": "component-1"}],
        "/v1/files/spaces/space-1/entries": {"items": [{"id": "file-1"}]},
        "/v1/billing/costs": {"items": [], "total": 0},
        "/v1/billing/exports": {"exports": [{"id": "export-1"}], "total": 1},
    }

    def handler(request):
        return httpx.Response(200, json=payloads[request.url.path])

    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)),
    )

    async def call_all():
        return (
            await client.billing.nodepool_costs(),
            await client.billing.run_cost("run-1"),
            await client.capabilities.list(),
            await client.components.list(),
            await client.files.list_entries("space-1"),
            await client.billing.costs(),
            await client.billing.exports(),
        )

    nodepools, run_cost, capabilities, components, files, costs, exports = asyncio.run(call_all())
    assert nodepools == [{"nodepool_id": "np-1"}]
    assert run_cost == [{"amount": 3}]
    assert capabilities == [{"id": "cap-1"}]
    assert [component.id for component in components] == ["component-1"]
    assert isinstance(components[0], ComponentRead)
    assert isinstance(files, PaginatedFileList)
    assert costs == {"items": [], "total": 0}
    assert exports == {"exports": [{"id": "export-1"}], "total": 1}


@pytest.mark.parametrize(
    "payload", [{"exports": [{"id": "export-1"}], "total": 1}, {}, {"exports": None, "total": None}]
)
def test_async_exports_preserves_populated_empty_and_nullable_envelopes(payload):
    import httpx

    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(
            base_url=BASE_URL,
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)),
        ),
    )
    assert asyncio.run(client.billing.exports()) == payload


@pytest.mark.parametrize(
    "call,payload",
    [
        (lambda client: client.billing.egress_usage(), {"entries": [], "summary": {}}),
        (
            lambda client: client.billing.experiment_usage(),
            {"period_start": None, "period_end": None},
        ),
        (lambda client: client.billing.intelligence_usage(), {"intelligences": [], "total": {}}),
        (
            lambda client: client.billing.orchestration_usage(),
            {"cpu_seconds": 0, "total_tokens_in": 0},
        ),
    ],
)
def test_usage_residuals_preserve_source_valid_mappings_without_a_usage_shell(call, payload):
    client, _recorder = make_client(json_handler(payload))
    assert call(client) == payload


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.billing.egress_usage(),
        lambda client: client.billing.experiment_usage(),
        lambda client: client.billing.intelligence_usage(),
        lambda client: client.billing.orchestration_usage(),
    ],
)
def test_usage_residuals_reject_non_objects(call):
    client, _recorder = make_client(json_handler([]))
    with pytest.raises(ValueError, match="expected an object response"):
        call(client)


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/v1/billing/egress-usage", {"entries": []}),
        ("/v1/billing/experiment-usage", {"period_start": None}),
        ("/v1/billing/intelligence-usage", {"intelligences": []}),
        ("/v1/billing/orchestration-usage", {"cpu_seconds": 0}),
    ],
)
def test_async_usage_residuals_preserve_source_valid_mappings(path, payload):
    import httpx

    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(
            base_url=BASE_URL,
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)),
        ),
    )
    method = {
        "/v1/billing/egress-usage": client.billing.egress_usage,
        "/v1/billing/experiment-usage": client.billing.experiment_usage,
        "/v1/billing/intelligence-usage": client.billing.intelligence_usage,
        "/v1/billing/orchestration-usage": client.billing.orchestration_usage,
    }[path]
    assert asyncio.run(method()) == payload


# This is the complete 22-wrapper residual audit from amended S04.  Bodies
# come from the corresponding API response schemas, not generic `{}` mocks.
# In particular infrastructure-costs is the source's OffsetPaginatedResponse,
# rather than the older CostReportResponse-shaped fixture.
_BILLING_RESIDUALS = [
    (
        "costs",
        lambda c: c.billing.costs(),
        {"items": [{"entry_id": "e1"}], "total": 1, "has_more": True},
        "has_more",
        True,
    ),
    (
        "exports",
        lambda c: c.billing.exports(),
        {"exports": [{"id": "export-1"}], "total": 1},
        "exports",
        [{"id": "export-1"}],
    ),
    (
        "component_costs_by_capability",
        lambda c: c.billing.component_costs_by_capability("cap-1"),
        {"entries": [{"id": "entry-1"}], "total_entry_count": 1},
        "total_entry_count",
        1,
    ),
    (
        "component_costs_by_component",
        lambda c: c.billing.component_costs_by_component("component-1"),
        {"component_id": "component-1", "by_orchestration": []},
        "by_orchestration",
        [],
    ),
    (
        "cost_report_capabilities",
        lambda c: c.billing.cost_report_capabilities(),
        {"capabilities": [{"id": "cap-1"}], "total_runs": 1},
        "capabilities",
        [{"id": "cap-1"}],
    ),
    (
        "cost_report_summary",
        lambda c: c.billing.cost_report_summary(),
        {"grand_total_usd": 1.0, "categories": {"compute": 1.0}},
        "grand_total_usd",
        1.0,
    ),
    (
        "cost_report_capability",
        lambda c: c.billing.cost_report_capability("cap-1"),
        {"children": [{"id": "child-1"}], "summary": {"cost": 1}},
        "children",
        [{"id": "child-1"}],
    ),
    (
        "cost_report_components",
        lambda c: c.billing.cost_report_components(),
        {"components": [{"id": "component-1"}]},
        "components",
        [{"id": "component-1"}],
    ),
    (
        "cost_report_component",
        lambda c: c.billing.cost_report_component("component-1"),
        {"component_name": "component-1", "orchestrations": []},
        "component_name",
        "component-1",
    ),
    (
        "cost_report_experiments",
        lambda c: c.billing.cost_report_experiments(),
        {"experiments": [{"id": "experiment-1"}]},
        "experiments",
        [{"id": "experiment-1"}],
    ),
    (
        "cost_report_experiment",
        lambda c: c.billing.cost_report_experiment("experiment-1"),
        {"experiment_name": "experiment-1", "entry_count": 1},
        "experiment_name",
        "experiment-1",
    ),
    (
        "cost_report_intelligences",
        lambda c: c.billing.cost_report_intelligences(),
        {"intelligences": [{"id": "intelligence-1"}]},
        "intelligences",
        [{"id": "intelligence-1"}],
    ),
    (
        "cost_report_intelligence",
        lambda c: c.billing.cost_report_intelligence("intelligence-1"),
        {"intelligence_name": "intelligence-1"},
        "intelligence_name",
        "intelligence-1",
    ),
    (
        "cost_report_orchestrations",
        lambda c: c.billing.cost_report_orchestrations(),
        {"orchestrations": [{"id": "orchestration-1"}]},
        "orchestrations",
        [{"id": "orchestration-1"}],
    ),
    (
        "cost_report_orchestration",
        lambda c: c.billing.cost_report_orchestration("orchestration-1"),
        {"orchestration_name": "orchestration-1"},
        "orchestration_name",
        "orchestration-1",
    ),
    (
        "cost_report_infrastructure",
        lambda c: c.billing.cost_report_infrastructure(),
        {"categories": [{"name": "compute"}], "totals": {"usd": 1}},
        "categories",
        [{"name": "compute"}],
    ),
    (
        "egress_usage",
        lambda c: c.billing.egress_usage(),
        {"entries": [{"destination": "example"}], "total_count": 1},
        "entries",
        [{"destination": "example"}],
    ),
    (
        "experiment_usage",
        lambda c: c.billing.experiment_usage(),
        {"experiments": [{"id": "experiment-1"}], "experiment_count": 1},
        "experiments",
        [{"id": "experiment-1"}],
    ),
    (
        "intelligence_usage",
        lambda c: c.billing.intelligence_usage(),
        {"intelligences": [{"id": "intelligence-1"}], "total": {"usd": 1}},
        "intelligences",
        [{"id": "intelligence-1"}],
    ),
    (
        "orchestration_usage",
        lambda c: c.billing.orchestration_usage(),
        {"cpu_hours": 1.0, "by_provider": {"fixture": 1}},
        "cpu_hours",
        1.0,
    ),
    (
        "infrastructure_costs",
        lambda c: c.billing.infrastructure_costs(),
        {
            "items": [{"resource": "compute"}],
            "total": 1,
            "limit": 25,
            "offset": 0,
            "has_more": False,
        },
        "items",
        [{"resource": "compute"}],
    ),
    (
        "intelligence_snapshots",
        lambda c: c.billing.intelligence_snapshots(),
        {"snapshots": [{"id": "snapshot-1"}], "total": 1, "limit": 25, "offset": 0},
        "snapshots",
        [{"id": "snapshot-1"}],
    ),
]


@pytest.mark.parametrize(
    "name,call,payload,attribute,expected",
    _BILLING_RESIDUALS,
    ids=[case[0] for case in _BILLING_RESIDUALS],
)
def test_source_shaped_billing_residuals_expose_all_advertised_and_required_fields(
    name, call, payload, attribute, expected
):
    """Exercise every source-advertised key and every required model field.

    Sixteen current results are permissive ``CostReportResponse`` shells with
    no declared required fields, so their model-field loop is deliberately
    empty; their source-advertised payload keys below are the meaningful check.
    The loop is still load-bearing: the four pre-B1 usage wrappers returned
    ``UsageResponse`` shells whose required ``organization_id`` was absent.
    """
    client, _recorder = make_client(json_handler(payload))

    result = call(client)
    actual = result[attribute] if isinstance(result, dict) else getattr(result, attribute)

    assert actual == expected, name
    for field_name, field_value in payload.items():
        actual = result[field_name] if isinstance(result, dict) else getattr(result, field_name)
        assert actual == field_value, f"{name}.{field_name}"

    if not isinstance(result, dict):
        required = [
            field_name
            for field_name, field in type(result).model_fields.items()
            if field.is_required()
        ]
        for field_name in required:
            getattr(result, field_name)


def test_billing_residual_matrix_keeps_all_22_reviewed_wrappers():
    assert len(_BILLING_RESIDUALS) == 22
