"""Shared helpers for the ``openapi/regen.py`` must-fail controls.

See ``tests/test_regen_check.py`` for what the controls assert and why.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = os.environ.get("PERCEIVO_REGEN_CHECK_REQUIRED") == "1"
_TIMEOUT = 600

try:
    importlib.metadata.version("datamodel-code-generator")
    GENERATOR = True
except importlib.metadata.PackageNotFoundError:
    GENERATOR = False

needs_generator = pytest.mark.skipif(
    not GENERATOR and not REQUIRED,
    reason=(
        'datamodel-code-generator is not installed (pip install -e ".[codegen]"). '
        "These controls are UNRUN here, which is not the same as passing."
    ),
)

#: An upstream document small enough to generate in a second.
UPSTREAM_DOC = {
    "openapi": "3.1.0",
    "info": {"title": "Example API", "version": "2.3.4"},
    "paths": {
        "/v1/things": {
            "get": {
                "operationId": "list_things",
                "responses": {
                    "200": {
                        "description": "ok",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}
                        },
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Thing": {
                "type": "object",
                "title": "Thing",
                "properties": {"name": {"type": "string", "title": "Name"}},
            },
        }
    },
}

_HEADER = re.compile(
    r"# GENERATED CODE - DO NOT EDIT BY HAND\.\n"
    r"# Regenerate with: python openapi/regen\.py \(see CONTRIBUTING\.md\)\.\n"
    r"# Source: (?P<name>[^,\n/\\]+)(?:, version (?P<version>[^,\n]+))?, "
    r"sha256 (?P<sha>[0-9a-f]{64})\n"
)


def _doc_bytes(doc: dict) -> bytes:
    return (json.dumps(doc, indent=2) + "\n").encode("utf-8")


def _upstream(tree: pathlib.Path, doc: dict = UPSTREAM_DOC, name: str = "public.json") -> str:
    """Write ``doc`` as an upstream document in ``tree`` (the directory the tool
    runs in) and return its file name."""
    (tree / name).write_bytes(_doc_bytes(doc))
    return name


def _client_tree(destination: pathlib.Path) -> pathlib.Path:
    """A private copy of everything the generator reads and writes."""
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(REPO / "openapi", destination / "openapi", ignore=ignore)
    shutil.copytree(
        REPO / "perceivo_client" / "generated",
        destination / "perceivo_client" / "generated",
        ignore=ignore,
    )
    return destination


def _regen(tree: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(tree / "openapi" / "regen.py"), *args],
        cwd=tree,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_TIMEOUT,
    )


def _say(result: subprocess.CompletedProcess) -> str:
    return f"exit {result.returncode}\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"


def _provenance(tree: pathlib.Path) -> dict:
    return json.loads((tree / "openapi" / "spec_provenance.json").read_text(encoding="utf-8-sig"))


def _write_provenance(tree: pathlib.Path, manifest: dict) -> None:
    (tree / "openapi" / "spec_provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def _spec_sha(tree: pathlib.Path) -> str:
    return hashlib.sha256((tree / "openapi" / "openapi-v1.json").read_bytes()).hexdigest()


def _models(tree: pathlib.Path) -> pathlib.Path:
    return tree / "perceivo_client" / "generated" / "models"


def _copy_of(tree: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    shutil.copytree(tree, destination, ignore=shutil.ignore_patterns("__pycache__"))
    return destination
