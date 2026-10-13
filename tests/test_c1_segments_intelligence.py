"""Every path value of the intelligence methods is one segment.

Covers the methods ``client.intelligence``. Each caller-supplied path value
is sent as ``../xN``, which ``httpx`` would otherwise resolve against the parent
collection; the request must carry it as the single encoded segment
``..%2FxN`` at the position the wrapper matrix pins, from the sync client and
from its async twin.
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
        lambda c: c.intelligence.activate_drift_baseline("../x0", "../x1"),
        "POST",
        f"{B}/intelligence/..%2Fx0/drift/baselines/..%2Fx1/activate",
        id="intelligence.activate_drift_baseline",
    ),
    pytest.param(
        lambda c: c.intelligence.activate_model_family("../x0", "../x1"),
        "POST",
        f"{B}/intelligence/..%2Fx0/model-families/..%2Fx1/activate",
        id="intelligence.activate_model_family",
    ),
    pytest.param(
        lambda c: c.intelligence.apply_traffic_plan("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/traffic-plan",
        id="intelligence.apply_traffic_plan",
    ),
    pytest.param(
        lambda c: c.intelligence.attach_service_secret("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/service-secrets",
        id="intelligence.attach_service_secret",
    ),
    pytest.param(
        lambda c: c.intelligence.create_model_family("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/model-families",
        id="intelligence.create_model_family",
    ),
    pytest.param(
        lambda c: c.intelligence.create_training_configuration("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/training-configurations",
        id="intelligence.create_training_configuration",
    ),
    pytest.param(
        lambda c: c.intelligence.create_training_group("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/training-groups",
        id="intelligence.create_training_group",
    ),
    pytest.param(
        lambda c: c.intelligence.create_trigger("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/triggers",
        id="intelligence.create_trigger",
    ),
    pytest.param(
        lambda c: c.intelligence.deactivate_model_family("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/model-families/..%2Fx1",
        id="intelligence.deactivate_model_family",
    ),
    pytest.param(
        lambda c: c.intelligence.delete_drift_baseline("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/drift/baselines/..%2Fx1",
        id="intelligence.delete_drift_baseline",
    ),
    pytest.param(
        lambda c: c.intelligence.delete_model("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/models/..%2Fx1",
        id="intelligence.delete_model",
    ),
    pytest.param(
        lambda c: c.intelligence.delete_training_configuration("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/training-configurations/..%2Fx1",
        id="intelligence.delete_training_configuration",
    ),
    pytest.param(
        lambda c: c.intelligence.delete_training_group("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/training-groups/..%2Fx1",
        id="intelligence.delete_training_group",
    ),
    pytest.param(
        lambda c: c.intelligence.delete_trigger("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/triggers/..%2Fx1",
        id="intelligence.delete_trigger",
    ),
    pytest.param(
        lambda c: c.intelligence.delete_version("../x0", "../x1"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/versions/..%2Fx1",
        id="intelligence.delete_version",
    ),
    pytest.param(
        lambda c: c.intelligence.detach_service_secret("../x0", "../x1", "../x2"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/service-secrets/..%2Fx1/..%2Fx2",
        id="intelligence.detach_service_secret",
    ),
    pytest.param(
        lambda c: c.intelligence.export_bundle("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/export",
        id="intelligence.export_bundle",
    ),
    pytest.param(
        lambda c: c.intelligence.get_drift_baseline("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/drift/baselines/..%2Fx1",
        id="intelligence.get_drift_baseline",
    ),
    pytest.param(
        lambda c: c.intelligence.get_drift_config("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/drift/config",
        id="intelligence.get_drift_config",
    ),
    pytest.param(
        lambda c: c.intelligence.get_feature_view("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/features/..%2Fx1",
        id="intelligence.get_feature_view",
    ),
    pytest.param(
        lambda c: c.intelligence.get_model_family("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/model-families/..%2Fx1",
        id="intelligence.get_model_family",
    ),
    pytest.param(
        lambda c: c.intelligence.get_pii_config("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/config/pii",
        id="intelligence.get_pii_config",
    ),
    pytest.param(
        lambda c: c.intelligence.get_inference_request_artifact("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/inference/requests/..%2Fx1/artifact",
        id="intelligence.get_inference_request_artifact",
    ),
    pytest.param(
        lambda c: c.intelligence.get_prediction_logging_config("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/config/prediction-logging",
        id="intelligence.get_prediction_logging_config",
    ),
    pytest.param(
        lambda c: c.intelligence.get_training_configuration("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/training-configurations/..%2Fx1",
        id="intelligence.get_training_configuration",
    ),
    pytest.param(
        lambda c: c.intelligence.get_training_group("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/training-groups/..%2Fx1",
        id="intelligence.get_training_group",
    ),
    pytest.param(
        lambda c: c.intelligence.get_training_job("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/training-jobs/..%2Fx1",
        id="intelligence.get_training_job",
    ),
    pytest.param(
        lambda c: c.intelligence.get_trigger_execution("../x0", "../x1", "../x2"),
        "GET",
        f"{B}/intelligence/..%2Fx0/triggers/..%2Fx1/executions/..%2Fx2",
        id="intelligence.get_trigger_execution",
    ),
    pytest.param(
        lambda c: c.intelligence.ingest("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/execute/ingest",
        id="intelligence.ingest",
    ),
    pytest.param(
        lambda c: c.intelligence.get_lineage("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/lineage",
        id="intelligence.get_lineage",
    ),
    pytest.param(
        lambda c: c.intelligence.list_feature_views("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/features",
        id="intelligence.list_feature_views",
    ),
    pytest.param(
        lambda c: c.intelligence.list_model_families("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/model-families",
        id="intelligence.list_model_families",
    ),
    pytest.param(
        lambda c: c.intelligence.list_predictions("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/inference/predictions",
        id="intelligence.list_predictions",
    ),
    pytest.param(
        lambda c: c.intelligence.list_prediction_outcomes("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/inference/predictions/..%2Fx1/outcomes",
        id="intelligence.list_prediction_outcomes",
    ),
    pytest.param(
        lambda c: c.intelligence.list_inference_requests("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/inference/requests",
        id="intelligence.list_inference_requests",
    ),
    pytest.param(
        lambda c: c.intelligence.list_service_secrets("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/service-secrets",
        id="intelligence.list_service_secrets",
    ),
    pytest.param(
        lambda c: c.intelligence.list_training_configurations("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/training-configurations",
        id="intelligence.list_training_configurations",
    ),
    pytest.param(
        lambda c: c.intelligence.list_training_groups("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/training-groups",
        id="intelligence.list_training_groups",
    ),
    pytest.param(
        lambda c: c.intelligence.list_triggers("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/triggers",
        id="intelligence.list_triggers",
    ),
    pytest.param(
        lambda c: c.intelligence.materialize("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/materialize",
        id="intelligence.materialize",
    ),
    pytest.param(
        lambda c: c.intelligence.get_inference_request("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/inference/requests/..%2Fx1",
        id="intelligence.get_inference_request",
    ),
    pytest.param(
        lambda c: c.intelligence.register_model("../x0", {}),
        "POST",
        f"{B}/intelligence/..%2Fx0/models",
        id="intelligence.register_model",
    ),
    pytest.param(
        lambda c: c.intelligence.remove_training_group_member("../x0", "../x1", "../x2"),
        "DELETE",
        f"{B}/intelligence/..%2Fx0/training-groups/..%2Fx1/members/..%2Fx2",
        id="intelligence.remove_training_group_member",
    ),
    pytest.param(
        lambda c: c.intelligence.replace_drift_config("../x0", {}),
        "PUT",
        f"{B}/intelligence/..%2Fx0/drift/config",
        id="intelligence.replace_drift_config",
    ),
    pytest.param(
        lambda c: c.intelligence.replace_pii_config("../x0", {}),
        "PUT",
        f"{B}/intelligence/..%2Fx0/config/pii",
        id="intelligence.replace_pii_config",
    ),
    pytest.param(
        lambda c: c.intelligence.replace_prediction_logging_config("../x0", {}),
        "PUT",
        f"{B}/intelligence/..%2Fx0/config/prediction-logging",
        id="intelligence.replace_prediction_logging_config",
    ),
    pytest.param(
        lambda c: c.intelligence.replace_training_group_member("../x0", "../x1", "../x2", {}),
        "PUT",
        f"{B}/intelligence/..%2Fx0/training-groups/..%2Fx1/members/..%2Fx2",
        id="intelligence.replace_training_group_member",
    ),
    pytest.param(
        lambda c: c.intelligence.restore("../x0"),
        "POST",
        f"{B}/intelligence/..%2Fx0/restore",
        id="intelligence.restore",
    ),
    pytest.param(
        lambda c: c.intelligence.run_training_group("../x0", "../x1"),
        "POST",
        f"{B}/intelligence/..%2Fx0/training-groups/..%2Fx1/run",
        id="intelligence.run_training_group",
    ),
    pytest.param(
        lambda c: c.intelligence.sample_feature_view("../x0", "../x1"),
        "GET",
        f"{B}/intelligence/..%2Fx0/features/..%2Fx1/sample",
        id="intelligence.sample_feature_view",
    ),
    pytest.param(
        lambda c: c.intelligence.start("../x0"),
        "POST",
        f"{B}/intelligence/..%2Fx0/start",
        id="intelligence.start",
    ),
    pytest.param(
        lambda c: c.intelligence.get_status("../x0"),
        "GET",
        f"{B}/intelligence/..%2Fx0/status",
        id="intelligence.get_status",
    ),
    pytest.param(
        lambda c: c.intelligence.stop("../x0"),
        "POST",
        f"{B}/intelligence/..%2Fx0/stop",
        id="intelligence.stop",
    ),
    pytest.param(
        lambda c: c.intelligence.update_model_family("../x0", "../x1", {}),
        "PATCH",
        f"{B}/intelligence/..%2Fx0/model-families/..%2Fx1",
        id="intelligence.update_model_family",
    ),
    pytest.param(
        lambda c: c.intelligence.update_training_configuration("../x0", "../x1", {}),
        "PATCH",
        f"{B}/intelligence/..%2Fx0/training-configurations/..%2Fx1",
        id="intelligence.update_training_configuration",
    ),
    pytest.param(
        lambda c: c.intelligence.update_training_group("../x0", "../x1", {}),
        "PATCH",
        f"{B}/intelligence/..%2Fx0/training-groups/..%2Fx1",
        id="intelligence.update_training_group",
    ),
    pytest.param(
        lambda c: c.intelligence.update_trigger("../x0", "../x1", {}),
        "PATCH",
        f"{B}/intelligence/..%2Fx0/triggers/..%2Fx1",
        id="intelligence.update_trigger",
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


def test_the_table_covers_57_methods():
    assert len(_ROWS) == 57
