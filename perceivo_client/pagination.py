"""Pagination helpers for page/page-size and offset/limit list endpoints.

:func:`paginate_pages` walks an ``{"items": [...], "total": N}`` collection
by ``page``/``page_size``, which is how most list operations page.
:func:`paginate` walks one of the few ``limit``/``offset`` operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable, Iterator

from pydantic import BaseModel

from perceivo_client.generated.models import RunPage

_ITEM_KEYS = ("items", "data", "results", "records")
_PAGE_RESERVED_PARAMS = frozenset({"page", "limit", "offset"})


def page_items(page: Any) -> list[Any]:
    """Extract the item list from a raw page envelope.

    Tries the common list keys, then falls back to the sole list value in the
    dict; returns ``[]`` for an empty/unknown shape and passes a bare list
    through unchanged.
    """
    if isinstance(page, list):
        return page
    if isinstance(page, BaseModel):
        page = page.model_dump(warnings=False)
    if not isinstance(page, dict):
        return []
    for key in _ITEM_KEYS:
        value = page.get(key)
        if isinstance(value, list):
            return value
    list_values = [v for v in page.values() if isinstance(v, list)]
    if len(list_values) == 1:
        return list_values[0]
    return []


def paginate(
    fetch: Callable[..., Any],
    *,
    limit: int = 100,
    max_items: int | None = None,
    **params: Any,
) -> Iterator[Any]:
    """Yield every item across pages of an **offset/limit** list endpoint.

    Only a few list operations page by ``limit``/``offset``; among the client's
    methods they are ``client.grants.list``, ``client.query.logs`` and
    ``client.billing.organization_costs``. Most others page by
    ``page``/``page_size``: use :func:`paginate_pages` for those. Pointed at a
    page/page-size method, this helper sends parameters the operation ignores
    and either stops after the first page or never stops.

    Args:
        fetch: A ``limit``/``offset`` list method, e.g. ``client.grants.list``.
            It is called as ``fetch(limit=..., offset=..., **params)``.
        limit: Page size requested per call.
        max_items: Optional hard cap on the total number of items yielded.
        **params: Extra query parameters forwarded on every page request.

    Yields:
        Each item, in order, until a short page (fewer than ``limit`` items) is
        returned or ``max_items`` is reached.
    """
    offset = 0
    yielded = 0
    while True:
        page = fetch(limit=limit, offset=offset, **params)
        items = page_items(page)
        for item in items:
            yield item
            yielded += 1
            if max_items is not None and yielded >= max_items:
                return
        if len(items) < limit:
            return
        offset += len(items)


def _validate_page_options(
    page_size: int, max_items: int | None, params: Mapping[str, Any]
) -> None:
    reserved = sorted(_PAGE_RESERVED_PARAMS.intersection(params))
    if reserved:
        raise ValueError(
            "paginate_pages owns the reserved query parameter(s): " + ", ".join(reserved)
        )
    if isinstance(page_size, bool) or not isinstance(page_size, int):
        raise TypeError("page_size must be a non-boolean int")
    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")
    if max_items is not None:
        if isinstance(max_items, bool) or not isinstance(max_items, int):
            raise TypeError("max_items must be None or a non-boolean int")
        if max_items < 0:
            raise ValueError("max_items must be greater than or equal to 0")


class _PageWalk:
    """The state of one :func:`paginate_pages` walk, shared with the async helper.

    Each response is checked against the envelope the first page declared.
    Without ``total_pages`` every page but the last must be full, so a short or
    empty page means the collection changed during the walk. With
    ``total_pages`` the walk requests every page up to it and accepts short or
    empty pages: the API can filter a page after cutting it (``query.search``
    with ``protection``), and later pages can still hold matches.
    """

    def __init__(self, page_size: int) -> None:
        self.page_size = page_size
        self.page = 1
        self.yielded = 0
        self._total: int | None = None
        self._total_pages: int | None = None

    def accept(self, response: Any) -> tuple[list[Any], bool]:
        """Validate one page; return its items and whether it is the last."""
        if isinstance(response, RunPage):
            # ``RunPage.total`` counts the runs in the returned page, not the
            # result set. A walk driven by it stops after page one.
            raise ValueError(
                "paginate_pages refuses runs.list: its total counts only the runs in the "
                "returned page, so a walk driven by it would stop after page one. Page it "
                "yourself: pass page=1, 2, ... until a page shorter than page_size, or an "
                "empty one, comes back"
            )
        if isinstance(response, BaseModel):
            response = response.model_dump(warnings=False)
        if not isinstance(response, Mapping):
            raise ValueError("paginate_pages requires an items/total mapping envelope")

        items = response.get("items")
        total = response.get("total")
        total_pages = response.get("total_pages")
        if not isinstance(items, list):
            raise ValueError("paginate_pages requires envelope.items to be a list")
        if not _is_count(total):
            raise ValueError("paginate_pages requires envelope.total to be a non-negative int")
        if total_pages is not None and not _is_count(total_pages):
            raise ValueError(
                "paginate_pages requires envelope.total_pages to be absent or a non-negative int"
            )
        if self.page == 1:
            self._total, self._total_pages = total, total_pages
        elif (total, total_pages) != (self._total, self._total_pages):
            raise ValueError(
                "paginate_pages requires total and total_pages to remain stable across pages"
            )

        remaining = min(self.page_size, total - self.yielded)
        if total_pages is None:
            if len(items) != remaining:
                raise ValueError(
                    "paginate_pages received an early short, empty, or oversized page "
                    f"(expected {remaining} items, got {len(items)})"
                )
            last = self.yielded + len(items) == total
        else:
            if len(items) > remaining:
                raise ValueError(
                    "paginate_pages received an oversized page "
                    f"(at most {remaining} items expected, got {len(items)})"
                )
            last = self.page >= total_pages
        self.page += 1
        return items, last


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def paginate_pages(
    fetch: Callable[..., Any],
    *,
    page_size: int = 25,
    max_items: int | None = None,
    **params: Any,
) -> Iterator[Any]:
    """Yield items from an ``items,total`` page/page-size list endpoint.

    Supported wrappers, passed directly: ``orchestrations.list``,
    ``intelligence.list``, ``reviews.list``, ``query.search`` and
    ``experiments.list``. Three more answer the same ``items,total`` page but
    take a positional id, so bind it first with :func:`functools.partial`:
    ``capabilities.list_orchestrations`` (``capability_id``),
    ``files.list_entries`` and ``files.list_trash`` (``space_id``). It refuses
    ``runs.list``, whose ``total`` counts only the returned page. Any other
    wrapper is unsupported: a bare-array, cursor-paged or ``data``/``next``
    list fails the envelope check.
    It owns the page counter and calls ``fetch`` with only ``page`` and
    ``page_size`` plus the caller's non-reserved filters.

    When the page carries ``total_pages``, the walk requests every page up to
    it and accepts short or empty pages, because the API can filter a page
    after cutting it (``query.search`` with ``protection``) and later pages can
    still hold items. Without ``total_pages`` every page but the last must be
    full.

    Args:
        fetch: A supported synchronous ``list``-style method.
        page_size: Requested page size, from 1 through the API maximum of 100.
        max_items: Optional non-negative cap on items yielded.
        **params: Non-pagination query parameters forwarded on every request.

    Raises:
        TypeError: If ``page_size`` or ``max_items`` has the wrong type.
        ValueError: If options are out of range or a response violates the
            required ``items,total`` envelope and exact-page contract.
    """
    _validate_page_options(page_size, max_items, params)
    if max_items == 0:
        return

    walk = _PageWalk(page_size)
    while True:
        items, last = walk.accept(fetch(page=walk.page, page_size=page_size, **params))
        for item in items:
            yield item
            walk.yielded += 1
            if max_items is not None and walk.yielded >= max_items:
                return
        if last:
            return
