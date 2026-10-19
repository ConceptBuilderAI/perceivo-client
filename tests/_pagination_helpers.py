"""Mock handlers shared by the pagination test modules."""

from __future__ import annotations

import httpx


def _paged_handler(pages):
    """Return a handler that serves successive JSON pages by request order."""
    state = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        i = state["i"]
        state["i"] = min(i + 1, len(pages) - 1)
        return httpx.Response(200, json=pages[i])

    return handler
