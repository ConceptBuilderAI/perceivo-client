# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 4cb0cc1fb62e540b6329e643c14e3ed2ef7982f14766508c71bd02701feb1b21

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class RunOverheadResponse(BaseModel):
    """
    ``GET /v1/billing/run-overhead/{run_id}`` — component vs overhead split
    for one run.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    is_final: bool | None = Field(None, title="Is Final")
    overhead_cost_usd: float | None = Field(None, title="Overhead Cost Usd")
    overhead_cu_hours: float | None = Field(None, title="Overhead Cu Hours")
    overhead_duration_ms: int | None = Field(None, title="Overhead Duration Ms")
    run_id: str | None = Field(None, title="Run Id")
    total_component_cost_usd: float | None = Field(
        None, title="Total Component Cost Usd"
    )
    total_component_duration_ms: int | None = Field(
        None, title="Total Component Duration Ms"
    )


class RunResult(BaseModel):
    """
    The output of a run.

    ``output_payload`` is null until the run reaches a terminal status. A run
    that failed carries its terminal ``status`` and ``error_message``.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    artifact: dict[str, Any] | None = Field(None, title="Artifact")
    completed_at: str | None = Field(None, title="Completed At")
    error_message: str | None = Field(None, title="Error Message")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    output_payload: dict[str, Any] | None = Field(None, title="Output Payload")
    run_id: str = Field(..., title="Run Id")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    workload_id: str | None = Field(None, title="Workload Id")


class RunStatus(BaseModel):
    """
    The status of a run.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    completed_at: str | None = Field(None, title="Completed At")
    error: str | None = Field(None, title="Error")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    run_id: str = Field(..., title="Run Id")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    workload_id: str | None = Field(None, title="Workload Id")


class RunSteps(BaseModel):
    """
    Per-node execution detail for one run of a workload.

    Each entry in ``steps`` describes one node's activity, including when it
    first and last executed and one span per execution. A node that ran more
    than once has more than one span.

    Note: ``count`` is the number of steps **in this response**, which is the whole
    set for the run — this collection is not windowed.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    count: int | None = Field(
        None, description="Number of steps returned.", title="Count"
    )
    run_id: str | None = Field(None, title="Run Id")
    run_number: int | None = Field(None, title="Run Number")
    status: str | None = Field(
        None, description="Status of the run described.", title="Status"
    )
    steps: list[dict[str, Any]] | None = Field(
        None, description="One entry per node that executed.", title="Steps"
    )
    workload_id: str = Field(..., title="Workload Id")


class RunSummary(BaseModel):
    """
    One run. ``run_id`` is accepted by every ``/v1/orchestrations/runs/{run_id}`` operation.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    completed_at: str | None = Field(None, title="Completed At")
    error: str | None = Field(None, title="Error")
    orchestration_id: str | None = Field(None, title="Orchestration Id")
    queued_at: str | None = Field(None, title="Queued At")
    run_id: str = Field(..., title="Run Id")
    source: str | None = Field(None, title="Source")
    started_at: str | None = Field(None, title="Started At")
    status: str | None = Field(None, title="Status")
    workload_id: str | None = Field(None, title="Workload Id")
    workload_type: str | None = Field(None, title="Workload Type")


class RuntimeObservations(BaseModel):
    """
    What static analysis of the script found. The script is never run.

    Despite the name, nothing here observes an execution. The validator parses
    the script into a syntax tree and inspects it; it does not import, evaluate
    or run any part of it, in a sandbox or otherwise. Every field below is a
    property of the source **text**, so each is a lower bound: anything a
    program assembles at run time is invisible to all three.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    calls: list[str] | None = Field(
        None,
        description="Platform SDK calls that appear in the script's source, as dotted names such as `perceivo.log.info`. Sorted and de-duplicated: a call written once and a call written in a loop both appear once, a call inside an unreachable branch still appears, and no arguments, ordering or counts are reported. This is what the code *contains*, not what it did.",
        title="Calls",
    )
    detected_hosts: list[str] | None = Field(
        None,
        description="Hostnames of `http://` and `https://` URLs written as literal strings in the script.\n\nNote: This is not a list of the hosts the component will contact, and an empty list is not evidence that it contacts none. The check is a pattern match over string literals, so a URL the script assembles at run time — by concatenation, formatting, an f-string, an environment variable or a configuration value — does not appear here. Use it to notice hard-coded endpoints, not to establish that a component has no egress.",
        title="Detected Hosts",
    )
    logs: list[str] | None = Field(
        None,
        description="Notes from the validator recording which groups of checks it ran. These are the validator's own messages — the script is not run, so it emits nothing. Present only when `validation_profile` is `full`.",
        title="Logs",
    )


class SearchIndexCreated(BaseModel):
    """
    The index was created.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    created: bool = Field(..., description="Always true on success.", title="Created")
    index: str = Field(..., description="Name of the index created.", title="Index")


class SearchIndexDeleted(BaseModel):
    """
    The index and everything in it were deleted.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    deleted: bool = Field(..., description="Always true on success.", title="Deleted")
    index: str = Field(..., description="Name of the index deleted.", title="Index")


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
