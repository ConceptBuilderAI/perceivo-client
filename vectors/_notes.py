"""The table's ``notes``: what an implementer needs to know that the rows do not say."""

from __future__ import annotations

NOTES: list[str] = [
    "Eleven fields, ten '\\n' separators, no trailing newline. Field 1 is the "
    "constant 'perceivo-hmac-v1' and is never configurable; field 2 is the "
    "audience; field 3 is the key id; field 8 is Content-Type; field 9 is the "
    "organization; field 11, the nonce, is last.",
    "Fields 1-3 and 9 must be bound, not merely present. A signed field that the "
    "verifier never compares with a value it holds itself provides no "
    "protection, because the signer chooses its value. Field 1 is compared for "
    "exact equality; field 2 with the verifier's configured audience; field 3 "
    "with the id of the key whose secret was used. Field 8 is not bound: it is "
    "signed so it cannot be altered in transit, and the server reads the header "
    "itself when it parses the body.",
    "Field 9 must be bound even though field 8 is not. The organization selects "
    "the tenant the request is authorised against, so the verifier must confirm "
    "that the signed value equals the Perceivo-Organization header it received. "
    "Make that comparison after compare_digest has accepted the signature: "
    "before then, both values are unauthenticated client input. Vector n07 "
    "distinguishes an implementation that binds field 9 from one that only "
    "signs it.",
    "The negative_vectors list contains correctly signed canonical requests that "
    "must be rejected. A bare MAC check accepts every one of them. Reject them "
    "all with the same outcome: a distinct reason per check tells an attacker "
    "which check failed.",
    "The negative vectors fall into three classes, given by 'refused_by': "
    "'arity' rows (n01, n02, n06) are rejected on the field count before any "
    "other check; 'prelude_binding' rows (n03, n04, n05) carry all eleven fields "
    "and are rejected on the content of fields 1-3; the 'metadata_binding' row "
    "(n07) has correct fields 1-3 and is rejected only after the MAC check, on "
    "field 9. Check 'field_count' for each row as well as the rejection: a "
    "prelude_binding row with the wrong field count would be rejected on arity "
    "and leave the field 1-3 checks untested.",
    "The audience is a deployment label, assigned by the server and configured "
    "on both sides. It is not a hostname or the Host header, and is never "
    "derived from the request: a verifier that read it from the request would "
    "compare the client's value with itself.",
    "key_id is the API key id as a lowercase hyphenated 8-4-4-4-12 UUID, not the "
    "key prefix, which every key in an organization shares. v28 supplies the "
    "same UUID in uppercase and must produce v01's signature. Normalise by "
    "parsing the UUID and rendering it again, so the only outcomes are the "
    "correct signature or a rejection.",
    "content_type is the Content-Type request header verbatim: not normalised, "
    "not case-folded, parameters not removed. An absent header is the empty "
    "string (v01, v29), as for the query field. v30 and v31 have identical "
    "bodies whose declared multipart boundaries differ, and therefore different "
    "signatures; signing only the media type would give them one signature and "
    "allow the body to be re-framed. v02, v32 and v33 are three signatures over "
    "the same body bytes.",
    "Sign after the body and headers are final. HTTP client libraries generate "
    "the multipart boundary themselves, so a signature computed before the "
    "client sets Content-Type covers a value the request never carries, and the "
    "request fails with a 401.",
    "No field may contain '\\n'. A request that would place a newline in a field "
    "is unsignable and must be rejected, not escaped. A Content-Type header that "
    "appears more than once is also rejected rather than joined or resolved to "
    "one value.",
    "Field 8 admits printable ASCII, 0x20-0x7E, only. A Content-Type containing "
    "any other byte is unsignable and must be rejected when signing, never "
    "escaped or transliterated. This is narrower than RFC 7231, which admits "
    "obs-text in a quoted-string. On printable ASCII, latin-1 and UTF-8 decoding "
    "agree, so a signer and a verifier that decode header bytes differently "
    "still produce the same field. The empty value is allowed (v01, v29).",
    "The unsignable_vectors list is a third kind of vector, distinct from "
    "negative_vectors. A negative vector is a correctly signed string a verifier "
    "must reject (mac_is_correct is true for all of them). An unsignable vector "
    "has no canonical_request and no signature, because the only conforming "
    "response to its input is to refuse to sign. Check these by canonicalising "
    "the input and requiring an error.",
    "body_base64 null means no body; an empty string means a zero-byte body. "
    "Both produce the same digest (see v01 and v18).",
    "The HMAC key is the secret's raw bytes, never a hex or base64 re-encoding "
    "of them. For secret_utf8 those bytes are its UTF-8 encoding, which is why "
    "every positive vector keys on secret_utf8 directly. An issued secret is "
    "different: it is written as hex and must be decoded, as secret_transport "
    "describes.",
    "The canonical request is UTF-8 encoded before HMAC. Every positive vector "
    "here is ASCII, because raw_path and the query string are percent-encoded on "
    "the wire and field 8 is restricted to printable ASCII. The unsignable "
    "vectors include the non-ASCII Content-Type values a signer must reject.",
    "The signature covers no authority: neither the Host header nor an "
    "absolute-form request target. The audience identifies the deployment "
    "instead, and is configured rather than taken from the request.",
    "canonical_path is field 5 and is the normalised path, not raw_path "
    "verbatim. Two operations, in this order: (1) percent-decode unreserved "
    "characters only (A-Z a-z 0-9 - . _ ~), in either hex case; (2) remove dot "
    "segments per RFC 3986 5.2.4. Nothing else changes: '//' is not merged, a "
    "trailing '/' is kept, a reserved escape such as '%2F' is not decoded, and "
    "an escape step 1 did not decode is not case-normalised. The server applies "
    "this transform to every path before routing, and nothing to the query, so "
    "the signature covers the path the server acts on. A signer that emits "
    "raw_path verbatim fails v22, v23, v25, v26 and v27; one that reverses the "
    "two steps fails v27 alone.",
    "The path transform is not injective. v22, v23 and v24 are three request "
    "targets with one signature, and so are v25, v26 and v27. A signature "
    "therefore covers a set of equivalent targets. This is safe because every "
    "target in a set reaches the server as the same normalised path.",
    "canonical_query is field 6 and is the query string verbatim: every byte "
    "after the first '?', in the order sent. Nothing is split, sorted, decoded, "
    "re-encoded, deduplicated or reassembled. An implementation that sorts fails "
    "v03, v04, v06, v15, v20 and v21, and collapses two distinct pairs to a "
    "single signature: v19/v20 and v04/v21.",
    "v35 and v36 are the organization pair: the same request differing only in "
    "the Perceivo-Organization value, with different signatures. Exactly three "
    "positive rows sign a non-empty organization: v34, v35 and v36; the other 33 "
    "sign the empty string. An implementation that omitted field 9 would still "
    "pass those 33 and fail only v34, v35 and v36. Compare either with v01, the "
    "same request with no header: three requests, three signatures.",
    "The five unsignable rows u01-u05 carry 'field_number': 8 and cover the field 8 character set.",
    "u06-u11 are the field 9 unsignable rows ('field_number': 9). Field 9 is "
    "rejected, never normalised: uppercase, braced and unhyphenated UUIDs are "
    "refused rather than converted to the canonical spelling. This differs from "
    "key_id (see v28), which is normalised: key_id is a UUID the server has "
    "already resolved, while field 9 is client text that the signer, the "
    "verifier and the server's authorisation must all read identically. An "
    "implementation that reuses its key_id normaliser for field 9 passes v28 and "
    "fails u06, u07 and u08.",
    "v19 and v20 are a permutation pair: the same two elements in both orders, "
    "with different signatures. The server resolves a repeated key to its last "
    "occurrence, so the two targets mean different things. A verifier that "
    "accepted one signature for both would accept a request whose meaning was "
    "not signed.",
    "Body-size-cap vectors (a body exactly at the cap, and one byte over, "
    "expecting 413) are not included. The body size limit is a server-side "
    "admission control, not a canonicalisation rule.",
]
