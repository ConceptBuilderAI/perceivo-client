"""Verify an installed perceivo-client artifact outside its source checkout."""

from __future__ import annotations

import argparse
import base64
import hmac
import json
import pathlib
import urllib.parse
import urllib.request
from importlib.metadata import version

import perceivo_client
from perceivo_client.signing import (
    SigningError,
    build_canonical_request,
    canonical_content_type,
    canonical_organization,
    compute_signature,
    load_golden_vectors,
    split_target,
    verify_signature,
    verify_signed_request,
)


def _installed_artifact() -> pathlib.Path:
    direct_url = next(
        path
        for path in pathlib.Path(perceivo_client.__file__)
        .resolve()
        .parent.parent.glob("perceivo_client-*.dist-info/direct_url.json")
        if path.is_file()
    )
    payload = json.loads(direct_url.read_text(encoding="utf-8"))
    return pathlib.Path(
        urllib.request.url2pathname(urllib.parse.urlparse(payload["url"]).path)
    ).resolve()


def _verify_positive(table: dict[str, object]) -> int:
    vectors = table["vectors"]
    assert isinstance(vectors, list) and vectors
    for vector in vectors:
        raw_path, query = split_target(vector["target"])
        body = None if vector["body_base64"] is None else base64.b64decode(vector["body_base64"])
        canonical = build_canonical_request(
            audience=vector["audience"],
            key_id=vector["key_id_input"],
            method=vector["method"],
            raw_path=raw_path,
            query_string=query,
            body=body,
            content_type=vector["content_type"],
            organization=vector["organization"],
            timestamp=vector["timestamp"],
            nonce=vector["nonce"],
        )
        assert canonical.count("\n") == 10, vector["id"]
        fields = canonical.split("\n")
        assert fields[7] == vector["canonical_content_type"], vector["id"]
        assert fields[8] == vector["canonical_organization"], vector["id"]
        assert hmac.compare_digest(canonical, vector["canonical_request"]), vector["id"]
        assert hmac.compare_digest(
            compute_signature(canonical, table["secret_utf8"]), vector["signature"]
        ), vector["id"]
    return len(vectors)


def _verify_negative(table: dict[str, object]) -> int:
    negatives = table["negative_vectors"]
    assert isinstance(negatives, list) and negatives
    grounds = {case["refused_by"] for case in negatives}
    assert grounds == {"arity", "prelude_binding", "metadata_binding"}, grounds
    for case in negatives:
        assert verify_signature(
            case["signature"], case["canonical_request"], table["secret_utf8"]
        ), case["id"]
        assert case["field_count"] == len(case["canonical_request"].split("\n")), case["id"]
        assert (case["refused_by"] == "arity") == (case["field_count"] != table["field_count"]), (
            case["id"]
        )
        verified = verify_signed_request(
            signature=case["signature"],
            canonical_request=case["canonical_request"],
            secret=table["secret_utf8"],
            audience=case["verifier_audience"],
            key_id=case["verifier_key_id"],
        )
        # Organization binding is checked by the server, so a metadata-binding
        # case still verifies here.
        assert verified == (case["refused_by"] == "metadata_binding"), case["id"]
    return len(negatives)


def _verify_unsignable(table: dict[str, object]) -> int:
    unsignable = table["unsignable_vectors"]
    assert isinstance(unsignable, list) and unsignable
    assert [case["id"] for case in unsignable if case["field_number"] == 8] == [
        "u01-content-type-non-ascii-text",
        "u02-content-type-latin1-high-byte",
        "u03-content-type-newline",
        "u04-content-type-tab",
        "u05-content-type-del-control",
    ]
    for case in unsignable:
        if case["field_number"] == 8:
            refuse = canonical_content_type
            value = base64.b64decode(case["content_type_base64"])
        else:
            refuse = canonical_organization
            values = [
                base64.b64decode(value).decode("utf-8")
                for value in case["organization_values_base64"]
            ]
            value = values if len(values) > 1 else values[0]
        try:
            refuse(value)
        except SigningError:
            pass
        else:
            raise AssertionError(f"{case['id']}: signer accepted an unsignable input")
    return len(unsignable)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-artifact", type=pathlib.Path, required=True)
    args = parser.parse_args()

    package_root = pathlib.Path(perceivo_client.__file__).resolve()
    assert "site-packages" in package_root.parts, package_root
    assert version("perceivo-client") == args.expected_version
    assert _installed_artifact() == args.expected_artifact.resolve()

    table = load_golden_vectors()
    declared = table["vector_counts"]
    assert table["wire_format_revision"] == 3
    assert table["field_count"] == 11
    positive = _verify_positive(table)
    negative = _verify_negative(table)
    unsignable = _verify_unsignable(table)
    assert (positive, negative, unsignable) == (
        declared["positive"],
        declared["negative"],
        declared["unsignable"],
    )
    print(
        f"perceivo-client {args.expected_version}: {positive} positive, "
        f"{negative} correctly-MACed negative, {unsignable} unsignable vectors"
    )


if __name__ == "__main__":
    main()
