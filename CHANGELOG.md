# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-12

The first stable release of `perceivo-client`, the Python client for the
Perceivo public REST API. It requires Python 3.11 or later, `httpx` and
`pydantic`.

### Added

- `Client` and `AsyncClient`, with 30 resource namespaces (`client.auth`,
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
