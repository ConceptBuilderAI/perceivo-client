"""``files.list_entries`` and ``files.list_trash``: the ``PaginatedFileList`` page.

Both answer ``items``, ``total``, ``page``, ``page_size`` and ``total_pages``.
The page is validated into :class:`PaginatedFileList`, so each item is a typed
:class:`FileEntryRead`, from the sync client and its thread-backed async twin,
and ``paginate_pages`` walks either one bound to its space.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio
import functools
import uuid

import httpx
import pytest

from perceivo_client import AsyncClient, paginate_pages
from perceivo_client.generated.models import FileEntryRead, PaginatedFileList
from tests.conftest import BASE_URL, json_handler, make_client

_SPACE = "space-1"
_SPACE_ID = "7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e0001"
_USER_ID = "7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e0002"


def _entry(n: int) -> dict:
    return {
        "id": f"7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e1{n:03d}",
        "storage_space_id": _SPACE_ID,
        "name": f"file-{n}.csv",
        "path": f"/file-{n}.csv",
        "entry_type": "file",
        "is_starred": False,
        "is_trashed": False,
        "created_at": "2026-10-03T00:00:00Z",
        "updated_at": "2026-10-03T00:00:00Z",
        "created_by_user_id": _USER_ID,
        "updated_by_user_id": _USER_ID,
    }


def _page(items: list[dict], *, total: int, page: int = 1, page_size: int = 50) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size),
    }


def _async_client(payload) -> AsyncClient:
    """An AsyncClient whose HTTP layer always serves ``payload``."""
    return AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(
            base_url=BASE_URL,
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)),
        ),
    )


@pytest.mark.parametrize(
    "call,path",
    [
        (lambda c: c.files.list_entries(_SPACE), f"/v1/files/spaces/{_SPACE}/entries"),
        (lambda c: c.files.list_trash(_SPACE), f"/v1/files/spaces/{_SPACE}/trash"),
    ],
    ids=["entries", "trash"],
)
def test_a_page_is_validated_into_typed_entries(call, path):
    client, recorder = make_client(json_handler(_page([_entry(1), _entry(2)], total=2)))

    page = call(client)

    assert isinstance(page, PaginatedFileList)
    assert (page.total, page.page, page.total_pages) == (2, 1, 1)
    assert all(isinstance(item, FileEntryRead) for item in page.items)
    assert [item.name for item in page.items] == ["file-1.csv", "file-2.csv"]
    assert page.items[0].storage_space_id == uuid.UUID(_SPACE_ID)
    assert recorder.last.url.path == path


def test_an_empty_page_has_no_items():
    client, _ = make_client(json_handler(_page([], total=0)))

    page = client.files.list_entries(_SPACE)

    assert (page.items, page.total) == ([], 0)


def test_the_async_client_returns_the_same_typed_page():
    page = asyncio.run(_async_client(_page([_entry(1)], total=1)).files.list_entries(_SPACE))

    assert isinstance(page, PaginatedFileList)
    assert [item.name for item in page.items] == ["file-1.csv"]


def test_list_entries_sends_each_filter_under_its_query_name():
    client, recorder = make_client(json_handler(_page([], total=0)))

    client.files.list_entries(
        _SPACE,
        parent_id="folder-1",
        include_trashed=True,
        starred_only=False,
        sort_by="updated_at",
        sort_order="desc",
        page=2,
        page_size=100,
    )

    assert dict(recorder.last.url.params) == {
        "parent_id": "folder-1",
        "include_trashed": "true",
        "starred_only": "false",
        "sort_by": "updated_at",
        "sort_order": "desc",
        "page": "2",
        "page_size": "100",
    }


def test_list_entries_search_mode_sends_query_and_its_filters_only():
    client, recorder = make_client(json_handler(_page([], total=0)))

    client.files.list_entries(_SPACE, query="report", entry_type="file", mime_type="text/csv")

    assert dict(recorder.last.url.params) == {
        "query": "report",
        "entry_type": "file",
        "mime_type": "text/csv",
    }


def test_list_entries_without_arguments_sends_no_query():
    client, recorder = make_client(json_handler(_page([], total=0)))

    client.files.list_entries(_SPACE)

    assert recorder.last.url.query == b""


@pytest.mark.parametrize("method", ["list_entries", "list_trash"])
def test_paginate_pages_walks_a_bound_file_listing(method):
    entries = [_entry(n) for n in range(5)]

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        size = int(request.url.params["page_size"])
        chunk = entries[(page - 1) * size : page * size]
        return httpx.Response(200, json=_page(chunk, total=len(entries), page=page, page_size=size))

    client, recorder = make_client(handler)
    fetch = functools.partial(getattr(client.files, method), _SPACE)

    walked = list(paginate_pages(fetch, page_size=2))

    assert [item["name"] for item in walked] == [f"file-{n}.csv" for n in range(5)]
    assert [r.url.params["page"] for r in recorder.requests] == ["1", "2", "3"]
