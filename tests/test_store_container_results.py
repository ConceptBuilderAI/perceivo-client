"""Store-container create and delete calls return the result model the contract names."""

from __future__ import annotations

import pytest

from perceivo_client.generated.models import (
    SearchIndexCreated,
    SearchIndexDeleted,
    VectorStoreCollectionCreated,
    VectorStoreCollectionDeleted,
)
from tests.conftest import json_handler, make_client


@pytest.mark.parametrize(
    "call,body,model",
    [
        (
            lambda c: c.infrastructure.create_search_index({"name": "i1"}),
            {"created": True, "index": "i1"},
            SearchIndexCreated,
        ),
        (
            lambda c: c.infrastructure.delete_search_index("i1"),
            {"deleted": True, "index": "i1"},
            SearchIndexDeleted,
        ),
        (
            lambda c: c.infrastructure.create_vector_store_collection({"name": "c1"}),
            {"created": True, "collection": "c1"},
            VectorStoreCollectionCreated,
        ),
        (
            lambda c: c.infrastructure.delete_vector_store_collection("c1"),
            {"dropped": True, "collection": "c1"},
            VectorStoreCollectionDeleted,
        ),
    ],
)
def test_store_container_create_and_delete_return_their_echo(call, body, model):
    client, _ = make_client(json_handler(body))
    got = call(client)
    assert isinstance(got, model)
    assert got.model_dump() == body
