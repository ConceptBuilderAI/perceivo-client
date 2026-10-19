"""Every path value of the assets methods is sent as one encoded segment.

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
        lambda c: c.assets.copy("../x0"), "POST", f"{B}/assets/..%2Fx0/copy", id="assets.copy"
    ),
    pytest.param(
        lambda c: c.assets.export_bundle("../x0"),
        "GET",
        f"{B}/assets/..%2Fx0/export",
        id="assets.export_bundle",
    ),
    pytest.param(
        lambda c: c.assets.restore("../x0"),
        "POST",
        f"{B}/assets/..%2Fx0/restore",
        id="assets.restore",
    ),
    pytest.param(
        lambda c: c.capabilities.apply_traffic_plan("../x0", {}),
        "POST",
        f"{B}/capabilities/..%2Fx0/traffic-plan",
        id="capabilities.apply_traffic_plan",
    ),
    pytest.param(
        lambda c: c.capabilities.attach_orchestration("../x0", "../x1"),
        "PUT",
        f"{B}/capabilities/..%2Fx0/orchestrations/..%2Fx1",
        id="capabilities.attach_orchestration",
    ),
    pytest.param(
        lambda c: c.capabilities.copy("../x0"),
        "POST",
        f"{B}/capabilities/..%2Fx0/copy",
        id="capabilities.copy",
    ),
    pytest.param(
        lambda c: c.capabilities.create_trigger("../x0", {}),
        "POST",
        f"{B}/capabilities/..%2Fx0/triggers",
        id="capabilities.create_trigger",
    ),
    pytest.param(
        lambda c: c.capabilities.delete_traffic("../x0"),
        "DELETE",
        f"{B}/capabilities/..%2Fx0/traffic",
        id="capabilities.delete_traffic",
    ),
    pytest.param(
        lambda c: c.capabilities.delete_traffic_plan("../x0"),
        "DELETE",
        f"{B}/capabilities/..%2Fx0/traffic-plan",
        id="capabilities.delete_traffic_plan",
    ),
    pytest.param(
        lambda c: c.capabilities.delete_trigger("../x0", "../x1"),
        "DELETE",
        f"{B}/capabilities/..%2Fx0/triggers/..%2Fx1",
        id="capabilities.delete_trigger",
    ),
    pytest.param(
        lambda c: c.capabilities.delete_version("../x0", "../x1"),
        "DELETE",
        f"{B}/capabilities/..%2Fx0/versions/..%2Fx1",
        id="capabilities.delete_version",
    ),
    pytest.param(
        lambda c: c.capabilities.detach_orchestration("../x0", "../x1"),
        "DELETE",
        f"{B}/capabilities/..%2Fx0/orchestrations/..%2Fx1",
        id="capabilities.detach_orchestration",
    ),
    pytest.param(
        lambda c: c.capabilities.get_evaluation_summary("../x0"),
        "GET",
        f"{B}/capabilities/..%2Fx0/evaluation-summary",
        id="capabilities.get_evaluation_summary",
    ),
    pytest.param(
        lambda c: c.capabilities.get_traffic("../x0"),
        "GET",
        f"{B}/capabilities/..%2Fx0/traffic",
        id="capabilities.get_traffic",
    ),
    pytest.param(
        lambda c: c.capabilities.get_traffic_plan("../x0"),
        "GET",
        f"{B}/capabilities/..%2Fx0/traffic-plan",
        id="capabilities.get_traffic_plan",
    ),
    pytest.param(
        lambda c: c.capabilities.get_lineage("../x0"),
        "GET",
        f"{B}/capabilities/..%2Fx0/lineage",
        id="capabilities.get_lineage",
    ),
    pytest.param(
        lambda c: c.capabilities.list_orchestrations("../x0"),
        "GET",
        f"{B}/capabilities/..%2Fx0/orchestrations",
        id="capabilities.list_orchestrations",
    ),
    pytest.param(
        lambda c: c.capabilities.list_triggers("../x0"),
        "GET",
        f"{B}/capabilities/..%2Fx0/triggers",
        id="capabilities.list_triggers",
    ),
    pytest.param(
        lambda c: c.capabilities.replace_evaluation_config("../x0", {}),
        "PUT",
        f"{B}/capabilities/..%2Fx0/evaluation-config",
        id="capabilities.replace_evaluation_config",
    ),
    pytest.param(
        lambda c: c.capabilities.restore("../x0"),
        "POST",
        f"{B}/capabilities/..%2Fx0/restore",
        id="capabilities.restore",
    ),
    pytest.param(
        lambda c: c.capabilities.replace_traffic("../x0", {}),
        "PUT",
        f"{B}/capabilities/..%2Fx0/traffic",
        id="capabilities.replace_traffic",
    ),
    pytest.param(
        lambda c: c.capabilities.update_trigger("../x0", "../x1", {}),
        "PATCH",
        f"{B}/capabilities/..%2Fx0/triggers/..%2Fx1",
        id="capabilities.update_trigger",
    ),
    pytest.param(
        lambda c: c.components.delete_version("../x0", "../x1"),
        "DELETE",
        f"{B}/components/..%2Fx0/versions/..%2Fx1",
        id="components.delete_version",
    ),
    pytest.param(
        lambda c: c.components.get_dependents("../x0"),
        "GET",
        f"{B}/components/..%2Fx0/dependents",
        id="components.get_dependents",
    ),
    pytest.param(
        lambda c: c.components.get_artifact("../x0"),
        "GET",
        f"{B}/components/..%2Fx0/artifact",
        id="components.get_artifact",
    ),
    pytest.param(
        lambda c: c.components.get_lineage("../x0"),
        "GET",
        f"{B}/components/..%2Fx0/lineage",
        id="components.get_lineage",
    ),
    pytest.param(
        lambda c: c.components.replace_artifact("../x0", {}),
        "PUT",
        f"{B}/components/..%2Fx0/artifact",
        id="components.replace_artifact",
    ),
    pytest.param(
        lambda c: c.components.restore("../x0"),
        "POST",
        f"{B}/components/..%2Fx0/restore",
        id="components.restore",
    ),
    pytest.param(
        lambda c: c.components.run("../x0", {}),
        "POST",
        f"{B}/components/..%2Fx0/run",
        id="components.run",
    ),
    pytest.param(
        lambda c: c.experiments.delete("../x0"),
        "DELETE",
        f"{B}/experiments/..%2Fx0",
        id="experiments.delete",
    ),
    pytest.param(
        lambda c: c.experiments.get("../x0"),
        "GET",
        f"{B}/experiments/..%2Fx0",
        id="experiments.get",
    ),
    pytest.param(
        lambda c: c.experiments.run("../x0"),
        "POST",
        f"{B}/experiments/..%2Fx0/run",
        id="experiments.run",
    ),
    pytest.param(
        lambda c: c.experiments.get_session("../x0"),
        "GET",
        f"{B}/experiments/..%2Fx0/session",
        id="experiments.get_session",
    ),
    pytest.param(
        lambda c: c.experiments.stop("../x0"),
        "POST",
        f"{B}/experiments/..%2Fx0/stop",
        id="experiments.stop",
    ),
    pytest.param(
        lambda c: c.experiments.update("../x0", {}),
        "PATCH",
        f"{B}/experiments/..%2Fx0",
        id="experiments.update",
    ),
    pytest.param(
        lambda c: c.orchestrations.assign_capability("../x0", {}),
        "POST",
        f"{B}/orchestrations/..%2Fx0/assign-capability",
        id="orchestrations.assign_capability",
    ),
    pytest.param(
        lambda c: c.orchestrations.get_compatibility("../x0", "x1"),
        "GET",
        f"{B}/orchestrations/..%2Fx0/compatibility",
        id="orchestrations.get_compatibility",
    ),
    pytest.param(
        lambda c: c.orchestrations.copy("../x0"),
        "POST",
        f"{B}/orchestrations/..%2Fx0/copy",
        id="orchestrations.copy",
    ),
    pytest.param(
        lambda c: c.orchestrations.delete_draft("../x0"),
        "DELETE",
        f"{B}/orchestrations/drafts/..%2Fx0",
        id="orchestrations.delete_draft",
    ),
    pytest.param(
        lambda c: c.orchestrations.delete_version("../x0", "../x1"),
        "DELETE",
        f"{B}/orchestrations/..%2Fx0/versions/..%2Fx1",
        id="orchestrations.delete_version",
    ),
    pytest.param(
        lambda c: c.orchestrations.export_bundle("../x0"),
        "GET",
        f"{B}/orchestrations/..%2Fx0/export",
        id="orchestrations.export_bundle",
    ),
    pytest.param(
        lambda c: c.orchestrations.get_draft("../x0"),
        "GET",
        f"{B}/orchestrations/drafts/..%2Fx0",
        id="orchestrations.get_draft",
    ),
    pytest.param(
        lambda c: c.orchestrations.get_graph("../x0"),
        "GET",
        f"{B}/orchestrations/..%2Fx0/graph",
        id="orchestrations.get_graph",
    ),
    pytest.param(
        lambda c: c.orchestrations.get_lineage("../x0"),
        "GET",
        f"{B}/orchestrations/..%2Fx0/lineage",
        id="orchestrations.get_lineage",
    ),
    pytest.param(
        lambda c: c.orchestrations.list_node_secret_bindings("../x0"),
        "GET",
        f"{B}/orchestrations/..%2Fx0/node-secrets",
        id="orchestrations.list_node_secret_bindings",
    ),
    pytest.param(
        lambda c: c.orchestrations.publish_draft("../x0", {}),
        "POST",
        f"{B}/orchestrations/drafts/..%2Fx0/publish",
        id="orchestrations.publish_draft",
    ),
    pytest.param(
        lambda c: c.orchestrations.restore("../x0"),
        "POST",
        f"{B}/orchestrations/..%2Fx0/restore",
        id="orchestrations.restore",
    ),
    pytest.param(
        lambda c: c.orchestrations.update_draft("../x0", {}),
        "PATCH",
        f"{B}/orchestrations/drafts/..%2Fx0",
        id="orchestrations.update_draft",
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


def test_the_table_covers_48_methods():
    assert len(_ROWS) == 48
