"""Wrapper-matrix endpoint cases, part 5: ingest jobs and batch uploads."""

from tests._fixtures_wrapper_cases_part1 import B

VS = f"{B}/infrastructure/vector-store/collections/x0/ingest-jobs"
SI = f"{B}/infrastructure/search-index/indices/x0/ingest-jobs"

CASES = [
    (lambda c: c.infrastructure.create_vector_store_ingest_job("x0", {}), "POST", VS),
    (lambda c: c.infrastructure.list_vector_store_ingest_jobs("x0"), "GET", VS),
    (lambda c: c.infrastructure.get_vector_store_ingest_job("x0", "x1"), "GET", f"{VS}/x1"),
    (
        lambda c: c.infrastructure.list_vector_store_ingest_job_files("x0", "x1"),
        "GET",
        f"{VS}/x1/files",
    ),
    (
        lambda c: c.infrastructure.cancel_vector_store_ingest_job("x0", "x1"),
        "POST",
        f"{VS}/x1/cancel",
    ),
    (
        lambda c: c.infrastructure.resume_vector_store_ingest_job("x0", "x1", version=3),
        "POST",
        f"{VS}/x1/resume",
    ),
    (lambda c: c.infrastructure.create_search_index_ingest_job("x0", {}), "POST", SI),
    (lambda c: c.infrastructure.list_search_index_ingest_jobs("x0"), "GET", SI),
    (lambda c: c.infrastructure.get_search_index_ingest_job("x0", "x1"), "GET", f"{SI}/x1"),
    (
        lambda c: c.infrastructure.list_search_index_ingest_job_files("x0", "x1"),
        "GET",
        f"{SI}/x1/files",
    ),
    (
        lambda c: c.infrastructure.cancel_search_index_ingest_job("x0", "x1"),
        "POST",
        f"{SI}/x1/cancel",
    ),
    (
        lambda c: c.infrastructure.resume_search_index_ingest_job("x0", "x1", version=3),
        "POST",
        f"{SI}/x1/resume",
    ),
    (lambda c: c.files.create_upload_urls({}), "POST", f"{B}/files/upload-urls"),
    (lambda c: c.files.register_entries("x0", {}), "POST", f"{B}/files/spaces/x0/entries/batch"),
]
