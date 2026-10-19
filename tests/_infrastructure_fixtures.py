"""Shared constants and the routed handler of the infrastructure-services tests."""

from __future__ import annotations

import httpx

_I = "/v1/infrastructure"
_S = f"{_I}/search-index/indices"
_V = f"{_I}/vector-store/collections"
_EXPORT = b'{"id": "d1", "body": "x"}\n{"id": "d2", "body": "y"}\n'


def _routed(routes: dict[tuple[str, str], tuple[int, object]]):
    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    return handler
