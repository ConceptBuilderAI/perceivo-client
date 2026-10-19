"""Every caller-supplied path value is one encoded segment, or it is refused.

Cases are derived by calling each public resource method with a sentinel per
argument and recording which arguments land in the request path.
"""

from __future__ import annotations

import contextlib
import inspect
import uuid
from collections import Counter
from typing import Any

import httpx
import pytest

from perceivo_client._paths import segment
from perceivo_client.resources._base import BaseResource
from tests.conftest import make_client

_REFUSED_VALUES = ("..", ".", "")


def _handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={})


def _namespaces(client: Any) -> dict[str, BaseResource]:
    return {
        name: value
        for name, value in vars(client).items()
        if not name.startswith("_") and isinstance(value, BaseResource)
    }


def _dummy(param: inspect.Parameter, sentinel: str) -> Any:
    """A placeholder argument: a sentinel string unless the annotation says otherwise."""
    ann = str(param.annotation)
    if param.name == "body" or ann.startswith("dict"):
        return {}
    if ann.startswith("bool"):
        return False
    if ann.startswith("int"):
        return 1
    if ann.startswith("list"):
        return []
    if "bytes" in ann:
        return b"x"
    return sentinel


def _required(method: Any) -> list[inspect.Parameter]:
    return [
        p
        for p in inspect.signature(method).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]


def _call(method: Any, params: list[inspect.Parameter], values: dict[str, Any]) -> None:
    args = [values[p.name] for p in params if p.kind is not inspect.Parameter.KEYWORD_ONLY]
    kwargs = {p.name: values[p.name] for p in params if p.kind is inspect.Parameter.KEYWORD_ONLY}
    method(*args, **kwargs)


def _segments(request: httpx.Request) -> list[str]:
    return request.url.raw_path.split(b"?", 1)[0].decode("ascii").split("/")


def _discover() -> list[tuple[str, str, str]]:
    """(namespace, method, argument) for every argument that lands in a request path."""
    client, rec = make_client(_handler)
    found: list[tuple[str, str, str]] = []
    for ns_name, ns in sorted(_namespaces(client).items()):
        for meth_name, method in inspect.getmembers(ns, inspect.ismethod):
            if meth_name.startswith("_"):
                continue
            params = _required(method)
            values = {p.name: _dummy(p, f"sentinel{i}q") for i, p in enumerate(params)}
            rec.requests.clear()
            with contextlib.suppress(Exception):  # the response shape is irrelevant here
                _call(method, params, values)
            if not rec.requests:
                continue
            segs = _segments(rec.requests[0])
            found.extend(
                (ns_name, meth_name, p.name)
                for p in params
                if isinstance(values[p.name], str) and values[p.name] in segs
            )
    return found


_CASES = _discover()


def _invoke(ns_name: str, meth_name: str, arg: str, value: Any):
    client, rec = make_client(_handler)
    method = getattr(getattr(client, ns_name), meth_name)
    params = _required(method)
    values = {p.name: _dummy(p, f"ok{i}") for i, p in enumerate(params)}
    values[arg] = value
    return method, params, values, rec


def test_population_is_the_whole_surface():
    """The derivation found every path argument, so the tests below are not vacuous."""
    by_ns = Counter(ns for ns, _, _ in _CASES)
    assert len(_CASES) == 374, sorted(_CASES)
    for ns in (
        "alert_channels",
        "alert_rules",
        "alerts",
        "assets",
        "billing",
        "capabilities",
        "components",
        "experiments",
        "files",
        "grants",
        "groups",
        "infrastructure",
        "intelligence",
        "invitations",
        "members",
        "operations",
        "orchestrations",
        "queue",
        "reviews",
        "roles",
        "runs",
        "secrets",
        "service_accounts",
        "support",
        "threads",
        "webhooks",
    ):
        assert by_ns[ns] > 0, f"no path argument discovered on {ns}"
    for case in (
        ("infrastructure", "get_search_index", "index_name"),
        ("infrastructure", "get_vector_store_collection", "collection_name"),
        ("infrastructure", "update_nodepool", "nodepool_name"),
        ("infrastructure", "delete_nodepool", "nodepool_name"),
        ("infrastructure", "get_cache_key", "key"),
        ("infrastructure", "ingest_search_index", "index_name"),
        ("infrastructure", "query_search_index", "index_name"),
        ("infrastructure", "ingest_vector_store_collection", "collection_name"),
        ("infrastructure", "query_vector_store_collection", "collection_name"),
        ("infrastructure", "start_cluster_service", "service"),
        ("infrastructure", "invoke_mcp_tool", "tool_name"),
        ("secrets", "get_value", "secret_id"),
        ("orchestrations", "get_node_secret_aliases", "node_id"),
        ("grants", "update", "grant_id"),
        ("grants", "delete", "grant_id"),
    ):
        assert case in _CASES, case


@pytest.mark.parametrize("bad", _REFUSED_VALUES, ids=["dotdot", "dot", "empty"])
@pytest.mark.parametrize(("ns_name", "meth_name", "arg"), _CASES, ids=lambda v: v)
def test_dot_and_empty_segments_are_refused_before_sending(ns_name, meth_name, arg, bad):
    method, params, values, rec = _invoke(ns_name, meth_name, arg, bad)
    with pytest.raises(ValueError, match=rf"{arg} must be one path segment"):
        _call(method, params, values)
    assert rec.requests == []


@pytest.mark.parametrize(("ns_name", "meth_name", "arg"), _CASES, ids=lambda v: v)
def test_slash_is_encoded_and_stays_one_segment(ns_name, meth_name, arg):
    method, params, values, rec = _invoke(ns_name, meth_name, arg, "a/b")
    baseline_method, _, baseline_values, baseline_rec = _invoke(ns_name, meth_name, arg, "plain")
    for m, v in ((method, values), (baseline_method, baseline_values)):
        with contextlib.suppress(Exception):  # the response shape is irrelevant here
            _call(m, params, v)
    segs = _segments(rec.requests[0])
    plain = _segments(baseline_rec.requests[0])
    assert "a%2Fb" in segs
    assert len(segs) == len(plain)
    assert [s if s != "a%2Fb" else "plain" for s in segs] == plain


@pytest.mark.parametrize(("ns_name", "meth_name", "arg"), _CASES, ids=lambda v: v)
def test_uuid_ids_are_sent_unchanged(ns_name, meth_name, arg):
    """Behaviour-preserving for valid input: a UUID, as text or object, encodes to itself."""
    ident = uuid.UUID("9efa4550-e04e-4624-a6f2-684af0330f23")
    for value in (str(ident), ident):
        method, params, values, rec = _invoke(ns_name, meth_name, arg, value)
        with contextlib.suppress(Exception):  # the response shape is irrelevant here
            _call(method, params, values)
        assert str(ident) in _segments(rec.requests[0])


def test_httpx_resolves_dot_segments_which_is_the_hazard():
    """``httpx`` drops ``..`` and the segment before it, which the refusal prevents."""
    url = httpx.URL("https://api.test/v1/indices/idx/documents/..")
    assert url.path == "/v1/indices/idx"


def test_dotdot_cache_key_is_refused_before_sending():
    client, rec = make_client(_handler)
    with pytest.raises(ValueError, match="key must be one path segment"):
        client.infrastructure.get_cache_key("..")
    assert rec.requests == []


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain", "plain"),
        ("a/b", "a%2Fb"),
        ("a?b#c", "a%3Fb%23c"),
        ("50%", "50%25"),
        ("...", "..."),
        ("a b", "a%20b"),
        ("9efa4550-e04e-4624-a6f2-684af0330f23", "9efa4550-e04e-4624-a6f2-684af0330f23"),
        (uuid.UUID(int=1), "00000000-0000-0000-0000-000000000001"),
    ],
)
def test_segment_encoding(value, expected):
    assert segment(value, "f") == expected


@pytest.mark.parametrize("bad", _REFUSED_VALUES)
def test_segment_refuses(bad):
    with pytest.raises(ValueError, match=r"^name must be one path segment"):
        segment(bad, "name")
