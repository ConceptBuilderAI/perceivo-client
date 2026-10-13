"""``openapi/regen.py``: generation, ``--check`` and ``--refresh``, as must-fail controls.

Every control drives the command line in a subprocess and asserts the EXIT
CODE, because the exit code is what CI reads. 0 is clean, 1 is a difference, 2
is "could not do what was asked" -- and a control that expects 1 must not be
satisfied by 2, or a broken environment would read as a caught defect.

The controls, by letter:

(a) a planted property in a copy of the spec makes ``--check`` exit 1;
(b) a hand edit to one ``_partNN.py`` makes it exit 1;
(c) ``--refresh`` without ``--upstream``, and ``--release`` without it, exit 2;
(d) an unreadable, non-JSON, remote or out-of-tree upstream document exits 2,
    never 0;
(e) ``--check --release --upstream`` exits 0 on a clean refresh;
(f) the unchanged tree exits 0 -- the positive control for (a) and (b);
(g) a hand-edited spec whose hash was re-recorded passes the local legs and
    fails the upstream leg, as does an upstream document other than the
    recorded one;
(h) every generated module's header names the spec by file name, version and
    hash only.

Controls that run the code generator are skipped where it is not installed
(the sdist and dependency-floor jobs install no ``codegen`` extra). The CI step
that owns this check sets ``PERCEIVO_REGEN_CHECK_REQUIRED=1``, which turns that
skip into a failure, so the controls cannot all skip in the one job that is
supposed to run them.
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


@pytest.fixture(scope="module")
def refreshed(tmp_path_factory) -> tuple[pathlib.Path, str]:
    """A client tree refreshed, through the command line, from a stand-in
    upstream document. Tests copy it before changing it."""
    root = tmp_path_factory.mktemp("refreshed")
    tree = _client_tree(root / "client")
    source = _upstream(tree)
    result = _regen(tree, "--refresh", "--upstream", source)
    assert result.returncode == 0, _say(result)
    return tree, source


def _copy_of(tree: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    shutil.copytree(tree, destination, ignore=shutil.ignore_patterns("__pycache__"))
    return destination


# --------------------------------------------------------------------------
# The environment this file needs, stated so a skip cannot hide
# --------------------------------------------------------------------------
def test_the_generator_is_installed_where_the_check_is_required() -> None:
    if not REQUIRED:
        pytest.skip("PERCEIVO_REGEN_CHECK_REQUIRED is not set; generator controls may skip")
    assert GENERATOR, "PERCEIVO_REGEN_CHECK_REQUIRED=1 but datamodel-code-generator is absent"


# --------------------------------------------------------------------------
# (f) positive control, on the real tree
# --------------------------------------------------------------------------
@needs_generator
def test_f_the_unchanged_tree_exits_0() -> None:
    result = _regen(REPO, "--check")
    assert result.returncode == 0, _say(result)
    assert "check OK (legs: models, spec_sha256;" in result.stdout, _say(result)


# --------------------------------------------------------------------------
# (a) (b) the model comparison
# --------------------------------------------------------------------------
@needs_generator
def test_a_a_planted_property_in_the_spec_exits_1(tmp_path) -> None:
    tree = _client_tree(tmp_path / "client")
    spec_path = tree / "openapi" / "openapi-v1.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["components"]["schemas"]["ActivityResponse"]["properties"]["planted_by_control_a"] = {
        "type": "string",
        "title": "Planted By Control A",
    }
    spec_path.write_bytes(
        (json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    )
    # Re-record the hash, so the ONLY leg that can fail is the model comparison.
    # Without this the control would pass on the hash leg alone and say nothing
    # about whether the models are compared at all.
    manifest = _provenance(tree)
    manifest["vendored"]["sha256"] = _spec_sha(tree)
    _write_provenance(tree, manifest)

    result = _regen(tree, "--check")
    assert result.returncode == 1, _say(result)
    assert "vendored.sha256 records" not in result.stderr, _say(result)
    assert "differs from a fresh generation" in result.stderr, _say(result)


@needs_generator
def test_b_a_hand_edit_to_one_generated_module_exits_1(tmp_path) -> None:
    tree = _client_tree(tmp_path / "client")
    part = _models(tree) / "_part03.py"
    part.write_bytes(part.read_bytes() + b"# edited by hand\n")

    result = _regen(tree, "--check")
    assert result.returncode == 1, _say(result)
    assert "generated/models/_part03.py: differs from a fresh generation" in result.stderr
    assert result.stderr.count("DIFFERENCE:") == 1, _say(result)


@needs_generator
def test_b_a_stray_and_a_missing_generated_module_each_exit_1(tmp_path) -> None:
    """The comparison is over the SET of files, not only the files both sides have."""
    tree = _client_tree(tmp_path / "client")
    models = _models(tree)
    (models / "_part99.py").write_bytes(b"# not produced by the generator\n")
    (models / "_part00.py").unlink()

    result = _regen(tree, "--check")
    assert result.returncode == 1, _say(result)
    assert "_part99.py: committed, but the generator does not produce it" in result.stderr
    assert "_part00.py: produced by the generator, but not committed" in result.stderr


# --------------------------------------------------------------------------
# (c) (d) the upstream document is required where it is needed, and an
# unusable one is exit 2. No generator needed: each is refused before anything
# is generated, and the test asserts nothing was written.
# --------------------------------------------------------------------------
def test_c_refresh_without_upstream_exits_2(tmp_path) -> None:
    tree = _client_tree(tmp_path / "client")
    before = _spec_sha(tree)
    result = _regen(tree, "--refresh")
    assert result.returncode == 2, _say(result)
    assert "--refresh requires --upstream" in result.stderr, _say(result)
    assert _spec_sha(tree) == before


@needs_generator
def test_c_release_without_upstream_exits_2(tmp_path) -> None:
    tree = _client_tree(tmp_path / "client")
    result = _regen(tree, "--check", "--release")
    assert result.returncode == 2, _say(result)
    assert "--check --release requires --upstream" in result.stderr, _say(result)
    assert "check OK" not in result.stdout


@needs_generator
@pytest.mark.parametrize("mode", ["--refresh", "--check"])
def test_d_a_missing_upstream_document_exits_2(tmp_path, mode) -> None:
    tree = _client_tree(tmp_path / "client")
    before = _spec_sha(tree)
    result = _regen(tree, mode, "--upstream", "absent.json")
    assert result.returncode == 2, _say(result)
    assert "cannot read the upstream document" in result.stderr, _say(result)
    assert "check OK" not in result.stdout
    assert _spec_sha(tree) == before


@pytest.mark.parametrize(
    "source", ["https://example.invalid/public.json", "http://example.invalid/public.json"]
)
def test_d_a_url_is_refused_without_a_request(tmp_path, source) -> None:
    tree = _client_tree(tmp_path / "client")
    before = _spec_sha(tree)
    result = _regen(tree, "--refresh", "--upstream", source)
    assert result.returncode == 2, _say(result)
    assert "must be a local file" in result.stderr, _say(result)
    assert _spec_sha(tree) == before


@pytest.mark.parametrize("escape", ["../outside.json", "openapi/../../outside.json", "ABSOLUTE"])
def test_d_a_path_with_a_directory_part_is_refused(tmp_path, escape) -> None:
    outside = tmp_path / "outside.json"
    outside.write_bytes(_doc_bytes(UPSTREAM_DOC))
    tree = _client_tree(tmp_path / "client")
    before = _spec_sha(tree)
    source = str(outside) if escape == "ABSOLUTE" else escape
    result = _regen(tree, "--refresh", "--upstream", source)
    assert result.returncode == 2, _say(result)
    assert "must be a file name in the current directory" in result.stderr, _say(result)
    assert _spec_sha(tree) == before


def test_d_a_name_that_resolves_outside_the_current_directory_is_refused(
    tmp_path, monkeypatch
) -> None:
    """A symbolic link in the current directory that points elsewhere."""
    spec = importlib.util.spec_from_file_location("regen_link_test", REPO / "openapi" / "regen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    real = module.os.path.realpath
    outside = str(tmp_path / "elsewhere" / "public.json")
    working = tmp_path / "working"
    working.mkdir()
    monkeypatch.chdir(working)
    monkeypatch.setattr(
        module.os.path,
        "realpath",
        lambda path: outside if path.endswith("public.json") else real(path),
    )
    with pytest.raises(module.RegenError, match="resolves outside"):
        module._read_upstream("public.json")


@pytest.mark.parametrize(
    "content, message",
    [
        (b"<<<<<<< not json\n", "is not UTF-8 JSON"),
        (b'{"openapi": "3.1.0"}\n', "is not an OpenAPI document"),
    ],
)
def test_d_an_upstream_document_that_is_not_an_openapi_document_exits_2(
    tmp_path, content, message
) -> None:
    tree = _client_tree(tmp_path / "client")
    (tree / "public.json").write_bytes(content)
    before = _spec_sha(tree)

    result = _regen(tree, "--refresh", "--upstream", "public.json")
    assert result.returncode == 2, _say(result)
    assert f"the upstream document {message}" in result.stderr, _say(result)
    assert "Traceback" not in result.stderr, _say(result)
    assert _spec_sha(tree) == before


# --------------------------------------------------------------------------
# The refresh: what it writes, and that it writes the same bytes twice
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# (e) (g) the upstream leg
# --------------------------------------------------------------------------
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
    """A spec edited by hand, with the hash re-recorded and the models
    regenerated, passes every leg that reads only this repository. The upstream
    leg is the one that catches it."""
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
    """The positive control for the moved-document failure above."""
    source_tree, _source = refreshed
    tree = _copy_of(source_tree, tmp_path / "client")
    moved = json.loads(json.dumps(UPSTREAM_DOC))
    moved["components"]["schemas"]["Thing"]["properties"]["colour"] = {"type": "string"}
    other = _upstream(tree, moved, "moved.json")

    assert _regen(tree, "--refresh", "--upstream", other).returncode == 0
    assert "colour" in (_models(tree) / "_part00.py").read_text(encoding="utf-8")
    result = _regen(tree, "--check", "--upstream", other)
    assert result.returncode == 0, _say(result)


# --------------------------------------------------------------------------
# (h) generated headers name the spec by content only
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Usage errors and an unusable environment are exit 2, never 0 and never 1
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "args",
    [
        ("--check", "--refresh", "--upstream", "x.json"),
        ("--refresh", "--upstream", "x.json", "--spec", "y.json"),
        ("--release",),
        ("--upstream", "x.json"),
    ],
)
def test_contradictory_arguments_exit_2(tmp_path, args) -> None:
    tree = _client_tree(tmp_path / "client")
    before = _spec_sha(tree)
    result = _regen(tree, *args)
    assert result.returncode == 2, _say(result)
    assert _spec_sha(tree) == before


@needs_generator
def test_a_generator_version_other_than_the_recorded_one_exits_2(tmp_path) -> None:
    tree = _client_tree(tmp_path / "client")
    manifest = _provenance(tree)
    manifest["generator"]["code_generator"] = "datamodel-code-generator==0.0.0"
    _write_provenance(tree, manifest)

    result = _regen(tree, "--check")
    assert result.returncode == 2, _say(result)
    assert "A comparison across generator versions proves nothing" in result.stderr
    assert "'datamodel-code-generator==0.0.0'" in result.stderr, _say(result)
    assert "check OK" not in result.stdout


@needs_generator
@pytest.mark.parametrize("position, name", [(0, "black"), (1, "isort")])
def test_a_formatter_version_other_than_the_recorded_one_exits_2(tmp_path, position, name) -> None:
    """black and isort decide generated bytes as the generator does."""
    tree = _client_tree(tmp_path / "client")
    manifest = _provenance(tree)
    assert manifest["generator"]["code_formatters"][position].startswith(f"{name}==")
    manifest["generator"]["code_formatters"][position] = f"{name}==0.0.0"
    _write_provenance(tree, manifest)

    result = _regen(tree, "--check")
    assert result.returncode == 2, _say(result)
    assert f"'{name}==0.0.0'" in result.stderr, _say(result)
    assert "check OK" not in result.stdout


def test_the_codegen_extra_pins_exactly_what_the_provenance_records() -> None:
    """The install pin and the recorded versions are one fact in two files. If
    they part, CI installs one set and --check demands another."""
    import tomllib

    extra = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "optional-dependencies"
    ]["codegen"]
    generator = _provenance(REPO)["generator"]
    recorded = [generator["code_generator"], *generator["code_formatters"]]
    assert [pin.replace("[http]", "") for pin in extra] == recorded
    assert [pin.split("==")[0] for pin in recorded] == [
        "datamodel-code-generator",
        "black",
        "isort",
    ]


@needs_generator
def test_a_provenance_missing_a_field_the_check_reads_exits_2(tmp_path) -> None:
    tree = _client_tree(tmp_path / "client")
    manifest = _provenance(tree)
    del manifest["vendored"]["sha256"]
    _write_provenance(tree, manifest)

    result = _regen(tree, "--check")
    assert result.returncode == 2, _say(result)
    assert "lacks a field --check reads" in result.stderr, _say(result)


# --------------------------------------------------------------------------
# Line endings: the check compares working-tree bytes, so the working tree is
# pinned to LF whatever core.autocrlf says
# --------------------------------------------------------------------------
_EOL_RULE = "perceivo_client/generated/** text eol=lf"


def test_gitattributes_pins_the_generated_package_to_lf() -> None:
    """Without this rule a checkout under ``core.autocrlf=true`` holds CRLF and
    ``--check`` exits 1 on an unchanged tree. Read from the file, so it also
    runs from an unpacked sdist, where there is no repository to ask."""
    lines = (REPO / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert _EOL_RULE in lines, f"{_EOL_RULE!r} is not a line of .gitattributes"


def test_git_resolves_eol_lf_for_every_generated_module() -> None:
    """The rule as git applies it, not as it is spelled: a later line that
    overrides it, or a pattern that stops matching, fails here."""
    inside = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )
    if inside.returncode != 0 or pathlib.Path(inside.stdout.strip()).resolve() != REPO:
        pytest.skip("not a git checkout of this repository (for example an unpacked sdist)")
    modules = sorted(
        path.relative_to(REPO).as_posix()
        for path in (REPO / "perceivo_client" / "generated").rglob("*.py")
    )
    assert len(modules) >= 21, modules  # generated/__init__, models/__init__, the parts
    result = subprocess.run(
        ["git", "-C", str(REPO), "check-attr", "text", "eol", "--", *modules],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )
    assert result.returncode == 0, result.stderr
    resolved = set(result.stdout.splitlines())
    wrong = [
        module
        for module in modules
        if f"{module}: eol: lf" not in resolved or f"{module}: text: set" not in resolved
    ]
    assert wrong == [], f"git does not resolve `text eol=lf` for: {wrong}"
