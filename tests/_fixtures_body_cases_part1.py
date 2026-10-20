"""Request-body cases, part 1: alerts through alert rules."""

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
]
