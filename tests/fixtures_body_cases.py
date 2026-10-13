"""Request-body cases shared by the convenience-wrapper contract tests."""

BODY_CASES = [
    (
        lambda c: c.alerts.resolve("x0", {"probe": "alerts.resolve"}),
        "POST",
        "/v1/alerts/x0/resolve",
        "alerts.resolve",
    ),
    (
        lambda c: c.billing.create_export({"probe": "billing.create_export"}),
        "POST",
        "/v1/billing/exports",
        "billing.create_export",
    ),
    (
        lambda c: c.capabilities.build_execution_graph(
            "x0", {"probe": "capabilities.build_execution_graph"}
        ),
        "POST",
        "/v1/capabilities/x0/execution-graphs/build",
        "capabilities.build_execution_graph",
    ),
    (
        lambda c: c.capabilities.build_from_config(
            "x0", "x1", {"probe": "capabilities.build_from_config"}
        ),
        "POST",
        "/v1/capabilities/x0/execution-graphs/configs/x1/build",
        "capabilities.build_from_config",
    ),
    (
        lambda c: c.capabilities.create({"probe": "capabilities.create"}),
        "POST",
        "/v1/capabilities",
        "capabilities.create",
    ),
    (
        lambda c: c.capabilities.create_graph_config(
            "x0", {"probe": "capabilities.create_graph_config"}
        ),
        "POST",
        "/v1/capabilities/x0/execution-graphs/configs",
        "capabilities.create_graph_config",
    ),
    (
        lambda c: c.capabilities.run("x0", {"probe": "capabilities.run"}),
        "POST",
        "/v1/capabilities/x0/run",
        "capabilities.run",
    ),
    (
        lambda c: c.capabilities.replace_traffic("x0", {"probe": "capabilities.replace_traffic"}),
        "PUT",
        "/v1/capabilities/x0/traffic",
        "capabilities.replace_traffic",
    ),
    (
        lambda c: c.capabilities.update("x0", {"probe": "capabilities.update"}),
        "PATCH",
        "/v1/capabilities/x0",
        "capabilities.update",
    ),
    (
        lambda c: c.capabilities.update_graph_config(
            "x0", "x1", {"probe": "capabilities.update_graph_config"}
        ),
        "PUT",
        "/v1/capabilities/x0/execution-graphs/configs/x1",
        "capabilities.update_graph_config",
    ),
    (
        lambda c: c.components.create({"probe": "components.create"}),
        "POST",
        "/v1/components",
        "components.create",
    ),
    (
        lambda c: c.components.update("x0", {"probe": "components.update"}),
        "PATCH",
        "/v1/components/x0",
        "components.update",
    ),
    (
        lambda c: c.components.validate({"probe": "components.validate"}),
        "POST",
        "/v1/components/validate",
        "components.validate",
    ),
    (
        lambda c: c.components.import_bundle({"probe": "components.import_bundle"}),
        "POST",
        "/v1/components/import",
        "components.import_bundle",
    ),
    (
        lambda c: c.infrastructure.create_nodepool({"probe": "infrastructure.create_nodepool"}),
        "POST",
        "/v1/infrastructure/cluster/nodepools",
        "infrastructure.create_nodepool",
    ),
    (
        lambda c: c.infrastructure.query_search_index(
            "x0", {"probe": "infrastructure.query_search_index"}
        ),
        "POST",
        "/v1/infrastructure/search-index/indices/x0/search",
        "infrastructure.query_search_index",
    ),
    (
        lambda c: c.infrastructure.invoke_mcp_tool(
            "x0", {"probe": "infrastructure.invoke_mcp_tool"}
        ),
        "POST",
        "/v1/infrastructure/cluster/mcp/tools/x0/invoke",
        "infrastructure.invoke_mcp_tool",
    ),
    (
        lambda c: c.infrastructure.replace_mcp_config(
            {"probe": "infrastructure.replace_mcp_config"}
        ),
        "PUT",
        "/v1/infrastructure/cluster/mcp/config",
        "infrastructure.replace_mcp_config",
    ),
    (
        lambda c: c.infrastructure.query_vector_store_collection(
            "x0", {"probe": "infrastructure.query_vector_store_collection"}
        ),
        "POST",
        "/v1/infrastructure/vector-store/collections/x0/search",
        "infrastructure.query_vector_store_collection",
    ),
    (
        lambda c: c.infrastructure.update_nodepool(
            "x0", {"probe": "infrastructure.update_nodepool"}
        ),
        "PATCH",
        "/v1/infrastructure/cluster/nodepools/x0",
        "infrastructure.update_nodepool",
    ),
    (
        lambda c: c.intelligence.create({"probe": "intelligence.create"}),
        "POST",
        "/v1/intelligence",
        "intelligence.create",
    ),
    (
        lambda c: c.intelligence.create_drift_baseline(
            "x0", {"probe": "intelligence.create_drift_baseline"}
        ),
        "POST",
        "/v1/intelligence/x0/drift/baselines",
        "intelligence.create_drift_baseline",
    ),
    (
        lambda c: c.intelligence.evaluate("x0", {"probe": "intelligence.evaluate"}),
        "POST",
        "/v1/intelligence/x0/evaluate",
        "intelligence.evaluate",
    ),
    (
        lambda c: c.intelligence.predict("x0", {"probe": "intelligence.predict"}),
        "POST",
        "/v1/intelligence/x0/inference/predict",
        "intelligence.predict",
    ),
    (
        lambda c: c.intelligence.predict_batch("x0", {"probe": "intelligence.predict_batch"}),
        "POST",
        "/v1/intelligence/x0/inference/predict/batch",
        "intelligence.predict_batch",
    ),
    (
        lambda c: c.intelligence.promote_model("x0", "x1", {"probe": "intelligence.promote_model"}),
        "POST",
        "/v1/intelligence/x0/models/x1/promote",
        "intelligence.promote_model",
    ),
    (
        lambda c: c.intelligence.train("x0", {"probe": "intelligence.train"}),
        "POST",
        "/v1/intelligence/x0/train",
        "intelligence.train",
    ),
    (
        lambda c: c.intelligence.update("x0", {"probe": "intelligence.update"}),
        "PATCH",
        "/v1/intelligence/x0",
        "intelligence.update",
    ),
    (
        lambda c: c.orchestrations.replace_node_secret_binding(
            "x0", "x1", "x2", {"probe": "orchestrations.replace_node_secret_binding"}
        ),
        "PUT",
        "/v1/orchestrations/x0/nodes/x1/secrets/x2",
        "orchestrations.replace_node_secret_binding",
    ),
    (
        lambda c: c.orchestrations.create({"probe": "orchestrations.create"}),
        "POST",
        "/v1/orchestrations",
        "orchestrations.create",
    ),
    (
        lambda c: c.orchestrations.import_bundle({"probe": "orchestrations.import_bundle"}),
        "POST",
        "/v1/orchestrations/import",
        "orchestrations.import_bundle",
    ),
    (
        lambda c: c.orchestrations.run("x0", {"probe": "orchestrations.run"}),
        "POST",
        "/v1/orchestrations/x0/run",
        "orchestrations.run",
    ),
    (
        lambda c: c.orchestrations.update("x0", {"probe": "orchestrations.update"}),
        "PATCH",
        "/v1/orchestrations/x0",
        "orchestrations.update",
    ),
    (
        lambda c: c.reviews.complete("x0", {"probe": "reviews.complete"}),
        "POST",
        "/v1/reviews/x0/complete",
        "reviews.complete",
    ),
    (
        lambda c: c.reviews.start_and_complete("x0", {"probe": "reviews.start_and_complete"}),
        "POST",
        "/v1/reviews/x0/complete",
        "reviews.start_and_complete",
    ),
    (
        lambda c: c.reviews.update("x0", {"probe": "reviews.update"}),
        "PATCH",
        "/v1/reviews/x0",
        "reviews.update",
    ),
    (lambda c: c.roles.create({"probe": "roles.create"}), "POST", "/v1/roles", "roles.create"),
    (
        lambda c: c.roles.update("x0", {"probe": "roles.update"}),
        "PATCH",
        "/v1/roles/x0",
        "roles.update",
    ),
    (
        lambda c: c.secrets.create({"probe": "secrets.create"}),
        "POST",
        "/v1/secrets",
        "secrets.create",
    ),
    (
        lambda c: c.secrets.rotate("x0", {"probe": "secrets.rotate"}),
        "POST",
        "/v1/secrets/x0/rotate",
        "secrets.rotate",
    ),
    (
        lambda c: c.secrets.update("x0", {"probe": "secrets.update"}),
        "PATCH",
        "/v1/secrets/x0",
        "secrets.update",
    ),
    (
        lambda c: c.service_accounts.create({"probe": "service_accounts.create"}),
        "POST",
        "/v1/service-accounts",
        "service_accounts.create",
    ),
    (
        lambda c: c.service_accounts.update("x0", {"probe": "service_accounts.update"}),
        "PATCH",
        "/v1/service-accounts/x0",
        "service_accounts.update",
    ),
    (
        lambda c: c.support.create_attachment("x0", {"probe": "support.create_attachment"}),
        "POST",
        "/v1/support/tickets/x0/attachments",
        "support.create_attachment",
    ),
    (
        lambda c: c.support.create_comment("x0", {"probe": "support.create_comment"}),
        "POST",
        "/v1/support/tickets/x0/comments",
        "support.create_comment",
    ),
    (
        lambda c: c.support.create({"probe": "support.create"}),
        "POST",
        "/v1/support/tickets",
        "support.create",
    ),
    (
        lambda c: c.support.update("x0", {"probe": "support.update"}),
        "PATCH",
        "/v1/support/tickets/x0",
        "support.update",
    ),
    (
        lambda c: c.triggers.create({"probe": "triggers.create"}),
        "POST",
        "/v1/triggers",
        "triggers.create",
    ),
    (
        lambda c: c.triggers.invoke("x0", {"probe": "triggers.invoke"}),
        "POST",
        "/v1/triggers/x0/invoke",
        "triggers.invoke",
    ),
    (
        lambda c: c.triggers.update("x0", {"probe": "triggers.update"}),
        "PATCH",
        "/v1/triggers/x0",
        "triggers.update",
    ),
    (
        lambda c: c.webhooks.create({"probe": "webhooks.create"}),
        "POST",
        "/v1/webhooks",
        "webhooks.create",
    ),
    (
        lambda c: c.webhooks.update("x0", {"probe": "webhooks.update"}),
        "PATCH",
        "/v1/webhooks/x0",
        "webhooks.update",
    ),
    # Access namespaces.
    (
        lambda c: c.groups.create({"probe": "groups.create"}),
        "POST",
        "/v1/groups",
        "groups.create",
    ),
    (
        lambda c: c.groups.update("x0", {"probe": "groups.update"}),
        "PATCH",
        "/v1/groups/x0",
        "groups.update",
    ),
    (
        lambda c: c.groups.update_member("x0", "x1", {"probe": "groups.update_member"}),
        "PATCH",
        "/v1/groups/x0/members/x1",
        "groups.update_member",
    ),
    (
        lambda c: c.members.invite({"probe": "members.invite"}),
        "POST",
        "/v1/members",
        "members.invite",
    ),
    (
        lambda c: c.members.update_role("x0", {"probe": "members.update_role"}),
        "PATCH",
        "/v1/members/x0",
        "members.update_role",
    ),
    # Alert channels and rules.
    (
        lambda c: c.alert_channels.create({"probe": "alert_channels.create"}),
        "POST",
        "/v1/alert-channels",
        "alert_channels.create",
    ),
    (
        lambda c: c.alert_channels.update("x0", {"probe": "alert_channels.update"}),
        "PATCH",
        "/v1/alert-channels/x0",
        "alert_channels.update",
    ),
    (
        lambda c: c.alert_rules.create({"probe": "alert_rules.create"}),
        "POST",
        "/v1/alert-rules",
        "alert_rules.create",
    ),
    (
        lambda c: c.alert_rules.update("x0", {"probe": "alert_rules.update"}),
        "PATCH",
        "/v1/alert-rules/x0",
        "alert_rules.update",
    ),
    (
        lambda c: c.alert_rules.test("x0", {"probe": "alert_rules.test"}),
        "POST",
        "/v1/alert-rules/x0/test",
        "alert_rules.test",
    ),
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
        lambda c: c.orchestrations.create_node_secret_binding(
            "x0", {"probe": "orchestrations.create_node_secret_binding"}
        ),
        "POST",
        "/v1/orchestrations/x0/node-secrets",
        "orchestrations.create_node_secret_binding",
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
