"""Every path value of the access and runtime methods is sent as one encoded segment.

Each value is sent as ``../xN`` and must arrive as ``..%2FxN``, from the sync and
async clients.
"""

from __future__ import annotations

import asyncio

import pytest

from tests.conftest import make_client
from tests.fixtures_wrapper_cases import B
from tests.test_pagination_and_async import _async_from_sync
from tests.test_wrapper_matrix import _shape_aware_handler

_ROWS = [
    pytest.param(
        lambda c: c.alert_channels.delete("../x0"),
        "DELETE",
        f"{B}/alert-channels/..%2Fx0",
        id="alert_channels.delete",
    ),
    pytest.param(
        lambda c: c.alert_channels.get("../x0"),
        "GET",
        f"{B}/alert-channels/..%2Fx0",
        id="alert_channels.get",
    ),
    pytest.param(
        lambda c: c.alert_channels.update("../x0", {}),
        "PATCH",
        f"{B}/alert-channels/..%2Fx0",
        id="alert_channels.update",
    ),
    pytest.param(
        lambda c: c.alert_rules.delete("../x0"),
        "DELETE",
        f"{B}/alert-rules/..%2Fx0",
        id="alert_rules.delete",
    ),
    pytest.param(
        lambda c: c.alert_rules.get("../x0"),
        "GET",
        f"{B}/alert-rules/..%2Fx0",
        id="alert_rules.get",
    ),
    pytest.param(
        lambda c: c.alert_rules.test("../x0"),
        "POST",
        f"{B}/alert-rules/..%2Fx0/test",
        id="alert_rules.test",
    ),
    pytest.param(
        lambda c: c.alert_rules.update("../x0", {}),
        "PATCH",
        f"{B}/alert-rules/..%2Fx0",
        id="alert_rules.update",
    ),
    pytest.param(
        lambda c: c.groups.add_member("../x0", {}),
        "POST",
        f"{B}/groups/..%2Fx0/members",
        id="groups.add_member",
    ),
    pytest.param(
        lambda c: c.groups.delete("../x0"), "DELETE", f"{B}/groups/..%2Fx0", id="groups.delete"
    ),
    pytest.param(lambda c: c.groups.get("../x0"), "GET", f"{B}/groups/..%2Fx0", id="groups.get"),
    pytest.param(
        lambda c: c.groups.list_members("../x0"),
        "GET",
        f"{B}/groups/..%2Fx0/members",
        id="groups.list_members",
    ),
    pytest.param(
        lambda c: c.groups.remove_member("../x0", "../x1"),
        "DELETE",
        f"{B}/groups/..%2Fx0/members/..%2Fx1",
        id="groups.remove_member",
    ),
    pytest.param(
        lambda c: c.groups.remove_principal("../x0", "../x1", "../x2"),
        "DELETE",
        f"{B}/groups/..%2Fx0/members/..%2Fx1/..%2Fx2",
        id="groups.remove_principal",
    ),
    pytest.param(
        lambda c: c.groups.update("../x0", {}), "PATCH", f"{B}/groups/..%2Fx0", id="groups.update"
    ),
    pytest.param(
        lambda c: c.groups.update_member("../x0", "../x1", {}),
        "PATCH",
        f"{B}/groups/..%2Fx0/members/..%2Fx1",
        id="groups.update_member",
    ),
    pytest.param(
        lambda c: c.infrastructure.create_managed_service_backup("../x0"),
        "POST",
        f"{B}/infrastructure/managed/..%2Fx0/backups",
        id="infrastructure.create_managed_service_backup",
    ),
    pytest.param(
        lambda c: c.infrastructure.get_database("../x0"),
        "GET",
        f"{B}/infrastructure/databases/..%2Fx0",
        id="infrastructure.get_database",
    ),
    pytest.param(
        lambda c: c.infrastructure.get_managed_service("../x0"),
        "GET",
        f"{B}/infrastructure/managed/..%2Fx0",
        id="infrastructure.get_managed_service",
    ),
    pytest.param(
        lambda c: c.infrastructure.get_managed_service_backup("../x0", "../x1"),
        "GET",
        f"{B}/infrastructure/managed/..%2Fx0/backups/..%2Fx1",
        id="infrastructure.get_managed_service_backup",
    ),
    pytest.param(
        lambda c: c.infrastructure.list_managed_service_backups("../x0"),
        "GET",
        f"{B}/infrastructure/managed/..%2Fx0/backups",
        id="infrastructure.list_managed_service_backups",
    ),
    pytest.param(
        lambda c: c.infrastructure.get_nodepool("../x0"),
        "GET",
        f"{B}/infrastructure/cluster/nodepools/..%2Fx0",
        id="infrastructure.get_nodepool",
    ),
    pytest.param(
        lambda c: c.infrastructure.record_database_activity("../x0"),
        "POST",
        f"{B}/infrastructure/databases/..%2Fx0/activity",
        id="infrastructure.record_database_activity",
    ),
    pytest.param(
        lambda c: c.infrastructure.scale_nodepool("../x0", {}),
        "POST",
        f"{B}/infrastructure/cluster/nodepools/..%2Fx0/scale",
        id="infrastructure.scale_nodepool",
    ),
    pytest.param(
        lambda c: c.infrastructure.delete_search_index("../x0"),
        "DELETE",
        f"{B}/infrastructure/search-index/indices/..%2Fx0",
        id="infrastructure.delete_search_index",
    ),
    pytest.param(
        lambda c: c.infrastructure.delete_search_index_document("../x0", "../x1"),
        "DELETE",
        f"{B}/infrastructure/search-index/indices/..%2Fx0/documents/..%2Fx1",
        id="infrastructure.delete_search_index_document",
    ),
    pytest.param(
        lambda c: c.infrastructure.list_search_index_documents("../x0"),
        "GET",
        f"{B}/infrastructure/search-index/indices/..%2Fx0/documents",
        id="infrastructure.list_search_index_documents",
    ),
    pytest.param(
        lambda c: c.infrastructure.export_search_index("../x0"),
        "POST",
        f"{B}/infrastructure/search-index/indices/..%2Fx0/export",
        id="infrastructure.export_search_index",
    ),
    pytest.param(
        lambda c: c.infrastructure.import_search_index("../x0", b"x1"),
        "POST",
        f"{B}/infrastructure/search-index/indices/..%2Fx0/import",
        id="infrastructure.import_search_index",
    ),
    pytest.param(
        lambda c: c.infrastructure.add_search_index_document("../x0", {}),
        "POST",
        f"{B}/infrastructure/search-index/indices/..%2Fx0/documents",
        id="infrastructure.add_search_index_document",
    ),
    pytest.param(
        lambda c: c.infrastructure.start_database("../x0"),
        "POST",
        f"{B}/infrastructure/databases/..%2Fx0/start",
        id="infrastructure.start_database",
    ),
    pytest.param(
        lambda c: c.infrastructure.start_managed_service("../x0"),
        "POST",
        f"{B}/infrastructure/managed/..%2Fx0/start",
        id="infrastructure.start_managed_service",
    ),
    pytest.param(
        lambda c: c.infrastructure.stop_managed_service("../x0"),
        "POST",
        f"{B}/infrastructure/managed/..%2Fx0/stop",
        id="infrastructure.stop_managed_service",
    ),
    pytest.param(
        lambda c: c.infrastructure.update_managed_service("../x0", {}),
        "PATCH",
        f"{B}/infrastructure/managed/..%2Fx0",
        id="infrastructure.update_managed_service",
    ),
    pytest.param(
        lambda c: c.infrastructure.update_cluster_service("../x0", {}),
        "PATCH",
        f"{B}/infrastructure/cluster/..%2Fx0",
        id="infrastructure.update_cluster_service",
    ),
    pytest.param(
        lambda c: c.infrastructure.delete_vector_store_collection("../x0"),
        "DELETE",
        f"{B}/infrastructure/vector-store/collections/..%2Fx0",
        id="infrastructure.delete_vector_store_collection",
    ),
    pytest.param(
        lambda c: c.infrastructure.delete_vector_store_entity("../x0", "../x1"),
        "DELETE",
        f"{B}/infrastructure/vector-store/collections/..%2Fx0/entities/..%2Fx1",
        id="infrastructure.delete_vector_store_entity",
    ),
    pytest.param(
        lambda c: c.infrastructure.list_vector_store_entities("../x0"),
        "GET",
        f"{B}/infrastructure/vector-store/collections/..%2Fx0/entities",
        id="infrastructure.list_vector_store_entities",
    ),
    pytest.param(
        lambda c: c.infrastructure.export_vector_store_collection("../x0"),
        "POST",
        f"{B}/infrastructure/vector-store/collections/..%2Fx0/export",
        id="infrastructure.export_vector_store_collection",
    ),
    pytest.param(
        lambda c: c.infrastructure.import_vector_store_collection("../x0", b"x1"),
        "POST",
        f"{B}/infrastructure/vector-store/collections/..%2Fx0/import",
        id="infrastructure.import_vector_store_collection",
    ),
    pytest.param(
        lambda c: c.infrastructure.add_vector_store_entities("../x0", {}),
        "POST",
        f"{B}/infrastructure/vector-store/collections/..%2Fx0/entities",
        id="infrastructure.add_vector_store_entities",
    ),
    pytest.param(
        lambda c: c.invitations.cancel("../x0"),
        "POST",
        f"{B}/invitations/..%2Fx0/cancel",
        id="invitations.cancel",
    ),
    pytest.param(
        lambda c: c.invitations.resend("../x0"),
        "POST",
        f"{B}/invitations/..%2Fx0/resend",
        id="invitations.resend",
    ),
    pytest.param(
        lambda c: c.members.remove("../x0"), "DELETE", f"{B}/members/..%2Fx0", id="members.remove"
    ),
    pytest.param(
        lambda c: c.members.restore("../x0"),
        "POST",
        f"{B}/members/..%2Fx0/restore",
        id="members.restore",
    ),
    pytest.param(
        lambda c: c.members.update_role("../x0", {}),
        "PATCH",
        f"{B}/members/..%2Fx0",
        id="members.update_role",
    ),
    pytest.param(
        lambda c: c.operations.cancel("../x0"),
        "POST",
        f"{B}/operations/..%2Fx0/cancel",
        id="operations.cancel",
    ),
    pytest.param(
        lambda c: c.operations.get("../x0"), "GET", f"{B}/operations/..%2Fx0", id="operations.get"
    ),
    pytest.param(
        lambda c: c.runs.events("../x0"),
        "GET",
        f"{B}/orchestrations/runs/..%2Fx0/events",
        id="runs.events",
    ),
    pytest.param(
        lambda c: c.runs.pause("../x0"),
        "POST",
        f"{B}/orchestrations/runs/..%2Fx0/pause",
        id="runs.pause",
    ),
    pytest.param(
        lambda c: c.runs.resume("../x0"),
        "POST",
        f"{B}/orchestrations/runs/..%2Fx0/resume",
        id="runs.resume",
    ),
    pytest.param(
        lambda c: c.runs.steps("../x0"),
        "GET",
        f"{B}/orchestrations/runs/..%2Fx0/steps",
        id="runs.steps",
    ),
    pytest.param(
        lambda c: c.runs.stop("../x0"),
        "POST",
        f"{B}/orchestrations/runs/..%2Fx0/stop",
        id="runs.stop",
    ),
    pytest.param(
        lambda c: c.service_accounts.delete("../x0"),
        "DELETE",
        f"{B}/service-accounts/..%2Fx0",
        id="service_accounts.delete",
    ),
]


@pytest.mark.parametrize("call,verb,raw_path", _ROWS)
def test_each_path_value_is_sent_as_one_encoded_segment(call, verb, raw_path):
    client, rec = make_client(_shape_aware_handler)

    call(client)

    assert rec.last.method == verb
    assert rec.last.url.raw_path.split(b"?")[0] == raw_path.encode()


@pytest.mark.parametrize("call,verb,raw_path", _ROWS)
def test_the_async_client_sends_the_same_encoded_segment(call, verb, raw_path):
    sync, rec = make_client(_shape_aware_handler)
    client = _async_from_sync(sync)

    async def run():
        return await call(client)

    asyncio.run(run())

    assert rec.last.method == verb
    assert rec.last.url.raw_path.split(b"?")[0] == raw_path.encode()


def test_the_table_covers_53_methods():
    assert len(_ROWS) == 53
