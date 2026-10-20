# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 c7769c0bc51e6694b75353cd8f1a8155cbef0675f5aea3aae9979f1bb5457490

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class SecretCreate(BaseModel):
    """
    A new secret. The value is write-only: no read on this API returns it.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    expiration_date: str | None = Field(None, title="Expiration Date")
    name: str = Field(..., title="Name")
    value: str = Field(..., title="Value")


class SecretRead(BaseModel):
    """
    A secret's metadata. The stored value is never part of it.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    created_at: str | None = Field(None, title="Created At")
    description: str | None = Field(None, title="Description")
    expiration_date: str | None = Field(None, title="Expiration Date")
    id: str = Field(..., title="Id")
    name: str = Field(..., title="Name")
    organization_id: str | None = Field(None, title="Organization Id")
    status: str = Field(
        ...,
        description="The secret's lifecycle state, for example `active`, `expired` or `disabled`. Treat an unrecognised value as not usable.",
        title="Status",
    )
    updated_at: AwareDatetime | None = Field(
        None,
        description="When the secret's metadata or value last changed.",
        title="Updated At",
    )


class SecretRotate(BaseModel):
    """
    The new material to store. The secret keeps its identifier.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    value: str = Field(
        ...,
        description="The new secret material. Write-only: no read on this API returns it.",
        min_length=1,
        title="Value",
    )


class SecretUpdate(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    description: str | None = Field(None, title="Description")
    expiration_date: str | None = Field(None, title="Expiration Date")
    name: str | None = Field(None, title="Name")
    value: str | None = Field(None, title="Value")


class SecretValueRead(BaseModel):
    """
    A secret's decrypted value.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    expires_at: str | None = Field(None, title="Expires At")
    value: str = Field(..., title="Value")


class ServiceAccountCreate(BaseModel):
    """
    Body for ``POST /v1/service-accounts``.

    Note: ``privileges`` is **capped**, not defaulted: whatever arrives here is
    intersected with the creating principal's own grant, so an account cannot be
    minted with more privilege than the principal creating it, and asking for
    less still works. A list whose intersection is empty -- every privilege it
    names is one the principal does not hold -- is refused with 403 naming them,
    not created empty. The same cap applies to ``ServiceAccountUpdate``, so an
    account cannot be widened after creation either.

    Note: Two states, not three. **Omit** ``privileges`` to inherit your own set;
    send a **list** to get a capped subset. An explicit ``null`` is **refused**
    (422): on ``PATCH`` a null means "reduce this account to the empty set", and a
    created account cannot hold none, so the one reading that would work here is
    "everything the creator holds" — the widest possible outcome, spelled the way
    a caller spells an empty field. One literal must not mean *empty* on one verb
    of this plane and *grant me everything* on the other.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    endpoint_access: EndpointAccess | None = Field(
        None,
        description="The endpoints the account may call. Omit to give it your own credential's endpoint access; a wider policy, `null` included, is refused with `403`.",
    )
    expires_at: str | None = Field(
        None,
        description="When the credential stops authenticating, as an ISO 8601 timestamp. Omit for a credential that does not expire.",
        title="Expires At",
    )
    name: str | None = Field(
        None,
        description="A display name for the account. Omit for a default name.",
        title="Name",
    )
    privileges: list[str] | None = Field(
        None,
        description="The account's endpoint privileges: which operations it may call. They confer no access to resources; grant that with `/v1/grants` or a group membership. Omit to give it the endpoint privileges your own credential holds, or send a list to request a subset of them: the list is intersected with what you hold, and a list naming only privileges you do not hold is refused with `403`, naming them. `null` is refused with `422`.",
        title="Privileges",
    )


class ServiceAccountCreated(BaseModel):
    """
    The creation response — the only body that ever carries key material.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str = Field(..., title="Created By User Id")
    endpoint_access: EndpointAccess | None = None
    expires_at: str | None = Field(None, title="Expires At")
    id: str = Field(..., title="Id")
    is_active: bool = Field(..., title="Is Active")
    key: str = Field(
        ...,
        description="Full plaintext key. Returned once, on creation, never again.",
        title="Key",
    )
    name: str | None = Field(None, title="Name")
    organization_id: str = Field(..., title="Organization Id")
    prefix: str = Field(..., title="Prefix")
    privileges: list[str] | None = Field(None, title="Privileges")


class ServiceAccountRead(BaseModel):
    """
    A service account as every READ path returns it.

    Note: There is no ``key`` field and there must never be one: key material is
    returned exactly once, on creation, and no read path may return it
    again.

    ``prefix`` is a display label shared by every key in the organization. It
    does not identify a single key and does not change on rotation; identify an
    account by ``id``. Identifiers, ``prefix`` included, are opaque and MUST NOT
    be parsed by clients.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    auth_mode: str | None = Field(None, title="Auth Mode")
    created_at: str = Field(..., title="Created At")
    created_by_user_id: str = Field(..., title="Created By User Id")
    endpoint_access: EndpointAccess | None = None
    expires_at: str | None = Field(None, title="Expires At")
    has_signing_secret: bool | None = Field(False, title="Has Signing Secret")
    id: str = Field(..., title="Id")
    is_active: bool = Field(..., title="Is Active")
    last_used_at: str | None = Field(None, title="Last Used At")
    lock_clears_at: str | None = Field(
        None,
        description="When a lock that clears on its own stops refusing requests. Null both for an unlocked account and for a permanent lock; `lock_is_permanent` tells them apart.",
        title="Lock Clears At",
    )
    lock_count_24h: int | None = Field(
        None,
        description="Lock events in the last 24 hours, where computed (the single-account read). Null means not computed, not zero.",
        title="Lock Count 24H",
    )
    lock_is_permanent: bool | None = Field(
        False,
        description="True when the lock never clears on its own. Read with `locked_at`.",
        title="Lock Is Permanent",
    )
    lock_reason: str | None = Field(None, title="Lock Reason")
    locked_at: str | None = Field(None, title="Locked At")
    name: str | None = Field(None, title="Name")
    organization_id: str = Field(..., title="Organization Id")
    prefix: str = Field(..., title="Prefix")
    privileges: list[str] | None = Field(None, title="Privileges")
    revoked_at: str | None = Field(None, title="Revoked At")
    revoked_by_user_id: str | None = Field(None, title="Revoked By User Id")
    signing_secret_enrolled_at: str | None = Field(
        None, title="Signing Secret Enrolled At"
    )


class ServiceAccountRevoked(BaseModel):
    """
    The body ``DELETE /v1/service-accounts/{id}`` returns on a successful revoke.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    revoked: bool = Field(..., title="Revoked")
    revoked_at: str | None = Field(None, title="Revoked At")
    revoked_by_user_id: str | None = Field(None, title="Revoked By User Id")


class ServiceAccountUpdate(BaseModel):
    """
    Body for ``PATCH /v1/service-accounts/{service_account_id}``.

    Note: ``privileges`` is **capped** exactly as on create — intersected with the
    editing principal's own grant — so this operation cannot widen an account
    beyond its editor. Omit the field to leave privileges untouched, or send a
    list to set a capped subset. Omitting the field is not the same as sending an
    empty list.

    Note: ``null`` and ``[]`` both mean the empty set, and an empty set is
    **refused** with 422 ("privileges list must not be empty"). Sending either
    does not leave the account holding nothing — no request on this route can.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    endpoint_access: EndpointAccess | None = Field(
        None,
        description="A new endpoint access policy, replacing the current one. Omit to leave it unchanged.",
    )
    expires_at: str | None = Field(
        None,
        description="A new expiry, as an ISO 8601 timestamp. Omit to leave the current expiry unchanged.",
        title="Expires At",
    )
    is_active: bool | None = Field(
        None,
        description="Not applied: sending it changes nothing. To stop an account authenticating, revoke it with `DELETE /v1/service-accounts/{service_account_id}`.",
        title="Is Active",
    )
    name: str | None = Field(
        None, description="A new display name for the account.", title="Name"
    )
    privileges: list[str] | None = Field(
        None,
        description="The account's new endpoint privileges (no resource access; that is granted separately), capped to the privileges your own credential holds. Omit to leave the account's privileges unchanged; `null` and `[]` are refused with `422`.",
        title="Privileges",
    )


class ServiceLifecycleResponse(BaseModel):
    """
    Generic infrastructure service start/stop acknowledgement.

    The shape varies by service_type (MCP returns a full status; the data stores
    return a lighter ``{status, ...}``), so this is intentionally permissive.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    message: str | None = Field(None, title="Message")
    service_type: str | None = Field(None, title="Service Type")
    status: str | None = Field(None, title="Status")


class ServiceSecretCreate(BaseModel):
    """
    Attach an organization secret to one service of an intelligence.

    ``alias`` is the name the extension asks for at run time --
    ``await perceivo.secrets.get_by_alias("alpha_vantage_api_key")`` -- so it is
    part of the script's contract and not a label. The secret VALUE never
    travels on this route; only the id of a secret that already exists in the
    organization.
    """

    alias: str = Field(..., max_length=100, min_length=1, title="Alias")
    secret_id: str = Field(..., title="Secret Id")
    service_type: str = Field(
        ...,
        description="feature, training, inference or evaluation",
        title="Service Type",
    )


class ServiceSecretRead(BaseModel):
    """
    A secret attached to an intelligence service. Carries no secret value.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    alias: str | None = Field(None, title="Alias")
    id: str | None = Field(None, title="Id")
    intelligence_id: str | None = Field(None, title="Intelligence Id")
    secret_id: str | None = Field(None, title="Secret Id")
    secret_name: str | None = Field(None, title="Secret Name")
    service_type: str | None = Field(None, title="Service Type")


class StartIntelligenceRequest(BaseModel):
    """
    Start an intelligence runtime.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    force_restart: bool | None = Field(False, title="Force Restart")
    skip_infrastructure_check: bool | None = Field(
        False, title="Skip Infrastructure Check"
    )


class StopIntelligenceRequest(BaseModel):
    """
    Stop an intelligence runtime.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    graceful: bool | None = Field(True, title="Graceful")
    timeout_seconds: int | None = Field(30, title="Timeout Seconds")


class StorageSpaceCreate(BaseModel):
    """
    Create a storage space. ``organization_id`` is set from the API key.
    """

    description: str | None = Field(None, title="Description")
    is_default: bool | None = Field(False, title="Is Default")
    name: str = Field(..., max_length=255, title="Name")
    quota_bytes: int | None = Field(None, title="Quota Bytes")


class StorageSpaceRead(BaseModel):
    """
    A storage space belonging to an organization.
    """

    created_at: AwareDatetime = Field(..., title="Created At")
    created_by_user_id: UUID = Field(..., title="Created By User Id")
    description: str | None = Field(None, title="Description")
    id: UUID = Field(..., title="Id")
    is_default: bool = Field(..., title="Is Default")
    is_personal: bool = Field(..., title="Is Personal")
    name: str = Field(..., title="Name")
    organization_id: UUID | None = Field(None, title="Organization Id")
    owner_user_id: UUID | None = Field(None, title="Owner User Id")
    quota_bytes: int | None = Field(None, title="Quota Bytes")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    used_bytes: int = Field(..., title="Used Bytes")


class StorageSpaceUpdateName(RootModel[str]):
    root: str = Field(..., description="New space name", max_length=255, title="Name")


class QuotaBytes(RootModel[int]):
    root: int = Field(
        ..., description="Storage quota in bytes", ge=0, title="Quota Bytes"
    )


class StorageSpaceUpdate(BaseModel):
    """
    Fields to change on a storage space. Omitted fields are left alone.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    description: str | None = Field(
        None, description="New description", title="Description"
    )
    is_default: bool | None = Field(
        None,
        description="Make this the organization's default space",
        title="Is Default",
    )
    name: StorageSpaceUpdateName | None = Field(
        None, description="New space name", title="Name"
    )
    quota_bytes: QuotaBytes | None = Field(
        None, description="Storage quota in bytes", title="Quota Bytes"
    )


class StorageUsageRead(BaseModel):
    """
    Usage summary for a single storage space.
    """

    file_count: int = Field(..., title="File Count")
    folder_count: int = Field(..., title="Folder Count")
    quota_bytes: int | None = Field(None, title="Quota Bytes")
    storage_space_id: UUID = Field(..., title="Storage Space Id")
    storage_space_name: str = Field(..., title="Storage Space Name")
    trashed_bytes: int | None = Field(0, title="Trashed Bytes")
    trashed_file_count: int | None = Field(0, title="Trashed File Count")
    used_bytes: int = Field(..., title="Used Bytes")


class SubscriptionRead(BaseModel):
    """
    ``GET /v1/billing/subscription`` — the org's billing configuration record.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    azure_subscription_id: str | None = Field(None, title="Azure Subscription Id")
    azure_tenant_id: str | None = Field(None, title="Azure Tenant Id")
    billing_currency: str | None = Field(None, title="Billing Currency")
    billing_cycle: str | None = Field(None, title="Billing Cycle")
    created_at: str | None = Field(None, title="Created At")
    csp_partner_id: str | None = Field(None, title="Csp Partner Id")
    csp_partner_name: str | None = Field(None, title="Csp Partner Name")
    default_compute_markup_percent: float | None = Field(
        None, title="Default Compute Markup Percent"
    )
    default_llm_markup_percent: float | None = Field(
        None, title="Default Llm Markup Percent"
    )
    default_storage_markup_percent: float | None = Field(
        None, title="Default Storage Markup Percent"
    )
    default_transfer_markup_percent: float | None = Field(
        None, title="Default Transfer Markup Percent"
    )
    id: str | None = Field(None, title="Id")
    invoice_email: str | None = Field(None, title="Invoice Email")
    is_active: bool | None = Field(None, title="Is Active")
    markup_overrides: list[Any] | None = Field(None, title="Markup Overrides")
    organization_id: str | None = Field(None, title="Organization Id")
    updated_at: str | None = Field(None, title="Updated At")


class SubscriptionReadV1(BaseModel):
    """
    One subscription.

    Note: The subscriptions operation returns a **list**, even though its path is
    singular — an organization may hold more than one.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created_at: str = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    organization_id: str = Field(..., title="Organization Id")
    status: str | None = Field(None, title="Status")
    tier_id: str | None = Field(None, title="Tier Id")
    updated_at: str = Field(..., title="Updated At")
