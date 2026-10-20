"""Auth header injection + whoami / check_privilege introspection parsing."""

from __future__ import annotations

import pytest

from perceivo_client import Client, MissingCredentialsError
from perceivo_client._version import __version__
from perceivo_client.auth import APICredentials
from tests.conftest import json_handler, make_client


def test_api_key_header_is_sent_on_every_request():
    client, rec = make_client(json_handler({"ok": True}))
    client.orchestrations.list()
    req = rec.last
    assert req.headers["X-API-Key"] == "test-key"
    assert req.headers["Accept"] == "application/json"
    assert req.headers["User-Agent"] == f"perceivo-client/{__version__}"


def test_api_credentials_repr_and_str_redact_the_key():
    secret = "pk_live_must_never_be_rendered"
    credentials = APICredentials(base_url="https://api.test", api_key=secret)

    for rendered in (repr(credentials), str(credentials)):
        assert secret not in rendered
        assert "api_key=<redacted>" in rendered


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("PERCEIVO_API_KEY", raising=False)
    with pytest.raises(MissingCredentialsError):
        Client(base_url="https://api.test")


def test_missing_credentials_is_a_perceivo_error(monkeypatch):
    from perceivo_client import PerceivoError

    monkeypatch.delenv("PERCEIVO_API_KEY", raising=False)
    with pytest.raises(PerceivoError):
        Client(base_url="https://api.test")


def test_only_the_perceivo_environment_variables_are_read(monkeypatch):
    """No other variable names supply the key or the URL."""
    from perceivo_client.auth import DEFAULT_API_URL, resolve_credentials

    monkeypatch.delenv("PERCEIVO_API_KEY", raising=False)
    monkeypatch.delenv("PERCEIVO_API_URL", raising=False)
    monkeypatch.setenv("CONCEPTBUILDER_API_KEY", "other-key")
    monkeypatch.setenv("CONCEPTBUILDER_API_URL", "https://other.test")
    with pytest.raises(MissingCredentialsError):
        resolve_credentials()
    assert resolve_credentials(api_key="k").base_url == DEFAULT_API_URL


def test_explicit_api_key_and_env_key(monkeypatch):
    monkeypatch.setenv("PERCEIVO_API_KEY", "env-key")
    client, rec = make_client(json_handler({}))
    # make_client passes api_key explicitly; explicit wins over env.
    client.auth.whoami()
    assert rec.last.headers["X-API-Key"] == "test-key"


def test_whoami_hits_the_published_whoami_path_and_parses():
    payload = {
        "type": "service_account",
        "id": "key_abc",
        "organization_id": "org_xyz",
        "organization_name": "Acme",
        "roles": ["admin"],
        "endpoint_access": {"allow_all": True},
        "effective_privileges": ["ORCHESTRATION_EXECUTE", "ORCHESTRATION_READ"],
        "is_admin": True,
    }
    client, rec = make_client(json_handler(payload))
    result = client.auth.whoami()
    assert rec.last.method == "GET"
    assert rec.last.url.path == "/v1/whoami"
    assert result.type == "service_account"
    assert result.id == "key_abc"
    assert result.organization_id == "org_xyz"
    assert result.organization_name == "Acme"
    assert result.roles == ["admin"]
    assert result.endpoint_access == {"allow_all": True}
    assert "ORCHESTRATION_EXECUTE" in result.effective_privileges
    assert result.is_admin is True


def test_check_privilege_hits_grants_check_and_parses():
    client, rec = make_client(
        json_handler({"allowed": True, "privileges": ["ORCHESTRATION_EXECUTE"]})
    )
    result = client.auth.check_privilege("ORCHESTRATION_EXECUTE")
    assert rec.last.url.path == "/v1/grants/check"
    assert dict(rec.last.url.params) == {"privilege": "ORCHESTRATION_EXECUTE"}
    assert result.allowed is True
    assert result.privileges == ["ORCHESTRATION_EXECUTE"]


@pytest.mark.parametrize("call", ["check_privilege", "allowed"])
@pytest.mark.parametrize("kwarg", ["resource_type", "resource_id"])
def test_the_privilege_check_takes_no_resource_params(call, kwarg):
    client, rec = make_client(json_handler({"allowed": True}))
    with pytest.raises(TypeError):
        getattr(client.auth, call)("SECRET_USE", **{kwarg: "x"})
    assert rec.requests == []


def test_allowed_boolean_wrapper_true_on_grant():
    client, _ = make_client(json_handler({"allowed": True}))
    assert client.auth.allowed("ORCHESTRATION_EXECUTE") is True


def test_allowed_is_false_on_a_200_denial():
    # /grants/check answers a denial with HTTP 200 and allowed=false.
    client, _ = make_client(json_handler({"allowed": False}))
    assert client.auth.allowed("ORCHESTRATION_EXECUTE") is False


def test_allowed_reads_only_allowed():
    """Only ``allowed`` decides: an answer without it is not a grant."""
    client, _ = make_client(json_handler({"privileges": ["ORCHESTRATION_EXECUTE"]}))
    assert client.auth.allowed("ORCHESTRATION_EXECUTE") is False


def test_allowed_boolean_wrapper_false_on_403_denial():
    # An HTTP 403 is still folded into False.
    client, _ = make_client(
        json_handler({"detail": "Access denied: missing X on organization"}, status=403)
    )
    assert client.auth.allowed("ORCHESTRATION_EXECUTE") is False


def test_client_context_manager_closes():
    handler = json_handler({})
    with make_client(handler)[0] as client:
        assert isinstance(client, Client)


def test_generated_models_validate_whoami_payload():
    # Deliverable 1: generated typed models are usable on returned payloads.
    from perceivo_client.generated.models import WhoamiResponse

    payload = {
        "type": "service_account",
        "id": "k",
        "organization_id": "o",
        "effective_privileges": ["A"],
        "is_admin": False,
    }
    model = WhoamiResponse.model_validate(payload)
    assert model.type == "service_account"
    assert model.id == "k"
    assert model.effective_privileges == ["A"]


def test_base_url_normalization():
    client, _ = make_client(json_handler({}))
    assert isinstance(client.base_url, str)
    assert not client.base_url.endswith("/")


def test_default_base_url_is_production_not_dev(monkeypatch):
    """A published client that omits PERCEIVO_API_URL must land on
    PRODUCTION, never the dev cluster."""
    from perceivo_client.auth import DEFAULT_API_URL, resolve_credentials

    monkeypatch.delenv("PERCEIVO_API_URL", raising=False)

    creds = resolve_credentials(api_key="k")
    assert creds.base_url == "https://api.perceivo.ai"
    assert DEFAULT_API_URL == "https://api.perceivo.ai"
    assert "dev" not in creds.base_url


def test_env_var_still_overrides_default(monkeypatch):
    """The production default must remain overridable for dev/testing."""
    from perceivo_client.auth import resolve_credentials

    monkeypatch.setenv("PERCEIVO_API_URL", "https://api.staging.example.com")
    creds = resolve_credentials(api_key="k")
    assert creds.base_url == "https://api.staging.example.com"
