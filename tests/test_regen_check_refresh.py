"""Tests for ``openapi/regen.py`` that start from a refreshed client tree."""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from tests._regen_check_support import (
    _HEADER,
    REPO,
    UPSTREAM_DOC,
    _client_tree,
    _copy_of,
    _doc_bytes,
    _models,
    _provenance,
    _regen,
    _say,
    _spec_sha,
    _upstream,
    _write_provenance,
    needs_generator,
)


@pytest.fixture(scope="module")
def refreshed(tmp_path_factory) -> tuple[pathlib.Path, str]:
    """A client tree refreshed from a stand-in upstream document; tests copy it first."""
    root = tmp_path_factory.mktemp("refreshed")
    tree = _client_tree(root / "client")
    source = _upstream(tree)
    result = _regen(tree, "--refresh", "--upstream", source)
    assert result.returncode == 0, _say(result)
    return tree, source


@needs_generator
def test_the_refresh_records_the_upstream_document_by_content(refreshed) -> None:
    tree, source = refreshed
    manifest = _provenance(tree)
    upstream_bytes = (tree / source).read_bytes()
    assert manifest["upstream"]["sha256"] == hashlib.sha256(upstream_bytes).hexdigest()
    assert manifest["upstream"]["version"] == "2.3.4"
    # The refresh rewrites values, not the explanatory text beside them.
    assert manifest["upstream"]["_role"] == _provenance(REPO)["upstream"]["_role"]
    assert manifest["vendored"]["_role"] == _provenance(REPO)["vendored"]["_role"]
    assert manifest["vendored"]["sha256"] == _spec_sha(tree)
    assert manifest["vendored"]["paths"] == 1
    assert manifest["vendored"]["operations"] == 1
    # Nothing in the record names where the document was read from.
    recorded = json.dumps(manifest)
    assert "public.json" not in recorded
    assert str(tree) not in recorded


@needs_generator
def test_two_refreshes_from_one_document_write_identical_trees(refreshed, tmp_path) -> None:
    first, source = refreshed
    second = _client_tree(tmp_path / "client")
    assert _upstream(second) == source
    result = _regen(second, "--refresh", "--upstream", source)
    assert result.returncode == 0, _say(result)

    def digest(tree: pathlib.Path) -> dict[str, str]:
        return {
            path.relative_to(tree).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(tree.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
        }

    assert digest(first) == digest(second)
    assert len(digest(first)) >= 5  # regen.py, spec, provenance, models/__init__, one part


@needs_generator
def test_e_release_passes_on_a_clean_refresh(refreshed) -> None:
    tree, source = refreshed
    result = _regen(tree, "--check", "--release", "--upstream", source)
    assert result.returncode == 0, _say(result)
    assert "legs: models, spec_sha256, upstream;" in result.stdout, _say(result)


@needs_generator
def test_g_a_hand_edited_spec_passes_locally_and_fails_the_upstream_leg(
    refreshed, tmp_path
) -> None:
    """A hand-edited spec with a re-recorded hash fails only the upstream check."""
    source_tree, source = refreshed
    tree = _copy_of(source_tree, tmp_path / "client")
    spec_path = tree / "openapi" / "openapi-v1.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["components"]["schemas"]["Thing"]["properties"]["ahead"] = {"type": "string"}
    spec_path.write_bytes(
        (json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    )
    assert _regen(tree).returncode == 0
    manifest = _provenance(tree)
    manifest["vendored"]["sha256"] = _spec_sha(tree)
    _write_provenance(tree, manifest)

    local_only = _regen(tree, "--check")
    assert local_only.returncode == 0, _say(local_only)  # the gap the upstream leg closes

    result = _regen(tree, "--check", "--upstream", source)
    assert result.returncode == 1, _say(result)
    assert "openapi-v1.json is not the transform of the upstream document" in result.stderr


@needs_generator
def test_g_an_upstream_document_other_than_the_recorded_one_exits_1(refreshed, tmp_path) -> None:
    source_tree, _source = refreshed
    tree = _copy_of(source_tree, tmp_path / "client")
    moved = json.loads(json.dumps(UPSTREAM_DOC))
    moved["components"]["schemas"]["Thing"]["properties"]["colour"] = {"type": "string"}
    other = _upstream(tree, moved, "moved.json")

    result = _regen(tree, "--check", "--upstream", other)
    assert result.returncode == 1, _say(result)
    assert "upstream.sha256 records" in result.stderr, _say(result)
    assert "is not the transform of the upstream document" in result.stderr, _say(result)


@needs_generator
def test_the_spec_written_by_a_refresh_from_a_moved_document_passes(refreshed, tmp_path) -> None:
    source_tree, _source = refreshed
    tree = _copy_of(source_tree, tmp_path / "client")
    moved = json.loads(json.dumps(UPSTREAM_DOC))
    moved["components"]["schemas"]["Thing"]["properties"]["colour"] = {"type": "string"}
    other = _upstream(tree, moved, "moved.json")

    assert _regen(tree, "--refresh", "--upstream", other).returncode == 0
    assert "colour" in (_models(tree) / "_part00.py").read_text(encoding="utf-8")
    result = _regen(tree, "--check", "--upstream", other)
    assert result.returncode == 0, _say(result)


def test_h_every_committed_module_names_the_vendored_spec_by_hash_and_version() -> None:
    spec_bytes = (REPO / "openapi" / "openapi-v1.json").read_bytes()
    expected = (
        "openapi-v1.json",
        json.loads(spec_bytes)["info"]["version"],
        hashlib.sha256(spec_bytes).hexdigest(),
    )
    modules = sorted(_models(REPO).glob("*.py"))
    assert len(modules) >= 2, modules
    for module in modules:
        match = _HEADER.match(module.read_text(encoding="utf-8"))
        assert match is not None, f"{module.name}: header is not the expected three lines"
        assert match.group("name", "version", "sha") == expected, module.name


@needs_generator
def test_h_a_spec_passed_by_path_is_named_by_its_file_name_only(refreshed, tmp_path) -> None:
    source_tree, _source = refreshed
    tree = _copy_of(source_tree, tmp_path / "client")
    elsewhere = tmp_path / "some" / "where"
    elsewhere.mkdir(parents=True)
    unversioned = json.loads(json.dumps(UPSTREAM_DOC))
    del unversioned["info"]["version"]
    spec = elsewhere / "candidate.json"
    spec.write_bytes(_doc_bytes(unversioned))

    result = _regen(tree, "--spec", str(spec))
    assert result.returncode == 0, _say(result)
    header = _HEADER.match((_models(tree) / "__init__.py").read_text(encoding="utf-8"))
    assert header is not None
    assert header.group("name", "version", "sha") == (
        "candidate.json",
        None,
        hashlib.sha256(spec.read_bytes()).hexdigest(),
    )
    assert "some" not in header.group(0)
