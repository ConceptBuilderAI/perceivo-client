"""Run every Python excerpt in the README against the real client over a mock transport.

The Quickstart is covered by ``test_readme_quickstart.py``; this module supplies the
names the other excerpts assume and executes each one.
"""

from __future__ import annotations

import asyncio
import re
import socket
import textwrap
from pathlib import Path

import httpx
import pytest

import perceivo_client.client as client_module
from perceivo_client import AsyncClient, Client

README_PATH = Path(__file__).resolve().parents[1] / "README.md"

_QUICKSTART_MARKER = 'os.environ["PERCEIVO_ORCHESTRATION_ID"]'  # test_readme_quickstart.py
_MISSING_ID = "orchestration-missing"


def _python_blocks() -> list[str]:
    readme = README_PATH.read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)\n```", readme, flags=re.DOTALL)


def _excerpts() -> list[str]:
    return [block for block in _python_blocks() if _QUICKSTART_MARKER not in block]


def _handler(requests: list[httpx.Request]):
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith(f"/orchestrations/{_MISSING_ID}"):
            return httpx.Response(
                404,
                json={"code": "not_found", "message": "no such orchestration"},
                headers={"Perceivo-Request-Id": "req-1"},
            )
        if path == "/v1/whoami":
            return httpx.Response(
                200,
                json={
                    "id": "service-account-1",
                    "organization_id": "org-1",
                    "effective_privileges": [],
                    "endpoint_access": {"allow_all": True},
                },
            )
        # A response body every remaining excerpt can read.
        return httpx.Response(
            200,
            json={"id": "x", "items": [{"id": "x"}], "total": 1, "succeeded": 1, "failed": 0},
        )

    return handler


@pytest.fixture
def mocked_transport(monkeypatch) -> list[httpx.Request]:
    requests: list[httpx.Request] = []
    transport = httpx.MockTransport(_handler(requests))
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
    monkeypatch.setenv("PERCEIVO_API_URL", "https://api.example.test")
    return requests


def _namespace(block: str) -> dict:
    processed: list = []
    names = {
        "orchestration_id": _MISSING_ID if "PerceivoNotFoundError" in block else "orch-1",
        "update_body": {"name": "renamed"},
        "intelligence_id": "intel-1",
        "space_id": "space-1",
        "csv_bytes": b"a,b\n1,2\n",
        "process": processed.append,
        "request_body": b'{"event":"run.completed"}',
        "webhook_secret": "whsec_test",
        "request_headers": {},
        "_processed": processed,
    }
    if "async for" in block:
        names["client"] = AsyncClient()
    elif "client = Client(" not in block:
        names["client"] = Client()
    return names


def _execute(block: str, names: dict) -> None:
    if "async " in block:
        wrapped = "async def _excerpt():\n" + textwrap.indent(block, "    ")
        exec(compile(wrapped, "README.md", "exec"), names)
        asyncio.run(names["_excerpt"]())
    else:
        exec(compile(block, "README.md", "exec"), names)


def test_the_readme_has_excerpts_to_run():
    blocks = _python_blocks()
    excerpts = _excerpts()

    assert len(blocks) - len(excerpts) == 1, "expected exactly one Quickstart block"
    assert len(excerpts) >= 10, len(excerpts)


@pytest.mark.parametrize("index", range(len(_excerpts())))
def test_each_readme_excerpt_runs_against_the_client(index, mocked_transport):
    block = _excerpts()[index]
    names = _namespace(block)

    _execute(block, names)

    if "paginate_pages" in block:
        assert names["_processed"], block


def test_the_errors_excerpt_reaches_its_handler(mocked_transport, capsys):
    """The errors excerpt is run against a 404, so its ``except`` branch executes."""
    (block,) = [b for b in _excerpts() if "PerceivoNotFoundError" in b]

    _execute(block, _namespace(block))

    assert capsys.readouterr().out.split() == ["not_found", "no", "such", "orchestration", "req-1"]


def test_the_with_options_excerpt_sends_its_timeout(mocked_transport):
    (block,) = [b for b in _excerpts() if "with_options" in b]

    _execute(block, _namespace(block))

    start = [r for r in mocked_transport if r.url.path.endswith("/intelligence/intel-1/start")]
    assert len(start) == 1
    assert start[0].extensions["timeout"]["read"] == 180.0


_NAMESPACE_ROW = re.compile(r"^\| `client\.([a-z_]+)` \|")


def _namespace_table_rows(readme: str) -> list[str]:
    """The namespaces in the README's namespace table; a blank line ends the table."""
    section = readme.split("### Namespaces", 1)[1]
    lines = section.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Namespace |"))
    assert set(lines[start + 1]) <= set("|- "), "the header is not followed by a delimiter row"
    rows = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        match = _NAMESPACE_ROW.match(line)
        assert match, f"not a namespace row: {line[:60]}"
        rows.append(match.group(1))
    return rows


def test_every_namespace_is_a_row_of_the_namespace_table():
    namespaces = {n for n, v in vars(Client(api_key="k")).items() if hasattr(v, "_t")}
    rows = _namespace_table_rows(README_PATH.read_text(encoding="utf-8"))

    assert len(namespaces) == 29
    assert len(rows) == len(set(rows))
    assert set(rows) == namespaces


def test_a_blank_line_inside_the_namespace_table_is_detected():
    readme = README_PATH.read_text(encoding="utf-8")
    broken = readme.replace("\n| `client.alerts` |", "\n\n| `client.alerts` |", 1)

    assert broken != readme
    assert len(_namespace_table_rows(broken)) < len(_namespace_table_rows(readme))
