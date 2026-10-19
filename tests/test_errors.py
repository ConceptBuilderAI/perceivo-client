"""Error-envelope -> typed-exception mapping (tolerant of wire-shape variants)."""

from __future__ import annotations

import httpx
import pytest

from perceivo_client.errors import (
    PerceivoAPIError,
    PerceivoAuthError,
    PerceivoConflictError,
    PerceivoConnectionError,
    PerceivoExecutionLockedError,
    PerceivoGrantError,
    PerceivoNotFoundError,
    PerceivoRateLimitError,
    PerceivoServerError,
    PerceivoValidationError,
)
from tests.conftest import json_handler, make_client, make_transport


@pytest.mark.parametrize(
    "status,exc",
    [
        (401, PerceivoAuthError),
        (403, PerceivoGrantError),
        (404, PerceivoNotFoundError),
        (422, PerceivoValidationError),
        (500, PerceivoServerError),
        (418, PerceivoAPIError),  # unmapped 4xx -> base API error
    ],
)
def test_status_maps_to_typed_exception(status, exc):
    payload = {"error_code": "PCV-X", "message": "boom", "details": {"k": "v"}}
    client, _ = make_client(json_handler(payload, status=status))
    with pytest.raises(exc) as info:
        client.orchestrations.get("orch_1")
    err = info.value
    assert err.status_code == status
    assert err.code == "PCV-X"
    assert err.message == "boom"
    assert err.details == {"k": "v"}


def test_platform_envelope_correlation_id_becomes_request_id():
    # The real platform ErrorResponse uses error_code + correlation_id.
    payload = {
        "error_code": "PCV-DATA-NOTF-0001",
        "message": "orchestration not found",
        "correlation_id": "corr-123",
        "service": "orchestrations",
        "timestamp": "2026-07-18T00:00:00Z",
    }
    client, _ = make_client(json_handler(payload, status=404))
    with pytest.raises(PerceivoNotFoundError) as info:
        client.orchestrations.get("missing")
    assert info.value.request_id == "corr-123"
    assert info.value.code == "PCV-DATA-NOTF-0001"


def test_documented_envelope_code_and_request_id():
    # The documented public shape: code / message / details / request_id.
    payload = {"code": "FORBIDDEN", "message": "nope", "request_id": "req-9"}
    client, _ = make_client(json_handler(payload, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.list()
    assert info.value.code == "FORBIDDEN"
    assert info.value.request_id == "req-9"


def test_bare_error_string_envelope():
    # The edge handler emits {"error": "unauthorized"}.
    client, _ = make_client(json_handler({"error": "unauthorized"}, status=401))
    with pytest.raises(PerceivoAuthError) as info:
        client.auth.whoami()
    assert info.value.code == "unauthorized"


def test_request_id_falls_back_to_header():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="oops", headers={"X-Correlation-Id": "hdr-cid"})

    client, _ = make_client(handler)
    with pytest.raises(PerceivoServerError) as info:
        client.orchestrations.list()
    assert info.value.request_id == "hdr-cid"
    assert info.value.message == "oops"


def test_transport_error_becomes_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns fail")

    transport, _ = make_transport(handler, max_retries=0)
    with pytest.raises(PerceivoConnectionError):
        transport.request("GET", "/v1/orchestrations")


def test_grant_error_surfaces_allowed_groups():
    # A scoped-key denial should tell the caller which groups are allowed.
    payload = {
        "error_code": "ENDPOINT_NOT_ALLOWED",
        "message": "endpoint not allowed for this key",
        "details": {"allowed_groups": ["admin", "ops"]},
    }
    client, _ = make_client(json_handler(payload, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.list()
    assert info.value.allowed_groups == ["admin", "ops"]


def test_grant_error_allowed_groups_from_nested_endpoint_access():
    payload = {
        "message": "forbidden",
        "details": {"endpoint_access": {"allowed_groups": ["billing"]}},
    }
    client, _ = make_client(json_handler(payload, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.list()
    assert info.value.allowed_groups == ["billing"]


def test_grant_error_allowed_groups_absent_is_none():
    client, _ = make_client(json_handler({"message": "nope"}, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.list()
    assert info.value.allowed_groups is None


def test_exception_str_is_informative():
    client, _ = make_client(
        json_handler({"error_code": "PCV-X", "message": "boom", "request_id": "r1"}, status=400)
    )
    with pytest.raises(PerceivoAPIError) as info:
        client.orchestrations.list()
    text = str(info.value)
    assert "400" in text
    assert "PCV-X" in text
    assert "boom" in text


# --- request ids --------------------------------------------------------------


def test_perceivo_request_id_header_is_the_request_id():
    """The edge's id is on every response, including refusals with no body id."""
    client, _ = make_client(
        json_handler(
            {"error": "unauthorized"}, status=401, headers={"Perceivo-Request-Id": "edge-1"}
        )
    )
    with pytest.raises(PerceivoAuthError) as info:
        client.auth.whoami()
    assert info.value.request_id == "edge-1"


def test_perceivo_request_id_header_wins_over_a_backing_service_correlation_id():
    payload = {"error_code": "PCV-CORE-NOTF-0001", "message": "gone", "correlation_id": "backend-7"}
    client, _ = make_client(
        json_handler(payload, status=404, headers={"Perceivo-Request-Id": "edge-2"})
    )
    with pytest.raises(PerceivoNotFoundError) as info:
        client.orchestrations.get("orch_1")
    assert info.value.request_id == "edge-2"


# --- body shapes ----------------------------------------------------------------


@pytest.mark.parametrize(
    "status,code,exc",
    [
        (403, "organization_suspended", PerceivoGrantError),
        (404, "organization_unavailable", PerceivoNotFoundError),
    ],
)
def test_detail_object_keeps_its_code_and_message(status, code, exc):
    """The data service's organization-state refusal: ``{"detail": {code, message}}``."""
    payload = {"detail": {"code": code, "message": "Organization state refusal"}}
    client, _ = make_client(json_handler(payload, status=status))
    with pytest.raises(exc) as info:
        client.orchestrations.get("orch_1")
    assert info.value.code == code
    assert info.value.message == "Organization state refusal"
    assert info.value.details == payload["detail"]


def test_conflict_detail_object_surfaces_the_invitation_id():
    payload = {
        "detail": {
            "code": "invitation_pending",
            "message": "An invitation is already pending",
            "invitation_id": "inv-1",
        }
    }
    client, _ = make_client(json_handler(payload, status=409))
    with pytest.raises(PerceivoConflictError) as info:
        client.orchestrations.get("orch_1")
    assert info.value.code == "invitation_pending"
    assert info.value.message == "An invitation is already pending"
    assert info.value.details["invitation_id"] == "inv-1"


def test_fastapi_validation_list_lands_in_details_errors():
    errors = [{"type": "missing", "loc": ["body", "name"], "msg": "Field required"}]
    client, _ = make_client(json_handler({"detail": errors}, status=422))
    with pytest.raises(PerceivoValidationError) as info:
        client.orchestrations.get("orch_1")
    assert info.value.details == {"errors": errors}
    assert info.value.message == "Request validation failed"


def test_nested_error_object_wins_over_a_top_level_detail_string():
    """The gateway's organization-state body carries both."""
    payload = {
        "error": {"code": "organization_suspended", "message": "Organization is suspended"},
        "detail": "Forbidden",
    }
    client, _ = make_client(json_handler(payload, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.get("orch_1")
    assert info.value.code == "organization_suspended"
    assert info.value.message == "Organization is suspended"


def test_slug_refusal_reason_lands_in_details():
    payload = {"error": "unauthorized", "reason": "timestamp_skew"}
    client, _ = make_client(json_handler(payload, status=401))
    with pytest.raises(PerceivoAuthError) as info:
        client.auth.whoami()
    assert info.value.code == "unauthorized"
    assert info.value.details == {"reason": "timestamp_skew"}


def test_bare_slug_has_no_details():
    client, _ = make_client(json_handler({"error": "forbidden"}, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.get("orch_1")
    assert info.value.details is None


# --- 429: rate limit versus execution lock --------------------------------------

_LOCK_MESSAGE = (
    "Organization is execution-locked; cost-incurring operations are blocked "
    "until the lock is cleared."
)

#: The platform envelope that carries a mapping refusal in ``details``: the
#: lock code is only in ``details.code``, and the message spells the lock with a
#: hyphen, so neither ``code`` nor ``message`` names it.
_STRUCTURED_LOCK = {
    "error_code": "PCV-CORE-RATE-0001",
    "message": _LOCK_MESSAGE,
    "details": {"code": "execution_locked", "message": _LOCK_MESSAGE},
}


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"detail": {"code": "execution_locked", "message": _LOCK_MESSAGE}}, id="data"),
        pytest.param(
            {
                "error_code": "PCV-CORE-RATE-0001",
                "message": "{'code': 'execution_locked', 'message': '" + _LOCK_MESSAGE + "'}",
            },
            id="gateway",
        ),
        pytest.param(_STRUCTURED_LOCK, id="gateway-structured"),
    ],
)
def test_execution_lock_is_its_own_error_not_a_rate_limit(payload):
    client, _ = make_client(json_handler(payload, status=429), max_retries=0)
    with pytest.raises(PerceivoExecutionLockedError) as info:
        client.orchestrations.list()
    assert not isinstance(info.value, PerceivoRateLimitError)
    assert info.value.status_code == 429


def test_a_get_meeting_the_structured_execution_lock_is_sent_once():
    client, rec = make_client(json_handler(_STRUCTURED_LOCK, status=429), max_retries=3)
    with pytest.raises(PerceivoExecutionLockedError):
        client.orchestrations.list()
    assert len(rec.requests) == 1


def test_a_details_code_other_than_the_lock_is_a_rate_limit():
    payload = {**_STRUCTURED_LOCK, "details": {"code": "rate_limited"}}
    client, _ = make_client(json_handler(payload, status=429), max_retries=0)
    with pytest.raises(PerceivoRateLimitError):
        client.orchestrations.list()


def test_a_real_rate_limit_is_still_a_rate_limit_error():
    payload = {"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}}
    client, _ = make_client(
        json_handler(payload, status=429, headers={"Retry-After": "7"}), max_retries=0
    )
    with pytest.raises(PerceivoRateLimitError) as info:
        client.orchestrations.list()
    assert info.value.code == "RATE_LIMIT_EXCEEDED"
    assert info.value.retry_after == 7.0


def test_a_resume_refused_for_a_lock_with_text_only_is_the_documented_rate_limit():
    """``runs.resume`` documents ``PerceivoRateLimitError`` for this refusal.

    A resume refused because the organization may not run work names its
    reason only as text, with no ``execution_locked`` code, so it is not an
    execution-lock error, and as a ``POST`` it is sent once.
    """
    payload = {"detail": "Organization execution is locked"}
    client, rec = make_client(json_handler(payload, status=429), max_retries=3)
    with pytest.raises(PerceivoRateLimitError) as info:
        client.runs.resume("run-1")
    assert not isinstance(info.value, PerceivoExecutionLockedError)
    assert info.value.message == "Organization execution is locked"
    assert len(rec.requests) == 1


@pytest.mark.parametrize(
    "name",
    [
        "PerceivoAPIError",
        "PerceivoAuthError",
        "PerceivoConflictError",
        "PerceivoConnectionError",
        "PerceivoError",
        "PerceivoExecutionLockedError",
        "PerceivoNotFoundError",
        "PerceivoGrantError",
        "PerceivoRateLimitError",
        "PerceivoServerError",
        "PerceivoValidationError",
    ],
)
def test_every_exception_is_exported_from_the_package_root(name: str) -> None:
    import perceivo_client
    from perceivo_client import errors

    assert name in perceivo_client.__all__
    assert getattr(perceivo_client, name) is getattr(errors, name)


@pytest.mark.parametrize("status,exc", [(401, PerceivoAuthError), (403, PerceivoGrantError)])
def test_an_auth_rejection_is_sent_once_under_the_default_retry_budget(status, exc, monkeypatch):
    # A rejected credential stays rejected; a retry would only repeat the refusal.
    monkeypatch.setattr("perceivo_client._transport.time.sleep", lambda seconds: None)
    client, rec = make_client(
        json_handler({"error_code": "denied", "message": "no"}, status=status)
    )
    with pytest.raises(exc):
        client.auth.whoami()
    assert len(rec.requests) == 1


def test_the_default_retry_budget_retries_a_rate_limit(monkeypatch):
    # Control: the test above must not pass with a zero retry budget.
    delays: list[float] = []
    monkeypatch.setattr("perceivo_client._transport.time.sleep", delays.append)
    client, rec = make_client(json_handler({"message": "slow down"}, status=429))
    with pytest.raises(PerceivoRateLimitError):
        client.auth.whoami()
    assert len(rec.requests) > 1
    assert len(delays) == len(rec.requests) - 1


def test_a_dark_organization_raises_not_found_on_any_call():
    """``{"error": "organization_unavailable"}`` refuses every call, a resource-less one too."""
    client, _ = make_client(json_handler({"error": "organization_unavailable"}, status=404))
    with pytest.raises(PerceivoNotFoundError) as info:
        client.auth.whoami()
    assert info.value.code == "organization_unavailable"
    assert info.value.details is None


def test_a_suspended_organization_raises_grant_error_on_a_change():
    """``{"error": "organization_suspended"}``: a change, not a missing privilege."""
    client, _ = make_client(json_handler({"error": "organization_suspended"}, status=403))
    with pytest.raises(PerceivoGrantError) as info:
        client.orchestrations.delete("orch_1")
    assert info.value.code == "organization_suspended"
    assert info.value.allowed_groups is None
