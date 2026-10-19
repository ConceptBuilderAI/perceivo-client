"""G-18: every convenience wrapper targets a path+method that exists in the
vendored OpenAPI spec.

``test_wrapper_matrix`` pins each wrapper's concrete (method, path) internally;
this test closes the loop by validating those paths against
``openapi/openapi-v1.json`` — the same drift-guard the API side uses. If a
wrapper drifts from the served contract (renamed path, wrong verb, removed
endpoint), this fails instead of silently 404-ing at runtime.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from tests.conftest import make_client
from tests.test_wrapper_matrix import CASES, _shape_aware_handler

_SPEC_PATH = pathlib.Path(__file__).resolve().parents[1] / "openapi" / "openapi-v1.json"
_HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}


def _load_spec_paths() -> dict[str, set[str]]:
    """Return {path_template: {UPPER_METHOD, ...}} from the vendored spec."""
    spec = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for template, ops in spec.get("paths", {}).items():
        out[template] = {m.upper() for m in ops if m.lower() in _HTTP_METHODS}
    return out


_SPEC_PATHS = _load_spec_paths()

# No wrapper is exempt from the check below.


def _template_matches(concrete: str, template: str) -> bool:
    """True if a concrete path matches a spec template ({param} = wildcard)."""
    cs = concrete.strip("/").split("/")
    ts = template.strip("/").split("/")
    if len(cs) != len(ts):
        return False
    for c, t in zip(cs, ts, strict=True):
        if t.startswith("{") and t.endswith("}"):
            continue
        if c != t:
            return False
    return True


def test_spec_is_loaded():
    assert _SPEC_PATH.exists()
    assert _SPEC_PATHS, "vendored openapi spec has no paths"


def _spec_finding(method: str, path: str) -> str | None:
    """Why ``method path`` is not in the vendored spec, or ``None`` when it is."""
    matches = [t for t in _SPEC_PATHS if _template_matches(path, t)]
    if not matches:
        return f"{method} {path} matches no path in the OpenAPI spec"
    allowed_methods = set().union(*(_SPEC_PATHS[t] for t in matches))
    if method not in allowed_methods:
        return (
            f"{method} not defined for {path} in the spec (spec allows {sorted(allowed_methods)})"
        )
    return None


@pytest.mark.parametrize("call,method,path", CASES)
def test_wrapper_path_exists_in_spec(call, method, path):
    # Exercise the wrapper so the pinned path in CASES stays honest.
    client, rec = make_client(_shape_aware_handler)
    call(client)
    assert rec.last.url.path == path
    assert rec.last.method == method

    assert _spec_finding(method, path) is None


# Paths the SDK called before the contract moved them. Each must be REFUSED by
# the check above: a guard that has never been shown to fail is not known to be
# able to. The first column is the wrong path a wrapper could still be calling.
_PLANTED_WRONG_PATHS = [
    ("GET", "/v1/capabilities/x0/queue", "matches no path"),
    ("GET", "/v1/capabilities/x0/activity", "matches no path"),
    ("POST", "/v1/capabilities/x0/activity/bulk-cancel", "matches no path"),
    ("GET", "/v1/capabilities/x0/scoring", "matches no path"),
    ("GET", "/v1/infrastructure/storage/files", "matches no path"),
    ("POST", "/v1/infrastructure/storage/import", "matches no path"),
    ("GET", "/v1/infrastructure/elasticsearch/indices", "matches no path"),
    ("GET", "/v1/infrastructure/milvus/collections", "matches no path"),
    ("GET", "/v1/infrastructure/redis/keys", "matches no path"),
    # The run surface is under /orchestrations/runs, and the intelligence
    # predict and baseline routes are under inference/ and drift/.
    ("GET", "/v1/runs/x0", "matches no path"),
    ("GET", "/v1/runs/x0/result", "matches no path"),
    ("GET", "/v1/runs/x0/logs", "matches no path"),
    ("GET", "/v1/runs/x0/artifacts", "matches no path"),
    ("POST", "/v1/runs/x0/cancel", "matches no path"),
    ("POST", "/v1/intelligence/x0/predict", "matches no path"),
    ("POST", "/v1/intelligence/x0/predict/batch", "matches no path"),
    ("GET", "/v1/intelligence/x0/baselines", "matches no path"),
    ("POST", "/v1/intelligence/x0/baselines", "matches no path"),
    # These three log routes do not exist; runs.logs() and query.logs() call
    # GET /v1/logs instead.
    ("GET", "/v1/orchestrations/runs/x0/logs", "matches no path"),
    ("GET", "/v1/logs/intelligence/x0/errors", "matches no path"),
    ("GET", "/v1/logs/intelligence/x0/extension", "matches no path"),
    # The path exists; the verb does not.
    ("PUT", "/v1/queue/cancel", "PUT not defined"),
]


@pytest.mark.parametrize("method,path,fragment", _PLANTED_WRONG_PATHS)
def test_a_planted_wrong_path_is_refused(method, path, fragment):
    finding = _spec_finding(method, path)

    assert finding is not None, f"{method} {path} must not be in the vendored spec"
    assert fragment in finding


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/v1/queue"),
        ("GET", "/v1/queue/summary"),
        ("POST", "/v1/queue/cancel"),
        ("DELETE", "/v1/queue/x0"),
        ("GET", "/v1/whoami"),
        ("GET", "/v1/orchestrations/runs/x0"),
        ("POST", "/v1/orchestrations/runs/x0/cancel"),
        ("POST", "/v1/intelligence/x0/inference/predict"),
        ("POST", "/v1/intelligence/x0/inference/predict/batch"),
        ("GET", "/v1/intelligence/x0/drift/baselines"),
        ("POST", "/v1/intelligence/x0/drift/baselines"),
        # The grants surface.
        ("GET", "/v1/grants"),
        ("POST", "/v1/grants"),
        ("POST", "/v1/grants/preview"),
        ("POST", "/v1/grants/apply"),
        ("PATCH", "/v1/grants/x0"),
        ("DELETE", "/v1/grants/x0"),
    ],
)
def test_the_positive_control_is_accepted(method, path):
    """The other half of the control: a path known to be published passes."""
    assert _spec_finding(method, path) is None


def test_a_wrapper_repointed_at_a_removed_path_reds_the_wrapper_check():
    """End to end: a case row carrying a removed path fails the same assertion
    ``test_wrapper_path_exists_in_spec`` makes for every wrapper."""
    client, rec = make_client(_shape_aware_handler)
    client._transport.request("GET", "/v1/capabilities/x0/queue")

    assert _spec_finding(rec.last.method, rec.last.url.path) is not None
