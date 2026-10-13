"""The top-level ``Client`` — the ergonomic front door to the Perceivo API."""

from __future__ import annotations

import httpx

from perceivo_client._transport import Transport
from perceivo_client.auth import resolve_credentials
from perceivo_client.ratelimit import RateLimitInfo
from perceivo_client.resources import (
    AlertChannelsResource,
    AlertRulesResource,
    AlertsResource,
    AssetsResource,
    AuthResource,
    BillingResource,
    CapabilitiesResource,
    ComponentsResource,
    ExperimentsResource,
    FilesResource,
    GrantsResource,
    GroupsResource,
    InfrastructureResource,
    IntelligenceResource,
    InvitationsResource,
    MembersResource,
    OperationsResource,
    OrchestrationsResource,
    OrganizationResource,
    QueryResource,
    QueueResource,
    ReviewsResource,
    RolesResource,
    RunsResource,
    SecretsResource,
    ServiceAccountsResource,
    SupportResource,
    ThreadsResource,
    TriggersResource,
    WebhooksResource,
)
from perceivo_client.signing import RequestSigner, resolve_signing_credentials


class Client:
    """A synchronous client for the Perceivo REST API.

    Authentication resolves ``PERCEIVO_API_KEY`` / ``PERCEIVO_API_URL`` from the
    environment (or explicit ``api_key`` / ``base_url`` arguments) and sends the
    key as the ``X-API-Key`` header. Rate-limit headers are parsed on every
    response (:attr:`rate_limit`). ``GET`` requests retry ``429``/``502``/``503``/
    ``504`` with backoff honoring ``Retry-After``, except a ``429``
    ``execution_locked``, which waiting cannot clear. Every other method makes
    one request and raises the typed error; reconcile state before retrying a
    write yourself.

    **HMAC request signing is opt-in and off by default.** Pass ``key_id``,
    ``signing_secret`` and ``hmac_audience`` (``key_id`` and ``signing_secret``
    may instead come from ``PERCEIVO_KEY_ID`` / ``PERCEIVO_SIGNING_SECRET``) to
    add the ``X-Perceivo-*`` signature headers to every request; the API key is
    still sent alongside. A partial configuration raises rather than sending
    unsigned.

    ``hmac_audience`` is the audience label of the deployment you are calling,
    for example ``"perceivo-api-prod"``. It has **no environment fallback** and
    is never derived from ``base_url``: it is a label, not a hostname. See
    :mod:`perceivo_client.signing`.

    Example:
        >>> from perceivo_client import Client
        >>> client = Client()                       # reads PERCEIVO_API_KEY
        >>> me = client.auth.whoami()               # introspect this key
        >>> runs = client.runs.list()               # the organization's runs

    Use the client as a context manager, or call :meth:`close`, to release the
    HTTP connection pool. Use :meth:`with_options` to give one call a
    different timeout.

    Namespaces:
        ``auth``, ``orchestrations``, ``runs``, ``intelligence``,
        ``capabilities``, ``queue``, ``components``, ``files``, ``webhooks``,
        ``billing``, ``reviews``, ``alerts``, ``triggers``,
        ``support``, ``secrets``, ``infrastructure``, ``roles``,
        ``service_accounts``, ``organization``, ``members``, ``invitations``,
        ``groups``, ``grants``, ``operations``, ``query``, ``alert_channels``,
        ``alert_rules``, ``assets``, ``experiments`` and ``threads``.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        http_client: httpx.Client | None = None,
        key_id: str | None = None,
        signing_secret: str | bytes | None = None,
        hmac_audience: str | None = None,
    ) -> None:
        self._credentials = resolve_credentials(base_url=base_url, api_key=api_key)
        # base_url is deliberately not passed: the audience is a configured
        # deployment label, never derived from a URL or a Host header.
        signing_credentials = resolve_signing_credentials(
            key_id=key_id, signing_secret=signing_secret, audience=hmac_audience
        )
        self._bind(
            Transport(
                self._credentials,
                timeout=timeout,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                http_client=http_client,
                signer=(
                    RequestSigner(signing_credentials) if signing_credentials is not None else None
                ),
            )
        )

    def _bind(self, transport: Transport) -> None:
        """Attach ``transport`` and build every namespace over it."""
        self._transport = transport
        self.auth = AuthResource(self._transport)
        self.orchestrations = OrchestrationsResource(self._transport)
        self.runs = RunsResource(self._transport)
        self.intelligence = IntelligenceResource(self._transport)
        self.capabilities = CapabilitiesResource(self._transport)
        self.queue = QueueResource(self._transport)
        self.components = ComponentsResource(self._transport)
        self.files = FilesResource(self._transport)
        self.webhooks = WebhooksResource(self._transport)
        self.billing = BillingResource(self._transport)
        self.reviews = ReviewsResource(self._transport)
        self.alerts = AlertsResource(self._transport)
        self.triggers = TriggersResource(self._transport)
        self.support = SupportResource(self._transport)
        self.secrets = SecretsResource(self._transport)
        self.infrastructure = InfrastructureResource(self._transport)
        self.roles = RolesResource(self._transport)
        self.service_accounts = ServiceAccountsResource(self._transport)
        self.organization = OrganizationResource(self._transport)
        self.members = MembersResource(self._transport)
        self.invitations = InvitationsResource(self._transport)
        self.groups = GroupsResource(self._transport)
        self.grants = GrantsResource(self._transport)
        self.operations = OperationsResource(self._transport)
        self.query = QueryResource(self._transport)
        self.alert_channels = AlertChannelsResource(self._transport)
        self.alert_rules = AlertRulesResource(self._transport)
        self.assets = AssetsResource(self._transport)
        self.experiments = ExperimentsResource(self._transport)
        self.threads = ThreadsResource(self._transport)

    @property
    def base_url(self) -> str:
        """The resolved API base URL."""
        return self._credentials.base_url

    @property
    def rate_limit(self) -> RateLimitInfo | None:
        """Rate-limit state parsed from the most recent response, if any."""
        return self._transport.last_rate_limit

    def with_options(self, *, timeout: float | None) -> Client:
        """A client for the same API whose requests use a different timeout.

        Use it for one operation that legitimately runs longer than the
        client's timeout, without raising the timeout of every other call::

            client.with_options(timeout=180.0).intelligence.start(intelligence_id)

        The returned client shares this client's credentials, signing, retry
        settings and connection pool. The timeout is applied to each request,
        so it also applies to an injected ``http_client``. :attr:`rate_limit`
        is tracked per client. Closing the returned client leaves the shared
        pool open; close this client to release it.

        Args:
            timeout: Seconds that bound each of the connect, read, write and
                pool waits of every attempt, except that ``files.upload``,
                ``files.replace_content`` and the three infrastructure ingests
                wait at least 150 s to read and write. ``None`` disables the
                limits.

        Returns:
            A new :class:`Client`.
        """
        derived = Client.__new__(Client)
        derived._credentials = self._credentials
        derived._bind(self._transport.with_timeout(timeout))
        return derived

    def close(self) -> None:
        """Close the HTTP connection pool.

        A pool passed in as ``http_client`` is left open: whoever created it
        closes it.
        """
        self._transport.close()

    def __enter__(self) -> Client:
        """Return this client; :meth:`close` runs when the block exits."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the client."""
        self.close()
