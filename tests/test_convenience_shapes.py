"""Request-shape assertions across every namespace.

Every wrapper that takes a body forwards its JSON body verbatim, and every wrapper
that accepts ``**params`` forwards them as the query string.
"""

from __future__ import annotations

import json

import httpx
import pytest

from tests.conftest import json_handler, make_client
from tests.fixtures_body_cases import BODY_CASES


def _body(req):
    return json.loads(req.content) if req.content else None


def _shape_aware_handler(request):
    payloads = {
        "/v1/billing/costs": {"items": [], "total": 0},
        "/v1/billing/nodepool-costs": [],
    }
    return httpx.Response(200, json=payloads.get(request.url.path, {}))


# (lambda client: call-with-probe-body, method, path, probe) — the body carries
# {"probe": "<namespace>.<method>"} and must round-trip to the wire unchanged.


@pytest.mark.parametrize("call,method,path,probe", BODY_CASES)
def test_body_forwarded_verbatim(call, method, path, probe):
    client, rec = make_client(json_handler({}))
    call(client)
    assert rec.last.method == method
    assert rec.last.url.path == path
    assert _body(rec.last) == {"probe": probe}


# (lambda client: call-with-probe_key, method, path) — a **params kwarg must
# surface as a query parameter on the request URL.
QUERY_CASES = [
    (
        lambda c: c.billing.component_costs_by_capability("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/component-costs/capability/x0",
    ),
    (
        lambda c: c.billing.component_costs_by_component("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/component-costs/component/x0",
    ),
    (lambda c: c.billing.cost_report(probe_key="probe_val"), "GET", "/v1/billing/cost-report"),
    (
        lambda c: c.billing.cost_report_capabilities(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/capabilities",
    ),
    (
        lambda c: c.billing.cost_report_capability("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/capability/x0",
    ),
    (
        lambda c: c.billing.cost_report_component("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/component/x0",
    ),
    (
        lambda c: c.billing.cost_report_components(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/components",
    ),
    (
        lambda c: c.billing.cost_report_csv(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/csv",
    ),
    (
        lambda c: c.billing.cost_report_experiment("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/experiment/x0",
    ),
    (
        lambda c: c.billing.cost_report_experiments(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/experiments",
    ),
    (
        lambda c: c.billing.cost_report_infrastructure(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/infrastructure",
    ),
    (
        lambda c: c.billing.cost_report_intelligence("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/intelligence/x0",
    ),
    (
        lambda c: c.billing.cost_report_intelligences(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/intelligences",
    ),
    (
        lambda c: c.billing.cost_report_orchestration("x0", probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/orchestration/x0",
    ),
    (
        lambda c: c.billing.cost_report_orchestrations(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/orchestrations",
    ),
    (
        lambda c: c.billing.cost_report_summary(probe_key="probe_val"),
        "GET",
        "/v1/billing/cost-report/summary",
    ),
    (lambda c: c.billing.costs(probe_key="probe_val"), "GET", "/v1/billing/costs"),
    (
        lambda c: c.billing.egress_usage(probe_key="probe_val"),
        "GET",
        "/v1/billing/egress-usage",
    ),
    (lambda c: c.billing.estimates(probe_key="probe_val"), "GET", "/v1/billing/estimates"),
    (
        lambda c: c.billing.experiment_usage(probe_key="probe_val"),
        "GET",
        "/v1/billing/experiment-usage",
    ),
    (lambda c: c.billing.exports(probe_key="probe_val"), "GET", "/v1/billing/exports"),
    (
        lambda c: c.billing.infrastructure_costs(probe_key="probe_val"),
        "GET",
        "/v1/billing/infrastructure-costs",
    ),
    (
        lambda c: c.billing.intelligence_snapshots(probe_key="probe_val"),
        "GET",
        "/v1/billing/intelligence-snapshots",
    ),
    (
        lambda c: c.billing.intelligence_usage(probe_key="probe_val"),
        "GET",
        "/v1/billing/intelligence-usage",
    ),
    (lambda c: c.billing.invoices(probe_key="probe_val"), "GET", "/v1/billing/invoices"),
    (
        lambda c: c.billing.nodepool_costs(probe_key="probe_val"),
        "GET",
        "/v1/billing/nodepool-costs",
    ),
    (
        lambda c: c.billing.orchestration_usage(probe_key="probe_val"),
        "GET",
        "/v1/billing/orchestration-usage",
    ),
    (
        lambda c: c.billing.organization_costs(probe_key="probe_val"),
        "GET",
        "/v1/cost-entries/organization",
    ),
    (
        lambda c: c.billing.resource_breakdown(probe_key="probe_val"),
        "GET",
        "/v1/billing/resource-breakdown",
    ),
    (lambda c: c.billing.summary(probe_key="probe_val"), "GET", "/v1/billing/summary"),
    (
        lambda c: c.billing.transactions(probe_key="probe_val"),
        "GET",
        "/v1/billing/transactions",
    ),
    (
        lambda c: c.billing.unified_cost(probe_key="probe_val"),
        "GET",
        "/v1/billing/unified-cost",
    ),
    (lambda c: c.billing.usage(probe_key="probe_val"), "GET", "/v1/billing/usage"),
    (
        lambda c: c.billing.usage_breakdown(probe_key="probe_val"),
        "GET",
        "/v1/billing/usage/breakdown",
    ),
    (
        lambda c: c.billing.usage_summary(probe_key="probe_val"),
        "GET",
        "/v1/billing/usage-summary",
    ),
    (lambda c: c.threads.list(probe_key="probe_val"), "GET", "/v1/threads"),
    (lambda c: c.threads.search("x0", probe_key="probe_val"), "GET", "/v1/threads/search"),
    (
        lambda c: c.threads.list_messages("x0", probe_key="probe_val"),
        "GET",
        "/v1/threads/x0/messages",
    ),
    (lambda c: c.reviews.list(probe_key="probe_val"), "GET", "/v1/reviews"),
    (lambda c: c.support.list(probe_key="probe_val"), "GET", "/v1/support/tickets"),
]


@pytest.mark.parametrize("call,method,path", QUERY_CASES)
def test_query_params_forwarded(call, method, path):
    client, rec = make_client(_shape_aware_handler)
    call(client)
    assert rec.last.method == method
    assert rec.last.url.path == path
    assert dict(rec.last.url.params).get("probe_key") == "probe_val"


def test_no_content_returns_none():
    def handler(request):
        return httpx.Response(204)

    client, _ = make_client(handler)
    assert client.orchestrations.delete("orch_1") is None
