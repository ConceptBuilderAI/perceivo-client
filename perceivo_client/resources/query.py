"""Query namespace (``client.query``).

The organization-wide read surface: the event feed, logs, metrics and asset
search. Time windows are passed as ``start`` and ``end`` and sent as the
``from`` and ``to`` query parameters. An argument left as ``None`` is not sent.
"""

from __future__ import annotations

from typing import Any

from perceivo_client.generated.models import AssetSearchResponse, EventPage, MetricSeries
from perceivo_client.resources._base import BaseResource

_BASE = "/v1"


class QueryResource(BaseResource):
    """Events, logs, metrics and search."""

    def events(
        self,
        *,
        event_type: str | None = None,
        start: str | None = None,
        end: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> EventPage:
        """Read the organization's event feed (``GET /events``).

        Args:
            event_type: Only events of this type (the ``filter[event_type]``
                query parameter).
            start: Earliest event time, RFC 3339 (sent as ``from``).
            end: Latest event time, RFC 3339 (sent as ``to``).
            page: Page number; the server default is ``1``.
            page_size: Events per page; the server default is ``50``.
            sort: Sort key; the server default is ``-occurred_at``.

        Returns:
            :class:`EventPage` — one page of events.

        Raises:
            PerceivoGrantError: For a key refused ``COMPLIANCE_READ``
                (``403``).
            PerceivoValidationError: For a malformed query (``422``).
            PerceivoAPIError: On any other error response, for example
                ``PerceivoServerError`` (``502``) when an upstream service fails.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "filter[event_type]": event_type,
            "from": start,
            "to": end,
            "page": page,
            "page_size": page_size,
            "sort": sort,
        }
        return self._model(EventPage, self._get(f"{_BASE}/events", params=params))

    def logs(
        self,
        scope: str,
        *,
        scope_id: str | None = None,
        channel: str | None = None,
        start: str | None = None,
        end: str | None = None,
        q: str | None = None,
        version: str | None = None,
        service_type: str | None = None,
        level: str | None = None,
        domain: str | None = None,
        severity: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None,
    ) -> dict[str, Any]:
        """Read the log lines of one run, orchestration, intelligence, capability or organization.

        Calls ``GET /logs``. Each scope accepts only some of the optional
        arguments; any other is refused with ``422`` naming what the scope
        takes.

        The body is the scope's own, returned as a ``dict``:

        * ``run``: ``{workload_id, entries, count, limit, namespace_resolved}``.
          ``namespace_resolved`` false means the run's log location could not
          be resolved, so an empty ``entries`` does not prove the run logged
          nothing. A run that has not started returns
          ``{workload_id, run_id, entries: [], count: 0}``.
        * ``orchestration``: ``{status, data: {resultType, result, stats}}``,
          each stream in ``result`` carrying ``values`` of
          ``[timestamp_ns, line]``.
        * ``intelligence``, ``capability`` and ``organization`` (``system``,
          ``error``, ``extension``): ``{items, total, pagination}``.
        * ``organization`` with ``channel="notification"``: ``{items, total,
          pagination, next_cursor, truncated}``.

        For every scope except ``run``, a failure behind the API (a missing
        privilege on the backing service, a window wider than 30 days, an
        outage) arrives as ``200``, not as an error, with a fixed empty body
        that is not always the scope's success shape:

        * ``intelligence`` and ``organization`` (every channel, including
          ``notification``): ``{"items": [], "total": 0}``, with no
          ``pagination``, ``next_cursor`` or ``truncated``.
        * ``orchestration`` and every ``capability`` channel:
          ``{"status": "success", "data": {"resultType": "streams",
          "result": [], "stats": {...}}}``, with no ``items``.

        Read the optional keys with ``dict.get``, and narrow the window and
        confirm the privilege before concluding nothing was logged.

        Args:
            scope: ``run``, ``orchestration``, ``intelligence``, ``capability``
                or ``organization``.
            scope_id: The run, orchestration, intelligence or capability id.
                Not taken for ``organization``, which is always the caller's.
            channel: The kind of line. ``run``: ``provider``,
                ``conversation``, ``conversation_input``,
                ``conversation_stream``, ``error``, ``extension``,
                ``snapshot`` or ``state_transition`` (omitted, every kind).
                ``orchestration``: ``provider``, ``conversation``, ``error``,
                ``state``, ``extension`` or ``snapshot``. ``intelligence``:
                ``error`` or ``extension``. ``capability``: ``system``,
                ``error``, ``extension`` or ``snapshot``. ``organization``:
                ``system``, ``error``, ``extension`` or ``notification``.
                Omitted, every scope but ``run`` reads ``error``.
            start: Window start, RFC 3339 (a run also accepts unix
                nanoseconds); sent as ``from``.
            end: Window end, in the same forms; sent as ``to``.
            q: Free-text search (``intelligence``, ``capability``,
                ``organization``).
            version: Exact semantic version (``intelligence``, ``capability``).
            service_type: ``training``, ``inference``, ``feature`` or
                ``manager`` (``intelligence``).
            level: ``INFO``, ``DEBUG``, ``WARNING`` or ``ERROR``
                (``intelligence`` ``extension`` only).
            domain: Notification domain (``organization`` ``notification``
                only).
            severity: Notification severities, comma-separated
                (``organization`` ``notification`` only).
            limit: Lines to return: at most 5000 for a run, 10000 for an
                orchestration, 500 for notifications and 1000 otherwise.
            offset: Notifications to skip (``organization`` ``notification``
                only).
            order: ``newest_first`` (the default) or ``oldest_first`` (``run``
                only).

        Returns:
            ``dict[str, Any]`` — the scope's body, or the empty failure body,
            as described above.

        Raises:
            PerceivoGrantError: For a key without the scope's privilege
                (``403``).
            PerceivoNotFoundError: For a run, orchestration or capability that
                is absent or belongs to another organization (``404``).
            PerceivoValidationError: For an unknown scope or channel, an
                argument the scope does not take, or a ``limit`` over the
                maximum (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "scope": scope,
            "scope_id": scope_id,
            "channel": channel,
            "from": start,
            "to": end,
            "q": q,
            "version": version,
            "service_type": service_type,
            "level": level,
            "domain": domain,
            "severity": severity,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        return self._get(f"{_BASE}/logs", params=params)

    def metrics(
        self,
        subject: str,
        subject_id: str,
        *,
        series: str | None = None,
        window: str | None = None,
        granularity: str | None = None,
        model_id: str | None = None,
        version: str | None = None,
    ) -> MetricSeries:
        """Read the metrics of a capability, intelligence or orchestration (``GET /metrics``).

        Omit ``series`` for the summary.

        Args:
            subject: ``capability``, ``intelligence`` or ``orchestration``.
            subject_id: The id of that asset.
            series: ``runs`` for a capability or orchestration;
                ``latency_p50``, ``latency_p95``, ``latency_p99``,
                ``throughput``, ``accuracy``, ``drift_score`` or ``error_rate``
                for an intelligence.
            window: ``1h``, ``6h``, ``24h``, ``7d`` or ``30d``.
            granularity: ``1m``, ``5m``, ``1h`` or ``1d`` (intelligence series
                only).
            model_id: One model (intelligence series only; not with
                ``drift_score``).
            version: Exact semantic version; omitted, every version is
                aggregated.

        Returns:
            :class:`MetricSeries`.

        Raises:
            PerceivoGrantError: For a key without the subject's read
                privilege (``403``).
            PerceivoNotFoundError: For a subject that is absent or belongs to
                another organization (``404``).
            PerceivoValidationError: For a selector value or combination that is
                not served (``422``).
            PerceivoAPIError: On any other error response, including ``400``
                for ``model_id`` with ``drift_score``.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "subject": subject,
            "subject_id": subject_id,
            "series": series,
            "window": window,
            "granularity": granularity,
            "model_id": model_id,
            "version": version,
        }
        return self._model(MetricSeries, self._get(f"{_BASE}/metrics", params=params))

    def search(
        self,
        *,
        q: str | None = None,
        asset_type: str | None = None,
        category: str | None = None,
        status: str | None = None,
        protection: str | None = None,
        deleted: bool | None = None,
        sort: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> AssetSearchResponse:
        """Search the organization's assets and the platform's shared ones (``GET /search``).

        ``protection`` is applied after the page is cut, so with it a page can
        be short, or empty, while later pages still hold matches; ``total`` and
        ``total_pages`` count matches before the filter. With ``protection``,
        request every page from 1 to ``total_pages`` instead of stopping at the
        first short page; ``paginate_pages(client.query.search, ...)`` does
        this. Without it, every page but the last is full.

        Args:
            q: Free text, matched as a case-insensitive substring of the name
                and descriptions.
            asset_type: One asset type, for example ``orchestration`` or
                ``intelligence`` (sent as ``type``).
            category: Exact category.
            status: Exact status, for example ``active``.
            protection: ``managed`` (your own assets) or ``platform`` (shared
                by the platform).
            deleted: ``True`` includes soft-deleted assets; the server default
                is ``false``.
            sort: ``name``, ``created_at``, ``updated_at``, ``type`` or
                ``status``, prefixed with ``-`` for descending; the server
                default is ``-created_at``.
            page: Page number; the server default is ``1``.
            page_size: Matches per page, 1 to 100; the server default is
                ``25``.

        Returns:
            :class:`AssetSearchResponse` — one page of matches.

        Raises:
            PerceivoValidationError: For an out-of-range ``page`` or
                ``page_size`` (``422``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        params = {
            "q": q,
            "type": asset_type,
            "category": category,
            "status": status,
            "protection": protection,
            "deleted": deleted,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }
        return self._model(AssetSearchResponse, self._get(f"{_BASE}/search", params=params))
