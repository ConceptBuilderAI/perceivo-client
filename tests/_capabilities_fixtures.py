"""Shared constants and the routed handler of the capabilities, assets and experiments tests."""

from __future__ import annotations

import httpx

_K = "/v1/capabilities"
_A = "/v1/assets"
_E = "/v1/experiments"
_EXPERIMENT = {
    "id": "exp-1",
    "name": "notebook",
    "organization_id": "org-1",
    "user_id": "u1",
    "status": "DRAFT",
    "created_at": "2026-10-03T00:00:00Z",
}
_TRIGGER = {
    "id": "trg-1",
    "trigger_type": "cron",
    "cron_expression": "0 * * * *",
    "timezone": "UTC",
    "enabled": True,
}
_BUNDLE = {"export_type": "component", "component": {"name": "scorer", "script": "x = 1"}}


def _routed(routes: dict[tuple[str, str], tuple[int, object]]):
    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    return handler


_EXPERIMENT_ROUTES = {
    ("POST", _E): (201, _EXPERIMENT),
    ("POST", f"{_E}/exp-1/run"): (
        202,
        {"experiment_id": "exp-1", "status": "QUEUED", "job_id": "job-1"},
    ),
    ("GET", f"{_E}/exp-1/session"): (200, {"experiment_id": "exp-1", "status": "QUEUED"}),
}
