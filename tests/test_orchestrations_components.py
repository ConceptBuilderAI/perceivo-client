"""Orchestrations and components.

``client.orchestrations`` gains drafts, definition validation, capability
assignment and compatibility, copy, export, the graph, lineage, version
delete/restore and the orchestration-level node-secret bindings;
``client.components`` gains the script artifact, dependents, isolated runs,
lineage and version delete/restore. Method and path for every row are pinned by
``test_wrapper_matrix``; this module pins what that matrix cannot see: the
draft -> publish id chain, the artifact replace -> new version id chain, the
script read as text, the node-secret surface carrying no secret value, the
required ``capability_id`` query, ``restore(detach=...)``, empty-body defaults,
``PUT`` verbs, ``204`` bodies, the bare arrays ``paginate_pages`` does not walk,
typed returns and async parity.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from perceivo_client import paginate_pages
from perceivo_client.generated.models import (
    AssetLineageRead,
    AssignCapabilityResultRead,
    CapabilityCompatibilityRead,
    ComponentDetailRead,
    ComponentRunResult,
    ComponentUsageReport,
    LineageRestoreResult,
    NodeSecretRead,
    OrchestrationDraftPublished,
    OrchestrationDraftRead,
    OrchestrationExportRead,
    OrchestrationGraph,
    OrchestrationRead,
    OrchestrationRestoreResult,
    OrchestrationValidationResult,
)
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_O = "/v1/orchestrations"
_C = "/v1/components"
_DRAFT = {
    "id": "drf-1",
    "name": "nightly",
    "organization_id": "org-1",
    "created_by_user_id": "u1",
    "canvas_state": {},
    "base_version_id": "orc-1",
}
_DETAIL = {
    "id": "cmp-2",
    "name": "scorer",
    "asset_type": "component",
    "organization_id": "org-1",
    "status": "active",
    "created_at": "2026-10-03T00:00:00Z",
    "updated_at": "2026-10-03T00:00:00Z",
    "parent_asset_id": "cmp-1",
    "version_number": 2,
}
_BINDING = {
    "id": "b1",
    "orchestration_id": "orc-1",
    "node_id": "n1",
    "secret_id": "sec-1",
    "alias": "vendor_key",
}


def _routed(routes: dict[tuple[str, str], tuple[int, object]]):
    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes[(request.method, request.url.path)]
        return httpx.Response(status, json=body)

    return handler


_DRAFT_ROUTES = {
    ("POST", f"{_O}/drafts"): (201, _DRAFT),
    ("PATCH", f"{_O}/drafts/drf-1"): (200, _DRAFT),
    ("POST", f"{_O}/drafts/drf-1/publish"): (200, {"orchestration_id": "orc-2"}),
}


# --- chains --------------------------------------------------------------------


def test_draft_id_round_trips_into_update_and_publish():
    client, rec = make_client(_routed(_DRAFT_ROUTES))

    draft = client.orchestrations.create_draft({"source_orchestration_id": "orc-1"})
    client.orchestrations.update_draft(draft.id, {"staged_changes": {"nodes": []}})
    published = client.orchestrations.publish_draft(
        draft.id, {"expected_base_version_id": draft.base_version_id}
    )

    assert isinstance(draft, OrchestrationDraftRead)
    assert isinstance(published, OrchestrationDraftPublished)
    assert published.orchestration_id == "orc-2"
    assert [r.method for r in rec.requests] == ["POST", "PATCH", "POST"]
    assert json.loads(rec.last.content) == {"expected_base_version_id": "orc-1"}


def test_replace_artifact_returns_the_new_version_id_not_the_path_id():
    client, rec = make_client(json_handler(_DETAIL))

    got = client.components.replace_artifact("cmp-1", {"script": "print(1)"})

    assert isinstance(got, ComponentDetailRead)
    assert got.id == "cmp-2"
    assert got.parent_asset_id == "cmp-1"
    assert rec.last.method == "PUT"
    assert rec.last.url.path == f"{_C}/cmp-1/artifact"
    assert json.loads(rec.last.content) == {"script": "print(1)"}


def test_async_draft_chain_awaits_each_step():
    sync, rec = make_client(_routed(_DRAFT_ROUTES))
    client = _async_from_sync(sync)

    async def drive():
        draft = await client.orchestrations.create_draft({"name": "nightly"})
        await client.orchestrations.update_draft(draft.id, {})
        return await client.orchestrations.publish_draft(draft.id, {})

    published = asyncio.run(drive())

    assert isinstance(published, OrchestrationDraftPublished)
    assert [r.url.path for r in rec.requests] == [
        f"{_O}/drafts",
        f"{_O}/drafts/drf-1",
        f"{_O}/drafts/drf-1/publish",
    ]


# --- the script artifact --------------------------------------------------------


def test_get_artifact_returns_the_script_as_text():
    script = "def run(x):\n    return x\n"
    client, rec = make_client(
        lambda _r: httpx.Response(200, text=script, headers={"Content-Type": "text/plain"})
    )

    got = client.components.get_artifact("cmp-1")

    assert got == script
    assert rec.last.url.path == f"{_C}/cmp-1/artifact"


def test_get_artifact_does_not_decode_a_script_that_parses_as_json():
    client, _ = make_client(
        lambda _r: httpx.Response(200, text='{"a": 1}', headers={"Content-Type": "text/plain"})
    )

    assert client.components.get_artifact("cmp-1") == '{"a": 1}'


def test_async_get_artifact_returns_text():
    sync, rec = make_client(lambda _r: httpx.Response(200, text="print(1)"))
    client = _async_from_sync(sync)

    got = asyncio.run(client.components.get_artifact("cmp-1"))

    assert got == "print(1)"
    assert rec.last.method == "GET"


# --- node secrets ------------------------------------------------------------------


def test_node_secret_models_declare_no_value_field():
    read_fields = set(NodeSecretRead.model_fields)

    assert read_fields == {
        "alias",
        "created_at",
        "id",
        "node_id",
        "orchestration_id",
        "secret_expiration_date",
        "secret_id",
        "secret_name",
        "secret_status",
    }


def test_list_node_secrets_is_a_typed_bare_array():
    client, rec = make_client(json_handler([_BINDING, {**_BINDING, "id": "b2"}]))

    got = client.orchestrations.list_node_secret_bindings("orc-1")

    assert [b.id for b in got] == ["b1", "b2"]
    assert all(isinstance(b, NodeSecretRead) for b in got)
    assert dict(rec.last.url.params) == {}


# --- query parameters and bodies ----------------------------------------------------


def test_compatibility_sends_the_required_capability_id():
    client, rec = make_client(json_handler({"is_compatible": True}))

    got = client.orchestrations.get_compatibility("orc-1", "cap-1")

    assert isinstance(got, CapabilityCompatibilityRead)
    assert rec.last.url.path == f"{_O}/orc-1/compatibility"
    assert dict(rec.last.url.params) == {"capability_id": "cap-1"}


@pytest.mark.parametrize(
    "detach,expected",
    [(None, {}), (True, {"detach": "true"}), (False, {"detach": "false"})],
)
def test_restore_spells_detach_only_when_given(detach, expected):
    client, rec = make_client(json_handler({"id": "orc-1", "status": "active"}))

    got = client.orchestrations.restore("orc-1", detach=detach)

    assert isinstance(got, OrchestrationRestoreResult)
    assert rec.last.method == "POST"
    assert dict(rec.last.url.params) == expected
    assert rec.last.content == b""


def test_copy_sends_an_empty_object_without_a_body():
    client, rec = make_client(json_handler({"id": "orc-9"}, status=201))

    got = client.orchestrations.copy("orc-1")

    assert isinstance(got, OrchestrationRead)
    assert rec.last.url.path == f"{_O}/orc-1/copy"
    assert rec.last.content == b"{}"


def test_validate_returns_an_invalid_definition_as_a_result():
    client, rec = make_client(json_handler({"valid": False, "errors": ["dangling edge"]}))

    got = client.orchestrations.validate({"nodes": [], "ports": [], "edges": []})

    assert isinstance(got, OrchestrationValidationResult)
    assert got.valid is False
    assert rec.last.url.path == f"{_O}/validate"


def test_run_returns_a_failed_component_run_as_a_result():
    client, rec = make_client(json_handler({"success": False, "errors": ["boom"]}))

    got = client.components.run("cmp-1", {"request_data": {"x": 1}})

    assert isinstance(got, ComponentRunResult)
    assert got.success is False
    assert json.loads(rec.last.content) == {"request_data": {"x": 1}}


def test_component_restore_is_a_bodiless_post():
    client, rec = make_client(json_handler({"id": "cmp-1", "status": "active"}))

    got = client.components.restore("cmp-1")

    assert isinstance(got, LineageRestoreResult)
    assert rec.last.method == "POST"
    assert rec.last.content == b""


# --- pagination --------------------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.orchestrations.list_drafts(), OrchestrationDraftRead),
        (lambda c: c.orchestrations.list_node_secret_bindings("orc-1"), NodeSecretRead),
    ],
)
def test_bare_array_lists_are_typed(call, model):
    client, _ = make_client(json_handler([{"id": "a"}, {"id": "b"}]))

    got = call(client)

    assert len(got) == 2
    assert all(isinstance(item, model) for item in got)


def test_paginate_pages_refuses_the_bare_draft_list():
    client, rec = make_client(json_handler([{"id": "a"}]))
    walker = paginate_pages(lambda **_kw: client.orchestrations.list_drafts())

    with pytest.raises(ValueError):
        next(walker)
    assert rec.last.url.path == f"{_O}/drafts"


# --- typed returns and 204s ---------------------------------------------------------


@pytest.mark.parametrize(
    "call,model",
    [
        (lambda c: c.orchestrations.get_draft("d1"), OrchestrationDraftRead),
        (lambda c: c.orchestrations.assign_capability("o1", {}), AssignCapabilityResultRead),
        (lambda c: c.orchestrations.export_bundle("o1"), OrchestrationExportRead),
        (lambda c: c.orchestrations.get_graph("o1"), OrchestrationGraph),
        (lambda c: c.orchestrations.get_lineage("o1"), AssetLineageRead),
        (lambda c: c.components.get_dependents("c1"), ComponentUsageReport),
        (lambda c: c.components.get_lineage("c1"), AssetLineageRead),
    ],
)
def test_object_returns_are_typed(call, model):
    client, _ = make_client(json_handler({"id": "x"}))

    assert isinstance(call(client), model)


@pytest.mark.parametrize(
    "call,path",
    [
        (lambda c: c.orchestrations.delete_draft("d1"), f"{_O}/drafts/d1"),
        (lambda c: c.orchestrations.delete_version("o1", "v1"), f"{_O}/o1/versions/v1"),
        (lambda c: c.components.delete_version("c1", "v1"), f"{_C}/c1/versions/v1"),
    ],
)
def test_deletes_return_none_on_no_content(call, path):
    client, rec = make_client(lambda _r: httpx.Response(204))

    assert call(client) is None
    assert rec.last.method == "DELETE"
    assert rec.last.url.path == path


# --- async parity ------------------------------------------------------------------


def test_async_component_run_awaits_and_hits_the_exact_path():
    sync, rec = make_client(json_handler({"success": True, "output": {"y": 2}}))
    client = _async_from_sync(sync)

    got = asyncio.run(client.components.run("cmp-1", {"request_data": {}}))

    assert isinstance(got, ComponentRunResult)
    assert rec.last.url.path == f"{_C}/cmp-1/run"


def test_async_restore_forwards_detach():
    sync, rec = make_client(json_handler({"id": "orc-1", "status": "active"}))
    client = _async_from_sync(sync)

    got = asyncio.run(client.orchestrations.restore("orc-1", detach=True))

    assert isinstance(got, OrchestrationRestoreResult)
    assert dict(rec.last.url.params) == {"detach": "true"}
