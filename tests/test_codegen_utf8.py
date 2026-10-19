"""The spec refresh decodes the upstream document as UTF-8, whatever the console encoding."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


def _load_regen():
    path = Path(__file__).parents[1] / "openapi" / "regen.py"
    spec = importlib.util.spec_from_file_location("client_regen_utf8_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_refresh_decodes_the_upstream_document_as_utf8(monkeypatch, tmp_path):
    module = _load_regen()
    description = "Usage — café"
    upstream_bytes = json.dumps(
        {"info": {"description": description, "version": "9.9.9"}, "paths": {}},
        ensure_ascii=False,
    ).encode("utf-8")
    upstream = tmp_path / "public.json"
    upstream.write_bytes(upstream_bytes)

    output = tmp_path / "openapi.json"
    provenance = tmp_path / "spec_provenance.json"
    provenance.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "_installed_generator", lambda: "datamodel-code-generator==0")
    monkeypatch.setattr(module, "_installed_formatters", lambda: ["black==0", "isort==0"])
    monkeypatch.setattr(module, "SPEC_PATH", output)
    monkeypatch.setattr(module, "PROVENANCE_PATH", provenance)
    monkeypatch.chdir(tmp_path)
    module.refresh_spec("public.json")

    assert json.loads(output.read_text(encoding="utf-8"))["info"]["description"] == description
    assert description.encode("utf-8") in output.read_bytes()
    assert b"\r" not in output.read_bytes()
    assert output.read_bytes().endswith(b"\n")
    written = json.loads(provenance.read_text(encoding="utf-8"))
    assert written["upstream"] == {
        "sha256": hashlib.sha256(upstream_bytes).hexdigest(),
        "version": "9.9.9",
    }
    assert written["vendored"]["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert b"\r" not in provenance.read_bytes()


def test_generated_parts_end_in_one_lf(monkeypatch, tmp_path):
    module = _load_regen()
    output = tmp_path / "models"
    monkeypatch.setattr(module, "MODELS_PKG", output)
    monkeypatch.setattr(module, "MODELS_FLAT", tmp_path / "models.py")
    module._split_into_package(
        "from pydantic import BaseModel\n\nclass Item(BaseModel):\n    pass\n\n\n",
        "# header",
    )
    content = (output / "_part00.py").read_bytes()
    assert b"\r" not in content
    assert content.endswith(b"\n")
    assert not content.endswith(b"\n\n")
