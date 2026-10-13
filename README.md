# perceivo-client

The Python client for the **Perceivo Platform API**. Use it to run
orchestrations and capabilities, read run results, manage components, files and
webhooks, and inspect your organization's access from agents, CI pipelines and
your own applications.

`perceivo-client` is a typed REST client: responses are Pydantic v2 models
generated from the public OpenAPI contract, and every error is a typed
exception. It is a separate package from `perceivo`, the component-authoring
framework.

**Documentation:** https://perceivo.ai/docs

## Install

```bash
pip install perceivo-client
```

`perceivo-client` supports Python 3.11+ and depends only on `httpx>=0.27.0` and
`pydantic>=2.10.0`. The Pydantic floor is required by the generated models.

## Quickstart

You need a Perceivo service-account API key allowed to read its own access and
to execute the orchestration you choose. Set it in the environment rather than
in source code:

| Variable | Value |
|----------|-------|
| `PERCEIVO_API_KEY` | your service-account API key |
| `PERCEIVO_ORCHESTRATION_ID` | an existing orchestration you may execute |
| `PERCEIVO_API_URL` | optional; defaults to `https://api.perceivo.ai` |

This example starts real, potentially billable work and does not cancel it. It
assumes the orchestration accepts a `prompt` input; adapt the input body to your
orchestration's definition. Execution either returns a `run_id` at once or
accepts the work onto a queue and returns a `request_id`; supply a
`callback_url` to be notified when queued work completes.

```python
import os

from perceivo_client import Client

orchestration_id = os.environ["PERCEIVO_ORCHESTRATION_ID"]

# Reads PERCEIVO_API_KEY (and the optional PERCEIVO_API_URL) from the
# environment; pass api_key=... / base_url=... to set them explicitly.
with Client() as client:
    # 1. Who am I? The service account's organization and effective access.
    me = client.auth.whoami()
    print(me.organization_id, me.effective_privileges)

    # 2. Run the orchestration. The identifiers are nested under `result`.
    execution = client.orchestrations.run(orchestration_id, {"input": {"prompt": "hi"}})
    execution_result = execution.result or {}
    run_id = execution_result.get("run_id")
    request_id = execution_result.get("request_id")

    # 3. Read the run's result, or report the queued request.
    if run_id:
        result = client.runs.result(run_id)
        print(result)
    elif request_id:
        print(f"queued request accepted: {request_id}")
    else:
        raise RuntimeError("execution response contained neither run_id nor request_id")
```

A returned `run_id` does not mean the run has finished: `client.runs.get(run_id)`
reports its status, and `client.runs.cancel(run_id)` stops it.

### Authentication

| Source | Base URL | API key |
|--------|----------|---------|
| Explicit argument | `Client(base_url=...)` | `Client(api_key=...)` |
| Environment | `PERCEIVO_API_URL` | `PERCEIVO_API_KEY` |
| Default | `https://api.perceivo.ai` (production) | none; a key is required |

The key is sent as the `X-API-Key` header on every request. If you omit
`PERCEIVO_API_URL`, the client targets **production**. With no key anywhere,
constructing a client raises `MissingCredentialsError`.

`AsyncClient` takes the same keyword arguments as `Client` and exposes the same
namespaces with awaitable methods:

```python
from perceivo_client import AsyncClient

async with AsyncClient() as client:
    me = await client.auth.whoami()
```

### Timeouts

Every request is bounded by the client's `timeout` (30 seconds by default;
`None` disables the limit), except `files.upload`, `files.replace_content` and
the three infrastructure ingests (`ingest_search_index`,
`ingest_vector_store_collection` and `ingest_cache`). Those wait at least 150
seconds for the response: a longer `timeout` is kept, and `None` stays
unbounded. One slow operation does not need a slow client:
`with_options` returns a client that shares the original's credentials,
signing, retry settings and connection pool, and sends its requests with a
different timeout.

```python
from perceivo_client import Client

client = Client(max_retries=3, backoff_factor=0.5, timeout=30.0)

# Starting an intelligence answers only once its services are deployed.
started = client.with_options(timeout=180.0).intelligence.start(intelligence_id)
```

`AsyncClient.with_options(timeout=...)` is the async form. The timeout is
applied to each request, so it also holds for an `http_client` you pass in.

### Rate limiting and retries

Every response's `X-RateLimit-Limit`, `X-RateLimit-Remaining` and
`X-RateLimit-Reset` headers are parsed into `client.rate_limit`, a
`RateLimitInfo`. The per-address limit reported in `Perceivo-RateLimit-*`
headers is in its `address_limit`, `address_remaining` and `address_reset`
fields. Retry safety depends on the method:

| Request | 429 / 502 / 503 / 504 behavior |
|---------|---------------------------------|
| `GET` | Retries up to `max_retries`, honoring `Retry-After` and then using exponential backoff. |
| `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS` | Makes one request and raises the typed error. |

A status cannot prove that a mutation did not already complete. If a mutation
raises `PerceivoRateLimitError`, wait for its advertised delay, re-read the
affected resource using a stable identifier, and decide whether another action
is needed. Do not blindly resend the original payload:

```python
import time

from perceivo_client import Client, PerceivoRateLimitError

client = Client()
try:
    client.orchestrations.update(orchestration_id, update_body)
except PerceivoRateLimitError as exc:
    if exc.retry_after is not None:
        time.sleep(exc.retry_after)
    current = client.orchestrations.get(orchestration_id)
    # Compare current state with update_body before deciding whether to retry.
```

Read-like `POST` wrappers also make one attempt:
`client.infrastructure.query_search_index`,
`client.infrastructure.query_vector_store_collection`,
`client.infrastructure.export_search_index`,
`client.infrastructure.export_vector_store_collection`, `client.components.validate`,
`client.capabilities.evaluate`, and `client.webhooks.test`. The client cannot
prove that these operations are safe to replay.

A `429` whose code is `execution_locked` is not a rate limit: the organization's
cost-incurring work is blocked until its budget is restored. It raises
`PerceivoExecutionLockedError` and is never retried.

The focused snippets in this and the following sections are excerpts, not standalone
notebook cells: they assume a configured client and the named application inputs.
The retry excerpt above, for example, requires `orchestration_id` and
`update_body`.

### Pagination

Most list operations page by `page`/`page_size` and answer an `items`/`total`
envelope. `paginate_pages()` walks them:

```python
from perceivo_client import paginate_pages

for orchestration in paginate_pages(client.orchestrations.list, page_size=25):
    process(orchestration)
```

It supports these methods passed directly: `client.orchestrations.list`,
`client.intelligence.list`, `client.reviews.list`, `client.query.search` and
`client.experiments.list`. Three more take a positional id, so bind it first
with `functools.partial`: `client.capabilities.list_orchestrations`
(`capability_id`), `client.files.list_entries` and `client.files.list_trash`
(`space_id`).

```python
import functools

from perceivo_client import paginate_pages

for entry in paginate_pages(functools.partial(client.files.list_entries, space_id)):
    process(entry)
```

When a page reports `total_pages`, the helper requests every page up to it and
accepts short or empty pages on the way. The API can filter a page after cutting
it (`client.query.search` with `protection`), so a later page can still hold
results. Without `total_pages`, every page but the last must be full, and the
helper refuses a malformed envelope rather than guessing.

`page_size` must be an integer from 1 through 100; a larger value raises
`ValueError` before any request is sent. `max_items` caps the number of items
yielded, and `max_items=0` sends no request. Keyword arguments other than
`page` and `page_size` are forwarded as filters on every request, for example
`paginate_pages(client.query.search, asset_type="component")`.

Other list operations page differently:

- **Offset/limit:** `client.grants.list`, `client.query.logs` and
  `client.billing.organization_costs` page by `limit`/`offset`. Walk them with
  `paginate()`, for example `paginate(client.grants.list, grantee_type="user")`.
- **Cursor:** `client.operations.list` takes `cursor=`; pass the previous page's
  `next` until it is absent.
- **`data`/`next` pages:** `client.threads.list`, `client.threads.search` and
  `client.intelligence.list_inference_requests`. Pass `page=n` until `next` is
  null.
- **Backwards by time:** `client.threads.list_messages`. Pass the oldest
  message's `created_at` as `before` while `has_more` is true.
- **Page-local totals:** `client.runs.list` counts only the returned page in
  `total` (so `paginate_pages()` refuses it), and the store reads `client.infrastructure.list_search_index_documents`
  and `list_vector_store_entities` answer in each store's own shape. Request
  pages with a fixed `page_size` until a short or empty page comes back.
- **Whole lists:** `client.roles.list`, `client.service_accounts.list`,
  `client.groups.list`, `client.webhooks.list`, `client.secrets.list` without
  `page`, and the bare-array lists (`client.intelligence.list_predictions`,
  training configurations and groups, triggers, node secret bindings, drafts and
  thread participants) return every row in one response.

`AsyncClient` offers the same helpers as methods:

```python
async for review in client.paginate_pages(client.reviews.list, page_size=50):
    process(review)
```

Cancelling the async task stops awaiting the helper, but `AsyncClient` is
thread-backed and cannot cancel an in-flight worker request. That request may
finish in its worker thread.

### Errors

Every `>= 400` response is raised as a typed exception carrying the normalized
error envelope (`code`, `message`, `details`, `request_id`):

| Status | Exception |
|--------|-----------|
| 401 | `PerceivoAuthError` |
| 403 | `PerceivoGrantError` |
| 404 | `PerceivoNotFoundError` |
| 409 | `PerceivoConflictError` |
| 422 | `PerceivoValidationError` |
| 429 `execution_locked` | `PerceivoExecutionLockedError` |
| 429 | `PerceivoRateLimitError` |
| 5xx | `PerceivoServerError` |
| other 4xx | `PerceivoAPIError` |

All of them inherit `PerceivoAPIError`, which inherits `PerceivoError`.
Transport failures raise `PerceivoConnectionError`, and missing credentials
raise `MissingCredentialsError`; both are `PerceivoError` too.

`request_id` is the `Perceivo-Request-Id` response header when the API sends
one; quote it when you contact support. For a validation failure,
`details["errors"]` holds the list of field errors. For a structured refusal,
`details` holds the whole refusal object, so fields such as an existing
`invitation_id` on a `409` are kept.

```python
from perceivo_client import PerceivoNotFoundError

try:
    client.orchestrations.get(orchestration_id)
except PerceivoNotFoundError as exc:
    print(exc.code, exc.message, exc.request_id)
```

### Namespaces

The client mirrors the API's domain groups:

| Namespace | Domain | Primary methods |
|-----------|--------|-----------------|
| `client.auth` | Authentication / Privileges | `whoami()` (GET /v1/whoami), `check_privilege()` and `allowed()` (GET /v1/grants/check) |
| `client.organization` | Organization | `get`, `get_limits`, `get_subscription` |
| `client.members` | Members | `list`, `invite`, `update_role`, `remove`, `restore` |
| `client.invitations` | Invitations | `list`, `cancel`, `resend` |
| `client.groups` | Groups | `list/create/get/update/delete`, `list_members`, `update_member`, `remove_member` |
| `client.grants` | Access grants | `list`, `create`, `update`, `delete`, `preview`, `apply` |
| `client.orchestrations` | Orchestrations | `list/create/get/update/delete`, `run`, `import_bundle`, `export_bundle`, `list_drafts`, `create/get/update/delete_draft`, `publish_draft`, `validate`, `assign_capability`, `get_compatibility`, `copy`, `get_graph`, `get_lineage`, `delete_version`, `restore`, `list/create_node_secret_binding(s)`, `get_node_secret_aliases`, `replace/delete_node_secret_binding` |
| `client.runs` | Runs | `list`, `get`, `logs`, `events`, `steps`, `result`, `artifacts`, `pause`, `resume`, `stop`, `cancel` |
| `client.operations` | Operations | `list`, `get`, `cancel` |
| `client.query` | Query | `events`, `logs` (GET /v1/logs), `metrics`, `search` |
| `client.alert_channels` | Alerts | `list/create/get/update/delete` |
| `client.alert_rules` | Alerts | `list/create/get/update/delete`, `get_catalog`, `test` |
| `client.intelligence` | Intelligence | `list/create/get/update/delete`, `start`, `stop`, `get_status`, `predict`, `predict_batch`, `list_inference_requests`, `get_inference_request`, `get_inference_request_artifact`, `list_predictions`, `list_prediction_outcomes`, `train`, `get_training_job`, `evaluate`, `list_models`, `get_model`, `register_model`, `delete_model`, `promote_model`, `retire_model`, `list/create/get/update_model_family`, `activate_model_family`, `deactivate_model_family`, `apply_traffic_plan`, `list/create/get/activate/delete_drift_baseline(s)`, `get_drift_config`, `replace_drift_config`, `export_bundle`, `import_bundle`, `get_lineage`, `delete_version`, `restore`, `list/create/get/update/delete_training_configuration(s)`, `list/create/get/update/delete_training_group(s)`, `replace_training_group_member`, `remove_training_group_member`, `run_training_group`, `list_feature_views`, `get_feature_view`, `sample_feature_view`, `materialize`, `ingest`, `get/replace_pii_config`, `get/replace_prediction_logging_config`, `list/attach/detach_service_secret(s)`, `list/create/update/delete_trigger(s)`, `get_trigger_execution` |
| `client.capabilities` | Capabilities | `list/create/get/update/delete`, `run`, `restart`, `replace_traffic`, `get_traffic`, `delete_traffic`, `get/apply/delete_traffic_plan`, `evaluate`, `list_evaluations`, `get_evaluation`, `get_evaluation_config`, `replace_evaluation_config`, `get_evaluation_summary`, `list/create/update/delete_trigger(s)`, `list_orchestrations`, `attach_orchestration`, `detach_orchestration`, `copy`, `get_lineage`, `delete_version`, `restore`, `list_execution_graphs`, `get/delete/build_execution_graph`, `list_graph_configs`, `create/update/delete_graph_config`, `build_from_config` |
| `client.queue` | Queue | `list`, `get_summary`, `cancel_item`, `cancel` |
| `client.assets` | Assets | `copy`, `export_bundle`, `import_bundle`, `restore` |
| `client.experiments` | Experiments | `list/create/get/update/delete`, `run`, `get_session`, `stop` |
| `client.components` | Components | `list/create/get/update/delete`, `validate`, `export_bundle`, `import_bundle`, `get_artifact`, `replace_artifact`, `get_dependents`, `run`, `get_lineage`, `delete_version`, `restore` |
| `client.files` | Files & Storage | `list_spaces`, `get_space`, `create_space`, `update_space`, `delete_space`, `get_space_usage`, `list_entries`, `create_entry`, `get_entry`, `update_entry`, `delete_entry`, `copy`, `move`, `upload`, `create_upload_url`, `replace_content`, `download`, `list_trash`, `empty_trash`, `restore_entry`, `restore_entries` |
| `client.reviews` | Reviews | `list/get/update`, `start`, `complete`, `start_and_complete`, `assign`, `save_draft`, `cancel` |
| `client.support` | Support | `list/create/get/update`, `list_comments`, `create_comment`, `list_attachments`, `create_attachment`, `get_attachment_content`, `delete_attachment` |
| `client.threads` | Messaging | `list/create/get/update/delete`, `search`, `acknowledge`, `list_messages`, `create_message`, `list_participants`, `add_participant`, `remove_participant` |
| `client.infrastructure` | Infrastructure | `get`; cluster services (`list/get/update/start/stop_cluster_service(s)`); search index (`list_search_indices`, `get/create/delete_search_index`, `list_search_index_documents`, `add/delete_search_index_document`, `query/export/import/ingest_search_index`); vector store (`list/get/create/delete_vector_store_collection(s)`, `list/add_vector_store_entities`, `delete_vector_store_entity`, `query/export/import/ingest_vector_store_collection`); cache (`list_cache_keys`, `get_cache_key`, `ingest_cache`); MCP (`get/replace_mcp_config`, `list_mcp_tools`, `invoke_mcp_tool`); nodepools (`list/create/get/update/scale/delete_nodepool(s)`); managed services and backups (`list/get/update/start/stop_managed_service(s)`, `list/get/create_managed_service_backup(s)`); dedicated databases (`get_database`, `start_database`, `record_database_activity`); `get_capacity` |
| `client.webhooks` | Webhooks | `list/create/get/update/delete`, `list_deliveries`, `get_delivery`, `test`, `list_event_types` |
| `client.service_accounts` | Service accounts | `list/create/get/update`, `rotate`, `unlock`, `delete` (returns the `ServiceAccountRevoked` receipt) |
| `client.alerts` | Alerts | `list`, `get`, `get_summary`, `acknowledge`, `resolve` |
| `client.triggers` | Triggers | `list/create/get/update/delete`, `invoke` |
| `client.secrets` | Secrets | `list/create/get/update/delete`, `get_value`, `rotate` |
| `client.roles` | Roles | `list/create/get/update/delete` |
| `client.billing` | Billing | costs, usage, cost reports, estimates, invoices, transactions and exports |

Methods return the typed model the API contract declares for the operation, or
the JSON shape the API actually serves where the contract's model does not
match it; see *Response shapes* below. The generated Pydantic v2 models are
available as `perceivo_client.models`, for type hints and for validating your
own payloads:

```python
from perceivo_client import models

me = client.auth.whoami()
assert isinstance(me, models.WhoamiResponse)
```

### Response shapes

- `client.runs.logs()` returns a `RunLogPage` (`entries`, `count`, `limit`,
  `workload_id`, `run_id`, `namespace_resolved`). Narrow it with `start=`,
  `end=`, `channel=`, `limit=` and `order=`.
- `client.reviews.complete()` returns a `ReviewCompletion` (`review_request`,
  `ready_to_resume` and the resumed workload).
- `client.capabilities.list_evaluations()` returns an `EvaluationRunPage`
  (`items`, `total`) of the 20 newest evaluation runs, and `get_evaluation()`
  an `EvaluationRunStatus` keyed by `evaluation_id`.
- `RunLogPage`, `ReviewCompletion` and the evaluation models are importable
  from `perceivo_client`.
- `client.query.logs()`, `client.intelligence.start()`, `stop()` and
  `get_status()`, and the infrastructure cluster-service methods return the
  `dict` the API sends.
- `client.capabilities.list()`, `billing.nodepool_costs()` and
  `billing.run_cost()` return bare lists of dictionaries.
- `client.files.list_entries(space_id)` returns a `PaginatedFileList`; read the
  entries from `page.items`.
- `client.support.get_attachment_content()` returns the attachment's `bytes`
  exactly as served.

A file is an **entry** in a **storage space**. `files.list_spaces()` lists the
organization's spaces; `list_entries(space_id)` and `upload(space_id, file_name, data)`
take the space, and `get_entry(entry_id)`, `download(entry_id)` and
`delete_entry(entry_id)` take the entry.

Billing envelopes are mappings: use `costs["items"]`, `costs["total"]` and
`costs.get("has_more", False)` for `billing.costs()`, and `exports.get("exports")`
and `exports.get("total")` for `billing.exports()`. Export fields may be absent
or explicitly `null`. `billing.egress_usage()`, `billing.experiment_usage()`,
`billing.intelligence_usage()` and `billing.orchestration_usage()` also return
the source mapping: use mapping access, and tolerate bodies with no
`organization_id`.

### Uploading a file

`files.upload()` is a **multipart** operation:

```python
result = client.files.upload(space_id, "rows.csv", csv_bytes, content_type="text/csv")
print(result.succeeded, result.failed)  # read both: a refused file still answers 200

stored = client.files.list_entries(space_id).items
```

(`space_id` is one of `client.files.list_spaces()`, and `csv_bytes` is your own file
content: `bytes`, or a seekable binary file object opened for reading.)

The bytes go in a multipart part named `files`; `folder_id=` puts the file in a
folder of the space. The route accepts a file of at most 10 MiB and answers
`200` with a per-file result even when storage refuses the file, so read
`failed` and each item's `status` rather than the status code. Each stored item
carries its `entry`. The operation is not idempotent: retrying uploads again.

> **Note:** `files.upload()` is not available with request signing enabled. A
> multipart body is streamed by `httpx`, and this client will not sign a body it
> has not read. Calling it on a signing client raises `SigningError` and sends
> nothing; it does not fall back to an unsigned request.

### Ingesting documents into a store

`client.infrastructure.ingest_search_index`, `ingest_vector_store_collection`
and `ingest_cache` chunk, embed and store one document:
`ingest_search_index(index_name, filename, data)`,
`ingest_vector_store_collection(collection_name, filename, data)` and
`ingest_cache(key_prefix, filename, data)`. Like `files.upload()` they send
**multipart** form data and are refused on a signing client with
`SigningError`.

The API answers `200` even when the document is refused. The result's `files`
list has one entry per document, with its `filename`, its `status`
(`completed` or `error`) and, for a refusal, its `error`; `total_inserted`
counts completed documents only. Read them rather than the status code.

### Verifying webhook deliveries

Every delivery carries three headers: `Perceivo-Timestamp` (integer Unix
seconds), `Perceivo-Delivery-Id` (a lowercase UUID) and
`Perceivo-Signature: v1=<hex>`. The signature is HMAC-SHA256, keyed by the
webhook's secret, over `<timestamp>.<delivery_id>.<raw body>`.
`verify_webhook` checks all of it:

```python
from perceivo_client import verify_webhook

# request_body: the raw body BYTES, before any JSON parsing
if verify_webhook(
    request_body,
    secret=webhook_secret,
    signature=request_headers.get("Perceivo-Signature"),
    timestamp=request_headers.get("Perceivo-Timestamp"),
    delivery_id=request_headers.get("Perceivo-Delivery-Id"),
    tolerance=300,  # replay window in seconds; the default. None disables it
):
    ...  # authentic and recent: deduplicate on the delivery id, then process
```

It returns `True` or `False` and never raises on a missing or malformed header.
The signature is compared in constant time, and a delivery whose timestamp is
more than `tolerance` seconds from your clock is rejected even when its
signature is genuine. The body must be `bytes`: a `str` raises `TypeError`,
because a decoded and re-encoded body is not guaranteed to be the bytes that
were signed.

`compute_webhook_signature(body, secret, *, timestamp, delivery_id)` returns the
`v1=<hex>` value, for building a test delivery:

```python
from perceivo_client import compute_webhook_signature

signature = compute_webhook_signature(
    b'{"event":"run.completed"}',
    "whsec_test",
    timestamp=1767225600,
    delivery_id="3f2c1d4e-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
)
```

### Signing outbound requests (opt-in)

HMAC-SHA256 request signing is **off by default**. With nothing configured the
client sends unsigned requests authenticated by the API key alone.

```python
from perceivo_client import Client

client = Client(
    api_key="perceivo_...",  # still sent as X-API-Key
    key_id="9efa4550-e04e-4624-a6f2-684af0330f23",  # or PERCEIVO_KEY_ID
    signing_secret="...",  # or PERCEIVO_SIGNING_SECRET
    hmac_audience="perceivo-api-prod",  # explicit; no env fallback
)
```

The two **credentials** may come from the environment. The **audience** may not:
it is explicit configuration and is never derived from `base_url`, from a `Host`
header, or from anything else in the environment. A signature that names no
deployment would verify at every deployment.

The canonical request has **eleven** fields, including the organization, and
the signed path is the path the client sends. If you implement signing
yourself, follow the
[HMAC request signing guide](https://github.com/ConceptBuilderAI/perceivo-client/blob/HEAD/docs/HMAC_REQUEST_SIGNING.md)
and check your implementation against its golden and negative vectors. The
golden vectors ship in the wheel, at
`perceivo_client/signing/vectors/hmac_v1_vectors.json`, and
`perceivo_client.load_golden_vectors()` reads them.

## How the client is generated

The typed models are generated from the public Perceivo API OpenAPI document.
The vendored copy is `openapi/openapi-v1.json`, and its hash and the generator
versions are recorded in `openapi/spec_provenance.json`. The generator is
[`datamodel-code-generator`](https://github.com/koxudaxi/datamodel-code-generator)
(pinned `==0.83.0` in the `codegen` extra). Its output is split into modules
under `perceivo_client/generated/models/`, which re-exports the public model
names. The HTTP transport and convenience layer are hand-written.

From a checkout or an unpacked source distribution, with the `codegen` extra
installed:

```bash
# Write nothing; exit 1 if the committed models differ from what the pinned
# generator produces from the vendored spec
python openapi/regen.py --check
```

## Links

- Source code: https://github.com/ConceptBuilderAI/perceivo-client
- Issues: https://github.com/ConceptBuilderAI/perceivo-client/issues
- Changelog: https://github.com/ConceptBuilderAI/perceivo-client/blob/HEAD/CHANGELOG.md
- Contributing: https://github.com/ConceptBuilderAI/perceivo-client/blob/HEAD/CONTRIBUTING.md
- Security policy: https://github.com/ConceptBuilderAI/perceivo-client/blob/HEAD/SECURITY.md

## License

Apache-2.0. See
[LICENSE](https://github.com/ConceptBuilderAI/perceivo-client/blob/HEAD/LICENSE)
and [NOTICE](https://github.com/ConceptBuilderAI/perceivo-client/blob/HEAD/NOTICE).
