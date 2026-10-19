"""Wrapper-matrix endpoint cases, part 3: intelligence."""

from tests._fixtures_wrapper_cases_part1 import B

CASES = [
    # --- intelligence ---
    (
        lambda c: c.intelligence.activate_drift_baseline("x0", "x1"),
        "POST",
        f"{B}/intelligence/x0/drift/baselines/x1/activate",
    ),
    (
        lambda c: c.intelligence.activate_model_family("x0", "x1"),
        "POST",
        f"{B}/intelligence/x0/model-families/x1/activate",
    ),
    (
        lambda c: c.intelligence.apply_traffic_plan("x0", {}),
        "POST",
        f"{B}/intelligence/x0/traffic-plan",
    ),
    (
        lambda c: c.intelligence.attach_service_secret("x0", {}),
        "POST",
        f"{B}/intelligence/x0/service-secrets",
    ),
    (lambda c: c.intelligence.create({}), "POST", f"{B}/intelligence"),
    (
        lambda c: c.intelligence.create_drift_baseline("x0", {}),
        "POST",
        f"{B}/intelligence/x0/drift/baselines",
    ),
    (
        lambda c: c.intelligence.create_model_family("x0", {}),
        "POST",
        f"{B}/intelligence/x0/model-families",
    ),
    (
        lambda c: c.intelligence.create_training_configuration("x0", {}),
        "POST",
        f"{B}/intelligence/x0/training-configurations",
    ),
    (
        lambda c: c.intelligence.create_training_group("x0", {}),
        "POST",
        f"{B}/intelligence/x0/training-groups",
    ),
    (lambda c: c.intelligence.create_trigger("x0", {}), "POST", f"{B}/intelligence/x0/triggers"),
    (
        lambda c: c.intelligence.deactivate_model_family("x0", "x1"),
        "DELETE",
        f"{B}/intelligence/x0/model-families/x1",
    ),
    (lambda c: c.intelligence.delete("x0"), "DELETE", f"{B}/intelligence/x0"),
    (
        lambda c: c.intelligence.delete_drift_baseline("x0", "x1"),
        "DELETE",
        f"{B}/intelligence/x0/drift/baselines/x1",
    ),
    (lambda c: c.intelligence.delete_model("x0", "x1"), "DELETE", f"{B}/intelligence/x0/models/x1"),
    (
        lambda c: c.intelligence.delete_training_configuration("x0", "x1"),
        "DELETE",
        f"{B}/intelligence/x0/training-configurations/x1",
    ),
    (
        lambda c: c.intelligence.delete_training_group("x0", "x1"),
        "DELETE",
        f"{B}/intelligence/x0/training-groups/x1",
    ),
    (
        lambda c: c.intelligence.delete_trigger("x0", "x1"),
        "DELETE",
        f"{B}/intelligence/x0/triggers/x1",
    ),
    (
        lambda c: c.intelligence.delete_version("x0", "x1"),
        "DELETE",
        f"{B}/intelligence/x0/versions/x1",
    ),
    (
        lambda c: c.intelligence.detach_service_secret("x0", "x1", "x2"),
        "DELETE",
        f"{B}/intelligence/x0/service-secrets/x1/x2",
    ),
    (
        lambda c: c.intelligence.list_drift_baselines("x0"),
        "GET",
        f"{B}/intelligence/x0/drift/baselines",
    ),
    (lambda c: c.intelligence.evaluate("x0"), "POST", f"{B}/intelligence/x0/evaluate"),
    (lambda c: c.intelligence.export_bundle("x0"), "GET", f"{B}/intelligence/x0/export"),
    (lambda c: c.intelligence.get("x0"), "GET", f"{B}/intelligence/x0"),
    (
        lambda c: c.intelligence.get_drift_baseline("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/drift/baselines/x1",
    ),
    (lambda c: c.intelligence.get_drift_config("x0"), "GET", f"{B}/intelligence/x0/drift/config"),
    (
        lambda c: c.intelligence.get_feature_view("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/features/x1",
    ),
    (lambda c: c.intelligence.get_model("x0", "x1"), "GET", f"{B}/intelligence/x0/models/x1"),
    (
        lambda c: c.intelligence.get_model_family("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/model-families/x1",
    ),
    (lambda c: c.intelligence.get_pii_config("x0"), "GET", f"{B}/intelligence/x0/config/pii"),
    (
        lambda c: c.intelligence.get_inference_request_artifact("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/inference/requests/x1/artifact",
    ),
    (
        lambda c: c.intelligence.get_prediction_logging_config("x0"),
        "GET",
        f"{B}/intelligence/x0/config/prediction-logging",
    ),
    (
        lambda c: c.intelligence.get_training_configuration("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/training-configurations/x1",
    ),
    (
        lambda c: c.intelligence.get_training_group("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/training-groups/x1",
    ),
    (
        lambda c: c.intelligence.get_training_job("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/training-jobs/x1",
    ),
    (
        lambda c: c.intelligence.get_trigger_execution("x0", "x1", "x2"),
        "GET",
        f"{B}/intelligence/x0/triggers/x1/executions/x2",
    ),
    (lambda c: c.intelligence.import_bundle({}), "POST", f"{B}/intelligence/import"),
    (lambda c: c.intelligence.ingest("x0", {}), "POST", f"{B}/intelligence/x0/execute/ingest"),
    (lambda c: c.intelligence.get_lineage("x0"), "GET", f"{B}/intelligence/x0/lineage"),
    (lambda c: c.intelligence.list(), "GET", f"{B}/intelligence"),
    (lambda c: c.intelligence.list_feature_views("x0"), "GET", f"{B}/intelligence/x0/features"),
    (
        lambda c: c.intelligence.list_model_families("x0"),
        "GET",
        f"{B}/intelligence/x0/model-families",
    ),
    (lambda c: c.intelligence.list_models("x0"), "GET", f"{B}/intelligence/x0/models"),
    (
        lambda c: c.intelligence.list_predictions("x0"),
        "GET",
        f"{B}/intelligence/x0/inference/predictions",
    ),
    (
        lambda c: c.intelligence.list_prediction_outcomes("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/inference/predictions/x1/outcomes",
    ),
    (
        lambda c: c.intelligence.list_inference_requests("x0"),
        "GET",
        f"{B}/intelligence/x0/inference/requests",
    ),
    (
        lambda c: c.intelligence.list_service_secrets("x0"),
        "GET",
        f"{B}/intelligence/x0/service-secrets",
    ),
    (
        lambda c: c.intelligence.list_training_configurations("x0"),
        "GET",
        f"{B}/intelligence/x0/training-configurations",
    ),
    (
        lambda c: c.intelligence.list_training_groups("x0"),
        "GET",
        f"{B}/intelligence/x0/training-groups",
    ),
    (lambda c: c.intelligence.list_triggers("x0"), "GET", f"{B}/intelligence/x0/triggers"),
    (lambda c: c.intelligence.materialize("x0", {}), "POST", f"{B}/intelligence/x0/materialize"),
    (lambda c: c.intelligence.predict("x0", {}), "POST", f"{B}/intelligence/x0/inference/predict"),
    (
        lambda c: c.intelligence.predict_batch("x0", {}),
        "POST",
        f"{B}/intelligence/x0/inference/predict/batch",
    ),
    (
        lambda c: c.intelligence.promote_model("x0", "x1"),
        "POST",
        f"{B}/intelligence/x0/models/x1/promote",
    ),
    (
        lambda c: c.intelligence.get_inference_request("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/inference/requests/x1",
    ),
    (lambda c: c.intelligence.register_model("x0", {}), "POST", f"{B}/intelligence/x0/models"),
    (
        lambda c: c.intelligence.remove_training_group_member("x0", "x1", "x2"),
        "DELETE",
        f"{B}/intelligence/x0/training-groups/x1/members/x2",
    ),
    (
        lambda c: c.intelligence.replace_drift_config("x0", {}),
        "PUT",
        f"{B}/intelligence/x0/drift/config",
    ),
    (
        lambda c: c.intelligence.replace_pii_config("x0", {}),
        "PUT",
        f"{B}/intelligence/x0/config/pii",
    ),
    (
        lambda c: c.intelligence.replace_prediction_logging_config("x0", {}),
        "PUT",
        f"{B}/intelligence/x0/config/prediction-logging",
    ),
    (
        lambda c: c.intelligence.replace_training_group_member("x0", "x1", "x2", {}),
        "PUT",
        f"{B}/intelligence/x0/training-groups/x1/members/x2",
    ),
    (lambda c: c.intelligence.restore("x0"), "POST", f"{B}/intelligence/x0/restore"),
    (
        lambda c: c.intelligence.retire_model("x0", "x1"),
        "POST",
        f"{B}/intelligence/x0/models/x1/retire",
    ),
    (
        lambda c: c.intelligence.run_training_group("x0", "x1"),
        "POST",
        f"{B}/intelligence/x0/training-groups/x1/run",
    ),
    (
        lambda c: c.intelligence.sample_feature_view("x0", "x1"),
        "GET",
        f"{B}/intelligence/x0/features/x1/sample",
    ),
    (lambda c: c.intelligence.start("x0"), "POST", f"{B}/intelligence/x0/start"),
    (lambda c: c.intelligence.get_status("x0"), "GET", f"{B}/intelligence/x0/status"),
    (lambda c: c.intelligence.stop("x0"), "POST", f"{B}/intelligence/x0/stop"),
    (lambda c: c.intelligence.train("x0"), "POST", f"{B}/intelligence/x0/train"),
    (lambda c: c.intelligence.update("x0", {}), "PATCH", f"{B}/intelligence/x0"),
    (
        lambda c: c.intelligence.update_model_family("x0", "x1", {}),
        "PATCH",
        f"{B}/intelligence/x0/model-families/x1",
    ),
    (
        lambda c: c.intelligence.update_training_configuration("x0", "x1", {}),
        "PATCH",
        f"{B}/intelligence/x0/training-configurations/x1",
    ),
    (
        lambda c: c.intelligence.update_training_group("x0", "x1", {}),
        "PATCH",
        f"{B}/intelligence/x0/training-groups/x1",
    ),
    (
        lambda c: c.intelligence.update_trigger("x0", "x1", {}),
        "PATCH",
        f"{B}/intelligence/x0/triggers/x1",
    ),
]
