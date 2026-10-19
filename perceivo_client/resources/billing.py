"""Billing namespace (``client.billing``).

Cost reports, usage, subscription, and billing exports — the read surface a
customer or their agent uses to see what an organization is spending, broken
down by capability, component, orchestration, intelligence, experiment, and
infrastructure. All operations are reads except the export create.
"""

from __future__ import annotations

from typing import Any, cast

from typing_extensions import NotRequired, TypedDict

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    CostEstimate,
    CostReportResponse,
    CostSummary,
    ExportRead,
    Invoice,
    InvoiceContent,
    InvoicePage,
    SubscriptionRead,
    TransactionPage,
    UsageBreakdownResponse,
    UsageMetricsResponse,
)
from perceivo_client.resources._base import BaseResource

_BASE = "/v1/billing"


class BillingUsageEntriesPage(TypedDict):
    items: list[dict[str, Any]]
    total: int
    has_more: NotRequired[bool]


class ExportListResponse(TypedDict):
    exports: NotRequired[list[dict[str, Any]] | None]
    total: NotRequired[int | None]


def _list_response(data: Any, operation: str) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise ValueError(f"{operation} expected a list response")
    return data


def _object_response(data: Any, operation: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{operation} expected an object response")
    return data


class BillingResource(BaseResource):
    """Cost reports, usage, subscription, and exports."""

    # --- top-level cost / usage reports ---
    def costs(self, **params: Any) -> BillingUsageEntriesPage:
        data = _object_response(self._get(f"{_BASE}/costs", params=params or None), "billing.costs")
        if "items" not in data or "total" not in data:
            raise ValueError("billing.costs response requires items and total")
        return cast(BillingUsageEntriesPage, data)

    def run_cost(self, run_id: str) -> list[dict[str, Any]]:
        return _list_response(
            self._get(f"{_BASE}/costs/{segment(run_id, 'run_id')}"), "billing.run_cost"
        )

    def run_overhead(self, run_id: str) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/run-overhead/{segment(run_id, 'run_id')}")
        )

    def usage(self, **params: Any) -> UsageMetricsResponse:
        return self._model(UsageMetricsResponse, self._get(f"{_BASE}/usage", params=params or None))

    def usage_breakdown(self, **params: Any) -> UsageBreakdownResponse:
        return self._model(
            UsageBreakdownResponse, self._get(f"{_BASE}/usage/breakdown", params=params or None)
        )

    def usage_summary(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/usage-summary", params=params or None)
        )

    def summary(self, **params: Any) -> CostReportResponse:
        return self._model(CostReportResponse, self._get(f"{_BASE}/summary", params=params or None))

    def subscription(self) -> SubscriptionRead:
        return self._model(SubscriptionRead, self._get(f"{_BASE}/subscription"))

    def unified_cost(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/unified-cost", params=params or None)
        )

    def resource_breakdown(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/resource-breakdown", params=params or None)
        )

    # --- per-resource usage reports ---
    def orchestration_usage(self, **params: Any) -> dict[str, Any]:
        return _object_response(
            self._get(f"{_BASE}/orchestration-usage", params=params or None),
            "billing.orchestration_usage",
        )

    def intelligence_usage(self, **params: Any) -> dict[str, Any]:
        return _object_response(
            self._get(f"{_BASE}/intelligence-usage", params=params or None),
            "billing.intelligence_usage",
        )

    def experiment_usage(self, **params: Any) -> dict[str, Any]:
        return _object_response(
            self._get(f"{_BASE}/experiment-usage", params=params or None),
            "billing.experiment_usage",
        )

    def egress_usage(self, **params: Any) -> dict[str, Any]:
        return _object_response(
            self._get(f"{_BASE}/egress-usage", params=params or None), "billing.egress_usage"
        )

    def infrastructure_costs(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/infrastructure-costs", params=params or None)
        )

    def nodepool_costs(self, **params: Any) -> list[dict[str, Any]]:
        return _list_response(
            self._get(f"{_BASE}/nodepool-costs", params=params or None), "billing.nodepool_costs"
        )

    def intelligence_snapshots(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/intelligence-snapshots", params=params or None)
        )

    # --- component-costs ---
    def component_costs_by_capability(
        self, capability_id: str, **params: Any
    ) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/component-costs/capability/{segment(capability_id, 'capability_id')}",
                params=params or None,
            ),
        )

    def component_costs_by_component(self, component_id: str, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/component-costs/component/{segment(component_id, 'component_id')}",
                params=params or None,
            ),
        )

    # --- cost-report family ---
    def cost_report(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/cost-report", params=params or None)
        )

    def cost_report_summary(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/cost-report/summary", params=params or None)
        )

    def cost_report_csv(self, **params: Any) -> Any:
        # untyped: CSV text export, not a JSON response model
        return self._get(f"{_BASE}/cost-report/csv", params=params or None)

    def cost_report_capabilities(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(f"{_BASE}/cost-report/capabilities", params=params or None),
        )

    def cost_report_capability(self, capability_id: str, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/cost-report/capability/{segment(capability_id, 'capability_id')}",
                params=params or None,
            ),
        )

    def cost_report_components(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/cost-report/components", params=params or None)
        )

    def cost_report_component(self, component_id: str, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/cost-report/component/{segment(component_id, 'component_id')}",
                params=params or None,
            ),
        )

    def cost_report_orchestrations(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(f"{_BASE}/cost-report/orchestrations", params=params or None),
        )

    def cost_report_orchestration(self, orchestration_id: str, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/cost-report/orchestration/{segment(orchestration_id, 'orchestration_id')}",
                params=params or None,
            ),
        )

    def cost_report_intelligences(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(f"{_BASE}/cost-report/intelligences", params=params or None),
        )

    def cost_report_intelligence(self, intelligence_id: str, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/cost-report/intelligence/{segment(intelligence_id, 'intelligence_id')}",
                params=params or None,
            ),
        )

    def cost_report_experiments(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse, self._get(f"{_BASE}/cost-report/experiments", params=params or None)
        )

    def cost_report_experiment(self, experiment_id: str, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(
                f"{_BASE}/cost-report/experiment/{segment(experiment_id, 'experiment_id')}",
                params=params or None,
            ),
        )

    def cost_report_infrastructure(self, **params: Any) -> CostReportResponse:
        return self._model(
            CostReportResponse,
            self._get(f"{_BASE}/cost-report/infrastructure", params=params or None),
        )

    def organization_costs(self, **params: Any) -> CostSummary:
        """Organization-wide cost summary (``GET /cost-entries/organization``).

        Accepts ``period_start`` / ``period_end`` / ``limit`` / ``offset`` query
        params. Path is not under ``_BASE``.
        """
        return self._model(
            CostSummary, self._get("/v1/cost-entries/organization", params=params or None)
        )

    # --- invoices / transactions / estimates ---
    def estimates(self, **params: Any) -> CostEstimate:
        return self._model(CostEstimate, self._get(f"{_BASE}/estimates", params=params or None))

    def invoices(self, **params: Any) -> InvoicePage:
        return self._model(InvoicePage, self._get(f"{_BASE}/invoices", params=params or None))

    def invoice(self, invoice_id: str) -> Invoice:
        return self._model(
            Invoice, self._get(f"{_BASE}/invoices/{segment(invoice_id, 'invoice_id')}")
        )

    def invoice_content(self, invoice_id: str) -> InvoiceContent:
        return self._model(
            InvoiceContent,
            self._get(f"{_BASE}/invoices/{segment(invoice_id, 'invoice_id')}/content"),
        )

    def transactions(self, **params: Any) -> TransactionPage:
        return self._model(
            TransactionPage, self._get(f"{_BASE}/transactions", params=params or None)
        )

    # --- exports ---
    def exports(self, **params: Any) -> ExportListResponse:
        data = _object_response(
            self._get(f"{_BASE}/exports", params=params or None), "billing.exports"
        )
        return cast(ExportListResponse, data)

    def create_export(self, body: dict[str, Any]) -> ExportRead:
        return self._model(ExportRead, self._post(f"{_BASE}/exports", json=body))

    def export(self, export_id: str) -> ExportRead:
        return self._model(
            ExportRead, self._get(f"{_BASE}/exports/{segment(export_id, 'export_id')}")
        )
