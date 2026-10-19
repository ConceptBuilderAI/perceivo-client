"""``components.export_bundle`` and ``components.import_bundle``: the transfer pair.

The export document is what the import accepts, unchanged. The wrapper cases
pin method and path; this pins the body, the absence of query parameters and
the typed results.
"""

from __future__ import annotations

import json

import pytest

from perceivo_client.generated.models import ComponentExportDocument, ComponentImportResult
from tests.conftest import json_handler, make_client

_COMPONENT = "0f8fad5b-d9cb-469f-a165-70867728950e"
_EXPORT = {"exported_at": "2026-10-02T00:00:00Z", "component": {"name": "c", "category": "x"}}


def test_export_reads_the_component_export_route():
    client, rec = make_client(json_handler(_EXPORT))

    document = client.components.export_bundle(_COMPONENT)

    assert len(rec.requests) == 1
    assert rec.last.method == "GET"
    assert rec.last.url.path == f"/v1/components/{_COMPONENT}/export"
    assert dict(rec.last.url.params) == {}
    assert rec.last.content == b""
    assert isinstance(document, ComponentExportDocument)
    assert document.component.name == "c"


def test_import_component_posts_the_export_document():
    served = {"success": True, "asset_name": "c", "component_ids": ["x"]}
    client, rec = make_client(json_handler(served, status=201))
    body = {**_EXPORT, "new_name": "copy"}

    result = client.components.import_bundle(body)

    assert len(rec.requests) == 1
    assert rec.last.method == "POST"
    assert rec.last.url.path == "/v1/components/import"
    assert dict(rec.last.url.params) == {}
    assert json.loads(rec.last.content) == body
    assert isinstance(result, ComponentImportResult)
    assert result.asset_name == "c"


def test_the_export_document_is_accepted_unchanged_by_import():
    """The pair the API documents: export, then import the same document."""
    client, rec = make_client(json_handler(_EXPORT))
    document = client.components.export_bundle(_COMPONENT)

    client.components.import_bundle(document.model_dump(mode="json", exclude_unset=True))

    assert rec.last.url.path == "/v1/components/import"
    assert json.loads(rec.last.content) == _EXPORT


def test_export_takes_no_query_parameters():
    """The operation declares none, so the wrapper accepts none."""
    client, rec = make_client(json_handler(_EXPORT))
    call = client.components.export_bundle

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        call(_COMPONENT, version="1")

    assert rec.requests == []


def test_the_transfer_pair_left_the_files_namespace():
    client, _rec = make_client(json_handler({}))

    present = [name for name in ("import_asset", "export_asset") if hasattr(client.files, name)]

    assert present == []
