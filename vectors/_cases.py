"""The positive cases the generator turns into rows of the vector table.

* ``CASES``: requests that exercise every canonical field except the key id and
  the organization.
* ``KEY_ID_CASES``: requests whose point is the spelling of the key id.
* ``ORGANIZATION_CASES``: requests that carry a ``Perceivo-Organization`` header.

Inputs a signer must refuse are in ``_unsignable_cases.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _constants import MULTIPART_BODY, ORGANIZATION_A, ORGANIZATION_B

# (id, description, method, target, body-bytes-or-None, content-type-or-None)
CASES: list[tuple[str, str, str, str, bytes | None, str | None]] = [
    (
        "v01-get-empty-body-empty-query",
        "GET with no query and no body. The body field is the SHA-256 of zero "
        "bytes, never of '{}' and never empty; the query field is the empty "
        "string and its separators remain. The request has no Content-Type, so "
        "field 8 is the empty string by the same convention.",
        "GET",
        "/v1/orchestrations",
        None,
        None,
    ),
    (
        "v02-post-json-body",
        "POST with a compact JSON body. The bytes hashed are the bytes sent, "
        "never a re-serialization. Content-Type is 'application/json' with no "
        "parameters; compare v32 and v33, same bytes with parameters, three "
        "different signatures.",
        "POST",
        "/v1/orchestrations/9efa4550-e04e-4624-a6f2-684af0330f23/run",
        b'{"inputs":{"prompt":"hello"}}',
        "application/json",
    ),
    (
        "v03-query-order-is-preserved",
        "Query keys arrive in a non-alphabetical order and are signed in that "
        "order. A sorting implementation emits "
        "'archived=false&cursor=abc&limit=10' here and produces a different "
        "signature, so this vector fails against one.",
        "GET",
        "/v1/orchestrations?limit=10&cursor=abc&archived=false",
        None,
        None,
    ),
    (
        "v04-valueless-key",
        "A key with no '=' keeps that distinction from a key with an empty "
        "value: 'flag' stays 'flag'. Submission order is preserved, so this is "
        "'flag&flag=&a=1', not the sorted 'a=1&flag&flag='.",
        "GET",
        "/v1/components?flag&flag=&a=1",
        None,
        None,
    ),
    (
        "v05-empty-value",
        "'?a=' is an empty value, distinct from '?a'.",
        "GET",
        "/v1/components?a=",
        None,
        None,
    ),
    (
        "v06-repeated-key",
        "Repeated keys keep their submission order: 'tag=zeta&tag=alpha&tag=beta' "
        "signs in exactly that order. The server resolves a repeated key to its "
        "last occurrence, so the order carries meaning.",
        "GET",
        "/v1/components?tag=zeta&tag=alpha&tag=beta",
        None,
        None,
    ),
    (
        "v07-percent-2f-in-path",
        "%2F in the path is not decoded: '/a%2Fb' and '/a/b' are different "
        "requests with different signatures.",
        "GET",
        "/v1/files/a%2Fb",
        None,
        None,
    ),
    (
        "v08-percent-encoding-case-preserved",
        "Percent-encoding case is preserved: '%2f' is not normalized to '%2F'. "
        "Compare with v07: same route, different signature.",
        "GET",
        "/v1/files/a%2fb",
        None,
        None,
    ),
    (
        "v09-plus-in-query-value",
        "'+' in a query value stays '+'. Nothing is decoded and nothing is "
        "re-encoded, so '+' is not read as a space.",
        "GET",
        "/v1/logs?q=a+b&r=a%20b",
        None,
        None,
    ),
    (
        "v10-double-slash-path",
        "'//' in the path is preserved, not collapsed.",
        "GET",
        "/v1//components",
        None,
        None,
    ),
    (
        "v11-non-ascii-path",
        "A non-ASCII path segment is signed in its percent-encoded UTF-8 form "
        "(cafe with an acute accent). No Unicode normalization is applied: NFC "
        "and NFD spellings are different bytes and sign differently.",
        "GET",
        "/v1/files/caf%C3%A9",
        None,
        None,
    ),
    (
        "v12-non-utf8-body",
        "A body containing bytes that are not valid UTF-8 (0xff 0xfe 0x00 0x01) "
        "hashes normally: the body is hashed as bytes, never as text.",
        "POST",
        "/v1/files/upload",
        b"\xff\xfe\x00\x01binary",
        "application/octet-stream",
    ),
    (
        "v13-trailing-slash-significant",
        "A trailing '/' is significant: compare with v01, same route, different signature.",
        "GET",
        "/v1/orchestrations/",
        None,
        None,
    ),
    (
        "v14-delete-with-query",
        "DELETE with a query and no body, so the body field is the empty-body digest.",
        "DELETE",
        "/v1/components/abc?cascade=true",
        None,
        None,
    ),
    (
        "v15-empty-query-element",
        "Empty elements between '&' separators are retained in place, so "
        "'a=1&&b=2' canonicalizes to 'a=1&&b=2'. A sorting implementation moves "
        "the empty element to the front and emits '&a=1&b=2'.",
        "GET",
        "/v1/components?a=1&&b=2",
        None,
        None,
    ),
    (
        "v16-value-containing-equals",
        "An '=' inside a value needs no rule at all when the bytes are emitted "
        "verbatim: 'filter=a=b&z=1' signs as itself. There is no key/value "
        "split in which the distinction could be lost.",
        "GET",
        "/v1/logs?filter=a=b&z=1",
        None,
        None,
    ),
    (
        "v17-utf8-body",
        "A UTF-8 body with non-ASCII text, hashed as the encoded bytes.",
        "POST",
        "/v1/conversations",
        '{"message":"café — naïve"}'.encode(),
        "application/json; charset=utf-8",
    ),
    (
        "v18-explicitly-empty-body",
        "An explicitly empty body (zero bytes) is identical to no body at all.",
        "POST",
        "/v1/components/refresh",
        b"",
        "application/json",
    ),
    (
        "v19-permutation-pair-a",
        "Permutation pair, member A. With v20: the same two elements in both "
        "orders. The server resolves a repeated key to its last occurrence, so "
        "v19 means org=victim and v20 means org=attacker, and their signatures "
        "must differ. A sorting implementation returns 'org=attacker&org=victim' "
        "for both and produces one signature for two different requests.",
        "GET",
        "/v1/organizations?org=attacker&org=victim",
        None,
        None,
    ),
    (
        "v20-permutation-pair-b",
        "Permutation pair, member B: v19's elements in reverse submission "
        "order. Compare the signatures with v19: they must not be equal.",
        "GET",
        "/v1/organizations?org=victim&org=attacker",
        None,
        None,
    ),
    (
        "v21-bare-key-order-preserved",
        "A non-alphabetical query whose sorted form differs from "
        "its submission form: 'flag=&flag&a=1' signs as itself, where a sorting "
        "implementation emits 'a=1&flag&flag='. This vector cannot pass against "
        "one.",
        "GET",
        "/v1/components?flag=&flag&a=1",
        None,
        None,
    ),
    # --- canonical_path cases ----------------------------------------------
    # Field 5 is the normalised path, not raw_path. v22/v23/v24 normalise to one
    # path and v25/v26/v27 to another, so each group shares one signature.
    (
        "v22-unreserved-escape-lowercase-hex",
        "Path normalisation step 1 decodes unreserved escapes only: '%7e' "
        "becomes '~', so the path field is '/v1/files/a~b'. Compare with "
        "v23 and v24: all three have one signature. A signature covers every "
        "target that normalises to the same path, because the server acts on "
        "the normalised path.",
        "GET",
        "/v1/files/a%7eb",
        None,
        None,
    ),
    (
        "v23-unreserved-escape-uppercase-hex",
        "Both hex cases decode: '%7E' becomes '~' exactly as '%7e' does. Same "
        "signature as v22 and v24. Contrast v07/v08, where '%2F' and '%2f' are "
        "reserved, are not decoded, and therefore keep their hex-case "
        "difference and sign differently.",
        "GET",
        "/v1/files/a%7Eb",
        None,
        None,
    ),
    (
        "v24-literal-unreserved-character",
        "The same path with the character sent literally. A signer "
        "that emits raw_path verbatim gives v24 this signature and gives v22 "
        "and v23 two others, so it agrees here and fails there.",
        "GET",
        "/v1/files/a~b",
        None,
        None,
    ),
    (
        "v25-dot-segment-removed",
        "Path normalisation step 2 removes dot segments (RFC 3986 5.2.4): "
        "'/v1/x/../components' signs as '/v1/components'. HTTP clients "
        "and the server both remove dot segments, so the normalised path is "
        "the one every hop agrees on.",
        "GET",
        "/v1/x/../components",
        None,
        None,
    ),
    (
        "v26-single-dot-segment-removed",
        "'/./' is removed too: '/v1/./components' signs as "
        "'/v1/components'. Same signature as v25 and v27.",
        "GET",
        "/v1/./components",
        None,
        None,
    ),
    (
        "v27-encoded-dot-segment-decode-then-remove",
        "Step order. '%2E' is unreserved, so step 1 decodes it to '.' and step "
        "2 then removes it as a dot segment: '/v1/x/%2E%2E/components' "
        "signs as '/v1/components'. An implementation that removes dot "
        "segments first finds none to remove and emits "
        "'/v1/x/../components' instead. This is the only vector that "
        "distinguishes the two orders.",
        "GET",
        "/v1/x/%2E%2E/components",
        None,
        None,
    ),
    # --- Content-Type cases (field 8) --------------------------------------
    (
        "v29-absent-content-type-with-a-body",
        "A POST that carries body bytes and no Content-Type header. Field 8 is "
        "the empty string, the same convention the query field uses: not a "
        "guessed default and not an omitted field. An implementation that "
        "defaults an absent header to 'application/octet-stream' produces a "
        "different signature here and agrees everywhere else.",
        "POST",
        "/v1/files/upload",
        b"raw-bytes-no-declared-type",
        None,
    ),
    (
        "v30-multipart-boundary-pair-a",
        "Boundary pair, member A. The body bytes are identical to v31 and only "
        "the multipart 'boundary' parameter differs. Signing Content-Type "
        "prevents the same signed bytes from being re-framed so that the "
        "server's multipart parser reads different parts from them. Because "
        "Content-Type is signed verbatim, the two sign differently. An "
        "implementation that reduces it to the media type and drops parameters "
        "emits one signature for both.",
        "POST",
        "/v1/files/upload",
        MULTIPART_BODY,
        "multipart/form-data; boundary=----X",
    ),
    (
        "v31-multipart-boundary-pair-b",
        "Boundary pair, member B: same bytes, different declared boundary. "
        "Compare the signatures with v30: they must not be equal.",
        "POST",
        "/v1/files/upload",
        MULTIPART_BODY,
        "multipart/form-data; boundary=----Y",
    ),
    (
        "v32-charset-pair-a",
        "Charset pair, member A. Same method, target and body bytes as v02, "
        "with a charset parameter appended. Its signature differs from v02's, "
        "which is what proves parameters are not stripped.",
        "POST",
        "/v1/orchestrations/9efa4550-e04e-4624-a6f2-684af0330f23/run",
        b'{"inputs":{"prompt":"hello"}}',
        "application/json; charset=utf-8",
    ),
    (
        "v33-charset-pair-b",
        "Charset pair, member B: differs from v32 only in the case of the "
        "charset value. Content-Type is not case-folded, so the two sign "
        "differently. v02, v32 and v33 are three distinct signatures over one "
        "set of body bytes.",
        "POST",
        "/v1/orchestrations/9efa4550-e04e-4624-a6f2-684af0330f23/run",
        b'{"inputs":{"prompt":"hello"}}',
        "application/json; charset=UTF-8",
    ),
]

# Vectors whose point is the SUPPLIED form of a field rather than the request.
# (id, description, key-id-as-supplied, method, target, body, content-type)
KEY_ID_CASES: list[tuple[str, str, str, str, str, bytes | None, str | None]] = [
    (
        "v28-key-id-mixed-case-normalised",
        "Key id normalisation. 'key_id_input' is the same UUID as every other "
        "vector's, supplied in uppercase. Field 3 is the lowercase 8-4-4-4-12 "
        "form, so this vector's canonical_request and signature are identical "
        "to v01's. An implementation that uses the string as supplied produces "
        "a different signature here and agrees everywhere else. Normalise by "
        "parsing the UUID and rendering it again. Braced, unhyphenated and "
        "uppercase forms all normalise to the same field 3.",
        "0F8FAD5B-D9CB-469F-A165-70867728950E",
        "GET",
        "/v1/orchestrations",
        None,
        None,
    ),
]


# Field 9 cases. Each carries an organization; every other input repeats a request
# already in CASES.
# (id, description, method, target, body, content-type, organization)
ORGANIZATION_CASES: list[tuple[str, str, str, str, bytes | None, str | None, str]] = [
    (
        "v34-organization-present",
        "A well-formed Perceivo-Organization on a request that also carries a "
        "body and a Content-Type, so field 9 is exercised in a realistic shape "
        "rather than only in isolation. Field 9 is the header verbatim, "
        "lowercase hyphenated 8-4-4-4-12. Compare with v02, the same request "
        "with no organization header: the signatures differ.",
        "POST",
        "/v1/orchestrations/9efa4550-e04e-4624-a6f2-684af0330f23/run",
        b'{"inputs":{"prompt":"hello"}}',
        "application/json",
        ORGANIZATION_A,
    ),
    (
        "v35-organization-pair-a",
        "Organization pair, member A. Identical to v36 in method, target, body "
        "and Content-Type; only the organization differs. Only v34, v35 and v36 "
        "sign a non-empty organization, so these are the rows that fail if an "
        "implementation omits field 9. It is also the same request as v01, "
        "which sends no header: three requests, three signatures.",
        "GET",
        "/v1/orchestrations",
        None,
        None,
        ORGANIZATION_A,
    ),
    (
        "v36-organization-pair-b",
        "Organization pair, member B: same request, different organization. "
        "Compare the signatures with v35: they must not be equal. An "
        "implementation that omits field 9, or signs a constant there, emits "
        "one signature for both, so a signature captured for one organization "
        "would verify when presented with the other's header.",
        "GET",
        "/v1/orchestrations",
        None,
        None,
        ORGANIZATION_B,
    ),
]
