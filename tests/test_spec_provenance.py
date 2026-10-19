"""The vendored OpenAPI document and its provenance record.

Checks that need the upstream document are the upstream check in RELEASING.md;
this module checks what the repository can verify alone.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATTRIBUTES_PATH = ROOT / ".gitattributes"
SPEC_PATH = ROOT / "openapi" / "openapi-v1.json"
MANIFEST_PATH = ROOT / "openapi" / "spec_provenance.json"

SPEC_BYTES = SPEC_PATH.read_bytes()
SPEC = json.loads(SPEC_BYTES)
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))

_SHA256 = re.compile(r"[0-9a-f]{64}")
_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


def _canonical(value: object) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"


def _leaf_strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _leaf_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _leaf_strings(item)]
    return [value] if isinstance(value, str) else []


class TestTheRecordIdentifiesTheSpecByContentOnly:
    def test_the_record_has_exactly_the_sections_the_check_reads(self) -> None:
        assert sorted(MANIFEST) == ["_comment", "generator", "upstream", "vendored"]

    def test_the_upstream_document_is_named_by_hash_and_version(self) -> None:
        upstream = MANIFEST["upstream"]
        assert sorted(upstream) == ["_role", "sha256", "version"]
        assert _SHA256.fullmatch(upstream["sha256"]), upstream["sha256"]
        # The transform leaves ``info`` unchanged.
        assert upstream["version"] == SPEC["info"]["version"]

    def test_no_recorded_value_is_a_url_or_a_path_outside_this_repository(self) -> None:
        values = _leaf_strings(MANIFEST)
        assert values, "the scan found no strings; it would pass on anything"
        offending = [
            text for text in values if "://" in text or "github" in text.lower() or ":\\" in text
        ]
        assert offending == []


class TestTheRecordAgreesWithTheSpec:
    def test_the_recorded_hash_is_the_committed_spec_bytes(self) -> None:
        assert hashlib.sha256(SPEC_BYTES).hexdigest() == MANIFEST["vendored"]["sha256"]

    def test_the_recorded_counts_are_the_spec_counts(self) -> None:
        operations = sum(1 for item in SPEC["paths"].values() for key in item if key in _METHODS)
        assert MANIFEST["vendored"]["paths"] == len(SPEC["paths"])
        assert MANIFEST["vendored"]["operations"] == operations


class TestTheCommittedSpecBytesAreCanonical:
    def test_the_spec_is_stored_in_the_form_the_transform_writes(self) -> None:
        assert _canonical(SPEC) == SPEC_BYTES

    def test_the_spec_is_pinned_to_lf(self) -> None:
        lines = ATTRIBUTES_PATH.read_text(encoding="utf-8").splitlines()
        assert "openapi/openapi-v1.json text eol=lf" in lines
        assert b"\r" not in SPEC_BYTES
        assert SPEC_BYTES.endswith(b"\n")

    def test_a_crlf_copy_does_not_match_the_recorded_hash(self) -> None:
        crlf = SPEC_BYTES.replace(b"\n", b"\r\n")
        assert hashlib.sha256(crlf).hexdigest() != MANIFEST["vendored"]["sha256"]
