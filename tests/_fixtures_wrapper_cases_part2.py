"""Wrapper-matrix endpoint cases, part 2: infrastructure."""

from tests._fixtures_wrapper_cases_part1 import B

CASES = [
    # --- infrastructure ---
    # The *_ingest and *_import methods are multipart; their request shapes are
    # pinned in tests/test_store_ingest.py and tests/test_infrastructure_services_stores.py.
    (
        lambda c: c.infrastructure.ingest_cache("x0", "x1.txt", b"x2"),
        "POST",
        f"{B}/infrastructure/cache/ingest",
    ),
    (lambda c: c.infrastructure.get_cache_key("x0"), "GET", f"{B}/infrastructure/cache/keys/x0"),
    (lambda c: c.infrastructure.list_cache_keys(), "GET", f"{B}/infrastructure/cache/keys"),
    (lambda c: c.infrastructure.get_capacity(), "GET", f"{B}/infrastructure/capacity"),
    (lambda c: c.infrastructure.list_cluster_services(), "GET", f"{B}/infrastructure/cluster"),
    (
        lambda c: c.infrastructure.create_managed_service_backup("x0"),
        "POST",
        f"{B}/infrastructure/managed/x0/backups",
    ),
    (
        lambda c: c.infrastructure.create_nodepool({}),
        "POST",
        f"{B}/infrastructure/cluster/nodepools",
    ),
    (lambda c: c.infrastructure.get_database("x0"), "GET", f"{B}/infrastructure/databases/x0"),
    (
        lambda c: c.infrastructure.delete_nodepool("x0"),
        "DELETE",
        f"{B}/infrastructure/cluster/nodepools/x0",
    ),
    (lambda c: c.infrastructure.get(), "GET", f"{B}/infrastructure"),
    (lambda c: c.infrastructure.get_managed_service("x0"), "GET", f"{B}/infrastructure/managed/x0"),
    (
        lambda c: c.infrastructure.get_managed_service_backup("x0", "x1"),
        "GET",
        f"{B}/infrastructure/managed/x0/backups/x1",
    ),
    (
        lambda c: c.infrastructure.list_managed_service_backups("x0"),
        "GET",
        f"{B}/infrastructure/managed/x0/backups",
    ),
    (lambda c: c.infrastructure.list_managed_services(), "GET", f"{B}/infrastructure/managed"),
    (lambda c: c.infrastructure.get_mcp_config(), "GET", f"{B}/infrastructure/cluster/mcp/config"),
    (
        lambda c: c.infrastructure.invoke_mcp_tool("x0"),
        "POST",
        f"{B}/infrastructure/cluster/mcp/tools/x0/invoke",
    ),
    (lambda c: c.infrastructure.list_mcp_tools(), "GET", f"{B}/infrastructure/cluster/mcp/tools"),
    (
        lambda c: c.infrastructure.replace_mcp_config({}),
        "PUT",
        f"{B}/infrastructure/cluster/mcp/config",
    ),
    (
        lambda c: c.infrastructure.get_nodepool("x0"),
        "GET",
        f"{B}/infrastructure/cluster/nodepools/x0",
    ),
    (lambda c: c.infrastructure.list_nodepools(), "GET", f"{B}/infrastructure/cluster/nodepools"),
    (
        lambda c: c.infrastructure.record_database_activity("x0"),
        "POST",
        f"{B}/infrastructure/databases/x0/activity",
    ),
    (
        lambda c: c.infrastructure.scale_nodepool("x0", {}),
        "POST",
        f"{B}/infrastructure/cluster/nodepools/x0/scale",
    ),
    (
        lambda c: c.infrastructure.create_search_index({}),
        "POST",
        f"{B}/infrastructure/search-index/indices",
    ),
    (
        lambda c: c.infrastructure.delete_search_index("x0"),
        "DELETE",
        f"{B}/infrastructure/search-index/indices/x0",
    ),
    (
        lambda c: c.infrastructure.delete_search_index_document("x0", "x1"),
        "DELETE",
        f"{B}/infrastructure/search-index/indices/x0/documents/x1",
    ),
    (
        lambda c: c.infrastructure.list_search_index_documents("x0"),
        "GET",
        f"{B}/infrastructure/search-index/indices/x0/documents",
    ),
    (
        lambda c: c.infrastructure.export_search_index("x0"),
        "POST",
        f"{B}/infrastructure/search-index/indices/x0/export",
    ),
    (
        lambda c: c.infrastructure.import_search_index("x0", b"x1"),
        "POST",
        f"{B}/infrastructure/search-index/indices/x0/import",
    ),
    (
        lambda c: c.infrastructure.get_search_index("x0"),
        "GET",
        f"{B}/infrastructure/search-index/indices/x0",
    ),
    (
        lambda c: c.infrastructure.list_search_indices(),
        "GET",
        f"{B}/infrastructure/search-index/indices",
    ),
    (
        lambda c: c.infrastructure.ingest_search_index("x0", "x1.txt", b"x2"),
        "POST",
        f"{B}/infrastructure/search-index/indices/x0/ingest",
    ),
    (
        lambda c: c.infrastructure.add_search_index_document("x0", {}),
        "POST",
        f"{B}/infrastructure/search-index/indices/x0/documents",
    ),
    (
        lambda c: c.infrastructure.query_search_index("x0", {}),
        "POST",
        f"{B}/infrastructure/search-index/indices/x0/search",
    ),
    (lambda c: c.infrastructure.get_cluster_service("x0"), "GET", f"{B}/infrastructure/cluster/x0"),
    (
        lambda c: c.infrastructure.start_database("x0"),
        "POST",
        f"{B}/infrastructure/databases/x0/start",
    ),
    (
        lambda c: c.infrastructure.start_managed_service("x0"),
        "POST",
        f"{B}/infrastructure/managed/x0/start",
    ),
    (
        lambda c: c.infrastructure.start_cluster_service("x0"),
        "POST",
        f"{B}/infrastructure/cluster/x0/start",
    ),
    (
        lambda c: c.infrastructure.stop_managed_service("x0"),
        "POST",
        f"{B}/infrastructure/managed/x0/stop",
    ),
    (
        lambda c: c.infrastructure.stop_cluster_service("x0"),
        "POST",
        f"{B}/infrastructure/cluster/x0/stop",
    ),
    (
        lambda c: c.infrastructure.update_managed_service("x0", {}),
        "PATCH",
        f"{B}/infrastructure/managed/x0",
    ),
    (
        lambda c: c.infrastructure.update_nodepool("x0", {}),
        "PATCH",
        f"{B}/infrastructure/cluster/nodepools/x0",
    ),
    (
        lambda c: c.infrastructure.update_cluster_service("x0", {}),
        "PATCH",
        f"{B}/infrastructure/cluster/x0",
    ),
    (
        lambda c: c.infrastructure.get_vector_store_collection("x0"),
        "GET",
        f"{B}/infrastructure/vector-store/collections/x0",
    ),
    (
        lambda c: c.infrastructure.list_vector_store_collections(),
        "GET",
        f"{B}/infrastructure/vector-store/collections",
    ),
    (
        lambda c: c.infrastructure.create_vector_store_collection({}),
        "POST",
        f"{B}/infrastructure/vector-store/collections",
    ),
    (
        lambda c: c.infrastructure.delete_vector_store_collection("x0"),
        "DELETE",
        f"{B}/infrastructure/vector-store/collections/x0",
    ),
    (
        lambda c: c.infrastructure.delete_vector_store_entity("x0", "x1"),
        "DELETE",
        f"{B}/infrastructure/vector-store/collections/x0/entities/x1",
    ),
    (
        lambda c: c.infrastructure.list_vector_store_entities("x0"),
        "GET",
        f"{B}/infrastructure/vector-store/collections/x0/entities",
    ),
    (
        lambda c: c.infrastructure.export_vector_store_collection("x0"),
        "POST",
        f"{B}/infrastructure/vector-store/collections/x0/export",
    ),
    (
        lambda c: c.infrastructure.import_vector_store_collection("x0", b"x1"),
        "POST",
        f"{B}/infrastructure/vector-store/collections/x0/import",
    ),
    (
        lambda c: c.infrastructure.ingest_vector_store_collection("x0", "x1.txt", b"x2"),
        "POST",
        f"{B}/infrastructure/vector-store/collections/x0/ingest",
    ),
    (
        lambda c: c.infrastructure.add_vector_store_entities("x0", {}),
        "POST",
        f"{B}/infrastructure/vector-store/collections/x0/entities",
    ),
    (
        lambda c: c.infrastructure.query_vector_store_collection("x0", {}),
        "POST",
        f"{B}/infrastructure/vector-store/collections/x0/search",
    ),
]
