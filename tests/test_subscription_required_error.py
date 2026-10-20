"""A ``403`` ``subscription_required`` refusal maps to its own grant-error subclass."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from perceivo_client.errors import (
    PerceivoAPIError,
    PerceivoExecutionLockedError,
    PerceivoGrantError,
    PerceivoRateLimitError,
    PerceivoSubscriptionRequiredError,
)
from tests.conftest import json_handler, make_client

_MESSAGE = (
    "This organization has no live subscription. Choose a plan or start a trial to run workloads."
)
_REASON = "PCV-DATA-BILL-2023"
_DETAILS = {"code": "subscription_required", "reason_code": _REASON, "message": _MESSAGE}


def _envelope(error_code: str, details: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "error_code": error_code,
        "message": _MESSAGE,
        "correlation_id": "corr-1",
        "service": "svc",
        "timestamp": "2026-10-19T00:00:00Z",
        "details": details,
    }


#: The platform envelope, as each refusing service mints it: the top-level
#: ``error_code`` names the service and differs from call to call.
_ERROR_CODES = (
    "PCV-SCHD-AUTH-0001",
    "PCV-INTM-AUTH-0001",
    "PCV-CORE-AUTH-0001",
    "PCV-APIS-AUTH-0001",
)

#: A detail-object refusal, and the same body after the public edge
#: re-envelopes it: the reason moves to ``details`` under a catalogue code.
_NATIVE = {"detail": {"code": "subscription_required", "message": _MESSAGE}}
_CANONICALISED = _envelope(
    "PCV-APIS-AUTH-0001", {"code": "subscription_required", "message": _MESSAGE}
)
_TOP_LEVEL = {"code": "subscription_required", "message": _MESSAGE, "reason_code": _REASON}


def _from(payload: Any, status: int = 403) -> PerceivoAPIError:
    return PerceivoAPIError.from_response(httpx.Response(status, json=payload))


@pytest.mark.parametrize("error_code", _ERROR_CODES)
def test_details_code_selects_the_subclass_whatever_the_error_code(error_code):
    err = _from(_envelope(error_code, dict(_DETAILS)))
    assert type(err) is PerceivoSubscriptionRequiredError
    assert isinstance(err, PerceivoGrantError)
    assert err.status_code == 403
    assert err.code == error_code
    assert err.message == _MESSAGE
    assert err.reason_code == _REASON
    assert err.request_id == "corr-1"


@pytest.mark.parametrize(
    "payload,reason",
    [
        pytest.param(_NATIVE, None, id="detail-object"),
        pytest.param(_CANONICALISED, None, id="canonicalised"),
        pytest.param(_TOP_LEVEL, _REASON, id="top-level-code"),
    ],
)
def test_every_other_body_shape_selects_the_subclass(payload, reason):
    err = _from(payload)
    assert type(err) is PerceivoSubscriptionRequiredError
    assert isinstance(err, PerceivoGrantError)
    assert err.message == _MESSAGE
    assert err.reason_code == reason


def test_a_top_level_code_beside_an_error_code_still_selects_the_subclass():
    err = _from({"error_code": "PCV-CORE-AUTH-0001", "code": "subscription_required"})
    assert type(err) is PerceivoSubscriptionRequiredError
    assert err.code == "PCV-CORE-AUTH-0001"
    assert err.reason_code is None


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(_envelope("PCV-CORE-AUTH-0001", None), id="envelope-no-details"),
        pytest.param(_envelope("PCV-CORE-AUTH-0001", {"code": "other"}), id="other-code"),
        pytest.param({"error": "organization_suspended"}, id="suspended-slug"),
        pytest.param({"detail": {"code": "forbidden", "message": "no"}}, id="detail-object"),
        pytest.param({"detail": "Forbidden"}, id="detail-string"),
        pytest.param(["subscription_required"], id="list-body"),
        # The error_code alone is never the key, even when it spells the reason.
        pytest.param({"error_code": "subscription_required", "message": "no"}, id="error-code"),
        # The message is never matched.
        pytest.param(_envelope("PCV-CORE-AUTH-0001", {"message": _MESSAGE}), id="message"),
    ],
)
def test_a_403_without_the_code_stays_a_plain_grant_error(payload):
    assert type(_from(payload)) is PerceivoGrantError


def test_a_403_with_a_non_json_body_stays_a_plain_grant_error():
    err = PerceivoAPIError.from_response(httpx.Response(403, text="subscription_required"))
    assert type(err) is PerceivoGrantError


@pytest.mark.parametrize("status", [401, 404, 409, 422, 500])
def test_the_code_on_another_status_does_not_select_the_subclass(status):
    err = _from(_envelope("PCV-X", dict(_DETAILS)), status=status)
    assert not isinstance(err, PerceivoSubscriptionRequiredError)


def test_a_non_string_reason_code_is_none():
    details = {"code": "subscription_required", "reason_code": 7}
    err = _from(_envelope("PCV-CORE-AUTH-0001", details))
    assert type(err) is PerceivoSubscriptionRequiredError
    assert err.reason_code is None


def test_allowed_groups_is_still_read_on_the_subclass():
    err = _from(_envelope("PCV-CORE-AUTH-0001", {**_DETAILS, "allowed_groups": ["g1"]}))
    assert type(err) is PerceivoSubscriptionRequiredError
    assert err.allowed_groups == ["g1"]


@pytest.mark.parametrize(
    "payload,exc",
    [
        pytest.param({"message": "slow down"}, PerceivoRateLimitError, id="rate-limit"),
        pytest.param(
            _envelope("PCV-INTM-RATE-0001", dict(_DETAILS)),
            PerceivoRateLimitError,
            id="code-on-429",
        ),
        pytest.param(
            {"detail": {"code": "execution_locked", "message": "locked"}},
            PerceivoExecutionLockedError,
            id="execution-locked",
        ),
    ],
)
def test_a_429_is_unchanged(payload, exc):
    assert type(_from(payload, status=429)) is exc


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(_envelope("PCV-SCHD-AUTH-0001", dict(_DETAILS)), id="envelope"),
        pytest.param(_NATIVE, id="detail-object"),
    ],
)
def test_a_get_answering_subscription_required_is_sent_once(payload, monkeypatch):
    delays: list[float] = []
    monkeypatch.setattr("perceivo_client._transport.time.sleep", delays.append)
    client, rec = make_client(json_handler(payload, status=403))
    with pytest.raises(PerceivoSubscriptionRequiredError):
        client.auth.whoami()
    assert len(rec.requests) == 1
    assert delays == []


_GATED_CALLS = [
    pytest.param(lambda c: c.intelligence.start("intel_1"), id="start"),
    pytest.param(lambda c: c.intelligence.train("intel_1"), id="train"),
    pytest.param(lambda c: c.intelligence.promote_model("intel_1", "model_1"), id="promote"),
    pytest.param(
        lambda c: c.intelligence.apply_traffic_plan("intel_1", {"allocations": []}),
        id="traffic-plan",
    ),
]


@pytest.mark.parametrize("call", _GATED_CALLS)
@pytest.mark.parametrize("error_code", _ERROR_CODES[:3])
def test_each_gated_call_raises_the_subclass_once(call, error_code):
    client, rec = make_client(json_handler(_envelope(error_code, dict(_DETAILS)), status=403))
    with pytest.raises(PerceivoSubscriptionRequiredError) as info:
        call(client)
    assert info.value.reason_code == _REASON
    assert len(rec.requests) == 1
    assert rec.requests[0].method == "POST"
