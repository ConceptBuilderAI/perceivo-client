"""Run-log time windows, execution-lock documentation, file sort keys and the
evaluation-run answers, held to what the API reads and sends.

* ``runs.logs`` takes the same window arguments as ``query.logs`` (``start``,
  ``end``) and sends them as the ``from``/``to`` the run-logs route reads; it
  takes no free-form keywords, so a misspelt parameter fails before sending.
* A ``429`` execution lock raises :class:`PerceivoExecutionLockedError`, and the
  methods that can meet one say so.
* ``files.list_entries`` documents only the sort keys the platform honours.
* ``capabilities.list_evaluations`` answers ``{items, total}`` and
  ``capabilities.get_evaluation`` names the run ``evaluation_id``.
"""

from __future__ import annotations

import asyncio
import inspect

import pytest

from perceivo_client import PerceivoExecutionLockedError, PerceivoRateLimitError
from perceivo_client.resources import capabilities as capabilities_module
from perceivo_client.resources.capabilities import (
    CapabilitiesResource,
    EvaluationRun,
    EvaluationRunPage,
    EvaluationRunStatus,
)
from perceivo_client.resources.files import FilesResource
from perceivo_client.resources.query import QueryResource
from perceivo_client.resources.runs import RunLogPage, RunsResource
from tests.conftest import json_handler, make_client
from tests.test_pagination_and_async import _async_from_sync

_RUN_LOGS = {"workload_id": "wl-1", "entries": [], "count": 0, "limit": 100}

# --- runs.logs: explicit window arguments, sent under the route's names -------


def test_run_logs_send_the_window_as_from_and_to():
    client, rec = make_client(json_handler(_RUN_LOGS))

    client.runs.logs(
        "run-1",
        channel="error",
        start="2026-10-01T00:00:00Z",
        end="2026-10-02T00:00:00Z",
        limit=50,
        order="oldest_first",
    )

    assert rec.last.url.path == "/v1/logs"
    assert sorted(rec.last.url.params.multi_items()) == [
        ("channel", "error"),
        ("from", "2026-10-01T00:00:00Z"),
        ("limit", "50"),
        ("order", "oldest_first"),
        ("scope", "run"),
        ("scope_id", "run-1"),
        ("to", "2026-10-02T00:00:00Z"),
    ]


def test_run_logs_without_arguments_send_only_the_scope():
    client, rec = make_client(json_handler(_RUN_LOGS))

    got = client.runs.logs("run-1")

    assert isinstance(got, RunLogPage)
    assert sorted(rec.last.url.params.multi_items()) == [("scope", "run"), ("scope_id", "run-1")]


def test_run_logs_send_the_same_query_as_query_logs_for_the_run_scope():
    window = {"channel": "error", "start": "1", "end": "2", "limit": 5, "order": "newest_first"}
    client, rec = make_client(json_handler(_RUN_LOGS))

    client.runs.logs("run-1", **window)
    by_runs = sorted(rec.last.url.params.multi_items())
    client.query.logs("run", scope_id="run-1", **window)
    by_query = sorted(rec.last.url.params.multi_items())

    assert by_runs == by_query


@pytest.mark.parametrize("name", ["from", "to", "scope", "scope_id", "probe_key"])
def test_run_logs_refuse_a_keyword_they_do_not_declare_before_sending(name):
    client, rec = make_client(json_handler(_RUN_LOGS))
    kwargs = {name: "x"}

    with pytest.raises(TypeError, match=name):
        client.runs.logs("run-1", **kwargs)
    assert rec.requests == []


def test_run_logs_take_the_run_scope_arguments_of_query_logs_and_no_free_keywords():
    runs = inspect.signature(RunsResource.logs).parameters
    query = inspect.signature(QueryResource.logs).parameters

    assert all(p.kind is not inspect.Parameter.VAR_KEYWORD for p in runs.values())
    assert set(runs) - {"self", "run_id"} == {"channel", "start", "end", "limit", "order"}
    assert set(runs) - {"self", "run_id"} <= set(query)


def test_run_logs_refuse_an_empty_run_id_before_sending():
    client, rec = make_client(json_handler(_RUN_LOGS))

    with pytest.raises(ValueError, match="run_id must not be empty"):
        client.runs.logs("")
    assert rec.requests == []


def test_run_logs_from_the_async_client_send_the_window():
    sync, rec = make_client(json_handler(_RUN_LOGS))

    asyncio.run(_async_from_sync(sync).runs.logs("run-1", start="a", end="b"))

    assert rec.last.url.params["from"] == "a"
    assert rec.last.url.params["to"] == "b"


# --- runs.list: explicit paging arguments --------------------------------------


def test_runs_list_send_status_and_paging_under_their_wire_names():
    client, rec = make_client(json_handler({"items": [], "total": 0}))

    client.runs.list(status="RUNNING", page=2, page_size=10)

    assert rec.last.url.path == "/v1/orchestrations/runs"
    assert sorted(rec.last.url.params.multi_items()) == [
        ("filter[status]", "RUNNING"),
        ("page", "2"),
        ("page_size", "10"),
    ]


def test_runs_list_without_arguments_send_no_query():
    client, rec = make_client(json_handler({"items": [], "total": 0}))

    client.runs.list()

    assert rec.last.url.query == b""


def test_runs_list_refuse_an_undeclared_keyword_before_sending():
    client, rec = make_client(json_handler({"items": [], "total": 0}))

    with pytest.raises(TypeError, match="probe_key"):
        client.runs.list(probe_key="x")
    assert rec.requests == []


# --- execution lock: raised and documented as PerceivoExecutionLockedError -----

_LOCKED = {"detail": {"code": "execution_locked", "message": "Execution is locked"}}

_LOCKABLE = [
    pytest.param(lambda c: c.capabilities.run("cap-1"), id="run"),
    pytest.param(lambda c: c.capabilities.restart("cap-1"), id="restart"),
    pytest.param(lambda c: c.capabilities.evaluate("cap-1"), id="evaluate"),
]


@pytest.mark.parametrize("call", _LOCKABLE)
def test_an_execution_lock_raises_the_lock_error_not_the_rate_limit_error(call):
    client, _ = make_client(json_handler(_LOCKED, status=429))

    with pytest.raises(PerceivoExecutionLockedError) as caught:
        call(client)
    assert not isinstance(caught.value, PerceivoRateLimitError)


@pytest.mark.parametrize("name", ["run", "restart", "evaluate"])
def test_the_lockable_capability_methods_document_the_lock_error(name):
    doc = inspect.getdoc(getattr(CapabilitiesResource, name))

    assert "PerceivoExecutionLockedError" in doc
    assert "PerceivoRateLimitError" not in doc


def _resource_methods():
    from perceivo_client import resources

    for module_info in sorted(
        inspect.getmembers(resources, inspect.ismodule), key=lambda pair: pair[0]
    ):
        module = module_info[1]
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__ or not cls.__name__.endswith("Resource"):
                continue
            for name, fn in inspect.getmembers(cls, inspect.isfunction):
                if not name.startswith("_"):
                    yield f"{cls.__name__}.{name}", inspect.getdoc(fn) or ""


def _lock_sentences(doc: str) -> list[str]:
    flat = " ".join(doc.split())
    return [s for s in flat.split(". ") if "execution is locked" in s]


#: Methods whose lock refusal gives its reason as text only, with no
#: ``execution_locked`` code, so the client raises ``PerceivoRateLimitError``.
_TEXT_ONLY_LOCK = {"RunsResource.resume"}


def test_every_docstring_that_names_an_execution_lock_names_the_lock_error():
    pairs = [(where, s) for where, doc in _resource_methods() for s in _lock_sentences(doc)]
    coded = [(where, s) for where, s in pairs if where not in _TEXT_ONLY_LOCK]
    wrong = [where for where, sentence in coded if "PerceivoRateLimitError" in sentence]
    unnamed = [where for where, sentence in coded if "PerceivoExecutionLockedError" not in sentence]

    assert len(pairs) >= 8  # the sweep found the methods it is about
    assert {where for where, _ in pairs} >= _TEXT_ONLY_LOCK
    assert wrong == []
    assert unnamed == []


def test_a_text_only_lock_docstring_names_the_rate_limit_error_and_says_why():
    docs = dict(_resource_methods())
    for where in _TEXT_ONLY_LOCK:
        flat = " ".join(docs[where].split())
        assert "(``PerceivoRateLimitError``) when the organization may not run work" in flat
        assert "no ``execution_locked`` code" in flat


def test_the_lock_sweep_flags_a_sentence_that_names_the_rate_limit_error():
    planted = (
        "Raises: ``429`` (``PerceivoRateLimitError``) while the organization's execution is locked."
    )

    sentences = _lock_sentences(planted)

    assert len(sentences) == 1
    assert "PerceivoRateLimitError" in sentences[0]


# --- files.list_entries: honoured sort keys only --------------------------------


def test_list_entries_documents_only_the_sort_keys_the_platform_honours():
    doc = " ".join(inspect.getdoc(FilesResource.list_entries).split())
    sort_by = doc[doc.index("sort_by:") : doc.index("sort_order:")]

    assert "``size``" not in sort_by
    for key in ("``name``", "``created_at``", "``updated_at``"):
        assert key in sort_by


def test_list_entries_sends_the_sort_keys_when_browsing():
    client, rec = make_client(json_handler({"items": [], "total": 0}))

    client.files.list_entries("sp-1", sort_by="created_at", sort_order="desc")

    assert rec.last.url.params["sort_by"] == "created_at"
    assert rec.last.url.params["sort_order"] == "desc"


# --- capabilities: evaluation runs ----------------------------------------------

_STORED_RUN = {
    "id": "ev-1",
    "organization_id": "org-1",
    "kind": "capability_run",
    "subject_type": "capability",
    "subject_id": "cap-1",
    "evaluator_asset_id": None,
    "status": "completed",
    "trigger_type": "scheduled",
    "triggered_by_user_sub": "system",
    "started_at": "2026-10-04T20:15:13+00:00",
    "completed_at": "2026-10-04T20:15:14+00:00",
    "duration_ms": 1170,
    "recommendation": None,
    "summary_metrics": {"scored": 0},
    "config": None,
    "error_message": None,
    "created_at": "2026-10-04T20:15:13+00:00",
    "updated_at": "2026-10-04T20:15:13+00:00",
}
_EVALUATIONS = {"items": [_STORED_RUN], "total": 1221}

_STORED_STATUS = {
    "evaluation_id": "ev-1",
    "capability_id": "cap-1",
    "organization_id": "org-1",
    "status": "completed",
    "summary_metrics": {"scored": 0},
    "error": None,
    "started_at": "2026-10-04T20:15:13+00:00",
    "completed_at": "2026-10-04T20:15:14+00:00",
}
_IN_PROGRESS_STATUS = {
    "evaluation_id": "ev-2",
    "capability_id": "cap-1",
    "organization_id": "org-1",
    "status": "running",
    "summary_metrics": None,
    "result": None,
    "error": None,
}


def test_list_evaluations_reads_the_items_and_the_total():
    client, rec = make_client(json_handler(_EVALUATIONS))

    got = client.capabilities.list_evaluations("cap-1")

    assert rec.last.url.path == "/v1/capabilities/cap-1/evaluations"
    assert isinstance(got, EvaluationRunPage)
    assert got.total == 1221
    assert [type(run) for run in got.items] == [EvaluationRun]
    assert got.items[0].id == "ev-1"
    assert got.items[0].subject_id == "cap-1"
    assert got.items[0].summary_metrics == {"scored": 0}


def test_list_evaluations_returns_an_empty_page_for_a_capability_never_evaluated():
    client, _ = make_client(json_handler({"items": [], "total": 0}))

    got = client.capabilities.list_evaluations("cap-1")

    assert got.items == []
    assert got.total == 0


def test_get_evaluation_reads_the_run_id_as_evaluation_id():
    client, rec = make_client(json_handler(_STORED_STATUS))

    got = client.capabilities.get_evaluation("cap-1", "ev-1")

    assert rec.last.url.path == "/v1/capabilities/cap-1/evaluations/ev-1"
    assert isinstance(got, EvaluationRunStatus)
    assert got.evaluation_id == "ev-1"
    assert got.status == "completed"
    assert got.completed_at == "2026-10-04T20:15:14+00:00"


def test_get_evaluation_reads_an_in_progress_run():
    client, _ = make_client(json_handler(_IN_PROGRESS_STATUS))

    got = client.capabilities.get_evaluation("cap-1", "ev-2")

    assert got.evaluation_id == "ev-2"
    assert got.status == "running"
    assert got.started_at is None


def test_the_evaluation_methods_return_their_own_models():
    hints_list = inspect.signature(CapabilitiesResource.list_evaluations).return_annotation
    hints_get = inspect.signature(CapabilitiesResource.get_evaluation).return_annotation

    assert hints_list in (EvaluationRunPage, "EvaluationRunPage")
    assert hints_get in (EvaluationRunStatus, "EvaluationRunStatus")
    assert not hasattr(capabilities_module, "EvaluationRunRead")


def test_the_evaluation_methods_from_the_async_client_read_the_models():
    sync, _ = make_client(json_handler(_EVALUATIONS))

    got = asyncio.run(_async_from_sync(sync).capabilities.list_evaluations("cap-1"))

    assert got.items[0].id == "ev-1"
