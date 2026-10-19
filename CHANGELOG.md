# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-19

First public release.

### Added

- `Client` and `AsyncClient`, typed clients for the Perceivo Platform API, with
  Pydantic v2 models generated from the public OpenAPI document and available
  as `perceivo_client.models`.
- Namespaces for the API's domains: `auth`, `organization`, `members`,
  `invitations`, `groups`, `grants`, `roles`, `service_accounts`, `secrets`,
  `orchestrations`, `runs`, `operations`, `queue`, `query`, `capabilities`,
  `components`, `assets`, `experiments`, `intelligence`, `infrastructure`,
  `files`, `reviews`, `support`, `threads`, `webhooks`, `alerts`,
  `alert_channels`, `alert_rules` and `billing`.
- Three authentication modes: an API key (`X-API-Key`), HMAC-SHA256 request
  signing (`key_id`, `signing_secret`, `hmac_audience`), and an Entra bearer
  token (`bearer_token`, a string or a callable). Configuration can come from
  arguments or from `PERCEIVO_API_URL`, `PERCEIVO_API_KEY`, `PERCEIVO_KEY_ID`
  and `PERCEIVO_SIGNING_SECRET`.
- Golden and negative HMAC signing vectors shipped in the wheel, readable with
  `load_golden_vectors()`, and a signing guide in `docs/HMAC_REQUEST_SIGNING.md`.
- Retries for `GET` requests on 429, 502, 503 and 504, honouring `Retry-After`
  and then backing off exponentially; other methods are sent once. Rate-limit
  headers are parsed into `client.rate_limit`.
- Typed exceptions for every error response, carrying `code`, `message`,
  `details` and `request_id`, all derived from `PerceivoError`.
- Pagination helpers: `paginate_pages()` for `page`/`page_size` lists and
  `paginate()` for `limit`/`offset` lists.
- File uploads and downloads, batch direct uploads, and ingest jobs for vector
  stores and search indexes.
- Webhook signature verification with `verify_webhook()`.
- Type information (`py.typed`).
