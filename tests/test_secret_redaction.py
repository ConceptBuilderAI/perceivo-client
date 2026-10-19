"""Secret-bearing response fields stay out of ``repr()``/``str()``.

``perceivo_client._redaction`` patches four generated models so that printing or
logging a result does not write a credential out in clear, while the attribute
and ``model_dump()`` still carry the value the caller needs.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from perceivo_client import _redaction  # importing it installs the redaction
from perceivo_client.generated.models import (
    IngestTriggerRead,
    SecretValueRead,
    ServiceAccountCreated,
    UploadTargetResponse,
)

UPLOAD_SAS = "https://acct.blob.core.windows.net/c/b?sv=2024&sp=cw&sig=UPLOADSASSECRET0001"
TRIGGER_TOKEN = "trg_TRIGGERTOKENSECRET0002"
SA_KEY = "pk_live_SERVICEACCOUNTKEYSECRET0003"
SECRET_VALUE = "SECRETVALUEPLAINTEXT0004"

CASES: list[tuple[type[BaseModel], dict[str, Any], str, str]] = [
    (
        UploadTargetResponse,
        {
            "blob_name": "b",
            "container_name": "c",
            "expires_at": "2026-10-03T00:00:00Z",
            "file_name": "f.csv",
            "upload_url": UPLOAD_SAS,
        },
        "upload_url",
        UPLOAD_SAS,
    ),
    (
        IngestTriggerRead,
        {"id": "t1", "http_enabled": True, "http_token": TRIGGER_TOKEN},
        "http_token",
        TRIGGER_TOKEN,
    ),
    (
        ServiceAccountCreated,
        {
            "created_at": "2026-10-03T00:00:00Z",
            "created_by_user_id": "u1",
            "id": "sa1",
            "is_active": True,
            "key": SA_KEY,
            "organization_id": "o1",
            "prefix": "pk_live_SERV",
        },
        "key",
        SA_KEY,
    ),
    (
        SecretValueRead,
        {"expires_at": "2026-11-01T00:00:00Z", "value": SECRET_VALUE},
        "value",
        SECRET_VALUE,
    ),
]
IDS = [case[0].__name__ for case in CASES]


@pytest.mark.parametrize(("model", "payload", "field", "secret"), CASES, ids=IDS)
def test_secret_is_not_in_repr_or_str(model, payload, field, secret):
    result = model.model_validate(payload)
    for rendered in (repr(result), str(result), f"{result}", f"{result!r}", repr([result])):
        assert secret not in rendered
        assert f"{field}=<redacted>" in rendered


@pytest.mark.parametrize(("model", "payload", "field", "secret"), CASES, ids=IDS)
def test_secret_is_still_on_the_attribute_and_in_the_dump(model, payload, field, secret):
    result = model.model_validate(payload)
    assert getattr(result, field) == secret
    assert result.model_dump()[field] == secret
    assert result.model_dump(mode="json")[field] == secret
    assert secret in result.model_dump_json()


@pytest.mark.parametrize(("model", "payload", "field", "secret"), CASES, ids=IDS)
def test_other_fields_still_render(model, payload, field, secret):
    rendered = repr(model.model_validate(payload))
    other = next(k for k in payload if k != field)
    assert f"{other}=" in rendered


def test_a_null_token_renders_as_none():
    rendered = repr(IngestTriggerRead(id="t1", http_enabled=False, http_token=None))
    assert "http_token=None" in rendered


def test_the_redaction_table_covers_exactly_the_four_models():
    assert {m.__name__: sorted(f) for m, f in _redaction.REDACTED_FIELDS.items()} == {
        "UploadTargetResponse": ["upload_url"],
        "IngestTriggerRead": ["http_token"],
        "ServiceAccountCreated": ["key"],
        "SecretValueRead": ["value"],
    }


def test_install_is_idempotent():
    before = {m: m.__dict__["__repr_args__"] for m in _redaction.REDACTED_FIELDS}
    _redaction.install()
    assert {m: m.__dict__["__repr_args__"] for m in _redaction.REDACTED_FIELDS} == before


def test_install_refuses_a_field_a_regeneration_removed(monkeypatch):
    monkeypatch.setitem(
        _redaction.REDACTED_FIELDS, SecretValueRead, frozenset({"value", "gone_field"})
    )
    with pytest.raises(RuntimeError, match="gone_field"):
        _redaction.install()
