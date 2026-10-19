# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `PerceivoSubscriptionRequiredError`, a `PerceivoGrantError` subclass, is
  raised for a `403` whose `details.code` (or top-level `code`) is
  `subscription_required`: the organization has no live subscription, so
  choose a plan or start a trial. `reason_code` carries the reported billing
  reason when the body has one. The top-level `error_code` is not the key: it
  names the refusing service. It is never retried, and an existing
  `except PerceivoGrantError` still catches it. A `429` maps as before.
- `client.groups.add_member(group_id, body)` adds a user or service account to a
  group, and `client.groups.remove_principal(group_id, principal_type,
  principal_id)` removes either kind (`/v1/groups/{group_id}/members/{principal_type}/{principal_id}`).
- Live public-API matrix harness fixes: grants skip non-grantable
  privileges, a zero key may hold a route's visibility privilege
  (`zero_key_holds`), capability graph cells build on a completed run, the
  component fixture names its type and port, and more foreign ids are harvested.
- Ingest jobs on the vector store and the search index. The six
  `client.infrastructure.*_vector_store_ingest_job*` methods each have a
  `*_search_index_ingest_job*` twin:
  - `create_vector_store_ingest_job(collection_name, body, *, idempotency_key=None)`
    ingests already-uploaded files (`entry_ids`, or a `space_id` with an
    optional `folder_id`) in the background;
  - `list_vector_store_ingest_jobs` and `list_vector_store_ingest_job_files`
    page with `before` / `after`;
  - `get_vector_store_ingest_job` and `cancel_vector_store_ingest_job`;
  - `resume_vector_store_ingest_job(..., *, version, idempotency_key=None)`
    sends `version` as `If-Match: "<version>"` and starts a new job over the
    files that did not succeed.
  All need `INFRA_CONFIGURE`, reads included.
- Batch direct uploads: `client.files.create_upload_urls(body)` gets up to 100
  upload URLs for one space, and `client.files.register_entries(space_id, body)`
  registers up to 100 uploads. A file refused at admission (its parent or its
  `blob_name`) refuses the whole batch; a file the service refuses after that is
  reported in the results, so check `failed_count`.

### Changed

- `ModelRegisterRequest` no longer has a `name` field and `ModelRegisterRequestName`
  is removed: the platform never stored a model name. `ModelRead.name` is the
  model family's name. The vendored spec also picks up the `FILE_READ` and
  `INTELLIGENCE_READ` co-requirements now published as `x-perceivo-privilege-also`.
- Docstrings and the README's Errors section now name the statuses the
  OpenAPI document declares. Client behaviour is unchanged.
  - Every operation can answer `401` and `403`, and `404` for an organization
    that is disabled, being deleted or deleted (code
    `organization_unavailable`). A `403` refused before routing carries
    `{"error": "forbidden"}`, or `{"error": "organization_suspended"}` when
    the organization is suspended and the request is not a `GET`, `HEAD` or
    `OPTIONS` request or an export. `PerceivoGrantError` and
    `PerceivoNotFoundError` say so.
  - `client.files.get_entry()` names `FILE_READ`; without it the client
    raises `PerceivoGrantError`.
  - `client.queue.cancel_item()` says a key holds `WORKLOAD_CONTROL` through
    its organization-level privileges, including grants made on the
    organization.
  - `client.intelligence.delete()` and `delete_version()` name the `409`
    answered while a runtime is active; stop the intelligence first.
  - The vector-store, search-index and cache-key methods name the `400`,
    `404`, `409`, `502`, `503` and `504` those stores relay.
    `create_search_index()` documents an existing name as `400`, not `409`.
  - `client.capabilities.run()` and `client.support.create_attachment()` name
    `413`; `client.intelligence.promote_model()` names the `409` of a
    promotion freeze; `client.components.update()` names the `400` for a
    malformed or repeated port.
  - `client.capabilities.get_traffic()` and `get_traffic_plan()` still answer
    `None`, not `404`, for a well-formed capability id they cannot find.

### Fixed

- The `client.support.list()` docstring said a `403` (`PerceivoGrantError`)
  came only from a lookup by ticket number without `ORGANIZATION_READ`. The
  API checks `ORGANIZATION_READ` on every form of the list, with or without
  `filter[ticket_number]`, and refuses a key without it with `403` before
  anything is read. The docstring now says so, and a test pins the `403` to
  `PerceivoGrantError` for both forms.
- The `client.capabilities.update()` docstring now names the `400` answered
  when a new `start_component_id` or `end_component_id` names a component that
  is missing, deleted, or not a START or END component. The client raises the
  base `PerceivoAPIError`.

## [1.0.0] - 2026-10-16

The first stable release of `perceivo-client`, the Python client for the
Perceivo public REST API. It requires Python 3.11 or later, `httpx` and
`pydantic`.

### Added

- `Client` and `AsyncClient`, with 29 resource namespaces (`client.auth`,
  `client.grants`, `client.runs`, `client.capabilities` and the rest) that
  wrap the public operations. Request and response bodies are pydantic models
  generated from the vendored OpenAPI document `openapi/openapi-v1.json` and
  importable as `perceivo_client.models`.
- **Paths.** Every operation is called at its `/v1/...` path on the base URL.
  The base URL defaults to `https://api.perceivo.ai`; set `base_url` or
  `PERCEIVO_API_URL` to call another deployment.
- **API key.** The key comes from `api_key` or `PERCEIVO_API_KEY` and is sent
  in the `X-API-Key` header, and nowhere else. A missing key raises
  `MissingCredentialsError`. The signer refuses a request whose query string
  carries an `api_key` parameter, in any spelling a server would decode to it,
  and raises `SigningError`.
- **HMAC request signing**, opt-in and off by default. Pass `key_id`,
  `signing_secret` and `hmac_audience` (the first two may come from
  `PERCEIVO_KEY_ID` and `PERCEIVO_SIGNING_SECRET`; the audience has no
  environment fallback), and every request carries the `X-Perceivo-Key-Id`,
  `X-Perceivo-Timestamp`, `X-Perceivo-Nonce` and `X-Perceivo-Signature`
  headers alongside the API key. The signature covers the method, the path and
  query exactly as sent, the body digest, `Content-Type`, the acting
  organization, the audience, the timestamp and the nonce. A partial
  configuration raises rather than sending unsigned.
  `perceivo_client.signing` provides `sign_request`,
  `build_canonical_request`, `verify_signature` and the published test vectors
  (`load_golden_vectors`). `docs/HMAC_REQUEST_SIGNING.md` specifies the
  protocol.
- **Signed multipart requests.** With request signing enabled,
  `files.upload`, `files.replace_content`,
  `infrastructure.import_search_index`,
  `infrastructure.import_vector_store_collection`,
  `infrastructure.ingest_cache`, `infrastructure.ingest_search_index` and
  `infrastructure.ingest_vector_store_collection` are signed like every other
  request: the transport encodes the multipart body to bytes once, signs those
  exact bytes with the `Content-Type` and `boundary` it sends, and sends the
  same bytes with a `Content-Length`. A file object is read in full, so a
  signed multipart request holds the whole file in memory.
- **Privilege pre-flight.** `client.auth.check_privilege(privilege)` calls
  `GET /v1/grants/check` and returns `PrivilegeCheckResponse` (`allowed` and
  the caller's `privileges`). `client.auth.allowed(privilege)` returns `True`
  only when the check answers `allowed`, and `False` on a `403`. Both take the
  privilege alone: the answer is always about the calling credential, at
  organization level. `client.auth.whoami()` calls `GET /v1/whoami`.
- **Grants.** Access is named Grant throughout. `client.grants` lists,
  creates, updates and deletes grants at `/v1/grants`, and previews and
  applies cascading change sets. The models are `GrantRead`,
  `AssetGrantCreate`, `AssetGrantRead`, `ChangeSet` and `CascadeApplyResult`
  (`grant_ids`), and a replacing grant names `replaces_grant_id`.
- **Errors.** Every error response raises a subclass of `PerceivoAPIError`
  with `status_code`, `code`, `message`, `details` and `request_id`,
  normalised across every error body shape the API returns:
  `PerceivoAuthError` (`401`), `PerceivoGrantError` (`403`, with
  `allowed_groups` for an endpoint-access refusal), `PerceivoNotFoundError`
  (`404`), `PerceivoConflictError` (`409`), `PerceivoValidationError`
  (`422`), `PerceivoRateLimitError` (`429`, with `rate_limit` and
  `retry_after`), `PerceivoExecutionLockedError` (`429` `execution_locked`)
  and `PerceivoServerError` (`5xx`). A transport failure raises
  `PerceivoConnectionError`. All of them derive from `PerceivoError`.
- **Retries.** `GET` requests are retried on `429`, `502`, `503` and `504`, up
  to `max_retries` (default 3), honouring `Retry-After`. A `429`
  `execution_locked` is never retried, because waiting does not clear it.
- `paginate()` and `paginate_pages()` for list operations,
  `Client.with_options(timeout=...)` for a per-call timeout, and
  `verify_webhook()` and `compute_webhook_signature()` for webhook deliveries.
- **Bearer (Entra) authentication.** `Client` and `AsyncClient` accept a
  keyword-only `bearer_token`: a token string, or a zero-argument callable
  returning one that is invoked once per request so a caller refreshing a
  short-lived Entra token always sends the current value. In bearer mode the
  client sends `Authorization: Bearer <token>` and never an `X-API-Key` or
  signature header, caches nothing, and adds no Azure dependency. `bearer_token`
  has no environment fallback and is mutually exclusive with `api_key` and with
  the HMAC `key_id` / `signing_secret` / `hmac_audience` inputs; configuring
  more than one mode raises the new `AmbiguousCredentialsError` at construction.
  `perceivo_client.auth` gains `BearerCredentials` and
  `resolve_bearer_credentials`.

### Removed

- The three node-secret write operations retired from the public API in
  api-service 0.183.0 are not in the client:
  `orchestrations.create_node_secret_binding`
  (`POST /v1/orchestrations/{orchestration_id}/node-secrets`),
  `orchestrations.replace_node_secret_binding`
  (`PUT /v1/orchestrations/{orchestration_id}/nodes/{node_id}/secrets/{alias}`)
  and `orchestrations.delete_node_secret_binding` (`DELETE` of the same path),
  and their request models `BindNodeSecretRequest` and `NodeSecretBindRequest`.
  Secrets are bound to nodes through a draft's `publish_payload.secret_ops`:
  create or update the draft with `orchestrations.create_draft` /
  `update_draft`, then call `publish_draft`. `list_node_secret_bindings` and
  `get_node_secret_aliases` remain.
- The `GraphConfigRead` model. `capabilities.list_graph_configs`
  (`GET /v1/capabilities/{capability_id}/execution-graphs/configs`) returns
  `PaginatedItemsResponse`.

### Known gaps

- Billing export download (`GET /v1/billing/exports/{export_id}/download`) is
  not in this release; the server route ships in a later platform release and
  the client adds `billing.download_export` in 1.1.0.
