# HMAC Request Signing (`v1`)

Request signing lets the Perceivo API verify that a request's method, path,
query, body, `Content-Type` and acting organization were not altered in transit,
that the signature was made for this deployment and with this key, and that the
request is not a replay.

The signature does not cover the exact request line you sent: see "What is not
signed" in section 2 for the fields it omits, and `canonical_path` in section 3
for targets that sign identically.

Signing is opt-in and off by default. A client that does not configure a signing
secret sends unsigned requests.

- Reference implementation: `perceivo_client/signing/`
- Golden vectors: [`../perceivo_client/signing/vectors/hmac_v1_vectors.json`](../perceivo_client/signing/vectors/hmac_v1_vectors.json),
  shipped as package data and read with `from perceivo_client.signing import load_golden_vectors`

This document is the specification of the `v1` signature format.

---

## 1. Enabling signing

<!-- illustrative: names a key id and a secret the reader supplies; not executable here -->

```python
from perceivo_client import Client

client = Client(
    api_key="perceivo_...",  # still sent as X-API-Key
    key_id="9efa4550-e04e-4624-a6f2-684af0330f23",
    signing_secret="...",  # issued once, at key creation
    hmac_audience="perceivo-api-prod",  # the deployment you are calling
)
client.orchestrations.list()  # every request is now signed
```

The key id and signing secret can instead come from the `PERCEIVO_KEY_ID` and
`PERCEIVO_SIGNING_SECRET` environment variables.

The audience cannot. It has no environment variable and is never derived from
`base_url`, a `Host` header or anything else in the environment: it is explicit
configuration, passed at the call site (see `audience` in section 3). To vary it
by deployment, read it from your own configuration:
`Client(..., hmac_audience=settings.perceivo_audience)`.

Configuring some but not all of the three raises `SigningError` when the client
is constructed, so a partially configured client never sends unsigned requests
while appearing to sign them.

To sign a request the client is not making:

<!-- illustrative: names a key id and a secret the reader supplies; not executable here -->

```python
from perceivo_client.signing import sign_request

signed = sign_request(
    method="POST",
    target="/v1/orchestrations/<id>/run",  # the path you will send (section 3)
    body=b'{"inputs":{}}',  # the exact bytes you will send
    content_type="application/json",  # the exact header you will send
    organization=None,  # the exact Perceivo-Organization header you will send
    key_id="...",
    secret="...",
    audience="perceivo-api-prod",
)
signed.headers  # the four X-Perceivo-* headers
signed.canonical_request  # contains no secret; safe to log
```

`target` is the path and query exactly as you will send them. See "Which path
to sign" in section 3.

`content_type`, `organization` and `audience` are required keyword arguments with
no defaults. Pass `content_type=None` or `organization=None` when the request has
no such header.

Sign the organization you send. The server compares field 9 of the signed string
with the `Perceivo-Organization` header it received, after verifying the MAC, and
rejects a difference, so a request that signs one organization and sends another
fails even though its MAC is correct.

---

## 2. The wire format

Signing adds four headers. The API key is still sent as well.

| Header | Value |
| --- | --- |
| `X-Perceivo-Key-Id` | The API key id as a lowercase hyphenated UUID (section 3) |
| `X-Perceivo-Timestamp` | Unix time in seconds, base 10 |
| `X-Perceivo-Nonce` | 8-128 characters from `[A-Za-z0-9_-]`, from a cryptographically secure source, used once |
| `X-Perceivo-Signature` | `v1=` followed by 64 lowercase hex characters |

The audience has no header. Both sides hold it as configuration: a value the
client sends is a value an attacker could choose.

The `v1=` prefix is required. A correct HMAC without the prefix, or with a
different prefix, is rejected with a 401.

### The canonical request

Eleven fields joined by ten `\n` (0x0A) separators, with no trailing newline:

```
perceivo-hmac-v1\n{audience}\n{key_id}\n{METHOD}\n{canonical_path}\n{canonical_query}\n{sha256_hex(body)}\n{content_type}\n{organization}\n{timestamp}\n{nonce}
```

| # | Field | Value | What it prevents |
| --- | --- | --- | --- |
| 1 | domain | the literal `perceivo-hmac-v1` | A signature made for another scheme with the same secret being accepted here |
| 2 | `audience` | the deployment's configured label | A signature captured at one deployment being replayed at another |
| 3 | `key_id` | the API key id, lowercase hyphenated UUID | A signature being presented under a different key |
| 4 | `METHOD` | uppercase, as on the request line | Method substitution |
| 5 | `canonical_path` | the normalised path (section 3) | Path tampering |
| 6 | `canonical_query` | the query string, verbatim (section 3) | Query tampering, including reordering |
| 7 | body digest | lowercase hex SHA-256 of the exact body bytes | Body tampering |
| 8 | `content_type` | the header verbatim, or `""` if absent | Re-framing identical body bytes with a different multipart boundary or charset |
| 9 | `organization` | the `Perceivo-Organization` header verbatim, or `""` if absent | A captured signature being presented with a different organization |
| 10 | `timestamp` | Unix seconds | Replay outside the time window (the server rejects beyond ±300 seconds) |
| 11 | `nonce` | single-use random value | Replay within the time window |

Every field is always present. An absent query, `Content-Type` or
`Perceivo-Organization` header is the empty string, so the canonical request
always has eleven fields. The server checks the field count before it computes
the MAC, so a canonical request with a field missing is rejected on its field
count rather than as a signature mismatch.

Field 9 is rejected rather than normalised. It must be a lowercase, hyphenated
RFC 4122 UUID or empty; uppercase, braced and unhyphenated spellings raise
`SigningError` when signing. The key id, by contrast, is normalised for you:
the key id is a value the server has already resolved, while the organization is
client input that the signer, the verifier and the server's authorisation must all
read identically.

The string is encoded as UTF-8 and passed to HMAC-SHA256, keyed on the signing
secret's raw bytes.

The secret you are issued is text. Perceivo generates 32 random bytes and
issues them once, at key creation, as 64 hex characters. The key is the bytes
those characters encode, so the issued secret must be decoded:
`bytes.fromhex(secret)` in Python, `Buffer.from(secret, 'hex')` in Node.js.
Encoding it as UTF-8 instead produces a 64-byte key that never matches the
server's 32-byte key. Both sides then compute a well-formed HMAC-SHA256, the
digests differ, and the server returns the same 401 as for a wrong key id or a
stale timestamp.

A secret that is not 64 hex characters, such as the `secret_utf8` test secret in
the golden vectors, is keyed on its UTF-8 bytes. The `secret_transport_vectors`
list in the vector table covers both cases and publishes the signature that the
incorrect encoding produces: if your signature for `t01` equals the signature the
table publishes for `t02`, your implementation encodes the secret instead of
decoding it.

Compare with the value the table publishes for `t02`, not with your own output for
`t02`. The two rows have identical inputs and differ only in the published answer,
so a correct implementation computes the same signature for both.

The domain is always first and the nonce always last. A fixed value at the start
means no attacker-chosen prefix can shift the field boundaries.

### Signed fields must also be bound

Fields 1, 2, 3 and 9 protect nothing merely by appearing in the string. A
verifier must also compare each with a value it holds itself:

- field 1 with the constant `perceivo-hmac-v1`;
- field 2 with its own configured audience, never with the request's `Host`
  header;
- field 3 with the id of the key whose secret it used;
- field 9 with the `Perceivo-Organization` header it received, after the MAC
  comparison (see section 7).

A verifier that only runs `compare_digest` accepts a six-field canonical request
(`n01`) and a signature made for another deployment (`n04`). Every check must
fail with the same outcome: a distinct status or message per check tells an
attacker which field to change.

`verify_signed_request(signature=..., canonical_request=..., secret=...,
audience=..., key_id=...)` in this package checks fields 1, 2 and 3, and section
7's negative vectors test it. `verify_signature` is the MAC check alone and
accepts all seven negative vectors.

### What is not signed

- **The host.** The signature covers no authority: neither the `Host` header nor
  an absolute-form request target. The audience identifies the deployment
  instead, and it is configured on both sides rather than read from the request.
- **The scheme or an absolute URL.** The server may see `http` for a request the
  client made over `https`, so a canonical request built from an absolute URL
  would not match.
- **Headers other than `Content-Type` and `Perceivo-Organization`.** Field 8 is
  signed because on a multipart route the body parser, the boundary and the
  charset are all selected from that header, so the body digest alone does not
  determine how the body is read. Field 9 is signed because it selects the
  organization the request is authorised against.

The signature covers the request as routed, not the bytes on the wire.

### The `v1=` prefix

The prefix identifies the signature algorithm, HMAC-SHA256. Because the prefix
does not identify the canonical request format, a verifier must check the field
count before comparing digests (see `n01`, `n02` and `n06` in section 7).

### Server-side rules

- Reject a request when `|now - timestamp| > 300` seconds.
- A nonce is single-use; reject a replayed nonce.
- Compare digests in constant time (`hmac.compare_digest`).
- Check the field count, domain, audience and key id before the digest
  comparison, and the organization after it.
- Reject a signed request that carries `api_key` in the query string. This
  client refuses to sign one.

---

## 3. Canonicalisation rules

Every rule below is pinned by tests and by the golden vectors.

### Character set

`raw_path` and the query string must be printable ASCII (0x21-0x7E): origin-form
and already percent-encoded, exactly as an HTTP client writes them on the request
line. Non-ASCII input raises `SigningError` rather than being encoded on the
caller's behalf, because the encoding an HTTP library applies is that library's
decision.

This check is the only transformation applied to the query string.

### A newline in any field is rejected, never escaped

`\n` is the field separator, so a field containing one would add a field:
`/a?b\nc` and `/a\nb?c` would otherwise produce the same canonical string. Every
field rejects a newline. Escaping is not used, because it would give one
canonical string two spellings and require every implementation to agree on the
escaping scheme.

### `audience` (field 2)

A label, assigned by the server, that identifies the deployment you are calling.
1-64 characters from `[A-Za-z0-9._:-]`, matched as `\A[A-Za-z0-9._:-]{1,64}\Z`.
Case is significant.

| Deployment | Audience |
| --- | --- |
| Production | `perceivo-api-prod` |
| Local development | `perceivo-api-local` |

The audience is not a hostname and must never be derived from one:

- a `Host` header is chosen by the client, so binding it binds a value an
  attacker chooses;
- one deployment is reachable under several hostnames, and each spelling would
  produce a different signature for the same request.

Configure the same label on the client and the server; the verifier compares
field 2 with its own value. This client has no environment variable for it
(section 1) and sends no header for it (section 2).

### `key_id` (field 3)

The API key id as a lowercase hyphenated UUID (8-4-4-4-12), for example
`0f8fad5b-d9cb-469f-a165-70867728950e`. The `X-Perceivo-Key-Id` header carries
the same value.

Callers store UUIDs in whatever case their tooling produced, so normalise the key
id before signing. There must be exactly two outcomes: the normalised spelling,
or a rejection.

- Accepted spellings: hyphenated, unhyphenated, braced, `urn:uuid:`-prefixed, in
  any hex case. The Python reference is `str(uuid.UUID(value))`; the JavaScript
  example implements the same set.
- Anything that is not a UUID is rejected, including the key prefix
  (for example `example-key-prefix`). The prefix is an opaque display label
  shared by every key in an organization, so it cannot identify a key.
- `X-Perceivo-Key-Id` carries the normalised spelling, identical to field 3.

Vector `v28-key-id-mixed-case-normalised` is `v01` with the key id in uppercase.
Both have the same signature.

### `METHOD`

Uppercase ASCII (`^[A-Z]+$`), signed exactly as it appears on the request line. A
lowercase method is rejected, not normalised: signing `GET` while the HTTP
library sends `get` would produce a 401. The client's transport signs the method
`httpx` has already uppercased, so `client.request("delete", ...)` works.

### `canonical_path`

#### Which path to sign

Sign the path exactly as you send it, still percent-encoded: the API checks
the signature over the path it receives. The query is signed as sent too.
Normalisation (below) is applied to that path on both sides.

#### Normalisation

The signature covers the path as the API normalises it, not the bytes you sent.
The path (with the query removed) goes through two operations, in this order:

1. Percent-decode escapes of unreserved characters only (`A-Z a-z 0-9 - . _ ~`).
   Both hex cases decode: `%7e` and `%7E` both become `~`.
2. Remove dot segments as specified by RFC 3986 section 5.2.4, applied to the
   output of step 1.

Nothing else changes.

| Case | Rule | Reason |
| --- | --- | --- |
| Trailing `/` | Significant: `/x` and `/x/` differ | They are different routes |
| `//` | Kept | Dot-segment removal does not merge slashes |
| `%7e` / `%7E` / `~` | All three sign identically | `~` is unreserved, so both escapes decode |
| `%2F` vs `%2f` | Different signatures, neither decoded | `/` is reserved; decoding it would make `/a%2Fb` and `/a/b` sign alike although they are different resources |
| `%C3%A9` (`é`) | Kept encoded | Not unreserved |
| `.` and `..` segments | Removed | The server removes them before routing |
| `%2E%2E` | Removed | `%2E` is unreserved, so step 1 produces `..`, which step 2 removes; this is why the order matters |
| `%zz`, a trailing `%` | Kept as written | Not a well-formed escape |
| Non-ASCII (`/café`) | Rejected | Percent-encode it (`/caf%C3%A9`) exactly as you will send it |

#### Why the path is normalised and the query is not

The API applies exactly this transform to every request path before routing, and
applies nothing to the query. The signature covers what the server acts on: for
the path that is the normalised form, and for the query it is the bytes as sent.

#### Targets that sign identically

`/a/%7eb` and `/a/~b` produce one signature, as do `/v1/x/../c` and
`/v1/c`. A signature covers every target that normalises to the same path,
not the exact bytes on the request line. This is safe because every such target
reaches the server as the same path. It does not apply to the query, where
different byte sequences can mean different things.

#### Implementing the transform

Do not use a general-purpose URL normaliser. `new URL(...).pathname` in
JavaScript and `os.path.normpath` or `path.normalize` in most languages do more
than these two steps: they merge `//`, remove trailing slashes or decode reserved
escapes, and any of those changes the field. Implement the two steps directly;
the reference implementation does so in about 25 lines.

Vectors `v22`-`v27` test this rule. A signer that signs the path as sent fails
`v22`, `v23`, `v25`, `v26` and `v27`; a signer that reverses the two steps fails
`v27`.

**Rejected targets.** Each of these raises `SigningError` when signing:

- a target that does not begin with `/`: absolute-form (`http://host/a`) and
  `OPTIONS *`. The server discards the authority of an absolute-form target
  before the application sees it;
- a target containing `#`: the fragment is never sent to the server;
- a target ending in a bare `?`: an empty query cannot be distinguished from no
  query. Send `/x`, not `/x?`.

### `canonical_query`

An empty or absent query is the empty string; the separators remain, so the
canonical request always has eleven fields.

Otherwise the field is the query string verbatim: every byte after the first `?`
of the request target, in the order sent. Nothing is split, sorted, decoded,
re-encoded, deduplicated or reassembled.

| Query in | Canonical query | |
| --- | --- | --- |
| `limit=10&cursor=abc&archived=false` | the same | Order is kept |
| `a=1&&b=2` | the same | An empty element is kept in place |
| `flag` vs `flag=` | each as written | Different requests, different signatures |
| `filter=a=b&z=1` | the same | Nothing is split, so `=` inside a value needs no rule |
| `q=a+b&r=a%20b` | the same | `+` stays `+` and `%20` stays `%20` |
| `%2f` vs `%2F` | each as written | Hex case is a byte difference |

#### Why the query is signed verbatim

A sorted query would give `?org=attacker&org=victim` and
`?org=victim&org=attacker` the same signature. The server resolves a repeated
key to its last occurrence, so those two targets mean different things. Signing
the bytes as sent gives them different signatures. An implementation that sorts
the query fails vectors `v03`, `v04`, `v06`, `v15`, `v20` and `v21`.

#### Sign the query your transport sends

Because the query is signed as sent, it must not change between signing and
sending. If an HTTP library, URL builder or proxy rewrites the query after you
sign, the server returns a 401. Build the request first, then sign the target the
transport will send. The client's own transport signs the target `httpx` has
already prepared.

> In JavaScript, do not use `URLSearchParams` for this: it decodes, re-encodes and
> can reorder. Take the raw substring after the first `?`.

### Body

Lowercase hex SHA-256 of the exact bytes sent.

- An absent or empty body is the SHA-256 of zero bytes:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. It is never
  the digest of `{}`, and the field is never empty.
- A `str` body is encoded as UTF-8 with no Unicode normalisation. NFC and NFD
  spellings of the same text are different bytes and sign differently.
- A body that is not valid UTF-8 is hashed as bytes like any other.
- Streaming bodies cannot be signed and raise `SigningError`. Read them into bytes
  first and send those bytes. `httpx` builds multipart bodies as streams, so the
  client's transport reads a multipart body into bytes once (`request.read()`),
  signs those bytes and sends the same bytes with a `Content-Length`. Every
  multipart method (`files.upload`, `files.replace_content` and the
  infrastructure imports and ingests) is signed this way, and holds the whole
  encoded body in memory.

### `content_type` (field 8)

The `Content-Type` request header, verbatim: not normalised, not case-folded, and
with its parameters. An absent header is the empty string.

| Header sent | Field 8 |
| --- | --- |
| *(absent)* | *(empty)* |
| `application/json` | `application/json` |
| `application/json; charset=utf-8` | `application/json; charset=utf-8` |
| `application/json; charset=UTF-8` | `application/json; charset=UTF-8`, a different field |
| `multipart/form-data; boundary=----X` | `multipart/form-data; boundary=----X` |

Do not reduce the header to its media type. Changing the multipart `boundary`
parameter changes how identical body bytes are split into form fields, and the
body digest does not constrain it. Vectors `v30-multipart-boundary-pair-a` and
`v31-multipart-boundary-pair-b` have identical bodies, differ only in
`boundary`, and have different signatures.

Field 8 admits printable ASCII (0x20-0x7E) only. A `Content-Type` containing any
other byte cannot be signed; `unsignable_vectors` rows `u01`-`u05` cover this.

A repeated `Content-Type` header is rejected rather than resolved by picking one
value, because the signer and the server's parser might pick differently.
`httpx.Headers.get` and Node.js's `headers['content-type']` both join repeated
values with `", "`, which hides the repetition; read the header as a list
(`get_list`) and let the signer reject it.

#### Sign after the request is final

HTTP client libraries generate the multipart `boundary` themselves, so a
signature computed before the request is built covers a `Content-Type` the
request never carries. Build the request, read its final headers and body, sign,
then add the signature headers. The client's transport does this and reads
`Content-Type` from the built request.

### Timestamp and nonce

- **Timestamp**: Unix time in seconds, base 10, digits only: no sign, no
  fractional part, no leading zero unless the value is `0`. It must match the
  `X-Perceivo-Timestamp` header exactly.
- **Nonce**: 8-128 characters from `[A-Za-z0-9_-]`, from a cryptographically
  secure random source. A counter or a value derived from the time is not
  acceptable.

### Retries

Sign each attempt, and generate a new timestamp and nonce for every retry. The
server rejects a reused nonce as a replay. The client's transport does this.

---

## 4. The golden vectors

[`../perceivo_client/signing/vectors/hmac_v1_vectors.json`](../perceivo_client/signing/vectors/hmac_v1_vectors.json)
lists requests with the canonical request and signature each must produce. This
client is tested against it, and any other implementation can be.

The table declares `"wire_format_revision": 3` and `"field_count": 11`. Check both
before using it.

### Reading the table

The table ships in the `perceivo-client` package. Read it with the accessor
rather than a file path:

<!-- illustrative: the body is the reader's own verifier, left as an ellipsis -->

```python
from perceivo_client.signing import load_golden_vectors

table = load_golden_vectors()
assert table["wire_format_revision"] == 3
assert table["field_count"] == 11

for vector in table["vectors"]:
    canonical, signature = my_canonicaliser(vector)  # your implementation
    assert canonical == vector["canonical_request"], vector["id"]
    assert signature == vector["signature"], vector["id"]
```

Pass `vector["key_id_input"]` to your canonicaliser, not `vector["key_id"]`. The
table publishes both the spelling the caller held and the normalised spelling the
signer must produce; using the normalised one would make `v28` test nothing.

`golden_vectors_bytes()` returns the exact bytes of the table, so you can record
a hash of the file you validated against. The inputs, canonical requests and
signatures do not change within `v1`; descriptive text may.

The `secret_utf8` value in the table is a published test constant that protects
nothing. Every row maps `(audience, key_id, method, path, query, body,
content_type, organization, timestamp, nonce, secret)` to a signature, so the
key must be included for anyone to reproduce a row.

> **Warning:** the test secret is not a credential and must never be used as one.
> It appears in the table and in the `openssl` command below. Real signing secrets are issued once, at key creation, and never appear
> in documentation. If a value in this section matches one of your secrets,
> rotate that secret.

All positive vectors share one secret, audience, timestamp and nonce:

| | |
| --- | --- |
| Secret (UTF-8), test value only | `perceivo-test-signing-secret-v1` |
| Audience | `perceivo-api-local` |
| Key id | `0f8fad5b-d9cb-469f-a165-70867728950e` |
| Timestamp | `1767225600` (2026-01-01T00:00:00Z) |
| Nonce | `sT8kQ2vX7wLpR4nB1mZ6yH0j` |

### The primary vector

```
id:           v01-get-empty-body-empty-query
audience:     perceivo-api-local
key_id:       0f8fad5b-d9cb-469f-a165-70867728950e
method:       GET
target:       /v1/orchestrations
body:         (none)
content-type: (absent)
timestamp:    1767225600
nonce:        sT8kQ2vX7wLpR4nB1mZ6yH0j
secret:       perceivo-test-signing-secret-v1
```

Canonical request, as a Python `repr` so the separators are visible. The query
(field 6), `Content-Type` (field 8) and `Perceivo-Organization` (field 9) are
all empty, and appear as consecutive `\n\n\n`:

```
'perceivo-hmac-v1\nperceivo-api-local\n0f8fad5b-d9cb-469f-a165-70867728950e\nGET\n/v1/orchestrations\n\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n\n\n1767225600\nsT8kQ2vX7wLpR4nB1mZ6yH0j'
```

Signature:

```
v1=ee71c0810679e5b5477186d4d1ca0444d7823b8be284a0a9bc4a07bd9e1ebdd8
```

The table is authoritative. To check these values against the installed table:

<!-- runnable: executed by tests/test_docs_hmac_guide_snippets.py -->

```python
from perceivo_client.signing import load_golden_vectors

table = load_golden_vectors()
assert table["wire_format_revision"] == 3
assert table["field_count"] == 11
v01 = next(v for v in table["vectors"] if v["id"] == "v01-get-empty-body-empty-query")
print(repr(v01["canonical_request"]))  # must equal the repr above
print(v01["signature"])  # must equal the signature above
```

To reproduce the signature without any Perceivo code (the `-hmac` argument is the
published test secret; never pass a real secret on a command line, where it is
recorded in shell history):

```bash
printf 'perceivo-hmac-v1\nperceivo-api-local\n0f8fad5b-d9cb-469f-a165-70867728950e\nGET\n/v1/orchestrations\n\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n\n\n1767225600\nsT8kQ2vX7wLpR4nB1mZ6yH0j' \
  | openssl dgst -sha256 -hmac 'perceivo-test-signing-secret-v1'   # test value
```

`printf` interprets the `\n` escapes; `echo` does not on some shells and may add a
trailing newline, which changes the digest. The canonical request has no trailing
newline.

### Canonical query examples

| Vector | Query in | Canonical query | A sorting implementation emits |
| --- | --- | --- | --- |
| `v03-query-order-is-preserved` | `limit=10&cursor=abc&archived=false` | *the same* | `archived=false&cursor=abc&limit=10` |
| `v04-valueless-key` | `flag&flag=&a=1` | *the same* | `a=1&flag&flag=` |
| `v05-empty-value` | `a=` | *the same* | *the same* |
| `v06-repeated-key` | `tag=zeta&tag=alpha&tag=beta` | *the same* | `tag=alpha&tag=beta&tag=zeta` |
| `v09-plus-in-query-value` | `q=a+b&r=a%20b` | *the same* | *the same* |
| `v15-empty-query-element` | `a=1&&b=2` | *the same* | `&a=1&b=2` |
| `v16-value-containing-equals` | `filter=a=b&z=1` | *the same* | *the same* |
| `v21-bare-key-order-preserved` | `flag=&flag&a=1` | *the same* | `a=1&flag&flag=` |

The canonical query is always the query as sent. The last column shows whether a
mismatch comes from sorting.

### The permutation pair

`v19-permutation-pair-a` and `v20-permutation-pair-b` contain the same two query
elements in both orders:

| Vector | Target | Signature |
| --- | --- | --- |
| `v19` | `/v1/organizations?org=attacker&org=victim` | `v1=c2987780...` |
| `v20` | `/v1/organizations?org=victim&org=attacker` | `v1=2ca93fef...` |

They have different signatures. The server resolves a repeated key to its last
occurrence, so `v19` means `org=victim` and `v20` means `org=attacker`. If your
implementation produces one signature for both, it is sorting the query.

### Path normalisation cases

Every vector has a `canonical_path` field beside `raw_path`, so the effect of
normalisation is visible without running anything.

| Vector | `raw_path` | `canonical_path` | A verbatim-path implementation emits |
| --- | --- | --- | --- |
| `v22-unreserved-escape-lowercase-hex` | `/v1/files/a%7eb` | `/v1/files/a~b` | `/v1/files/a%7eb` |
| `v23-unreserved-escape-uppercase-hex` | `/v1/files/a%7Eb` | `/v1/files/a~b` | `/v1/files/a%7Eb` |
| `v24-literal-unreserved-character` | `/v1/files/a~b` | `/v1/files/a~b` | *the same* |
| `v25-dot-segment-removed` | `/v1/x/../components` | `/v1/components` | `/v1/x/../components` |
| `v26-single-dot-segment-removed` | `/v1/./components` | `/v1/components` | `/v1/./components` |
| `v27-encoded-dot-segment-decode-then-remove` | `/v1/x/%2E%2E/components` | `/v1/components` | `/v1/x/%2E%2E/components` |

`v22`, `v23` and `v24` share one signature, and `v25`, `v26` and `v27` share
another: different targets, one normalised path, one signature.

`v27` tests the order of the two steps. `%2E` decodes to `.`, so decoding first
gives `/v1/components`; removing dot segments first gives
`/v1/x/../components` and a different signature. It is the only vector that
distinguishes the two orders.

### Key id and Content-Type cases

| Vector | What it tests |
| --- | --- |
| `v28-key-id-mixed-case-normalised` | `v01` with an uppercase key id and the same signature. Fails if field 3 is not normalised. |
| `v29-absent-content-type-with-a-body` | A body with no `Content-Type`: field 8 is the empty string and the string still has eleven fields. |
| `v30-multipart-boundary-pair-a` / `v31-multipart-boundary-pair-b` | Identical bodies, different `boundary`, two signatures. Fails if the media type is reduced or parameters are removed. |
| `v02-post-json-body` / `v32-charset-pair-a` / `v33-charset-pair-b` | One body, three headers (`application/json`, `; charset=utf-8`, `; charset=UTF-8`), three signatures. Parameter presence and case both matter. |

The other path cases (`v07`/`v08` `%2F` vs `%2f`, `v10` `//`, `v11`
percent-encoded UTF-8, `v13` trailing slash) are unchanged by normalisation,
which shows that the transform does nothing more than its two steps. The body
cases (`v12` non-UTF-8, `v17` UTF-8, `v18` explicitly empty) each have a
`description` in the table.

Body-size-limit vectors are not included: the body size limit is a server-side
admission control, not a canonicalisation rule.

To regenerate the table, run `python vectors/generate_vectors.py` from the
repository root. A change to any input, canonical request or signature is a
change to the wire format.

### Parser dependence

The request target the server's application sees is whatever its HTTP parser
produces. The table records the parser the server is specified against
(`httptools`, `uvicorn` 0.35.0) under `server_parser_contract`. These values are
declared, not measured, by this repository.

---

## 5. Debugging a signature mismatch

1. Print your canonical request as a `repr` (or JSON-escaped in JavaScript). It
   contains no secret and is safe to log. Most mismatches are visible here.
2. Count the fields: eleven, with ten `\n` separators and no trailing newline. If
   you have ten, `organization` (field 9) is missing; it is present as the empty
   string when you send no header. Nine means `Content-Type` is missing too.
3. Check field 1 is exactly `perceivo-hmac-v1` and field 2 is the audience the
   server is configured with, not your hostname or `base_url`.
4. Check field 3 is the lowercase hyphenated key id and is identical to the
   `X-Perceivo-Key-Id` header you sent.
5. Check the body field is the digest of the bytes you sent, not of a
   re-serialisation of your payload, and not of `{}` for a GET.
6. Check field 8 is the `Content-Type` your HTTP client sent, with its parameters
   and case. For a multipart upload, read it from the built request: the client
   generated the `boundary`.
7. Check the timestamp and nonce in the string are identical to the headers.
8. Check that you signed the path you sent (section 3, "Which path to sign").
   Then check that nothing re-encoded, reordered or trimmed the target after you
   signed it. The query is signed as sent, so reordering is the most common
   cause.
9. Compare your canonical query with the raw substring after the first `?`. They
   must be identical; if yours is in alphabetical order, you are sorting.
10. Compare your path field with `canonical_path`. If your target contained
    `%7e`, `%7E`, `.` or `..` and the field still does, you skipped
    normalisation. If `%2F` was decoded, `//` was merged or a trailing `/` was
    removed, you normalised too much, probably with a general-purpose URL helper.
    See section 3.
11. Confirm your clock is within 300 seconds of the correct time.
12. Check that the secret is decoded from hex rather than encoded as UTF-8: if
    your signature for `t01` equals the published `t02` signature, it is encoded.
13. If the endpoint is under `/v1/marketplace/` or another public prefix, the
    signature is not checked at all; see section 8.

---

## 6. The `X-Perceivo-Key-Id` header

The header carries the API key id: the UUID that identifies the key, normalised
to its lowercase hyphenated form and identical to canonical field 3. It is not
the key prefix, which is an opaque display label shared by every key in an
organization. This client rejects a key prefix rather than signing it.

A server that expects the key prefix in this header does not reproduce vector
`v28`.

---

## 7. The negative vectors

A MAC check alone does not verify everything this format signs. These vectors
test whether a verifier binds the signed fields (see "Signed fields must also be
bound" in section 2).

Every row in `negative_vectors` is correctly signed with the published secret,
so a bare digest comparison accepts all of them. Each row also has
`verifier_audience`, `verifier_key_id` and `presented_organization`: the
audience the verifier is configured with, the key id it resolved, and the
organization header the request carried.

Each row's `refused_by` gives the check that must reject it:

| `refused_by` | Rows | Rejected on | Before the MAC check? |
| --- | --- | --- | --- |
| `arity` | `n01`, `n02`, `n06` | the field count, before any field is read | yes |
| `prelude_binding` | `n03`, `n04`, `n05` | the content of fields 1-3, compared with values the server holds | yes |
| `metadata_binding` | `n07` | field 9, compared with the organization header the server received | no, after `compare_digest` |

The `prelude_binding` rows have all eleven fields, so only the field 1-3 checks
can reject them. Check each row's `field_count` as well as the rejection: a row
rejected on its field count does not test the field 1-3 checks.

`n07` is the one row that passes the field count, the field 1-3 checks and the
MAC check. Only comparing field 9 with the received header, after the digest
comparison, rejects it. Before the MAC check both values are unauthenticated
client input, so comparing them proves nothing.

| Vector | What is wrong | What accepting it would allow |
| --- | --- | --- |
| `n01-six-field-downgrade` | Six fields: method, path, query, body digest, timestamp and nonce only | Every other field unchecked |
| `n02-nine-field-downgrade` | Nine fields: no `Content-Type` and no organization | Field 8 unbound, so a multipart body could be re-framed |
| `n06-ten-field-downgrade` | Ten fields: the organization field omitted rather than empty | Field 9 unbound, so a captured signature could be presented with another organization. It differs from `v01`, which signs field 9 as the empty string: same value, different field count |
| `n07-organization-metadata-unbound` | Field 9 names one organization; `presented_organization` names another. Field count, fields 1-3 and MAC are correct | Field 9 signed but never compared, so a captured signature could be presented with another organization |
| `n03-wrong-domain-separator` | Field 1 is `perceivo-hmac-v2` | A signature made for another scheme with the same secret accepted here |
| `n04-audience-mismatch` | Field 2 is `perceivo-api-prod`; the verifier is `perceivo-api-local` | A signature made for one deployment accepted at another |
| `n05-key-id-mismatch` | Field 3 names a different key from the one whose secret signed it | A signature presented under another key |

Check both that each MAC is correct and that each row is rejected:

<!-- runnable: executed by tests/test_docs_hmac_guide_snippets.py -->

```python
from perceivo_client.signing import (
    load_golden_vectors,
    verify_signature,
    verify_signed_request,
)

table = load_golden_vectors()

# Every class must be present, or the loop below could pass without testing one.
grounds = {n["refused_by"] for n in table["negative_vectors"]}
assert grounds == {"arity", "prelude_binding", "metadata_binding"}, grounds

for negative in table["negative_vectors"]:
    # The MAC is correct, so a rejection below is due to binding, not the digest.
    assert verify_signature(
        negative["signature"], negative["canonical_request"], table["secret_utf8"]
    ), negative["id"]

    # Each row has the field count its class requires.
    assert negative["field_count"] == len(negative["canonical_request"].split("\n")), negative["id"]
    assert (negative["refused_by"] == "arity") == (
        negative["field_count"] != table["field_count"]
    ), negative["id"]

    verified = verify_signed_request(
        signature=negative["signature"],
        canonical_request=negative["canonical_request"],
        secret=table["secret_utf8"],
        audience=negative["verifier_audience"],
        key_id=negative["verifier_key_id"],
    )

    if negative["refused_by"] == "metadata_binding":
        # verify_signed_request takes no request headers, so it cannot compare
        # field 9 with the received organization and accepts n07. A server must
        # reject n07 itself, after compare_digest.
        assert verified, negative["id"]
    else:
        assert not verified, negative["id"]
```

`n01`, `n02` and `n06` show why the field count is checked before the digests are
compared: all three have a `v1=` signature and a correct MAC.

`n07` shows the opposite for field 9. Fields 1-3 are compared with values the
server holds (a constant, its configured audience, the key id it resolved), so
those checks are meaningful before authentication. Field 9 is compared with
another client-supplied value, so the check is meaningful only after the MAC has
been verified.

Reject all seven with the same outcome. Reporting which check failed helps an
attacker, and for the checks after `compare_digest` it would also confirm that
the signature itself was valid.

---

## 8. Public paths are not signature-checked

Signing is enabled for a key by setting its `auth_mode` to `hmac`. This protects
requests that authenticate with that key. It has no effect on paths that
authenticate with no key.

Some path prefixes are public: the request never resolves a key, so there is no
`auth_mode` to consult. On those requests the `X-Perceivo-*` headers are not
parsed or verified, and sending them changes nothing.

The public prefixes are:

```text
/ping   /health   /ready   /docs   /redoc   /openapi.json   /metrics
/v1/marketplace/
```

`/v1/marketplace/` is a customer API surface, not a health or documentation
endpoint. Requests to it are not signature-protected, whatever your keys'
`auth_mode`. If your threat model requires integrity protection for the
marketplace, request signing is not the control that provides it.
