"""``paginate_pages`` over pages that declare ``total_pages``.

``query.search`` with ``protection`` filters each page after the API has cut
it, so a page can be short or empty while later pages still hold matches;
``total`` and ``total_pages`` count the matches before the filter. A walk that
stopped at the first short page would miss them, so with ``total_pages`` the
helper requests every page up to it. Without ``total_pages`` a short page still
means the collection changed, and the walk refuses it.

No network and no credentials: every case drives an ``httpx.MockTransport``.
"""

from __future__ import annotations

import asyncio
import functools

import httpx
import pytest

from perceivo_client import AsyncClient, paginate_pages
from tests.conftest import BASE_URL, RequestRecorder, make_client

_SPACE = "space-1"


def _row(n: int) -> dict:
    return {
        "id": f"asset-{n}",
        "name": f"asset {n}",
        "organization_id": "org-1",
        "ownership": "platform",
        "protection": "platform",
        "status": "active",
        "type": "component",
    }


def _search_page(rows: list[int], *, total: int, total_pages: int | None, page_size: int = 3):
    body = {"items": [_row(n) for n in rows], "total": total, "page_size": page_size}
    if total_pages is not None:
        body["total_pages"] = total_pages
    return body


def _pages_handler(pages: list[dict]):
    """Serve ``pages[page - 1]`` for the requested ``page``; a page past the end is a 500."""

    def _handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        if page > len(pages):
            return httpx.Response(500, json={"error": "page beyond the fixture"})
        return httpx.Response(200, json=pages[page - 1])

    return _handler


#: Nine matches before the filter, three pages of three; the filter left two,
#: none and one: an empty page sits between two pages that hold matches.
_FILTERED = [
    _search_page([1, 2], total=9, total_pages=3),
    _search_page([], total=9, total_pages=3),
    _search_page([7], total=9, total_pages=3),
]


def test_a_filtered_search_is_walked_to_total_pages_past_an_empty_page():
    client, rec = make_client(_pages_handler(_FILTERED))
    names = [
        row["name"]
        for row in paginate_pages(client.query.search, page_size=3, protection="platform")
    ]
    assert names == ["asset 1", "asset 2", "asset 7"]
    assert [r.url.params["page"] for r in rec.requests] == ["1", "2", "3"]


def test_the_walk_stops_at_total_pages_without_requesting_another_page():
    pages = [_search_page([1], total=4, total_pages=2), _search_page([3], total=4, total_pages=2)]
    client, rec = make_client(_pages_handler(pages))
    got = list(paginate_pages(client.query.search, page_size=3))
    assert len(got) == 2
    assert len(rec.requests) == 2


def test_the_async_walk_is_driven_by_total_pages_too():
    recorder = RequestRecorder(_pages_handler(_FILTERED))
    client = AsyncClient(
        api_key="test-key",
        base_url=BASE_URL,
        http_client=httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recorder)),
    )

    async def _walk() -> list[str]:
        return [
            row["name"]
            async for row in client.paginate_pages(
                client.query.search, page_size=3, protection="platform"
            )
        ]

    assert asyncio.run(_walk()) == ["asset 1", "asset 2", "asset 7"]
    assert len(recorder.requests) == 3


def test_without_total_pages_an_early_short_page_is_still_refused():
    pages = [
        _search_page([1, 2], total=9, total_pages=None),
        _search_page([4, 5, 6], total=9, total_pages=None),
    ]
    client, _ = make_client(_pages_handler(pages))
    walk = paginate_pages(client.query.search, page_size=3)
    with pytest.raises(ValueError, match="early short"):
        list(walk)


def test_a_page_larger_than_the_page_size_is_refused_with_total_pages():
    pages = [_search_page([1, 2, 3, 4], total=9, total_pages=3)]
    client, _ = make_client(_pages_handler(pages))
    walk = paginate_pages(client.query.search, page_size=3)
    with pytest.raises(ValueError, match="oversized"):
        list(walk)


def test_a_total_pages_that_changes_during_the_walk_is_refused():
    pages = [
        _search_page([1, 2, 3], total=9, total_pages=3),
        _search_page([], total=9, total_pages=4),
    ]
    client, _ = make_client(_pages_handler(pages))
    walk = paginate_pages(client.query.search, page_size=3)
    with pytest.raises(ValueError, match="stable across pages"):
        list(walk)


@pytest.mark.parametrize("total_pages", [True, -1, "3"])
def test_a_total_pages_that_is_not_a_count_is_refused(total_pages):
    page = {"items": [], "total": 0, "total_pages": total_pages}
    client, _ = make_client(_pages_handler([page]))
    walk = paginate_pages(client.reviews.list, page_size=3)
    with pytest.raises(ValueError, match="total_pages"):
        list(walk)


def _entry(n: int) -> dict:
    return {
        "id": f"7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e1{n:03d}",
        "storage_space_id": "7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e0001",
        "name": f"file-{n}.csv",
        "path": f"/file-{n}.csv",
        "entry_type": "file",
        "is_starred": False,
        "is_trashed": False,
        "created_at": "2026-10-03T00:00:00Z",
        "updated_at": "2026-10-03T00:00:00Z",
        "created_by_user_id": "7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e0002",
        "updated_by_user_id": "7a3d0c55-6b2f-4f0e-9a51-0c6f2b1e0002",
    }


def test_files_list_entries_is_walked_bound_to_its_space():
    pages = [
        {"items": [_entry(1), _entry(2)], "total": 3, "page": 1, "page_size": 2, "total_pages": 2},
        {"items": [_entry(3)], "total": 3, "page": 2, "page_size": 2, "total_pages": 2},
    ]
    client, rec = make_client(_pages_handler(pages))
    fetch = functools.partial(client.files.list_entries, _SPACE)
    names = [entry["name"] for entry in paginate_pages(fetch, page_size=2, query="file")]
    assert names == ["file-1.csv", "file-2.csv", "file-3.csv"]
    assert [dict(r.url.params) for r in rec.requests] == [
        {"query": "file", "page": "1", "page_size": "2"},
        {"query": "file", "page": "2", "page_size": "2"},
    ]
    assert {r.url.path for r in rec.requests} == {f"/v1/files/spaces/{_SPACE}/entries"}
