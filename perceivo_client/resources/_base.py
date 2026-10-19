"""Base class for convenience resource namespaces."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from perceivo_client._transport import Transport

_M = TypeVar("_M", bound=BaseModel)


def _coerce(model: type[_M], obj: dict) -> _M:
    """Validate ``obj`` into ``model``; on a validation miss, fall back to
    ``model_construct`` so a response that omits a nominally-required field yields
    a best-effort typed object instead of crashing the caller. Most models are
    ``extra="allow"``, so unmodeled keys survive either path; a model the contract
    closes (``additionalProperties: false``, e.g. ``SecretRead``) is
    ``extra="forbid"`` and drops them."""
    try:
        return model.model_validate(obj)
    except ValidationError:
        return model.model_construct(**obj)


class BaseResource:
    """Shared request helpers for a domain namespace (e.g. ``client.orchestrations``).

    Resource methods return the typed pydantic model declared for the operation's
    response in the OpenAPI contract (validated via :meth:`_model` / :meth:`_list`),
    or ``None`` for an empty/``204`` response. The models live in
    :mod:`perceivo_client.generated.models`.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    @staticmethod
    def _model(model: type[_M], data: Any) -> _M | Any:
        """Validate a JSON object into ``model``.

        Lenient by design: a ``None``/``204`` body or a non-object payload (e.g. a
        bare list or error text the caller will branch on) passes through unchanged
        rather than raising — the typed happy-path is an object.
        """
        return _coerce(model, data) if isinstance(data, dict) else data

    @staticmethod
    def _list(model: type[_M], data: Any) -> list[_M] | Any:
        """Validate a JSON array into ``list[model]``; pass a non-list through."""
        return (
            [_coerce(model, x) if isinstance(x, dict) else x for x in data]
            if isinstance(data, list)
            else data
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        files: Any = None,
        min_timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self._t.request(
            method,
            path,
            params=params,
            json=json,
            files=files,
            min_timeout=min_timeout,
            headers=headers,
        )
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        files: Any = None,
        min_timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """POST ``path``. ``files`` is an ``httpx`` multipart mapping; it is
        mutually exclusive with ``json`` (httpx refuses both on one request).
        ``headers`` are added to the request's own (``If-Match``,
        ``Idempotency-Key``)."""
        return self._request(
            "POST",
            path,
            params=params,
            json=json,
            files=files,
            min_timeout=min_timeout,
            headers=headers,
        )

    def _patch(self, path: str, *, json: Any = None) -> Any:
        return self._request("PATCH", path, json=json)

    def _put(self, path: str, *, json: Any = None) -> Any:
        return self._request("PUT", path, json=json)

    def _delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._request("DELETE", path, params=params)
