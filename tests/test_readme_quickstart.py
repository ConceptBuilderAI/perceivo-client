"""Run the README Quickstart over a socket-blocked client and check the README's content."""

from __future__ import annotations

import json
import os
import re
import socket
import tomllib
from pathlib import Path
from typing import Any

import httpx
import pytest

import perceivo_client.client as client_module

README_PATH = Path(__file__).resolve().parents[1] / "README.md"


def _quickstart_fence() -> str:
    readme = README_PATH.read_text(encoding="utf-8")
    section = readme.split("## Quickstart", 1)[1].split("### Authentication", 1)[0]
    fences = re.findall(r"```python\n(.*?)\n```", section, flags=re.DOTALL)
    assert len(fences) == 1
    return fences[0]


#: Placeholder or pre-publication text that must not appear in the README.
_PREPUBLICATION_TEXT = (
    "`<PYPI_PROJECT_URL>`",
    "PYPI_PROJECT_OWNER",
    "PYPI_TRUSTED_PUBLISHER_REPOSITORY",
    "<CLIENT_RELEASE_TAG>",
    "<published-version>",
    "<destination-40-hex>",
    "prepublication",
    "unregistered",
    "deliberately non-runnable",
    "Do not run it",
    "Future publication placeholders",
    "This repository is private",
    "has not published an official",
)

#: A placeholder such as ``<UPPER_CASE>`` or ``<published-version>``; ``<hex>`` is allowed.
_PLACEHOLDER_RE = re.compile(r"<(?:[A-Z][A-Z0-9_]*|[a-z0-9]+(?:-[a-z0-9]+)+)>")

_DOCS_URL = "https://perceivo.ai/docs"
_PUBLIC_REPOSITORY = "github.com/ConceptBuilderAI/perceivo-client"
_MARKDOWN_LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")


def _readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_is_the_public_install_document():
    """The README gives the install line and docs site and carries no placeholders."""
    readme = _readme()

    assert "```bash\npip install perceivo-client\n```" in readme
    assert _DOCS_URL in readme

    leftover = [text for text in _PREPUBLICATION_TEXT if text in readme]
    assert leftover == [], f"README still carries pre-publication text: {leftover}"
    assert _PLACEHOLDER_RE.findall(readme) == []

    assert "artifacts already exist" not in readme
    assert "everything the Perceivo web app does" not in readme


def test_the_placeholder_pattern_sees_a_planted_placeholder():
    assert _PLACEHOLDER_RE.findall("x `<PYPI_PROJECT_URL>` y") == ["<PYPI_PROJECT_URL>"]
    assert _PLACEHOLDER_RE.findall("pip install perceivo-client==<published-version>") == [
        "<published-version>"
    ]
    assert _PLACEHOLDER_RE.findall("# sha256=<hex>") == []


def test_readme_names_no_private_source_or_internal_host():
    readme = _readme()

    assert "git+https://" not in readme
    for match in re.finditer(r"github\.com/ConceptBuilderAI/[\w.-]+", readme):
        assert match.group(0) == _PUBLIC_REPOSITORY, match.group(0)


def test_every_readme_link_is_absolute():
    """Relative links do not resolve on the PyPI project page."""
    targets = _MARKDOWN_LINK_TARGET.findall(_readme())

    assert targets, "the README has no markdown links at all; this check proves nothing"
    relative = [t for t in targets if not t.startswith(("https://", "http://", "#"))]
    assert relative == [], f"relative links break on PyPI: {relative}"


def test_readme_identifies_current_signing_and_customer_codegen_contracts():
    readme = README_PATH.read_text(encoding="utf-8")
    root = README_PATH.parent
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    codegen = metadata["project"]["optional-dependencies"]["codegen"][0]
    version = codegen.split("==", 1)[1]
    assert f"pinned `=={version}`" in readme
    assert "public Perceivo API OpenAPI document" in readme
    assert "perceivo_client/generated/models/" in readme
    assert "**eleven** fields" in readme
    assert "192 paths / 240 operations" not in readme
    assert "excerpts, not standalone" in readme


def _handler(execution_result: dict[str, Any], requests: list[tuple[str, str, bytes]]):
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path, request.content))
        path = request.url.path
        if path == "/v1/whoami":
            return httpx.Response(
                200,
                json={
                    "id": "service-account-1",
                    "organization_id": "org-1",
                    "effective_privileges": ["ORCHESTRATION_EXECUTE"],
                    "endpoint_access": {"allow_all": True},
                },
            )
        if path == "/v1/orchestrations/orchestration-1/run":
            assert json.loads(request.content) == {"input": {"prompt": "hi"}}
            return httpx.Response(200, json={"success": True, "result": execution_result})
        if path == "/v1/orchestrations/runs/run-1/result":
            return httpx.Response(200, json={"run_id": "run-1", "status": "completed"})
        return httpx.Response(404, json={"detail": f"unexpected test path: {path}"})

    return handler


@pytest.mark.parametrize(
    ("execution_result", "expected_paths", "expected_output"),
    [
        (
            {"run_id": "run-1"},
            [
                "/v1/whoami",
                "/v1/orchestrations/orchestration-1/run",
                "/v1/orchestrations/runs/run-1/result",
            ],
            None,
        ),
        (
            {"run_id": None, "request_id": "request-1"},
            [
                "/v1/whoami",
                "/v1/orchestrations/orchestration-1/run",
            ],
            "queued request accepted: request-1",
        ),
    ],
)
def test_exact_quickstart_handles_immediate_and_queued_execution(
    monkeypatch,
    capsys,
    execution_result,
    expected_paths,
    expected_output,
):
    requests = _run_quickstart(monkeypatch, execution_result)

    output = capsys.readouterr()
    assert [path for _method, path, _content in requests] == expected_paths
    if expected_output is not None:
        assert expected_output in output.out
    assert output.err == ""
    assert os.environ["PERCEIVO_ORCHESTRATION_ID"] == "orchestration-1"


def _run_quickstart(monkeypatch, execution_result: dict[str, Any]) -> list[tuple[str, str, bytes]]:
    """Run the README Quickstart fence over a mocked, socket-blocked client."""
    requests: list[tuple[str, str, bytes]] = []
    transport = httpx.MockTransport(_handler(execution_result, requests))
    real_httpx_client = httpx.Client

    def mocked_httpx_client(*args, **kwargs):
        return real_httpx_client(*args, transport=transport, **kwargs)

    monkeypatch.setattr(client_module.httpx, "Client", mocked_httpx_client)
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: pytest.fail("external socket use is forbidden"),
    )
    monkeypatch.setenv("PERCEIVO_API_KEY", "test-key")
    monkeypatch.setenv("PERCEIVO_API_URL", "https://api.test.perceivo.ai")
    monkeypatch.setenv("PERCEIVO_ORCHESTRATION_ID", "orchestration-1")

    exec(compile(_quickstart_fence(), "README.md#quickstart", "exec"), {})
    return requests


def _spec_operations_missing(calls: list[tuple[str, str]]) -> list[str]:
    """The ``METHOD path`` calls the vendored OpenAPI spec does not publish."""
    from tests.test_spec_conformance import _SPEC_PATHS, _template_matches

    missing = []
    for method, path in calls:
        templates = [t for t in _SPEC_PATHS if _template_matches(path, t)]
        if not any(method in _SPEC_PATHS[t] for t in templates):
            missing.append(f"{method} {path}")
    return missing


def test_every_quickstart_call_is_an_operation_in_the_vendored_spec(monkeypatch):
    """The immediate-``run_id`` branch reaches every Quickstart call."""
    requests = _run_quickstart(monkeypatch, {"run_id": "run-1"})
    calls = [(method, path) for method, path, _content in requests]

    assert len(calls) == 3, calls
    assert _spec_operations_missing(calls) == []


def test_the_quickstart_spec_check_refuses_an_unpublished_operation():
    assert _spec_operations_missing(
        [
            ("POST", "/v1/conversations/run-1/messages"),
            ("DELETE", "/v1/whoami"),
            ("GET", "/v1/whoami"),
        ]
    ) == ["POST /v1/conversations/run-1/messages", "DELETE /v1/whoami"]


# The lookbehind skips module paths such as ``perceivo_client.generated.models``.
_README_METHOD_RE = re.compile(r"(?<![\w.])client\.([a-z_]+)\.([a-z_]+)")


def _documented_methods() -> set[tuple[str, str]]:
    """Every ``client.<namespace>.<method>`` the README names."""
    readme = README_PATH.read_text(encoding="utf-8")
    return {(ns, meth) for ns, meth in _README_METHOD_RE.findall(readme)}


def test_the_readme_finds_method_references_at_all():
    documented = _documented_methods()

    assert len(documented) >= 15
    assert ("auth", "whoami") in documented
    assert ("orchestrations", "run") in documented


def test_every_method_the_readme_documents_exists_on_the_client():
    client = client_module.Client(api_key="test-key", base_url="https://api.test.perceivo.ai")
    missing = sorted(
        f"client.{ns}.{meth}"
        for ns, meth in _documented_methods()
        if not hasattr(getattr(client, ns, None), meth)
    )

    assert missing == [], f"README documents methods the client does not define: {missing}"


def test_the_readme_names_no_namespace_the_client_does_not_have():
    client = client_module.Client(api_key="test-key", base_url="https://api.test.perceivo.ai")
    missing = sorted({ns for ns, _m in _documented_methods() if not hasattr(client, ns)})

    assert missing == [], f"README documents namespaces the client does not define: {missing}"
