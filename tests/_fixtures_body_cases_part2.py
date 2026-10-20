"""Request-body cases, part 2: intelligence through threads."""

BODY_CASES = [
    # Intelligence serving.
    (
        lambda c: c.intelligence.apply_traffic_plan(
            "x0", {"probe": "intelligence.apply_traffic_plan"}
        ),
        "POST",
        "/v1/intelligence/x0/traffic-plan",
        "intelligence.apply_traffic_plan",
    ),
    (
        lambda c: c.intelligence.create_model_family(
            "x0", {"probe": "intelligence.create_model_family"}
        ),
        "POST",
        "/v1/intelligence/x0/model-families",
        "intelligence.create_model_family",
    ),
    (
        lambda c: c.intelligence.import_bundle({"probe": "intelligence.import_bundle"}),
        "POST",
        "/v1/intelligence/import",
        "intelligence.import_bundle",
    ),
    (
        lambda c: c.intelligence.register_model("x0", {"probe": "intelligence.register_model"}),
        "POST",
        "/v1/intelligence/x0/models",
        "intelligence.register_model",
    ),
    (
        lambda c: c.intelligence.replace_drift_config(
            "x0", {"probe": "intelligence.replace_drift_config"}
        ),
        "PUT",
        "/v1/intelligence/x0/drift/config",
        "intelligence.replace_drift_config",
    ),
    (
        lambda c: c.intelligence.start("x0", {"probe": "intelligence.start"}),
        "POST",
        "/v1/intelligence/x0/start",
        "intelligence.start",
    ),
    (
        lambda c: c.intelligence.stop("x0", {"probe": "intelligence.stop"}),
        "POST",
        "/v1/intelligence/x0/stop",
        "intelligence.stop",
    ),
    (
        lambda c: c.intelligence.update_model_family(
            "x0", "x1", {"probe": "intelligence.update_model_family"}
        ),
        "PATCH",
        "/v1/intelligence/x0/model-families/x1",
        "intelligence.update_model_family",
    ),
    # Intelligence training and data.
    (
        lambda c: c.intelligence.attach_service_secret(
            "x0", {"probe": "intelligence.attach_service_secret"}
        ),
        "POST",
        "/v1/intelligence/x0/service-secrets",
        "intelligence.attach_service_secret",
    ),
    (
        lambda c: c.intelligence.create_training_configuration(
            "x0", {"probe": "intelligence.create_training_configuration"}
        ),
        "POST",
        "/v1/intelligence/x0/training-configurations",
        "intelligence.create_training_configuration",
    ),
    (
        lambda c: c.intelligence.create_training_group(
            "x0", {"probe": "intelligence.create_training_group"}
        ),
        "POST",
        "/v1/intelligence/x0/training-groups",
        "intelligence.create_training_group",
    ),
    (
        lambda c: c.intelligence.create_trigger("x0", {"probe": "intelligence.create_trigger"}),
        "POST",
        "/v1/intelligence/x0/triggers",
        "intelligence.create_trigger",
    ),
    (
        lambda c: c.intelligence.ingest("x0", {"probe": "intelligence.ingest"}),
        "POST",
        "/v1/intelligence/x0/execute/ingest",
        "intelligence.ingest",
    ),
    (
        lambda c: c.intelligence.materialize("x0", {"probe": "intelligence.materialize"}),
        "POST",
        "/v1/intelligence/x0/materialize",
        "intelligence.materialize",
    ),
    (
        lambda c: c.intelligence.replace_pii_config(
            "x0", {"probe": "intelligence.replace_pii_config"}
        ),
        "PUT",
        "/v1/intelligence/x0/config/pii",
        "intelligence.replace_pii_config",
    ),
    (
        lambda c: c.intelligence.replace_prediction_logging_config(
            "x0", {"probe": "intelligence.replace_prediction_logging_config"}
        ),
        "PUT",
        "/v1/intelligence/x0/config/prediction-logging",
        "intelligence.replace_prediction_logging_config",
    ),
    (
        lambda c: c.intelligence.replace_training_group_member(
            "x0", "x1", "x2", {"probe": "intelligence.replace_training_group_member"}
        ),
        "PUT",
        "/v1/intelligence/x0/training-groups/x1/members/x2",
        "intelligence.replace_training_group_member",
    ),
    (
        lambda c: c.intelligence.update_training_configuration(
            "x0", "x1", {"probe": "intelligence.update_training_configuration"}
        ),
        "PATCH",
        "/v1/intelligence/x0/training-configurations/x1",
        "intelligence.update_training_configuration",
    ),
    (
        lambda c: c.intelligence.update_training_group(
            "x0", "x1", {"probe": "intelligence.update_training_group"}
        ),
        "PATCH",
        "/v1/intelligence/x0/training-groups/x1",
        "intelligence.update_training_group",
    ),
    (
        lambda c: c.intelligence.update_trigger(
            "x0", "x1", {"probe": "intelligence.update_trigger"}
        ),
        "PATCH",
        "/v1/intelligence/x0/triggers/x1",
        "intelligence.update_trigger",
    ),
    # Orchestrations and components.
    (
        lambda c: c.components.replace_artifact("x0", {"probe": "components.replace_artifact"}),
        "PUT",
        "/v1/components/x0/artifact",
        "components.replace_artifact",
    ),
    (
        lambda c: c.components.run("x0", {"probe": "components.run"}),
        "POST",
        "/v1/components/x0/run",
        "components.run",
    ),
    (
        lambda c: c.orchestrations.assign_capability(
            "x0", {"probe": "orchestrations.assign_capability"}
        ),
        "POST",
        "/v1/orchestrations/x0/assign-capability",
        "orchestrations.assign_capability",
    ),
    (
        lambda c: c.orchestrations.copy("x0", {"probe": "orchestrations.copy"}),
        "POST",
        "/v1/orchestrations/x0/copy",
        "orchestrations.copy",
    ),
    (
        lambda c: c.orchestrations.create_draft({"probe": "orchestrations.create_draft"}),
        "POST",
        "/v1/orchestrations/drafts",
        "orchestrations.create_draft",
    ),
    (
        lambda c: c.orchestrations.publish_draft("x0", {"probe": "orchestrations.publish_draft"}),
        "POST",
        "/v1/orchestrations/drafts/x0/publish",
        "orchestrations.publish_draft",
    ),
    (
        lambda c: c.orchestrations.update_draft("x0", {"probe": "orchestrations.update_draft"}),
        "PATCH",
        "/v1/orchestrations/drafts/x0",
        "orchestrations.update_draft",
    ),
    (
        lambda c: c.orchestrations.validate({"probe": "orchestrations.validate"}),
        "POST",
        "/v1/orchestrations/validate",
        "orchestrations.validate",
    ),
    # Capabilities, assets and experiments.
    (
        lambda c: c.assets.copy("x0", {"probe": "assets.copy"}),
        "POST",
        "/v1/assets/x0/copy",
        "assets.copy",
    ),
    (
        lambda c: c.assets.import_bundle({"probe": "assets.import_bundle"}),
        "POST",
        "/v1/assets/import",
        "assets.import_bundle",
    ),
    (
        lambda c: c.capabilities.apply_traffic_plan(
            "x0", {"probe": "capabilities.apply_traffic_plan"}
        ),
        "POST",
        "/v1/capabilities/x0/traffic-plan",
        "capabilities.apply_traffic_plan",
    ),
    (
        lambda c: c.capabilities.copy("x0", {"probe": "capabilities.copy"}),
        "POST",
        "/v1/capabilities/x0/copy",
        "capabilities.copy",
    ),
    (
        lambda c: c.capabilities.create_trigger("x0", {"probe": "capabilities.create_trigger"}),
        "POST",
        "/v1/capabilities/x0/triggers",
        "capabilities.create_trigger",
    ),
    (
        lambda c: c.capabilities.replace_evaluation_config(
            "x0", {"probe": "capabilities.replace_evaluation_config"}
        ),
        "PUT",
        "/v1/capabilities/x0/evaluation-config",
        "capabilities.replace_evaluation_config",
    ),
    (
        lambda c: c.capabilities.update_trigger(
            "x0", "x1", {"probe": "capabilities.update_trigger"}
        ),
        "PATCH",
        "/v1/capabilities/x0/triggers/x1",
        "capabilities.update_trigger",
    ),
    (
        lambda c: c.experiments.create({"probe": "experiments.create"}),
        "POST",
        "/v1/experiments",
        "experiments.create",
    ),
    (
        lambda c: c.experiments.update("x0", {"probe": "experiments.update"}),
        "PATCH",
        "/v1/experiments/x0",
        "experiments.update",
    ),
    # Infrastructure.
    (
        lambda c: c.infrastructure.create_managed_service_backup(
            "x0", {"probe": "infrastructure.create_managed_service_backup"}
        ),
        "POST",
        "/v1/infrastructure/managed/x0/backups",
        "infrastructure.create_managed_service_backup",
    ),
    (
        lambda c: c.infrastructure.scale_nodepool("x0", {"probe": "infrastructure.scale_nodepool"}),
        "POST",
        "/v1/infrastructure/cluster/nodepools/x0/scale",
        "infrastructure.scale_nodepool",
    ),
    (
        lambda c: c.infrastructure.create_search_index(
            {"probe": "infrastructure.create_search_index"}
        ),
        "POST",
        "/v1/infrastructure/search-index/indices",
        "infrastructure.create_search_index",
    ),
    (
        lambda c: c.infrastructure.add_search_index_document(
            "x0", {"probe": "infrastructure.add_search_index_document"}
        ),
        "POST",
        "/v1/infrastructure/search-index/indices/x0/documents",
        "infrastructure.add_search_index_document",
    ),
    (
        lambda c: c.infrastructure.update_managed_service(
            "x0", {"probe": "infrastructure.update_managed_service"}
        ),
        "PATCH",
        "/v1/infrastructure/managed/x0",
        "infrastructure.update_managed_service",
    ),
    (
        lambda c: c.infrastructure.update_cluster_service(
            "x0", {"probe": "infrastructure.update_cluster_service"}
        ),
        "PATCH",
        "/v1/infrastructure/cluster/x0",
        "infrastructure.update_cluster_service",
    ),
    (
        lambda c: c.infrastructure.create_vector_store_collection(
            {"probe": "infrastructure.create_vector_store_collection"}
        ),
        "POST",
        "/v1/infrastructure/vector-store/collections",
        "infrastructure.create_vector_store_collection",
    ),
    (
        lambda c: c.infrastructure.add_vector_store_entities(
            "x0", {"probe": "infrastructure.add_vector_store_entities"}
        ),
        "POST",
        "/v1/infrastructure/vector-store/collections/x0/entities",
        "infrastructure.add_vector_store_entities",
    ),
    # Files, messaging, reviews and support.
    (
        lambda c: c.files.copy("x0", {"probe": "files.copy"}),
        "POST",
        "/v1/files/entries/x0/copy",
        "files.copy",
    ),
    (
        lambda c: c.files.create_entry("x0", {"probe": "files.create_entry"}),
        "POST",
        "/v1/files/spaces/x0/entries",
        "files.create_entry",
    ),
    (
        lambda c: c.files.create_space({"probe": "files.create_space"}),
        "POST",
        "/v1/files/spaces",
        "files.create_space",
    ),
    (
        lambda c: c.files.create_upload_url({"probe": "files.create_upload_url"}),
        "POST",
        "/v1/files/upload-url",
        "files.create_upload_url",
    ),
    (
        lambda c: c.files.move("x0", {"probe": "files.move"}),
        "POST",
        "/v1/files/entries/x0/move",
        "files.move",
    ),
    (
        lambda c: c.files.restore_entries({"probe": "files.restore_entries"}),
        "POST",
        "/v1/files/trash/restore",
        "files.restore_entries",
    ),
    (
        lambda c: c.files.update_entry("x0", {"probe": "files.update_entry"}),
        "PATCH",
        "/v1/files/entries/x0",
        "files.update_entry",
    ),
    (
        lambda c: c.files.update_space("x0", {"probe": "files.update_space"}),
        "PATCH",
        "/v1/files/spaces/x0",
        "files.update_space",
    ),
    (
        lambda c: c.reviews.assign("x0", {"probe": "reviews.assign"}),
        "POST",
        "/v1/reviews/x0/assign",
        "reviews.assign",
    ),
    (
        lambda c: c.reviews.save_draft("x0", {"probe": "reviews.save_draft"}),
        "PUT",
        "/v1/reviews/x0/draft",
        "reviews.save_draft",
    ),
    (
        lambda c: c.threads.add_participant("x0", {"probe": "threads.add_participant"}),
        "POST",
        "/v1/threads/x0/participants",
        "threads.add_participant",
    ),
    (
        lambda c: c.threads.create({"probe": "threads.create"}),
        "POST",
        "/v1/threads",
        "threads.create",
    ),
    (
        lambda c: c.threads.create_message("x0", {"probe": "threads.create_message"}),
        "POST",
        "/v1/threads/x0/messages",
        "threads.create_message",
    ),
    (
        lambda c: c.threads.update("x0", {"probe": "threads.update"}),
        "PATCH",
        "/v1/threads/x0",
        "threads.update",
    ),
]
